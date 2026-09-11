#!/usr/bin/env python3
"""
Pattern 7: Multi-Agent Collaboration (Ollama Local) — Supervisor + Specialists
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
    task: str
    specialist_type: str
    specialist_response: str
    supervisor_synthesis: str

def supervisor(state: State) -> State:
    """Supervisor clasifica y asigna a especialista"""
    prompt = f"""Analiza esta tarea y asigna a un especialista:
- 'tech' para problemas técnicos
- 'business' para problemas empresariales
- 'creative' para problemas creativos

Tarea: {state['task']}

Responde con UNA palabra: tech, business o creative"""

    response = llm.invoke(prompt).strip().lower()
    state["specialist_type"] = response
    logger.info(f"🧑‍💼 Supervisor asigna a: {response}")
    return state

def tech_specialist(state: State) -> State:
    """Especialista técnico"""
    prompt = f"""Eres un especialista técnico. Resuelve esto:

{state['task']}

Proporciona una solución técnica clara."""

    response = llm.invoke(prompt)
    state["specialist_response"] = response.strip()
    logger.info(f"🔧 Especialista técnico respondió")
    return state

def business_specialist(state: State) -> State:
    """Especialista empresarial"""
    prompt = f"""Eres un especialista empresarial. Analiza esto:

{state['task']}

Proporciona perspectiva estratégica y de negocio."""

    response = llm.invoke(prompt)
    state["specialist_response"] = response.strip()
    logger.info(f"💼 Especialista empresarial respondió")
    return state

def creative_specialist(state: State) -> State:
    """Especialista creativo"""
    prompt = f"""Eres un especialista creativo. Aborda esto:

{state['task']}

Proporciona soluciones innovadoras y creativas."""

    response = llm.invoke(prompt)
    state["specialist_response"] = response.strip()
    logger.info(f"🎨 Especialista creativo respondió")
    return state

def synthesize(state: State) -> State:
    """Supervisor sintetiza respuesta final"""
    prompt = f"""Como supervisor, sintetiza esta respuesta de especialista en conclusión clara:

RESPUESTA DEL ESPECIALISTA:
{state['specialist_response']}

Síntesis ejecutiva (2-3 párrafos)."""

    response = llm.invoke(prompt)
    state["supervisor_synthesis"] = response.strip()
    logger.info(f"✓ Síntesis completada")
    return state

def route_to_specialist(state: State) -> Literal["tech", "business", "creative"]:
    """Enruta al especialista apropiado"""
    return state["specialist_type"]

workflow = StateGraph(State)
workflow.add_node("supervisor", supervisor)
workflow.add_node("tech", tech_specialist)
workflow.add_node("business", business_specialist)
workflow.add_node("creative", creative_specialist)
workflow.add_node("synthesize", synthesize)

workflow.set_entry_point("supervisor")
workflow.add_conditional_edges("supervisor", route_to_specialist, {
    "tech": "tech",
    "business": "business",
    "creative": "creative"
})
workflow.add_edge("tech", "synthesize")
workflow.add_edge("business", "synthesize")
workflow.add_edge("creative", "synthesize")
workflow.add_edge("synthesize", END)

graph = workflow.compile()

if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("PATRÓN 7: MULTI-AGENTE - SUPERVISOR + ESPECIALISTAS")
    logger.info("="*70)

    task = "¿Cómo podemos implementar IA en nuestro producto?"
    logger.info(f"Tarea: {task}")

    result = graph.invoke({
        "task": task,
        "specialist_type": "",
        "specialist_response": "",
        "supervisor_synthesis": ""
    })

    print("\n" + "="*70)
    print("RESULTADO MULTI-AGENTE:")
    print("="*70)
    print(f"Especialista asignado: {result['specialist_type'].upper()}")
    print(f"\n{result['supervisor_synthesis']}")
    logger.info("✓ Patrón 7 completado")
