"""
Herramientas (tools) que los agentes de CrewAI pueden invocar.

Diferencia clave frente al lab original (src/tools.py, que usaba
`ibm_watsonx_ai.ModelInference` para mandar la imagen a WatsonX):
aqui la imagen nunca sale de la maquina. `_call_ollama_vision` le manda la
imagen (en base64) al servidor Ollama local vía su API nativa `/api/generate`,
que es la que soporta el campo `images` para modelos multimodales (llava,
qwen2.5vl, etc.). Todo el trafico va a `base_url` (por defecto
http://localhost:11434), nunca a internet.

Cada Tool es una clase `BaseTool` de `crewai.tools` (el patron estandar de
CrewAI >=0.75): declara un `name`, una `description` (que el LLM del agente
lee para decidir cuando usarla) y un `args_schema` (Pydantic) que define los
argumentos que el agente debe pasarle.
"""

import os
import re
import json
import base64
import configparser
from typing import List, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

import logging
logger = logging.getLogger(__name__)

# --- Configuracion centralizada: ver config.ini en la raiz del proyecto ---
_CONFIG = configparser.ConfigParser()
_CONFIG.read(os.path.join(os.path.dirname(__file__), "..", "config.ini"))

OLLAMA_BASE_URL = _CONFIG.get("ollama", "base_url", fallback="http://localhost:11434")
VISION_MODEL = _CONFIG.get("ollama", "vision_model", fallback="llava:7b")
TEXT_MODEL = _CONFIG.get("ollama", "text_model", fallback="qwen2.5:7b-instruct-q4_K_M")
TEMPERATURE_VISION = _CONFIG.getfloat("ollama", "temperature_vision", fallback=0.1)
TEMPERATURE_TEXT = _CONFIG.getfloat("ollama", "temperature_text", fallback=0.3)
TIMEOUT = int(_CONFIG.get("ollama", "timeout", fallback="180"))
KEEP_ALIVE = _CONFIG.get("ollama", "keep_alive", fallback="10m")
TOP_P = _CONFIG.getfloat("ollama", "top_p", fallback=0.9)
NUM_PREDICT = int(_CONFIG.get("ollama", "num_predict", fallback="500"))

logger.info(f"[TOOLS.PY] Ollama config: {OLLAMA_BASE_URL}")
logger.info(f"[TOOLS.PY]   vision_model={VISION_MODEL} (temp={TEMPERATURE_VISION})")
logger.info(f"[TOOLS.PY]   text_model={TEXT_MODEL} (temp={TEMPERATURE_TEXT})")
logger.info(f"[TOOLS.PY]   timeout={TIMEOUT}s, keep_alive={KEEP_ALIVE}")


