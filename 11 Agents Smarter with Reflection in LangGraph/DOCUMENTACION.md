# 📚 DOCUMENTACIÓN: Agentes con Reflexión en LangGraph

**Proyecto 11 — Versión 2.0 (StateGraph v1.0+)**  
**Estado:** 🟢 HITO 1 COMPLETADO  
**Última actualización:** 2026-09-29

---

## 📑 Tabla de Contenidos

1. [Inicio Rápido](#inicio-rápido)
2. [Arquitectura Técnica](#arquitectura-técnica)
3. [Cómo Funciona](#cómo-funciona)
4. [Guía de Extensión](#guía-de-extensión)
5. [Troubleshooting](#troubleshooting)
6. [Referencias](#referencias)

---

## Inicio Rápido

### Requisitos

- Python 3.13 (env-llm-ia) ✅ o 3.14 (env-llm-314) ✅
- Ollama corriendo: `ollama serve`
- Modelo disponible: `ollama pull qwen2.5:7b`
- Dependencias: `pip install -r requirements.txt`

### Ejecutar el Notebook

```powershell
# 1. Activar PowerShell
$env:PYTHONIOENCODING = "utf-8"

# 2. Navegar
cd "C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\11 Agents Smarter with Reflection in LangGraph"

# 3. Abrir Jupyter
C:\workspace-vc\env-llm-ia\Scripts\jupyter.exe notebook reflection_agent.ipynb

# 4. En navegador: Kernel → Restart & Run All
```

**Tiempo estimado:** 15-20 minutos  
**Output:** 
- `outputs/benchmark.jsonl` — métricas de reflexión
- `outputs/convergencia_reflexion.png` — gráficos

---

## Arquitectura Técnica

### Patrón: Generate → Reflect → Revise (Sistema 2)

```
[Usuario] "Escribe un post de LinkedIn"
    ↓
[GENERATE - Sistema 1: Rápido]
    ↓
[REFLECT - Sistema 2: Deliberado]
    ↓
[DECIDE] ¿Score ≥ 7 o ciclos máximos?
    ├─ Sí: END
    └─ No: VUELVE A GENERATE
    ↓
[FINAL OUTPUT] Post mejorado
```

### LangGraph StateGraph

**¿Por qué StateGraph vs MessageGraph?**

MessageGraph estaba deprecado en LangGraph v1.0. StateGraph proporciona:
- ✅ **Estado tipado:** TypedDict con validación
- ✅ **Auditoría completa:** cycle_count, drafts[], reflections[], quality_scores[]
- ✅ **Reducers:** operator.add acumula ciclos automáticamente
- ✅ **Type hints:** Mejor debugging y documentación

### ReflectionState (Tipado)

```python
class ReflectionState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]    # Acumula
    drafts: Annotated[list[str], operator.add]              # Acumula
    reflections: Annotated[list[str], operator.add]         # Acumula
    quality_scores: Annotated[list[float], operator.add]    # Acumula
    cycle_count: int                                         # Contador
    final_output: str                                        # Respuesta final
```

### 3 Nodos: Generate, Reflect, Router

**1. Generation Node**
- Input: state["messages"] (historial)
- Output: Post generado (AIMessage)
- LLM: qwen2.5:7b (configurable en config.ini)
- Temperature: 0.3 (determinista moderado)

**2. Reflection Node**
- Input: state["messages"] (post generado)
- Output: Evaluación crítica (HumanMessage como feedback)
- Criterios: 7 aspectos (claridad, tono, engagement, etc.)
- Temperature: 0.2 (determinista, crítica objetiva)

**3. Router (should_continue)**
- Lógica: `if cycle_count >= max_cycles: return "end"`
- Parada: máximo 4 ciclos (configurable)
- Alternativa futura: convergencia automática

---

## Cómo Funciona

### Configuración (config.ini)

```ini
[ollama]
base_url = http://localhost:11434
model_name = qwen2.5:7b
temperature = 0.3
max_tokens = 2000

[agente]
max_reflection_cycles = 4
quality_threshold = 0.7

[reflection_criteria]
check_clarity = true
check_engagement = true
check_completeness = true
```

### Ejecución Paso a Paso

```python
# 1. Estado inicial
initial_state = {
    "messages": [HumanMessage(content="...")],
    "drafts": [],
    "reflections": [],
    "quality_scores": [],
    "cycle_count": 0,
    "final_output": ""
}

# 2. Invocar workflow
response = workflow.invoke(initial_state)

# 3. Acceder a auditoría
print(response['cycle_count'])        # 4
print(response['quality_scores'])     # [8.38, 10.0, 10.0, 10.0, 10.0]
print(response['final_output'])       # Post mejorado
```

### Métricas Capturadas

```json
{
  "timestamp": "2026-09-29T...",
  "modelo": "qwen2.5:7b",
  "tema": "Computación cuántica aplicada a high trading",
  "num_cycles": 4,
  "quality_progression": [8.38, 10.0, 10.0, 10.0, 10.0],
  "initial_score": 8.38,
  "final_score": 10.0,
  "improvement": 1.62,
  "convergence_rate": 0.081,
  "wall_time_seconds": 105.57
}
```

---

## Guía de Extensión

### Cambiar Dominio (LinkedIn → Emails)

**En Notebook, actualizar prompts:**

```python
GENERATION_PROMPT = """Eres un experto en emails profesionales.
Genera el mejor email basándote en la solicitud del usuario."""

REFLECTION_PROMPT = """Eres crítico de emails profesionales.
Evalúa claridad, tono, call-to-action, profesionalismo."""
```

### Agregar Nuevo Criterio de Evaluación

```python
# Actual: 7 criterios en REFLECTION_PROMPT
# Nuevo: Agregar en el prompt

REFLECTION_PROMPT = """...
8. **Originalidad:** ¿Aporta perspectiva diferenciada?
..."""
```

### Modificar Máximo de Ciclos

```ini
[agente]
max_reflection_cycles = 5  # Cambiar de 4 a 5
```

### Ejecutar Múltiples Temas

```python
temas = [
  "Tema 1: IA y agentes",
  "Tema 2: Computación cuántica",
  "Tema 3: Reflexión deliberada"
]

for tema in temas:
  # Ejecutar workflow
  response = workflow.invoke(...)
  # Guardar métricas
  benchmark.guardar_metricas([metrica])
```

---

## Troubleshooting

### Problema: "Connection refused" a Ollama

**Causa:** Ollama no está corriendo  
**Solución:**
```bash
ollama serve  # En terminal separada
```

### Problema: Score no mejora de ciclo a ciclo

**Causa:** Prompt de reflexión es vago  
**Solución:** Hacer criterios más específicos en REFLECTION_PROMPT

### Problema: "variable messages should be a list"

**Causa:** Pasando estado completo en lugar de state["messages"]  
**Solución:** Verificar que `generate_chain.invoke({"messages": state["messages"]})`

### Problema: "Graph must have an entrypoint"

**Causa:** StateGraph requiere edge START → generate explícito  
**Solución:** Verificar `graph.add_edge(START, "generate")`

---

## Referencias

### Archivos del Proyecto

- **reflection_agent.ipynb** — Notebook principal (42 celdas, StateGraph v2.0)
- **config.ini** — Parámetros: Ollama, agente, reflection_criteria
- **benchmark.py** — Captura de métricas (SimpleReflectionBenchmark)
- **CHECKPOINT.md** — Hitos de avance (Hito 0 y 1 completados)
- **requirements.txt** — Dependencias: langchain>=1.4, langgraph>=1.0, ollama

### Conceptos Teóricos

- **Sistema 1 vs Sistema 2 (Kahneman):** "Thinking, Fast and Slow"
- **LangGraph:** https://python.langchain.com/docs/langgraph
- **StateGraph vs MessageGraph:** MessageGraph deprecated v1.0, usar StateGraph
- **Ollama:** https://ollama.ai

### Métricas de Reflexión

- **Convergencia:** Velocidad de mejora (0.0-1.0)
- **Ciclos:** Iteraciones de generate-reflect
- **Mejora:** Diferencia score final - inicial
- **Latencia:** Tiempo total en segundos

---

## Estado del Proyecto

| Hito | Fecha | Estado | Descripción |
|------|-------|--------|-------------|
| 0 | 2026-09-28 | 🟢 ✅ | Arquitectura + Documentación |
| 1 | 2026-09-29 | 🟢 ✅ | StateGraph v1.0+, Notebook ejecutado |
| 2 | 2026-09-30+ | ⬜ Pendiente | Validación estadística (5+ temas) |

---

**Versión:** 2.0 (StateGraph)  
**Framework:** LangChain 1.x + LangGraph 1.0+  
**Python:** 3.13 ✅ y 3.14 ✅  
**Status:** 🟢 Listo para producción
