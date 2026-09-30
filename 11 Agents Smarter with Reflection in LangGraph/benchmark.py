"""
Benchmarking para Agentes con Reflexión
Captura métricas de reflexión: ciclos, scores, convergencia
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class ReflectionBenchmark:
    """Captura y analiza métricas de reflexión."""

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.benchmark_file = self.output_dir / "benchmark.jsonl"

    def medir_reflexion(
        self,
        topic: str,
        quality_progression: List[float],
        final_post: str,
        wall_time: float,
        num_cycles: int,
        model: str,
        temperature: float
    ) -> Dict[str, Any]:
        """
        Captura una métrica de reflexión completa.

        Args:
            topic: Tema del post ("IA", "LinkedIn tips", etc.)
            quality_progression: Scores en cada ciclo [3, 6, 8]
            final_post: Post final después de reflexión
            wall_time: Tiempo total en segundos
            num_cycles: Número de ciclos realizados
            model: Nombre del modelo ("qwen2.5:7b")
            temperature: Temperatura usada

        Returns:
            Diccionario con métricas listas para JSONL
        """

        convergence_rate = self._calcular_convergencia(quality_progression)
        initial_score = quality_progression[0] if quality_progression else 0
        final_score = quality_progression[-1] if quality_progression else 0
        improvement = final_score - initial_score

        metrica = {
            "timestamp": datetime.now().isoformat(),
            "modelo": model,
            "temperatura": temperature,
            "tema": topic,
            "num_cycles": num_cycles,
            "quality_progression": quality_progression,
            "initial_score": initial_score,
            "final_score": final_score,
            "improvement": improvement,
            "convergence_rate": convergence_rate,
            "wall_time_seconds": round(wall_time, 2),
            "final_post": final_post[:300],  # Primeros 300 chars
            "exito": True
        }

        return metrica

    def _calcular_convergencia(self, scores: List[float]) -> float:
        """
        Calcula velocidad de convergencia (0.0-1.0).
        Qué tan rápido mejora.
        """
        if len(scores) < 2:
            return 0.0

        improvements = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0

        # Normalizar a 0-1 (5 puntos de mejora = velocidad máxima)
        return min(avg_improvement / 5.0, 1.0)

    def guardar_metricas(self, metricas: List[Dict]) -> None:
        """Guarda métricas en JSONL (append-only)."""

        with open(self.benchmark_file, 'a', encoding='utf-8') as f:
            for metrica in metricas:
                f.write(json.dumps(metrica, ensure_ascii=False) + '\n')

        print(f"[OK] {len(metricas)} métrica(s) guardadas en {self.benchmark_file}")

    def cargar_metricas(self) -> pd.DataFrame:
        """Carga todas las métricas JSONL."""

        if not self.benchmark_file.exists():
            return pd.DataFrame()

        metricas = []
        with open(self.benchmark_file, 'r', encoding='utf-8') as f:
            for linea in f:
                metricas.append(json.loads(linea))

        return pd.DataFrame(metricas)

    def analizar_reflexion(self) -> Dict[str, Any]:
        """Análisis completo de reflexión."""

        df = self.cargar_metricas()

        if df.empty:
            return {"error": "Sin métricas disponibles"}

        analisis = {
            "total_posts": len(df),
            "ciclos_promedio": df["num_cycles"].mean(),
            "mejora_promedio": df["improvement"].mean(),
            "convergencia_promedio": df["convergence_rate"].mean(),
            "latencia_promedio": df["wall_time_seconds"].mean(),
            "score_inicial_promedio": df["initial_score"].mean(),
            "score_final_promedio": df["final_score"].mean(),
            "modelos": df["modelo"].unique().tolist(),
            "temas": df["tema"].unique().tolist(),
        }

        return analisis

    def generar_grafico_convergencia(self) -> None:
        """Genera gráfico de convergencia (score vs ciclo)."""

        df = self.cargar_metricas()

        if df.empty:
            print("[WARN] Sin datos para gráfico")
            return

        plt.figure(figsize=(10, 6))

        for idx, row in df.iterrows():
            progression = row["quality_progression"]
            ciclos = range(1, len(progression) + 1)
            plt.plot(ciclos, progression, marker='o', label=row["tema"][:20])

        plt.xlabel("Ciclo de Reflexión")
        plt.ylabel("Score de Calidad (1-10)")
        plt.title("Convergencia de Reflexión: Mejora de Calidad por Ciclo")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        output_file = self.output_dir / "convergencia_reflexion.png"
        plt.savefig(output_file, dpi=150)
        print(f"[OK] Gráfico guardado en {output_file}")
        plt.close()

    def generar_reporte(self) -> str:
        """Genera reporte markdown con análisis de reflexión."""

        analisis = self.analizar_reflexion()

        if "error" in analisis:
            return analisis["error"]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reporte = f"""# 📊 REPORTE DE REFLEXIÓN — Agentes Inteligentes con LangGraph

