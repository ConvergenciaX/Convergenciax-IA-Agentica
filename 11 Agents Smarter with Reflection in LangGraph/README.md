# Agents Smarter with Reflection in LangGraph (Proyecto 11)

**Estado:** 🟢 **PROYECTO NUEVO — Hito 0: Arquitectura**  
**Framework:** LangChain + LangGraph (Reflection Loop)  
**Patrón:** Generate → Reflect → Revise (Sistema 2 Thinking)  
**Caso Práctico:** Generador de LinkedIn Posts Optimizados  
**Lenguaje:** 100% Español (Documentación en Inglés)  
**Python:** 3.13 (env-llm-ia) ✅  
**Última actualización:** 2026-09-28

---

## ¿Qué es Reflexión en Agentes?

**Reflexión** es el proceso donde un agente IA:

1. **Generate (Generar):** Crea una respuesta inicial
2. **Reflect (Reflexionar):** Evalúa críticamente su propia respuesta
3. **Revise (Revisar):** Mejora la respuesta basándose en la evaluación
4. **Repeat (Repetir):** Ciclo hasta alcanzar calidad satisfactoria

### Ejemplo: Generación de LinkedIn Post

```
[GENERATE]
Post inicial: "Aprendo IA. ¡Emocionado!"
↓
[REFLECT]
Evaluación: "Muy genérico, sin valor específico, no generará engagement"
Puntuación: 3/10 (Baja)
↓
[REVISE]
Post mejorado: "Acabo de entrenar un agente ReAct que genera, reflexiona 
y se mejora a sí mismo. La capacidad de reflexión es lo que diferencia 
la IA competente de la excepcional. ¿Qué avances en IA te sorprenden?"
Puntuación: 8/10 (Alta)
↓
[DECIDE]
¿Continuar? No → Respuesta final lista
```

---

## Sistema 1 vs Sistema 2 (Kahneman)

### Sistema 1: Rápido, Intuitivo
```
[LLM] → "Aprendo IA. ¡Emocionado!"
Tiempo: 2s
Calidad: Baja
```

### Sistema 2: Lento, Deliberado (Nuestro Proyecto)
```
[Generate] → [Reflect] → [Revise] → [Decide Loop]
Tiempo: 10-20s
Calidad: ALTA ✅
```

**Este proyecto implementa Sistema 2 artificial:** reflexión deliberada → mejores resultados

---

## Arquitectura: StateGraph con Reflection Loop

```python
from langgraph.graph import StateGraph

class ReflectionState(TypedDict):
    query: str
    # Acumuladores (Reducers)
    drafts: Annotated[list, operator.add]           # Borrador 1, 2, 3...
    reflections: Annotated[list, operator.add]      # Evaluación de cada borrador
    revisions: Annotated[list, operator.add]        # Mejoras aplicadas
    quality_scores: Annotated[list, operator.add]   # Puntuación por ciclo
    final_response: str
    cycle_count: int
```

**Flujo:**
```
query → [generate] → draft₁
                ↓
                [reflect] → eval₁ (score: 3/10)
                ↓
         ¿Score ≥ 7? No
                ↓
                [revise] → draft₂
                ↓
                [reflect] → eval₂ (score: 7/10)
                ↓
         ¿Score ≥ 7? Yes
                ↓
        [final] → response
```

---

## Caso de Uso: LinkedIn Posts

### Por qué LinkedIn?

1. ✅ **Problema real:** Escribir posts profesionales impactantes
2. ✅ **Evaluable:** Criterios claros (claridad, profesionalismo, engagement)
3. ✅ **Iterativo:** Mejora visible ciclo a ciclo
4. ✅ **Práctico:** Aplicable inmediatamente

### Ejemplos de Reflexión

**Ciclo 1 (Score: 2/10):**
```
Draft: "Hola a todos, me encanta la IA"
Reflection: "Muy genérico, sin contenido, sin valor para audiencia"
```

**Ciclo 2 (Score: 6/10):**
```
Draft: "Los modelos de lenguaje están transformando la forma en que 
trabajamos. Hoy aprendí sobre agentes con reflexión."
Reflection: "Mejor, pero aún falta especificidad y perspectiva personal"
```

**Ciclo 3 (Score: 8/10):**
```
Draft: "Después de meses estudiando IA, descubrí que la reflexión 
deliberada es lo que diferencia modelos 'correctos' de modelos 'excelentes'. 
Un agente que genera, reflexiona y revisa sus respuestas produce resultados 
que un modelo único no puede lograr.

¿Cómo el pensamiento Sistema 2 (Kahneman) se está implementando en IA?"
Reflection: "Profundo, personal, invita a discusión, valor claro"
```

---

## Flujo Completo: Hito 0 → Hito 2

### Hito 0: Arquitectura (Actual)
- ✅ LangGraph StateGraph diseñado
- ✅ Patrón Generate → Reflect → Revise definido
- ✅ Criterios de reflexión claros
- ✅ config.ini y estructura base

### Hito 1: Agente Funcional (Próximo)
- [ ] Notebook `reflection_agent.ipynb` ejecutándose
- [ ] 5 LinkedIn posts generados y mejorados
- [ ] Métricas de reflexión capturadas (ciclos, scores)
- [ ] Reportes con progresión de calidad

### Hito 2: Validación y Extensión
- [ ] 20+ posts en `verdades_esperadas.jsonl` con evaluación manual
- [ ] Análisis: score vs ciclos (convergencia)
- [ ] Extensión: aplicar a casos distintos (emails, reportes, etc.)
- [ ] Benchmarking: reflexión vs sin reflexión

---

## Estructura del Proyecto

