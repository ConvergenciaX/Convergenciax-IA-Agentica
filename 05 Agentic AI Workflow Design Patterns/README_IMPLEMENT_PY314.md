# Implement Workflow Patterns with LangGraph (Ollama Local) — Python 3.14

**Estado:** ✅ Ejecutable, testeable, optimizado para Python 3.14  
**Versión:** 1.0.0  
**Basado en:** IBM Skills Network (Kunal Makwana)  
**LLM Original:** OpenAI `gpt-4o-mini` → **Ollama Local** (100% offline)  
**Python:** 3.14.x (testeado en 3.14.2)

---

## 📖 Descripción

Script ejecutable que implementa los **3 patrones fundamentales** del notebook original IBM Skills Network, convertido a Ollama local con infraestructura declarada:

1. **Prompt Chaining** — Job application assistant (job description → resume → cover letter)
2. **Routing** — Task classifier (summarize vs translate)
3. **Parallelization** — Multilingual translator (French, Spanish, Japanese simultáneamente)

**Todo parametrizable desde `config.ini`. Sin APIs cloud, 100% offline.**

---

## 🚀 Inicio Rápido (3 Pasos)

### 1. Instalar Dependencias

```bash
pip install -r requirements_notebook_py314.txt
```

**Verificar que pip resuelve a Python 3.14:**
```bash
python --version  # Debe mostrar 3.14.x
pip --version     # Debe mostrar python 3.14
```

Si no, especifica explícitamente:
```bash
C:\workspace-vc\env-llm-314\Scripts\pip install -r requirements_notebook_py314.txt
```

### 2. Verificar Ollama

```bash
ollama list
ollama pull qwen2.5:7b  # Si no lo tienes
```

### 3. Ejecutar el Script

```bash
# Todos los patrones
python implement_patterns_py314.py

# Patrón específico
python implement_patterns_py314.py --pattern 1
python implement_patterns_py314.py --pattern 2
python implement_patterns_py314.py --pattern 3
```

---

## ⚙️ Infraestructura Declarada

**Todo configurado en `config.ini`:**

```ini
[ollama]
base_url = http://localhost:11434
model_name = qwen2.5:7b          # ← Cambia aquí el modelo
temperature = 0.7                # ← Ajusta creatividad

[logging]
level = INFO                      # ← DEBUG, INFO, WARNING, ERROR
log_file = logs/patterns.log      # ← Dónde se guardan los logs
log_dir = logs

[proyecto]
nombre = Implement Workflow Patterns with LangGraph (Ollama Local)
version = 1.0.0
```

**No hardcodeado. Todo externalizado.**

---

## 📊 Los 3 Patrones

### Patrón 1: Prompt Chaining ⛓️

**Qué es:** Una tarea compleja se descompone en pasos secuenciales, donde cada paso depende del anterior.

**Estructura:**
```
Job Description
    ↓
[Nodo 1: Generar Resume Summary]
    ↓
Resume Summary (output del paso 1 → input del paso 2)
    ↓
[Nodo 2: Generar Cover Letter]
    ↓
Cover Letter (output final)
```

**Caso de uso:** Asistente de solicitud laboral

**Cuándo usarlo:**
- Pipelines con pasos claramente secuenciales y dependientes
- Output de un paso alimenta el siguiente
- Cada paso es relativamente independiente en lógica

---

### Patrón 2: Routing 🚦

**Qué es:** Un clasificador analiza la entrada y la enruta a uno de varios handlers especializados basado en la clasificación.

**Estructura:**
```
User Input
    ↓
[Nodo Router: Clasificar tarea]
    ↓
    Condición: task_type == "summarize" → [Summarize Handler]
               task_type == "translate"  → [Translate Handler]
    ↓
Output especializado
```

**Caso de uso:** Task classifier (resumir vs traducir)

**Cuándo usarlo:**
- Sistema maneja múltiples tipos de tarea completamente diferentes
- Cada tipo requiere lógica/prompts especializados
- Decisiones rápidas basadas en clasificación

---

### Patrón 3: Parallelization ⚡

**Qué es:** Múltiples nodos independientes se ejecutan simultáneamente sobre la misma entrada, luego un agregador combina resultados.

**Estructura:**
```
Input (texto a traducir)
    ↓
    ┌─────────────────────┐
    ↓         ↓         ↓
[FR Translator] [ES Translator] [JP Translator]  ← Paralelo
    ↓         ↓         ↓
    └─────────────────────┘
            ↓
    [Aggregator: Combina]
            ↓
    Output (3 traducciones)
```

**Caso de uso:** Traductor multilingüe

**Cuándo usarlo:**
- 2+ subtareas independientes sin dependencias entre sí
- Reducir latencia total (ejecutar en paralelo reduce wall-clock time)
- Los resultados deben combinarse en un resultado final

---

## 💻 Ejemplo de Ejecución

### Ejecutar todos los patrones:

```bash
python implement_patterns_py314.py
```

**Output esperado:**

```
======================================================================
INFRAESTRUCTURA INICIALIZADA
======================================================================
Python: 3.14.2 (main, ...)
Config: config.ini
Logging: logs/patterns.log (level=INFO)
Ollama LLM: qwen2.5:7b
Ollama URL: http://localhost:11434
======================================================================

======================================================================
PATRÓN 1: PROMPT CHAINING (Job Application Assistant)
======================================================================

📝 Ejecutando: generate_resume_summary
✓ Resume generado (245 caracteres)
📝 Ejecutando: generate_cover_letter
✓ Cover letter generado (567 caracteres)

======================================================================
RESULTADOS - PATRÓN 1: PROMPT CHAINING
======================================================================

📋 RESUME SUMMARY:
Dynamic data scientist with extensive experience in machine learning...

💌 COVER LETTER:
Dear Hiring Manager,

I am writing to express my strong interest in the Data Scientist position...

======================================================================
PATRÓN 2: ROUTING (Task Classifier)
======================================================================
...

======================================================================
PATRÓN 3: PARALLELIZATION (Multilingual Translator)
======================================================================
...

✓ TODOS LOS PATRONES COMPLETADOS EXITOSAMENTE
```

