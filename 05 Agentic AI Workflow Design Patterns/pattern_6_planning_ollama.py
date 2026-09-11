#!/usr/bin/env python3
"""
Pattern 6: Planning (Ollama Local) — Explicit plan then execution
"""

import configparser
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
    goal: str
    plan: str
    execution_results: str
    final_analysis: str

def create_plan(state: State) -> State:
    """Crea un plan explícito para alcanzar el objetivo"""
    prompt = f"""Crea un plan detallado de 5 pasos para: {state['goal']}

Formato:
1. Paso 1: [descripción]
2. Paso 2: [descripción]
... etc"""

    response = llm.invoke(prompt)
    state["plan"] = response.strip()
    logger.info(f"📋 Plan creado")
    print(f"📋 PLAN:\n{state['plan']}")
    return state

def execute_plan(state: State) -> State:
    """Ejecuta el plan (simulado)"""
    prompt = f"""Simula ejecutar este plan paso a paso y reporta resultados:

PLAN:
{state['plan']}

Formato: "Paso 1: [resultado]... Paso 2: [resultado]..." etc"""

    response = llm.invoke(prompt)
    state["execution_results"] = response.strip()
    logger.info(f"⚙️ Plan ejecutado")
    return state

def analyze_results(state: State) -> State:
    """Analiza resultados y extrae aprendizajes"""
    prompt = f"""Analiza estos resultados de ejecución y extrae 3 aprendizajes clave:

RESULTADOS:
{state['execution_results']}

Formato: "1. Aprendizaje 1..., 2. Aprendizaje 2..., 3. Aprendizaje 3..." """

    response = llm.invoke(prompt)
    state["final_analysis"] = response.strip()
    logger.info(f"🔍 Análisis completado")
    return state

workflow = StateGraph(State)
workflow.add_node("plan", create_plan)
workflow.add_node("execute", execute_plan)
workflow.add_node("analyze", analyze_results)

workflow.set_entry_point("plan")
workflow.add_edge("plan", "execute")
workflow.add_edge("execute", "analyze")
workflow.add_edge("analyze", END)

graph = workflow.compile()

if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("PATRÓN 6: PLANNING - PLAN EXPLÍCITO + EJECUCIÓN")
    logger.info("="*70)

    goal = "Aprender LangGraph y construir un agente multi-agente"
    result = graph.invoke({
        "goal": goal,
        "plan": "",
        "execution_results": "",
        "final_analysis": ""
    })

    print("\n" + "="*70)
    print("EJECUCIÓN Y ANÁLISIS:")
    print("="*70)
    print(f"\nRESULTADOS:\n{result['execution_results']}")
    print(f"\nAPRENDIZAJES CLAVE:\n{result['final_analysis']}")
    logger.info("✓ Patrón 6 completado")
