"""
Esquemas Pydantic que fuerzan la salida estructurada de los agentes.

Por que existen: los modelos de lenguaje devuelven texto libre por defecto.
CrewAI permite pedirle a un Task que valide su salida contra un `output_pydantic`
(ver src/crew.py) - si el modelo no respeta el esquema, CrewAI reintenta
el parseo antes de devolver el resultado. Esto es lo que le permite a app.py
(la interfaz Gradio) leer campos como `.recipes` o `.nutrients` de forma
confiable en vez de tener que parsear texto libre con regex.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Recipe(BaseModel):
    """Una receta individual sugerida por el recipe_suggestion_agent."""
    title: str = Field(..., description="Nombre de la receta")
    ingredients: List[str] = Field(..., description="Ingredientes usados, ya filtrados por dieta")
    instructions: str = Field(..., description="Pasos de preparacion, en texto")
    calorie_estimate: int = Field(..., description="Calorias estimadas por porcion")


class RecipeSuggestionOutput(BaseModel):
    """Salida completa del flujo 'recipe': una lista de recetas propuestas."""
    recipes: List[Recipe] = Field(default_factory=list)


class Vitamin(BaseModel):
    name: str
    percentage_dv: str = Field(..., description="Porcentaje del valor diario recomendado, ej. '15%'")


class Mineral(BaseModel):
    name: str
    amount: str = Field(..., description="Cantidad estimada, ej. '2 mg'")


class Nutrients(BaseModel):
    """Desglose de macro y micronutrientes de un plato."""
    protein: Optional[str] = None
    carbohydrates: Optional[str] = None
    fats: Optional[str] = None
    vitamins: List[Vitamin] = Field(default_factory=list)
    minerals: List[Mineral] = Field(default_factory=list)


class NutrientAnalysisOutput(BaseModel):
    """Salida completa del flujo 'analysis': nutrientes + evaluacion de salud."""
    dish: Optional[str] = Field(None, description="Nombre o descripcion corta del plato detectado")
    portion_size: Optional[str] = Field(None, description="Tamano de porcion estimado, ej. '1 plato mediano'")
    estimated_calories: Optional[int] = None
    total_calories: Optional[int] = None
    nutrients: Nutrients = Field(default_factory=Nutrients)
    health_evaluation: Optional[str] = Field(
        None, description="Resumen en texto de que tan saludable es el plato y sugerencias de mejora"
    )
