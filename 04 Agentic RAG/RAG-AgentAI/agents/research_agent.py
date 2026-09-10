"""DocChat RAG — Research agent (generates answer from retrieved documents)."""
from langchain_ollama import ChatOllama
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Generate a detailed answer from retrieved documents."""

    def __init__(self):
        """Initialize ChatOllama for answer generation."""
        logger.info(f"Initializing ResearchAgent with model='{settings.OLLAMA_TEXT_MODEL}'")

        self.model = ChatOllama(
            model=settings.OLLAMA_TEXT_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3,  # Some creativity for answer variation
            top_p=settings.OLLAMA_TOP_P,
            num_predict=settings.OLLAMA_NUM_PREDICT
        )
        logger.info("✓ ResearchAgent initialized")

    def research(self, question: str, retriever) -> str:
        """
        Generate a detailed answer from retrieved documents.

        Args:
            question: User's question
            retriever: LangChain retriever (hybrid BM25+vector)

        Returns:
            Generated answer based on retrieved documents
        """
        logger.debug(f"ResearchAgent.research(question='{question}')")

        try:
            # Retrieve relevant documents
            docs = retriever.invoke(question)
            if not docs:
                logger.warning("No documents retrieved for research")
                return "No encontré documentos relevantes para responder tu pregunta."

            # Limit context to avoid exceeding token limits
            context_docs = docs[:settings.MAX_CONTEXT_DOCS]
            context = "\n\n".join([f"[Doc {i+1}] {doc.page_content}"
                                  for i, doc in enumerate(context_docs)])

            # Create answer generation prompt
            prompt = f"""Eres un asistente IA útil. Responde la pregunta del usuario SOLO basándote en los documentos proporcionados.

**Instrucciones:**
- Usa solo información de los documentos abajo.
- Sé claro, conciso y bien estructurado.
- Si los documentos no contienen la respuesta, dilo.
- Cita qué documento(s) usaste.

**Pregunta:** {question}

**Documentos:**
{context}

**Respuesta:**"""

            # Call LLM
            message = self.model.invoke(prompt)
            answer = message.content.strip()

            logger.debug(f"✓ Answer generated ({len(answer)} chars)")
            return answer

        except Exception as e:
            logger.error(f"❌ Error in research: {e}", exc_info=True)
            return f"Error generating answer: {str(e)}"
