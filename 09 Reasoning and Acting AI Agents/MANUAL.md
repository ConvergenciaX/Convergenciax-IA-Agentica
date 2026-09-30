# MANUAL TÉCNICO — Reasoning and Acting AI Agents

**Guía de desarrollo para Hito 1 y beyond**

---

## 1. Agregar una Nueva Tool

### Paso 1: Definir en `tools.py`

```python
from langchain.tools import Tool
from typing import Union

def mi_tool_execute(input: str) -> str:
    """Lógica de la herramienta"""
    try:
        result = do_something(input)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

mi_tool = Tool(
    name="mi_tool",
    func=mi_tool_execute,
    description="Descripción clara de qué hace esta tool"
)
```

### Paso 2: Registrar en el Agente

```python
# reasoning_acting_agent.ipynb
from tools import calculator, wikipedia, datetime_tool, unit_converter, mi_tool

tools = [calculator, wikipedia, datetime_tool, unit_converter, mi_tool]
```

### Paso 3: Testear

Agregar caso en `data/verdades_esperadas.jsonl`:
```json
{"consulta": "test de mi_tool", "respuesta_esperada": "resultado esperado", "herramientas_esperadas": ["mi_tool"]}
```

---

## 2. Agregar Casos de Prueba

### Formato de `verdades_esperadas.jsonl`

```json
{
  "id": 11,
  "consulta": "Tu pregunta aquí",
  "respuesta_esperada": "Respuesta esperada o palabra clave",
  "herramientas_esperadas": ["tool1", "tool2"],
  "dificultad": "facil|medio|dificil"
}
```

### Ejecutar Evaluación

```python
# En reasoning_acting_agent.ipynb

from benchmark import evaluar_exactitud, evaluar_razonamiento

for caso in casos_prueba:
    resultado = app.invoke({"query": caso["consulta"], ...})
    exactitud = evaluar_exactitud(resultado["final_answer"], caso["respuesta_esperada"])
    razonamiento = evaluar_razonamiento(resultado["reasoning_steps"])
    
    print(f"Exactitud: {exactitud}")
    print(f"Pasos ReAct: {razonamiento['num_pasos']}")
```

---

## 3. Interpretar Reportes de Benchmark

### Archivo: `REPORTE_REACT_YYYYMMDD_HHMMSS.md`

**Secciones:**
- **Resumen Ejecutivo**: Contexto de ejecución
- **Métricas por Modelo**: Tabla con latencia, pasos, tools por modelo
- **Análisis de Razonamiento**: Distribución de pasos ReAct
- **Recomendaciones**: Insights de los resultados

**Ejemplo de interpretación:**
```
| Modelo | Consultas | Latencia | Pasos |
|--------|-----------|----------|-------|
| qwen2.5:7b | 3 | 2.5s | 3.0 |
| llama3.1:8b | 3 | 4.2s | 4.0 |

→ qwen2.5 es más rápido pero llama3.1 razona más (más pasos = más profundo)
```

### Gráficos Generados

| Gráfico | Propósito |
|---------|----------|
| 01_comparacion_latencia.png | Distribución de tiempos (box plot) |
| 02_comparacion_pasos.png | Número de pasos ReAct por modelo |
| 03_tradeoff_latencia_pasos.png | Scatter: ¿más pasos = más lentitud? |

---

## 4. Workflow de Desarrollo

### Hito 1: Agente Funcional

**Semana 1:**
1. Crear `tools.py` con 4 tools implementadas
2. Crear `reasoning_acting_agent.ipynb` con:
   - Celdas 1-3: Verificación de entorno
   - Celda 4: Cargar tools
   - Celda 5: Construir StateGraph
   - Celda 6: Ejecutar casos de prueba
3. Testear con 3 casos de `verdades_esperadas.jsonl`
4. Ejecutar `python analyze_benchmark.py`
5. Revisar reportes (latencia, pasos, exactitud)

**Criterio de éxito:**
- ✅ Notebook ejecuta sin errores
- ✅ ReAct trace visible (Thought → Action → Observation)
- ✅ Exactitud ≥80% en casos de prueba
- ✅ Reportes generados con timestamp

### Hito 2: Validación Completa

**Semana 2-3:**
1. Expandir `verdades_esperadas.jsonl` a 20+ casos
2. Agregar casos complejos (multi-step reasoning)
3. Benchmark comparativo: qwen vs llama vs mistral
4. Análisis de trade-off: latencia vs exactitud vs pasos
5. Optimizar prompts del agente
6. Documentación finalizada

