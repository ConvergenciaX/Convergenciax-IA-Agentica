"""DocChat RAG — Hybrid retriever builder (BM25 + multi-Chroma collections with idempotent indexing)."""
from typing import Dict, List, Optional
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from config.settings import settings
import chromadb
import hashlib
import logging
import time
import requests

logger = logging.getLogger(__name__)


class RetrieverBuilder:
    """Build a hybrid retriever using BM25 + multiple Chroma collections (one per document)."""

    def __init__(self):
        """Initialize embeddings using Ollama."""
        logger.info(f"Initializing OllamaEmbeddings with model='{settings.EMBEDDING_MODEL}', "
                   f"base_url='{settings.OLLAMA_BASE_URL}'")

        self.embeddings = OllamaEmbeddings(
            model=settings.EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
        self.chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT
        )
        logger.info("✓ OllamaEmbeddings initialized")

    def list_collections(self) -> List[str]:
        """List all collections currently in ChromaDB."""
        try:
            collections = self.chroma_client.list_collections()
            names = [c.name for c in collections]
            logger.debug(f"Collections in ChromaDB: {names}")
            return names
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def get_collection_details(self, collection_name: str) -> dict:
        """Get collection details (count, metadata, etc.)."""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            count = collection.count()
            return {
                "name": collection_name,
                "chunks": count,
                "metadata": getattr(collection, "metadata", {})
            }
        except Exception as e:
            logger.error(f"Failed to get details for '{collection_name}': {e}")
            return None

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from ChromaDB.

        Use case: Update documents by deleting old collection and re-indexing.
        """
        try:
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"✓ Collection '{collection_name}' deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            return False

    def get_health_status(self) -> Dict:
        """Check ChromaDB health: heartbeat, host:port, collections, chunks.

        Returns dict with:
            - heartbeat_ok (bool): ChromaDB is responding
            - heartbeat_ms (float): latency in milliseconds
            - host, port (str, int): connection details
            - total_collections (int): number of collections
            - total_chunks (int): sum of chunks across all collections
            - collections_detail (list): [{name, count}, ...]
            - error (str): descriptive error if heartbeat fails
        """
        result = {
            "heartbeat_ok": False,
            "heartbeat_ms": None,
            "host": settings.CHROMA_HOST,
            "port": settings.CHROMA_PORT,
            "total_collections": 0,
            "total_chunks": 0,
            "collections_detail": [],
            "error": None,
        }

        # 1. Heartbeat check (use /api/v2/heartbeat for ChromaDB v2+)
        try:
            heartbeat_url = f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v1/heartbeat"
            start = time.perf_counter()
            response = requests.get(heartbeat_url, timeout=5)
            elapsed_ms = (time.perf_counter() - start) * 1000
            result["heartbeat_ms"] = elapsed_ms

            if response.status_code == 200:
                result["heartbeat_ok"] = True
                logger.debug(f"✓ ChromaDB heartbeat OK ({elapsed_ms:.1f}ms)")
            elif response.status_code == 501 or "deprecated" in response.text.lower():
                # Fall back to /api/v2/heartbeat if v1 is deprecated
                logger.debug("v1 API deprecated, trying v2...")
                heartbeat_url = f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v2/heartbeat"
                start = time.perf_counter()
                response = requests.get(heartbeat_url, timeout=5)
                elapsed_ms = (time.perf_counter() - start) * 1000
                result["heartbeat_ms"] = elapsed_ms
                if response.status_code == 200:
                    result["heartbeat_ok"] = True
                    logger.debug(f"✓ ChromaDB heartbeat OK (v2, {elapsed_ms:.1f}ms)")
                else:
                    result["error"] = f"HTTP {response.status_code} from heartbeat endpoint"
                    logger.warning(f"ChromaDB heartbeat returned {response.status_code}")
            else:
                result["error"] = f"HTTP {response.status_code} from heartbeat endpoint"
                logger.warning(f"ChromaDB heartbeat returned {response.status_code}")
        except requests.exceptions.Timeout:
            result["error"] = "Timeout connecting to ChromaDB"
            logger.warning("ChromaDB heartbeat timeout")
        except requests.exceptions.ConnectionError:
            result["error"] = f"Cannot connect to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}"
            logger.warning(f"ChromaDB connection refused: {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        except Exception as e:
            result["error"] = str(e)
            logger.warning(f"ChromaDB health check failed: {e}")

        # 2. Collections and chunks count
        if result["heartbeat_ok"]:
            try:
                collections = self.chroma_client.list_collections()
                result["total_collections"] = len(collections)

                for col in collections:
                    try:
                        count = col.count()
                        result["total_chunks"] += count
                        result["collections_detail"].append({"name": col.name, "count": count})
                    except Exception as e:
                        logger.warning(f"Could not get count for collection '{col.name}': {e}")

                logger.debug(f"✓ ChromaDB: {result['total_collections']} collections, {result['total_chunks']} chunks")
            except Exception as e:
                logger.warning(f"Failed to enumerate collections: {e}")
                result["error"] = f"Heartbeat OK but could not enumerate collections: {e}"

        return result

    def build_retriever(self, collections_to_index: Dict[str, Optional[List[Document]]],
                       selected_existing: Optional[List[str]] = None) -> EnsembleRetriever:
        """Build hybrid retriever from new documents and/or existing collections.

        Args:
            collections_to_index: {collection_name: chunks_list | None}
                - chunks_list: nueva colección a crear e indexar
                - None: colección ya existente en Chroma (reutilizar sin reembeber)
            selected_existing: colecciones seleccionadas del dropdown (backup si no vienen en collections_to_index)

        Retorna: EnsembleRetriever combinando:
            - 1 BM25 sobre corpus combinado de todas las colecciones
            - 1 Retriever vectorial por colección (pesos repartidos)
        """
        try:
            all_collection_names = set()
            all_docs_for_bm25 = []

            # 1. Indexar nuevas colecciones
            for collection_name, chunks in collections_to_index.items():
                if chunks is None:
                    # Colección ya existe; solo obtener sus textos para BM25
                    all_collection_names.add(collection_name)
                    logger.info(f"Reusing existing collection: '{collection_name}'")
                    try:
                        collection = self.chroma_client.get_collection(name=collection_name)
                        stored = collection.get(include=["documents", "metadatas"])
                        for text in stored.get("documents", []):
                            all_docs_for_bm25.append(Document(page_content=text))
                    except Exception as e:
                        logger.warning(f"Could not retrieve texts from '{collection_name}': {e}")
                else:
                    # Nueva colección: indexar con deduplicación + idempotencia
                    all_collection_names.add(collection_name)
                    logger.info(f"Indexing new collection: '{collection_name}' with {len(chunks)} chunks")
                    self._index_collection_idempotent(collection_name, chunks)
                    all_docs_for_bm25.extend(chunks)

            # 2. Agregar colecciones seleccionadas del dropdown (si no ya están en collections_to_index)
            if selected_existing:
                for col_name in selected_existing:
                    if col_name not in all_collection_names:
                        all_collection_names.add(col_name)
                        logger.info(f"Reusing selected collection: '{col_name}'")
                        try:
                            collection = self.chroma_client.get_collection(name=col_name)
                            stored = collection.get(include=["documents"])
                            for text in stored.get("documents", []):
                                all_docs_for_bm25.append(Document(page_content=text))
                        except Exception as e:
                            logger.warning(f"Could not retrieve '{col_name}': {e}")

            if not all_collection_names:
                raise ValueError("No collections to index (all missing or empty)")

            logger.info(f"Building retriever over {len(all_collection_names)} collection(s): {sorted(all_collection_names)}")

            # 3. BM25 sobre corpus combinado
            if not all_docs_for_bm25:
                raise ValueError("No documents to index in BM25")

            bm25 = BM25Retriever.from_documents(all_docs_for_bm25)
            logger.info(f"✓ BM25 created from {len(all_docs_for_bm25)} combined documents")

            # 4. Vectorial: 1 retriever por colección
            vector_retrievers = []
            for collection_name in sorted(all_collection_names):
                try:
                    vector_store = Chroma(
                        client=self.chroma_client,
                        collection_name=collection_name,
                        embedding_function=self.embeddings
                    )
                    v_ret = vector_store.as_retriever(
                        search_kwargs={"k": settings.VECTOR_SEARCH_K}
                    )
                    vector_retrievers.append(v_ret)
                    logger.debug(f"  → Vector retriever for '{collection_name}'")
                except Exception as e:
                    logger.warning(f"Could not create vector retriever for '{collection_name}': {e}")

            if not vector_retrievers:
                raise ValueError("No vector retrievers created")

            # 5. Ensemble: BM25 + vectoriales con pesos automáticos
            # weights = [bm25_weight, vector_weight_1, vector_weight_2, ...]
            # Pesos: BM25 = 40%, resto repartido equally entre vectoriales
            bm25_weight, vector_weight_total = settings.ENSEMBLE_WEIGHTS
            per_vector = vector_weight_total / len(vector_retrievers) if vector_retrievers else 0

            weights = [bm25_weight] + [per_vector] * len(vector_retrievers)
            retrievers = [bm25] + vector_retrievers

            logger.info(f"Ensemble weights: BM25={bm25_weight:.2f}, "
                       f"Vector (per collection)={per_vector:.2f} x {len(vector_retrievers)}")

            hybrid_retriever = EnsembleRetriever(
                retrievers=retrievers,
                weights=weights
            )
            logger.info(f"✓ Hybrid retriever built successfully")
            return hybrid_retriever

        except Exception as e:
            logger.error(f"❌ Failed to build retriever: {e}", exc_info=True)
            raise

    def _index_collection_idempotent(self, collection_name: str, docs: List[Document]):
        """Index documents idempotently: only embed missing chunks, skip duplicates.

        IDs deterministas = sha256(chunk text) para detectar duplicados cuando
        el mismo archivo se indexa en otra sesión.
        """
        try:
            # Get or create collection
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.debug(f"Collection '{collection_name}' ready")

            # Compute deterministic IDs
            docs_to_embed = []
            ids_to_embed = []

            for doc in docs:
                doc_id = hashlib.sha256(doc.page_content.encode()).hexdigest()[:32]

                # Check if already exists
                try:
                    existing = collection.get(ids=[doc_id], include=[])
                    if existing["ids"]:
                        logger.debug(f"  Skipping duplicate (already indexed): {doc_id[:8]}...")
                        continue
                except Exception:
                    pass

                # New document: will embed
                docs_to_embed.append(doc)
                ids_to_embed.append(doc_id)

            if not docs_to_embed:
                logger.info(f"  All chunks already indexed in '{collection_name}'")
                return

            # Embed only new chunks
            logger.info(f"  Embedding {len(docs_to_embed)} new chunks...")
            embeddings_list = self.embeddings.embed_documents([d.page_content for d in docs_to_embed])

            # Add to collection with deterministic IDs
            collection.add(
                ids=ids_to_embed,
                documents=[d.page_content for d in docs_to_embed],
                embeddings=embeddings_list,
                metadatas=[getattr(d, "metadata", {}) for d in docs_to_embed]
            )

            logger.info(f"✓ Collection '{collection_name}': {len(docs_to_embed)} new chunks indexed, "
                       f"{len(docs) - len(docs_to_embed)} duplicates skipped")

        except Exception as e:
            logger.error(f"Failed to index '{collection_name}': {e}", exc_info=True)
            raise
