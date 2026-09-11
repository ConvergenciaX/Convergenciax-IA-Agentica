#!/usr/bin/env python3
"""
Pattern 5: Tool Use (Ollama Local) — LLM decides when/how to use tools
"""

import configparser
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_ollama import OllamaLLM
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

llm = OllamaLLM(
    model=config.get('ollama', 'model_name', fallback='qwen2.5:7b'),
    base_url=config.get('ollama', 'base_url', fallback='http://localhost:11434'),
)

logger.info(f"✓ Ollama LLM initialized")

# Mock tools (en producción serían APIs reales)
def get_weather(location: str) -> str:
    """Simula obtener clima"""
    return f"Clima en {location}: 22°C, Nublado, Humedad 65%"

def search_web(query: str) -> str:
    """Simula búsqueda web"""
    return f"Resultados para '{query}': 10,000 enlaces encontrados (simulado)"

def calculate(expression: str) -> str:
    """Simula calculadora"""
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except:
        return "Error en cálculo"

class State(TypedDict):
    user_query: str
    tool_decision: str
    tool_result: str
    final_response: str

def decide_tool(state: State) -> State:
    """LLM decide qué herramienta usar"""
    prompt = f"""Analiza esta pregunta y decide qué herramienta usar:
- 'weather' para información del clima
- 'search' para búsqueda web
- 'calculate' para matemáticas
- 'respond' si no necesita herramienta

Pregunta: {state['user_query']}

Responde con UNA palabra: weather, search, calculate o respond."""

    response = llm.invoke(prompt).strip().lower()
    state["tool_decision"] = response
    logger.info(f"🔧 Herramienta seleccionada: {response}")
    return state

def use_tool(state: State) -> State:
    """Ejecuta la herramienta decidida"""
    decision = state["tool_decision"]

    if decision == "weather":
        state["tool_result"] = get_weather("Madrid")
    elif decision == "search":
        state["tool_result"] = search_web(state["user_query"])
    elif decision == "calculate":
        state["tool_result"] = calculate("2 + 2 * 3")
    else:
        state["tool_result"] = "No se requiere herramienta"

    logger.info(f"⚙️ Resultado de herramienta: {state['tool_result'][:50]}")
    return state

def generate_response(state: State) -> State:
    """Genera respuesta final con resultado de herramienta"""
    prompt = f"""Basándote en este resultado de herramienta, responde la pregunta del usuario:

Pregunta original: {state['user_query']}
Resultado: {state['tool_result']}

Respuesta clara y útil:"""

    response = llm.invoke(prompt).strip()
    state["final_response"] = response
    logger.info(f"✓ Respuesta generada")
    return state

workflow = StateGraph(State)
workflow.add_node("decide", decide_tool)
workflow.add_node("execute", use_tool)
workflow.add_node("respond", generate_response)

workflow.set_entry_point("decide")
workflow.add_edge("decide", "execute")
workflow.add_edge("execute", "respond")
workflow.add_edge("respond", END)

graph = workflow.compile()

if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("PATRÓN 5: TOOL USE - DECISIÓN Y EJECUCIÓN DE HERRAMIENTAS")
    logger.info("="*70)

    query = "¿Cuál es 2 + 2 por 3?"
    logger.info(f"Pregunta: {query}")

    result = graph.invoke({
        "user_query": query,
        "tool_decision": "",
        "tool_result": "",
        "final_response": ""
    })

    print("\n" + "="*70)
    print("RESULTADO:")
    print("="*70)
    print(f"Herramienta usada: {result['tool_decision'].upper()}")
    print(f"Resultado de herramienta: {result['tool_result']}")
    print(f"\nRespuesta: {result['final_response']}")
    logger.info("✓ Patrón 5 completado")
