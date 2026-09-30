"""
benchmark.py — Captura, Persistencia, Evaluación y Análisis de ReAct Agents

Este módulo centraliza toda la lógica de medición de rendimiento y evaluación.
El notebook IMPORTA estas funciones, nunca las define inline.

Funcionalidad:
1. CAPTURA: medir_y_registrar() — Extrae métricas durante ejecución
2. PERSISTENCIA: guardar_metricas() — Guarda a JSONL append-only
3. EVALUACIÓN: evaluar_exactitud(), evaluar_razonamiento() — Calidad
4. ANÁLISIS: generar_graficos_comparativos(), analizar_benchmark_completo() — Comparación

Autor: Claude (IA) + Usuario
Versión: 1.0 (Python 3.14, LangChain + LangGraph)
"""

import time
from datetime import datetime
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List

# Configuración visual
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


def medir_y_registrar(
    agent_result: Dict[str, Any],
    wall_time: float,
    model_name: str,
    temperature: float,
    variant_label: str,
    consulta: str
) -> Dict[str, Any]:
    """
    Extrae métricas de la ejecución del agente ReAct.

    Args:
        agent_result: Resultado del agente (contiene state, intermediate_steps)
        wall_time: Tiempo transcurrido en segundos
        model_name: Nombre del modelo Ollama
        temperature: Temperatura de inferencia
        variant_label: Etiqueta de variante
        consulta: Consulta original del usuario

    Returns:
        dict: Métrica con todas las dimensiones
    """
    try:
        # Extraer información de intermediate_steps (ReAct trace)
        intermediate_steps = agent_result.get("intermediate_steps", [])
        num_steps = len(intermediate_steps)

        # Extraer reasoning_steps si está en state (LangGraph)
        reasoning_steps = agent_result.get("reasoning_steps", [])
        num_reasoning_steps = len(reasoning_steps)

        # Respuesta final
        respuesta = agent_result.get("output", "")

        # Conteo de tools usadas
        tools_usadas = set()
        for step in intermediate_steps:
            if isinstance(step, tuple) and len(step) > 0:
                action = step[0]
                if hasattr(action, 'tool'):
                    tools_usadas.add(action.tool)

        metrica = {
            "timestamp": datetime.now().isoformat(),
            "modelo": model_name,
            "temperatura": temperature,
            "variant_label": variant_label,
            "consulta": consulta[:100],  # Primeros 100 caracteres
            "respuesta": respuesta[:200],  # Primeros 200 caracteres
            "wall_time_seconds": round(wall_time, 3),
            "num_steps": num_steps,
            "num_reasoning_steps": num_reasoning_steps,
            "tools_usadas": list(tools_usadas),
            "num_tools": len(tools_usadas),
            "exito": True,
            "error": None
        }

        return metrica

    except Exception as e:
        print(f"[ERROR] Error en medir_y_registrar: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "modelo": model_name,
            "temperatura": temperature,
            "variant_label": variant_label,
            "consulta": consulta[:100],
            "wall_time_seconds": round(wall_time, 3),
            "exito": False,
            "error": str(e)[:200]
        }


def guardar_metricas(metricas: List[Dict], output_dir: str = "outputs", enabled: bool = True) -> None:
    """
    Guarda métricas en JSONL append-only.

    Args:
        metricas: Lista de métricas a guardar
        output_dir: Directorio de salida
        enabled: Si False, no guarda (útil para desactivar en desarrollo)
    """
    if not enabled or not metricas:
        return

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "benchmark.jsonl")

    try:
        with open(output_file, 'a', encoding='utf-8') as f:
            for metrica in metricas:
                f.write(json.dumps(metrica, ensure_ascii=False) + "\n")

        print(f"[OK] {len(metricas)} métrica(s) anexada(s) a: {output_file}")
    except Exception as e:
        print(f"[ERROR] Error guardando métricas: {e}")


