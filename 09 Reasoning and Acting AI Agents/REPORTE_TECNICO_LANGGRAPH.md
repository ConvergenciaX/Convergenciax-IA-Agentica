# 📊 REPORTE TÉCNICO — LangGraph + Reducers en ReAct Agents

**Fecha:** 2026-09-20  
**Versión:** 1.0  
**Proyecto:** Reasoning and Acting AI Agents  
**Framework:** LangChain + LangGraph  

---

## 1. Introducción: ¿Por Qué LangGraph?

### Problema: ReAct Clásico vs ReAct Moderno

**ReAct Clásico (LangChain puro):**
```
Thought: "Necesito calcular 2 + 2"
Action: calculator
Action Input: 2 + 2
Observation: 4
Thought: "Ya tengo la respuesta"
→ Final Answer: 4
```

**Problema:** El trace (Thought/Action/Observation) se pierde en la respuesta textual. Para **capturar métricas de razonamiento** (¿cuántos pasos? ¿qué tools se usaron?), hay que parsear texto manualmente.

**ReAct Moderno (LangGraph + Reducers):**
```python
state["reasoning_steps"] = [
    {"thought": "Necesito calcular...", "action": "calculator", "observation": 4},
    {"thought": "Ya tengo...", "action": None, "observation": None}
]
```

**Ventaja:** El trace es **datos estructurados en el state**, no texto parseado. Benchmarking automático: `len(state["reasoning_steps"])` = número de pasos.

---

## 2. Conceptos Clave de LangGraph

### 2.1 ¿Qué es un StateGraph?

Un **StateGraph** es un grafo dirigido donde:
- **Nodos** = funciones de procesamiento (think, act, validate)
- **Aristas** = transiciones entre nodos
- **State** = diccionario compartido que fluye a través del grafo

```python
from langgraph.graph import StateGraph
from typing import TypedDict

class ReActState(TypedDict):
    query: str
    reasoning_steps: list  # Información compartida
    final_answer: str

workflow = StateGraph(ReActState)
workflow.add_node("think", think_node)
workflow.add_node("act", act_node)
workflow.add_edge("think", "act")
```

### 2.2 ¿Qué es un Reducer?

Un **Reducer** es una función que **agrupa valores** en lugar de reemplazarlos cuando múltiples nodos escriben a la misma clave de estado.

```python
from typing import Annotated
import operator

class ReActState(TypedDict):
    query: str
    # ↓ Reducer: operator.add concatena listas
    reasoning_steps: Annotated[list, operator.add]
    observations: Annotated[list, operator.add]
```

**Sin Reducer:**
```python
state["reasoning_steps"] = step1  # Sobrescribe
state["reasoning_steps"] = step2  # Pierde step1
```

**Con Reducer (operator.add):**
```python
state["reasoning_steps"] = [step1]  # reasoning_steps = [step1]
state["reasoning_steps"] = [step2]  # reasoning_steps = [step1, step2] ← Agrega
```

---

## 3. Arquitectura del Agente ReAct con LangGraph

### 3.1 State Type

```python
from typing import Annotated
import operator

class ReActState(TypedDict):
    query: str                    # Entrada del usuario
    
    # ← Reducers: acumulan en lugar de reemplazar
    reasoning_steps: Annotated[list, operator.add]    # Cada paso Thought/Action
    observations: Annotated[list, operator.add]       # Cada observación
    tools_used: Annotated[list, operator.add]         # Tools invocadas
    
    final_answer: str             # Salida (sobrescribible, sin reducer)
    iteration_count: int          # Contador de ciclos
```

**Clave:** `operator.add` concatena listas, no las reemplaza.

### 3.2 Nodos del Grafo

```python
def think_node(state: ReActState) -> ReActState:
    """
    Nodo de razonamiento: genera Thought.
    Llama al LLM para razonar sobre la consulta.
    """
    prompt = f"""
    Dada la consulta: {state['query']}
    Pasos anteriores: {state['reasoning_steps']}
    
    ¿Cuál es tu siguiente pensamiento?
    Responde solo con: Thought: <pensamiento>
    """
    
    llm = ...  # LLM configurado con Ollama
    thought = llm.invoke(prompt)
    
    return {
        "reasoning_steps": [{
            "type": "thought",
            "content": thought
        }]  # ← Reducer: se agrega a reasoning_steps existente
    }


def act_node(state: ReActState) -> ReActState:
    """
    Nodo de acción: selecciona y ejecuta una tool.
    Devuelve la observación de la tool.
    """
    # Extraer el pensamiento más reciente
    last_step = state["reasoning_steps"][-1] if state["reasoning_steps"] else {}
    
    # Decidir qué tool usar
    tool_name = select_tool(last_step["content"])
    tool = get_tool(tool_name)  # Calculadora, Wikipedia, etc.
    
    # Ejecutar tool
    observation = tool.run(...)
    
    return {
        "reasoning_steps": [{
            "type": "action",
            "tool": tool_name,
            "observation": observation
        }],
        "tools_used": [tool_name],  # ← Reducer: agrega tool a lista
        "observations": [observation]  # ← Reducer: agrega observación
    }
```

