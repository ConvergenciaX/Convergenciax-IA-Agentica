#!/usr/bin/env python3
"""
Pattern 4: Reflection (Ollama Local) — Auto-Refinement Loop
"""

import configparser
from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import OllamaLLM
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

llm = OllamaLLM(
    model=config.get('ollama', 'model_name', fallback='qwen2.5:7b'),
    base_url=config.get('ollama', 'base_url', fallback='http://localhost:11434'),
)

logger.info(f"✓ Ollama LLM initialized")

class State(TypedDict):
    topic: str
    draft: str
    feedback: str
    iteration: int

def generate_draft(state: State) -> State:
    """Genera borrador inicial o mejorado"""
    if state['iteration'] == 1:
        prompt = f"Escribe un párrafo corto sobre: {state['topic']}"
    else:
        prompt = f"Mejora este texto basándote en la crítica. CRÍTICA: {state['feedback']}\n\nTEXTO: {state['draft']}"

    response = llm.invoke(prompt)
    state["draft"] = response.strip()
    state["iteration"] += 1
    logger.info(f"📝 Borrador {state['iteration']} generado")
    return state

def evaluate_draft(state: State) -> State:
    """Evalúa la calidad del borrador"""
    prompt = f"Critica brevemente este texto (2-3 frases). ¿Es claro, conciso y bien estructurado?\n\n{state['draft']}\n\nCrítica:"
    response = llm.invoke(prompt)
    state["feedback"] = response.strip()
    logger.info(f"🔍 Evaluación completada")
    return state

def should_refine(state: State) -> Literal["refine", "finalize"]:
    """Decide si refinar más o terminar"""
    if state['iteration'] >= 3:
        return "finalize"
    if "excelente" in state['feedback'].lower() or "perfecto" in state['feedback'].lower():
        return "finalize"
    return "refine"

workflow = StateGraph(State)
workflow.add_node("generate", generate_draft)
workflow.add_node("evaluate", evaluate_draft)
workflow.add_node("finalize", lambda s: s)

workflow.set_entry_point("generate")
workflow.add_edge("generate", "evaluate")
workflow.add_conditional_edges("evaluate", should_refine, {
    "refine": "generate",
    "finalize": "finalize"
})
workflow.add_edge("finalize", END)

graph = workflow.compile()

if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("PATRÓN 4: REFLECTION - BUCLE DE REFINAMIENTO (OLLAMA LOCAL)")
    logger.info("="*70)

    result = graph.invoke({
        "topic": "Por qué LangGraph es revolucionario",
        "draft": "",
        "feedback": "",
        "iteration": 1
    })

    print("\n" + "="*70)
    print("RESULTADO FINAL (Refinado):")
    print("="*70)
    print(f"Iteraciones: {result['iteration']}")
    print(f"\n{result['draft']}")
    logger.info("✓ Patrón 4 completado")
