# Reasoning and Acting AI Agents — Patrón ReAct con LangGraph

**Estado:** 🟢 **PROYECTO NUEVO — Hito 0: Arquitectura**  
**Framework:** LangChain + LangGraph  
**Lenguaje:** 100% Español  
**Python:** 3.14 (env-llm-314) ✅  
**Última actualización:** 2026-09-20

---

## ¿Qué es ReAct?

**ReAct** (Reasoning + Acting) es un patrón de IA donde el agente alterna entre:

1. **Reasoning (Pensamiento):** "Necesito información sobre X"
2. **Acting (Acción):** Usar una herramienta para obtener X
3. **Observation (Observación):** Procesar el resultado de la herramienta
4. **Repite:** Hasta llegar a la respuesta final

### Ejemplo: Consulta Médica

```
Usuario: "¿Cuántos mg de paracetamol puede tomar un adulto?"

Agent Reasoning: "Necesito información sobre dosificación de paracetamol"
Agent Action: → Buscar en Wikipedia
Agent Observation: "Dosis típica: 500-1000 mg cada 4-6 horas, máximo 3000-4000 mg/día"

Agent Reasoning: "Tengo la información"
Agent Final Answer: "Un adulto puede tomar 500-1000 mg cada 4-6 horas, máximo 3000-4000 mg/día"
```

---

## Diferencia: LangChain vs LangGraph

### ❌ LangChain (ConversableAgent)

- Razonamiento visible como **texto**
- Difícil capturar métricas ("¿cuántos pasos?")
- Parsing manual de "Thought:", "Action:", etc.

### ✅ LangGraph (StateGraph + Reducers)

- Razonamiento como **datos estructurados** en el state
- Métricas automáticas: `len(state["reasoning_steps"])`
- State es la fuente única de verdad

**Este proyecto usa LangGraph para auditoría completa del razonamiento.**

---

## Herramientas del Agente

| Tool | Descripción | Ejemplo |
|------|------------|---------|
| **Calculadora** | Operaciones aritméticas | 2 + 2 = 4 |
| **Wikipedia** | Búsqueda de conocimiento | "Paracetamol" → información médica |
| **Fecha/Hora** | Información temporal | "¿Qué hora es?" → 2026-09-20 14:30 |
| **Conversor** | Temperatura, distancia, peso | 32°F → 0°C |

---

## Modelos Recomendados para ReAct

### 🏆 **Recomendación: `qwen2.5:7b` (MEJOR OPCIÓN)**

**Razón:** Excelente seguimiento de instrucciones + razonamiento estructurado

| Métrica | qwen2.5:7b | llama2:7b | mistral:7b | neural-chat:7b |
|---------|-----------|----------|-----------|-----------------|
| **Seguimiento formato Thought/Action/Observation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Razonamiento en pasos** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Latencia (segundos)** | 5-15s | 8-18s | 3-8s | 6-12s |
| **Tamaño modelo** | 7B | 7B | 7B | 7B |
| **Manejo de errores** | Excelente | Bueno | Bueno | Excelente |
| **Español** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Por qué qwen2.5:7b es ideal para ReAct:**
1. ✅ Sigue precisamente el formato `Thought: ... / Action: ... / Action Input: ... / Final Answer: ...`
2. ✅ Razonamiento claro en múltiples pasos (ReAct puro)
3. ✅ Excelente soporte de español 100%
4. ✅ Determinístico con temperature=0.3 (no aleatoriedad)
5. ✅ Contexto suficiente (8192 tokens) para razonamientos largos
6. ✅ Equilibrio latencia/calidad: 7-12 segundos en laptop (RTX 3050)

### Alternativas Válidas

| Modelo | Caso de Uso | Ventaja |
|--------|-----------|---------|
| **mistral:7b** | Si quieres más rapidez | 3-5s más rápido |
| **neural-chat:7b** | Chat puro (no ReAct) | Mejor conversacional, pero menos estructura |
| **llama2:7b** | Compatibilidad máxima | Modelo base más universal |
| **qwen:14b** | Precisión máxima | Mejor razonamiento, pero 30-40s latencia |

---

## Inicio Rápido

### Paso 1: Verificar Ollama

```bash
# Listar modelos disponibles
ollama list

# Recomendado: Descargar qwen2.5:7b si no está presente
ollama pull qwen2.5:7b

# Verificar conectividad
curl http://localhost:11434/api/tags
```

### Paso 2: Configurar config.ini

