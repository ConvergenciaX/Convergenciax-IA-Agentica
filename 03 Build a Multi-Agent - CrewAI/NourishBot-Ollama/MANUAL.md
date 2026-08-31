# NourishBot local (Ollama) — Arquitectura y manual de uso

## Qué es esto

Version local del lab `NourishBot` (IBM SkillsNetwork / CrewAI), que en su forma
original queda con varios `## TODO` sin resolver en `models.py`, `tools.py` y
`crew.py`, y depende de `ibm_watsonx_ai` (nube de IBM) tanto para el modelo de
visión como para el de texto.

Esta versión implementa el mismo caso de uso end-to-end — detectar
ingredientes en una foto, filtrarlos por dieta, analizar nutrientes o sugerir
recetas — pero **100% sobre Ollama local**: ni la imagen ni el texto del
usuario salen de la máquina, no se requiere API key de ningún proveedor.

Los archivos originales del lab (`app.py`, `crew.py`, `models.py`, `tools.py`,
`src/crew.py`, `src/models.py`, `src/tools.py`) **no se modificaron** — siguen
disponibles tal cual para completar el ejercicio del curso si quieres hacerlo
tú mismo. La versión Ollama vive en archivos paralelos:

| Original (lab, con TODOs) | Versión Ollama (completa) |
|---|---|
| `app.py` | `app_ollama.py` |
| `src/crew.py` | `src/crew_ollama.py` |
| `src/models.py` | `src/models_ollama.py` |
| `src/tools.py` | `src/tools_ollama.py` |
| `requirements.txt` | `requirements-ollama.txt` |
| — | `config.ini` (nuevo) |

`src/config/agents.yaml` y `src/config/tasks.yaml` **sí se reutilizan tal
cual** — ya eran genéricos (no mencionaban WatsonX ni OpenAI), así que no hacía
falta duplicarlos.

## Arquitectura

```
                         ┌─────────────────────┐
                         │   app_ollama.py       │  Gradio UI (puerto 5010)
                         │   (analyze_food)      │
                         └──────────┬───────────┘
                                    │ inputs: imagen, dieta, workflow
                                    ▼
                    ┌───────────────────────────────┐
                    │  src/crew_ollama.py             │
                    │  NourishBotRecipeCrew /          │
                    │  NourishBotAnalysisCrew          │  Process.sequential
                    └───────────────┬───────────────┘
                                    │ orquesta 3-4 Agents (CrewAI)
        ┌───────────────┬──────────┴───────────┬──────────────────┐
        ▼               ▼                      ▼                  ▼
 ingredient_      dietary_filtering_    nutrient_analysis_   recipe_suggestion_
 detection_agent  agent                 agent                agent
        │               │                      │                  │
        ▼               ▼                      ▼                  ▼
 ExtractIngredients  DietaryFilterTool   NutrientAnalysisTool   (sin tool,
 Tool + Filter-      (reglas fijas,      (modelo de vision +     razona en
 IngredientsTool     sin LLM)            parseo de JSON)         texto puro)
        │
        ▼
 ┌─────────────────────────────┐
 │ Ollama local                 │
 │ - modelo de VISION (llava)   │  <- src/tools_ollama.py llama
 │ - modelo de TEXTO (qwen2.5)  │  <- crewai.LLM(model="ollama/...")
 │ http://localhost:11434       │
 └─────────────────────────────┘
```

Puntos de diseño clave:

- **Separación vision vs. texto.** El LLM del `Agent` (definido en
  `crew_ollama.py` con `crewai.LLM(model="ollama/<text_model>", ...)`) es
  quien razona y decide qué tool llamar. Las tools que necesitan "ver" la
  imagen (`ExtractIngredientsTool`, `NutrientAnalysisTool`, en
  `tools_ollama.py`) hacen su propia llamada HTTP al modelo de visión vía
  `/api/generate` de Ollama, con la imagen en base64. Este es el mismo patrón
  del lab original (que llamaba a WatsonX `ModelInference` directamente
  dentro de las tools), solo que contra un servidor local.
