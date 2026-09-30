"""
analyze_benchmark.py — Análisis Post-Hoc de Benchmark

Script para ejecutar análisis completo después de correr el notebook.
Genera gráficos, tabla comparativa y reporte markdown.

Uso:
    python analyze_benchmark.py
"""

from benchmark import (
    cargar_benchmark_jsonl,
    generar_graficos_comparativos,
    generar_reporte_markdown,
    analizar_benchmark_completo
)
import os

if __name__ == "__main__":
    output_dir = "outputs"

    # Ejecutar análisis completo
    analizar_benchmark_completo(output_dir)

    print("\n✅ Análisis completado.")
    print(f"Resultados en: {os.path.abspath(output_dir)}/")
