"""
Definicion de los dos crews de NourishBot (Recetas y Analisis nutricional),
corriendo 100% sobre Ollama local en vez de IBM WatsonX.

Diferencia clave frente al lab original (carpeta hermana `NourishBot/src/crew.py`):
- El lab original creaba un `ibm_watsonx_ai.APIClient` apuntando a la nube de
  IBM y dejaba el `## TODO` de construir los Agents/Tasks sin resolver.
- Aqui cada Agent recibe un `crewai.LLM` que apunta al servidor Ollama local
  (`ollama/<modelo>` + `base_url`) - CrewAI usa LiteLLM por debajo, y LiteLLM
  sabe hablar con Ollama usando ese prefijo de proveedor. Ningun dato ni
  prompt sale de la maquina.
- Las herramientas de vision (ver src/tools.py) llaman aparte al
  modelo multimodal de Ollama; el LLM del Agent (modelo de texto) es quien
  decide CUANDO llamar a esas herramientas y como interpretar su resultado.

Flujo de cada crew (Process.sequential: cada Task corre en orden y puede leer
el resultado de las tareas anteriores via `context`):

  NourishBotRecipeCrew:
    ingredient_detection_task -> dietary_filtering_task -> recipe_suggestion_task

  NourishBotAnalysisCrew:
    ingredient_detection_task -> nutrient_analysis_task
"""

import os
import yaml
import configparser

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from src.tools import (
    ExtractIngredientsTool,
    FilterIngredientsTool,
    DietaryFilterTool,
    NutrientAnalysisTool,
)
from src.models import RecipeSuggestionOutput, NutrientAnalysisOutput

_CONFIG = configparser.ConfigParser()
_CONFIG.read(os.path.join(os.path.dirname(__file__), "..", "config.ini"))

OLLAMA_BASE_URL = _CONFIG.get("ollama", "base_url", fallback="http://localhost:11434")
TEXT_MODEL = _CONFIG.get("ollama", "text_model", fallback="qwen2.5:7b-instruct-q4_K_M")
TEMPERATURE = _CONFIG.getfloat("ollama", "temperature", fallback=0.2)

# Los agentes.yaml/tasks.yaml del lab original ya son genericos (no mencionan
# OpenAI ni WatsonX en ningun lado), asi que se reutilizan tal cual - solo
# cambia de donde viene el LLM que los ejecuta.
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")


def _build_ollama_llm() -> LLM:
    """
    Crea el LLM que usaran los Agents. El prefijo 'ollama/' le dice a LiteLLM
    (el router de proveedores que usa CrewAI por debajo) que hable el
    protocolo nativo de Ollama contra `base_url`, en vez de ir a OpenAI/Anthropic/etc.
    """
    return LLM(
        model=f"ollama/{TEXT_MODEL}",
        base_url=OLLAMA_BASE_URL,
        temperature=TEMPERATURE,
    )


@CrewBase
class BaseNourishBotCrew:
    """
    Clase base compartida por los dos crews: carga la configuracion de agentes
    y tareas una sola vez, y expone los 4 agentes + 4 tareas del dominio.
    Cada crew concreto (Recipe / Analysis) decide cuales de estos usar y en
    que Crew los combina (ver mas abajo).
    """

    agents_config_path = os.path.join(CONFIG_DIR, "agents.yaml")
    tasks_config_path = os.path.join(CONFIG_DIR, "tasks.yaml")

    def __init__(self, image_data: str, dietary_restrictions: str = None):
        self.image_data = image_data
        self.dietary_restrictions = dietary_restrictions or ""

        with open(self.agents_config_path, "r") as f:
            self.agents_config = yaml.safe_load(f)
        with open(self.tasks_config_path, "r") as f:
            self.tasks_config = yaml.safe_load(f)

        self.llm = _build_ollama_llm()

    # --- Agentes ---
    # Cada agent recibe solo las tools que necesita para su rol (principio de
    # menor privilegio: el agente de recetas, por ejemplo, no tiene acceso a
    # la tool de vision porque no le corresponde volver a mirar la imagen).

    @agent
    def ingredient_detection_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["ingredient_detection_agent"],
            tools=[ExtractIngredientsTool(), FilterIngredientsTool()],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def dietary_filtering_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["dietary_filtering_agent"],
            tools=[DietaryFilterTool()],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def nutrient_analysis_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["nutrient_analysis_agent"],
            tools=[NutrientAnalysisTool()],
            llm=self.llm,
            verbose=True,
        )

    @agent
    def recipe_suggestion_agent(self) -> Agent:
        # No necesita tools: razona en texto puro sobre la lista de
        # ingredientes ya filtrada que le llega via `context` de la tarea anterior.
        return Agent(
            config=self.agents_config["recipe_suggestion_agent"],
            llm=self.llm,
            verbose=True,
        )

    # --- Tareas ---
    # `context=[...]` es como CrewAI encadena tareas: le pasa al modelo el
    # resultado de la(s) tarea(s) listadas como contexto adicional del prompt.

    @task
    def ingredient_detection_task(self) -> Task:
        return Task(
            config=self.tasks_config["ingredient_detection_task"],
            agent=self.ingredient_detection_agent(),
        )

    @task
    def dietary_filtering_task(self) -> Task:
        return Task(
            config=self.tasks_config["dietary_filtering_task"],
            agent=self.dietary_filtering_agent(),
            context=[self.ingredient_detection_task()],
        )

    @task
    def nutrient_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["nutrient_analysis_task"],
            agent=self.nutrient_analysis_agent(),
            context=[self.ingredient_detection_task()],
            # output_pydantic obliga a CrewAI a validar/parsear la respuesta
            # final contra el esquema - es lo que permite a app.py leer
            # `.nutrients`, `.dish`, etc. de forma confiable.
            output_pydantic=NutrientAnalysisOutput,
        )

    @task
    def recipe_suggestion_task(self) -> Task:
        return Task(
            config=self.tasks_config["recipe_suggestion_task"],
            agent=self.recipe_suggestion_agent(),
            context=[self.dietary_filtering_task()],
            output_pydantic=RecipeSuggestionOutput,
        )


@CrewBase
class NourishBotRecipeCrew(BaseNourishBotCrew):
    """Flujo 'recipe': deteccion -> filtrado por dieta -> sugerencia de recetas."""

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.ingredient_detection_agent(),
                self.dietary_filtering_agent(),
                self.recipe_suggestion_agent(),
            ],
            tasks=[
                self.ingredient_detection_task(),
                self.dietary_filtering_task(),
                self.recipe_suggestion_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )


@CrewBase
class NourishBotAnalysisCrew(BaseNourishBotCrew):
    """Flujo 'analysis': deteccion -> analisis nutricional + evaluacion de salud."""

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.ingredient_detection_agent(),
                self.nutrient_analysis_agent(),
            ],
            tasks=[
                self.ingredient_detection_task(),
                self.nutrient_analysis_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )
