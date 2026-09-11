#!/usr/bin/env python3
"""
Pattern 2: Routing (Ollama Local)

Patrón 2: Enrutamiento
Clasifica input y lo enruta al manejador apropiado.

Adaptado para Ollama local — 100% offline, parametrizable desde config.ini
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
    temperature=float(config.get('ollama', 'temperature', fallback='0.7')),
)

logger.info(f"✓ Ollama LLM initialized: {config.get('ollama', 'model_name')}")

# State definition
class State(TypedDict):
    text: str
    sentiment: str
    response: str

# Classifier node
def classify_sentiment(state: State) -> State:
    """Determina si el texto es positivo o negativo (Nodo 1: Clasificador)"""
    prompt = f"""Analiza el sentimiento de este texto.
Responde con UNA SOLA palabra: 'positive' o 'negative'.

Texto: {state['text']}
"""
    response = llm.invoke(prompt).strip().lower()
    state["sentiment"] = "positive" if "positive" in response else "negative"
    logger.info(f"🎭 Sentimiento detectado: {state['sentiment']}")
    print(f"🎭 Sentimiento detectado: {state['sentiment']}")
    return state

# Positive response handler
def handle_positive(state: State) -> State:
    """Genera respuesta entusiasta (Nodo 2: Manejador positivo)"""
    prompt = f"""Genera una respuesta entusiasta y alentadora para este mensaje positivo:

"{state['text']}"

¡Sé cálido y celebra su éxito!
"""
    response = llm.invoke(prompt)
    state["response"] = response.strip()
    return state

# Negative response handler
def handle_negative(state: State) -> State:
    """Genera respuesta empática (Nodo 3: Manejador negativo)"""
    prompt = f"""Genera una respuesta empática y de apoyo para este mensaje:

"{state['text']}"

Sé comprensivo y ofrece perspectiva positiva.
"""
    response = llm.invoke(prompt)
    state["response"] = response.strip()
    return state

# Router function
def route_based_on_sentiment(state: State) -> Literal["positive", "negative"]:
    """Enruta basado en sentimiento detectado"""
    return state["sentiment"]

# Build the graph
workflow = StateGraph(State)
workflow.add_node("classify", classify_sentiment)
workflow.add_node("positive", handle_positive)
workflow.add_node("negative", handle_negative)

workflow.set_entry_point("classify")
workflow.add_conditional_edges("classify", route_based_on_sentiment, {
    "positive": "positive",
    "negative": "negative"
})
workflow.set_finish_point("positive")
workflow.set_finish_point("negative")

graph = workflow.compile()

if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("PATRÓN 2: ENRUTAMIENTO (OLLAMA LOCAL)")
    logger.info("="*70)

    test_cases = [
        "¡Lo logré! Finalmente completé mi proyecto de IA!",
        "No sé si pueda hacerlo. Me siento atrapado en este problema."
    ]

    for i, text in enumerate(test_cases, 1):
        logger.info(f"\n--- Test {i} ---")
        print(f"\n--- Test {i} ---")
        print(f"Input: {text}")
        result = graph.invoke({"text": text})
        print(f"Sentimiento: {result['sentiment'].upper()}")
        print(f"Respuesta: {result['response']}")

    logger.info("✓ Patrón 2 completado exitosamente")
