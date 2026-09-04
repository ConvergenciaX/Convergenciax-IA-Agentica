# Referencia de Logs — NourishBot-Ollama

## Qué esperar al ejecutar la app

```powershell
C:\workspace-vc\env-llm-ia\Scripts\python.exe app.py
```

Verás:

### Startup (primeros 1-2 segundos)

```
2026-09-03 10:16:30 [DEBUG] __main__ - Python: 3.13.13 (main, Aug 29 2024, 10:08:00)
2026-09-03 10:16:30 [DEBUG] __main__ - Working directory: C:\workspace-vc\LLM\CognitiveClass\...
2026-09-03 10:16:30 [INFO ] __main__ - Leyendo configuración desde: C:\workspace-vc\...\config.ini
2026-09-03 10:16:30 [INFO ] __main__ - Ollama config - base_url: http://convergenciax02:11434, vision: llava:7b, text: qwen2.5:7b-instruct-q4_K_M
2026-09-03 10:16:30 [INFO ] __main__ - === CONSTRUYENDO UI GRADIO ===
2026-09-03 10:16:31 [INFO ] __main__ - Lanzando servidor Gradio en http://127.0.0.1:5010...
```

✅ Si llegaste aquí, app está lista. Abre `http://127.0.0.1:5010` en el navegador.

---

## Cuando haces clic en "Analyze" (flujo RECIPE)

### Fase 1: Imagen guardada (0.1s)

```
2026-09-03 10:16:45 [INFO ] __main__ - [ANALYZE_FOOD] Iniciando análisis - workflow: recipe, restricciones: ''
2026-09-03 10:16:45 [DEBUG] __main__ - [ANALYZE_FOOD] Guardando imagen en: uploaded_image.jpg
2026-09-03 10:16:45 [INFO ] __main__ - [ANALYZE_FOOD] ✓ Imagen guardada
```

### Fase 2: Crew construido (0.5s)

```
2026-09-03 10:16:46 [INFO ] __main__ - [ANALYZE_FOOD] Instanciando crew: recipe
2026-09-03 10:16:46 [DEBUG] src.crew - [BaseNourishBotCrew.__init__] image_data=uploaded_image.jpg, dietary_restrictions=
2026-09-03 10:16:46 [DEBUG] src.crew - [BaseNourishBotCrew.__init__] Leyendo agents.yaml desde C:\...\src\config\agents.yaml
2026-09-03 10:16:46 [DEBUG] src.crew - [BaseNourishBotCrew.__init__] ✓ Agentes cargados: ['ingredient_detection_agent', 'dietary_filtering_agent', 'nutrient_analysis_agent', 'recipe_suggestion_agent']
2026-09-03 10:16:46 [INFO ] src.crew - [BUILD_LLM] ✓ LLM creado: ollama/qwen2.5:7b-instruct-q4_K_M
2026-09-03 10:16:46 [INFO ] __main__ - [ANALYZE_FOOD] ✓ NourishBotRecipeCrew instanciado
2026-09-03 10:16:46 [INFO ] src.crew - [NourishBotRecipeCrew.crew] ✓ Crew RECIPE construido exitosamente
```

### Fase 3: Kickoff (la magia — 30-60 segundos)

```
2026-09-03 10:16:47 [INFO ] __main__ - [ANALYZE_FOOD] Ejecutando crew.kickoff() - esto puede tomar minutos...

[CrewAI agentes corriendo... verás outputs internos de CrewAI aquí]

# Task 1: ingredient_detection_task ejecutándose
2026-09-03 10:16:50 [INFO ] src.tools - [CALL_OLLAMA_VISION] Iniciando llamada a http://convergenciax02:11434/api/generate con modelo llava:7b
2026-09-03 10:16:50 [DEBUG] src.tools - [CALL_OLLAMA_VISION] Codificando imagen a base64...
2026-09-03 10:16:50 [DEBUG] src.tools - [CALL_OLLAMA_VISION] ✓ Imagen codificada (87234 chars)
2026-09-03 10:16:50 [DEBUG] src.tools - [CALL_OLLAMA_VISION] Enviando POST a http://convergenciax02:11434/api/generate...
2026-09-03 10:17:05 [INFO ] src.tools - [CALL_OLLAMA_VISION] ✓ Respuesta recibida (523 chars)
2026-09-03 10:17:05 [DEBUG] src.tools - [CALL_OLLAMA_VISION] Response: chicken, rice, garlic, soy sauce, sesame oil, scallions...
2026-09-03 10:17:05 [INFO ] src.tools - [ExtractIngredientsTool._run] ✓ Ingredientes detectados: chicken, rice, garlic...

# Task 2: dietary_filtering_task ejecutándose (context: Task 1)
2026-09-03 10:17:10 [INFO ] src.tools - [FilterIngredientsTool._run] Iniciando filtrado de ingredientes
2026-09-03 10:17:10 [DEBUG] src.tools - [FilterIngredientsTool._run] Raw input: chicken\nrice\ngarlic\nsoy sauce\nses...
2026-09-03 10:17:10 [INFO ] src.tools - [FilterIngredientsTool._run] ✓ 4 ingredientes después del filtrado
2026-09-03 10:17:10 [DEBUG] src.tools - [FilterIngredientsTool._run] Ingredientes filtrados: ['chicken', 'rice', 'garlic', 'sesame oil']

# Task 3: recipe_suggestion_task ejecutándose (context: Task 2)
# LLM razonando en puro texto puro, sin tool
2026-09-03 10:17:30 [INFO ] __main__ - [ANALYZE_FOOD] ✓ kickoff() completado
```

