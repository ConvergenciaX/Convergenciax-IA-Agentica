#!/usr/bin/env python3
"""Pre-descargar modelos de EasyOCR para operación offline con imágenes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from utils.logging import logger

def download_easyocr_models():
    """Descarga modelos de EasyOCR localmente para OCR offline."""
    try:
        import easyocr

        ocr_models_path = Path(settings.DOCLING_OCR_MODELS_PATH)
        ocr_models_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"📥 Descargando modelos de EasyOCR...")
        logger.info(f"   Destino: {ocr_models_path}")
        logger.info(f"   Esto puede tomar 5-10 minutos la primera vez...")

        # EasyOCR reader descargará los modelos a model_storage_directory
        reader = easyocr.Reader(
            ['en', 'es'],  # Inglés + Español
            model_storage_directory=str(ocr_models_path),
            gpu=True  # Usar GPU si está disponible
        )

        logger.info(f"✅ Modelos de EasyOCR descargados exitosamente en: {ocr_models_path}")

        # Verificar que existen
        model_files = list(ocr_models_path.glob("*"))
        logger.info(f"   Total de archivos descargados: {len(model_files)}")
        for f in sorted(model_files)[:5]:
            logger.info(f"     • {f.name}")
        if len(model_files) > 5:
            logger.info(f"     ... y {len(model_files) - 5} más")

        logger.info(f"\n✅ SUCCESS! Ahora puedes usar OCR en modo offline.")
        logger.info(f"   Cambia en config.ini: do_ocr = true")
        logger.info(f"   Y reinicia la app para usar OCR con imágenes.\n")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to download EasyOCR models: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🔧 Descargando modelos de EasyOCR para OCR offline")
    logger.info("=" * 80)

    success = download_easyocr_models()

    logger.info("=" * 80)

    sys.exit(0 if success else 1)
