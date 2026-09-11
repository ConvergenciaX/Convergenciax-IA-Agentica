# Tutorial: 7 Patrones Fundamentales de Diseño Agéntico con LangGraph

**Autor de estudio:** Síntesis de *Implementing Workflow Patterns with LangGraph* (IBM Skills Network, Kunal Makwana) y *Mastering Agentic Design Patterns with LangGraph* (Mahendra Medapati)  
**Fecha:** 2026-09-10  
**Idioma:** Español (didáctico)  
**Enfoque:** Arquitectura LLM-agnóstica (aplica a Gemini, OpenAI, Ollama local, etc.)

---

## 📋 Tabla de Contenidos

1. [¿Qué son los patrones agénticos?](#qué-son-los-patrones-agénticos)
2. [Tabla comparativa de los 7 patrones](#tabla-comparativa-de-los-7-patrones)
3. [Patrón 1: Prompt Chaining](#patrón-1-prompt-chaining)
4. [Patrón 2: Routing](#patrón-2-routing)
5. [Patrón 3: Parallelization](#patrón-3-parallelization)
6. [Patrón 4: Reflection](#patrón-4-reflection)
7. [Patrón 5: Tool Use](#patrón-5-tool-use)
8. [Patrón 6: Planning](#patrón-6-planning)
9. [Patrón 7: Multi-Agent Collaboration](#patrón-7-multi-agent-collaboration)
10. [Cómo elegir el patrón correcto](#cómo-elegir-el-patrón-correcto)
11. [Próximos pasos](#próximos-pasos)

---

## ¿Qué son los patrones agénticos?

Un **patrón agéntico** es una forma probada de **organizar y orquestar** llamadas a un LLM (Large Language Model) para resolver tareas complejas. 

Así como en software tradicional tenemos patrones de diseño (MVC, Factory, Observer), los sistemas de IA necesitan **patrones de arquitectura** que definan:
- **Flujo de datos:** cómo fluye información entre pasos
- **Control de flujo:** decisiones condicionales, bucles, paralelización
- **Gestión de estado:** qué información se mantiene a lo largo del workflow

### ¿Por qué importan más que los prompts?

> "La forma en que estructuras tu workflow determina todo. Puedes tener el LLM más poderoso del mundo, pero si tu arquitectura es caótica, tu agente fallará en producción."

**La realidad en 2024-2025:** Los agentes que funcionan en producción no son sistemas completamente autónomos. Son **verticales, estrechamente enfocados, altamente controlables** con arquitecturas cognitivas personalizadas. Los patrones de abajo son esas arquitecturas.

### Arquitectura común: LangGraph

Todos los patrones en este tutorial se construyen sobre **LangGraph**, que proporciona:

```python
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# 1. Estado tipado (datos compartidos)
class State(TypedDict):
    input_field: str
    processing_field: str
    output_field: str

# 2. Nodos (funciones que procesan el estado)
def node_1(state: State) -> State:
    # Recibe estado, retorna estado actualizado
    state["processing_field"] = "resultado"
    return state

# 3. Grafo (orquestación)
workflow = StateGraph(State)
workflow.add_node("node_1", node_1)
workflow.set_entry_point("node_1")
workflow.add_edge("node_1", END)

# 4. Compilación
graph = workflow.compile()
result = graph.invoke({"input_field": "valor inicial"})
```

---

## Tabla comparativa de los 7 patrones

| Patrón | Qué es | Cuándo usarlo | Complejidad | Caso real |
|--------|--------|---------------|-------------|-----------|
| **1. Prompt Chaining** | Secuencia lineal donde cada paso depende del anterior | Pipelines de procesamiento paso a paso | ⭐ Baja | Resumir CV → generar carta de presentación |
| **2. Routing** | Clasificar entrada y enviarla a handler especializado | Múltiples intents/tipos de tarea | ⭐⭐ Media-baja | Chatbot de soporte (técnico vs. facturación) |
| **3. Parallelization** | Múltiples tareas independientes simultáneas + agregación | Tareas que no dependen entre sí | ⭐⭐ Media-baja | Traducir a 3 idiomas simultáneamente |
| **4. Reflection** | Generar → evaluar → refinar en bucle | Alto requerimiento de calidad | ⭐⭐⭐ Media | Generación de código o escritura creativa |
| **5. Tool Use** | LLM decide si necesita invocar herramientas | Datos en tiempo real o cálculos | ⭐⭐⭐ Media | Pregunta "¿qué hora es en NYC?" → usar tool |
| **6. Planning** | Generar plan explícito, luego ejecutar pasos | Tareas complejas multi-etapa | ⭐⭐⭐⭐ Alta | Análisis de impacto de mercado + síntesis |
| **7. Multi-Agent** | Supervisor + especialistas con dominios propios | Sistemas complejos con expertise variado | ⭐⭐⭐⭐ Alta | Uber: routear a agente meteorólogo, financiero, etc. |

---

## Patrón 1: Prompt Chaining

### Concepto

**Prompt Chaining** descompone una tarea compleja en una **secuencia de pasos**, donde cada paso:
- Recibe el estado completo (incluyendo salidas de pasos anteriores)
- Invoca el LLM con un prompt específico
- Actualiza el estado con su resultado
- Pasa el estado al siguiente paso

### Diagrama de flujo

```
┌─────────────┐
│   Input:    │
│ Job Desc.   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ Paso 1:                  │
│ Resume Summary Agent     │  (extrae puntos clave del CV respecto al puesto)
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Paso 2:                  │
│ Cover Letter Agent       │  (genera carta basada en resumen + descripción)
└──────┬───────────────────┘
       │
       ▼
┌─────────────────────┐
│  Output:            │
│  Cover Letter       │
└─────────────────────┘
```

### Código ilustrativo

Del notebook IBM (job application assistant):

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# Estado compartido
class ChainState(TypedDict):
    job_description: str
    resume_summary: str
    cover_letter: str

# Paso 1: Resumir CV según el puesto
def generate_resume_summary(state: ChainState) -> ChainState:
    prompt = f"""
    Basándote en esta descripción de puesto, extrae los puntos
    clave del CV del candidato que son más relevantes:
    
    Descripción: {state['job_description']}
    """
    response = llm.invoke(prompt)
    state["resume_summary"] = response.content.strip()
    return state

# Paso 2: Generar carta de presentación
def generate_cover_letter(state: ChainState) -> ChainState:
    prompt = f"""
    Genera una carta de presentación personalizada para este puesto.
    
    Puesto: {state['job_description']}
    Puntos fuertes del candidato: {state['resume_summary']}
    
    Hazla convincente y adaptada.
    """
    response = llm.invoke(prompt)
    state["cover_letter"] = response.content.strip()
    return state

# Construir el grafo
workflow = StateGraph(ChainState)
workflow.add_node("resume", generate_resume_summary)
workflow.add_node("letter", generate_cover_letter)

workflow.set_entry_point("resume")
workflow.add_edge("resume", "letter")
workflow.add_edge("letter", END)

graph = workflow.compile()

# Ejecutar
result = graph.invoke({
    "job_description": "Senior ML Engineer at TechCorp...",
})
print(result["cover_letter"])
```

### Cuándo usar Prompt Chaining

✅ **Úsalo cuando:**
- Tienes pasos **claramente secuenciales** (A → B → C)
- Cada paso es relativamente **independiente en lógica**
- El output de un paso es input directo del siguiente
- Necesitas **rastreabilidad** de cada paso

❌ **No lo uses cuando:**
- Los pasos pueden ser **independientes** (usa Parallelization)
- Necesitas **condicionales** (usa Routing)
- El problema requiere **realimentación/refinamiento** (usa Reflection)

### Ejemplo real: LinkedIn's SQL Bot

LinkedIn convierte preguntas en lenguaje natural a SQL:
1. **Paso 1:** Encontrar tablas relevantes
2. **Paso 2:** Escribir la query SQL
3. **Paso 3:** Ejecutar y detectar errores
4. **Paso 4:** Refinar si hay errores

Cada paso alimenta el siguiente; el estado contiene la query en evolución.

---

## Patrón 2: Routing

### Concepto

**Routing** (enrutamiento) significa que un **nodo clasificador** analiza la entrada y decide **a cuál de varios handlers especializados enviarla**.

Es útil cuando tu sistema debe manejar **múltiples tipos de tarea** con lógica completamente diferente.

### Diagrama de flujo

```
┌──────────────────┐
│   User Input     │
│  "Resumir esto"  │
└────────┬─────────┘
         │
         ▼
    ┌─────────────────┐
    │ ROUTER NODE     │
    │ (Classifies)    │
    └────┬────────────┘
         │
    ┌────┴──────────────┐
    │                   │
    ▼                   ▼
┌────────────┐    ┌──────────────┐
│ Summarize  │    │ Translate    │
│   Handler  │    │   Handler    │
└────────────┘    └──────────────┘
```

### Código ilustrativo

Del notebook IBM (task router para summarization vs. translation):

```python
from typing import Literal
from typing_extensions import TypedDict

class RouterState(TypedDict):
    user_input: str
    task_type: str      # "summarize" o "translate"
    output: str

# Nodo 1: Clasificador
def router_node(state: RouterState) -> RouterState:
    prompt = f"""
    Analiza la intención del usuario. Responde SOLO con una palabra:
    "summarize" si pide un resumen, "translate" si pide traducción.
    
    Usuario: {state['user_input']}
    """
    response = llm.invoke(prompt)
    state["task_type"] = response.content.strip().lower()
    return state

# Nodo 2: Handler especializado para summarization
def summarize_node(state: RouterState) -> RouterState:
    prompt = f"""
    Resume este texto en 2-3 oraciones:
    {state['user_input']}
    """
    response = llm.invoke(prompt)
    state["output"] = response.content.strip()
    return state

# Nodo 3: Handler especializado para translation
def translate_node(state: RouterState) -> RouterState:
    prompt = f"""
    Traduce al español:
    {state['user_input']}
    """
    response = llm.invoke(prompt)
    state["output"] = response.content.strip()
    return state

# Función router (decide a dónde ir)
def router_decision(state: RouterState) -> Literal["summarize", "translate"]:
    return "summarize" if "summarize" in state["task_type"] else "translate"

# Construir grafo
workflow = StateGraph(RouterState)
workflow.add_node("router", router_node)
workflow.add_node("summarize", summarize_node)
workflow.add_node("translate", translate_node)

workflow.set_entry_point("router")

# CONDICIONAL: enruta según task_type
workflow.add_conditional_edges(
    "router",
    router_decision,
    {
        "summarize": "summarize",
        "translate": "translate"
    }
)

workflow.add_edge("summarize", END)
workflow.add_edge("translate", END)

graph = workflow.compile()

# Ejecutar
result = graph.invoke({"user_input": "Quiero resumir este artículo..."})
```

### Cuándo usar Routing

✅ **Úsalo cuando:**
- Tu sistema maneja **múltiples tipos de tarea**
- Cada tipo requiere **lógica/tools completamente diferentes**
- Necesitas **decisiones rápidas** basadas en clasificación

❌ **No lo uses cuando:**
- Todos los pasos son **lineales** (usa Prompt Chaining)
- Las subtareas son **independientes en paralelo** (usa Parallelization)

### Ejemplo real: Uber Support Bot

Un chatbot de Uber enruta a diferentes especialistas:
- **"¿Dónde está mi conductor?"** → GPS Agent
- **"Cargo incorrecto en mi factura"** → Finance Agent
- **"El conductor fue grosero"** → HR / Compliance Agent

Cada agente tiene tools y prompts especializados para su dominio.

---

## Patrón 3: Parallelization

### Concepto

**Parallelization** ejecuta **múltiples nodos independientes al mismo tiempo** sobre la misma entrada, luego un **nodo agregador** combina sus resultados.

Es esencial cuando tienes subtareas que **no dependen entre sí** — reduce la latencia de pared (wall-clock time).

### Diagrama de flujo

```
┌─────────────────┐
│  English Text   │
└────────┬────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼      ▼
┌───────┐ ┌───────┐ ┌───────┐
│French │ │Spanish│ │Japanese│  (SIMULTÁNEOS)
└───┬───┘ └───┬───┘ └───┬───┘
    │         │         │
    └────┬────┴────┬────┘
         │
         ▼
    ┌────────────┐
    │ Aggregator │  (combina resultados)
    └────┬───────┘
         │
         ▼
    ┌──────────────┐
    │ Final Output │
    │ (3 idiomas)  │
    └──────────────┘
```

### Código ilustrativo

Del repo Mahendra (multilingual translation assistant):

```python
import operator
from typing import Annotated
from typing_extensions import TypedDict

# Estado con REDUCER para actualizaciones paralelas
class State(TypedDict):
    text: str
    outputs: Annotated[list, operator.add]  # ← Clave: lista acumulativa

# Tarea paralela 1: Traducir a francés
def translate_french(state: State):
    prompt = f"Traduce al francés: {state['text']}"
    response = llm.invoke(prompt)
    return {"outputs": [f"🇫🇷 Francés: {response.content.strip()}"]}

# Tarea paralela 2: Traducir a español
def translate_spanish(state: State):
    prompt = f"Traduce al español: {state['text']}"
    response = llm.invoke(prompt)
    return {"outputs": [f"🇪🇸 Español: {response.content.strip()}"]}

# Tarea paralela 3: Traducir a japonés
def translate_japanese(state: State):
    prompt = f"Traduce al japonés: {state['text']}"
    response = llm.invoke(prompt)
    return {"outputs": [f"🇯🇵 Japonés: {response.content.strip()}"]}

# Nodo agregador
def combine_translations(state: State):
    all_text = "\n\n".join(state['outputs'])
    prompt = f"""Sintetiza estas traducciones en un resumen coherente:
    {all_text}"""
    response = llm.invoke(prompt)
    return {"outputs": [f"\n✨ Síntesis:\n{response.content}"]}

# Construir grafo con paralelización
workflow = StateGraph(State)
workflow.add_node("french", translate_french)
workflow.add_node("spanish", translate_spanish)
workflow.add_node("japanese", translate_japanese)
workflow.add_node("combine", combine_translations)

# TODOS arrancan simultáneamente desde START
workflow.add_edge(START, "french")
workflow.add_edge(START, "spanish")
workflow.add_edge(START, "japanese")

# Todos convergen en el agregador
workflow.add_edge("french", "combine")
workflow.add_edge("spanish", "combine")
workflow.add_edge("japanese", "combine")

workflow.add_edge("combine", END)

graph = workflow.compile()

# Ejecutar
result = graph.invoke({"text": "Hello, world!", "outputs": []})
for output in result["outputs"]:
    print(output)
```

### La magia: Annotated + Reducer

```python
outputs: Annotated[list, operator.add]
```

Esto dice: "cuando múltiples nodos devuelven `outputs`, en lugar de sobreescribir, **concatena las listas**". Sin esto, el último nodo paralelizado sobrescribiría a los anteriores.

### Cuándo usar Parallelization

✅ **Úsalo cuando:**
- Tienes **2+ subtareas independientes**
- **No necesitan resultados de la otra** para ejecutarse
- Quieres **reducir latencia total** (no tiempo de cómputo, pero sí tiempo de espera)

❌ **No lo uses cuando:**
- Los pasos tienen **dependencias** (usa Prompt Chaining o Planning)
- Es una sola tarea (overhead innecesario)

### Ejemplo real: Análisis de documentos

Analizar un documento **en paralelo**:
- Nodo 1: Extraer resumen
- Nodo 2: Identificar palabras clave
- Nodo 3: Detectar sentimiento
- Agregador: combina en un reporte unificado

Si los 3 nodos tardaban 10s cada uno secuencialmente (30s total), en paralelo tarda ~10s.

---

## Patrón 4: Reflection

### Concepto

**Reflection** (reflexión) es cuando un agente **genera un resultado, lo evalúa/critica, y refina en bucle** hasta que aprueba su propia salida o alcanza un límite de iteraciones.

Es el patrón que **mueve a los agentes de "una sola vez" a "iterativo"**, mejorando la calidad.

### Diagrama de flujo

```
┌────────────────┐
│ Tarea inicial  │
└────────┬───────┘
         │
         ▼
    ┌─────────────┐
    │ Generate    │
    │ Draft (v1)  │
    └──────┬──────┘
           │
           ▼
      ┌──────────┐
      │ Evaluate │
      └─┬────────┘
        │
    ┌───┴────────────┐
    │                │
   (¿APPROVED?)      (NEEDS IMPROVEMENT?)
    │                │
   SÍ               NO
    │                │
    ▼                ▼
┌────────┐    ┌──────────────┐
│Finalize│    │ Generate     │
│(output)│    │ Draft (v2)   │
└────┬───┘    └──────┬───────┘
     │               │
     └───────┬───────┘ (loop max 3-5 veces)
             │
             ▼
        ┌──────────┐
        │ Final    │
        │ Output   │
        └──────────┘
```

### Código ilustrativo

Del repo Mahendra (pattern_4_reflection.py):

```python
from typing_extensions import TypedDict

class State(TypedDict):
    task: str
    draft: str
    feedback: str
    iteration: int
    final: str

# Nodo 1: Generar o refinar borrador
def generate_draft(state: State):
    iteration = state.get('iteration', 0) + 1
    
    if iteration == 1:
        prompt = f"Crea una respuesta clara para: {state['task']}"
    else:
        prompt = f"""Mejora este borrador basándote en el feedback:
        
        Borrador actual: {state['draft']}
        Feedback: {state['feedback']}
        """
    
    response = llm.invoke(prompt)
    
    return {
        "draft": response.content.strip(),
        "iteration": iteration
    }

# Nodo 2: Evaluar el borrador
def evaluate_draft(state: State):
    prompt = f"""Evalúa este borrador:
    
    Tarea: {state['task']}
    Borrador: {state['draft']}
    
    Si es excelente y cumple todos los requisitos, responde: APPROVED
    Si no, da feedback específico para mejora.
    """
    
    response = llm.invoke(prompt)
    return {"feedback": response.content.strip()}

# Nodo 3: Decidir si continuar o finalizar
def should_continue(state: State) -> str:
    max_iterations = 3
    
    if "APPROVED" in state["feedback"].upper():
        print(f"✅ Draft aprobado en iteración {state['iteration']}")
        return "finalize"
    elif state['iteration'] >= max_iterations:
        print(f"⚠️ Límite de iteraciones ({max_iterations}) alcanzado")
        return "finalize"
    else:
        print(f"🔄 Iteración {state['iteration']} - necesita mejora")
        return "refine"

# Nodo 4: Finalizar
def finalize_output(state: State):
    return {"final": state["draft"]}

# Construir grafo con bucle
workflow = StateGraph(State)
workflow.add_node("generate", generate_draft)
workflow.add_node("evaluate", evaluate_draft)
workflow.add_node("finalize", finalize_output)

workflow.set_entry_point("generate")
workflow.add_edge("generate", "evaluate")

# CONDICIONAL: bucle de refinamiento
workflow.add_conditional_edges(
    "evaluate",
    should_continue,
    {
        "refine": "generate",    # ← Vuelve a generar
        "finalize": "finalize"
    }
)

workflow.add_edge("finalize", END)

graph = workflow.compile()

# Ejecutar
result = graph.invoke({
    "task": "Explica computación cuántica a un niño de 10 años",
    "iteration": 0
})

print(result["final"])
```

### ⚠️ Regla crítica: max_iterations

**SIEMPRE** establece un límite máximo de iteraciones, de lo contrario podrías entrar en un bucle infinito si el LLM nunca aprueba su propia salida.

### Cuándo usar Reflection

✅ **Úsalo cuando:**
- Necesitas **alta calidad** (escritura, código, análisis)
- El LLM puede **mejorar iterativamente** su propio output
- Tienes **criterios claros** de aprobación

❌ **No lo uses cuando:**
- La tarea es **simple** (overhead innecesario)
- El LLM **no puede evaluar su propia calidad** (requiere evaluador externo)
- Los **costos/latencia** son críticos (cada iteración = más tokens + tiempo)

### Ejemplo real: Generación de código

Un agente genera código, lo revisa él mismo:
1. **v1:** "Aquí hay tu función"
2. **Evaluación:** "Falta manejo de errores, el nombre es confuso"
3. **v2:** Versión mejorada
4. **Evaluación:** "Bien, pero sin docstring"
5. **v3:** Versión final con docstring

Sin reflection, solo tendrías v1.

---

## Patrón 5: Tool Use

### Concepto

**Tool Use** es cuando un LLM **decide dinámicamente** si necesita invocar una herramienta/función externa (cálculos, APIs, bases de datos), la ejecuta, obtiene el resultado y lo usa para responder.

El LLM no ejecuta la herramienta; decide que la necesita, el sistema la ejecuta, y el resultado vuelve al LLM.

### Diagrama de flujo

```
┌──────────────────┐
│ User Query:      │
│ "¿Cuánto es      │
│  156 * 89?"      │
└────────┬─────────┘
         │
         ▼
    ┌─────────────────┐
    │ LLM with tools  │
    │ (decision)      │
    └────────┬────────┘
             │
      (¿Necesita tool?)
             │
         ┌───┴───┐
         │       │
        SÍ      NO
         │       │
         ▼       ▼
    ┌────────┐ ┌──────────┐
    │Execute │ │ Respuesta│
    │ Tool   │ │ directa  │
    └───┬────┘ └──────────┘
        │
        ▼
   ┌─────────────┐
   │ Tool result │  (ej. 13884)
   └──────┬──────┘
          │
          ▼
     ┌────────────────┐
     │ LLM with result│
     │ (genera respuesta)
     └────────┬───────┘
              │
              ▼
         ┌──────────┐
         │ Response │
         └──────────┘
```

### Código ilustrativo

Del repo Mahendra (pattern_5_tool_use.py):

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages

# Estado con historial de mensajes
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# Definir herramientas
@tool
def calculator(expression: str) -> str:
    """Evalúa una expresión matemática."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Resultado: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_weather(city: str) -> str:
    """Obtiene el clima de una ciudad (simulado)."""
    weather_db = {
        "San Francisco": "☀️ Soleado, 72°F",
        "New York": "🌧️ Lluvioso, 55°F",
        "Tokyo": "🌤️ Parcialmente nublado, 68°F",
    }
    return weather_db.get(city, f"Datos no disponibles para {city}")

# Inicializar LLM con tools
tools = [calculator, get_weather]
model_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)

# Nodo: Llamar a LLM
def call_model(state: State):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

# Nodo: Decidir si continuar o terminar
def should_continue(state: State) -> str:
    last_message = state["messages"][-1]
    
    # ¿Hay tool calls?
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print(f"🔧 Herramienta solicitada: {last_message.tool_calls[0]['name']}")
        return "tools"
    
    return "end"

# Construir grafo
workflow = StateGraph(State)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

# CONDICIONAL: si necesita tools, ir a tools; si no, terminar
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)

# Loop: después de ejecutar tool, volver al agente
workflow.add_edge("tools", "agent")

graph = workflow.compile()

# Ejecutar
queries = [
    "¿Cuánto es 156 * 89?",
    "¿Qué clima hace en Tokyo?",
]

for query in queries:
    print(f"\n❓ Pregunta: {query}")
    result = graph.invoke({"messages": [HumanMessage(content=query)]})
    final_response = result["messages"][-1].content
    print(f"💬 Respuesta: {final_response}\n")
```

### Cuándo usar Tool Use

✅ **Úsalo cuando:**
- Necesitas **datos actuales** (clima, precios de bolsa)
- Requieres **cálculos exactos** (no LLM hallucination)
- Integras con **APIs/bases de datos externas**

❌ **No lo uses cuando:**
- El LLM puede responder **sin información externa**
- No tienes **tools confiables** que implementar

### Ejemplo real: Asistente de compras

Un chatbot de ecommerce:
- Usuario: "¿Cómo sale el envío a Madrid?"
- LLM decide: necesito la tool `calculate_shipping(destination, weight)`
- Ejecuta: `calculate_shipping("Madrid", 2.5)` → "€15.50"
- LLM: "El envío a Madrid cuesta €15.50"

Sin tool use, el LLM haría una adivinanza (bad).

---

## Patrón 6: Planning

### Concepto

**Planning** (planificación) es cuando un agente **primero crea un plan multi-paso explícito**, luego **ejecuta cada paso** (a veces en paralelo) y **sintetiza resultados**.

Separa la fase de "pensar **cómo**" de la fase de "ejecutar **qué**".

### Diagrama de flujo

```
┌──────────────────┐
│ Tarea compleja   │
└────────┬─────────┘
         │
         ▼
    ┌───────────────┐
    │ Create Plan   │  "1. Investigar X, 2. Analizar Y, 3. Sintetizar"
    └───────┬───────┘
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌─────────────┐ ┌──────────────┐
│ Research 1  │ │ Research 2   │  (PARALELO)
└──────┬──────┘ └────────┬─────┘
       │                 │
       └────────┬────────┘
                │
                ▼
          ┌────────────┐
          │ Synthesize │
          │ Findings   │
          └──────┬─────┘
                 │
                 ▼
            ┌──────────┐
            │ Report   │
            └──────────┘
```

### Código ilustrativo

Del repo Mahendra (pattern_6_planning.py, adaptado):

```python
from typing import Annotated
from typing_extensions import TypedDict

# Reducer para merge de dicts (resultado de investigaciones paralelas)
def merge_dicts(left: dict, right: dict) -> dict:
    return {**left, **right}

class PlannerState(TypedDict):
    task: str
    plan: list[str]
    research_results: Annotated[dict, merge_dicts]  # Combina resultados
    final_output: str

# Nodo 1: Crear el plan
def create_plan(state: PlannerState):
    prompt = f"""Crea un plan de 3-5 pasos para:
    
    {state['task']}
    
    Formato: lista numerada.
    """
    response = llm.invoke(prompt)
    
    # Parse steps
    steps = [
        line.strip()
        for line in response.content.split('\n')
        if line.strip() and any(char.isdigit() for char in line[:3])
    ]
    
    print(f"📋 PLAN: {steps}")
    return {"plan": steps}

# Nodo 2: Investigación técnica (paralela)
def research_technology(state: PlannerState):
    prompt = f"""Investiga aspectos técnicos de:
    {state['task']}
    """
    response = llm.invoke(prompt)
    return {"research_results": {"technical": response.content}}

# Nodo 3: Investigación de mercado (paralela)
def research_market(state: PlannerState):
    prompt = f"""Investiga impacto de mercado de:
    {state['task']}
    """
    response = llm.invoke(prompt)
    return {"research_results": {"market": response.content}}

# Nodo 4: Sintetizar
def synthesize_report(state: PlannerState):
    research = state['research_results']
    
    prompt = f"""Crea un reporte ejecutivo basándote en:
    
    PLAN SEGUIDO:
    {chr(10).join(state['plan'])}
    
    ASPECTOS TÉCNICOS:
    {research.get('technical', 'N/A')}
    
    ASPECTOS DE MERCADO:
    {research.get('market', 'N/A')}
    
    Genera un reporte coherente de 3 párrafos.
    """
    
    response = llm.invoke(prompt)
    return {"final_output": response.content}

# Construir grafo
workflow = StateGraph(PlannerState)
workflow.add_node("planner", create_plan)
workflow.add_node("research_tech", research_technology)
workflow.add_node("research_market", research_market)
workflow.add_node("synthesize", synthesize_report)

workflow.set_entry_point("planner")

# Plan → luego investigaciones en paralelo
workflow.add_edge("planner", "research_tech")
workflow.add_edge("planner", "research_market")

# Ambas investigaciones convergen en síntesis
workflow.add_edge("research_tech", "synthesize")
workflow.add_edge("research_market", "synthesize")

workflow.add_edge("synthesize", END)

graph = workflow.compile()

# Ejecutar
result = graph.invoke({
    "task": "Analizar el impacto de IA en la industria financiera",
    "research_results": {}
})

print(result["final_output"])
```

### Cuándo usar Planning

✅ **Úsalo cuando:**
- La tarea es **compleja y multi-etapa**
- Hay **partes independientes** que pueden paralelizarse
- Necesitas **divorciar la estrategia de la ejecución**
- Quieres **rastreabilidad de la estrategia**

❌ **No lo uses cuando:**
- La tarea es **simple y lineal** (usa Prompt Chaining)
- No hay **paralelización posible** (overhead innecesario)

### Ejemplo real: Análisis competitivo

Planificar el análisis de 3 competidores:
1. **Plan:** "Investigar producto, precios, marketing de cada uno. Sintetizar."
2. **Ejecución paralela:** 3 agentes investigadores en simultáneo
3. **Síntesis:** Un agente crea el reporte comparativo final

Sin planning, harías esto secuencial: (investigar A) → (investigar B) → (investigar C) → (sintetizar). Con planning + paralelización, es más rápido.

---

## Patrón 7: Multi-Agent Collaboration

### Concepto

**Multi-Agent Collaboration** es un sistema donde **múltiples agentes especializados** con dominios y tools propios **colaboran bajo coordinación de un supervisor**.

El supervisor no hace el trabajo; **enruta a especialistas** y coordina el diálogo.

### Diagrama de flujo

```
┌──────────────────┐
│ User Query       │
│ "Cuál es el      │
│ clima en NYC?"   │
└────────┬─────────┘
         │
         ▼
    ┌─────────────────┐
    │ SUPERVISOR      │
    │ (Classifies)    │
    └──────┬──────────┘
           │
     ("Weather Agent")
           │
           ▼
      ┌────────────────┐
      │ Weather Agent  │  (has weather tools)
      │ (Specialist)   │
      └────────┬───────┘
               │
               ▼
          ┌──────────────┐
          │ Response to  │
          │ User         │
          └──────────────┘
```

Versus multi-agent con loops:

```
User ↔ Supervisor ↔ [Weather, News, Calculator agents]
```

El supervisor puede enrutar múltiples consultas a diferentes agentes, o incluso crear un diálogo multi-turno.

### Código ilustrativo

Del repo Mahendra (pattern_7_multi_agent.py, simplificado):

```python
from typing import Literal, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langgraph.graph.message import add_messages

class MultiAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    next_agent: str

# Router model (structuredoutput del LLM)
class Router(BaseModel):
    next_agent: Literal[
        "weather_agent",
        "news_agent",
        "calculator_agent",
        "__end__"
    ]
    reasoning: str

supervisor_model = llm.with_structured_output(Router)

# Nodo: Supervisor
def supervisor(state: MultiAgentState):
    last_message = state['messages'][-1]
    
    if isinstance(last_message, HumanMessage):
        print("\n🧑‍💼 SUPERVISOR analizando...")
        
        prompt = f"""Eres un supervisor con un equipo de especialistas:
        - weather_agent: preguntas de clima
        - news_agent: noticias
        - calculator_agent: matemáticas
        
        User: "{last_message.content}"
        
        A quién enrutas? (elige uno o __end__ si la conversación terminó)
        """
        
        decision = supervisor_model.invoke(prompt)
        print(f"   → Enrutando a: {decision.next_agent}")
        print(f"   → Razón: {decision.reasoning}")
        
        return {"next_agent": decision.next_agent}
    else:
        # Un agente ya respondió, terminar
        return {"next_agent": "__end__"}

# Función de enrutamiento
def router_fn(state: MultiAgentState) -> Literal["weather_agent", "news_agent", "calculator_agent", "__end__"]:
    return state["next_agent"]

# Agente especialista: Clima
def weather_agent(state: MultiAgentState):
    print("\n☀️ WEATHER AGENT activado")
    user_query = state['messages'][-1].content
    
    prompt = f"""Eres un especialista en clima. Responde:
    "{user_query}"
    Incluye temperatura, condiciones y pronóstico breve."""
    
    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=response.content)]}

# Agente especialista: Noticias
def news_agent(state: MultiAgentState):
    print("\n📰 NEWS AGENT activado")
    user_query = state['messages'][-1].content
    
    prompt = f"""Eres un especialista en noticias. Responde:
    "{user_query}"
    (Simula noticias recientes si es necesario)."""
    
    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=response.content)]}

# Agente especialista: Calculadora
def calculator_agent(state: MultiAgentState):
    print("\n🔢 CALCULATOR AGENT activado")
    user_query = state['messages'][-1].content
    
    prompt = f"""Eres un especialista en matemáticas. Resuelve:
    "{user_query}"
    Muestra el cálculo y el resultado."""
    
    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=response.content)]}

# Construir grafo
workflow = StateGraph(MultiAgentState)

workflow.add_node("supervisor", supervisor)
workflow.add_node("weather_agent", weather_agent)
workflow.add_node("news_agent", news_agent)
workflow.add_node("calculator_agent", calculator_agent)

workflow.set_entry_point("supervisor")

# Enrutamiento condicional desde supervisor
workflow.add_conditional_edges(
    "supervisor",
    router_fn,
    {
        "weather_agent": "weather_agent",
        "news_agent": "news_agent",
        "calculator_agent": "calculator_agent",
        "__end__": END
    }
)

# Todos los agentes terminan (o podrían volver al supervisor para multi-turn)
workflow.add_edge("weather_agent", END)
workflow.add_edge("news_agent", END)
workflow.add_edge("calculator_agent", END)

graph = workflow.compile()

# Ejecutar
queries = [
    "¿Qué clima hace en Tokyo?",
    "¿Cuánto es 234 * 67?",
    "¿Hay noticias tech hoy?",
]

for query in queries:
    print(f"\n{'='*50}")
    print(f"👤 USER: {query}")
    print('='*50)
    
    result = graph.invoke({
        "messages": [HumanMessage(content=query)],
        "next_agent": ""
    })
    
    if len(result["messages"]) > 1:
        final = result["messages"][-1].content
        print(f"\n🤖 RESPUESTA: {final}\n")
```

### Cuándo usar Multi-Agent Collaboration

✅ **Úsalo cuando:**
- Tu sistema tiene **múltiples dominios de expertise**
- Cada dominio necesita **tools/prompts especializados**
- Quieres **escalabilidad** (agregar nuevos agentes fácilmente)
- Sistema es suficientemente **complejo** para justificar overhead

❌ **No lo uses cuando:**
- Es una tarea **simple** (Routing es suficiente)
- No hay **especialización clara** entre partes
- Costo/latencia son **muy críticos** (overhead de coordinación)

### Ejemplo real: Replit's Coding Assistant

Replit usa múltiples agentes especializados:
- **Code-writing agent:** escribe código
- **Testing agent:** crea tests
- **Debugging agent:** identifica y fija bugs
- **Documentation agent:** genera docs
- **Supervisor:** enruta preguntas del usuario

Cada agente tiene tools propios (ejecutar código, debugger, etc.) y el supervisor coordina.

---

## Cómo elegir el patrón correcto

```
¿Cuál es tu problema?

1. ¿Pasos claros y secuenciales?
   SÍ → Prompt Chaining
   NO → (2)

2. ¿Múltiples tipos de tarea completamente diferentes?
   SÍ → Routing
   NO → (3)

3. ¿Subtareas independientes en paralelo?
   SÍ → Parallelization
   NO → (4)

4. ¿El agente necesita evaluar y refinar su propio trabajo?
   SÍ → Reflection
   NO → (5)

5. ¿Necesitas datos externos / APIs / herramientas?
   SÍ → Tool Use
   NO → (6)

6. ¿Tarea compleja con múltiples etapas de investigación?
   SÍ → Planning
   NO → (7)

7. ¿Sistema con múltiples dominios de expertise?
   SÍ → Multi-Agent Collaboration
   NO → Simple LLM call (no patrón necesario)
```

### Tabla de decisión rápida

| Si necesitas... | Usa... |
|-----------------|--------|
| Dividir tarea en pasos lineales | Prompt Chaining |
| Branching lógico simple | Routing |
| Paralelización | Parallelization |
| Iteración y refinamiento | Reflection |
| Integración con APIs/tools | Tool Use |
| Planificación explícita | Planning |
| Sistemas multi-dominio complejos | Multi-Agent |

**Nota:** Estos patrones **no son excluyentes**. Un sistema real a menudo combina varios (ej. Multi-Agent + Routing + Reflection + Tool Use).

---

## Próximos pasos

### Para tu equipo (uso inmediato)

1. **Estudia el código de ejemplo** de cada patrón en:
   - `Implement Workflow Patterns with LangGraph.ipynb` (3 patrones en profundidad)
   - `pattern_1..7_*.py` (7 patrones simples)

2. **Elige un patrón** que se ajuste a tu primera tarea IA real

3. **Prototipa** con un LLM local (Ollama) o uno que ya tengas

4. **Valida** con tus datos reales

### Migración a Ollama Local (pendiente)

Todos estos patrones son **100% agnósticos del LLM**. Cambiar de Google Gemini a Ollama local es solo:

```python
# ANTES (Gemini):
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=os.getenv("GOOGLE_API_KEY"))

# DESPUÉS (Ollama local):
from langchain_community.llms import Ollama
llm = Ollama(model="qwen2.5:7b", base_url="http://localhost:11434")
```

**Todo lo demás en tu código sigue igual.** La arquitectura del patrón no cambia.

### Recursos adicionales

- **LangGraph oficial:** https://langchain-ai.github.io/langgraph/
- **DeepLearning.ai (Agentic Design Patterns):** https://www.deeplearning.ai/
- **Papers:**
  - ReAct: Synergizing Reasoning and Acting (2022)
  - Reflexion: Language Agents with Verbal Reinforcement Learning (2023)
  - AutoGen: Enabling Next-Gen LLM Applications (Microsoft, 2023)

---

## Conclusión

Los 7 patrones agénticos resuelven la mayoría de problemas reales de AI/LLM:

- **Prompt Chaining:** pipelines paso a paso
- **Routing:** decisiones condicionales
- **Parallelization:** paralelización de subtareas
- **Reflection:** mejora iterativa
- **Tool Use:** integración con sistemas externos
- **Planning:** planificación estratégica
- **Multi-Agent:** sistemas especializados complejos

Dominarlos te permitirá construir agentes que **funcionan en producción**, no solo demos impresionantes.

**Recuerda:** buena arquitectura > prompts ingeniosos.

---

**Fin del tutorial.**

*Tutorial didáctico compilado a partir de:*
- *Implement Workflow Patterns with LangGraph* (IBM Skills Network, Kunal Makwana)
- *Mastering Agentic Design Patterns with LangGraph* (Mahendra Medapati)

*Traducción y adaptación educativa por: Claude Code (2026-09-10)*
