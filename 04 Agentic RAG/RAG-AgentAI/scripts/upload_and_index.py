#!/usr/bin/env python3
"""Upload and index a PDF independently — nombre del índice = título del documento."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import re
from document_processor.file_handler import DocumentProcessor
from retriever.builder import RetrieverBuilder
from utils.logging import logger


def _extract_title_from_pdf(pdf_path: str) -> str:
    """Intenta extraer el título del PDF (primeras líneas del contenido)."""
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
        from config.settings import settings
        from pathlib import Path as PathlibPath

        artifacts_path = PathlibPath(settings.DOCLING_ARTIFACTS_PATH)
        ocr_models_path = PathlibPath(settings.DOCLING_OCR_MODELS_PATH)

        # Build pipeline_options: solo incluir ocr_options si OCR está habilitado
        pipeline_kwargs = {
            "artifacts_path": artifacts_path,
            "do_ocr": settings.DOCLING_DO_OCR,
        }

        if settings.DOCLING_DO_OCR:
            pipeline_kwargs["ocr_options"] = EasyOcrOptions(
                model_storage_directory=str(ocr_models_path),
                download_enabled=False,
            )

        pipeline_options = PdfPipelineOptions(**pipeline_kwargs)

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: __import__('docling.document_converter', fromlist=['PdfFormatOption']).PdfFormatOption(
                    pipeline_options=pipeline_options
                ),
            }
        )

        doc = converter.convert(pdf_path).document
        markdown = doc.export_to_markdown()

        # Extraer primera línea con contenido (título)
        for line in markdown.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Primera línea de contenido real
                return line[:60]  # Max 60 chars
            elif line.startswith('#'):
                # Es un header, usarlo como título
                return re.sub(r'^#+\s*', '', line)[:60]

        return Path(pdf_path).stem[:60]

    except Exception as e:
        logger.warning(f"Could not extract title from PDF: {e}. Using filename.")
        return Path(pdf_path).stem[:60]


def _slugify_title(title: str) -> str:
    """Convertir título a nombre válido para colección: alfanumérico + guiones."""
    # Lowercase, remove special chars
    slug = re.sub(r'[^a-z0-9\s\-]', '', title.lower())
    # Replace spaces with underscores
    slug = re.sub(r'[\s]+', '_', slug.strip())
    # Remove consecutive dashes
    slug = re.sub(r'[\-]+', '_', slug)
    slug = slug.rstrip('_')

    # Enforce Chroma naming (3-63 chars)
    if len(slug) < 3:
        slug = f"doc_{slug}"
    if len(slug) > 63:
        slug = slug[:60]

    return slug


def upload_and_index(pdf_path: str, custom_title: str = None):
    """Upload and index a PDF with custom title."""
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        logger.error(f"File not found: {pdf_path}")
        return False

    logger.info(f"📄 Processing: {pdf_path}")

    # Extract or use custom title
    if custom_title:
        title = custom_title
        logger.info(f"📝 Using custom title: {title}")
    else:
        title = _extract_title_from_pdf(pdf_path)
        logger.info(f"📝 Extracted title: {title}")

    # Slugify title for collection name
    collection_name = _slugify_title(title)
    logger.info(f"🏷️  Collection name: '{collection_name}'")

    try:
        # 1. Process document
        logger.info("🔄 Processing document...")
        processor = DocumentProcessor()

        # Simulate uploaded file object
        class FakeFile:
            def __init__(self, path):
                self.name = path

        fake_file = FakeFile(str(pdf_file))
        chunks = processor._process_file(fake_file)

        if not chunks:
            logger.error(f"❌ No chunks produced from {pdf_path}")
            return False

        logger.info(f"✓ Extracted {len(chunks)} chunks")

        # 2. Index in ChromaDB
        logger.info("📚 Indexing in ChromaDB...")
        retriever_builder = RetrieverBuilder()

        collections_to_index = {collection_name: chunks}
        retriever = retriever_builder.build_retriever(
            collections_to_index=collections_to_index,
            selected_existing=None
        )

        logger.info(f"✅ SUCCESS! Document indexed as: '{collection_name}'")
        logger.info(f"   • Chunks: {len(chunks)}")
        logger.info(f"   • Title: {title}")
        logger.info(f"\n🔍 To query this index:")
        logger.info(f"   python scripts/search_by_title.py query '{collection_name}' 'your question'")
        logger.info(f"\n📋 To list all indexed documents:")
        logger.info(f"   python scripts/search_by_title.py list")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to index: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload and index a PDF with document title as collection name"
    )
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("-t", "--title", help="Custom document title (optional)")

    args = parser.parse_args()

    success = upload_and_index(args.pdf_path, args.title)
    sys.exit(0 if success else 1)