- **Filtrado por dieta determinístico.** `DietaryFilterTool` no le pregunta al
  LLM "¿esto es vegano?" — usa un diccionario fijo de exclusiones
  (`DIETARY_EXCLUSIONS` en `tools_ollama.py`). Que el pollo no sea vegano es
  un hecho de dominio, no una opinión del modelo; hacerlo determinístico lo
  vuelve testeable con un test unitario normal, sin necesitar evals de LLM.
- **Salida estructurada con Pydantic.** `recipe_suggestion_task` y
  `nutrient_analysis_task` usan `output_pydantic=RecipeSuggestionOutput` /
  `NutrientAnalysisOutput` (`src/models_ollama.py`). CrewAI valida/reintenta
  el parseo si el modelo no respeta el esquema — así `app_ollama.py` puede
  leer `.recipes`, `.nutrients`, etc. de forma confiable en vez de parsear
  texto libre.
- **Soberanía del dato completa.** Toda llamada de red va a
  `config.ini → [ollama] base_url` (por defecto `localhost:11434`). No hay
  ninguna API key, ni de OpenAI ni de WatsonX, en ningún archivo de este
  proyecto.

## Modelos de Ollama recomendados por GPU

NourishBot necesita **dos capacidades**: visión (leer la foto) y
razonamiento/JSON (filtrar, analizar, redactar). `config.ini` las separa en
`vision_model` y `text_model`.

Consideración importante de VRAM: por defecto, Ollama mantiene **un solo
modelo cargado en VRAM a la vez** y lo descarga/recarga al pedir otro modelo
distinto (unos segundos extra, no un error). Si `vision_model` y
`text_model` son distintos, el crew hará ese intercambio 1-2 veces por
corrida. En una GPU de 6 GB esto es aceptable para un flujo de chat no
interactivo como este; si se vuelve molesto, usa el mismo modelo para ambos
roles (ver tabla).

### RTX 3050 Ti Laptop — 6 GB VRAM

| Rol | Modelo recomendado | Tamaño | Notas |
|---|---|---|---|
| Visión (default) | `llava:7b` | ~4.7 GB (Q4) | Buen balance detalle/velocidad para reconocer ingredientes y platos. **No está descargado todavía** — `ollama pull llava:7b`. |
| Visión (alternativa liviana) | `moondream` | ~1.7 GB | Mucho más rápido y deja margen de VRAM, pero identifica menos ingredientes en fotos con muchos elementos (ej. una nevera llena). Buena opción si `llava:7b` se siente lento o si vas a correr algo más en la GPU al mismo tiempo. |
| Texto (default) | `qwen2.5:7b-instruct-q4_K_M` | 4.7 GB | Ya lo tienes descargado. Buen seguimiento de instrucciones/JSON, clave para los `output_pydantic`. |
| Texto (alternativa) | `phi4-mini:3.8b` | 2.5 GB | Ya descargado, más rápido, calidad de razonamiento algo menor — útil si priorizas velocidad de respuesta. |

Evitar en 6 GB: `llama3.1:8b-instruct-q2_K` (ya lo tienes, pero Q2 degrada
mucho el seguimiento de JSON estructurado, justo lo que necesitan las tasks
de recetas/nutrientes); `deepseek-coder:6.7b` (dominio equivocado, no tiene
capacidad de visión).

**Para minimizar el intercambio de modelos en 6 GB**, una opción es igualar
ambos roles a `llava:7b` (los modelos de visión modernos también razonan
razonablemente bien en texto plano) — sacrifica algo de calidad de redacción
en las recetas a cambio de que el crew completo use un solo modelo cargado.

### RTX A4500 — 16 GB VRAM

Con 16 GB hay margen para modelos de visión más grandes/capaces y para tener
visión+texto sin tanta presión de intercambio.

