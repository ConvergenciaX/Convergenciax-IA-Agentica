# CHECKPOINTS — Agente IA - CrewIA Multiagente (NourishBot local)

## 2026-08-31 — Build inicial: NourishBot 100% local con Ollama (CrewAI multiagente)

- Base: lab `NourishBot` (IBM SkillsNetwork, CrewAI) en esta misma carpeta —
  `app.py`, `src/crew.py`, `src/models.py`, `src/tools.py` quedaron con
  `## TODO` sin resolver y dependían de `ibm_watsonx_ai` (nube IBM). No se
  modificaron: siguen intactos para quien quiera completar el lab original.
- Nuevos artefactos (versión Ollama, en paralelo, sin tocar los del lab):
  - `src/models_ollama.py` — esquemas Pydantic (`RecipeSuggestionOutput`,
    `NutrientAnalysisOutput`) para forzar salida estructurada.
  - `src/tools_ollama.py` — 4 tools de CrewAI (`ExtractIngredientsTool`,
    `FilterIngredientsTool`, `DietaryFilterTool`, `NutrientAnalysisTool`).
    Vision vía `POST /api/generate` de Ollama con imagen en base64; filtrado
    por dieta determinístico (diccionario fijo, sin LLM).
  - `src/crew_ollama.py` — `NourishBotRecipeCrew` y `NourishBotAnalysisCrew`
    (`CrewBase` de CrewAI), 4 agentes + 4 tasks, `Process.sequential`, LLM de
    los agentes vía `crewai.LLM(model="ollama/<modelo>", base_url=...)`.
    Reutiliza `src/config/agents.yaml` y `src/config/tasks.yaml` del lab
    original (ya eran genéricos, sin referencias a WatsonX/OpenAI).
  - `app_ollama.py` — interfaz Gradio (puerto 5010, distinto al 5000 del
    original) con el mismo formateo de salida Markdown.
  - `config.ini` — `[ollama]` (base_url, vision_model, text_model,
    temperature), `[datos]`, `[logging]`. Incluye perfil comentado para GPU
    de 16 GB.
  - `requirements-ollama.txt` — dependencias mínimas (CrewAI, Gradio,
    requests, pydantic, PyYAML, pillow) sin SDKs cloud.
  - `MANUAL.md` — arquitectura completa (diagrama de flujo agentes/tools),
    tabla de modelos recomendados por GPU, cómo correrlo, qué es
    determinístico vs. dependiente del LLM.
- **Modelos recomendados:**
  - RTX 3050 Ti (6 GB VRAM): visión `llava:7b` (~4.7 GB, no descargado
    todavía — requiere `ollama pull llava:7b`), alternativa liviana
    `moondream` (~1.7 GB); texto `qwen2.5:7b-instruct-q4_K_M` (ya descargado).
  - RTX A4500 (16 GB VRAM): visión `qwen2.5vl:7b` (~6 GB) o
    `llama3.2-vision:11b` (~7.9 GB); texto `qwen2.5:14b-instruct-q4_K_M`
    (~9 GB) o `qwen2.5:7b-instruct-q4_K_M` si se prefiere no descargar el de 14B.
  - Ninguno de los modelos de visión recomendados estaba descargado en este
    equipo al momento de este checkpoint (`ollama list` solo mostraba
    modelos de texto: qwen2.5, llama3.1, phi4-mini, nemotron-mini,
    deepseek-coder, embeddings).
- **No probado en esta sesión (build inicial):** ni `crewai` ni ningún modelo
  de visión estaban instalados/descargados en este entorno; no se ejecutó
  `app_ollama.py` end-to-end contra un Ollama real. Ver sección "Pendiente"
  de `MANUAL.md`.
- Cómo verificar: `ollama pull llava:7b`, `pip install -r requirements-ollama.txt`,
  `python app_ollama.py`, probar los flujos `recipe` y `analysis` con las
  imágenes de `examples/`.
- Estado: en curso — arquitectura y código completos, pendiente prueba
  end-to-end contra Ollama real con el modelo de visión descargado.
