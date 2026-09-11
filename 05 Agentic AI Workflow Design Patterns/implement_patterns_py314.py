#!/usr/bin/env python3
"""
Implement Workflow Patterns with LangGraph — Ollama Local (Python 3.14)

Convertido del notebook IBM Skills Network (Kunal Makwana)
- LLM Original: OpenAI gpt-4o-mini → Ollama Local
- Python 3.14+ compatible
- Todo parametrizable desde config.ini
- Infraestructura declarada (config.ini, logging, etc.)

Uso:
    python implement_patterns_py314.py

    O ejecutar patrones individuales:
    python implement_patterns_py314.py --pattern 1
    python implement_patterns_py314.py --pattern 2
    python implement_patterns_py314.py --pattern 3
"""

import sys
import os
import configparser
import logging
import argparse
from typing import Literal, Annotated
import operator

# LangChain + LangGraph
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import OllamaLLM

# ═══════════════════════════════════════════════════════════════════════════
# INFRAESTRUCTURA: Configuración centralizada
# ═══════════════════════════════════════════════════════════════════════════

def setup_infrastructure() -> tuple:
    """Configura infraestructura: config.ini, logging, LLM"""

    # Cargar config.ini
    config = configparser.ConfigParser()
    config_path = 'config.ini'

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"config.ini no encontrado en {os.getcwd()}")

    config.read(config_path)

    # Configurar logging
    log_dir = config.get('logging', 'log_dir', fallback='logs')
    log_file = config.get('logging', 'log_file', fallback='logs/patterns.log')
    log_level = config.get('logging', 'level', fallback='INFO')

    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    # Inicializar Ollama LLM
    llm = OllamaLLM(
        model=config.get('ollama', 'model_name', fallback='qwen2.5:7b'),
        base_url=config.get('ollama', 'base_url', fallback='http://localhost:11434'),
        temperature=float(config.get('ollama', 'temperature', fallback='0.7')),
    )

    logger.info("="*70)
    logger.info("INFRAESTRUCTURA INICIALIZADA")
    logger.info("="*70)
    logger.info(f"Python: {sys.version}")
    logger.info(f"Config: {config_path}")
    logger.info(f"Logging: {log_file} (level={log_level})")
    logger.info(f"Ollama LLM: {config.get('ollama', 'model_name')}")
    logger.info(f"Ollama URL: {config.get('ollama', 'base_url')}")
    logger.info("="*70 + "\n")

    return config, llm, logger

# ═══════════════════════════════════════════════════════════════════════════
# PATRÓN 1: PROMPT CHAINING
# ═══════════════════════════════════════════════════════════════════════════

class ChainState(TypedDict):
    """Estado para Prompt Chaining: Job Description → Resume → Cover Letter"""
    job_description: str
    resume_summary: str
    cover_letter: str

def pattern_1_prompt_chaining(llm, logger) -> None:
    """
    Patrón 1: PROMPT CHAINING

    Descripción: Tareas complejas se descomponen en pasos secuenciales.
    Caso de uso: Job Application Assistant
    - Paso 1: Extraer requisitos del job description y generar resume summary
    - Paso 2: Usar resume summary para generar cover letter
    """

    logger.info("\n" + "="*70)
    logger.info("PATRÓN 1: PROMPT CHAINING (Job Application Assistant)")
    logger.info("="*70 + "\n")

    # Definir nodos
    def generate_resume_summary(state: ChainState) -> ChainState:
        """Nodo 1: Resume Summary Generator"""
        logger.info("📝 Ejecutando: generate_resume_summary")

        prompt = f"""You're a resume assistant. Read the following job description and summarize
the key qualifications and experience the ideal candidate should have, phrased as if from
the perspective of a strong applicant's resume summary.

Job Description:
{state['job_description']}

Resume Summary (2-3 sentences):
"""
        response = llm.invoke(prompt).strip()
        state["resume_summary"] = response
        logger.info(f"✓ Resume generado ({len(response)} caracteres)")
        return state

    def generate_cover_letter(state: ChainState) -> ChainState:
        """Nodo 2: Cover Letter Generator"""
        logger.info("📝 Ejecutando: generate_cover_letter")

        prompt = f"""You're a cover letter writing assistant. Using the resume summary below,
write a professional and personalized cover letter for the following job.

Resume Summary:
{state['resume_summary']}

Job Description:
{state['job_description']}

Cover Letter (2-3 paragraphs):
"""
        response = llm.invoke(prompt).strip()
        state["cover_letter"] = response
        logger.info(f"✓ Cover letter generado ({len(response)} caracteres)")
        return state

    # Construir workflow
    workflow = StateGraph(ChainState)
    workflow.add_node("generate_resume_summary", generate_resume_summary)
    workflow.add_node("generate_cover_letter", generate_cover_letter)

    workflow.set_entry_point("generate_resume_summary")
    workflow.add_edge("generate_resume_summary", "generate_cover_letter")
    workflow.add_edge("generate_cover_letter", END)

    app = workflow.compile()

    # Ejecutar
    input_state = {
        "job_description": """We are looking for a data scientist with experience in machine learning,
NLP, and Python. Prior work with large datasets and experience deploying models into production is required.""",
        "resume_summary": "",
        "cover_letter": ""
    }

    logger.info("Ejecutando workflow...")
    result = app.invoke(input_state)

    print("\n" + "="*70)
    print("RESULTADOS - PATRÓN 1: PROMPT CHAINING")
    print("="*70)
    print("\n📋 RESUME SUMMARY:")
    print(result['resume_summary'])
    print("\n💌 COVER LETTER:")
    print(result['cover_letter'])
    logger.info("✓ Patrón 1 completado exitosamente\n")