| Rol | Modelo recomendado | Tamaño | Notas |
|---|---|---|---|
| Visión (default) | `qwen2.5vl:7b` | ~6 GB (Q4) | Mejor comprensión de detalle visual y de conteo de ítems que llava 7B; buena opción "moderna" de VLM. Requiere `ollama pull qwen2.5vl:7b`. |
| Visión (alternativa, más grande) | `llama3.2-vision:11b` | ~7.9 GB (Q4) | Alternativa sólida de Meta, buen razonamiento sobre imágenes complejas (platos con muchos componentes). |
| Texto (default) | `qwen2.5:14b-instruct-q4_K_M` | ~9 GB | Mucho mejor razonamiento/estructura JSON que la versión 7B; en 16 GB cabe cómodo junto con el modelo de visión si Ollama necesita tenerlos cerca en el tiempo. Requiere `ollama pull qwen2.5:14b-instruct-q4_K_M`. |
| Texto (ya descargado, opción rápida) | `qwen2.5:7b-instruct-q4_K_M` | 4.7 GB | Si prefieres no descargar el de 14B, este ya funciona bien y deja aún más margen de VRAM. |

Con 16 GB también es viable, si más adelante se quiere exprimir calidad al
máximo, un modelo de visión más grande como `llava:34b` (~20 GB en Q4 —
**no entra** en 16 GB) — evitarlo en esta GPU; quedarse en el rango 7-11B de
visión es el punto correcto para esta tarjeta.

## Configuración (`config.ini`)

```ini
[ollama]
base_url = http://localhost:11434
vision_model = llava:7b
text_model = qwen2.5:7b-instruct-q4_K_M
temperature = 0.2

[datos]
uploaded_image_path = uploaded_image.jpg

[logging]
level = INFO
```

Cambiar de GPU/perfil (3050 Ti ↔ A4500) o de modelo es solo editar este
archivo — no hace falta tocar `crew_ollama.py` ni `tools_ollama.py`.

## Cómo correrlo

1. Confirma que Ollama está corriendo: `ollama list`.
2. Descarga el modelo de visión elegido (ninguno viene preinstalado en este
   equipo todavía): `ollama pull llava:7b` (perfil 6 GB) o
   `ollama pull qwen2.5vl:7b` (perfil 16 GB).
3. Instala dependencias: `pip install -r requirements-ollama.txt`.
4. Ajusta `config.ini` si vas a usar el perfil de 16 GB (descomenta esas
   líneas o reemplaza los valores).
5. Corre la app: `python app_ollama.py` → abre `http://127.0.0.1:5010`.
6. Sube una imagen (puedes usar las de `examples/`), elige restricción
   dietética (opcional) y el flujo `recipe` o `analysis`, y pulsa "Analyze".

## Qué es determinístico vs. qué depende del LLM

- **Determinístico / testeable con tests unitarios normales:** parseo de
  ingredientes (`FilterIngredientsTool`), filtrado por dieta
  (`DietaryFilterTool`, diccionario fijo), extracción de JSON de la respuesta
  del modelo de visión (`_extract_json_block`), formateo de salida a Markdown
  (`app_ollama.py`).
- **Depende del LLM / requiere evaluación cualitativa (evals), no tests
  exactos:** calidad de detección de ingredientes en la imagen, redacción de
  instrucciones de receta, estimación de calorías/nutrientes (son
  aproximaciones del modelo, no un cálculo nutricional certificado — no usar
  esta app como fuente médica/clínica).

## Pendiente / no verificado en esta sesión

- No se ejecutó el pipeline end-to-end contra un Ollama real en esta sesión:
  ni `crewai` ni un modelo de visión (`llava:7b` / `qwen2.5vl:7b`) estaban
  instalados/descargados en este entorno al momento de escribir el código.
  Antes de dar por buena la versión 3050 Ti: `ollama pull llava:7b`,
  `pip install -r requirements-ollama.txt`, correr `app_ollama.py` y probar
  ambos flujos (`recipe` y `analysis`) con las imágenes de `examples/`.
- Si `crewai.LLM(model="ollama/...")` no encuentra el proveedor en la versión
  de `crewai`/`litellm` instalada, revisar que la versión de `litellm`
  resuelta por `pip` soporte el prefijo `ollama/` (viene incluido en
  `crewai==0.75.0` vía su propia dependencia de litellm, pero versiones muy
  distintas de crewai pueden variar la sintaxis exacta del proveedor).
