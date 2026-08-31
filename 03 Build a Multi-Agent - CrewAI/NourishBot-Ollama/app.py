"""
Interfaz Gradio para NourishBot, version 100% local sobre Ollama.

Mismo formato de salida que el `app.py` del lab original (carpeta hermana
`NourishBot/`), pero apuntando a `src.crew` de este proyecto (que usa Ollama)
y en un puerto distinto (5010) para poder correr ambas apps a la vez sin
choque de puertos. La logica de formateo de Markdown no depende de si el LLM
es de OpenAI/WatsonX o de Ollama, solo del esquema Pydantic de salida
(`src/models.py`).
"""

import os
import configparser

import gradio as gr

from src.crew import NourishBotRecipeCrew, NourishBotAnalysisCrew

_CONFIG = configparser.ConfigParser()
_CONFIG.read(os.path.join(os.path.dirname(__file__), "config.ini"))
UPLOADED_IMAGE_PATH = _CONFIG.get("datos", "uploaded_image_path", fallback="uploaded_image.jpg")


def format_recipe_output(final_output: dict) -> str:
    """Convierte la salida (dict) del flujo 'recipe' en una tabla Markdown legible."""
    output = "## Recipe Ideas\n\n"
    recipes = final_output.get("recipes", [])

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
    output = "## Nutritional Analysis\n\n"

    if dish := final_output.get("dish"):
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
    """
    image.save(UPLOADED_IMAGE_PATH)

    inputs = {
        "uploaded_image": UPLOADED_IMAGE_PATH,
        "dietary_restrictions": dietary_restrictions,
        "workflow_type": workflow_type,
    }

    if workflow_type == "recipe":
        crew_instance = NourishBotRecipeCrew(
            image_data=UPLOADED_IMAGE_PATH,
            dietary_restrictions=dietary_restrictions,
        )
    elif workflow_type == "analysis":
        crew_instance = NourishBotAnalysisCrew(image_data=UPLOADED_IMAGE_PATH)
    else:
        return "Invalid workflow type. Choose 'recipe' or 'analysis'."

    crew_obj = crew_instance.crew()
    final_output = crew_obj.kickoff(inputs=inputs)
    final_output = final_output.to_dict()

    if workflow_type == "recipe":
        return format_recipe_output(final_output)
    return format_analysis_output(final_output)


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
    # Puerto distinto al de app.py (5000) para poder correr ambas versiones a la vez.
    demo.launch(server_name="127.0.0.1", server_port=5010)