### 3.3 Compilación del Grafo

```python
workflow = StateGraph(ReActState)

# Agregar nodos
workflow.add_node("think", think_node)
workflow.add_node("act", act_node)
workflow.add_node("answer", answer_node)

# Agregar aristas (transiciones)
workflow.add_edge("think", "act")
workflow.add_edge("act", "think")  # Loop: piensa de nuevo si no hay respuesta
workflow.add_conditional_edges(
    "think",
    lambda state: "answer" if should_answer(state) else "act",
    {"answer": "answer", "act": "act"}
)

# Compilar
app = workflow.compile()

# Ejecutar
result = app.invoke({
    "query": "¿Cuánto es 2 + 2?",
    "reasoning_steps": [],
    "observations": [],
    "tools_used": [],
    "iteration_count": 0
})

# Acceder a razonamiento acumulado
print(f"Pasos totales: {len(result['reasoning_steps'])}")
print(f"Tools usadas: {result['tools_used']}")
print(f"Respuesta: {result['final_answer']}")
```

---

## 4. Reducers Disponibles en LangGraph

### 4.1 Operators (módulo `operator`)

```python
import operator
from typing import Annotated

class State(TypedDict):
    # Concatenar listas
    messages: Annotated[list, operator.add]
    
    # Suma numérica (útil para contadores)
    total_tokens: Annotated[int, operator.add]
    
    # Última actualización (reemplazar)
    last_message: str
```

### 4.2 Reducer Personalizado

```python
def custom_reducer(existing: list, new_items: list) -> list:
    """Reducer que fusiona listas sin duplicados."""
    combined = existing + new_items if existing else new_items
    return list(dict.fromkeys(combined))  # Remover duplicados

class State(TypedDict):
    unique_tools: Annotated[list, custom_reducer]
```

---

## 5. Captura de Métricas con LangGraph

### 5.1 Métrica Automática: Pasos de Razonamiento

```python
def capturar_metricas(state: ReActState, wall_time: float) -> dict:
    """
    Extrae métricas del state después de ejecutar el agente.
    
    LangGraph + Reducers lo hace trivial:
    - reasoning_steps ya está acumulado
    - tools_used ya está acumulado
    - observations ya está acumulado
    """
    
    num_steps = len(state["reasoning_steps"])
    num_tools = len(set(state["tools_used"]))  # Tools únicos
    
    return {
        "wall_time_seconds": wall_time,
        "num_reasoning_steps": num_steps,
        "unique_tools_used": num_tools,
        "total_observations": len(state["observations"]),
        # Sin LangGraph (texto parseado): imposible de hacer fiable
        # Con LangGraph (state estructurado): trivial
    }
```

### 5.2 Integración con benchmark.py

```python
# reasoning_acting_agent.ipynb

from benchmark import medir_y_registrar, guardar_metricas
import time

# Ejecutar agente
t0 = time.perf_counter()
result = app.invoke({...})
wall_time = time.perf_counter() - t0

# Capturar métrica (simple porque state es estructurado)
metrica = medir_y_registrar(
    agent_result=result,
    wall_time=wall_time,
    model_name="qwen2.5:7b",
    temperature=0.3,
    variant_label="qwen-react",
    consulta="¿Cuánto es 2+2?"
)

# Guardar
metricas = [metrica]
guardar_metricas(metricas)
```

---

## 6. Comparativa: LangChain puro vs LangGraph

| Aspecto | LangChain (ConversableAgent) | LangGraph (StateGraph) |
|--------|--------|---------|
| **Captura de trace** | Texto → parseado manualmente | State estructurado → acceso directo |
| **Conteo de pasos** | `len(re.findall("Thought:", text))` 🔴 | `len(state["reasoning_steps"])` ✅ |
| **Tools usadas** | Parsing de "Action: tool_name" | `state["tools_used"]` lista clara |
| **Auditoría completa** | Difícil (texto opaco) | Fácil (state es datos) |
| **Benchmarking** | Manual, error-prone | Automático, robusto |
| **Debugging** | Ver output textual | Inspeccionar state en cada nodo |
| **Escalabilidad** | OK para 2-3 herramientas | Excelente para 5+ herramientas |

---

## 7. Mejores Prácticas en Este Proyecto