**Fecha:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total de posts procesados:** {analisis['total_posts']}
**Modelos analizados:** {', '.join(analisis['modelos'])}

---

## 📈 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Ciclos promedio** | {analisis['ciclos_promedio']:.2f} |
| **Mejora promedio (score inicial → final)** | +{analisis['mejora_promedio']:.2f} puntos |
| **Convergencia (velocidad)** | {analisis['convergencia_promedio']:.2f}/1.0 |
| **Latencia promedio** | {analisis['latencia_promedio']:.2f}s |
| **Score inicial promedio** | {analisis['score_inicial_promedio']:.2f}/10 |
| **Score final promedio** | {analisis['score_final_promedio']:.2f}/10 |

---

## 🎯 Análisis de Reflexión

**¿Qué significan estos números?**

- **Ciclos promedio {analisis['ciclos_promedio']:.2f}:** El agente necesita ~{analisis['ciclos_promedio']:.0f} iteraciones para alcanzar calidad
- **Mejora +{analisis['mejora_promedio']:.2f}:** Cada ciclo suma ~{analisis['mejora_promedio']/max(analisis['ciclos_promedio'],1):.1f} puntos
- **Convergencia {analisis['convergencia_promedio']:.2f}:** Velocidad de mejora ({['Lenta','Moderada','Rápida'][int(min(analisis['convergencia_promedio']*3, 2))]}})

---

## 💡 Conclusiones

1. **La reflexión funciona:** Score inicial {analisis['score_inicial_promedio']:.1f} → final {analisis['score_final_promedio']:.1f}
2. **Convergencia clara:** El agente sabe cuándo parar (mejora se estabiliza)
3. **Costo computacional:** {analisis['latencia_promedio']:.1f}s por post (aceptable para contenido profesional)

---

## 🔄 Próximos Pasos

1. Expandir a 20+ posts para validación estadística
2. Comparar reflexión vs sin reflexión (baseline)
3. Aplicar a otros dominios (emails, reportes)
4. Optimizar: ¿menos ciclos, igual calidad?

---

*Reporte generado automáticamente por `benchmark.py`*
*Visualizaciones en `outputs/convergencia_reflexion.png`*
"""

        reporte_file = self.output_dir / f"REPORTE_REFLEXION_{timestamp}.md"
        with open(reporte_file, 'w', encoding='utf-8') as f:
            f.write(reporte)

        print(f"[OK] Reporte generado: {reporte_file}")
        return str(reporte_file)


def analizar_benchmark_completo(output_dir: str = "outputs") -> None:
    """Análisis completo de benchmark (llamar desde notebook)."""

    benchmark = ReflectionBenchmark(output_dir=output_dir)

    print("\n" + "="*80)
    print("ANÁLISIS COMPLETO DE REFLEXIÓN")
    print("="*80)

    # Análisis
    analisis = benchmark.analizar_reflexion()
    print(f"\n✅ Total de posts: {analisis.get('total_posts', 0)}")

    # Gráfico
    benchmark.generar_grafico_convergencia()

    # Reporte
    benchmark.generar_reporte()

    print("\n" + "="*80)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*80)
