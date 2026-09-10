"""DocChat RAG — Relevance checker agent (decides if retrieved docs can answer the question)."""
from langchain_ollama import ChatOllama
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class RelevanceChecker:
    """Classify whether retrieved documents can answer a user's question."""

    def __init__(self):
        """Initialize ChatOllama for relevance classification."""
        logger.info(f"Initializing RelevanceChecker with model='{settings.OLLAMA_TEXT_MODEL}'")

        self.model = ChatOllama(
            model=settings.OLLAMA_TEXT_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.0,  # Deterministic for classification
            top_p=settings.OLLAMA_TOP_P,
            num_predict=10  # Very short response expected
        )
        logger.info("✓ RelevanceChecker initialized")

    def check(self, question: str, retriever, k: int = 3) -> str:
        """
        Retrieve relevant documents and classify their relevance to the question.

        Args:
            question: User's question
            retriever: LangChain retriever (hybrid BM25+vector)
            k: Number of top documents to use for classification

        Returns:
            "CAN_ANSWER", "PARTIAL", or "NO_MATCH"
        """
        logger.debug(f"RelevanceChecker.check(question='{question}', k={k})")

        try:
            # Retrieve top documents
            top_docs = retriever.invoke(question)
            if not top_docs:
                logger.debug("No documents returned from retriever")
                return "NO_MATCH"

            # Combine document content
            document_content = "\n\n".join(doc.page_content for doc in top_docs[:k])

            # Create classification prompt
            prompt = f"""Eres un verificador de relevancia. Clasifica qué tan bien los documentos responden la pregunta.

**Responde SOLO con una etiqueta: CAN_ANSWER, PARTIAL, o NO_MATCH**

- "CAN_ANSWER": Los párrafos contienen información explícita para responder completamente.
- "PARTIAL": Los párrafos mencionan el tema pero no dan detalles completos.
- "NO_MATCH": Los párrafos no discuten el tema de la pregunta.

**Pregunta:** {question}

**Párrafos:** {document_content}

**Respuesta (SOLO la etiqueta):**"""

            # Call LLM
            message = self.model.invoke(prompt)
            llm_response = message.content.strip().upper()

            logger.debug(f"LLM response: '{llm_response}'")

            # Validate response
            valid_labels = {"CAN_ANSWER", "PARTIAL", "NO_MATCH"}
            if llm_response not in valid_labels:
                logger.warning(f"Invalid response '{llm_response}', defaulting to NO_MATCH")
                return "NO_MATCH"

            logger.debug(f"✓ Classification: {llm_response}")
            return llm_response

        except Exception as e:
            logger.error(f"❌ Error in relevance check: {e}", exc_info=True)
            return "NO_MATCH"
