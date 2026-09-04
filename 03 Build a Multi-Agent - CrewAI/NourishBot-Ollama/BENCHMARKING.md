# Benchmarking — Medir y optimizar rendimiento

## Resumen rápido

Ahora `app.py` registra en archivo:
- **`logs/nourish_bot.log`** — logs detallados (stdout + archivo)
- **`logs/benchmark.log`** — JSON Lines con tiempos de cada ejecución

Analiza con:
```powershell
python analyze_benchmark.py
# o
python analyze_benchmark.py --workflow recipe
```

---

## Configuración (config.ini)

### Logging

```ini
[logging]
level = DEBUG              # DEBUG, INFO, WARNING, ERROR
log_dir = logs             # Dónde guardar logs
log_file = nourish_bot.log # Nombre del log principal
benchmark_file = benchmark.log  # Nombre del benchmark
log_max_size_mb = 10       # Rotar log cuando alcance 10 MB
log_backup_count = 5       # Mantener 5 logs viejos (.1, .2, .3...)
```

### Benchmark

```ini
[benchmark]
enabled = true             # Activar benchmarking
log_config = true          # Guardar config en cada ejecución
json_format = true         # Formato JSON Lines (no plain text)
```

---

## Cómo funciona

### Cada vez que ejecutas "Analyze":

1. **Inicio:** app.py imprime parámetros de configuración
   ```
   [ANALYZE_FOOD] Parámetros: vision_model=llava:7b text_model=qwen3:32b
   [ANALYZE_FOOD] Temperatura: vision=0.1, text=0.3
   ```

2. **Fases temporizadas:**
   ```
   Phase 1: save_image                     0.15s
   Phase 2: prepare_inputs                 0.02s
   Phase 3: instantiate_crew               0.50s
   Phase 4: get_crew_object                0.05s
   Phase 5: kickoff (LENTO)               45.32s  ← Principal
   Phase 6: process_output                 0.10s
   Phase 7: format_output                  0.05s
   ───────────────────────────────────────────
   TOTAL                                  46.19s
   ```

3. **Archivo benchmark.log:**
   ```json
   {
     "timestamp": "2026-09-03T10:16:47.123456",
     "workflow": "recipe",
     "dietary_restrictions": "vegan",
     "total_time_seconds": 46.19,
     "phase_times": {
       "save_image": 0.15,
       "kickoff": 45.32,
       "total": 46.19
     },
     "config": {
       "vision_model": "llava:7b",
       "text_model": "qwen3:32b",
       "temperature_vision": 0.1,
       "temperature_text": 0.3
     }
   }
   ```

---

## Analizar resultados

### Ver resumen general

```powershell
cd C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\03 Build a Multi-Agent - CrewAI\NourishBot-Ollama
python analyze_benchmark.py
```

Output:
```
✓ Cargados 5 benchmarks desde logs/benchmark.log

================================================================================
WORKFLOW: RECIPE
================================================================================

Tiempo Total (segundos):
  Min:      42.10s
  Max:      50.23s
  Promedio: 46.19s
  Corridas:  5

Tiempos por Fase:
  format_output       : 0.05s (min:  0.04s, max:  0.06s,  0.1% del total)
  get_crew_object     : 0.05s (min:  0.04s, max:  0.08s,  0.1% del total)
  instantiate_crew    : 0.50s (min:  0.42s, max:  0.61s,  1.1% del total)
  kickoff             :45.32s (min: 40.00s, max: 48.50s, 98.1% del total)
  prepare_inputs      : 0.02s (min:  0.02s, max:  0.03s,  0.0% del total)
  process_output      : 0.10s (min:  0.08s, max:  0.12s,  0.2% del total)
  save_image          : 0.15s (min:  0.10s, max:  0.20s,  0.3% del total)

Últimas 5 ejecuciones:
  [1] 2026-09-03T10:10:15.234567
      Total: 46.19s | Diet: vegan
      Config: vision=llava:7b text=qwen3:32b temp_vis=0.1 temp_txt=0.3
        - save_image: 0.15s
        - kickoff: 45.32s
```

### Filtrar por workflow

```powershell
python analyze_benchmark.py --workflow analysis
```

---

## Workflow típico: A/B testing

Para medir si un cambio mejora el rendimiento:

### Test 1: Config original

```ini
[ollama]
vision_model = llava:7b
text_model = qwen2.5:7b-instruct-q4_K_M
temperature_vision = 0.1
temperature_text = 0.3
```

Ejecuta 3-5 veces: sube imagen diferente cada vez, Analyze, anota tiempos.

