#!/usr/bin/env python3
"""
Script para analizar benchmarks guardados en archivo JSON Lines.

Uso:
    python analyze_benchmark.py                    # Analizar logs/benchmark.log
    python analyze_benchmark.py --file custom.log  # Analizar otro archivo
    python analyze_benchmark.py --workflow recipe  # Filtrar por workflow
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any


def load_benchmarks(filepath: str) -> List[Dict[str, Any]]:
    """Carga benchmarks desde archivo JSON Lines."""
    benchmarks = []
    path = Path(filepath)

    if not path.exists():
        print(f"❌ Archivo no encontrado: {filepath}")
        return []

    try:
        with open(path, 'r') as f:
            for i, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                    benchmarks.append(entry)
                except json.JSONDecodeError as e:
                    print(f"⚠ Línea {i} inválida: {e}")
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        return []

    print(f"✓ Cargados {len(benchmarks)} benchmarks desde {filepath}\n")
    return benchmarks


def analyze_benchmarks(benchmarks: List[Dict], workflow_filter: str = None):
    """Analiza benchmarks y muestra estadísticas."""

    if not benchmarks:
        print("No hay benchmarks para analizar.")
        return

    # Filtrar por workflow si se especifica
    if workflow_filter:
        benchmarks = [b for b in benchmarks if b.get("workflow") == workflow_filter]
        if not benchmarks:
            print(f"❌ No hay benchmarks para workflow '{workflow_filter}'")
            return
        print(f"Filtrando por workflow: {workflow_filter}\n")

    # Agrupar por workflow
    by_workflow = defaultdict(list)
    for b in benchmarks:
        workflow = b.get("workflow", "unknown")
        by_workflow[workflow].append(b)

    # Analizar por workflow
    for workflow, entries in sorted(by_workflow.items()):
        print(f"\n{'=' * 80}")
        print(f"WORKFLOW: {workflow.upper()}")
        print(f"{'=' * 80}")

        # Estadísticas de tiempo total
        total_times = [e.get("total_time_seconds", 0) for e in entries]
        if total_times:
            print(f"\nTiempo Total (segundos):")
            print(f"  Min:     {min(total_times):7.2f}s")
            print(f"  Max:     {max(total_times):7.2f}s")
            print(f"  Promedio:{sum(total_times)/len(total_times):7.2f}s")
            print(f"  Corridas: {len(total_times)}")

        # Estadísticas por fase
        phase_stats = defaultdict(list)
        for entry in entries:
            phases = entry.get("phase_times", {})
            for phase, duration in phases.items():
                if phase != "total":
                    phase_stats[phase].append(duration)

        if phase_stats:
            print(f"\nTiempos por Fase:")
            for phase in sorted(phase_stats.keys()):
                times = phase_stats[phase]
                if times:
                    avg = sum(times) / len(times)
                    min_t = min(times)
                    max_t = max(times)
                    pct = (avg / (sum(total_times)/len(total_times))) * 100 if total_times else 0
                    print(f"  {phase:20s}: {avg:7.2f}s (min: {min_t:6.2f}s, max: {max_t:6.2f}s, {pct:5.1f}% del total)")

        # Últimas 5 ejecuciones detalladas
        print(f"\nÚltimas 5 ejecuciones:")
        for i, entry in enumerate(entries[-5:], 1):
            timestamp = entry.get("timestamp", "unknown")
            total = entry.get("total_time_seconds", 0)
            diet = entry.get("dietary_restrictions", "none")
            config = entry.get("config", {})

            print(f"\n  [{i}] {timestamp}")
            print(f"      Total: {total:.2f}s | Diet: {diet}")

            if config:
                print(f"      Config: vision={config.get('vision_model')} "
                      f"text={config.get('text_model')} "
                      f"temp_vis={config.get('temperature_vision')} "
                      f"temp_txt={config.get('temperature_text')}")

            phases = entry.get("phase_times", {})
            if phases:
                for phase in sorted(phases.keys()):
                    if phase != "total":
                        print(f"        - {phase}: {phases[phase]:.2f}s")

    print(f"\n{'=' * 80}")


def main():
    parser = argparse.ArgumentParser(
        description="Analizar benchmarks de NourishBot"
    )
    parser.add_argument(
        "--file",
        default="logs/benchmark.log",
        help="Archivo de benchmark a analizar (default: logs/benchmark.log)"
    )
    parser.add_argument(
        "--workflow",
        help="Filtrar por workflow (recipe o analysis)"
    )

    args = parser.parse_args()

    benchmarks = load_benchmarks(args.file)
    analyze_benchmarks(benchmarks, args.workflow)


if __name__ == "__main__":
    main()
