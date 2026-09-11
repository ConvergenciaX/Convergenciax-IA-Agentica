#!/usr/bin/env python3
"""
Pattern 3: Parallelization (Ollama Local)

Patrón 3: Paralelización
Ejecuta múltiples tareas independientes simultáneamente.

Adaptado para Ollama local — 100% offline, parametrizable desde config.ini
"""

import configparser
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import OllamaLLM
import operator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

llm = OllamaLLM(
    model=config.get('ollama', 'model_name', fallback='qwen2.5:7b'),
    base_url=config.get('ollama', 'base_url', fallback='http://localhost:11434'),
    temperature=float(config.get('ollama', 'temperature', fallback='0.7')),
)

logger.info(f"✓ Ollama LLM initialized: {config.get('ollama', 'model_name')}")

# State with reducer for parallel results
class State(TypedDict):
    topic: str
    summaries: Annotated[list, operator.add]

# Parallel nodes (independent tasks)
def summarize_technical(state: State) -> dict:
    """Resumen técnico"""
    prompt = f"Crea un resumen TÉCNICO de {state['topic']} en 2 párrafos."
    response = llm.invoke(prompt).strip()
    logger.info("📊 Resumen técnico completado")
    return {"summaries": [f"TÉCNICO:\n{response}"]}

def summarize_business(state: State) -> dict:
    """Resumen empresarial"""
    prompt = f"Crea un resumen de IMPACTO EMPRESARIAL de {state['topic']} en 2 párrafos."
    response = llm.invoke(prompt).strip()
    logger.info("💼 Resumen empresarial completado")
    return {"summaries": [f"EMPRESARIAL:\n{response}"]}

def summarize_practical(state: State) -> dict:
    """Resumen práctico"""
    prompt = f"Crea un resumen de APLICACIÓN PRÁCTICA de {state['topic']} en 2 párrafos."
    response = llm.invoke(prompt).strip()
    logger.info("🛠️ Resumen práctico completado")
    return {"summaries": [f"PRÁCTICO:\n{response}"]}

# Aggregator (runs after all parallel tasks)
def aggregate_summaries(state: State) -> dict:
    """Combina todos los resúmenes"""
    aggregated = f"Perspectivas de {state['topic']}:\n\n" + "\n\n".join(state['summaries'])
    logger.info("✓ Resúmenes agregados")
    return {"summaries": [aggregated]}

# Build graph
workflow = StateGraph(State)
workflow.add_node("technical", summarize_technical)
workflow.add_node("business", summarize_business)
workflow.add_node("practical", summarize_practical)
workflow.add_node("aggregator", aggregate_summaries)

# Parallel execution from START
workflow.add_edge(START, "technical")
workflow.add_edge(START, "business")
workflow.add_edge(START, "practical")

# Converge at aggregator
workflow.add_edge("technical", "aggregator")
workflow.add_edge("business", "aggregator")
workflow.add_edge("practical", "aggregator")
workflow.add_edge("aggregator", END)

graph = workflow.compile()

if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("PATRÓN 3: PARALELIZACIÓN (OLLAMA LOCAL)")
    logger.info("="*70)

    topic = "Inteligencia Artificial en el siglo XXI"
    logger.info(f"Ejecutando resúmenes paralelos para: {topic}")

    result = graph.invoke({"topic": topic})

    print("\n" + "="*70)
    print("RESULTADOS PARALELOS (Ejecutados simultáneamente):")
    print("="*70)
    print(result['summaries'][-1])

    logger.info("✓ Patrón 3 completado exitosamente")
