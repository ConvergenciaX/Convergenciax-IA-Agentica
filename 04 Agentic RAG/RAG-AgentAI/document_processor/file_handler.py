"""DocChat RAG — Document processor (parsing PDFs/docs + chunking with Docling)."""
import os
import hashlib
import pickle
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from langchain_text_splitters import MarkdownHeaderTextSplitter
from config import constants
from config.settings import settings
from utils.logging import logger


class DocumentProcessor:
    """Parse documents (PDF, DOCX, TXT, MD) and split into semantic chunks.

    Configuración offline (sin contactar HuggingFace en runtime):
    - Docling: modelos pre-descargados en ./models/docling/ (ejecutar scripts/download_local_models.py una vez)
    - EasyOCR: modelos pre-cacheados en ./models/easyocr/ (se cachean automáticamente en primer uso)
    - Variables de entorno offline (HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE) activadas en app.py
    """

    def __init__(self, do_ocr_override: Optional[bool] = None):
        """Initialize the processor with cache directory, headers for splitting, y Docling pipeline offline.

        Args:
            do_ocr_override: If provided, overrides settings.DOCLING_DO_OCR for this instance.
                            Useful for UI-driven per-document OCR control.
        """
        self.headers = [("#", "Header 1"), ("##", "Header 2")]
        self.cache_dir = Path(settings.LOG_DIR) / "document_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Permitir override de OCR por parámetro (ej. desde UI)
        do_ocr = do_ocr_override if do_ocr_override is not None else settings.DOCLING_DO_OCR

        # Crear pipeline de Docling con configuración offline
        # (artifacts_path explícito evita que StandardPdfPipeline llame a download_models_hf())
        artifacts_path = Path(settings.DOCLING_ARTIFACTS_PATH)
        ocr_models_path = Path(settings.DOCLING_OCR_MODELS_PATH)

        logger.info(f"Inicializando Docling con artifacts_path={artifacts_path} (offline)")
        logger.info(f"  OCR: {'habilitado' if do_ocr else 'deshabilitado'}")
        if do_ocr_override is not None:
            logger.info(f"  (OCR override: {do_ocr_override}, config.ini: {settings.DOCLING_DO_OCR})")

        # Build pipeline_options: solo incluir ocr_options si OCR está habilitado
        pipeline_kwargs = {
            "artifacts_path": artifacts_path,
            "do_ocr": do_ocr,
        }

        if do_ocr:
            pipeline_kwargs["ocr_options"] = EasyOcrOptions(
                model_storage_directory=str(ocr_models_path),
                download_enabled=False,  # Nunca descargar en runtime
            )

        pipeline_options = PdfPipelineOptions(**pipeline_kwargs)

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            }
        )

        logger.info(f"DocumentProcessor initialized (cache: {self.cache_dir})")
        logger.info("✓ Docling pipeline configurado para operación offline")

    def validate_files(self, files: List) -> None:
        """Validate that uploaded files don't exceed size limits."""
        total_size = sum(os.path.getsize(f.name) for f in files)
        if total_size > constants.MAX_TOTAL_SIZE:
            msg = f"Total size {total_size/(1024*1024):.1f}MB exceeds limit {constants.MAX_TOTAL_SIZE/(1024*1024):.0f}MB"
            logger.error(msg)
            raise ValueError(msg)
        logger.debug(f"✓ File validation passed (total: {total_size/(1024*1024):.1f}MB)")

    def process(self, files: List) -> Dict[str, List]:
        """Process files (with caching) and return dict: collection_name -> chunks.

        Una colección por documento para aislamiento, reutilización, y búsqueda selectiva.
        Si un archivo produce 0 chunks, se omite su colección (ej. OCR fallido).
        """
        logger.info(f"Processing {len(files)} file(s) → una colección por documento")
        self.validate_files(files)

        collections = {}  # collection_name -> chunks

        for file in files:
            try:
                # Generate content-based hash for caching
                with open(file.name, "rb") as f:
                    file_content = f.read()
                    file_hash = self._generate_hash(file_content)

                cache_path = self.cache_dir / f"{file_hash}.pkl"

                if self._is_cache_valid(cache_path):
                    logger.info(f"Loading from cache: {file.name}")
                    chunks = self._load_from_cache(cache_path)
                else:
                    logger.info(f"Processing file: {file.name}")
                    chunks = self._process_file(file)
                    if chunks:
                        self._save_to_cache(chunks, cache_path)

                # Skip if no chunks produced (e.g. OCR failed, empty file)
                if not chunks:
                    logger.warning(f"⚠️  {file.name} produced 0 chunks; skipping (check OCR models or file validity)")
                    continue

                # Create collection name: slugified filename + content hash prefix
                collection_name = self._collection_name_for_file(file.name, file_hash)

                # Deduplicate within this document
                seen = set()
                deduped_chunks = []
                for chunk in chunks:
                    chunk_hash = self._generate_hash(chunk.page_content.encode())
                    if chunk_hash not in seen:
                        deduped_chunks.append(chunk)
                        seen.add(chunk_hash)

                collections[collection_name] = deduped_chunks
                logger.info(f"  → {file.name}: {len(deduped_chunks)} chunks → collection '{collection_name}'")

            except Exception as e:
                logger.error(f"Failed to process {file.name}: {e}", exc_info=True)
                # Continue with next file; don't let one failure block others
                continue

        logger.info(f"✓ Indexing {len(collections)} document(s) → {sum(len(c) for c in collections.values())} total chunks")
        return collections

    def _process_file(self, file) -> List:
        """Parse file with Docling (offline, sin contactar HuggingFace) y split by Markdown headers."""
        if not file.name.endswith(('.pdf', '.docx', '.txt', '.md')):
            logger.warning(f"Skipping unsupported file type: {file.name}")
            return []

        # Parse document to Markdown using Docling (pipeline ya inicializado en __init__ con offline mode)
        markdown = self.converter.convert(file.name).document.export_to_markdown()

        # Split by headers
        splitter = MarkdownHeaderTextSplitter(self.headers)
        chunks = splitter.split_text(markdown)
        return chunks

    def _generate_hash(self, content: bytes) -> str:
        """SHA256 hash of content for deduplication."""
        return hashlib.sha256(content).hexdigest()

    def _save_to_cache(self, chunks: List, cache_path: Path):
        """Pickle chunks with metadata."""
        with open(cache_path, "wb") as f:
            pickle.dump({
                "timestamp": datetime.now().timestamp(),
                "chunks": chunks
            }, f)

    def _load_from_cache(self, cache_path: Path) -> List:
        """Unpickle cached chunks."""
        with open(cache_path, "rb") as f:
            data = pickle.load(f)
        return data["chunks"]

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached chunks are still fresh."""
        if not cache_path.exists():
            return False

        # Use settings.CACHE_EXPIRE_DAYS if available (falls back to 7)
        expire_days = getattr(settings.config, "_sections", {}).get("rag", {}).get("cache_expire_days", 7)
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return cache_age < timedelta(days=expire_days)

    def _collection_name_for_file(self, filename: str, file_hash: str) -> str:
        """Generate deterministic collection name: slugified_filename + hash prefix.

        Ejemplo: 'My Document (2024).pdf' + 'a1b2c3d4...' → 'my_document_2024_a1b2c3d4'
        """
        # Slugify: letras/números/espacios → alfanuméricos/guiones, minúsculas
        slug = re.sub(r'[^a-z0-9\s\-]', '', filename.lower())
        slug = re.sub(r'[\s]+', '_', slug.strip())
        slug = re.sub(r'[\-]+', '_', slug)
        slug = slug.rstrip('_')[:40]  # Max 40 chars para el slug

        # Append hash prefix (8 chars, determinístico)
        hash_prefix = file_hash[:8]

        collection = f"{slug}_{hash_prefix}"

        # Enforce Chroma naming: 3-63 chars, alphanumeric + - _
        if len(collection) < 3:
            collection = f"doc_{hash_prefix}"
        if len(collection) > 63:
            collection = f"{slug[:32]}_{hash_prefix}"

        return collection