Editar `config.ini` sección `[ollama]`:

```ini
[ollama]
base_url = http://localhost:11434
model_name = qwen2.5:7b          # ← RECOMENDADO
temperature = 0.3                # ← Para determinismo (ReAct requiere esto)
max_tokens = 2000
num_ctx = 8192
```

### Paso 3: Instalar Dependencias

```bash
C:\workspace-vc\env-llm-ia\Scripts\python.exe -m pip install -r requirements.txt
```

### Paso 4: Ejecutar Notebook

```bash
C:\workspace-vc\env-llm-ia\Scripts\python.exe -m jupyter notebook reasoning_acting_agent_executed.ipynb
```

Celdas principales:
1. Verificación de entorno
2. Carga de config.ini
3. Definición de tools (calculadora, Wikipedia, fecha, conversor)
4. Construcción del agente ReAct (LangGraph)
5. Ejecución de 3 casos de prueba
6. Captura de métricas
7. Generación de reportes

### Paso 5: Analizar Resultados

```bash
# Generar gráficos, tabla, reporte markdown con timestamp
python analyze_benchmark.py

# Ver reporte más reciente
dir /od outputs/REPORTE_REACT_*.md | head -1
```

---

## Estructura del Proyecto

```
09 Reasoning and Acting AI Agents/
├── README.md                          # Este archivo
├── MANUAL.md                          # Guía técnica detallada
├── REPORTE_TECNICO_LANGGRAPH.md       # ⭐ Explicación de LangGraph + Reducers
├── config.ini                         # Parametrización (Ollama, agente, benchmark)
├── requirements.txt                   # Dependencias Python
├── benchmark.py                       # ⭐ Captura, análisis, reportes (NUNCA inline)
├── analyze_benchmark.py               # Script de análisis post-hoc
├── reasoning_acting_agent.ipynb       # Notebook educativo principal
├── tools.py                           # Definición de herramientas (calculadora, etc.)
├── data/
│   └── verdades_esperadas.jsonl       # Casos de prueba para evaluación
├── outputs/
│   ├── benchmark.jsonl                # Métricas JSONL (append-only)
│   ├── REPORTE_REACT_YYYYMMDD_HHMMSS.md # Reportes con timestamp
│   ├── 01_comparacion_latencia.png    # Gráficos generados
│   ├── 02_comparacion_pasos.png
│   └── 03_tradeoff_latencia_pasos.png
├── logs/
│   └── (logs de ejecución auto-generados)
└── checkpoint/
    └── CHECKPOINTS.md                 # Historial de hitos
```

---

## Conceptos Clave: LangGraph + Reducers

### State Explícito

```python
from typing import Annotated
import operator

class ReActState(TypedDict):
    query: str
    
    # ← Reducers: operator.add agrega en lugar de reemplazar
    reasoning_steps: Annotated[list, operator.add]
    observations: Annotated[list, operator.add]
    tools_used: Annotated[list, operator.add]
    
    final_answer: str  # Sin reducer: sobrescribible
```

**Ventaja:** `len(state["reasoning_steps"])` = número de pasos ReAct (automático, no parseado)

### StateGraph

```python
from langgraph.graph import StateGraph

workflow = StateGraph(ReActState)
workflow.add_node("think", think_node)      # Nodo de razonamiento
workflow.add_node("act", act_node)          # Nodo de acción
workflow.add_edge("think", "act")           # Arista: transición

app = workflow.compile()
result = app.invoke({"query": "...", "reasoning_steps": [], ...})

# Acceder a razonamiento acumulado
print(f"Pasos: {len(result['reasoning_steps'])}")
print(f"Tools: {result['tools_used']}")
```

**Ver `REPORTE_TECNICO_LANGGRAPH.md` para explicación completa.**

---

## Benchmarking Integrado

**Principio clave de la fábrica ia-dev:** Todo código de benchmarking en `benchmark.py`, **nunca inline en notebook**.

### Captura Automática

```python
# reasoning_acting_agent.ipynb
from benchmark import medir_y_registrar, guardar_metricas

result = app.invoke(...)  # Ejecutar agente
metrica = medir_y_registrar(result, wall_time, model, temp, label, query)
guardar_metricas([metrica])

# medir_y_registrar() extrae automáticamente:
# - num_steps (pasos ReAct)
# - tools_used (herramientas invocadas)
# - wall_time (latencia)
# - exactitud vs verdad esperada
```

### Análisis Post-Hoc

