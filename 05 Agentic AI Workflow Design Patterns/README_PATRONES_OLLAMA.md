# 7 Patrones Agénticos — Ollama Local

**Estado:** ✅ Convertidos y listos para usar  
**Versión:** 1.0.0  
**Basado en:** Agentic-Design-Patterns-with-LangGraph (Mahendra Medapati)  
**LLM Original:** Google Gemini → **Ollama Local** (100% offline)

---

## 📚 Descripción

Implementación de **7 patrones agénticos fundamentales** usando **LangGraph** y **Ollama** (LLM 100% local). Cada patrón está en un script Python independiente, completamente parametrizable desde `config.ini`.

### Los 7 Patrones

| # | Patrón | Script | Descripción |
|---|--------|--------|-------------|
| 1 | **Prompt Chaining** | `pattern_1_prompt_chaining_ollama.py` | Secuencia lineal: output → input |
| 2 | **Routing** | `pattern_2_routing_ollama.py` | Clasificación + enrutamiento condicional |
| 3 | **Parallelization** | `pattern_3_parallelization_ollama.py` | Múltiples tareas simultáneas + agregador |
| 4 | **Reflection** | `pattern_4_reflection_ollama.py` | Bucle de refinamiento automático |
| 5 | **Tool Use** | `pattern_5_tool_use_ollama.py` | LLM decide cuándo usar herramientas |
| 6 | **Planning** | `pattern_6_planning_ollama.py` | Plan explícito → ejecución |
| 7 | **Multi-Agent** | `pattern_7_multi_agent_ollama.py` | Supervisor + especialistas |

**Todas las inferencias corren localmente.** Sin API calls cloud, sin data leaving your infrastructure.

---

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install -r requirements_patterns_ollama.txt
```

### 2. Verificar Ollama

```bash
ollama list
ollama pull qwen2.5:7b
```

### 3. Ejecutar un Patrón

```bash
python pattern_1_prompt_chaining_ollama.py
python pattern_2_routing_ollama.py
python pattern_3_parallelization_ollama.py
# ... etc
```

---

## ⚙️ Configuración

**Todos los parámetros están centralizados en `config.ini`:**

```ini
[ollama]
base_url = http://localhost:11434
model_name = qwen2.5:7b          # Cambia aquí tu modelo
temperature = 0.7                # Control de creatividad (0.0-1.0)
max_tokens = 2048

[logging]
level = INFO                      # DEBUG, INFO, WARNING, ERROR
log_file = logs/patterns.log

