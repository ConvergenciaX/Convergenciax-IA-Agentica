"""DocChat RAG — Verification agent (checks if answer is supported by documents)."""
from langchain_ollama import ChatOllama
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class VerificationAgent:
    """Verify that a generated answer is supported by retrieved documents."""

    def __init__(self):
        """Initialize ChatOllama for answer verification."""
        logger.info(f"Initializing VerificationAgent with model='{settings.OLLAMA_TEXT_MODEL}'")

        self.model = ChatOllama(
            model=settings.OLLAMA_TEXT_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.0,  # Deterministic for verification
            top_p=settings.OLLAMA_TOP_P,
            num_predict=settings.OLLAMA_NUM_PREDICT
        )
        logger.info("✓ VerificationAgent initialized")

    def verify(self, question: str, answer: str, retriever) -> str:
        """
        Verify that the answer is supported by retrieved documents.

        Args:
            question: Original user question
            answer: Generated answer to verify
            retriever: LangChain retriever (hybrid BM25+vector)

        Returns:
            Verification report with findings
        """
        logger.debug(f"VerificationAgent.verify(question='{question}', answer length={len(answer)})")

        try:
            # Retrieve documents to check against
            docs = retriever.invoke(question)
            if not docs:
                logger.warning("No documents available for verification")
                return "Verification: Unable to verify (no documents). Relevant: UNKNOWN"

            context_docs = docs[:settings.MAX_CONTEXT_DOCS]
            context = "\n\n".join([f"[Doc {i+1}] {doc.page_content}"
                                  for i, doc in enumerate(context_docs)])

            # Create verification prompt
            prompt = f"""Eres un verificador de hechos. Verifica si la respuesta proporcionada está soportada por los documentos.

**Tarea:**
1. Comprueba si las afirmaciones de la respuesta están soportadas por los documentos.
2. Identifica contradicciones o afirmaciones no soportadas.
3. Proporciona un breve reporte de verificación.

**Formatea tu respuesta como:**
Soportado: SI/NO/PARCIAL
Relevante: SI/NO
Resumen: [1-2 oraciones sobre lo que encontraste]

**Pregunta:** {question}

**Respuesta Generada:**
{answer}

**Documentos de Apoyo:**
{context}

**Reporte de Verificación:**"""

            # Call LLM
            message = self.model.invoke(prompt)
            report = message.content.strip()

            logger.debug(f"✓ Verification report generated")
            return report

        except Exception as e:
            logger.error(f"❌ Error in verification: {e}", exc_info=True)
            return f"Verification: Error during verification: {str(e)}"
