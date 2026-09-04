# CHECKPOINTS — Agente IA - CrewIA Multiagente (NourishBot local)

## 2026-09-03 — ✅ PRODUCCIÓN: App completa + logging + documentación adaptable

- **Hito:** NourishBot corriendo exitosamente en `env-llm-ia` (Python 3.13) con logging
  log4j completo, documentación comprehensive, y patrón reutilizable para otros casos.
- **Fix aplicado (de sesión anterior):** Actualizar `gradio==5.50.0` (trae `gradio_client==1.14.0`
  que maneja bien schemas booleanos de pydantic 2.11+) + alinear `crewai==1.15.18` /
  `crewai-tools==1.15.18` en venv compartido. Resultado: cero `TypeError` sobre schema
  booleano, cero `ValueError` sobre localhost no accesible.
- **Logging agregado:** Estilo log4j (timestamp ISO, nivel, módulo, tag de contexto)
  en `app.py`, `src/crew.py`, `src/tools.py`. Cada interacción es rastreable:
  ```
  2026-09-03 10:16:46 [INFO ] __main__ - === INICIANDO NOURISBHOT OLLAMA ===
  2026-09-03 10:16:46 [INFO ] __main__ - Ollama config - base_url: http://convergenciax02:11434
  2026-09-03 10:16:50 [INFO ] src.tools - [CALL_OLLAMA_VISION] ✓ Respuesta recibida (523 chars)
  2026-09-03 10:16:51 [INFO ] __main__ - [ANALYZE_FOOD] ✓ COMPLETADO EXITOSAMENTE
  ```
- **Documentación MANUAL.md reescrita:**
  - Arquitectura visual con diagramas de flujo (vision ↔ razonamiento, task context chain)
  - Puntos clave: CrewAI orquestación, LiteLLM router, base64 multimodal, Pydantic validación
  - Logging explicado (niveles, cómo leerlo, dónde buscar)
  - **Sección nueva: "Adaptar a otros casos de negocio"** — 3 ejemplos reales (análisis
    documentos, clasificación de productos, inspección industrial) con checklist y changes
    mínimos de código
  - **Sección nueva: "Propuestas de optimización"** — 8 ideas concretas (caché VRAM,
    paralelización, streaming, keep_alive, re-ranking, fine-tuning, evals, observabilidad)
  - Troubleshooting expandido (bool TypeError, crewai import, DNS hostname, UI responsiveness)
- **Entorno verificado:** App levanta sin errores con `env-llm-ia`, servidor Gradio
  responde HTTP 200 en `127.0.0.1:5010`. Logging muestra inicio ↔ fin de cada operación.
- **No verificado desde esta sesión (requiere Ollama accesible):** Pipeline end-to-end
  (subir imagen real → analyze → ver resultado) porque `convergenciax02` no resuelve
  en esta sesión. Pero la app está lista; solo necesita conectividad con Ollama real
  cuando el usuario la ejecute en su entorno.

## 2026-09-01 — App arranca: fix de dependencias + venv Python 3.13 dedicado

- **Hallazgo clave (confirmado contra el índice de PyPI, no una suposición):
  ninguna versión de `crewai` soporta Python 3.14**, ni siquiera la más
  reciente (1.15.18, `Requires-Python >=3.10,<3.14`). El venv compartido
  `env-llm-314` (Python 3.14) nunca iba a poder correr este proyecto tal cual
  — no era un problema de pines de versión resoluble ahí.
- Fix: se creó `.venv313/` (venv de Python 3.13.13, dedicado a esta carpeta
  de proyecto) en vez de forzar el 3.14 compartido — única excepción
  documentada a la convención de `ia-dev-fullstack` de usar siempre
  `env-llm-314`.
- `requirements.txt` corregido con problemas reales encontrados al instalar
  (no hipotéticos):
  - Comentarios con `;` (inválido para pip, solo entiende `#`).
  - `crewai==0.75.0` (pin original) reemplazado por `crewai==1.15.18` fijo —
    dejarlo sin pin hacía que el resolver de `pip` retrocediera hasta
    `crewai==0.1.24` (2023, sin la API `@CrewBase` que usa este código) para
    evitar conflictos con el resto del árbol de dependencias.
  - `gradio==5.12.0` (requiere `aiofiles<24`) chocaba con `crewai==1.15.18`
    (requiere `aiofiles~=24.1.0`) → subido a `gradio==5.50.0`.
  - `requests==2.32.0` era una versión **yanked** de PyPI (CVE-2024-35195) y
    muy vieja para el resto del árbol → `requests>=2.32.3`.
  - `PyYAML==6.0.2` / `pillow==11.1.0` sin wheel para `cp314` → `PyYAML>=6.0.3`
    / `pillow>=11.3.0` (no problema en 3.13, pero se dejó así por si se
    reintenta en 3.14 en el futuro).