[proyecto]
nombre = 7 Patrones Agénticos (Ollama Local)
version = 1.0.0
```

### Personalizar Configuración

**Cambiar modelo:**
```ini
model_name = phi:latest        # Muy rápido, menor calidad
model_name = mistral:7b        # Excelente para lógica
model_name = neural-chat:7b    # Balance speed/quality
model_name = qwen2.5:7b        # Recomendado (defecto)
```

**Cambiar temperatura (creatividad):**
```ini
temperature = 0.3    # Determinístico, menos creativo
temperature = 0.7    # Balance (defecto)
temperature = 1.0    # Muy creativo, menos consistente
```

---

## 📖 Descripción de Patrones

### 1️⃣ Prompt Chaining — Secuencia Lineal

**Cuándo usarlo:** Pipelines con pasos dependientes y secuenciales.

**Estructura:**
```
Input → Node 1 → Node 2 → Node 3 → Output
```

**Ejemplo:** Extraer tópicos → Generar títulos de blog

---

### 2️⃣ Routing — Enrutamiento Condicional

**Cuándo usarlo:** Múltiples tipos de tarea con lógica especializada.

**Estructura:**
```
Input → Router (clasificador) → [Handler A | Handler B | Handler C]
```

**Ejemplo:** Analizar sentimiento → [Respuesta positiva | Respuesta negativa]

---

### 3️⃣ Parallelization — Ejecución Simultánea

**Cuándo usarlo:** Subtareas independientes sin dependencias.

**Estructura:**
```
Input → [Task 1 | Task 2 | Task 3] (en paralelo) → Aggregator → Output
```

**Ejemplo:** Traducción a 3 idiomas en paralelo → Combinar resultados

---

### 4️⃣ Reflection — Bucle de Refinamiento

**Cuándo usarlo:** Necesitas alta calidad con múltiples iteraciones.

**Estructura:**
```
Generate → Evaluate → [Refine | Finalize] → Output
```

**Ejemplo:** Borrador de párrafo → Crítica → Mejorar → Criterio de parada

**⚠️ Regla crítica:** Siempre establece `max_iterations` para evitar loops infinitos.

---

### 5️⃣ Tool Use — Integración de Herramientas

**Cuándo usarlo:** LLM necesita datos externos o ejecutar funciones.

**Estructura:**
```
Query → Decide Tool → [Tool 1 | Tool 2 | Tool 3] → Use Result → Response
```

**Ejemplo:** "¿Cuál es el clima?" → LLM decide → Llama weather_api → Responde

---

### 6️⃣ Planning — Plan Explícito + Ejecución

**Cuándo usarlo:** Problemas complejos que requieren análisis antes de actuar.

**Estructura:**
```
Goal → Create Plan → Execute Plan → Analyze Results
```

**Ejemplo:** "Cómo aprender IA" → Plan 5-pasos → Simular ejecución → Extraer lecciones

---

### 7️⃣ Multi-Agent — Supervisor + Especialistas

**Cuándo usarlo:** Diferentes tipos de expertos requieren perspectivas distintas.

**Estructura:**
```
Task → Supervisor (enruta) → [Tech Specialist | Business Specialist | Creative Specialist] → Synthesize
```

**Ejemplo:** "¿Cómo implementar IA?" → Supervisor asigna → Especialista responde → Síntesis final

---

## 💻 Ejemplos de Ejecución

### Ejecutar Patrón 1: Prompt Chaining

```bash
python pattern_1_prompt_chaining_ollama.py
```

**Output esperado:**
```
📝 Tópicos extraídos: LangGraph, AI Development, Multi-Agent Systems
🎯 Títulos generados!
📰 TÍTULOS GENERADOS:
- "LangGraph: Revolucionando el Desarrollo de IA..."
- "De Agentes Individuales a Sistemas Coordinados..."
```

### Ejecutar Patrón 4: Reflection

```bash
python pattern_4_reflection_ollama.py
```

**Output esperado:**
```
📝 Borrador 1 generado
🔍 Evaluación completada
📝 Borrador 2 generado
🔍 Evaluación completada
✓ Refinamiento completado (3 iteraciones)
```

---

## 📁 Estructura del Proyecto

```
05 Agentic AI Workflow Design Patterns/
├── config.ini                              # Configuración centralizada
├── requirements_patterns_ollama.txt        # Dependencias
├── README_PATRONES_OLLAMA.md              # Este archivo
│
├── pattern_1_prompt_chaining_ollama.py    # Patrón 1
├── pattern_2_routing_ollama.py            # Patrón 2
├── pattern_3_parallelization_ollama.py    # Patrón 3
├── pattern_4_reflection_ollama.py         # Patrón 4
├── pattern_5_tool_use_ollama.py           # Patrón 5
├── pattern_6_planning_ollama.py           # Patrón 6
├── pattern_7_multi_agent_ollama.py        # Patrón 7
│
├── logs/                                   # Logs de ejecución (auto-creado)
└── datos/                                  # Datos (auto-creado)
```

---

## 🔧 Troubleshooting

### Error: "Connection refused" a Ollama

```bash
ollama serve
```

### Error: "Model not found"

```bash
ollama pull qwen2.5:7b
```

Luego edita `config.ini` con el nombre del modelo.

### Responses lentas

Reduce el tamaño del modelo:
```bash
ollama pull phi:latest              # ~3.8 GB, muy rápido
ollama pull neural-chat:7b          # ~5 GB, balance
ollama pull qwen2.5:7b              # ~7 GB, recomendado
```

---

## 🎓 Aprendizaje

**Cada script está completamente comentado** con:
- Qué hace cada nodo
- Por qué se estructura así
- Cuándo usarlo en producción
- Cómo modificarlo

**Ruta de aprendizaje recomendada:**

1. **Comienza con Patrón 1** — Entiende TypedDict, nodos, edges
2. **Patrón 2** — Aprende conditional_edges y routing
3. **Patrón 3** — Domina parallelización con reducers
4. **Patrones 4-7** — Casos avanzados y combinaciones

---

## 📊 Comparación: Original vs. Ollama

| Aspecto | Original (Gemini) | Ollama Local |
|---------|------------------|--------------|
| **LLM** | `ChatGoogleGenerativeAI` | `OllamaLLM` |
| **API Key** | Requerida (Google) | No requerida |
| **Configuración** | Hardcodeada / .env | `config.ini` centralizado |
| **Costo** | $$ (API calls) | $0 (local) |
| **Privacidad** | Datos → Google servers | 100% local, offline |
| **Latencia** | Network + inference | Solo local inference |
| **Soberanía** | Dependencia cloud | Total control |

---

## 🚀 Próximos Pasos

1. **Experimenta con prompts** — Modifica las instrucciones en cada patrón
2. **Combina patrones** — Usa Routing + Chaining, o Reflection + Parallelization
3. **Integra con datos reales** — Conecta a bases de datos, APIs, documentos
4. **Optimiza para producción** — Agrega error handling, monitoring, perseverancia
5. **Escala horizontalmente** — Multi-GPU, distribución de carga

---

## 📚 Recursos

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Ollama:** https://ollama.ai/
- **Tutorial Completo:** `TUTORIAL_PATRONES_AGENTICOS.md` (en carpeta padre)

---

## 📝 Notas Finales

✅ **100% local.** Ninguna dependencia de APIs cloud.  
✅ **100% parametrizable.** Todo en `config.ini`.  
✅ **100% educativo.** Código comentado para aprender.  
✅ **100% tuyo.** Soberanía total de datos e IA.

---

**Última actualización:** 2026-09-10  
**Compatible con:** Ollama 0.1+, Python 3.13+  
**Basado en:** Agentic Design Patterns with LangGraph (Mahendra Medapati)

¡Listo para construir sistemas agénticos avanzados con Ollama! 🚀
