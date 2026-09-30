# MANUAL: Agentes con Reflexión en LangGraph

**Cómo extender, personalizar y escalar el agente de reflexión.**

---

## Parte 1: Entender el Flujo Base

### El Ciclo de Reflexión (3 pasos)

```
1. GENERATE: Crea contenido inicial
   Input: "Escribe un LinkedIn post sobre IA"
   Output: "Estoy aprendiendo IA. Es increíble."

2. REFLECT: Evalúa la calidad
   Input: Post anterior + criterios
   Output: "Score: 3/10. Muy genérico, sin valor específico."

3. REVISE: Mejora basándose en evaluación
   Input: Post anterior + feedback
   Output: "Acabo de entrenar un agente que se mejora a sí mismo..."
```

### State Structure (LangGraph)

```python
from typing import Annotated, TypedDict
import operator

class ReflectionState(TypedDict):
    # Entrada
    query: str
    
    # Acumuladores (Reducers: operator.add suma listas)
    drafts: Annotated[list, operator.add]           # Todos los borradores
    reflections: Annotated[list, operator.add]      # Todas las evaluaciones
    revisions: Annotated[list, operator.add]        # Cambios aplicados
    quality_scores: Annotated[list, operator.add]   # Score de cada ciclo
    
    # Salida (sin Reducer: se reemplaza)
    final_response: str
    
    # Control
    cycle_count: int
```

**Ventaja de Reducers:**
```python
# Ciclo 1
state = {"quality_scores": [3]}

# Ciclo 2 (Reducer suma, no reemplaza)
return {"quality_scores": [6]}
# Result: state["quality_scores"] = [3, 6]

# Ciclo 3
return {"quality_scores": [8]}
# Result: state["quality_scores"] = [3, 6, 8]  ← Auditoría completa
```

---

## Parte 2: Implementar Nodos Personalizados

### Nodo 1: GENERATE (Personalizar Prompt)

**Archivo: `tools/generation_tools.py`**

```python
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

def get_generation_prompt(topic: str, style: str = "professional") -> str:
    """Crea prompt para generar contenido."""
    
    prompts = {
        "professional": f"""Escribe un LinkedIn post profesional sobre: {topic}
        
Requisitos:
- Máximo 280 caracteres (LinkedIn limit)
- Tono profesional pero personal
- Invita a discusión
- Específico, no genérico""",
        
        "casual": f"""Escribe un tweet casual sobre: {topic}
        
Requisitos:
- Máximo 280 caracteres
- Tono divertido e informal
- Emoji opcional
- Viralizable""",
        
        "academic": f"""Escribe un post académico sobre: {topic}
        
Requisitos:
- Máximo 500 caracteres
- Tono riguroso
- Citar fuentes si aplica
- Educar a la audiencia"""
    }
    
    return prompts.get(style, prompts["professional"])

# Usar en nodo
def generate_node(state: ReflectionState) -> ReflectionState:
    llm = ChatOllama(model="qwen2.5:7b", temperature=0.7)
    
    prompt = get_generation_prompt(
        topic=state["query"],
        style="professional"  # ← PERSONALIZABLE
    )
    
    draft = llm.invoke([HumanMessage(content=prompt)]).content
    
    return {
        "drafts": [draft],
        "cycle_count": state["cycle_count"]
    }
```

### Nodo 2: REFLECT (Personalizar Criterios)

**Archivo: `tools/evaluation_tools.py`**

