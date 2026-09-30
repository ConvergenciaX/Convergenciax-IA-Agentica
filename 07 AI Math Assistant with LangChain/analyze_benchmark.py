#!/usr/bin/env python3
"""
Analizador de Benchmarks — IA Agente - Tools y Math

Lee el archivo outputs/benchmark.jsonl (append-only JSONL con métricas de cada consulta)
y genera:
1. Tabla de resumen por variante (promedio/min/max de tiempos y tokens)
2. 3 gráficos PNG: latencia, tokens, throughput

Uso:
    python analyze_benchmark.py                    (lee outputs/benchmark.jsonl)
    python analyze_benchmark.py --file logs/benchmark.log (lee otro archivo)
    python analyze_benchmark.py --output-dir ./charts (guarda gráficos ahí)
"""

import argparse
import json
import os
from pathlib import Path
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def load_benchmarks(filepath):
    """Carga archivo JSONL de métricas."""
    benchmarks = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                benchmarks.append(record)
            except json.JSONDecodeError as e:
                print(f"[WARN] Línea {line_num} malformada: {e}")
    return benchmarks


def analyze_benchmarks(benchmarks, output_dir="outputs/charts"):
    """Analiza benchmarks agrupados por variante."""
    if not benchmarks:
        print("[ERROR] No hay registros de benchmarking.")
        return

    # Crear directorio de salida si no existe
    Path(output_dir).mkdir(exist_ok=True)

    # Filtrar solo exitosos para análisis estadístico
    successful = [b for b in benchmarks if b.get("exito", False)]

    if not successful:
        print("[ERROR] No hay benchmarks exitosos.")
        return

    # Agrupar por variante
    grouped = defaultdict(list)
    for b in successful:
        variant = b.get("variant_label", "unknown")
        grouped[variant].append(b)

    # Imprimir resumen
    print("\n" + "="*80)
    print("RESUMEN DE BENCHMARKS")
    print("="*80)

    summary_data = []
    for variant in sorted(grouped.keys()):
        records = grouped[variant]

        wall_times = [r.get("wall_time_seconds", 0) for r in records]
        inference_times = [r.get("llm_inference_seconds", 0) for r in records]
        total_tokens = [r.get("tokens_total", 0) for r in records]
        output_tokens = [r.get("tokens_salida", 0) for r in records]

        # Evitar división por cero
        throughputs = []
        for inf_time, out_tok in zip(inference_times, output_tokens):
            if inf_time > 0:
                throughputs.append(out_tok / inf_time)
            else:
                throughputs.append(0)

        summary_data.append({
            "Variante": variant,
            "Consultas": len(records),
            "Latencia Prom (s)": f"{np.mean(wall_times):.3f}",
            "Latencia Min (s)": f"{np.min(wall_times):.3f}",
            "Latencia Max (s)": f"{np.max(wall_times):.3f}",
            "Inferencia Prom (s)": f"{np.mean(inference_times):.3f}",
            "Tokens Prom": int(np.mean(total_tokens)),
            "Throughput Prom (tok/s)": f"{np.mean(throughputs):.1f}" if throughputs else "N/A"
        })

    # Mostrar tabla
    df_summary = pd.DataFrame(summary_data)
    print(df_summary.to_string(index=False))

    # Generar gráficos
    print(f"\nGenerando gráficos en: {output_dir}/")

    # Gráfico 1: Latencia promedio por variante
    fig, ax = plt.subplots(figsize=(10, 5))
    variants = list(grouped.keys())
    latencies = [np.mean([r.get("wall_time_seconds", 0) for r in grouped[v]]) for v in variants]

    ax.bar(range(len(variants)), latencies, color='steelblue', alpha=0.7)
    ax.set_xticks(range(len(variants)))
    ax.set_xticklabels(variants, rotation=45, ha='right')
    ax.set_ylabel('Latencia (segundos)')
    ax.set_title('Latencia Promedio por Variante')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "latency_by_variant.png"), dpi=100)
    print(f"[OK] {output_dir}/latency_by_variant.png")
    plt.close()

    # Gráfico 2: Tokens (entrada/salida apilado) por variante
    fig, ax = plt.subplots(figsize=(10, 5))
    input_tokens = [np.mean([r.get("tokens_entrada", 0) for r in grouped[v]]) for v in variants]
    output_tokens_avg = [np.mean([r.get("tokens_salida", 0) for r in grouped[v]]) for v in variants]

    width = 0.5
    ax.bar(range(len(variants)), input_tokens, width, label='Entrada', color='skyblue', alpha=0.7)
    ax.bar(range(len(variants)), output_tokens_avg, width, bottom=input_tokens, label='Salida', color='orange', alpha=0.7)
    ax.set_xticks(range(len(variants)))
    ax.set_xticklabels(variants, rotation=45, ha='right')
    ax.set_ylabel('Tokens')
    ax.set_title('Tokens Promedio por Variante (Apilado)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "tokens_by_variant.png"), dpi=100)
    print(f"[OK] {output_dir}/tokens_by_variant.png")
    plt.close()

    # Gráfico 3: Throughput (tokens/segundo)
    fig, ax = plt.subplots(figsize=(10, 5))
    throughputs_avg = []
    for v in variants:
        records = grouped[v]
        throughputs = []
        for r in records:
            inf_time = r.get("llm_inference_seconds", 0)
            out_tok = r.get("tokens_salida", 0)
            if inf_time > 0:
                throughputs.append(out_tok / inf_time)
        if throughputs:
            throughputs_avg.append(np.mean(throughputs))
        else:
            throughputs_avg.append(0)

    ax.bar(range(len(variants)), throughputs_avg, color='seagreen', alpha=0.7)
    ax.set_xticks(range(len(variants)))
    ax.set_xticklabels(variants, rotation=45, ha='right')
    ax.set_ylabel('Tokens por Segundo')
    ax.set_title('Throughput Promedio por Variante')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "throughput_by_variant.png"), dpi=100)
    print(f"[OK] {output_dir}/throughput_by_variant.png")
    plt.close()

    print("\n[OK] Análisis completado.")


def main():
    parser = argparse.ArgumentParser(description="Analiza benchmarks de IA Agente - Tools y Math")
    parser.add_argument("--file", default="outputs/benchmark.jsonl", help="Archivo JSONL de métricas")
    parser.add_argument("--output-dir", default="outputs/charts", help="Directorio para gráficos PNG")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[ERROR] Archivo no encontrado: {args.file}")
        return

    print(f"[INFO] Cargando benchmarks desde: {args.file}")
    benchmarks = load_benchmarks(args.file)
    print(f"[OK] {len(benchmarks)} registros cargados.")

    analyze_benchmarks(benchmarks, args.output_dir)


if __name__ == "__main__":
    main()