Resultado esperado: ~30-40s (según tu GPU).

### Test 2: Cambio optimizado

```ini
[ollama]
vision_model = moondream          # ← Cambio: más rápido
text_model = qwen2.5:7b-instruct-q4_K_M
temperature_vision = 0.1
temperature_text = 0.3
keep_alive = 10m                  # ← Agregado: evita reloads
```

Ejecuta 3-5 veces igual.

### Analiza

```powershell
python analyze_benchmark.py --workflow recipe
```

Compara tiempos:
```
Test 1: Promedio 38.50s ❌ línea base
Test 2: Promedio 18.30s ✓ 52% más rápido
```

**Ganancia:** (38.50 - 18.30) / 38.50 × 100 = **52% más rápido** = 20.2 segundos ahorrados

---

## Parametrización — qué ajustar en config.ini

| Parámetro | Rango | Efecto en latencia | Efecto en calidad |
|-----------|-------|-------------------|------------------|
| `vision_model` | llava:7b, moondream, qwen2.5vl | moondream = -50% | moondream = -10% |
| `text_model` | qwen:7b, qwen:14b, phi4 | qwen:7b = -30% | qwen:7b = baseline |
| `temperature_vision` | 0.0-0.8 | 0.0 = +2% rápido | 0.0 = más determinístico |
| `temperature_text` | 0.0-0.8 | 0.0 = +2% rápido | 0.0 = recetas más planas |
| `num_predict` | 100-500 | 100 = -40% tiempo | 100 = respuestas cortas |
| `top_p` | 0.1-1.0 | 0.1 = +1% rápido | 0.1 = menos diverso |
| `keep_alive` | 5m, 10m | 10m = -5s si hay poca separación | N/A |

---

## Logs: qué buscar si es lento

### La fase `kickoff` toma >30s

**Diagnóstico:** Vision model o text model tardío.

Mira logs en `logs/nourish_bot.log`:

```
[CALL_OLLAMA_VISION] Enviando POST...
[CALL_OLLAMA_VISION] ✓ Respuesta recibida (523 chars, 15.42s)  ← 15 segundos = lento
```

**Fix:**
- Cambiar `vision_model = moondream` (tarda ~5s)
- O bajar `num_predict` de 500 a 200

### Muchos reloads de modelo (descarga/recarga)

Mira en logs:

```
[CALL_OLLAMA_VISION] ... llava:7b  ← Carga visión
[...tempo...]
[CALL_OLLAMA_TEXT] ... qwen:7b     ← Descarga llava, carga texto (+3-5s)
[...tempo...]
[CALL_OLLAMA_TEXT] ... qwen:7b     ← Ya en VRAM, rápido
```

**Fix:**
- Igualar modelos: `vision_model = text_model = moondream`
- O esperar a que `keep_alive` mantenga ambos (requiere >8GB VRAM)

### Conexión a Ollama lenta

Mira en logs:

```
[CALL_OLLAMA_VISION] Enviando POST a http://convergenciax02:11434/api/generate...
[...20+ segundos...]
[CALL_OLLAMA_VISION] ✓ Respuesta recibida (523 chars, 25.42s)
```

**Fix:**
- Cambiar `base_url = http://localhost:11434` si Ollama está aquí
- O aumentar `timeout = 300` si la red es lenta
- O usar modelo más rápido que depende menos de Ollama

---

## Logs detallados: salida esperada

Al ejecutar app.py:

