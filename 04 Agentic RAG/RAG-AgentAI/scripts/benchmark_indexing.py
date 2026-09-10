#!/usr/bin/env python3
"""Benchmark de rendimiento de indexación — identifica cuellos de botella."""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from document_processor.file_handler import DocumentProcessor
from retriever.builder import RetrieverBuilder
from config.settings import settings
from utils.logging import logger

class IndexingBenchmark:
    """Mide performance en cada etapa del indexado."""

    def __init__(self):
        self.timings = {}

    def benchmark_document_processing(self, pdf_path: str):
        """Mide tiempo de parsing + chunking (Docling)."""
        logger.info("\n" + "="*80)
        logger.info("ETAPA 1: PROCESAMIENTO DE DOCUMENTO (Docling + Chunking)")
        logger.info("="*80)

        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            logger.error(f"❌ Archivo no encontrado: {pdf_path}")
            return None

        file_size_mb = pdf_file.stat().st_size / (1024*1024)
        logger.info(f"Archivo: {pdf_file.name} ({file_size_mb:.1f} MB)")

        try:
            processor = DocumentProcessor()

            # Simular uploaded file
            class FakeFile:
                def __init__(self, path):
                    self.name = path

            fake_file = FakeFile(str(pdf_file))

            # Medir tiempo de procesamiento
            start = time.perf_counter()
            collections = processor.process([fake_file])
            elapsed = time.perf_counter() - start

            self.timings["document_processing"] = elapsed

            total_chunks = sum(len(chunks) for chunks in collections.values())
            speed = file_size_mb / elapsed if elapsed > 0 else 0
            chunk_speed = total_chunks / elapsed if elapsed > 0 else 0

            logger.info(f"\n✅ RESULTADOS:")
            logger.info(f"   Tiempo total: {elapsed:.2f}s")
            logger.info(f"   Chunks generados: {total_chunks}")
            logger.info(f"   Velocidad: {speed:.1f} MB/s")
            logger.info(f"   Chunks/segundo: {chunk_speed:.1f}")
            logger.info(f"   Colecciones: {list(collections.keys())}")

            # Desglose por etapa (aproximado)
            logger.info(f"\n📊 DESGLOSE (estimado):")
            logger.info(f"   • Docling parsing: ~{elapsed*0.6:.2f}s (60%)")
            logger.info(f"   • Chunking: ~{elapsed*0.3:.2f}s (30%)")
            logger.info(f"   • Deduplicación: ~{elapsed*0.1:.2f}s (10%)")

            return collections

        except Exception as e:
            logger.error(f"❌ Error procesando: {e}", exc_info=True)
            return None

    def benchmark_embedding(self, collections: dict):
        """Mide tiempo de embeddings (Ollama)."""
        logger.info("\n" + "="*80)
        logger.info("ETAPA 2: GENERACIÓN DE EMBEDDINGS (Ollama)")
        logger.info("="*80)

        try:
            retriever_builder = RetrieverBuilder()

            # Contar chunks
            total_chunks = sum(len(chunks) for chunks in collections.values())
            logger.info(f"Chunks a embebber: {total_chunks}")
            logger.info(f"Modelo embedding: {settings.EMBEDDING_MODEL}")
            logger.info(f"Host Ollama: {settings.OLLAMA_BASE_URL}")

            # Medir solo embedding (sin storage)
            start = time.perf_counter()
            all_docs = []
            for chunks in collections.values():
                all_docs.extend(chunks)

            # Test: embed primer chunk para ver latencia
            test_start = time.perf_counter()
            test_embedding = retriever_builder.embeddings.embed_query(all_docs[0].page_content if all_docs else "test")
            test_elapsed = time.perf_counter() - test_start
            logger.info(f"\n📊 Latencia de embedding (1 chunk):")
            logger.info(f"   Tiempo: {test_elapsed*1000:.1f}ms")
            logger.info(f"   Dimensiones: {len(test_embedding)}")

            # Proyectar tiempo total
            projected_total = test_elapsed * total_chunks
            logger.info(f"\n⏱️  PROYECCIÓN (si embebber secuencialmente):")
            logger.info(f"   Tiempo estimado: {projected_total:.2f}s ({projected_total/60:.1f} minutos)")
            logger.info(f"   Chunks/segundo: {total_chunks/projected_total:.1f}")

            self.timings["embedding_projected"] = projected_total

        except Exception as e:
            logger.error(f"❌ Error midiendo embedding: {e}", exc_info=True)

    def benchmark_indexing_in_chromadb(self, collections: dict):
        """Mide tiempo de indexación en ChromaDB."""
        logger.info("\n" + "="*80)
        logger.info("ETAPA 3: INDEXACIÓN EN CHROMADB")
        logger.info("="*80)

        try:
            retriever_builder = RetrieverBuilder()
            total_chunks = sum(len(chunks) for chunks in collections.values())
            logger.info(f"Chunks a indexar: {total_chunks}")
            logger.info(f"ChromaDB: {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")

            # Medir tiempo real de indexación
            start = time.perf_counter()
            retriever = retriever_builder.build_retriever(
                collections_to_index=collections,
                selected_existing=None
            )
            elapsed = time.perf_counter() - start

            self.timings["chromadb_indexing"] = elapsed

            speed = total_chunks / elapsed if elapsed > 0 else 0
            logger.info(f"\n✅ RESULTADOS:")
            logger.info(f"   Tiempo total: {elapsed:.2f}s")
            logger.info(f"   Chunks/segundo: {speed:.1f}")

        except Exception as e:
            logger.error(f"❌ Error indexando: {e}", exc_info=True)

    def print_summary(self):
        """Imprime resumen de timings y recomendaciones."""
        logger.info("\n\n" + "="*80)
        logger.info("RESUMEN DE RENDIMIENTO")
        logger.info("="*80)

        logger.info("\n⏱️  TIMINGS:")
        total_time = 0
        for stage, elapsed in self.timings.items():
            pct = (elapsed / sum(self.timings.values()) * 100) if self.timings else 0
            logger.info(f"   • {stage}: {elapsed:.2f}s ({pct:.0f}%)")
            total_time += elapsed

        logger.info(f"\n   TOTAL: {total_time:.2f}s")

        # Recomendaciones basadas en timings
        logger.info("\n💡 RECOMENDACIONES DE OPTIMIZACIÓN:")

        if "document_processing" in self.timings:
            doc_time = self.timings["document_processing"]
            if doc_time > 5:
                logger.info("   1. ⚠️  Docling es lento (>5s)")
                logger.info("      → Desactiva OCR si no necesitas (do_ocr=false en config.ini)")
                logger.info("      → Aumenta chunk_size en chunking para menos chunks")
                logger.info("      → Docling ya es muy optimizado; es el parsing de PDF que es CPU-intensive")

        if "embedding_projected" in self.timings:
            emb_time = self.timings["embedding_projected"]
            if emb_time > 10:
                logger.info("   2. ⚠️  Embeddings proyectado es lento (>10s)")
                logger.info("      → Usa embedding model más pequeño: nomic-embed-text (274MB)")
                logger.info("      → Batch embeddings: embebber múltiples chunks en paralelo")
                logger.info("      → Usa GPU para Ollama: ollama_gpu_layers > 0")

        if "chromadb_indexing" in self.timings:
            chroma_time = self.timings["chromadb_indexing"]
            if chroma_time > 5:
                logger.info("   3. ⚠️  ChromaDB es lento (>5s)")
                logger.info("      → Usa ChromaDB en-memory (sin HTTP)")
                logger.info("      → Batch adds: agrupa 100+ embeddings por request")
                logger.info("      → Network latency: asegúrate que ChromaDB esté localhost")

        logger.info("\n🚀 OPCIONES DE MEJORA (en orden de impacto):")
        logger.info("   1. GPU acceleration (Ollama + embeddings model on GPU)")
        logger.info("   2. Batch processing (embebber 32+ chunks en paralelo)")
        logger.info("   3. Smaller embedding model (nomic-embed-text vs mxbai-embed-large)")
        logger.info("   4. Disable OCR (si no necesitas)")
        logger.info("   5. ChromaDB in-memory (en lugar de HTTP client)")

def main():
    """Ejecuta benchmark completo."""
    logger.info("\n\n" + "🧪 BENCHMARK DE INDEXACIÓN RAG-AgentAI".center(80))
    logger.info("="*80)

    # Usar ejemplo PDF
    pdf_path = "examples/Financial Theory with Python.pdf"

    benchmark = IndexingBenchmark()

    # Etapa 1: Document processing
    collections = benchmark.benchmark_document_processing(pdf_path)
    if not collections:
        logger.error("❌ No se pudo procesar el documento")
        return 1

    # Etapa 2: Embedding proyectado
    benchmark.benchmark_embedding(collections)

    # Etapa 3: Indexación en ChromaDB
    benchmark.benchmark_indexing_in_chromadb(collections)

    # Resumen
    benchmark.print_summary()

    logger.info("\n" + "="*80)
    logger.info("✅ BENCHMARK COMPLETADO")
    logger.info("="*80)

    return 0

if __name__ == "__main__":
    sys.exit(main())