**Criterio de éxito:**
- ✅ Exactitud ≥95% en 20+ casos
- ✅ Razonamiento visible y coherente
- ✅ Reporte profesional con comparativas

---

## 5. Customización del Razonamiento

### Cambiar Prompt del Agente

```python
# reasoning_acting_agent.ipynb en celda de think_node

THINK_PROMPT = """
Eres un agente de razonamiento experto.
Dada la consulta: {query}
Pasos previos: {history}

Responde SOLO con:
Thought: [tu pensamiento aquí]
Action: [tool a usar]
Action Input: [entrada a la tool]

NO agregues texto adicional.
"""
```

### Cambiar Lógica de Parada

```python
def should_stop(state: ReActState) -> bool:
    """Decidir si el agente debe parar"""
    
    # Opción 1: Ya tiene respuesta
    if state["final_answer"]:
        return True
    
    # Opción 2: Alcanzó máximo de pasos
    if len(state["reasoning_steps"]) >= 10:
        return True
    
    # Opción 3: Last step fue successful
    if state["observations"] and state["observations"][-1]:
        return True
    
    return False
```

---

## 6. Debugging de ReAct

### Ver Estado Completo

```python
# reasoning_acting_agent.ipynb

result = app.invoke({"query": "tu pregunta", ...})

print("=== REASONING TRACE ===")
for i, step in enumerate(result["reasoning_steps"]):
    print(f"\nPaso {i+1}:")
    print(f"  Tipo: {step.get('type')}")
    print(f"  Contenido: {step.get('content', step.get('tool'))}")

print(f"\n=== OBSERVACIONES ===")
for obs in result["observations"]:
    print(f"  - {obs}")

print(f"\n=== RESPUESTA FINAL ===")
print(result["final_answer"])

print(f"\n=== MÉTRICAS ===")
print(f"Pasos: {len(result['reasoning_steps'])}")
print(f"Tools usadas: {result['tools_used']}")
```

### Logs Detallados

```python
# Activar en config.ini
[execution]
verbose = true
show_reasoning_trace = true
```

Esto mostrará cada transición de nodo en el notebook.

---

## 7. Configuración Avanzada

### Cambiar Modelo

```ini
# config.ini
[ollama]
model_name = llama3.1:8b-instruct-q2_K
temperature = 0.2  # Más determinístico
```

### Cambiar Parámetros ReAct

```ini
[agente]
max_iterations = 15  # Permitir más ciclos
verbose = true  # Ver trace completo
return_intermediate_steps = true  # Capturar pasos
```

### Cambiar Benchmarking

```ini
[benchmark]
enabled = true
variant_label = custom_label  # Para agrupar en reportes
```

---

## 8. Solución de Problemas

### Problema: "ReAct stack se infinito"

**Causa:** Lógica de parada incorrecta

**Solución:**
```python
def should_stop(state):
    # Agregar condición de parada más agresiva
    if len(state["reasoning_steps"]) >= max_iterations:
        return True  # ← Parar si alcanzó máximo
```

### Problema: "Tools no se invocan"

**Causa:** Formato de Action incorrecto en prompt

**Solución:** Revisar que el prompt dice exactamente cómo formatear Action/Action Input

```python
THINK_PROMPT = """
...
Action: [EXACTO nombre_de_tool]  # ← Coincidir con tool.name
Action Input: [entrada]
...
"""
```

### Problema: "Exactitud baja (< 50%)"

**Cause:** Prompt débil o tools incompletas

**Solución:**
1. Mejorar THINK_PROMPT con ejemplos
2. Verificar que tools devuelven resultados útiles
3. Agregar tool de "llamar a un humano" como fallback

---

## 9. Referencias

- **REPORTE_TECNICO_LANGGRAPH.md** → Conceptos de LangGraph
- **benchmark.py** → Funciones de captura y análisis
- **README.md** → Overview rápido
- **config.ini** → Todas las opciones de configuración

---

## 10. Checklist para Hito 1

- [ ] `tools.py` creado con 4 tools funcionales
- [ ] `reasoning_acting_agent.ipynb` creado (celdas 1-6)
- [ ] ReAct trace visible en output
- [ ] `benchmark.jsonl` se está llenando
- [ ] `analyze_benchmark.py` genera reportes con timestamp
- [ ] Exactitud ≥80% en casos de prueba
- [ ] README y MANUAL listos
- [ ] Checkpoint actualizado

---

*Documento técnico: 2026-09-20*  
*Para dudas específicas, consulta REPORTE_TECNICO_LANGGRAPH.md*
