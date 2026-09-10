"""DocChat RAG — Agentic RAG workflow (3-agent pipeline con retry loop)."""
from typing import Dict, Any
from .research_agent import ResearchAgent
from .verification_agent import VerificationAgent
from .relevance_checker import RelevanceChecker
import logging

logger = logging.getLogger(__name__)


class AgentWorkflow:
    """Orquestar relevancia → investigación → verificación → (opcionalmente re-investigar)."""

    def __init__(self):
        """Inicializa los tres agentes."""
        logger.info("Inicializando AgentWorkflow")
        self.researcher = ResearchAgent()
        self.verifier = VerificationAgent()
        self.relevance_checker = RelevanceChecker()
        logger.info("✓ AgentWorkflow inicializado")

    def full_pipeline(self, question: str, retriever: Any) -> Dict:
        """
        Ejecuta el pipeline RAG agéntico completo.

        Flujo:
        1. check_relevance: ¿Los documentos responden la pregunta?
        2. research: Generar respuesta basada en documentos
        3. verification: ¿La respuesta está soportada? Si no, volver a 2 (máx 1x)

        Args:
            question: Pregunta del usuario
            retriever: Recuperador híbrido (BM25 + vector)

        Returns:
            dict con "draft_answer" y "verification_report"
        """
        logger.info(f"Iniciando pipeline completo: '{question}'")

        try:
            # Paso 1: Verificar relevancia
            logger.debug("→ Paso 1: check_relevance")
            classification = self.relevance_checker.check(
                question=question,
                retriever=retriever,
                k=20
            )

            if classification == "NO_MATCH":
                logger.debug("  Resultado: NO_MATCH → finalizando")
                return {
                    "draft_answer": "Esta pregunta no está relacionada con los documentos. Por favor, haz otra pregunta.",
                    "verification_report": "Relevancia: NO"
                }

            # Paso 2: Investigación
            logger.debug("→ Paso 2: research")
            draft_answer = self.researcher.research(
                question=question,
                retriever=retriever
            )
            logger.debug(f"  Respuesta generada ({len(draft_answer)} caracteres)")

            # Paso 3: Verificación
            logger.debug("→ Paso 3: verification")
            verification_report = self.verifier.verify(
                question=question,
                answer=draft_answer,
                retriever=retriever
            )

            # Paso 4: Decidir si re-investigar
            if "Soportado: NO" in verification_report or "Relevant: NO" in verification_report:
                logger.debug("  Verificación falló → re-investigando (intento 1)")
                draft_answer = self.researcher.research(
                    question=question,
                    retriever=retriever
                )
                verification_report = self.verifier.verify(
                    question=question,
                    answer=draft_answer,
                    retriever=retriever
                )

            logger.info("✓ Pipeline completado exitosamente")
            return {
                "draft_answer": draft_answer,
                "verification_report": verification_report
            }

        except Exception as e:
            logger.error(f"❌ Pipeline falló: {e}", exc_info=True)
            raise