---

## 📁 Archivos Generados

```
implement_patterns_py314.py              # Script ejecutable principal
requirements_notebook_py314.txt          # Dependencias para Python 3.14
README_IMPLEMENT_PY314.md               # Este archivo
config.ini                              # Configuración centralizada
logs/                                   # Logs generados (auto-creado)
```

---

## 🔧 Especificidades de Python 3.14

### Compatibilidad Verificada

✅ **typing-extensions 4.8.0+** → `TypedDict` y `Annotated` funcionan perfectamente  
✅ **langchain 0.3.0+** → Soporte completo para Python 3.14  
✅ **langgraph 0.2.0+** → Sin dependencias de compilación (Rust/C)  
✅ **pydantic 2.0.0+** → Compatible con 3.14  

### No Hay Problemas de Compilación

Todos los paquetes tienen wheels precompilados para Python 3.14. **No requiere compilador de Rust/C.**

```bash
# Instalación rápida (sin compilación)
pip install -r requirements_notebook_py314.txt
```

---

## 🧪 Testing

### Test 1: Verificar instalación

```bash
python -c "import langchain; import langgraph; from langchain_ollama import OllamaLLM; print('✓ Imports OK')"
```

### Test 2: Verificar conexión Ollama

```bash
python -c "from langchain_ollama import OllamaLLM; llm = OllamaLLM(model='qwen2.5:7b'); print(llm.invoke('Hola'))"
```

### Test 3: Ejecutar un solo patrón

```bash
python implement_patterns_py314.py --pattern 1
```

---

## 🛠️ Troubleshooting

### Error: "Connection refused" a Ollama

```bash
ollama serve
```

Ejecuta esto en otra terminal antes de correr el script.

### Error: "ModuleNotFoundError: No module named 'langchain_ollama'"

```bash
pip install langchain-ollama
```

Asegúrate que pip está resolviendo a Python 3.14:
```bash
pip --version
```

### Error: "Model not found"

```bash
ollama pull qwen2.5:7b
```

### Responses lentas

Reduce el tamaño del modelo en `config.ini`:

```ini
model_name = phi:latest        # Muy rápido (~3.8 GB)
model_name = neural-chat:7b    # Balance speed/quality (~5 GB)
model_name = mistral:7b        # Lógica excelente (~7 GB)
model_name = qwen2.5:7b        # Recomendado (~7 GB)
```

---

## 📖 Estructura del Script

```python
# Infraestructura declarada
setup_infrastructure()     # config.ini → logging, LLM
    ↓
# Los 3 patrones
pattern_1_prompt_chaining()   # ⛓️  Chainining
pattern_2_routing()           # 🚦 Routing
pattern_3_parallelization()   # ⚡ Parallelization
    ↓
# Integración
main()                        # Orquesta todo, parse argumentos
```

**Cada patrón es independent** — puedes extraerlo y usarlo en tu código sin cambios.

---

## 🎓 Aprendizaje

1. **Lee el código** — Está completamente comentado
2. **Lee los logs** — Verás exactamente qué nodo se ejecuta cuándo
3. **Modifica los prompts** — Cambia las instrucciones LLM y experimenta
4. **Combina patrones** — Usa Routing + Chaining, o Reflection + Parallelization

---

## ✨ Características Clave

✅ **Ejecutable, no solo notebook** — Fácil de testear y debuggear  
✅ **Infraestructura declarada** — config.ini, logging estructurado  
✅ **Python 3.14 optimizado** — Sin problemas de compilación  
✅ **100% Ollama local** — Sin OpenAI, Google, o APIs cloud  
✅ **Producción-ready** — Logging, error handling, estructura profesional  
✅ **Didáctico** — Código comentado, información de debug

---

## 📊 Comparación: Notebook vs. Script Ejecutable

| Aspecto | Notebook Original | Script Ejecutable (Nuevo) |
|---------|------------------|-------------------------|
| Formato | `.ipynb` (Jupyter) | `.py` (Python puro) |
| Ejecución | Celda por celda | Script completo |
| Debugging | Interactivo | Logs estructurados |
| CI/CD | Difícil de automatizar | Fácil, simple `python` |
| Infraestructura | Hardcodeada | config.ini + logging |
| Python 3.14 | ⚠️ Depende de Jupyter | ✅ Totalmente compatible |

---

## 🚀 Próximos Pasos

1. **Ejecuta el script** — Verifica que funciona
2. **Inspecciona los logs** — Entiende el flujo
3. **Modifica config.ini** — Experimenta con parámetros
4. **Adapta los prompts** — Hazlo tuyo
5. **Integra en tu sistema** — Usa como base para producción

---

## 📚 Recursos

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Ollama:** https://ollama.ai/
- **Python 3.14 Release:** https://docs.python.org/3.14/

---

## 📝 Notas Finales

✅ **Python 3.14 compatible** — Testeado en 3.14.2  
✅ **Ollama local** — 100% offline, sin cloud  
✅ **Infraestructura profesional** — config.ini, logging, error handling  
✅ **Listo para producción** — Scalable, maintainable, testeable

---

**Última actualización:** 2026-09-10  
**Python:** 3.14.2  
**Status:** ✅ Production-ready

¡Listo para ejecutar! 🚀
