# NourishBot Local (Ollama) — Manual completo

## Tabla de contenidos

1. [Qué es esto](#qué-es-esto)
2. [Arquitectura](#arquitectura)
3. [Puntos clave para entender cómo funciona](#puntos-clave-para-entender-cómo-funciona)
4. [Cómo correrlo](#cómo-correrlo)
5. [Logging estilo log4j](#logging-estilo-log4j)
6. [Adaptar a otros casos de negocio](#adaptar-a-otros-casos-de-negocio)
7. [Propuestas de optimización](#propuestas-de-optimización)
8. [Modelos de Ollama recomendados](#modelos-de-ollama-recomendados)
9. [Troubleshooting](#troubleshooting)

---

## Qué es esto

Versión **100% local** del lab `NourishBot` (IBM SkillsNetwork / CrewAI).

**Original (con TODOs):** IBM WatsonX cloud + archivo `src/` incompleto.  
**Esta versión:** Ollama local (en tu máquina) + código completo + soberanía total del dato.

Caso de uso end-to-end:
1. Subes foto de comida → 
2. Detecta ingredientes (modelo de visión) → 
3. Filtra por restricción dietética (reglas fijas, determinísticas) → 
4. Sugiere recetas O analiza nutrientes (modelo de razonamiento)

**Cero datos salen de tu máquina.** Ni imagen, ni prompts, ni respuestas — todo corre contra Ollama en `localhost:11434` (o tu servidor Ollama configurado).

---

## Arquitectura

### Vista de alto nivel

```
┌─────────────────────────────────────────────────────────────┐
│                    NOURISH BOT FLUJO                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Usuario →  app.py (Gradio UI)                              │
│             ├─ Sube imagen                                   │
│             ├─ Elige restricción dietética (opcional)        │
│             └─ Elige workflow: "recipe" O "analysis"         │
│                      │                                       │
│                      ▼                                       │
│            src/crew.py (CrewAI orchestration)               │
│            ├─ NourishBotRecipeCrew     (3 agents)           │
│            └─ NourishBotAnalysisCrew   (2 agents)           │
│                      │                                       │
│        ┌─────────────┴─────────────┐                        │
│        ▼                           ▼                        │
│  RECIPE FLOW              ANALYSIS FLOW                      │
│  1. Detect ingredients    1. Detect ingredients              │
│  2. Dietary filter        2. Nutrient analysis               │
│  3. Suggest recipes       ↓ returns JSON                     │
│  ↓ returns JSON                                              │
│                                                               │
│  app.py formatea → Markdown → Gradio UI                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘

                    CAPAS DE EJECUCIÓN

┌──────────────────────────────────────────────────────────────┐
│ Capa 1: AGENTES (CrewAI)                                    │
│ ├─ ingredient_detection_agent      (LLM que decide qué ver) │
│ ├─ dietary_filtering_agent         (LLM + DietaryFilterTool)│
│ ├─ nutrient_analysis_agent         (LLM + NutrientTool)     │
│ └─ recipe_suggestion_agent         (LLM, razonamiento puro) │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Capa 2: TOOLS (src/tools.py)                               │
│ ├─ ExtractIngredientsTool          (vision API a Ollama)    │
│ ├─ FilterIngredientsTool           (limpieza de texto)      │
│ ├─ DietaryFilterTool               (diccionario fijo)       │
│ └─ NutrientAnalysisTool            (vision API a Ollama)    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Capa 3: INFERENCIA LOCAL (Ollama)                          │
│ ├─ vision_model    = llava:7b (o similar)                  │
│ ├─ text_model      = qwen2.5:7b-instruct-q4_K_M            │
│ └─ base_url        = http://convergenciax02:11434          │
└──────────────────────────────────────────────────────────────┘
```

### Flujo de datos en RECIPE workflow

```
input: {
  uploaded_image: "uploaded_image.jpg",
  dietary_restrictions: "vegan",
  workflow_type: "recipe"
}

Task 1: ingredient_detection_task
├─ Agent: ingredient_detection_agent (LLM text_model)
├─ Tools: ExtractIngredientsTool (llama vision_model en base64)
│         FilterIngredientsTool (regex + json)
└─ Output: ["chicken", "rice", "garlic", "soy sauce"]

Task 2: dietary_filtering_task  (context: Task 1)
├─ Agent: dietary_filtering_agent (LLM text_model)
├─ Tools: DietaryFilterTool (diccionario DIETARY_EXCLUSIONS["vegan"])
└─ Output: ["rice", "garlic"]  (sin pollo, sin soy = no vegan)

Task 3: recipe_suggestion_task (context: Task 2)
├─ Agent: recipe_suggestion_agent (LLM text_model, sin tools)
├─ Prompt: "Con estos ingredientes [rice, garlic], sugiere recetas"
├─ Output_pydantic: RecipeSuggestionOutput (Pydantic valida JSON)
└─ Output: {
    "recipes": [
      {"title": "Garlic Fried Rice",
       "ingredients": [...],
       "instructions": "...",
       "calorie_estimate": 450}
    ]
  }

app.py: format_recipe_output() convierte JSON → Markdown → UI Gradio
```

### Decisiones arquitectónicas clave

#### 1. **Separación Vision ↔ Razonamiento**

```
LLM del Agent (text_model)          Tool que ve imagen (vision_model)
─────────────────────────────────────────────────────────────────
Pregunta: "¿Qué hay en esta foto?"  Responde: Lee la imagen via Ollama
│ Decide: "Voy a llamar                    API /api/generate +
│ ExtractIngredientsTool"                  base64 imagen
│                                          
└─→ Tool se conecta directo a Ollama  local, no por el LLM
```

**Por qué:** El modelo de text (qwen2.5 7B) es rápido pero no multimodal. El modelo de vision (llava 7B) ve bien pero es más lento y usarlo para razonamiento puro sería ineficiente. Separar es más barato.

#### 2. **Filtrado dietético determinístico (no LLM)**

```python
# DENTRO de DietaryFilterTool
DIETARY_EXCLUSIONS = {
    "vegan": {"chicken", "beef", "milk", "egg", ...},
    "vegetarian": {...},
    "gluten-free": {...},
    "keto": {...}
}

# NO hacemos: "LLM, ¿esto es vegano?"  ← Arriesgado, dependiente del modelo
# Hacemos: diccionario lookup               ← Determinístico, testeable

filtered = [ing for ing in ingredients if ing.lower() not in excluded_set]
```

**Ventaja:** Es 100% predecible. No importa el modelo, cuál sea el día, o cuándo se ejecute — "pollo no es vegano" siempre. Se puede testear con tests unitarios normales sin evals de LLM.

#### 3. **Salida estructurada con Pydantic**

```python
# En src/models.py
class RecipeSuggestionOutput(BaseModel):
    recipes: List[RecipeItem]
    
class RecipeItem(BaseModel):
    title: str
    ingredients: List[str]
    instructions: str
    calorie_estimate: int

# En src/crew.py, task definition
@task
def recipe_suggestion_task(self) -> Task:
    return Task(
        config=self.tasks_config["recipe_suggestion_task"],
        agent=self.recipe_suggestion_agent(),
        context=[self.dietary_filtering_task()],
        output_pydantic=RecipeSuggestionOutput  # ← validación automática
    )

# En app.py, acceso seguro a campos
final_output = final_output.to_dict()
recipes = final_output.get("recipes", [])
for recipe in recipes:
    title = recipe['title']  # garantizado que existe y es string
```

**Ventaja:** CrewAI reintenta si el modelo no respeta el esquema. `app.py` accede campos sin parseo manual de texto.

#### 4. **Config externalizada en INI**

```ini
[ollama]
base_url = http://convergenciax02:11434
vision_model = llava:7b
text_model = qwen2.5:7b-instruct-q4_K_M
temperature = 0.2
```

- **Sin cambios de código:** cambiar GPU (6GB → 16GB) es editar `config.ini`.
- **Sin hardcoding:** El `base_url` no está en `crew.py` ni `tools.py`.
- **Multi-máquina:** `base_url` puede ser `localhost`, `192.168.1.100`, o un hostname de red.

---

## Puntos clave para entender cómo funciona

### 1. CrewAI es "orquestación de agentes con context encadenado"

```python
# Cada Task corre en orden (Process.sequential)
# Cada Task sabe del resultado de la anterior vía context=[]

Task 1 → Output1
Task 2 (context=[Task 1]) → puede leer Output1 en su prompt
Task 3 (context=[Task 2]) → puede leer Output2 en su prompt
```

CrewAI pasa el resultado anterior como texto en el prompt del siguiente agent. Así, ingredient_detection_task detecta `["chicken", "rice"]` en la imagen, y dietary_filtering_task lee eso y filtra por dieta.

### 2. LiteLLM es un "router de proveedores"

```python
# El prefijo "ollama/" le dice a LiteLLM: "esta es una llamada a Ollama, no OpenAI"
crewai.LLM(
    model="ollama/qwen2.5:7b-instruct-q4_K_M",
    base_url="http://localhost:11434",
    temperature=0.2
)

# LiteLLM internamente construye la llamada HTTP correcta hacia Ollama:
# POST /api/chat (compatible OpenAI) o /api/generate (API nativa)
```

Es lo que permite a CrewAI (diseñado originalmente para OpenAI) hablar con Ollama sin reescribir CrewAI.

### 3. Base64 y visión multisodal

```python
# En ExtractIngredientsTool._run()
def _call_ollama_vision(image_path: str, prompt: str) -> str:
    image_b64 = _encode_image_base64(image_path)  # Lee bytes, a base64
    
    payload = {
        "model": "llava:7b",
        "prompt": "Describe los ingredientes",
        "images": [image_b64],  # ← campo clave, Ollama lo decodifica
        "stream": False,
    }
    resp = requests.post(f"{base_url}/api/generate", json=payload)
    return resp.json()["response"]
```

Ollama recibe base64, lo decodifica a imagen en memoria, la pasa al modelo de visión, y devuelve texto. La imagen **nunca se guarda en disco del servidor** si `base_url` es remoto.

### 4. Logging como debugging

El logging log4j que agregué es como un "video" de toda ejecución:

```
2026-09-03 10:16:46 [INFO ] __main__ - [ANALYZE_FOOD] Iniciando análisis - workflow: recipe
2026-09-03 10:16:46 [DEBUG] __main__ - [ANALYZE_FOOD] Guardando imagen en: uploaded_image.jpg
2026-09-03 10:16:46 [INFO ] src.tools - [CALL_OLLAMA_VISION] Enviando POST a http://convergenciax02:11434/api/generate...
2026-09-03 10:16:55 [INFO ] src.tools - [CALL_OLLAMA_VISION] ✓ Respuesta recibida (523 chars)
2026-09-03 10:16:56 [INFO ] src.tools - [ExtractIngredientsTool._run] ✓ Ingredientes detectados: chicken, rice, garlic...
2026-09-03 10:16:57 [INFO ] src.crew - [NourishBotRecipeCrew.crew] ✓ Crew RECIPE construido exitosamente
2026-09-03 10:16:57 [INFO ] __main__ - [ANALYZE_FOOD] Ejecutando crew.kickoff() - esto puede tomar minutos...
2026-09-03 10:17:30 [INFO ] __main__ - [ANALYZE_FOOD] ✓ kickoff() completado
```

Cada log tiene timestamp, nivel (INFO/DEBUG/ERROR), módulo fuente, y un tag de contexto `[NOMBRE_FUNCION]` para rastrear de dónde viene.

---

## Cómo correrlo

### Requisitos previos

1. **Python 3.13** (o 3.12+). NO Python 3.14 — crewai no lo soporta.
2. **Ollama corriendo** en `http://convergenciax02:11434` (o la URL de `config.ini`).
3. **Modelo de visión descargado:** `ollama pull llava:7b` (o el que uses en config.ini).

### Opción A: Usar el venv compartido `env-llm-ia`

Si el bug de `gradio_client` + pydantic ya fue arreglado (gradio 5.50.0 + gradio_client 1.14.0), puedes usar el venv compartido:

```powershell
cd "C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\03 Build a Multi-Agent - CrewAI\NourishBot-Ollama"

# Instalar dependencias (una sola vez)
C:\workspace-vc\env-llm-ia\Scripts\python.exe -m pip install -r requirements.txt

# Ejecutar
C:\workspace-vc\env-llm-ia\Scripts\python.exe app.py
```

Abre `http://127.0.0.1:5010`.

### Opción B: Crear venv 3.13 dedicado (fallback)

Si `env-llm-ia` falla, crea un venv limpio dentro del proyecto:

```powershell
# Crear venv
& "C:\Users\Joel\AppData\Local\Programs\Python\Python313\python.exe" -m venv .venv313

# Instalar
& ".\.venv313\Scripts\python.exe" -m pip install -r requirements.txt

# Ejecutar
& ".\.venv313\Scripts\python.exe" app.py
```

### Verificación rápida

```powershell
# Importa sin errores?
C:\workspace-vc\env-llm-ia\Scripts\python.exe -c "from src.crew import NourishBotRecipeCrew; print('OK')"

# Ollama alcanzable?
curl http://convergenciax02:11434/api/tags

# App levanta?
C:\workspace-vc\env-llm-ia\Scripts\python.exe app.py
# (Debería decir "Launching on http://127.0.0.1:5010")

# Responde HTTP?
curl http://127.0.0.1:5010  # (desde otra terminal)
```

---

## Logging estilo log4j

### Configuración automática

En `app.py` al inicio:

```python
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)-5s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

Esto configura **todos los loggers** de toda la app (app.py, src/crew.py, src/tools.py) a nivel DEBUG o superior, formato consistente, salida a stdout (terminal).

### Niveles

```
DEBUG:   Detalles de bajo nivel (valores de variables, codificación base64, etc.)
INFO:    Eventos principales (app iniciada, imagen guardada, crew construido)
WARNING: Algo anormal pero recuperable (JSON no válido, fallback usado)
ERROR:   Algo rompió (conexión a Ollama falló, crash de modelo)
```

### Cómo leerlo

```
2026-09-03 10:16:46 [INFO ]  __main__                - [ANALYZE_FOOD] Iniciando análisis...
│            │        │       │                       │
│            │        │       └─ Módulo Python        │ Tag de contexto (función)
│            │        └─ Nivel (5 chars, justificado)
│            └─ Timestamp ISO
└─ Fecha

Busca "[ERROR]" o "[WARNING]" para localizaciones rápidas de problemas.
Búscalos "[NOMBRE_TOOL]" para rastrear el flujo de una tool específica.
```

---

## Adaptar a otros casos de negocio

### Patrón general

NourishBot es un caso específico de "orquestación de agentes con visión":

```
Imagen → Agent (decide si necesita ver) → Tool (vision API) → JSON → Otro Agent
```

Este patrón aplica a:

#### 1. **Análisis de documentos** (facturas, contratos, DNI)

```
Caso: OCR + extracción de campos

Reemplaza:
├─ ExtractIngredientsTool → ExtractFieldsTool
│  └─ Prompt: "Extrae nombre, fecha, monto, beneficiario"
├─ FilterIngredientsTool → ValidateFieldsTool
│  └─ Regla: "Si fecha > hoy, error"
└─ Modelos: RecipeSuggestionOutput → DocumentFields

Herramientas nuevas: ninguna, misma estructura

Config a editar:
[vision_model] = "qwen2.5vl:7b"  (mejor OCR que llava)
temperature = 0.1  (más determinístico, menos creativo)

Tasks: 1 (no necesitas múltiples agents)
```

#### 2. **Clasificación de imágenes + acción**

```
Caso: "Sube foto de producto → clasifica categoría → sugiere precio"

Reemplaza:
├─ ingredient_detection_agent → product_classifier_agent
├─ ExtractIngredientsTool → ClassifyProductTool
│  └─ Output: {"category": "electronics", "subcategory": "phones"}
├─ DietaryFilterTool → PricingRulesTool
│  └─ Diccionario: {"phones": [99, 299, 599]}
└─ recipe_suggestion_agent → price_suggester_agent (LLM que elige precio)

Models.py: ProductClassification (Pydantic)
```

#### 3. **Análisis de inspección de obra / mantenimiento**

```
Caso: "Foto de máquina dañada → detecta problemas → sugiere mantenimiento"

Reemplaza:
├─ ExtractIngredientsTool → DefectDetectionTool
│  └─ Prompt: "¿Qué daño ves en esta máquina?"
├─ DietaryFilterTool → SeverityClassificationTool
│  └─ Diccionario: {"oxidation": "LOW", "crack": "HIGH"}
└─ NutrientAnalysisTool → MaintenanceRecommendationTool
   └─ Output: {"defects": [...], "urgency": "MEDIUM", "parts_needed": [...]}
```

### Checklist para adaptar

- [ ] ¿Necesitas visión? (sí → usa vision_model en tools; no → quita ExtractIngredientsTool)
- [ ] ¿Los datos se filtran por reglas fijas o por LLM?
  - Reglas fijas → determinístico como DietaryFilterTool
  - LLM → agent con tools que preguntan al modelo
- [ ] ¿Output es JSON estructurado? → Pydantic en `src/models.py`
- [ ] ¿Cuántos agents? Empieza con 1-2, añade más solo si los prompts se vuelven complejos.
- [ ] Edita `config.ini`: vision_model, text_model, temperature, base_url si es remoto.
- [ ] Copiar `src/config/agents.yaml` y `src/config/tasks.yaml`, reemplaza rol/descripción.

---

## Propuestas de optimización

### 1. **Caché de modelos en VRAM**

**Problema actual:** Si `vision_model` ≠ `text_model`, Ollama descarga/recarga entre tasks (~2-5 sec overhead).

**Solución:** Usa el mismo modelo para visión y texto.

```ini
# Config A: Modelos distintos (actual, flexible)
vision_model = llava:7b
text_model = qwen2.5:7b-instruct-q4_K_M
temperature = 0.2

# Config B: Modelo único (más rápido, VRAM fijo)
vision_model = qwen2.5vl:7b
text_model = qwen2.5vl:7b  # ← mismo modelo
# Ventaja: 0 segundos de intercambio, qwen es VLM moderno
# Desventaja: redacción de recetas algo menor que 7B text-only
```

**Implementación:** Sin cambios de código, solo `config.ini`.

### 2. **Paralelización de tasks no-dependientes**

**Problema actual:** Process.sequential ejecuta todo en orden.

```
ingredient_detection_task (5 seg)
└─ dietary_filtering_task (2 seg, depende de task 1)
└─ recipe_suggestion_task (10 seg, depende de task 2)
TOTAL: 17 segundos
```

**Mejora:** Si hay tareas que NO dependen una de otra, ejecutarlas en paralelo.

```python
# Uso hipotético: si ingredient_detection carga imagen Y
# simultaneously queremos nutrient_analysis sobre la MISMA imagen
# (ambas leen de `context`, no dependen una de otra)

return Crew(
    agents=[...],
    tasks=[
        self.ingredient_detection_task(),
        self.nutrient_analysis_task(),        # ← paralelo con ingredient
        self.dietary_filtering_task(),        # ← depende de ingredient
        self.recipe_suggestion_task(),        # ← depende de dietary
    ],
    process=Process.hierarchical,  # ← cambiar a hierarchical/parallel
)
```

**Limitación:** CrewAI 1.x soporta mejor Process.sequential. Process.hierarchical existe pero requiere un "manager agent". Evaluar si vale la complejidad extra por el ahorro de tiempo.

### 3. **Streaming de respuesta**

**Problema actual:** El usuario espera a que `crew.kickoff()` complete (10-30 seg).

**Mejora:** Streamear tokens conforme el LLM genera, no esperar final.

```python
# Actual (blocking)
final_output = crew_obj.kickoff(inputs=inputs)

# Mejora (con streaming)
async for partial_output in crew_obj.kickoff_stream(inputs=inputs):
    # Envía partial_output al frontend Gradio en tiempo real
    yield partial_output
```

**Implementación:** Requiere Gradio streaming (`.stream()` callback) + CrewAI async. Mediano esfuerzo, gran UX.

### 4. **Cache de Ollama con "keep_alive"**

Ollama tiene parámetro `keep_alive` para mantener modelos cargados más tiempo sin unloadear automáticamente.

```python
# En _call_ollama_vision / _call_ollama_text
payload = {
    "model": model,
    "prompt": prompt,
    "images": [...],
    "stream": False,
    "options": {
        "temperature": TEMPERATURE,
        "keep_alive": "5m"  # ← mantén el modelo 5 min después del último uso
    }
}
```

**Efecto:** Si la siguiente tarea corre dentro de 5 min, el modelo ya está en VRAM. Cero reload.

### 5. **Re-ranking de ingredientes por confianza**

**Problema actual:** ExtractIngredientsTool devuelve lista plana. ¿"Chicken" es 99% seguro o 40% conjetura?

**Mejora:** Pedir al modelo de visión confianza.

```python
# Prompt mejorado
prompt = """
List every ingredient with confidence 0-100.
Format: ingredient|confidence
chicken|95
rice|90
garnish|30
"""
```

Luego, DietaryFilterTool usa esto: si confianza < 50%, no lo cuenta como ingrediente.

### 6. **Fine-tuning de modelos para dominio**

Si NourishBot corre 1000+ veces y ves que siempre falla en "identificar germinados", considera fine-tune de llava con imágenes de tu dominio.

```bash
# Pseudocódigo (requiere Ollama 0.2+)
ollama create nourish-vision-ft --modelfile Modelfile.finetune
# Modelfile especifica: base model + datos de entrenamiento
```

**Esfuerzo:** Alto (requiere dataset de imágenes etiquetadas).  
**ROI:** Solo si el caso de uso es muy específico y la precisión importa.

### 7. **Evaluación automática (evals)**

Sin ver logs, ¿cómo sabes si el cambio de modelo mejoró la calidad?

```python
# Script: evals.py
test_cases = [
    {
        "image_path": "examples/food-1.jpg",
        "expected_ingredients": {"chicken", "rice", "garlic"},
        "expected_calories": 400
    },
    # ... más casos
]

for test in test_cases:
    output = crew.kickoff(test)
    detected = set(output["ingredients"])
    precision = len(detected & test["expected"]) / len(detected)
    recall = len(detected & test["expected"]) / len(test["expected"])
    print(f"P={precision:.2%}, R={recall:.2%}")
```

Así ves antes/después de cambiar modelos o parámetros.

### 8. **Observabilidad remota (Langtrace / LangSmith)**

Si Ollama está en otro servidor, ¿cómo debuggeas latencia?

```python
# Con LangSmith (requiere login)
from langchain.callbacks import LangSmithCallbackHandler

callbacks = [LangSmithCallbackHandler(api_key="...")]
final_output = crew_obj.kickoff(inputs=inputs, callbacks=callbacks)
```

Dashboard en langsmith.com mostrará timing de cada llamada, tokens, etc.

---

## Modelos de Ollama recomendados

### RTX 3050 Ti (6 GB VRAM)

| Rol | Modelo | Tamaño | Notas |
|-----|--------|--------|-------|
| **Visión** | `llava:7b` | 4.7 GB | Default recomendado. `ollama pull llava:7b` |
| — | `moondream` | 1.7 GB | Más rápido, menos detalle (mejor para UI responsiva) |
| **Texto** | `qwen2.5:7b-instruct-q4_K_M` | 4.7 GB | Ya descargado, buen JSON |
| — | `phi4-mini:3.8b` | 2.5 GB | Más rápido, razonamiento menor |

**Perfil equilibrado:** llava:7b + qwen 7B = ~8 GB en disco, pero Ollama mantiene 1 en VRAM, recarga cuando cambia (aceptable en 6GB).

### RTX A4500 (16 GB VRAM)

| Rol | Modelo | Tamaño | Notas |
|-----|--------|--------|-------|
| **Visión** | `qwen2.5vl:7b` | 6 GB | Mejor VLM moderno, excelente OCR |
| — | `llama3.2-vision:11b` | 7.9 GB | Más grande, mejor razonamiento sobre imágenes |
| **Texto** | `qwen2.5:14b-instruct-q4_K_M` | 9 GB | Excelente JSON, mejor escritura |

---

## Troubleshooting

### "TypeError: argument of type 'bool' is not iterable"

**Causa:** gradio_client viejo (1.5.4) + pydantic 2.11+ genera schemas booleanos que gradio 5.12.0 no entiende.

**Fix:** 
```bash
pip install "gradio==5.50.0"  # trae gradio_client 1.14.0 automáticamente
```

### "Cannot import name 'LLM' from 'crewai'"

**Causa:** crewai viejo (0.1.x) sin la API moderna.

**Fix:**
```bash
pip install "crewai==1.15.18" "crewai-tools==1.15.18"
pip install -r requirements.txt
```

### "No address associated with hostname 'convergenciax02'"

**Causa:** Ollama corre en otra máquina pero el hostname no resuelve desde la tuya.

**Fixes:**
1. Usar IP: `base_url = http://192.168.1.100:11434`
2. Editar `/etc/hosts` (Linux) o `C:\Windows\System32\drivers\etc\hosts` (Windows):
   ```
   192.168.1.100 convergenciax02
   ```
3. Apuntar a `localhost` si Ollama corre localmente: `base_url = http://localhost:11434`

### "Connection refused: 127.0.0.1:5010"

Gradio no levanta. Mira los logs:

```
Si ves "[ERROR] ❌ ERROR al lanzar servidor":
├─ Puerto 5010 ya ocupado → cambiar en app.py o matar proceso
├─ Ollama no accesible → revisar base_url en config.ini
└─ Falta modelo → ollama pull llava:7b
```

### App levanta pero "Analyze" nunca termina

**Probables causas:**
1. Ollama no responde → `curl http://convergenciax02:11434/api/tags`
2. Modelo descargándose → normal, espera
3. GPU out of memory → reducir model size en config.ini
4. Logs dirán más → mira [CALL_OLLAMA_VISION] y timing

### "Successfully installed" pero import falla

```bash
pip install -r requirements.txt --force-reinstall --no-cache-dir
```

Algunas veces wheels caché están corruptos.

---

## Resumen ejecutivo

NourishBot es un **patrón reutilizable** de "orquestación de agentes + visión local". 

**Adaptable a:** documentos, inspección, clasificación, cualquier cosa que necesite "ver imagen + razonar + actuar".

**Clave arquitectónica:** Separación vision ↔ razonamiento, determinismo donde sea posible, Pydantic para salida.

**Performance:** 30-60 seg por análisis (visión 5-10s + razonamiento 20-50s). Paralelización y caché pueden bajar esto a 10-20s.

**Próximos pasos:** Prueba cambiar modelos en `config.ini`, mira logs, adapta a tu caso de uso siguiendo el checklist.