```python
def get_reflection_criteria(domain: str = "linkedin") -> str:
    """Define criterios de evaluación por dominio."""
    
    criteria = {
        "linkedin": """Evalúa este LinkedIn post (escala 1-10):

CRITERIOS:
1. Claridad (1-10): ¿Se entiende el mensaje principal?
2. Profesionalismo (1-10): ¿Tono y lenguaje apropiados?
3. Engagement (1-10): ¿Invita a comentarios/likes?
4. Especificidad (1-10): ¿Aporta algo concreto?
5. Estructura (1-10): ¿Fácil de leer?

SCORE FINAL = promedio(todos los criterios)
FEEDBACK = "¿Qué falta? ¿Qué mejorar?"

Post a evaluar: "{post}"\"""",
        
        "email": """Evalúa este email (escala 1-10):

CRITERIOS:
1. Claridad (1-10): ¿Es claro el propósito?
2. Profesionalismo (1-10): ¿Tono corporativo?
3. Brevedad (1-10): ¿Respeta el tiempo del lector?
4. Call-to-action (1-10): ¿Hay próximos pasos claros?
5. Personalización (1-10): ¿Siente personal, no templated?

SCORE FINAL = promedio(todos los criterios)
FEEDBACK = "¿Qué mejoras sugiere?"

Email a evaluar: "{email}\"""",
    }
    
    return criteria.get(domain, criteria["linkedin"])

def reflect_node(state: ReflectionState) -> ReflectionState:
    llm = ChatOllama(model="qwen2.5:7b", temperature=0.3)
    
    draft = state["drafts"][-1]
    criteria = get_reflection_criteria(domain="linkedin")  # ← PERSONALIZABLE
    
    prompt = criteria.format(post=draft)
    evaluation = llm.invoke([HumanMessage(content=prompt)]).content
    
    # Extraer score
    score = extract_score_from_evaluation(evaluation)
    
    return {
        "reflections": [evaluation],
        "quality_scores": [score]
    }

def extract_score_from_evaluation(text: str) -> float:
    """Extrae 'SCORE FINAL: 7/10' → 7.0"""
    import re
    match = re.search(r"SCORE FINAL.*?(\d+)/10", text)
    return float(match.group(1)) if match else 0.0
```

### Nodo 3: REVISE (Personalizar Mejoras)

```python
def revise_node(state: ReflectionState) -> ReflectionState:
    llm = ChatOllama(model="qwen2.5:7b", temperature=0.7)
    
    draft = state["drafts"][-1]
    evaluation = state["reflections"][-1]
    
    prompt = f"""Mejora este post basándote en la evaluación:

EVALUACIÓN ANTERIOR:
{evaluation}

POST ORIGINAL:
{draft}

TAREA: Reescribe el post incorporando las sugerencias de la evaluación.
RESTRICCIÓN: Máximo 280 caracteres (LinkedIn limit).
OUTPUT: Solo el nuevo post mejorado, sin explicación."""
    
    revised_draft = llm.invoke([HumanMessage(content=prompt)]).content
    
    return {
        "drafts": [revised_draft],
        "revisions": [f"Mejorado basado en: {evaluation[:100]}..."],
        "cycle_count": state["cycle_count"] + 1
    }
```

---

## Parte 3: Personalizar Criterios de Parada

### Opción A: Score-based (Recomendado)

```python
def should_continue(state: ReflectionState) -> str:
    """Parar cuando score ≥ threshold"""
    
    last_score = state["quality_scores"][-1]
    threshold = 7.0  # ← PERSONALIZABLE
    
    if last_score >= threshold:
        return "final"
    
    if state["cycle_count"] >= 3:  # Max 3 ciclos
        return "final"
    
    return "revise"
```

### Opción B: Convergencia-based

```python
def should_continue(state: ReflectionState) -> str:
    """Parar cuando convergencia es lenta"""
    
    scores = state["quality_scores"]
    
    if len(scores) < 2:
        return "revise"
    
    # Si últimos 2 scores tienen mejora < 1 punto
    improvement = scores[-1] - scores[-2]
    if improvement < 1.0 and len(scores) > 2:
        return "final"  # Ya no mejora significativamente
    
    if state["cycle_count"] >= 5:
        return "final"
    
    return "revise"
```

---

## Parte 4: Agregar Nuevos Dominios