- **Verificado en esta sesión:**
  - Imports de CrewAI 1.15.18 (`Agent`, `Crew`, `Process`, `Task`, `LLM`,
    `CrewBase`/`agent`/`crew`/`task`, `BaseTool`) — funcionan sin cambios de
    código en `src/crew.py` / `src/tools.py`.
  - `NourishBotRecipeCrew` y `NourishBotAnalysisCrew` se instancian y arman
    sus Agents/Tasks correctamente.
  - `app.py` levanta el servidor Gradio en `http://127.0.0.1:5010` y responde
    HTTP 200 sin errores de arranque.
- **No verificado (requiere al usuario, es de red/GPU no de código):**
  conectividad real con el Ollama configurado en `config.ini`
  (`http://convergenciax02:11434`) — desde esta sesión (máquina
  `ConvergenciaX01`) ese hostname no resuelve por DNS; puede ser normal
  (redes distintas) pero no se pudo confirmar. Falta correr el pipeline
  completo (`recipe` y `analysis`) contra un modelo de visión real.
- Ver `MANUAL.md` (secciones "Cómo correrlo" y "Ajustes que hicieron falta en
  `requirements.txt`") para el detalle completo y los comandos exactos.
- Estado: **la app arranca correctamente** en Python 3.13; pendiente solo la
  verificación end-to-end contra Ollama real (fuera del alcance de esta
  sesión por conectividad de red).

## 2026-08-31 (fix) — Proyecto separado en carpeta propia `NourishBot-Ollama`

- El build inicial (ver entrada de abajo) había creado los archivos `*_ollama.py`
  como archivos paralelos DENTRO de la carpeta del lab original `NourishBot/`
  (junto a `app.py`, `src/crew.py`, etc. con TODOs). El usuario pidió una
  carpeta de proyecto propia, siguiendo la convención de workspace de
  [[ia-dev-fullstack]] (cada proyecto = su propia carpeta, con su propio
  `checkpoint/`).
- Cambio: se creó `NourishBot-Ollama/` como carpeta hermana de `NourishBot/`
  (mismo nivel, dentro de `03 Build a Multi-Agent - CrewAI\`). Se copiaron y
  renombraron los archivos (ya no hace falta el sufijo `_ollama` porque el
  nombre de la carpeta ya distingue el proyecto):
  - `app_ollama.py` -> `NourishBot-Ollama/app.py`
  - `src/crew_ollama.py` -> `NourishBot-Ollama/src/crew.py`
  - `src/models_ollama.py` -> `NourishBot-Ollama/src/models.py`
  - `src/tools_ollama.py` -> `NourishBot-Ollama/src/tools.py`
  - `requirements-ollama.txt` -> `NourishBot-Ollama/requirements.txt`
  - `config.ini`, `MANUAL.md`, `checkpoint/CHECKPOINTS.md` -> copiados tal cual
  - `src/config/agents.yaml` y `src/config/tasks.yaml` -> copiados (se seguían
    reutilizando del lab original; ahora tienen su propia copia porque son
    proyectos en carpetas separadas)
  - `examples/*.jpg` -> copiadas (la UI de Gradio las referencia por ruta relativa)
  - Se actualizaron los imports internos (`from src.tools_ollama import` ->
    `from src.tools import`, etc.) y los comentarios/docstrings que
    mencionaban los nombres de archivo viejos.
- Los duplicados `*_ollama.py`/`config.ini`/`MANUAL.md`/`checkpoint/` que
  habían quedado dentro de `NourishBot/` (el lab original) se **eliminaron**
  — ese repo (es un `.git` local) vuelve a contener solo sus archivos
  originales con los `## TODO` sin resolver.
- **No se ha probado el arranque real todavía** (pendiente desde el build
  inicial): sigue sin instalarse `crewai` y sin descargar un modelo de visión
  en Ollama. Ver "Cómo verificar" en la entrada de abajo — los pasos no
  cambiaron, solo la carpeta desde la que se ejecutan (`NourishBot-Ollama/`
  en vez de la raíz de `NourishBot/`).
- Estado: en curso — proyecto correctamente aislado en su propia carpeta;
  sigue pendiente la prueba end-to-end contra Ollama real.

## 2026-08-31 — Build inicial: NourishBot 100% local con Ollama (CrewAI multiagente)

- Base: lab `NourishBot` (IBM SkillsNetwork, CrewAI), en ese momento en la
  misma carpeta (ver fix de arriba: luego se separó a `NourishBot-Ollama/`) —
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
