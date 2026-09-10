#!/usr/bin/env python3
"""
Descargar modelos de Docling (layout, tablas, detectores) UNA SOLA VEZ a
una carpeta local del proyecto, para que RAG-AgentAI corra 100% offline
después sin contactar HuggingFace.

Uso:
    python scripts/download_local_models.py

Requisitos:
    - Internet disponible (esta descarga se hace una sola vez)
    - Se requiere espacio en disco: ~1.5 GB para modelos de Docling
    - Después de esto, la carpeta ./models/docling/ se cachea permanentemente

Nota: EasyOCR descarga sus modelos en su primer uso real (cuando procesa
un PDF que contiene imágenes). Ver SETUP.md para el paso manual.
"""
import sys
from pathlib import Path

try:
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
except ImportError:
    print("❌ Error: Docling no está instalado. Instala con:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

MODELS_DIR = Path("./models/docling")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("📥 Descargando modelos de Docling para uso local (offline)")
print("=" * 70)
print(f"\nModelos a descargar:")
print("  - Layout Model (detección de estructura en PDFs)")
print("  - Table Structure Model (reconocimiento de tablas)")
print("  - Page Assemble Model (ensamblaje de página)")
print("  - Otros modelos de Docling v2.1.0")
print(f"\nDestino: {MODELS_DIR.resolve()}")
print(f"Tamaño estimado: ~1.5 GB")
print(f"Tiempo estimado: 5-10 minutos (depende de velocidad de red)\n")

try:
    print("⏳ Descargando... (esto puede tomar unos minutos)")
    path = StandardPdfPipeline.download_models_hf(
        local_dir=MODELS_DIR,
        force=False  # No re-descargar si ya existen
    )
    print(f"\n✅ SUCCESS!")
    print(f"   Modelos guardados en: {path}")
    print(f"   Tamaño: {sum(p.stat().st_size for p in Path(path).rglob('*')) / (1024**3):.2f} GB")

    print("\n" + "=" * 70)
    print("⏭️  PRÓXIMOS PASOS:")
    print("=" * 70)
    print("""
1. Pre-cachear modelos de EasyOCR (OCR en imágenes de PDFs):

   - Edita config.ini: do_ocr = true (debe estar ya)
   - Sube un PDF de ejemplo (idealmente con imágenes/gráficos)
   - La primera carga será lenta (~30-60 seg) mientras EasyOCR descarga modelos
   - Edita config.ini: do_ocr = true, download_enabled = false

   (Ver SETUP.md → "Paso 2.5" para detalles)

2. VerifiCA que todo funciona sin internet:

   - Abre 2 terminales: una con ChromaDB, otra con app.py
   - DESCONECTA LA RED (modo avión, desenchufa WiFi, etc.)
   - Sube un PDF nuevo
   - Confirma que se procesa correctamente sin errores de conexión

3. Listo para producción 100% local ✅

Para detalles técnicos:
   Ver: document_processor/file_handler.py → DocumentProcessor.__init__
   Ver: config.ini → [document_processor]
   Ver: SETUP.md → Paso 2.5 (pre-configuración)
""")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERROR durante descarga: {e}")
    print("\nDiagnóstico:")
    print("  - ¿Hay internet disponible?")
    print("  - ¿Puedes acceder a huggingface.co?")
    print("  - ¿Hay suficiente espacio en disco (~2 GB)?")
    print("\nIntenta de nuevo después de resolver el problema anterior.")
    sys.exit(1)