def _encode_image_base64(image_path: str) -> str:
    """Lee un archivo de imagen local y lo convierte a base64 (formato que espera la API de Ollama)."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _call_ollama_vision(image_path: str, prompt: str, model: str = VISION_MODEL) -> str:
    """
    Llama al endpoint nativo /api/generate de Ollama con una imagen adjunta.

    Se usa /api/generate (no el endpoint compatible con OpenAI /v1/chat/completions)
    porque en Ollama el soporte multimodal (campo `images`) esta expuesto de forma
    mas directa ahi. `stream=False` porque solo necesitamos la respuesta completa,
    no un stream token a token (esto es una llamada de herramienta, no un chat).
    """
    import time
    t_start = time.time()

    logger.info(f"[CALL_OLLAMA_VISION] Iniciando llamada a {OLLAMA_BASE_URL}/api/generate con modelo {model}")
    logger.debug(f"[CALL_OLLAMA_VISION] image_path={image_path}, prompt_len={len(prompt)}")

    try:
        logger.debug("[CALL_OLLAMA_VISION] Codificando imagen a base64...")
        encoded_image = _encode_image_base64(image_path)
        logger.debug(f"[CALL_OLLAMA_VISION] ✓ Imagen codificada ({len(encoded_image)} chars)")

        payload = {
            "model": model,
            "prompt": prompt,
            "images": [encoded_image],
            "stream": False,
            "options": {
                "temperature": TEMPERATURE_VISION,
                "top_p": TOP_P,
                "num_predict": NUM_PREDICT,
            },
            "keep_alive": KEEP_ALIVE,
        }

        logger.debug(f"[CALL_OLLAMA_VISION] Enviando POST a {OLLAMA_BASE_URL}/api/generate...")
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()

        result = resp.json().get("response", "").strip()
        elapsed = time.time() - t_start
        logger.info(f"[CALL_OLLAMA_VISION] ✓ Respuesta recibida ({len(result)} chars, {elapsed:.2f}s)")
        logger.debug(f"[CALL_OLLAMA_VISION] Response: {result[:200]}...")
        return result

    except requests.RequestException as e:
        elapsed = time.time() - t_start
        logger.error(f"[CALL_OLLAMA_VISION] ❌ ERROR de conexión tras {elapsed:.2f}s: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        elapsed = time.time() - t_start
        logger.error(f"[CALL_OLLAMA_VISION] ❌ ERROR tras {elapsed:.2f}s: {type(e).__name__}: {str(e)}", exc_info=True)
        raise


def _call_ollama_text(prompt: str, model: str = TEXT_MODEL) -> str:
    """Llamada de texto puro (sin imagen) al servidor Ollama local, para tareas de solo-razonamiento."""
    import time
    t_start = time.time()

    logger.info(f"[CALL_OLLAMA_TEXT] Iniciando llamada a {OLLAMA_BASE_URL}/api/generate con modelo {model}")
    logger.debug(f"[CALL_OLLAMA_TEXT] prompt_len={len(prompt)}")

    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": TEMPERATURE_TEXT,
                "top_p": TOP_P,
                "num_predict": NUM_PREDICT,
            },
            "keep_alive": KEEP_ALIVE,
        }

        logger.debug(f"[CALL_OLLAMA_TEXT] Enviando POST a {OLLAMA_BASE_URL}/api/generate...")
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=TIMEOUT)
        resp.raise_for_status()

        result = resp.json().get("response", "").strip()
        elapsed = time.time() - t_start
        logger.info(f"[CALL_OLLAMA_TEXT] ✓ Respuesta recibida ({len(result)} chars, {elapsed:.2f}s)")
        logger.debug(f"[CALL_OLLAMA_TEXT] Response: {result[:200]}...")
        return result

    except requests.RequestException as e:
        elapsed = time.time() - t_start
        logger.error(f"[CALL_OLLAMA_TEXT] ❌ ERROR de conexión tras {elapsed:.2f}s: {type(e).__name__}: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        elapsed = time.time() - t_start
        logger.error(f"[CALL_OLLAMA_TEXT] ❌ ERROR tras {elapsed:.2f}s: {type(e).__name__}: {str(e)}", exc_info=True)
        raise


def _extract_json_block(text: str) -> dict:
    """
    Los modelos locales a veces envuelven el JSON en texto o en ```json ... ```.
    Busca el primer bloque {...} balanceado y lo parsea; si falla, devuelve {}
    en vez de reventar el pipeline completo por un formateo imperfecto del modelo.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        logger.warning("No se pudo parsear JSON de la respuesta del modelo: %s", text[:200])
        return {}


# ---------------------------------------------------------------------------
# Tool 1: deteccion de ingredientes a partir de la imagen (vision model)
# ---------------------------------------------------------------------------

class ExtractIngredientsInput(BaseModel):
    image_path: str = Field(..., description="Ruta local al archivo de imagen de comida a analizar")


