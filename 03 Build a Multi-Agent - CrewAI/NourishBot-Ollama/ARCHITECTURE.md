# Arquitectura NourishBot-Ollama

## Capas de la aplicación

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 0: INTERFAZ                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Gradio UI (http://127.0.0.1:5010)                   │  │
│  │ ├─ File Upload (imagen JPG/PNG)                     │  │
│  │ ├─ Textbox (dietary_restrictions, opcional)         │  │
│  │ ├─ Radio (workflow: recipe / analysis)              │  │
│  │ └─ Button (Analyze)                                 │  │
│  │     │ input JSON → analyze_food(image, diet, flow) │  │
│  │     └─ output Markdown ← format_*_output()         │  │
│  └──────────────────────────────────────────────────────┘  │
│                        ↓                                     │
├─────────────────────────────────────────────────────────────┤
│  CAPA 1: ORQUESTACIÓN                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ src/crew.py                                          │  │
│  │ ├─ NourishBotRecipeCrew                             │  │
│  │ │  └─ Crew([agent1, agent2, agent3], tasks=[...])  │  │
│  │ └─ NourishBotAnalysisCrew                           │  │
│  │    └─ Crew([agent1, agent2], tasks=[...])          │  │
│  │                                                      │  │
│  │ Process.sequential: Task N → Task N+1, con context  │  │
│  └──────────────────────────────────────────────────────┘  │
│                        ↓                                     │
├─────────────────────────────────────────────────────────────┤
│  CAPA 2: AGENTES & HERRAMIENTAS                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ RECIPE FLOW:                                         │  │
│  │ ingredient_detection_agent                          │  │
│  │   └─ Tool: ExtractIngredientsTool (vision API)      │  │
│  │   └─ Tool: FilterIngredientsTool (regex)            │  │
│  │       └─ → dietary_filtering_agent                  │  │
│  │            └─ Tool: DietaryFilterTool (diccionario) │  │
│  │                └─ → recipe_suggestion_agent         │  │
│  │                     (LLM puro, sin tool)            │  │
│  │                                                      │  │
│  │ ANALYSIS FLOW:                                       │  │
│  │ ingredient_detection_agent                          │  │
│  │   └─ Tool: ExtractIngredientsTool (vision API)      │  │
│  │       └─ → nutrient_analysis_agent                  │  │
│  │            └─ Tool: NutrientAnalysisTool (vision)   │  │
│  └──────────────────────────────────────────────────────┘  │
│                        ↓                                     │
├─────────────────────────────────────────────────────────────┤
│  CAPA 3: LLAMADAS A OLLAMA                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ src/tools.py ← HTTP POST a Ollama                    │  │
│  │ ├─ _call_ollama_vision(image_b64, prompt)           │  │
│  │ │  └─ POST /api/generate                            │  │
│  │ │     ├─ model: llava:7b                            │  │
│  │ │     ├─ images: [base64_bytes]                     │  │
│  │ │     └─ prompt: "Extract ingredients..."           │  │
│  │ │         → response JSON                           │  │
│  │ │                                                    │  │
│  │ └─ _call_ollama_text(prompt)                        │  │
│  │    └─ POST /api/generate                            │  │
│  │       ├─ model: qwen2.5:7b-instruct-q4_K_M          │  │
│  │       └─ prompt: "Given ingredients, suggest..."    │  │
│  │           → response text                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                        ↓                                     │
├─────────────────────────────────────────────────────────────┤
│  CAPA 4: RUNTIME LOCAL (Ollama en machine)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Ollama Server (http://convergenciax02:11434)         │  │
│  │ ├─ Vision Model: llava:7b (4.7 GB VRAM)             │  │
│  │ ├─ Text Model: qwen2.5:7b-instruct (4.7 GB VRAM)    │  │
│  │ └─ GPU: RTX 3050 Ti (6 GB) — modelo A la vez        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Flujo de datos RECIPE

```
USER INPUTS
├─ uploaded_image.jpg  ← guardado en disco, ruta pasada
├─ dietary_restrictions = "vegan" (opcional)
└─ workflow_type = "recipe"
        ↓
┌──────────────────────────────────────────────────────────────┐
│ analyze_food() en app.py                                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 1. Image guardada en disco ← uploaded_image.jpg             │
│                                                               │
│ 2. NourishBotRecipeCrew instanciado                         │
│    ├─ Lee agents.yaml → define 4 agentes                   │
│    ├─ Lee tasks.yaml → define 3 tasks                      │
│    └─ Crea LLM: ollama/qwen2.5:7b-instruct                │
│                                                               │
│ 3. crew.crew() retorna Crew object                         │
│    ├─ agentes: [ingredient_detection_agent, ...]           │
│    ├─ tareas: [ingredient_detection_task, ...]             │
│    └─ process: sequential                                   │
│                                                               │
│ 4. crew.kickoff(inputs={image, diet, workflow})           │
│    ↓                                                         │
│    Task 1: ingredient_detection_task                       │
│    ├─ Agent: ingredient_detection_agent (LLM)              │
│    │  Prompt: "Extract ingredients from this image"        │
│    │  Available Tools: ExtractIngredientsTool,             │
│    │                   FilterIngredientsTool               │
│    │                                                        │
│    │ Agent decides: "Voy a llamar ExtractIngredientsTool" │
│    │  Tool: _call_ollama_vision(uploaded_image.jpg, ...)  │
│    │    ├─ Lee imagen del disco                           │
│    │    ├─ Codifica a base64                              │
│    │    ├─ POST a Ollama vision_model                    │
│    │    └─ Respuesta: "chicken, rice, garlic, ..."       │
│    │                                                        │
│    │ Agent decides: "Necesito limpiar esta lista"         │
│    │  Tool: FilterIngredientsTool                          │
│    │    ├─ Toma raw text                                  │
│    │    ├─ Quita numeración, espacios, duplicados        │
│    │    └─ Output JSON: ["chicken", "rice", "garlic"]    │
│    │                                                        │
│    └─ OUTPUT Task 1: Pasa al prompt de Task 2 como texto │
│                                                               │
│    Task 2: dietary_filtering_task (context: Task 1)        │
│    ├─ Agent: dietary_filtering_agent (LLM)                │
│    │  Prompt: "Filter ingredients by vegan. Available:     │
│    │           [chicken, rice, garlic] (from Task 1)"     │
│    │  Available Tools: DietaryFilterTool                  │
│    │                                                        │
│    │ Agent decides: "Voy a llamar DietaryFilterTool"      │
│    │  Tool: DietaryFilterTool                              │
│    │    ├─ Diccionario lookup: DIETARY_EXCLUSIONS["vegan"]│
│    │    ├─ Elimina: chicken (not vegan)                   │
│    │    └─ Keeps: ["rice", "garlic"]                      │
│    │                                                        │
│    └─ OUTPUT Task 2: Pasa al prompt de Task 3             │
│                                                               │
│    Task 3: recipe_suggestion_task (context: Task 2)        │
│    ├─ Agent: recipe_suggestion_agent (LLM)                │
│    │  Prompt: "Suggest recipes using: [rice, garlic]"    │
│    │  Available Tools: (ninguna, razonamiento puro)       │
│    │                                                        │
│    │ Agent generates: LLM call a text_model                │
│    │  POST Ollama text_model                              │
│    │  Response (raw): "Recipe 1: Garlic Fried Rice..."   │
│    │                                                        │
│    │ CrewAI valida contra output_pydantic                 │
│    │ ├─ output_pydantic=RecipeSuggestionOutput            │
│    │ └─ Reintenta si JSON no es válido                    │
│    │                                                        │
│    └─ OUTPUT Task 3 (final):                               │
│       {                                                     │
│         "recipes": [                                       │
│           {                                                 │
│             "title": "Garlic Fried Rice",                 │
│             "ingredients": ["rice", "garlic", ...],       │
│             "instructions": "Heat oil...",                │
│             "calorie_estimate": 450                       │
│           }                                                 │
│         ]                                                   │
│       }                                                     │
│                                                               │
│ 5. Salida en Markdown                                      │
│    └─ format_recipe_output(final_output) → HTML          │
│                                                               │
│ 6. Retorna a Gradio UI                                    │
│    ├─ Markdown renderizado                               │
│    └─ Usuario ve: receta formateada                      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Separación Vision ↔ Razonamiento

**Principio clave:** Dos modelos distintos, roles separados.

```
┌─────────────────────────────────┐
│ LLM del Agent (text_model)      │
│ qwen2.5:7b-instruct             │
├─────────────────────────────────┤
│ "Sé razonar bien"               │
│ "No sé ver imágenes"            │
│ "Tomo decisiones"               │
│                                  │
│ "¿Qué hay en la imagen?"        │
│ ↓ Pregunta a la herramienta     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Tool que ve imagen              │
│ ExtractIngredientsTool          │
├─────────────────────────────────┤
│ Llama Ollama vision_model       │
│ ↓ POST /api/generate            │
│ └─ llava:7b (lee imagen)        │
│                                  │
│ Respuesta: "chicken, rice..."   │
│ ↓ Retorna al LLM                │
└─────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ LLM decide qué hacer            │
│ "Ok, tengo ingredientes.        │
│  Ahora voy a filtrarlos."       │
│                                  │
│ Llama DietaryFilterTool         │
└─────────────────────────────────┘

VENTAJA: Modelos especializados, sin overhead de multimodalidad pura.
COSTO: Coordinar 2 modelos, gestionar caché en 6 GB.
```

---

## Estado y transiciones

```
┌─────────┐
│ INICIO  │
└────┬────┘
     │
     ▼ app.py: analyze_food()
┌─────────────────────┐
│ Imagen guardada     │
│ config cargada      │
└────┬────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Crew instanciado                    │
│ ├─ Agentes creados                  │
│ ├─ LLM conectado a Ollama           │
│ └─ Tasks encadenadas                │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│ crew.kickoff() ejecutándose         │
│ ├─ Task 1: vision + cleanup         │
│ ├─ Task 2: filter + rule            │
│ └─ Task N: LLM reasoning            │
│                                     │
│ Cada task lee el output anterior    │
└────┬────────────────────────────────┘
     │
     ▼ Pydantic valida output
┌─────────────────────────────────────┐
│ Output estructurado JSON            │
│ {recipes: [...] o nutrients: {...}} │
└────┬────────────────────────────────┘
     │
     ▼ format_*_output()
┌─────────────────────────────────────┐
│ Markdown formateado                 │
└────┬────────────────────────────────┘
     │
     ▼ Gradio UI
┌─────────────────────────────────────┐
│ Usuario ve resultado                │
└─────────────────────────────────────┘
```

---

## Posibles extensiones / adaptaciones

```
┌──────────────────────┐
│ NourishBot ACTUAL    │
│ ├─ Imagen comida     │
│ ├─ Vision model      │
│ ├─ Text model        │
│ └─ Output receta     │
└──────────────────────┘

EXTENSIONES CERCANAS:

┌──────────────────────┐
│ Documento Analysis   │
│ ├─ Imagen factura    │
│ ├─ Vision model (OCR)│
│ ├─ Text model        │
│ └─ Output JSON fields│
└──────────────────────┘

┌──────────────────────┐
│ Product Classifier   │
│ ├─ Imagen producto   │
│ ├─ Vision model      │
│ ├─ Rule dictionary   │
│ ├─ Price LLM         │
│ └─ Output precio     │
└──────────────────────┘

MISMA ARQUITECTURA, inputs/outputs distintos.
```

---

## Ejecución paralela (futuro)

Si quisieras paralelizar tareas no-dependientes:

```
ACTUAL (Process.sequential):
Task 1: 5s  ─┐
            ├─ Task 2: 2s ─┐
                          ├─ Task 3: 10s
                          └─ Task 4: 3s

Total: 20 segundos


FUTURO (Process.hierarchical, si es posible):
Task 1: 5s  ─┬─ Task 2: 2s ─┐
            │               ├─ Task 4: 3s
            └─ Task 3: 10s ─┘

Total: 15 segundos (si Task 2 y 3 no dependen uno del otro)
       Ganancia: 25% (depende del caso real)
```

**Tradeoff:** Paralelización complica la orquestación. CrewAI 1.x no lo soporta bien.