def evaluar_exactitud(respuesta: str, respuesta_esperada: str) -> float:
    """
    Evalúa exactitud de la respuesta comparando con la esperada.

    Estrategia simple: búsqueda de palabras clave en la respuesta.

    Args:
        respuesta: Respuesta del agente
        respuesta_esperada: Respuesta esperada (cadena o lista de palabras clave)

    Returns:
        float: Exactitud 0.0-1.0
    """
    if not respuesta or not respuesta_esperada:
        return 0.0

    respuesta_lower = respuesta.lower()
    esperada_lower = respuesta_esperada.lower()

    # Si es una cadena simple, buscar coincidencia parcial
    if isinstance(respuesta_esperada, str):
        if respuesta_lower == esperada_lower:
            return 1.0
        elif esperada_lower in respuesta_lower:
            return 0.8
        else:
            return 0.0

    return 0.0


def evaluar_razonamiento(reasoning_steps: List[Dict]) -> Dict[str, Any]:
    """
    Evalúa la calidad del razonamiento (número de pasos, uso de tools, etc.).

    Args:
        reasoning_steps: Pasos de razonamiento del agente

    Returns:
        dict: Métricas de razonamiento
    """
    if not reasoning_steps:
        return {
            "num_pasos": 0,
            "pasos_promedio": 0,
            "tiene_razonamiento": False
        }

    return {
        "num_pasos": len(reasoning_steps),
        "pasos_promedio": len(reasoning_steps),
        "tiene_razonamiento": len(reasoning_steps) > 0
    }


def cargar_benchmark_jsonl(archivo: str) -> pd.DataFrame:
    """
    Carga datos de benchmark desde JSONL.

    Args:
        archivo: Ruta del archivo JSONL

    Returns:
        pd.DataFrame: DataFrame con métricas
    """
    if not os.path.exists(archivo):
        print(f"[WARN] Archivo no encontrado: {archivo}")
        return pd.DataFrame()

    try:
        df = pd.read_json(archivo, lines=True)
        print(f"[OK] {len(df)} registros cargados desde {archivo}")
        return df
    except Exception as e:
        print(f"[ERROR] Error cargando {archivo}: {e}")
        return pd.DataFrame()


