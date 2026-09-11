#!/usr/bin/env python3
"""
Pattern 1: Prompt Chaining (Ollama Local)

Patrón 1: Encadenamiento de Prompts
Un agente's output se convierte en input de otro agente, como una carrera de relevos.

Adaptado para Ollama local — 100% offline, parametrizable desde config.ini
"""

import configparser
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import OllamaLLM
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar configuración desde config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Inicializar LLM con Ollama
llm = OllamaLLM(
    model=config.get('ollama', 'model_name', fallback='qwen2.5:7b'),
    base_url=config.get('ollama', 'base_url', fallback='http://localhost:11434'),
    temperature=float(config.get('ollama', 'temperature', fallback='0.7')),
)

logger.info(f"✓ Ollama LLM initialized: {config.get('ollama', 'model_name')}")

# Define state
class State(TypedDict):
    text: str
    topics: str
    title: str

# Node 1: Extract topics
def extract_topics(state: State) -> State:
    """Extrae tópicos clave del texto (Nodo 1)"""
    prompt = f"""Extrae 2-3 tópicos clave de este texto.
Sé conciso y específico.

Texto: {state['text']}
"""
    response = llm.invoke(prompt)
    state["topics"] = response.strip()
    logger.info(f"📝 Tópicos extraídos: {state['topics'][:50]}...")
    print(f"📝 Tópicos extraídos: {state['topics']}")
    return state

# Node 2: Generate titles
def generate_titles(state: State) -> State:
    """Genera títulos de blog atractivos (Nodo 2)"""
    prompt = f"""Genera 3 títulos de blog atractivos y optimizados para SEO basados en estos tópicos:

Tópicos: {state['topics']}

¡Hazlos convincentes y que generen clicks!
"""
    response = llm.invoke(prompt)
    state["title"] = response.strip()
    logger.info(f"🎯 Títulos generados")
    print(f"🎯 Títulos generados!")
    return state

# Build the graph
workflow = StateGraph(State)
workflow.add_node("extract_topics", extract_topics)
workflow.add_node("generate_titles", generate_titles)

# Connect nodes sequentially
workflow.set_entry_point("extract_topics")
workflow.add_edge("extract_topics", "generate_titles")
workflow.add_edge("generate_titles", END)

# Compile
graph = workflow.compile()

# Run it!
if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("PATRÓN 1: ENCADENAMIENTO DE PROMPTS (OLLAMA LOCAL)")
    logger.info("="*70)

    input_text = """
LangGraph revoluciona el desarrollo de IA introduciendo workflows basados en grafos.
Permite a los desarrolladores construir agentes modulares, debuggeables, con gestión
de estado persistente y coordinación multi-agente.
"""

    logger.info(f"Input: {input_text[:60]}...")
    result = graph.invoke({"text": input_text})

    print("\n" + "="*70)
    print("RESULTADOS FINALES:")
    print("="*70)
    print(f"\n📋 TÓPICOS EXTRAÍDOS:\n{result['topics']}")
    print(f"\n📰 TÍTULOS GENERADOS:\n{result['title']}")
    logger.info("✓ Patrón 1 completado exitosamente")
