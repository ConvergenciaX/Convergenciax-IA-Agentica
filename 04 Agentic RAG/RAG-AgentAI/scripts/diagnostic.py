#!/usr/bin/env python3
"""Diagnóstico: verifica que todo está listo para indexar."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from config.settings import settings
from utils.logging import logger

def check_ollama():
    """Verifica que Ollama está activo."""
    try:
        resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2)
        if resp.status_code == 200:
            logger.info("✅ Ollama: OK")
            return True
    except Exception as e:
        logger.error(f"❌ Ollama: NO RESPONDE ({e})")
        logger.error(f"   Ejecuta: ollama serve")
        return False

def check_chroma():
    """Verifica que ChromaDB está activo."""
    try:
        resp = requests.get(f"{settings.CHROMA_URL}/api/v2/heartbeat", timeout=2)
        if resp.status_code == 200:
            logger.info("✅ ChromaDB: OK")
            return True
    except Exception as e:
        logger.error(f"❌ ChromaDB: NO RESPONDE ({e})")
        logger.error(f"   Ejecuta: chroma run --host localhost --port 8000 --path ./chroma_data")
        return False

def check_docling_models():
    """Verifica que los modelos de Docling existen."""
    docling_path = Path(settings.DOCLING_ARTIFACTS_PATH)
    if docling_path.exists() and list(docling_path.glob("*")) :
        logger.info(f"✅ Docling models: OK ({docling_path})")
        return True
    else:
        logger.warning(f"⚠️  Docling models: NO ENCONTRADOS en {docling_path}")
        logger.warning(f"   Ejecuta: python scripts/download_local_models.py (requiere internet)")
        return False

def check_config():
    """Verifica la configuración."""
    logger.info(f"✅ Config:")
    logger.info(f"   • do_ocr: {settings.DOCLING_DO_OCR}")
    logger.info(f"   • Ollama: {settings.OLLAMA_BASE_URL}")
    logger.info(f"   • Chroma: {settings.CHROMA_URL}")
    logger.info(f"   • Embedding model: {settings.EMBEDDING_MODEL}")
    logger.info(f"   • Text model: {settings.OLLAMA_TEXT_MODEL}")

def main():
    logger.info("=" * 80)
    logger.info("🔧 DIAGNÓSTICO: Verificando que todo está listo para indexar")
    logger.info("=" * 80)

    checks = {
        "Ollama": check_ollama(),
        "ChromaDB": check_chroma(),
        "Docling models": check_docling_models(),
    }

    check_config()

    logger.info("=" * 80)

    if all(checks.values()):
        logger.info("✅ TODO LISTO. Ahora ejecuta:")
        logger.info(f"   python scripts/upload_and_index.py 'examples/Financial Theory with Python.pdf'")
        return True
    else:
        logger.error("❌ Faltan componentes. Ver arriba.")
        return False

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