def generar_graficos_comparativos(df: pd.DataFrame, output_dir: str = "outputs") -> Dict[str, str]:
    """
    Genera gráficos comparativos de rendimiento entre modelos.

    Args:
        df: DataFrame de benchmark
        output_dir: Directorio de salida

    Returns:
        dict: Rutas de archivos generados
    """
    os.makedirs(output_dir, exist_ok=True)
    archivos = {}

    df_ok = df[df['exito'] == True]
    if len(df_ok) == 0:
        print("[WARN] No hay datos exitosos para gráficos")
        return {}

    modelos = df_ok['modelo'].unique()

    # Gráfico 1: Latencia por modelo
    if 'wall_time_seconds' in df_ok.columns and len(modelos) > 0:
        fig, ax = plt.subplots(figsize=(12, 6))

        if len(modelos) == 1:
            # Para un solo modelo, hacer un gráfico de puntos en lugar de boxplot
            m = modelos[0]
            latencias = df_ok[df_ok['modelo'] == m]['wall_time_seconds'].values
            ax.scatter(range(len(latencias)), latencias, s=120, alpha=0.6, color='lightblue', edgecolors='black', linewidth=1)
            ax.set_ylabel('Latencia (segundos)', fontsize=12, fontweight='bold')
            ax.set_xlabel('Consulta #', fontsize=12, fontweight='bold')
            ax.set_title(f'Latencia por Consulta — {m}', fontsize=14, fontweight='bold')
        else:
            # Para múltiples modelos, usar boxplot
            datos_latencia = [df_ok[df_ok['modelo'] == m]['wall_time_seconds'].values for m in modelos]
            bp = ax.boxplot(datos_latencia, labels=modelos, patch_artist=True)
            for patch in bp['boxes']:
                patch.set_facecolor('lightblue')
            ax.set_ylabel('Latencia (segundos)', fontsize=12, fontweight='bold')
            ax.set_xlabel('Modelo', fontsize=12, fontweight='bold')
            ax.set_title('Comparación de Latencia por Modelo', fontsize=14, fontweight='bold')

        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        path1 = os.path.join(output_dir, "01_comparacion_latencia.png")
        plt.savefig(path1, dpi=100, bbox_inches='tight')
        plt.close()
        archivos['latencia'] = path1
        print(f"[OK] Gráfico 1/3 — Latencia: {path1}")

    # Gráfico 2: Pasos de razonamiento por modelo
    if 'num_steps' in df_ok.columns and len(modelos) > 0:
        fig, ax = plt.subplots(figsize=(12, 6))

        if len(modelos) == 1:
            # Para un solo modelo, hacer un gráfico de barras en lugar de boxplot
            m = modelos[0]
            pasos = df_ok[df_ok['modelo'] == m]['num_steps'].values
            ax.bar(range(len(pasos)), pasos, alpha=0.6, color='lightgreen', edgecolor='black', linewidth=1)
            ax.set_ylabel('Número de Pasos ReAct', fontsize=12, fontweight='bold')
            ax.set_xlabel('Consulta #', fontsize=12, fontweight='bold')
            ax.set_title(f'Pasos ReAct por Consulta — {m}', fontsize=14, fontweight='bold')
        else:
            # Para múltiples modelos, usar boxplot
            datos_pasos = [df_ok[df_ok['modelo'] == m]['num_steps'].values for m in modelos]
            bp = ax.boxplot(datos_pasos, labels=modelos, patch_artist=True)
            for patch in bp['boxes']:
                patch.set_facecolor('lightgreen')
            ax.set_ylabel('Número de Pasos ReAct', fontsize=12, fontweight='bold')
            ax.set_xlabel('Modelo', fontsize=12, fontweight='bold')
            ax.set_title('Comparación de Pasos de Razonamiento', fontsize=14, fontweight='bold')

        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        path2 = os.path.join(output_dir, "02_comparacion_pasos.png")
        plt.savefig(path2, dpi=100, bbox_inches='tight')
        plt.close()
        archivos['pasos'] = path2
        print(f"[OK] Gráfico 2/3 — Pasos: {path2}")

    # Gráfico 3: Trade-off Latencia vs Pasos
    if 'wall_time_seconds' in df_ok.columns and 'num_steps' in df_ok.columns:
        fig, ax = plt.subplots(figsize=(12, 8))

        colores_mapa = {
            'qwen2.5:7b': '#1f77b4',
            'llama3.1:8b-instruct-q2_K': '#ff7f0e',
            'mistral:7b': '#2ca02c'
        }

        for modelo in modelos:
            df_modelo = df_ok[df_ok['modelo'] == modelo]
            color = colores_mapa.get(modelo, '#d62728')
            ax.scatter(df_modelo['wall_time_seconds'], df_modelo['num_steps'],
                      label=modelo, s=120, alpha=0.6, color=color, edgecolors='black', linewidth=1)

        ax.set_xlabel('Latencia (segundos)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Pasos de Razonamiento', fontsize=12, fontweight='bold')
        ax.set_title('Trade-off: Latencia vs Pasos ReAct', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10, loc='best')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        path3 = os.path.join(output_dir, "03_tradeoff_latencia_pasos.png")
        plt.savefig(path3, dpi=100, bbox_inches='tight')
        plt.close()
        archivos['tradeoff'] = path3
        print(f"[OK] Gráfico 3/3 — Trade-off: {path3}")

    print(f"[OK] ✅ {len(archivos)} gráficos generados\n")
    return archivos