# ═══════════════════════════════════════════════════════════════════════════
# PATRÓN 2: ROUTING
# ═══════════════════════════════════════════════════════════════════════════

class RouterState(TypedDict):
    """Estado para Routing: Input → Clasificador → Manejador especializado"""
    user_input: str
    task_type: str
    output: str

def pattern_2_routing(llm, logger) -> None:
    """
    Patrón 2: ROUTING

    Descripción: Clasifica entrada y la enruta al handler apropiad
    Caso de uso: Task Classifier (Summarize vs Translate)
    """

    logger.info("\n" + "="*70)
    logger.info("PATRÓN 2: ROUTING (Task Classifier)")
    logger.info("="*70 + "\n")

    def router_node(state: RouterState) -> RouterState:
        """Clasificador: Decide si es summarize o translate"""
        logger.info("🚦 Ejecutando: router_node (clasificador)")

        prompt = f"""You are an AI task classifier.

Decide whether the user wants to:
- "summarize" a passage
- or "translate" text into French

Respond with ONLY one word: 'summarize' or 'translate'.

User Input: "{state['user_input']}"

Answer:"""

        response = llm.invoke(prompt).strip().lower()
        task_type = "summarize" if "summarize" in response else "translate"
        state["task_type"] = task_type
        logger.info(f"✓ Tarea clasificada como: {task_type}")
        return state

    def router(state: RouterState) -> Literal["summarize", "translate"]:
        """Función router: retorna el tipo de tarea"""
        return state["task_type"]

    def summarize_node(state: RouterState) -> RouterState:
        """Manejador: Summarize"""
        logger.info("📝 Ejecutando: summarize_node")

        prompt = f"Please provide a concise summary of the following passage:\n\n{state['user_input']}"
        response = llm.invoke(prompt).strip()
        state["output"] = response
        logger.info(f"✓ Resumen generado ({len(response)} caracteres)")
        return state

    def translate_node(state: RouterState) -> RouterState:
        """Manejador: Translate"""
        logger.info("🌍 Ejecutando: translate_node")

        prompt = f"Translate the following text to French:\n\n{state['user_input']}"
        response = llm.invoke(prompt).strip()
        state["output"] = response
        logger.info(f"✓ Traducción generada ({len(response)} caracteres)")
        return state

    # Construir workflow
    workflow = StateGraph(RouterState)
    workflow.add_node("router", router_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("translate", translate_node)

    workflow.set_entry_point("router")
    workflow.add_conditional_edges("router", router, {
        "summarize": "summarize",
        "translate": "translate"
    })
    workflow.set_finish_point("summarize")
    workflow.set_finish_point("translate")

    app = workflow.compile()

    # Test 1: Translation
    logger.info("Ejecutando Test 1: Translation")
    input1 = {"user_input": "Can you translate this sentence: I love programming?", "task_type": "", "output": ""}
    result1 = app.invoke(input1)

    print("\n" + "="*70)
    print("RESULTADOS - PATRÓN 2: ROUTING (Test 1: Translation)")
    print("="*70)
    print(f"Task Type: {result1['task_type'].upper()}")
    print(f"Output:\n{result1['output']}")

    # Test 2: Summarization
    logger.info("Ejecutando Test 2: Summarization")
    input2 = {"user_input": "Can you summarize: I love programming so much it's the best thing ever. All I want is programming.", "task_type": "", "output": ""}
    result2 = app.invoke(input2)

    print("\n" + "="*70)
    print("RESULTADOS - PATRÓN 2: ROUTING (Test 2: Summarization)")
    print("="*70)
    print(f"Task Type: {result2['task_type'].upper()}")
    print(f"Output:\n{result2['output']}")

    logger.info("✓ Patrón 2 completado exitosamente\n")

# ═══════════════════════════════════════════════════════════════════════════
# PATRÓN 3: PARALLELIZATION
# ═══════════════════════════════════════════════════════════════════════════

class ParallelState(TypedDict):
    """Estado para Parallelization con reducer para acumular resultados"""
    text: str
    french: str
    spanish: str
    japanese: str
    combined_output: str

def pattern_3_parallelization(llm, logger) -> None:
    """
    Patrón 3: PARALLELIZATION

    Descripción: Múltiples tareas independientes ejecutan al mismo tiempo
    Caso de uso: Multilingual Translation (3 idiomas en paralelo)
    """

    logger.info("\n" + "="*70)
    logger.info("PATRÓN 3: PARALLELIZATION (Multilingual Translator)")
    logger.info("="*70 + "\n")

    def translate_french(state: ParallelState) -> dict:
        """Tarea paralela 1: Traducir a francés"""
        logger.info("🇫🇷 Ejecutando: translate_french (paralelo)")
        response = llm.invoke(f"Translate the following text to French:\n\n{state['text']}")
        logger.info(f"✓ Francés completado ({len(response)} caracteres)")
        return {"french": response.strip()}

    def translate_spanish(state: ParallelState) -> dict:
        """Tarea paralela 2: Traducir a español"""
        logger.info("🇪🇸 Ejecutando: translate_spanish (paralelo)")
        response = llm.invoke(f"Translate the following text to Spanish:\n\n{state['text']}")
        logger.info(f"✓ Español completado ({len(response)} caracteres)")
        return {"spanish": response.strip()}

    def translate_japanese(state: ParallelState) -> dict:
        """Tarea paralela 3: Traducir a japonés"""
        logger.info("🇯🇵 Ejecutando: translate_japanese (paralelo)")
        response = llm.invoke(f"Translate the following text to Japanese:\n\n{state['text']}")
        logger.info(f"✓ Japonés completado ({len(response)} caracteres)")
        return {"japanese": response.strip()}

    def aggregator(state: ParallelState) -> dict:
        """Nodo agregador: Combina todas las traducciones"""
        logger.info("📋 Ejecutando: aggregator (sintetiza)")
        combined = f"Original Text: {state['text']}\n\n"
        combined += f"French: {state['french']}\n\n"
        combined += f"Spanish: {state['spanish']}\n\n"
        combined += f"Japanese: {state['japanese']}\n"
        logger.info("✓ Agregación completada")
        return {"combined_output": combined}

    # Construir workflow con edges paralelos
    graph = StateGraph(ParallelState)
    graph.add_node("translate_french", translate_french)
    graph.add_node("translate_spanish", translate_spanish)
    graph.add_node("translate_japanese", translate_japanese)
    graph.add_node("aggregator", aggregator)

    # Conexiones paralelas desde START
    graph.add_edge(START, "translate_french")
    graph.add_edge(START, "translate_spanish")
    graph.add_edge(START, "translate_japanese")

    # Convergencia en agregador
    graph.add_edge("translate_french", "aggregator")
    graph.add_edge("translate_spanish", "aggregator")
    graph.add_edge("translate_japanese", "aggregator")

    # Fin
    graph.add_edge("aggregator", END)

    app = graph.compile()

    # Ejecutar
    input_text = {
        "text": "Good morning! I hope you have a wonderful day.",
        "french": "",
        "spanish": "",
        "japanese": "",
        "combined_output": ""
    }

    logger.info("Ejecutando workflow (3 traducciones en paralelo)...")
    result = app.invoke(input_text)

    print("\n" + "="*70)
    print("RESULTADOS - PATRÓN 3: PARALLELIZATION")
    print("="*70)
    print(result['combined_output'])

    logger.info("✓ Patrón 3 completado exitosamente\n")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Ejecuta los patrones"""

    # Setup infraestructura
    config, llm, logger = setup_infrastructure()

    # Parse argumentos
    parser = argparse.ArgumentParser(
        description="Implement Workflow Patterns with LangGraph (Ollama Local)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python implement_patterns_py314.py              # Ejecuta todos los patrones
  python implement_patterns_py314.py --pattern 1  # Solo patrón 1
  python implement_patterns_py314.py --pattern 2  # Solo patrón 2
        """
    )
    parser.add_argument('--pattern', type=int, choices=[1, 2, 3],
                       help='Ejecutar patrón específico (1, 2, o 3)')

    args = parser.parse_args()

    try:
        if args.pattern is None:
            # Ejecutar todos
            pattern_1_prompt_chaining(llm, logger)
            pattern_2_routing(llm, logger)
            pattern_3_parallelization(llm, logger)
        elif args.pattern == 1:
            pattern_1_prompt_chaining(llm, logger)
        elif args.pattern == 2:
            pattern_2_routing(llm, logger)
        elif args.pattern == 3:
            pattern_3_parallelization(llm, logger)

        logger.info("✓ TODOS LOS PATRONES COMPLETADOS EXITOSAMENTE")
        print("\n✓ TODOS LOS PATRONES COMPLETADOS EXITOSAMENTE")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
