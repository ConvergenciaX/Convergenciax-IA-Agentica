#!/usr/bin/env python3
"""Search ChromaDB — Busca documentos por query o ID."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
import json
from config.settings import settings
from langchain_ollama import OllamaEmbeddings

def search_by_query(query: str, k: int = 5):
    """Busca por similitud semántica (embedding)."""

    print(f"🔎 Buscando: '{query}'")
    print(f"   Generando embedding con Ollama...")

    # Generar embedding de la query
    embeddings = OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL
    )
    query_embedding = embeddings.embed_query(query)
    print(f"   ✓ Embedding generado ({len(query_embedding)} dimensiones)")

    # Conectar a Chroma
    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    collection = client.get_collection(name=settings.CHROMA_COLLECTION_NAME)

    # Buscar
    print(f"\n   Buscando {k} fragmentos similares...")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )

    if not results["ids"] or len(results["ids"][0]) == 0:
        print("   (sin resultados)")
        return

    print(f"\n📋 Resultados (top {len(results['ids'][0])}):\n")
    for i, doc_id in enumerate(results["ids"][0], 1):
        doc = results["documents"][0][i-1]
        meta = results["metadatas"][0][i-1]
        distance = results["distances"][0][i-1]

        print(f"[{i}] Similitud: {1 - distance:.3f} | Archivo: {meta.get('file', 'N/A')}")
        print(f"    {doc[:100]}..." if len(doc) > 100 else f"    {doc}")
        print()

def search_by_id(doc_id: str):
    """Busca un documento específico por ID."""

    print(f"🔍 Buscando documento: {doc_id}")

    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    collection = client.get_collection(name=settings.CHROMA_COLLECTION_NAME)

    try:
        result = collection.get(ids=[doc_id], include=["documents", "metadatas"])

        if not result["ids"]:
            print("   (no encontrado)")
            return

        doc = result["documents"][0]
        meta = result["metadatas"][0]

        print(f"\n📄 Encontrado:")
        print(f"   Archivo: {meta.get('file', 'N/A')}")
        print(f"   Sección: {meta.get('section', 'N/A')}")
        print(f"   Contenido:\n{doc}\n")
        print(f"   Metadatos: {json.dumps(meta, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"   Error: {e}")

def list_all():
    """Lista todos los documentos con un resumen."""

    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    collection = client.get_collection(name=settings.CHROMA_COLLECTION_NAME)

    count = collection.count()
    print(f"📚 Total de fragmentos: {count}\n")

    if count == 0:
        print("(vacía)")
        return

    results = collection.get(include=["metadatas"])

    files = {}
    for meta in results["metadatas"]:
        fname = meta.get("file", "unknown")
        if fname not in files:
            files[fname] = 0
        files[fname] += 1

    print("📄 Por archivo:")
    for fname, n_chunks in sorted(files.items()):
        print(f"   {fname}: {n_chunks} fragmentos")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python search_chroma.py list                    # Listar todos")
        print("  python search_chroma.py query '<tu pregunta>'   # Buscar por similitud")
        print("  python search_chroma.py id '<doc_id>'           # Buscar por ID")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "list":
        list_all()
    elif cmd == "query" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        search_by_query(query, k=5)
    elif cmd == "id" and len(sys.argv) > 2:
        doc_id = sys.argv[2]
        search_by_id(doc_id)
    else:
        print("Comando no reconocido")