def generar_reporte_markdown(df: pd.DataFrame, output_file: str = None) -> None:
    """
    Genera reporte completo en Markdown con análisis de ReAct.

    Args:
        df: DataFrame de benchmark
        output_file: Archivo markdown de salida (si None, auto-genera con timestamp)
    """
    try:
        # Generar nombre con timestamp si no se proporciona
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/REPORTE_REACT_{timestamp}.md"

        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        df_ok = df[df['exito'] == True]
        if len(df_ok) == 0:
            print("[WARN] No hay datos exitosos para reporte")
            return

        # Generar contenido del reporte
        reporte = f"""# 📊 REPORTE DE REASONING AND ACTING — Análisis de Agente ReAct

**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total de consultas:** {len(df)} (exitosas: {len(df_ok)})
**Modelos analizados:** {', '.join(df_ok['modelo'].unique())}

---

## 📈 Resumen Ejecutivo

Este reporte analiza el rendimiento del agente ReAct (Reasoning + Acting) ejecutado en diferentes modelos Ollama.

**Dimensiones clave:**
- **Latencia**: Tiempo total de ejecución (en segundos)
- **Pasos ReAct**: Número de ciclos Thought→Action→Observation
- **Tools usadas**: Herramientas invocadas por consulta

---

## 📊 Métricas por Modelo

"""

        # Tabla de estadísticas por modelo
        reporte += "| Modelo | Consultas | Latencia (s) | Mín | Máx | Pasos | Tools |\n"
        reporte += "|--------|-----------|--------------|-----|-----|-------|-------|\n"

        for modelo in df_ok['modelo'].unique():
            df_modelo = df_ok[df_ok['modelo'] == modelo]
            lat_mean = df_modelo['wall_time_seconds'].mean()
            lat_min = df_modelo['wall_time_seconds'].min()
            lat_max = df_modelo['wall_time_seconds'].max()
            steps_mean = df_modelo['num_steps'].mean() if 'num_steps' in df_modelo.columns else 0
            tools_mean = df_modelo['num_tools'].mean() if 'num_tools' in df_modelo.columns else 0

            reporte += f"| {modelo} | {len(df_modelo)} | {lat_mean:.3f} | {lat_min:.3f} | {lat_max:.3f} | {steps_mean:.1f} | {tools_mean:.1f} |\n"

        reporte += "\n---\n\n## 🎯 Análisis de Razonamiento (ReAct)\n\n"

        if 'num_steps' in df_ok.columns:
            steps_stats = df_ok['num_steps'].describe()
            reporte += f"""
**Distribución de pasos ReAct:**
- Promedio: {steps_stats['mean']:.2f} pasos
- Mínimo: {int(steps_stats['min'])} pasos
- Máximo: {int(steps_stats['max'])} pasos
- Mediana: {df_ok['num_steps'].median():.1f} pasos

*Interpretación:* Más pasos = más razonamiento, pero mayor latencia. Busca balance.
"""

        reporte += "\n---\n\n## 📝 Recomendaciones\n\n"
        reporte += "1. **Balance latencia-razonamiento**: Evalúa si más pasos mejoran exactitud\n"
        reporte += "2. **Selección de modelo**: Compara latencia vs calidad de respuestas\n"
        reporte += "3. **Optimización de tools**: Algunas tools son más costosas que otras\n"

        reporte += f"\n---\n\n*Reporte generado: {datetime.now().isoformat()}*\n"

        # Guardar reporte
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(reporte)

        print(f"[OK] Reporte Markdown generado: {output_file}")

    except Exception as e:
        print(f"[ERROR] Error generando reporte: {e}")
        import traceback
        traceback.print_exc()


def analizar_benchmark_completo(output_dir: str = "outputs") -> None:
    """
    Ejecuta análisis completo: gráficos + tabla + reporte markdown.
    """
    print("█" * 120)
    print("█ ANÁLISIS COMPLETO DE BENCHMARK — ReAct Agent")
    print("█" * 120 + "\n")

    # Cargar datos
    archivo_json = os.path.join(output_dir, "benchmark.jsonl")
    df = cargar_benchmark_jsonl(archivo_json)

    if len(df) == 0:
        print("[WARN] No hay datos de benchmark para analizar")
        return

    # Generar gráficos
    generar_graficos_comparativos(df, output_dir)

    # Generar reporte markdown con timestamp
    generar_reporte_markdown(df)

    print("█" * 120)
    print("█ ✅ ANÁLISIS COMPLETADO")
    print("█" * 120 + "\n")


if __name__ == "__main__":
    # Script para ejecutar análisis manualmente
    print("Análisis de Benchmark — ReAct Agent")
    analizar_benchmark_completo()
