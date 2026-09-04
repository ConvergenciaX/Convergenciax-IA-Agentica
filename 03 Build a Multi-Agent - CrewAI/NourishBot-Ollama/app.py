import os
import sys
import time
import json
import logging
import configparser
from datetime import datetime
from logging.handlers import RotatingFileHandler

import gradio as gr

from src.crew import NourishBotRecipeCrew, NourishBotAnalysisCrew

# ============================================================================
# SETUP: Configuración de logging a STDOUT + ARCHIVO
# ============================================================================

_CONFIG = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), "config.ini")
_CONFIG.read(config_path)

# Crear directorio de logs si no existe
log_dir = _CONFIG.get("logging", "log_dir", fallback="logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, _CONFIG.get("logging", "log_file", fallback="nourish_bot.log"))
log_level_str = _CONFIG.get("logging", "level", fallback="DEBUG")
log_level = getattr(logging, log_level_str.upper(), logging.DEBUG)

# Formato log4j
log_format = '%(asctime)s [%(levelname)-5s] %(name)s - %(message)s'
log_formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

# Configurar logger raíz
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Handler: Stdout (terminal)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(log_formatter)
root_logger.addHandler(stdout_handler)

# Handler: Archivo con rotación
try:
    max_bytes = int(_CONFIG.get("logging", "log_max_size_mb", fallback="10")) * 1024 * 1024
    backup_count = int(_CONFIG.get("logging", "log_backup_count", fallback="5"))
    file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
except Exception as e:
    logging.warning(f"No se pudo configurar logging a archivo: {e}")

logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("=== INICIANDO NOURISBHOT OLLAMA ===")
logger.info("=" * 80)
logger.debug(f"Python: {sys.version}")
logger.debug(f"Working directory: {os.getcwd()}")
logger.debug(f"Log file: {log_file}")

# ============================================================================
# CARGAR CONFIGURACIÓN
# ============================================================================

UPLOADED_IMAGE_PATH = _CONFIG.get("datos", "uploaded_image_path", fallback="uploaded_image.jpg")

if _CONFIG.has_section('ollama'):
    base_url = _CONFIG.get('ollama', 'base_url', fallback='http://localhost:11434')
    vision_model = _CONFIG.get('ollama', 'vision_model', fallback='llava:7b')
    text_model = _CONFIG.get('ollama', 'text_model', fallback='qwen2.5:7b-instruct-q4_K_M')
    timeout = int(_CONFIG.get('ollama', 'timeout', fallback='180'))
    keep_alive = _CONFIG.get('ollama', 'keep_alive', fallback='10m')
    temperature_vision = float(_CONFIG.get('ollama', 'temperature_vision', fallback='0.1'))
    temperature_text = float(_CONFIG.get('ollama', 'temperature_text', fallback='0.3'))

    logger.info(f"Ollama config:")
    logger.info(f"  - base_url: {base_url}")
    logger.info(f"  - vision_model: {vision_model}")
    logger.info(f"  - text_model: {text_model}")
    logger.info(f"  - timeout: {timeout}s")
    logger.info(f"  - keep_alive: {keep_alive}")
    logger.info(f"  - temperature_vision: {temperature_vision}")
    logger.info(f"  - temperature_text: {temperature_text}")
else:
    logger.error("❌ No se encontró sección [ollama] en config.ini")
    temperature_vision = 0.1
    temperature_text = 0.3

# ============================================================================
# BENCHMARKING
# ============================================================================

BENCHMARK_ENABLED = _CONFIG.getboolean("benchmark", "enabled", fallback=True)
BENCHMARK_LOG_CONFIG = _CONFIG.getboolean("benchmark", "log_config", fallback=True)
BENCHMARK_JSON_FORMAT = _CONFIG.getboolean("benchmark", "json_format", fallback=True)
BENCHMARK_FILE = os.path.join(log_dir, _CONFIG.get("logging", "benchmark_file", fallback="benchmark.log"))

def log_benchmark(workflow_type: str, dietary_restrictions: str, total_time: float, phase_times: dict):
    """Registra tiempos de ejecución y parámetros en archivo de benchmark."""
    if not BENCHMARK_ENABLED:
        return

    try:
        timestamp = datetime.now().isoformat()

        if BENCHMARK_JSON_FORMAT:
            benchmark_entry = {
                "timestamp": timestamp,
                "workflow": workflow_type,
                "dietary_restrictions": dietary_restrictions,
                "total_time_seconds": round(total_time, 2),
                "phase_times": {k: round(v, 2) for k, v in phase_times.items()},
            }

            if BENCHMARK_LOG_CONFIG:
                benchmark_entry["config"] = {
                    "vision_model": vision_model,
                    "text_model": text_model,
                    "temperature_vision": temperature_vision,
                    "temperature_text": temperature_text,
                }

            with open(BENCHMARK_FILE, 'a') as f:
                f.write(json.dumps(benchmark_entry) + '\n')
        else:
            # Formato plain text
            config_str = ""
            if BENCHMARK_LOG_CONFIG:
                config_str = f" | vision={vision_model} text={text_model} temp={temperature_vision}/{temperature_text}"

            line = f"{timestamp} | {workflow_type} (diet={dietary_restrictions}) | total={total_time:.2f}s | phases={phase_times}{config_str}\n"
            with open(BENCHMARK_FILE, 'a') as f:
                f.write(line)

        logger.info(f"✓ Benchmark guardado en {BENCHMARK_FILE}")
    except Exception as e:
        logger.error(f"Error guardando benchmark: {e}")


def format_recipe_output(final_output: dict) -> str:
    """Convierte la salida (dict) del flujo 'recipe' en una tabla Markdown legible."""
    logger.debug("[FORMAT_RECIPE] Iniciando formateo de salida recipe")
    output = "## Recipe Ideas\n\n"
    recipes = final_output.get("recipes", [])
    logger.debug(f"[FORMAT_RECIPE] Cantidad de recetas en output: {len(recipes)}")

    if recipes:
        for idx, recipe in enumerate(recipes, 1):
            output += f"### {idx}. {recipe['title']}\n\n"
            output += "**Ingredients:**\n"
            output += "| Ingredient |\n|------------|\n"
            for ingredient in recipe["ingredients"]:
                output += f"| {ingredient} |\n"
            output += "\n"
            output += f"**Instructions:**\n{recipe['instructions']}\n\n"
            output += f"**Calorie Estimate:** {recipe['calorie_estimate']} kcal\n\n"
            output += "---\n\n"
    else:
        output += "No recipes could be generated."

    return output


def format_analysis_output(final_output: dict) -> str:
    """Convierte la salida (dict) del flujo 'analysis' en una tabla Markdown legible."""
    logger.debug("[FORMAT_ANALYSIS] Iniciando formateo de salida analysis")
    output = "## Nutritional Analysis\n\n"

    if dish := final_output.get("dish"):
        logger.debug(f"[FORMAT_ANALYSIS] Dish encontrado: {dish}")
        output += f"**Dish:** {dish}\n\n"
    if portion := final_output.get("portion_size"):
        output += f"**Portion Size:** {portion}\n\n"
    if est_cal := final_output.get("estimated_calories"):
        output += f"**Estimated Calories:** {est_cal} calories\n\n"

    output += "**Nutrient Breakdown:**\n\n"
    output += "| **Nutrient** | **Amount** |\n|--------------|------------|\n"

    nutrients = final_output.get("nutrients", {}) or {}
    for macro in ["protein", "carbohydrates", "fats"]:
        if value := nutrients.get(macro):
            output += f"| **{macro.capitalize()}** | {value} |\n"

    if vitamins := nutrients.get("vitamins", []):
        output += "\n**Vitamins:**\n\n| **Vitamin** | **%DV** |\n|-------------|--------|\n"
        for v in vitamins:
            output += f"| {v.get('name', 'N/A')} | {v.get('percentage_dv', 'N/A')} |\n"

    if minerals := nutrients.get("minerals", []):
        output += "\n**Minerals:**\n\n| **Mineral** | **Amount** |\n|-------------|-----------|\n"
        for m in minerals:
            output += f"| {m.get('name', 'N/A')} | {m.get('amount', 'N/A')} |\n"

    if health_eval := final_output.get("health_evaluation"):
        output += f"\n**Health Evaluation:**\n\n{health_eval}\n"

    return output


def analyze_food(image, dietary_restrictions, workflow_type, progress=gr.Progress(track_tqdm=True)):
    """
    Callback del boton 'Analyze'. Guarda la imagen subida localmente (nunca
    sale de la maquina), arma el crew correspondiente y ejecuta el pipeline
    de agentes de punta a punta contra el Ollama local.

    Mide tiempos de cada fase para benchmarking.
    """
    # ========================================================================
    # TIMING Y BENCHMARKING
    # ========================================================================
    t_start_total = time.time()
    phase_times = {}

    logger.info("=" * 80)
    logger.info(f"[ANALYZE_FOOD] Iniciando análisis - workflow: {workflow_type}, restricciones: '{dietary_restrictions}'")
    logger.info(f"[ANALYZE_FOOD] Parámetros: vision_model={vision_model}, text_model={text_model}")
    logger.info(f"[ANALYZE_FOOD] Temperatura: vision={temperature_vision}, text={temperature_text}")
    logger.info("=" * 80)

    try:
        # Fase 1: Guardar imagen
        t_phase = time.time()
        logger.debug(f"[ANALYZE_FOOD] Guardando imagen en: {UPLOADED_IMAGE_PATH}")
        image.save(UPLOADED_IMAGE_PATH)
        phase_times['save_image'] = time.time() - t_phase
        logger.info(f"[ANALYZE_FOOD] ✓ Imagen guardada ({phase_times['save_image']:.2f}s)")

        # Fase 2: Preparar inputs
        t_phase = time.time()
        inputs = {
            "uploaded_image": UPLOADED_IMAGE_PATH,
            "dietary_restrictions": dietary_restrictions,
            "workflow_type": workflow_type,
        }
        logger.debug(f"[ANALYZE_FOOD] Inputs preparados: {inputs}")
        phase_times['prepare_inputs'] = time.time() - t_phase

        # Fase 3: Instanciar crew
        t_phase = time.time()
        logger.info(f"[ANALYZE_FOOD] Instanciando crew: {workflow_type}")
        if workflow_type == "recipe":
            crew_instance = NourishBotRecipeCrew(
                image_data=UPLOADED_IMAGE_PATH,
                dietary_restrictions=dietary_restrictions,
            )
            logger.info("[ANALYZE_FOOD] ✓ NourishBotRecipeCrew instanciado")
        elif workflow_type == "analysis":
            crew_instance = NourishBotAnalysisCrew(image_data=UPLOADED_IMAGE_PATH)
            logger.info("[ANALYZE_FOOD] ✓ NourishBotAnalysisCrew instanciado")
        else:
            logger.error(f"[ANALYZE_FOOD] ❌ Workflow type inválido: {workflow_type}")
            return "Invalid workflow type. Choose 'recipe' or 'analysis'."
        phase_times['instantiate_crew'] = time.time() - t_phase
        logger.info(f"[ANALYZE_FOOD] Crew instantiation: {phase_times['instantiate_crew']:.2f}s")

        # Fase 4: Obtener crew object
        t_phase = time.time()
        logger.info("[ANALYZE_FOOD] Obteniendo crew object")
        crew_obj = crew_instance.crew()
        logger.debug(f"[ANALYZE_FOOD] Crew object: {crew_obj}")
        phase_times['get_crew_object'] = time.time() - t_phase

        # Fase 5: KICKOFF (operación principal)
        t_phase = time.time()
        logger.info("[ANALYZE_FOOD] Ejecutando crew.kickoff() - esto puede tomar minutos...")
        final_output = crew_obj.kickoff(inputs=inputs)
        phase_times['kickoff'] = time.time() - t_phase
        logger.info(f"[ANALYZE_FOOD] ✓ kickoff() completado ({phase_times['kickoff']:.2f}s)")

        # Fase 6: Procesar output
        t_phase = time.time()
        logger.debug(f"[ANALYZE_FOOD] Output raw type: {type(final_output)}")
        final_output = final_output.to_dict()
        logger.info(f"[ANALYZE_FOOD] ✓ Output convertido a dict - keys: {final_output.keys()}")
        phase_times['process_output'] = time.time() - t_phase

        # Fase 7: Formatear resultado
        t_phase = time.time()
        if workflow_type == "recipe":
            logger.info("[ANALYZE_FOOD] Formateando salida como recipe")
            result = format_recipe_output(final_output)
        else:
            logger.info("[ANALYZE_FOOD] Formateando salida como analysis")
            result = format_analysis_output(final_output)
        phase_times['format_output'] = time.time() - t_phase

        # ====================================================================
        # RESUMEN Y BENCHMARK
        # ====================================================================
        total_time = time.time() - t_start_total
        phase_times['total'] = total_time

        logger.info("=" * 80)
        logger.info("[ANALYZE_FOOD] RESUMEN DE TIEMPOS:")
        for phase, duration in sorted(phase_times.items()):
            pct = (duration / total_time * 100) if total_time > 0 else 0
            logger.info(f"  - {phase:20s}: {duration:7.2f}s ({pct:5.1f}%)")
        logger.info(f"  {'─' * 40}")
        logger.info(f"  {'TOTAL':20s}: {total_time:7.2f}s (100.0%)")
        logger.info("=" * 80)

        # Guardar en archivo de benchmark
        log_benchmark(workflow_type, dietary_restrictions, total_time, phase_times)

        logger.info("[ANALYZE_FOOD] ✓ COMPLETADO EXITOSAMENTE")
        return result

    except Exception as e:
        total_time = time.time() - t_start_total
        logger.error(f"[ANALYZE_FOOD] ❌ ERROR tras {total_time:.2f}s: {type(e).__name__}: {str(e)}", exc_info=True)

        # Registrar error en benchmark también
        phase_times['error'] = total_time
        log_benchmark(workflow_type, dietary_restrictions, total_time, phase_times)

        return f"Error durante el análisis: {type(e).__name__}: {str(e)}"


css = """
.title { font-size: 1.5em !important; text-align: center !important; color: #FFD700; }
.text { text-align: center; }
"""

with gr.Blocks(theme=gr.themes.Citrus(), css=css) as demo:
    gr.Markdown("# NourishBot (100% local - Ollama)", elem_classes="title")
    gr.Markdown(
        "Sube una imagen de comida, indica una restriccion dietetica (opcional) y elige "
        "un flujo: 'recipe' para ideas de recetas, 'analysis' para info nutricional. "
        "Todo el procesamiento corre en tu propia GPU via Ollama - la imagen nunca sale de esta maquina.",
        elem_classes="text",
    )

    with gr.Row():
        with gr.Column(scale=1, min_width=400):
            gr.Markdown("## Inputs", elem_classes="title")
            image_input = gr.Image(type="pil", label="Upload Image")
            dietary_input = gr.Textbox(label="Dietary Restrictions (optional)", placeholder="e.g., vegan")
            workflow_radio = gr.Radio(["recipe", "analysis"], label="Workflow Type", value="analysis")
            submit_btn = gr.Button("Analyze")

        with gr.Column(scale=2, min_width=600):
            gr.Examples(
                examples=[
                    ["examples/food-1.jpg", "vegan", "recipe"],
                    ["examples/food-2.jpg", "", "analysis"],
                    ["examples/food-3.jpg", "keto", "recipe"],
                    ["examples/food-4.jpg", "", "analysis"],
                ],
                inputs=[image_input, dietary_input, workflow_radio],
                label="Try an Example",
            )
            gr.Markdown("## Results will appear here...", elem_classes="title")
            result_display = gr.Markdown(
                "<div style='border: 1px solid #ccc; padding: 1rem; text-align: center; color: #666;'>No results yet</div>",
                height=500,
            )

    submit_btn.click(
        fn=analyze_food,
        inputs=[image_input, dietary_input, workflow_radio],
        outputs=result_display,
    )

if __name__ == "__main__":
    logger.info("=== CONSTRUYENDO UI GRADIO ===")
    # Puerto distinto al de app.py (5000) para poder correr ambas versiones a la vez.
    try:
        logger.info("Lanzando servidor Gradio en http://127.0.0.1:5010...")
        demo.launch(server_name="127.0.0.1", server_port=5010, show_error=True)
    except KeyboardInterrupt:
        logger.info("Servidor detenido por usuario (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ ERROR al lanzar servidor: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