class ExtractIngredientsTool(BaseTool):
    name: str = "extract_ingredients"
    description: str = (
        "Analiza una imagen de comida y devuelve una lista de ingredientes visibles, "
        "uno por linea. Usa el modelo de vision local (Ollama)."
    )
    args_schema: Type[BaseModel] = ExtractIngredientsInput

    def _run(self, image_path: str) -> str:
        logger.info(f"[ExtractIngredientsTool._run] Iniciando con imagen: {image_path}")
        prompt = (
            "You are a food vision expert. List every distinct ingredient or food item "
            "visible in this image. Reply with ONLY a plain list, one ingredient per line, "
            "no numbering, no extra commentary."
        )
        logger.debug("[ExtractIngredientsTool._run] Llamando a Ollama vision...")
        raw = _call_ollama_vision(image_path, prompt)
        logger.info(f"[ExtractIngredientsTool._run] ✓ Ingredientes detectados:\n{raw}")
        return raw


# ---------------------------------------------------------------------------
# Tool 2: limpieza/normalizacion de la lista cruda de ingredientes
# ---------------------------------------------------------------------------

class FilterIngredientsInput(BaseModel):
    raw_ingredients: str = Field(..., description="Texto crudo devuelto por extract_ingredients")


class FilterIngredientsTool(BaseTool):
    name: str = "filter_ingredients"
    description: str = (
        "Limpia y normaliza una lista cruda de ingredientes (quita duplicados, numeracion, "
        "lineas vacias) y la devuelve como una lista JSON de strings."
    )
    args_schema: Type[BaseModel] = FilterIngredientsInput

    def _run(self, raw_ingredients: str) -> str:
        logger.info("[FilterIngredientsTool._run] Iniciando filtrado de ingredientes")
        logger.debug(f"[FilterIngredientsTool._run] Raw input:\n{raw_ingredients}")

        seen = set()
        cleaned: List[str] = []
        for line in raw_ingredients.splitlines():
            # Quita numeracion tipo "1. ", vinetas "- " o "* ", y espacios sobrantes.
            item = re.sub(r"^\s*[\d\-\*\.\)]+\s*", "", line).strip(" .").lower()
            if item and item not in seen:
                seen.add(item)
                cleaned.append(item)

        logger.info(f"[FilterIngredientsTool._run] ✓ {len(cleaned)} ingredientes después del filtrado")
        logger.debug(f"[FilterIngredientsTool._run] Ingredientes filtrados: {cleaned}")
        return json.dumps(cleaned)


# ---------------------------------------------------------------------------
# Tool 3: filtrado por restriccion dietetica (deterministico, sin LLM)
# ---------------------------------------------------------------------------

# Listas de exclusion por dieta. Es deliberadamente una regla fija (no una
# llamada al LLM): que "el pollo no es vegano" no depende de la opinion del
# modelo, es un hecho de dominio - conviene que sea determinista y testeable
# (ver principio de arquitectura de la skill ia-dev-fullstack) en vez de
# arriesgarse a que el LLM lo pase por alto en una corrida particular.
DIETARY_EXCLUSIONS = {
    "vegan": {
        "chicken", "beef", "pork", "bacon", "ham", "turkey", "fish", "salmon", "tuna",
        "shrimp", "egg", "eggs", "milk", "cheese", "butter", "honey", "yogurt", "cream",
        "gelatin", "mayonnaise",
    },
    "vegetarian": {
        "chicken", "beef", "pork", "bacon", "ham", "turkey", "fish", "salmon", "tuna",
        "shrimp", "gelatin",
    },
    "gluten-free": {
        "bread", "wheat", "pasta", "flour", "barley", "rye", "noodles", "soy sauce",
        "couscous", "crackers", "breadcrumbs",
    },
    "keto": {
        "rice", "bread", "pasta", "potato", "potatoes", "sugar", "corn", "beans",
        "oats", "flour", "banana", "honey",
    },
}


class DietaryFilterInput(BaseModel):
    ingredients_json: str = Field(..., description="Lista JSON de ingredientes (salida de filter_ingredients)")
    dietary_restrictions: str = Field("", description="Restriccion dietetica: vegan, vegetarian, gluten-free, keto, o vacio")


