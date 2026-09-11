# Implement Workflow Patterns with LangGraph — Ollama Local

**Estado:** ✅ Convertido y listo para usar  
**Versión:** 1.0.0  
**Basado en:** IBM Skills Network course (Kunal Makwana)  
**LLM Original:** OpenAI `gpt-4o-mini` → **Ollama Local** (100% offline)

---

## 📚 Descripción

Este notebook enseña los **3 patrones fundamentales de workflow agénticos** usando **LangGraph** y **Ollama** (LLM 100% local):

1. **Prompt Chaining** — Secuencia lineal: Job Description → Resume Summary → Cover Letter
2. **Routing** — Enrutamiento condicional: Clasificador decide → Summarizer o Translator
3. **Parallelization** — Ejecución simultánea: Traducción a 3 idiomas en paralelo → Agregador

**Todas las inferencias corren localmente.** Sin API calls cloud, sin data leaving your infrastructure.

---

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install langchain langchain-community langgraph langchain-ollama python-dotenv pydantic typing-extensions
```

### 2. Verificar Ollama

```bash
ollama list
```

Si necesitas un modelo:
```bash
ollama pull qwen2.5:7b
```

### 3. Ejecutar el Notebook

```bash
jupyter notebook implement_patterns_ollama.ipynb
```

---

## ⚙️ Configuración

Todos los parámetros están en **`config.ini`**:

```ini
[ollama]
base_url = http://localhost:11434
model_name = qwen2.5:7b          # Cambia aquí tu modelo
temperature = 0.7                # Control de creatividad
max_tokens = 2048

[logging]
level = INFO
log_file = logs/notebook_patterns.log
```

**Personalizar:**
- Cambiar modelo: edita `model_name` en `[ollama]`
- Cambiar temperatura: ajusta `temperature` (0.0-1.0)
- Cambiar verbosity: cambia `level` en `[logging]` (DEBUG, INFO, WARNING)

---

## 📊 Estructura del Notebook

| Sección | Descripción | Nodos |
|---------|-------------|-------|
| **Patrón 1: Prompt Chaining** | Job application assistant | `generate_resume_summary` → `generate_cover_letter` |
| **Patrón 2: Routing** | Task classifier (summarize/translate) | `router` → [`summarize` \| `translate`] |
| **Patrón 3: Parallelization** | Multilingual translator | [`translate_french`, `translate_spanish`, `translate_japanese`] → `aggregator` |

---

## 💻 Ejemplo de Uso

### Patrón 1: Prompt Chaining

```python
input_state = {
    "job_description": "We are looking for a data scientist...",
    "resume_summary": "",
    "cover_letter": ""
}

result = app_chain.invoke(input_state)
print(result['cover_letter'])
```

### Patrón 2: Routing

```python
input_text = {
    "user_input": "Can you translate this sentence: I love programming?",
    "task_type": "",
    "output": ""
}

result = app_routing.invoke(input_text)
print(result['task_type'])   # "translate"
print(result['output'])      # Traducción en francés
```

### Patrón 3: Parallelization

```python
input_text = {
    "text": "Good morning!",
    "french": "",
    "spanish": "",
    "japanese": "",
    "combined_output": ""
}

result = app_parallel.invoke(input_text)
print(result['combined_output'])  # Todas las traducciones
```

---

## 📁 Archivos Generados

```
05 Agentic AI Workflow Design Patterns/
├── config.ini                           # Configuración centralizada
├── implement_patterns_ollama.ipynb      # Este notebook
├── README_NOTEBOOK_OLLAMA.md            # Este archivo
├── logs/                                # Logs de ejecución (auto-creado)
└── datos/                               # Datos (auto-creado)
```

---

## 🔧 Diferencias vs. Notebook Original

| Aspecto | Original (OpenAI) | Ollama Local |
|---------|------------------|--------------|
| **LLM** | `ChatOpenAI` (`gpt-4o-mini`) | `OllamaLLM` (configurable) |
| **API Key** | Requerida (API OpenAI) | No requerida |
| **Configuración** | Hardcodeada | `config.ini` centralizado |
| **Costo** | $$ (API calls) | $0 (local) |
| **Privacidad** | Datos → OpenAI servers | 100% local, offline |
| **Latencia** | Network + inference | Solo local inference |

---

## 🎓 Aprendizaje

Cada patrón está **completamente comentado**:
- Qué hace cada nodo
- Por qué se estructura así
- Cuándo usarlo en producción
- Cómo modificarlo para tu caso de uso

Lee el notebook de arriba a abajo para entender la teoría, luego ejecuta cada celda.

---

## 🛠️ Troubleshooting

### Error: "Connection refused" a Ollama

**Solución:** Asegúrate que Ollama está corriendo:
```bash
ollama serve
```

### Error: "Model not found"

**Solución:** Descarga el modelo:
```bash
ollama pull qwen2.5:7b
```

Luego edita `config.ini` para cambiar el `model_name` si usas otro.

### Responses lentas

**Causa:** Modelo demasiado grande para tu hardware  
**Solución:** Usa un modelo más pequeño:
```bash
ollama pull phi:latest        # Muy rápido, menor calidad
ollama pull neural-chat:7b    # Balance speed/quality
ollama pull qwen2.5:7b        # Buena calidad (recomendado)
ollama pull mistral:7b        # Excelente para código/lógica
```

---

## 📚 Recursos

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Ollama:** https://ollama.ai/
- **Original Course:** IBM Skills Network (Kunal Makwana)

---

## 📝 Notas Finales

Este notebook es **material educativo**. Usa los patrones como base para:
- ✅ Prototipos rápidos con LLM
- ✅ Sistemas multi-agente complejos
- ✅ Pipelines de procesamiento de NLP
- ✅ Cualquier workflow que requiera coordinación de múltiples LLM calls

**100% local. 100% offline. 100% tuyo.** 🚀

---

**Última actualización:** 2026-09-10  
**Versión Ollama:** Compatible con Ollama 0.1+  
**Python:** 3.13+