### 7.1 Definir State Explícitamente

```python
# ✅ BIEN: State es TypedDict con reducers claros
class ReActState(TypedDict):
    query: str
    reasoning_steps: Annotated[list, operator.add]
    observations: Annotated[list, operator.add]
    tools_used: Annotated[list, operator.add]
    final_answer: str

# ❌ MAL: State es dict genérico, reducers implícitos
state = {}
state["reasoning_steps"] = step1  # ¿Reducer o sobrescritura?
```

### 7.2 Separar Nodos por Responsabilidad

```python
# ✅ BIEN: Cada nodo tiene un propósito claro
workflow.add_node("think", think_node)       # Solo razonar
workflow.add_node("act", act_node)           # Solo actuar
workflow.add_node("observe", observe_node)   # Solo observar

# ❌ MAL: Todo en un nodo
workflow.add_node("step", step_node)  # think+act+observe mezclados
```

### 7.3 Usar Conditional Edges para Lógica Compleja

```python
# ✅ BIEN: Lógica clara de cuándo parar
workflow.add_conditional_edges(
    "think",
    lambda state: "answer" if should_answer(state) else "act",
    {"answer": "answer", "act": "act"}
)

# ❌ MAL: Lógica en el nodo mismo
def think_node(state):
    ...
    if should_answer(state):
        return {"final_answer": ...}
    else:
        return {"reasoning_steps": [...]}  # Ambiguo
```

### 7.4 Importar desde benchmark.py (Nunca Inline)

```python
# ✅ BIEN: Importar funciones de benchmarking
from benchmark import medir_y_registrar, guardar_metricas

# ❌ MAL: Definir benchmark inline
def custom_measure():
    ...

# Esto aplica a todos los proyectos de la fábrica ia-dev
```

---

## 8. Documentación de Campos en State

Tabla de referencia para cada campo de `ReActState`:

| Campo | Tipo | Reducer | Propósito | Ejemplo |
|-------|------|---------|----------|---------|
| `query` | str | — | Consulta del usuario | "¿Cuánto es 2+2?" |
| `reasoning_steps` | list | `operator.add` | Acumula Thought/Action | `[{"thought": "..."}, {"action": "calc"}]` |
| `observations` | list | `operator.add` | Acumula observaciones de tools | `[4, "información"]` |
| `tools_used` | list | `operator.add` | Tools invocadas (acumula) | `["calculator", "wikipedia"]` |
| `final_answer` | str | — | Respuesta final (sobrescribible) | "La respuesta es 4" |
| `iteration_count` | int | — | Contador de ciclos | 3 |

---

## 9. Troubleshooting Común

### Problema: "reasoning_steps no se acumula"

```python
# ❌ INCORRECTO: Sin Annotated
class ReActState(TypedDict):
    reasoning_steps: list  # ¿Reducer o no?

# ✅ CORRECTO: Anotado con reducer
class ReActState(TypedDict):
    reasoning_steps: Annotated[list, operator.add]
```

### Problema: "Tools se repiten en la lista"

```python
# ❌ Sin deduplicar
tools_list = state["tools_used"]  # [calculator, calculator, wikipedia]

# ✅ Con deduplicación
tools_unique = list(set(state["tools_used"]))  # [calculator, wikipedia]

# O mejor: usar reducer personalizado que deduplique automáticamente
def unique_reducer(existing, new):
    combined = (existing or []) + new
    return list(dict.fromkeys(combined))

class ReActState(TypedDict):
    tools_used: Annotated[list, unique_reducer]
```

---

## 10. Referencias

- **LangGraph Docs:** https://docs.langchain.com/oss/python/langgraph
- **ReAct Paper:** https://arxiv.org/abs/2210.03629
- **Proyecto Relacionado:** `07 AI Math Assistant with LangChain` (tool calling clásico)
- **Patrón de Benchmark:** `benchmark.py` en este proyecto (nunca inline)

---

## 11. Conclusión

**LangGraph + Reducers transforman ReAct de un patrón textual opaco a datos estructurados:**

- ✅ **State explícito** → auditoría completa del razonamiento
- ✅ **Reducers** → acumulación automática de pasos sin parsear
- ✅ **Benchmarking trivial** → contar pasos = `len(state["reasoning_steps"])`
- ✅ **Debugging claro** → inspeccionar state en cada nodo
- ✅ **Escalable** → agregar tools sin cambiar arquitectura

Este proyecto demuestra **por qué LangGraph es mejor que LangChain puro para agentes complejos**.

---

*Documento técnico: 2026-09-20*  
*Para dudas sobre LangGraph, ver `MANUAL.md` y el notebook `reasoning_acting_agent.ipynb`*