### Fase 4: Formateo de salida (0.1s)

```
2026-09-03 10:17:30 [DEBUG] __main__ - [ANALYZE_FOOD] Output raw type: <class 'crewai.agents.agent.ResultObject'>
2026-09-03 10:17:30 [INFO ] __main__ - [ANALYZE_FOOD] ✓ Output convertido a dict - keys: dict_keys(['recipes'])
2026-09-03 10:17:31 [INFO ] __main__ - [ANALYZE_FOOD] Formateando salida como recipe
2026-09-03 10:17:31 [DEBUG] [FORMAT_RECIPE] Iniciando formateo de salida recipe
2026-09-03 10:17:31 [DEBUG] [FORMAT_RECIPE] Cantidad de recetas en output: 2
2026-09-03 10:17:31 [INFO ] __main__ - [ANALYZE_FOOD] ✓ COMPLETADO EXITOSAMENTE
```

✅ Resultado aparece en la UI en Markdown.

---

## Cuando algo falla: Análisis rápido de logs

### Error: "Connection refused" (Ollama no responde)

```
2026-09-03 10:17:05 [ERROR] src.tools - [CALL_OLLAMA_VISION] ❌ ERROR de conexión: ConnectionError: Failed to establish a new connection: [Errno 10061] No se puede establecer conexión...
```

**Qué revisar:**
1. ¿Ollama está corriendo? `ollama list` en otra terminal
2. ¿Es el hostname correcto? Mira `base_url` en `config.ini`
3. ¿Firewall bloquea? `curl http://convergenciax02:11434/api/tags` desde terminal

### Error: "Cannot import name 'LLM' from 'crewai'"

```
2026-09-03 10:16:47 [ERROR] __main__ - ❌ ERROR: ImportError: cannot import name 'LLM' from 'crewai'...
```

**Qué hacer:**
```powershell
pip install "crewai==1.15.18" "crewai-tools==1.15.18"
```

### Error: "TypeError: argument of type 'bool' is not iterable"

```
2026-09-03 10:16:31 [ERROR] __main__ - ❌ ERROR: TypeError: argument of type 'bool' is not iterable...
```

**Qué hacer:**
```powershell
pip install "gradio==5.50.0"
```

---

## Leyendo logs como diagnostico

### Buscar bottlenecks

```
2026-09-03 10:16:50 [DEBUG] src.tools - [CALL_OLLAMA_VISION] Enviando POST...
2026-09-03 10:17:05 [INFO ] src.tools - [CALL_OLLAMA_VISION] ✓ Respuesta recibida
     ↑
     15 segundos = Ollama vision model tardó 15s
```

Si eso es lento (>30s para una imagen simple), considera:
- Modelo más rápido: `moondream` en lugar de `llava:7b`
- GPU más potente si el modelo es muy grande

### Buscar errores silenciosos

```
2026-09-03 10:17:10 [WARNING] src.tools - ⚠ No se extrajo JSON válido, usando fallback
```

Significa: el modelo de visión no devolvió JSON válido, la app usó un default vacío. Si ves muchos, considera:
- Mejorar el prompt en la tool
- Usar modelo de visión más capaz (qwen2.5vl en lugar de llava)

### Timeline total

Cuenta líneas de `[INFO]` principales:

```
10:16:47 [ANALYZE_FOOD] Ejecutando crew.kickoff()
10:17:30 [ANALYZE_FOOD] ✓ kickoff() completado

= 43 segundos total
```

---

## Niveles de log explicados

- **[DEBUG]:** Detalles técnicos (JSON, tamaños, rutas). Útil si algo falla misteriosamente.
- **[INFO]:** Hitos principales (app iniciada, imagen guardada, crew construido, completado). Mira estos para el flujo.
- **[WARNING]:** Algo anormal pero recuperable (JSON fallback usado, configuración por defecto).
- **[ERROR]:** Algo rompió. Aquí está tu culpable.

---

## Simulación: ANALYSIS workflow (más corto)

```
[ANALYZE_FOOD] Iniciando análisis - workflow: analysis, restricciones: ''
[ANALYZE_FOOD] ✓ Imagen guardada
[ANALYZE_FOOD] Instanciando crew: analysis
[ANALYZE_FOOD] ✓ NourishBotAnalysisCrew instanciado
[NourishBotAnalysisCrew.crew] ✓ Crew ANALYSIS construido exitosamente
[ANALYZE_FOOD] Ejecutando crew.kickoff() - esto puede tomar minutos...

[Task 1: ingredient_detection_task]
[CALL_OLLAMA_VISION] ✓ Respuesta recibida
[ExtractIngredientsTool._run] ✓ Ingredientes detectados

[Task 2: nutrient_analysis_task]
[CALL_OLLAMA_VISION] Enviando POST...
[CALL_OLLAMA_VISION] ✓ Respuesta recibida (JSON de nutrientes)
[NutrientAnalysisTool._run] ✓ JSON extraído - dish='Teriyaki Chicken with Rice'

[ANALYZE_FOOD] ✓ kickoff() completado
[FORMAT_ANALYSIS] Iniciando formateo de salida analysis
[ANALYZE_FOOD] ✓ COMPLETADO EXITOSAMENTE
```

---

## Configurar nivel de log (si quieres menos verbosidad)

En `app.py`:

```python
logging.basicConfig(
    level=logging.INFO,  # cambiar DEBUG → INFO para menos logs
    # ... resto igual
)
```

- `DEBUG`: todo (útil para diagnosticar)
- `INFO`: solo hitos (flujo limpio)
- `WARNING`: solo problemas recuperables
- `ERROR`: solo errores