### Ejemplo: Generador de Emails

```python
# 1. Agregar en config.ini
[reflection_criteria]
domains = linkedin, email, report, tweet

# 2. Crear prompts específicos
def get_generation_prompt(topic: str, domain: str) -> str:
    prompts = {
        "linkedin": "...",
        "email": f"Escribe un email profesional sobre {topic}...",
        "report": f"Escribe un reporte ejecutivo sobre {topic}...",
        "tweet": f"Escribe un tweet sobre {topic}...",
    }
    return prompts.get(domain)

# 3. Pasar domain al estado
state = {
    "query": "Agentes con reflexión",
    "domain": "email",  # ← NUEVO CAMPO
    ...
}

# 4. Usar en nodos
prompt = get_generation_prompt(state["query"], state["domain"])
```

---

## Parte 5: Benchmarking de Reflexión

**En `benchmark.py`:**

```python
def medir_reflexion(state: ReflectionState) -> dict:
    """Captura métricas específicas de reflexión."""
    
    return {
        "timestamp": datetime.now().isoformat(),
        
        # Cadena de mejora
        "quality_progression": state["quality_scores"],  # [3, 6, 8]
        "num_cycles": state["cycle_count"],
        
        # Convergencia
        "convergence_rate": calculate_convergence(state["quality_scores"]),
        
        # Contenido final
        "final_post": state["final_response"],
        "final_score": state["quality_scores"][-1],
        
        # Auditoría
        "all_drafts": state["drafts"],
        "all_reflections": state["reflections"],
    }

def calculate_convergence(scores: list) -> float:
    """Qué tan rápido converge (0.0-1.0)"""
    if len(scores) < 2:
        return 0.0
    
    improvements = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
    avg_improvement = sum(improvements) / len(improvements)
    
    return min(avg_improvement / 5.0, 1.0)  # Normalizar a 0-1
```

---

## Parte 6: Extensión Avanzada - Multi-Language

```python
# Agregar soporte para otros idiomas

def get_generation_prompt_multilang(topic: str, language: str) -> str:
    """Genera prompts en múltiples idiomas."""
    
    prompts = {
        "es": f"Escribe un LinkedIn post profesional sobre: {topic}",
        "en": f"Write a professional LinkedIn post about: {topic}",
        "fr": f"Écrivez un post LinkedIn professionnel sur: {topic}",
        "pt": f"Escreva um post profissional do LinkedIn sobre: {topic}",
    }
    
    return prompts.get(language, prompts["es"])
```

---

## Checklist: Cómo Extender

- [ ] Decide: ¿Nuevo dominio (email, reporte, tweet) o mismo dominio?
- [ ] Crea prompts específicos (generate, reflect, revise)
- [ ] Define criterios de evaluación (¿qué hace una respuesta "buena"?)
- [ ] Personaliza threshold de calidad (7/10 por defecto)
- [ ] Agrega casos de prueba en `data/verdades_esperadas.jsonl`
- [ ] Ejecuta `jupyter notebook reflection_agent.ipynb`
- [ ] Revisa `outputs/REPORTE_REFLEXION_*.md`
- [ ] Itera si es necesario

---

**Preguntas comunes:**

**P: ¿Qué pasa si max_cycles y score threshold nunca se alcanzan?**  
R: El máximo de ciclos (3) es la red de seguridad. Siempre terminará.

**P: ¿Cómo cambio el modelo LLM?**  
R: En `config.ini`: `model_name = mistral:7b` (o el que quieras)

**P: ¿Puedo usar diferentes modelos para generate vs reflect?**  
R: Sí, crea dos instancias de `ChatOllama`:
```python
llm_generate = ChatOllama(model="qwen2.5:7b")
llm_reflect = ChatOllama(model="mistral:7b")  # Más rápido para evaluación
```

---

**Autor:** Claude Haiku 4.5  
**Última actualización:** 2026-09-28