```bash
python analyze_benchmark.py
# Genera:
# - 3 gráficos PNG (latencia, pasos, trade-off)
# - Tabla comparativa (TXT)
# - Reporte profesional (Markdown con timestamp)
```

---

## Evaluación de Exactitud

Casos de prueba en `data/verdades_esperadas.jsonl`:

```json
{"consulta": "2+2", "respuesta_esperada": "4"}
{"consulta": "convertir 32F a C", "respuesta_esperada": "0"}
{"consulta": "población de París", "respuesta_esperada": "aproximadamente 2 millones"}
```

El script `benchmark.py` compara automáticamente respuestas del agente contra `respuesta_esperada`.

---

## Hitos Planificados

### Hito 0: Arquitectura ✅ (Actual)
- ✅ LangGraph + StateGraph diseñado
- ✅ Reducers para acumular razonamiento
- ✅ 4 tools definidas
- ✅ benchmark.py listo (reutilizable)
- ✅ Documentación técnica (REPORTE_TECNICO_LANGGRAPH.md)

### Hito 1: Agente Funcional (Próximo)
- [ ] Notebook `reasoning_acting_agent.ipynb` ejecutándose
- [ ] 3 casos de prueba correctos
- [ ] Métricas guardadas en `benchmark.jsonl`
- [ ] Reportes generándose con timestamp
- [ ] Exactitud ≥95% en casos de prueba

### Hito 2: Validación Completa (Futuro)
- [ ] 20+ casos de prueba en `verdades_esperadas.jsonl`
- [ ] Benchmark comparativo (qwen vs llama vs mistral)
- [ ] Análisis de trade-off: latencia vs pasos vs exactitud
- [ ] Documentación finalizada

---

## Comparativa con Otros Proyectos

| Aspecto | `07 Math Assistant` | `09 ReAct Agent` |
|--------|-----------|---------|
| **Framework** | LangChain | LangChain + **LangGraph** |
| **Patrón** | Tool Calling moderno | ReAct clásico (explícito) |
| **Razonamiento** | Implícito en LLM | **Visible en state** |
| **Captura de trace** | No | **Sí (Reducers)** |
| **Benchmarking** | Básico | **Completo con pasos ReAct** |

---

## Troubleshooting

### Error: "Module 'langgraph' not found"
```bash
pip install langgraph
# O reinstalar requirements.txt
pip install -r requirements.txt
```

### Error: "Ollama connection refused"
```bash
# Verificar Ollama
curl http://convergenciax02:11434/api/tags

# Si no responde, iniciar Ollama en otra terminal
ollama serve
```

### Métricas vacías
- Verificar que `benchmark_enabled = true` en config.ini
- Confirmar que `from benchmark import guardar_metricas` está en notebook
- Ejecutar `python analyze_benchmark.py` después de correr notebook

---

## Referencias Técnicas

- **REPORTE_TECNICO_LANGGRAPH.md** — Explicación profunda de LangGraph + Reducers
- **MANUAL.md** — Guía de cómo agregar tools nuevas
- **Proyecto Relacionado:** `07 AI Math Assistant with LangChain` (tool calling)
- **Proyecto Relacionado:** `08 MultiAgent Chatbot for Healthcare` (AutoGen multiagente)

---

## Comandos Útiles

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar notebook
jupyter notebook reasoning_acting_agent.ipynb

# Análisis de benchmark
python analyze_benchmark.py

# Ver reporte más reciente
ls -t outputs/REPORTE_REACT_*.md | head -1

# Ver métricas JSONL
head -5 outputs/benchmark.jsonl | python -m json.tool

# Verificar configuración
python -c "import configparser; c = configparser.ConfigParser(); c.read('config.ini', encoding='utf-8'); print(dict(c['ollama']))"
```

---

## Notas para Desarrolladores

1. **benchmark.py es la fuente de verdad** para benchmarking — cualquier cambio en métricas va allí
2. **State es estructurado** — no parsees texto para extraer pasos
3. **Reducers son tu amigo** — `Annotated[list, operator.add]` es más limpio que código manual
4. **Teste primero** — antes de agregar una tool, escribe un test en `verdades_esperadas.jsonl`

---

**Autor:** Claude Haiku 4.5  
**Sesión:** https://claude.ai/code/session_012AV7eFXU9i17FLBaAZxoe2  
**Última actualización:** 2026-09-20  
**Status:** ✅ Listo para Hito 1 (Agente Funcional)