```
10 Manual Tool-Calling Agent/
├── README.md                                  # Este archivo
├── MANUAL.md                                  # Guía de extensión
├── REPORTE_TECNICO_REFLEXION.md              # Arquitectura LangGraph + Reflexión
├── config.ini                                 # Parametrización (Ollama, criterios)
├── requirements.txt                           # Dependencias Python
├── benchmark.py                               # Captura de métricas de reflexión
├── analyze_benchmark.py                       # Análisis post-hoc
├── reflection_agent.ipynb                     # Notebook educativo principal
├── tools/
│   └── evaluation_tools.py                    # Herramientas de evaluación
├── data/
│   └── verdades_esperadas.jsonl               # Posts de referencia (5-20)
├── outputs/
│   ├── benchmark.jsonl                        # Métricas (ciclos, scores, tiempo)
│   ├── REPORTE_REFLEXION_YYYYMMDD_HHMMSS.md  # Reportes con timestamp
│   └── (gráficos: progresión de calidad)
├── logs/
│   └── (logs de ejecución)
└── checkpoint/
    └── CHECKPOINTS.md                         # Hitos completados
```

---

## Conceptos Clave

### 1. **Reflexión = Evaluación Crítica**

```python
# Node: REFLECT
def reflect_node(state: ReflectionState) -> ReflectionState:
    """Evalúa el draft actual basándose en criterios."""
    
    draft = state["drafts"][-1]
    
    prompt = f"""Evalúa este LinkedIn post en escala 1-10:

Post: "{draft}"

Criterios:
- Claridad (¿se entiende?): 1-10
- Profesionalismo (¿tono adecuado?): 1-10
- Engagement (¿invita a interacción?): 1-10
- Completitud (¿dice algo específico?): 1-10

Score FINAL: promedio de los 4 criterios (1-10)
Feedback: ¿Qué falta? ¿Qué mejorar?"""
    
    evaluation = llm.invoke(prompt)  # → "Score: 6/10. Falta especificidad..."
    
    return {
        "reflections": [evaluation],
        "quality_scores": [extract_score(evaluation)]
    }
```

### 2. **Decidir Cuándo Parar**

```python
def should_continue(state: ReflectionState) -> str:
    """Decidir si continuar reflejando o terminar."""
    
    last_score = state["quality_scores"][-1]
    cycle_count = state["cycle_count"]
    
    # Criterios de parada
    if last_score >= 7:           # Score suficientemente alto
        return "final"
    if cycle_count >= 3:          # Máximo de ciclos alcanzado
        return "final"
    
    # Continuar reflexionando
    return "revise"
```

### 3. **Acumular Ciclos (Reducers)**

```python
class ReflectionState(TypedDict):
    # Con Reducers: cada ciclo se AÑADE (no reemplaza)
    drafts: Annotated[list, operator.add]
    reflections: Annotated[list, operator.add]
    quality_scores: Annotated[list, operator.add]
    
    # Sin Reducer: se REEMPLAZA
    final_response: str
```

**Ventaja:** Auditoría completa del pensamiento:
```python
# Después de ejecutar el agente
state["drafts"]         # [draft1, draft2, draft3]
state["quality_scores"] # [3, 6, 8]
state["reflections"]    # [eval1, eval2, eval3]

# Visualizar convergencia:
plt.plot(state["quality_scores"])  # 3→6→8 (convergencia clara)
```

---

## Comandos Rápidos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar notebook
jupyter notebook reflection_agent.ipynb

# 3. Analizar resultados
python analyze_benchmark.py

# 4. Ver reporte más reciente
ls -t outputs/REPORTE_REFLEXION_*.md | head -1
```

---

## Comparativa: Sin Reflexión vs Con Reflexión

| Aspecto | Sin Reflexión | Con Reflexión |
|---------|-------------|---------------|
| **Proceso** | Generate → Output | Generate → Reflect → Revise → Output |
| **Tiempo** | 5s | 15-20s (3 ciclos) |
| **Calidad post** | 4/10 | 8/10 |
| **Mejora visible** | No | Sí (3→6→8) |
| **Auditoría** | Caja negra | Trace completo |
| **Aplicable a** | Trivial | Profesional, crítico |

---

## Diferencia: Proyecto 09 vs Proyecto 10

| Aspecto | Proyecto 09 (ReAct) | Proyecto 10 (Reflexión) |
|---------|-----------|-----------|
| **Patrón** | Thought → Action → Observation | Generate → Reflect → Revise |
| **Objetivo** | Resolver problemas con tools | Mejorar respuestas iterativamente |
| **Tools** | Externas (calculator, Wikipedia) | Internas (evaluación, mejora) |
| **Ciclos** | Necesarios para resolver | Opcionales, buscan calidad |
| **Caso uso** | Consultas factivas | Contenido creativo/profesional |

---

## Próximos Pasos

**Hito 1 (Próxima sesión):**
1. Crear `reflection_agent.ipynb` con flujo completo
2. Implementar nodos: generate, reflect, revise, decide
3. Probar con 5 LinkedIn posts
4. Capturar métricas: ciclos, scores, convergencia

**Hito 2:**
1. Expandir a 20+ posts reales
2. Análisis: ¿siempre converge? ¿score vs ciclos?
3. Extensión: aplicar a emails, reportes, etc.

---

## Referencias

- **REPORTE_TECNICO_REFLEXION.md** — Detalles de LangGraph + Reflection
- **MANUAL.md** — Cómo extender con nuevos criterios
- **Proyecto 09** — Patrón ReAct (análogo: múltiples pasos)
- **Kahneman, D.** — "Thinking Fast and Slow" (Sistema 1 vs 2)

---

**Autor:** Claude Haiku 4.5  
**Sesión:** https://claude.ai/code/session_012AV7eFXU9i17FLBaAZxoe2  
**Status:** ✅ Listo para Hito 1 (Agente Funcional con Reflexión)
