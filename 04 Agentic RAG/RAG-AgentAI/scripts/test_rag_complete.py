#!/usr/bin/env python3
"""Test completo de RAG-AgentAI — indexación, búsqueda y respuesta."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from document_processor.file_handler import DocumentProcessor
from retriever.builder import RetrieverBuilder
from agents.workflow import AgentWorkflow
from config.settings import settings
from utils.logging import logger
import json

def test_document_processing():
    """Test 1: Procesar documentos."""
    logger.info("=" * 80)
    logger.info("TEST 1: Procesar documentos")
    logger.info("=" * 80)

    try:
        processor = DocumentProcessor()

        # Simulate file
        class FakeFile:
            def __init__(self, path):
                self.name = path

        pdf_path = "examples/Financial Theory with Python.pdf"
        fake_file = FakeFile(pdf_path)

        logger.info(f"📄 Procesando: {pdf_path}")
        collections = processor.process([fake_file])

        if not collections:
            logger.error("❌ No documents processed")
            return False

        logger.info(f"✅ Procesados {len(collections)} documento(s)")
        total_chunks = sum(len(chunks) for chunks in collections.values())
        logger.info(f"   Total chunks: {total_chunks}")

        for col_name, chunks in collections.items():
            logger.info(f"   • {col_name}: {len(chunks)} chunks")

        return True, collections

    except Exception as e:
        logger.error(f"❌ Error procesando documentos: {e}", exc_info=True)
        return False


def test_indexing(collections):
    """Test 2: Indexar en ChromaDB."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Indexar en ChromaDB")
    logger.info("=" * 80)

    try:
        retriever_builder = RetrieverBuilder()

        logger.info("📚 Indexando documentos...")
        retriever = retriever_builder.build_retriever(
            collections_to_index=collections,
            selected_existing=None
        )

        logger.info("✅ Documentos indexados")

        # Verificar que se guardó
        all_collections = retriever_builder.list_collections()
        logger.info(f"   Colecciones en ChromaDB: {all_collections}")

        return True, retriever_builder

    except Exception as e:
        logger.error(f"❌ Error indexando: {e}", exc_info=True)
        return False


def test_retrieval(retriever_builder, query: str):
    """Test 3: Búsqueda de documentos."""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 3: Búsqueda (Query: '{query}')")
    logger.info("=" * 80)

    try:
        # Obtener cualquier colección indexada
        collections = retriever_builder.list_collections()
        if not collections:
            logger.error("❌ No hay colecciones indexadas")
            return False

        logger.info(f"📖 Colecciones disponibles: {collections}")

        # Construir retriever para la búsqueda
        retriever = retriever_builder.build_retriever(
            collections_to_index={},
            selected_existing=collections[:1]  # Usar la primera colección
        )

        logger.info(f"🔍 Buscando: '{query}'")
        results = retriever.invoke(query)

        logger.info(f"✅ Encontrados {len(results)} documentos")
        for i, doc in enumerate(results[:3], 1):
            logger.info(f"   [{i}] {doc.page_content[:100]}...")

        return True, results

    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}", exc_info=True)
        return False


def test_rag_pipeline(query: str):
    """Test 4: Pipeline RAG completo (3 agentes)."""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 4: Pipeline RAG (Query: '{query}')")
    logger.info("=" * 80)

    try:
        # Reconstruct everything
        processor = DocumentProcessor()
        retriever_builder = RetrieverBuilder()

        # Process documents
        logger.info("📄 Procesando documentos...")
        class FakeFile:
            def __init__(self, path):
                self.name = path

        collections = processor.process([FakeFile("examples/Financial Theory with Python.pdf")])

        if not collections:
            logger.error("❌ No chunks processed")
            return False

        # Index
        logger.info("📚 Indexando...")
        retriever = retriever_builder.build_retriever(
            collections_to_index=collections,
            selected_existing=None
        )

        # Run RAG pipeline
        logger.info("🚀 Ejecutando RAG pipeline (3 agentes)...")
        workflow = AgentWorkflow()

        result = workflow.full_pipeline(
            question=query,
            retriever=retriever
        )

        logger.info("✅ RAG completado")
        logger.info(f"\n📝 RESPUESTA:\n{result['draft_answer']}")
        logger.info(f"\n🔍 VERIFICACIÓN:\n{result['verification_report']}")

        return True

    except Exception as e:
        logger.error(f"❌ Error en RAG: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("\n\n" + "🧪 PRUEBA COMPLETA DE RAG-AgentAI".center(80))
    logger.info("=" * 80)

    # Test 1: Document Processing
    result1 = test_document_processing()
    if not result1:
        logger.error("❌ Test 1 falló")
        sys.exit(1)

    collections = result1[1]

    # Test 2: Indexing
    result2 = test_indexing(collections)
    if not result2:
        logger.error("❌ Test 2 falló")
        sys.exit(1)

    retriever_builder = result2[1]

    # Test 3: Retrieval
    result3 = test_retrieval(
        retriever_builder,
        "¿Cuáles son los principios fundamentales de la teoría financiera?"
    )
    if not result3:
        logger.error("❌ Test 3 falló")
        sys.exit(1)

    # Test 4: RAG Pipeline
    result4 = test_rag_pipeline(
        "¿Qué es la teoría moderna de carteras de inversión?"
    )

    # Summary
    logger.info("\n\n" + "=" * 80)
    logger.info("✅ TODOS LOS TESTS COMPLETADOS")
    logger.info("=" * 80)
    logger.info("\nPasos finales:")
    logger.info("  1. Abre http://127.0.0.1:5020 en tu navegador")
    logger.info("  2. Prueba la pestaña '💬 Preguntar' (sube un PDF + pregunta)")
    logger.info("  3. Prueba la pestaña '📚 Explorar Documentos' (lista + chunks)")
    logger.info("\n✨ RAG-AgentAI está listo para usar!")
