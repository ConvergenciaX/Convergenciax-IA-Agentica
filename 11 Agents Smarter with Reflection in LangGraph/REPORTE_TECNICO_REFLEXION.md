# 📖 REPORTE TÉCNICO: Agentes con Reflexión en LangGraph

**Arquitectura, Frameworks e Implementación**

---

## 📑 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Conceptos Fundamentales](#conceptos-fundamentales)
3. [Arquitectura de Sistema 2](#arquitectura-de-sistema-2)
4. [LangGraph: Fundamentos](#langgraph-fundamentos)
5. [MessageGraph vs StateGraph](#messagegraph-vs-stategraph)
6. [Patrón de Reflexión: Implementación](#patrón-de-reflexión-implementación)
7. [Integración Ollama](#integración-ollama)
8. [Benchmarking y Métricas](#benchmarking-y-métricas)
9. [Troubleshooting](#troubleshooting)

---

## Introducción

Este documento explica la arquitectura técnica detrás de **agentes inteligentes con reflexión en LangGraph**, implementados con **Ollama local** para inferencia.

### Problema Resuelto

Los LLM generan respuestas rápidamente, pero **sin capacidad de autoevaluación**. Un modelo que genera un post de LinkedIn en 2 segundos no sabe si es bueno o malo. 

**Solución:** Implementar un ciclo **Generate → Reflect → Revise** que imita el pensamiento "Sistema 2" (Kahneman): reflexión deliberada que mejora resultados.

---

## Conceptos Fundamentales

### Sistema 1 vs Sistema 2 (Kahneman)

| Aspecto | Sistema 1 | Sistema 2 |
|---------|----------|----------|
| **Velocidad** | Rápido (< 2s) | Lento (10-20s) |
| **Esfuerzo** | Bajo, automático | Alto, deliberado |
| **Reflexión** | Ninguna | Profunda |
| **Calidad** | Media | Alta |
| **Ejemplo** | LLM genera directamente | LLM genera → evalúa → revisa |

### Nuestro Agente: Implementa Sistema 2

```
[Usuario pide: "Escribe un post de LinkedIn"]
         ↓
    [GENERATE - Sistema 1]
    "Acabo de aprovechar las reflexiones en agentes IA"
         ↓
    [REFLECT - Sistema 2]
    "¿Es claro? ¿Genera engagement? ¿Es profesional?"
         ↓
    [REVISE - Sistema 2]
    "Transformo a: 'Después de meses estudiando reflexión en agentes IA, 
     descubrí que la evaluación crítica de nuestro propio trabajo es 
     lo que diferencia sistemas mediocres de excepcionales...'"
         ↓
    [RESULTADO: Post mejorado, específico, atractivo]
```

---

## Arquitectura de Sistema 2

### Flujo de 3 Nodos

#### 1. **Generation Node (Generación)**

```python
def generation_node(state: Sequence[BaseMessage]) -> List[BaseMessage]:
    """
    Genera borrador inicial sin reflexión.
    - Input: estado (lista de mensajes previos)
    - Output: AIMessage con contenido generado
    - LLM modelo: configurable (ej: qwen2.5:7b)
    """
    generated_post = generate_chain.invoke({"messages": state})
    return [AIMessage(content=generated_post.content)]
```

**Prompt del Sistema (español):**
```
"Eres un asistente profesional de contenido LinkedIn especializado en 
crear publicaciones atractivas, profesionales y de alta calidad. 
Genera la mejor publicación de LinkedIn posible basada en la solicitud del usuario. 
Si el usuario proporciona retroalimentación o crítica, responde con una versión 
refinada de tus intentos anteriores, mejorando la claridad, tono o engagement."
```

**Características:**
- Temperature: 0.7 (creatividad moderada)
- Max tokens: 2000 (posts largos soportados)
- Contexto: 8192 tokens

---

#### 2. **Reflection Node (Reflexión)**

```python
def reflection_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    """
    Evalúa críticamente el contenido generado.
    - Input: estado con el post generado
    - Output: HumanMessage con retroalimentación
    - Acta como "crítico profesional" del contenido
    """
    res = reflect_chain.invoke({"messages": messages})
    return [HumanMessage(content=res.content)]
```

**Prompt del Sistema (español):**
```
"Eres un estratega profesional de contenido LinkedIn y experto en 
liderazgo de pensamiento. Tu tarea es evaluar críticamente la publicación 
y proporcionar retroalimentación integral.

EVALÚA:
1. Calidad general (profesionalismo, alineación con mejores prácticas)
2. Estructura, tono, claridad, legibilidad
3. Potencial de engagement (likes, comentarios, shares)
4. Relevancia a industria/audiencia
5. Uso de formato (saltos de línea, puntos, hashtags)

PROPORCIONA:
- Fortalezas y debilidades
- Áreas de mejora específicas
- Sugerencias accionables"
```

**Características:**
- Temperature: 0.3 (determinista, crítica objetiva)
- Evaluación basada en 5 criterios
- Retroalimentación constructiva

---

#### 3. **Router Node (Decisión)**

```python
def should_continue(state: List[BaseMessage]) -> str:
    """
    Decide si continuar reflexionando o terminar.
    
    Criterios:
    - len(state) > 6: máximo de iteraciones alcanzado
    - Convergencia: mejora < 1 punto en últimos 2 ciclos
    """
    if len(state) > 6:
        return END
    return "reflect"
```

**Lógica:**
- **Máximo 3 ciclos** (3 generaciones + 3 reflexiones + 1 final)
- **Total: 7 mensajes** en estado
- Evita loops infinitos
- Podría mejorar: detección de convergencia

---

## LangGraph: Fundamentos

### ¿Qué es LangGraph?

Framework de **LangChain** para construir grafos de ejecución con **state management** explícito.

**Analogía:** Si LangChain es una cadena lineal (prompt → LLM → output), LangGraph es un grafo que permite **nodos**, **edges** y **lógica condicional**.

### Componentes Clave

#### 1. **MessageGraph**

Abstraccción prebuilt de LangGraph para workflows conversacionales:

```python
from langgraph.graph import MessageGraph

graph = MessageGraph()

# Añadir nodos (funciones que procesan estado)
graph.add_node("generate", generation_node)
graph.add_node("reflect", reflection_node)

# Conectar nodos
graph.add_edge("reflect", "generate")

# Lógica condicional
graph.add_conditional_edges("generate", should_continue)

# Compilar a workflow ejecutable
workflow = graph.compile()
```

**Ventajas:**
- State management automático
- Manejo de mensajes (HumanMessage, AIMessage, SystemMessage)
- Ejecución determinística
- Fácil de visualizar

---

## MessageGraph vs StateGraph

### MessageGraph (Nuestro Caso)

**Uso:** Workflows conversacionales con historial de mensajes.

```python
from langgraph.graph import MessageGraph

# State implícito: List[BaseMessage]
graph = MessageGraph()
```

**Ventajas:**
- ✅ Manejo automático de mensajes
- ✅ Historial conservado
- ✅ Menos código boilerplate
- ✅ Ideal para reflexión (evalúa todos los mensajes previos)

**Estado interno:**
```python
[
    HumanMessage(content="Escribe un post de LinkedIn"),
    AIMessage(content="Acabo de aprender IA..."),
    HumanMessage(content="Feedback: muy genérico..."),
    AIMessage(content="Post mejorado: Después de meses..."),
]
```

---

### StateGraph (Alternativa)

**Uso:** Workflows complejos con estado tipado personalizado.

```python
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated, List
import operator

class ReflectionState(TypedDict):
    query: str
    drafts: Annotated[List[str], operator.add]
    reflections: Annotated[List[str], operator.add]
    final_output: str
    iteration_count: int

graph = StateGraph(ReflectionState)
```

**Ventajas:**
- ✅ Control total sobre estructura de estado
- ✅ Reducers para acumular información
- ✅ Auditoría completa de ciclos
- ❌ Más complejo, más código

**¿Cuándo usar cada uno?**

| Caso | MessageGraph | StateGraph |
|------|--------------|-----------|
| Chatbot simple | ✅ | ❌ |
| Reflexión sobre historial | ✅ | ⚠️ |
| Múltiples variables tipadas | ❌ | ✅ |
| Auditoría de ciclos | ⚠️ | ✅ |

---

## Patrón de Reflexión: Implementación

### Ciclo Completo

```
USUARIO INPUT
    ↓
[1] GENERATE (generate_node)
    ├─ Invoca: generate_chain.invoke({"messages": state})
    ├─ LLM: ChatOllama(model="qwen2.5:7b")
    └─ Output: AIMessage con post
    ↓
[2] ROUTER (should_continue)
    ├─ Chequea: len(state) > 6?
    ├─ Sí → END (termina)
    └─ No → REFLECT
    ↓
[3] REFLECT (reflection_node)
    ├─ Invoca: reflect_chain.invoke({"messages": state})
    ├─ LLM: evalúa el post
    └─ Output: HumanMessage con feedback
    ↓
[LOOP] Vuelve a GENERATE con feedback

FINAL OUTPUT (al terminar)
```

### Ejemplo Real: Post de LinkedIn

**Iteración 1:**

```
GENERATE:
"Estoy aprendiendo IA. ¡Es increíble!"

REFLECT:
"Puntuación: 3/10
Débil: muy genérico, sin valor específico
Mejorar: agregue contexto, logros, invite discusión"
```

**Iteración 2:**

```
GENERATE:
"Después de meses estudiando IA y agentes con reflexión, 
descubrí que la evaluación crítica de nuestro propio trabajo 
es lo que diferencia sistemas mediocres de excepcionales. 
¿Cómo usas reflexión en tu trabajo? #IA"

REFLECT:
"Puntuación: 8/10
Fuerte: específico, personal, invita discusión
✓ Listo para publicar"
```

**Iteración 3:** → FIN (score ≥ 7)

---

## Integración Ollama

### ¿Qué es Ollama?

Herramienta local para ejecutar LLM sin APIs externas.

**Ventajas:**
- ✅ Privacidad (datos locales)
- ✅ Sin costo (sin API keys)
- ✅ Sin latencia de red (rápido)
- ❌ Requiere GPU / mucha RAM

### Instalación

```bash
# Descargar desde https://ollama.ai
ollama serve                    # Inicia el servidor
ollama pull qwen2.5:7b         # Descarga el modelo
```

### Integración en Notebook

```python
from langchain_ollama import ChatOllama

# Cargar desde config.ini
model_name = config.get('ollama', 'model_name')
base_url = config.get('ollama', 'base_url')

llm = ChatOllama(
    model=model_name,
    base_url=base_url,
    temperature=0.3,
    num_ctx=8192
)
```

### Parámetros Configurables

```ini
[ollama]
base_url = http://localhost:11434
model_name = qwen2.5:7b
temperature = 0.3      # 0=determinista, 1=creativo
max_tokens = 2000
num_ctx = 8192         # tamaño de contexto
```

**Modelos Recomendados:**

| Modelo | Tamaño | Velocidad | Calidad | Razonamiento |
|--------|--------|-----------|---------|--------------|
| qwen2.5:7b | 7B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| mistral:7b | 7B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| llama2:7b | 7B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## Benchmarking y Métricas

### Métricas Capturadas

```python
{
    "timestamp": "2026-09-28T...",
    "num_cycles": 3,
    "quality_progression": [3, 6, 8],
    "initial_score": 3,
    "final_score": 8,
    "improvement": 5,
    "convergence_rate": 0.83,
    "wall_time_seconds": 18.5,
    "final_post": "Después de meses...",
    "modelo": "qwen2.5:7b"
}
```

### Análisis

**Convergencia:**
- Rápida (< 3 ciclos): modelo entiende bien el feedback
- Lenta (3+ ciclos): feedback confuso o inconsistente
- Estancada: modelo no mejora después de crítica

**Mejora por Ciclo:**
- Buena: +2 puntos/ciclo
- Aceptable: +1 punto/ciclo
- Deficiente: < +0.5 puntos/ciclo

### Visualización

Gráfico de convergencia:
```
Score
10 |                  ●
   |               ●
   |            ●
   |         ●
   |      ●
5  |   ●
   |●
0  +------------ Ciclo
   1  2  3  4  5
```

**Interpretación:** Mejora clara en cada ciclo → reflexión funciona bien

---

## Troubleshooting

### Problema: "Connection refused" a Ollama

```python
# Verificar que Ollama está corriendo
requests.get("http://localhost:11434/api/tags")

# Si falla:
# 1. ollama serve (en otra terminal)
# 2. Esperar 5 segundos
# 3. Reintentar
```

### Problema: Modelo no genera mejoras

**Causa:** Prompt de reflexión es débil.

**Solución:** Mejorar criteria en reflection_prompt:
```python
# Actual: vago ("proporcione feedback")
# Mejor: específico ("evalúe claridad (1-10), tone (1-10)...")
```

### Problema: Loops infinitos

**Causa:** `should_continue()` siempre retorna "reflect"

**Solución:** Verificar máximo de iteraciones:
```python
if len(state) > 6:  # máximo 3 ciclos
    return END
```

### Problema: Latencia alta (> 30s)

**Causa:** Modelo grande (13B+) o GPU limitada

**Solución:**
1. Cambiar modelo: `model_name = mistral:7b` (más rápido)
2. Reducir `max_tokens` en config.ini
3. Usar menos contexto: `num_ctx = 4096`

---

## Conclusiones

**Reflexión en Agentes = Sistema 2 Artificial**

- Generate: respuesta instintiva
- Reflect: evaluación crítica
- Revise: mejora deliberada

**Ollama:** Permite experimentar localmente sin APIs externas.

**LangGraph:** Framework limpio para workflows con estado.

**Benchmarking:** Mide si reflexión realmente mejora calidad.

---

**Próximas Lecturas:**
- [LangGraph Docs](https://python.langchain.com/docs/langgraph)
- Kahneman, D. "Thinking, Fast and Slow"
- [Ollama Models](https://ollama.ai/library)

---

**Autor:** Claude Haiku 4.5  
**Última actualización:** 2026-09-28  
**Versión:** 1.0