```
================================================================================
2026-09-03 10:16:46 [INFO ] __main__ - === INICIANDO NOURISBHOT OLLAMA ===
================================================================================
2026-09-03 10:16:46 [DEBUG] __main__ - Python: 3.13.13 (main, Aug 29 2024, 10:08:00)
2026-09-03 10:16:46 [DEBUG] __main__ - Working directory: C:\workspace-vc\...
2026-09-03 10:16:46 [DEBUG] __main__ - Log file: logs\nourish_bot.log
2026-09-03 10:16:46 [INFO ] __main__ - Ollama config:
2026-09-03 10:16:46 [INFO ] __main__   - base_url: http://convergenciax02:11434
2026-09-03 10:16:46 [INFO ] __main__   - vision_model: llava:7b
2026-09-03 10:16:46 [INFO ] __main__   - text_model: qwen3:32b
2026-09-03 10:16:46 [INFO ] __main__   - timeout: 180s
2026-09-03 10:16:46 [INFO ] __main__   - keep_alive: 10m
2026-09-03 10:16:46 [INFO ] __main__   - temperature_vision: 0.1
2026-09-03 10:16:46 [INFO ] __main__   - temperature_text: 0.3
2026-09-03 10:16:47 [INFO ] __main__ - === CONSTRUYENDO UI GRADIO ===
2026-09-03 10:16:48 [INFO ] __main__ - Lanzando servidor Gradio en http://127.0.0.1:5010...

[Usuario sube imagen, hace clic Analyze]

2026-09-03 10:16:50 [INFO ] __main__ - ================================================================================
2026-09-03 10:16:50 [INFO ] __main__ - [ANALYZE_FOOD] Iniciando análisis - workflow: recipe, restricciones: 'vegan'
2026-09-03 10:16:50 [INFO ] __main__ - [ANALYZE_FOOD] Parámetros: vision_model=llava:7b, text_model=qwen3:32b
2026-09-03 10:16:50 [INFO ] __main__ - [ANALYZE_FOOD] Temperatura: vision=0.1, text=0.3
2026-09-03 10:16:50 [INFO ] __main__ - ================================================================================
2026-09-03 10:16:50 [INFO ] __main__ - [ANALYZE_FOOD] ✓ Imagen guardada (0.05s)
2026-09-03 10:16:51 [INFO ] __main__ - [ANALYZE_FOOD] ✓ NourishBotRecipeCrew instanciado
2026-09-03 10:16:51 [INFO ] src.crew - [NourishBotRecipeCrew.crew] ✓ Crew RECIPE construido exitosamente
2026-09-03 10:16:51 [INFO ] __main__ - [ANALYZE_FOOD] Ejecutando crew.kickoff() - esto puede tomar minutos...
[... CrewAI internals ...]
2026-09-03 10:16:52 [INFO ] src.tools - [CALL_OLLAMA_VISION] Iniciando llamada a http://convergenciax02:11434/api/generate con modelo llava:7b
2026-09-03 10:17:07 [INFO ] src.tools - [CALL_OLLAMA_VISION] ✓ Respuesta recibida (523 chars, 15.42s)
[... más processing ...]
2026-09-03 10:17:35 [INFO ] __main__ - [ANALYZE_FOOD] ✓ kickoff() completado (45.32s)
2026-09-03 10:17:35 [INFO ] __main__ - ================================================================================
2026-09-03 10:17:35 [INFO ] __main__ - [ANALYZE_FOOD] RESUMEN DE TIEMPOS:
2026-09-03 10:17:35 [INFO ] __main__   - format_output       :    0.05s (  0.1%)
2026-09-03 10:17:35 [INFO ] __main__   - get_crew_object     :    0.05s (  0.1%)
2026-09-03 10:17:35 [INFO ] __main__   - instantiate_crew    :    0.50s (  1.1%)
2026-09-03 10:17:35 [INFO ] __main__   - kickoff             :   45.32s ( 98.1%)
2026-09-03 10:17:35 [INFO ] __main__   - prepare_inputs      :    0.02s (  0.0%)
2026-09-03 10:17:35 [INFO ] __main__   - process_output      :    0.10s (  0.2%)
2026-09-03 10:17:35 [INFO ] __main__   - save_image          :    0.15s (  0.3%)
2026-09-03 10:17:35 [INFO ] __main__   - ────────────────────────────────
2026-09-03 10:17:35 [INFO ] __main__   - TOTAL               :   46.19s (100.0%)
2026-09-03 10:17:35 [INFO ] __main__ - ================================================================================
2026-09-03 10:17:35 [INFO ] __main__ - ✓ Benchmark guardado en logs\benchmark.log
2026-09-03 10:17:35 [INFO ] __main__ - [ANALYZE_FOOD] ✓ COMPLETADO EXITOSAMENTE
```

---

## Próximos pasos

1. **Ejecuta el app 3-5 veces con diferentes imágenes**
   ```powershell
   # Terminal 1: app corriendo
   C:\workspace-vc\env-llm-ia\Scripts\python.exe app.py
   
   # Terminal 2: sube imágenes en Gradio
   # http://127.0.0.1:5010
   ```

2. **Analiza los benchmarks**
   ```powershell
   python analyze_benchmark.py
   ```

3. **Identifica cuello de botella** (mira la fase con mayor %)

4. **Optimiza en config.ini** (reduce el modelo responsable)

5. **Repite 2-4 para medir mejora**

---

## Archivos

- **`logs/nourish_bot.log`** — Logs detallados, rotan automáticamente
- **`logs/benchmark.log`** — JSON Lines, una ejecución por línea
- **`analyze_benchmark.py`** — Script para analizar benchmarks