class DietaryFilterTool(BaseTool):
    name: str = "dietary_filter"
    description: str = (
        "Elimina de una lista de ingredientes aquellos incompatibles con una restriccion "
        "dietetica dada (vegan, vegetarian, gluten-free, keto). Si la restriccion esta vacia "
        "o no es reconocida, devuelve la lista sin cambios."
    )
    args_schema: Type[BaseModel] = DietaryFilterInput

    def _run(self, ingredients_json: str, dietary_restrictions: str = "") -> str:
        logger.info(f"[DietaryFilterTool._run] Iniciando filtrado por dieta: '{dietary_restrictions}'")
        logger.debug(f"[DietaryFilterTool._run] Raw ingredients JSON: {ingredients_json}")

        try:
            ingredients = json.loads(ingredients_json)
        except json.JSONDecodeError:
            logger.warning("[DietaryFilterTool._run] No se pudo parsear JSON, dividiendo por comas")
            ingredients = [i.strip() for i in ingredients_json.split(",") if i.strip()]

        diet_key = dietary_restrictions.strip().lower()
        excluded = DIETARY_EXCLUSIONS.get(diet_key, set())
        logger.debug(f"[DietaryFilterTool._run] Restricción '{diet_key}' excluye: {excluded}")

        filtered = [ing for ing in ingredients if ing.lower() not in excluded]
        logger.info(f"[DietaryFilterTool._run] ✓ {len(ingredients)} → {len(filtered)} ingredientes después del filtrado")
        logger.debug(f"[DietaryFilterTool._run] Ingredientes filtrados: {filtered}")
        return json.dumps(filtered)


# ---------------------------------------------------------------------------
# Tool 4: analisis nutricional (vision model + prompt orientado a JSON)
# ---------------------------------------------------------------------------

class NutrientAnalysisInput(BaseModel):
    image_path: str = Field(..., description="Ruta local al archivo de imagen del plato a analizar")


class NutrientAnalysisTool(BaseTool):
    name: str = "nutrient_analysis"
    description: str = (
        "Analiza una imagen de un plato completo y devuelve un JSON con nombre del plato, "
        "porcion estimada, calorias, macronutrientes (proteina, carbohidratos, grasas) y, "
        "si es posible, vitaminas y minerales relevantes."
    )
    args_schema: Type[BaseModel] = NutrientAnalysisInput

    def _run(self, image_path: str) -> str:
        logger.info(f"[NutrientAnalysisTool._run] Iniciando análisis nutricional: {image_path}")
        prompt = (
            "You are a nutrition expert analyzing a photo of a dish. "
            "Estimate its nutritional content and reply with ONLY a JSON object "
            "(no markdown, no commentary) matching exactly this shape:\n"
            "{\n"
            '  "dish": "short dish name",\n'
            '  "portion_size": "estimated portion, e.g. \'1 medium plate\'",\n'
            '  "estimated_calories": 450,\n'
            '  "nutrients": {\n'
            '    "protein": "20g",\n'
            '    "carbohydrates": "40g",\n'
            '    "fats": "15g",\n'
            '    "vitamins": [{"name": "Vitamin C", "percentage_dv": "10%"}],\n'
            '    "minerals": [{"name": "Iron", "amount": "2mg"}]\n'
            "  }\n"
            "}\n"
            "If you are unsure of an exact value, give your best reasonable estimate - never leave a field null."
        )

        logger.debug("[NutrientAnalysisTool._run] Llamando a Ollama vision...")
        raw = _call_ollama_vision(image_path, prompt)
        logger.debug("[NutrientAnalysisTool._run] Extrayendo JSON de respuesta...")
        data = _extract_json_block(raw)

        if not data:
            # Fallback minimo para que el pipeline no se caiga si el modelo no devolvio JSON valido.
            logger.warning("[NutrientAnalysisTool._run] ⚠ No se extrajo JSON válido, usando fallback")
            data = {"dish": "unknown", "nutrients": {}}
        else:
            logger.info(f"[NutrientAnalysisTool._run] ✓ JSON extraído - dish='{data.get('dish')}'")

        return json.dumps(data)
