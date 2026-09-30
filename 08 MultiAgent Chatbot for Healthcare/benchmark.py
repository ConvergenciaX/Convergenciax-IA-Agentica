"""
benchmark.py — Instrumentación, Persistencia, Evaluación y Análisis de AutoMed v2

Este módulo centraliza toda la lógica de medición de rendimiento y evaluación.
El notebook IMPORTA estas funciones, nunca las define inline.

Funcionalidad:
1. CAPTURA: medir_y_registrar() — Extrae métricas durante ejecución
2. PERSISTENCIA: guardar_metricas() — Guarda a JSONL append-only
3. EVALUACIÓN: evaluar_exactitud(), evaluar_utilidad_semantica() — Calidad
4. ANÁLISIS: generar_graficos_comparativos(), analizar_benchmark_completo() — Comparación

Autor: Claude (IA) + Usuario
Versión: 2.1 (Python 3.14, AutoGen 0.14.1)
"""

import time
from datetime import datetime
import json
import os


# ═══════════════════════════════════════════════════════════════════════════
# FASE 1: CAPTURA DE MÉTRICAS (durante ejecución)
# ═══════════════════════════════════════════════════════════════════════════

def medir_y_registrar(chat_result, wall_time, model_name, temperature, variant_label, consulta):
    """
    Extrae métricas de una respuesta AutoGen ChatResult y construye registro de benchmarking.

    Args:
        chat_result: objeto ChatResult devuelto por agent.initiate_chat()
        wall_time: tiempo de pared en segundos (time.perf_counter() - t0)
        model_name: nombre del modelo (ej "qwen2.5:7b")
        temperature: temperatura usada
        variant_label: etiqueta de variante para agrupación (ej "qwen25_baseline")
        consulta: texto de la consulta ejecutada (se trunca a 100 chars en registro)

    Returns:
        dict: registro de métrica listo para guardar en JSONL
    """
    try:
        respuesta_final = chat_result.summary or "Sin resumen disponible."
        num_turnos_reales = len(chat_result.chat_history) if hasattr(chat_result, 'chat_history') else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "variant_label": variant_label,
            "modelo": model_name,
            "temperatura": temperature,
            "consulta": consulta[:100],
            "wall_time_seconds": round(wall_time, 3),
            "num_agent_turns": num_turnos_reales,
            "respuesta_resumen": respuesta_final[:200],
            "exito": True,
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "variant_label": variant_label,
            "consulta": consulta[:100],
            "exito": False,
            "error": str(e)[:200],
            "wall_time_seconds": round(wall_time, 3)
        }


# ═══════════════════════════════════════════════════════════════════════════
# FASE 2: PERSISTENCIA (guarda a JSONL)
# ═══════════════════════════════════════════════════════════════════════════

def guardar_metricas(metricas, output_dir, enabled=True):
    """
    Persiste métricas en outputs/benchmark.jsonl (append-only, JSONL).

    Args:
        metricas: lista de dicts (cada uno es una métrica)
        output_dir: carpeta donde vive benchmark.jsonl (ej "outputs")
        enabled: booleano, si False hace skip silencioso
    """
    if not enabled:
        return

    os.makedirs(output_dir, exist_ok=True)

    benchmark_file = os.path.join(output_dir, "benchmark.jsonl")
    with open(benchmark_file, 'a', encoding='utf-8') as f:
        for m in metricas:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    print(f"[OK] {len(metricas)} métrica(s) anexada(s) a: {benchmark_file}")


# ═══════════════════════════════════════════════════════════════════════════
# FASE 3: EVALUACIÓN (calidad de respuestas)
# ═══════════════════════════════════════════════════════════════════════════

def evaluar_exactitud(respuesta, verdad_esperada):
    """
    Compara respuesta contra valor esperado (exactitud 0-1).
    Soporta valores numéricos y textuales.
    """
    if isinstance(verdad_esperada, (int, float)):
        try:
            valor = float(respuesta.split()[-1])
            error_pct = abs(valor - verdad_esperada) / abs(verdad_esperada)
            return max(0, 1 - error_pct)
        except:
            return 0
    else:
        return 1 if verdad_esperada.lower() in respuesta.lower() else 0


def evaluar_utilidad_semantica(respuesta, consulta):
    """
    Evalúa si la respuesta responde la consulta (0-1).
    Heurística: overlap de palabras clave.
    """
    palabras = set(consulta.lower().split())
    respuesta_palabras = set(respuesta.lower().split())
    overlap = len(palabras & respuesta_palabras) / len(palabras) if palabras else 0
    return min(1, overlap)


def obtener_casos_a_revisar_hibrido(metricas, umbral_muestreo=0.5, n_max=None):
    """
    Para evaluación híbrida: retorna casos límite que necesitan revisión manual.
    """
    lower = 1 - umbral_muestreo
    casos = [m for m in metricas if lower <= m.get('exactitud_auto', 0) <= umbral_muestreo]
    return casos[:n_max] if n_max else casos


# ═══════════════════════════════════════════════════════════════════════════
# FASE 4: ANÁLISIS Y VISUALIZACIÓN (comparación de modelos)
# ═══════════════════════════════════════════════════════════════════════════

def cargar_benchmark_jsonl(archivo):
    """
    Carga métricas desde archivo benchmark.jsonl.

    Args:
        archivo: ruta a outputs/benchmark.jsonl

    Returns:
        pandas.DataFrame con todas las métricas
    """
    try:
        import pandas as pd
        df = pd.read_json(archivo, lines=True)
        print(f"[OK] Cargadas {len(df)} métricas desde {archivo}")
        return df
    except Exception as e:
        print(f"[ERROR] No se pudo cargar {archivo}: {e}")
        return None


def generar_resumen_por_modelo(df):
    """
    Genera tabla resumen de métricas por modelo.

    Args:
        df: DataFrame de benchmark

    Returns:
        DataFrame agrupado por modelo con estadísticas
    """
    try:
        import pandas as pd

        df_ok = df[df['exito'] == True]

        if len(df_ok) == 0:
            print("[WARN] No hay consultas exitosas para analizar")
            return None

        print("\n" + "="*100)
        print("RESUMEN POR MODELO")
        print("="*100)

        for modelo in sorted(df_ok['modelo'].unique()):
            df_m = df_ok[df_ok['modelo'] == modelo]

            latencia_promedio = df_m['wall_time_seconds'].mean()
            tokens_promedio = df_m['tokens_total'].mean() if 'tokens_total' in df_m.columns else 0
            throughput = tokens_promedio / latencia_promedio if latencia_promedio > 0 else 0

            print(f"\n📊 MODELO: {modelo}")
            print(f"   Consultas: {len(df_m)}")
            print(f"   Latencia (promedio):  {latencia_promedio:.3f}s")
            print(f"   Latencia (mín/máx):   {df_m['wall_time_seconds'].min():.3f}s / {df_m['wall_time_seconds'].max():.3f}s")
            print(f"   Tokens (promedio):    {tokens_promedio:.0f}")
            print(f"   Throughput:           {throughput:.2f} tokens/segundo")
            print(f"   Turnos agentes:       {df_m['num_agent_turns'].mean():.1f}")

        print("\n" + "="*100 + "\n")
        return df_ok

    except Exception as e:
        print(f"[ERROR] Error generando resumen: {e}")
        return None


def generar_graficos_comparativos(df, output_dir="outputs"):
    """
    Genera gráficos comparativos de rendimiento entre modelos.

    Args:
        df: DataFrame de benchmark
        output_dir: directorio para guardar gráficos

    Returns:
        dict con paths de archivos generados
    """
    try:
        import pandas as pd
        import matplotlib.pyplot as plt

        os.makedirs(output_dir, exist_ok=True)

        df_ok = df[df['exito'] == True]

        if len(df_ok) == 0:
            print("[WARN] No hay datos exitosos para gráficos")
            return {}

        archivos = {}
        modelos = sorted(df_ok['modelo'].unique())

        # ═══════════════════════════════════════════════════════════════════
        # Gráfico 1: Latencia por modelo (box plot)
        # ═══════════════════════════════════════════════════════════════════
        fig, ax = plt.subplots(figsize=(12, 6))
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
        print(f"[OK] Gráfico 1/4 — Latencia: {path1}")

        # ═══════════════════════════════════════════════════════════════════
        # Gráfico 2: Tokens totales por modelo
        # ═══════════════════════════════════════════════════════════════════
        if 'tokens_total' in df_ok.columns:
            fig, ax = plt.subplots(figsize=(12, 6))
            datos_tokens = [df_ok[df_ok['modelo'] == m]['tokens_total'].values for m in modelos]

            bp = ax.boxplot(datos_tokens, labels=modelos, patch_artist=True)
            for patch in bp['boxes']:
                patch.set_facecolor('lightgreen')

            ax.set_ylabel('Tokens totales', fontsize=12, fontweight='bold')
            ax.set_xlabel('Modelo', fontsize=12, fontweight='bold')
            ax.set_title('Comparación de Tokens por Modelo', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            path2 = os.path.join(output_dir, "02_comparacion_tokens.png")
            plt.savefig(path2, dpi=100, bbox_inches='tight')
            plt.close()
            archivos['tokens'] = path2
            print(f"[OK] Gráfico 2/4 — Tokens: {path2}")

        # ═══════════════════════════════════════════════════════════════════
        # Gráfico 3: Trade-off Latencia vs Tokens (scatter)
        # ═══════════════════════════════════════════════════════════════════
        if 'tokens_total' in df_ok.columns:
            fig, ax = plt.subplots(figsize=(12, 8))

            colores_mapa = {
                'qwen2.5:7b': '#1f77b4',
                'deepseek-v2:16b': '#ff7f0e',
                'llama3.1:8b-instruct-q2_K': '#2ca02c'
            }

            for modelo in modelos:
                df_modelo = df_ok[df_ok['modelo'] == modelo]
                color = colores_mapa.get(modelo, '#d62728')
                ax.scatter(df_modelo['wall_time_seconds'], df_modelo['tokens_total'],
                          label=modelo, s=120, alpha=0.6, color=color, edgecolors='black', linewidth=1)

            ax.set_xlabel('Latencia (segundos)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Tokens totales', fontsize=12, fontweight='bold')
            ax.set_title('Trade-off: Latencia vs Tokens', fontsize=14, fontweight='bold')
            ax.legend(fontsize=10, loc='best')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()

            path3 = os.path.join(output_dir, "03_tradeoff_latencia_tokens.png")
            plt.savefig(path3, dpi=100, bbox_inches='tight')
            plt.close()
            archivos['tradeoff'] = path3
            print(f"[OK] Gráfico 3/4 — Trade-off: {path3}")

        # ═══════════════════════════════════════════════════════════════════
        # Gráfico 4: Throughput (tokens/segundo) por modelo
        # ═══════════════════════════════════════════════════════════════════
        if 'tokens_total' in df_ok.columns:
            fig, ax = plt.subplots(figsize=(12, 6))

            throughputs = []
            for modelo in modelos:
                df_modelo = df_ok[df_ok['modelo'] == modelo]
                tp = (df_modelo['tokens_total'] / df_modelo['wall_time_seconds']).values
                throughputs.append(tp)

            bp = ax.boxplot(throughputs, labels=modelos, patch_artist=True)
            for patch in bp['boxes']:
                patch.set_facecolor('lightyellow')

            ax.set_ylabel('Throughput (tokens/segundo)', fontsize=12, fontweight='bold')
            ax.set_xlabel('Modelo', fontsize=12, fontweight='bold')
            ax.set_title('Comparación de Throughput', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            path4 = os.path.join(output_dir, "04_comparacion_throughput.png")
            plt.savefig(path4, dpi=100, bbox_inches='tight')
            plt.close()
            archivos['throughput'] = path4
            print(f"[OK] Gráfico 4/4 — Throughput: {path4}")

        print(f"[OK] ✅ {len(archivos)} gráficos generados\n")
        return archivos

    except Exception as e:
        print(f"[ERROR] Error generando gráficos: {e}")
        import traceback
        traceback.print_exc()
        return {}


def generar_tabla_comparativa(df, output_file="outputs/TABLA_COMPARATIVA_MODELOS.txt"):
    """
    Genera tabla comparativa de rendimiento entre modelos.
    """
    try:
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        df_ok = df[df['exito'] == True]

        if len(df_ok) == 0:
            print("[WARN] No hay datos para tabla comparativa")
            return ""

        tabla_texto = "═" * 120 + "\n"
        tabla_texto += "TABLA COMPARATIVA DE RENDIMIENTO POR MODELO\n"
        tabla_texto += "═" * 120 + "\n\n"

        for modelo in sorted(df_ok['modelo'].unique()):
            df_m = df_ok[df_ok['modelo'] == modelo]

            latencia_promedio = df_m['wall_time_seconds'].mean()
            tokens_promedio = df_m['tokens_total'].mean() if 'tokens_total' in df_m.columns else 0
            throughput = tokens_promedio / latencia_promedio if latencia_promedio > 0 else 0

            tabla_texto += f"📊 MODELO: {modelo}\n"
            tabla_texto += f"   ├─ Consultas exitosas:        {len(df_m)}\n"
            tabla_texto += f"   ├─ LATENCIA:\n"
            tabla_texto += f"   │  ├─ Promedio:                {latencia_promedio:.3f}s\n"
            tabla_texto += f"   │  ├─ Mínima:                  {df_m['wall_time_seconds'].min():.3f}s\n"
            tabla_texto += f"   │  ├─ Máxima:                  {df_m['wall_time_seconds'].max():.3f}s\n"
            tabla_texto += f"   │  └─ Desv. Estándar:          {df_m['wall_time_seconds'].std():.3f}s\n"
            tabla_texto += f"   ├─ TOKENS:\n"
            tabla_texto += f"   │  ├─ Promedio:                {tokens_promedio:.0f}\n"
            tabla_texto += f"   │  ├─ Mínimo:                  {df_m['tokens_total'].min():.0f}\n"
            tabla_texto += f"   │  └─ Máximo:                  {df_m['tokens_total'].max():.0f}\n"
            tabla_texto += f"   ├─ Throughput:                {throughput:.2f} tokens/segundo\n"
            tabla_texto += f"   └─ Turnos agentes promedio:   {df_m['num_agent_turns'].mean():.1f}\n"
            tabla_texto += "\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(tabla_texto)

        print(tabla_texto)
        print(f"[OK] Tabla comparativa guardada: {output_file}\n")
        return tabla_texto

    except Exception as e:
        print(f"[ERROR] Error generando tabla: {e}")
        return ""


def analizar_benchmark_completo(archivo_jsonl="outputs/benchmark.jsonl", output_dir="outputs"):
    """
    Ejecuta análisis completo: gráficos + tabla + resumen.

    Uso típico en script o terminal:
        from benchmark import analizar_benchmark_completo
        analizar_benchmark_completo()
    """
    print("\n" + "█" * 120)
    print("█ ANÁLISIS COMPLETO DE BENCHMARK — COMPARACIÓN DE MODELOS")
    print("█" * 120 + "\n")

    if not os.path.exists(archivo_jsonl):
        print(f"[ERROR] Archivo no encontrado: {archivo_jsonl}")
        return

    # Cargar datos
    df = cargar_benchmark_jsonl(archivo_jsonl)
    if df is None or len(df) == 0:
        print("[ERROR] No se pudo cargar benchmark")
        return

    # Generar resumen
    print("\n[PASO 1/3] Generando resumen por modelo...")
    generar_resumen_por_modelo(df)

    # Generar gráficos
    print("\n[PASO 2/3] Generando gráficos comparativos...")
    graficos = generar_graficos_comparativos(df, output_dir)

    # Generar tabla
    print("[PASO 3/3] Generando tabla comparativa...")
    generar_tabla_comparativa(df, os.path.join(output_dir, "TABLA_COMPARATIVA_MODELOS.txt"))

    print("█" * 120)
    print("█ ✅ ANÁLISIS COMPLETADO")
    print("█" * 120 + "\n")


def generar_reporte_markdown(df, output_file=None):
    """
    Genera reporte completo en Markdown con análisis de rendimiento.

    Args:
        df: DataFrame de benchmark
        output_file: archivo markdown de salida (si None, auto-genera con timestamp)
    """
    try:
        # Generar nombre con timestamp si no se proporciona
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/REPORTE_BENCHMARK_{timestamp}.md"

        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        df_ok = df[df['exito'] == True]

        if len(df_ok) == 0:
            print("[WARN] No hay datos exitosos para reporte")
            return

        # Encabezado
        reporte = """# 📊 REPORTE DE BENCHMARK — Comparación de Modelos

**Fecha:** {}
**Total de consultas:** {} (exitosas: {})
**Modelos analizados:** {}

---

## 📈 Resumen Ejecutivo

Este reporte presenta un análisis comparativo de rendimiento entre los diferentes modelos
evaluados en el sistema AutoMed v2. Se consideran tres dimensiones principales:

1. **Latencia (velocidad)** — Tiempo de respuesta por consulta
2. **Eficiencia (tokens)** — Cantidad de tokens consumidos
3. **Throughput** — Tokens procesados por segundo

---

## 📊 Métricas por Modelo

""".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            len(df),
            len(df_ok),
            ", ".join(sorted(df_ok['modelo'].unique()))
        )

        # Tabla comparativa
        reporte += "| Modelo | Consultas | Latencia (s) | Mín | Máx | Tokens | Throughput | Turnos |\n"
        reporte += "|--------|-----------|--------------|-----|-----|--------|-----------|--------|\n"

        for modelo in sorted(df_ok['modelo'].unique()):
            df_m = df_ok[df_ok['modelo'] == modelo]

            latencia_promedio = df_m['wall_time_seconds'].mean()
            latencia_min = df_m['wall_time_seconds'].min()
            latencia_max = df_m['wall_time_seconds'].max()
            tokens_promedio = df_m['tokens_total'].mean() if 'tokens_total' in df_m.columns else 0
            throughput = tokens_promedio / latencia_promedio if latencia_promedio > 0 else 0
            turnos = df_m['num_agent_turns'].mean()

            reporte += f"| {modelo} | {len(df_m)} | {latencia_promedio:.3f} | {latencia_min:.3f} | {latencia_max:.3f} | {tokens_promedio:.0f} | {throughput:.2f} | {turnos:.1f} |\n"

        reporte += "\n---\n\n"

        # Gráficos
        reporte += """## 📉 Visualizaciones

### Latencia por Modelo
![Latencia](01_comparacion_latencia.png)
*Box plot mostrando distribución de latencias por modelo.*

### Tokens Consumidos
![Tokens](02_comparacion_tokens.png)
*Distribución de tokens totales por modelo.*

### Trade-off: Latencia vs Tokens
![Trade-off](03_tradeoff_latencia_tokens.png)
*Relación entre velocidad (latencia) y eficiencia (tokens).*

### Throughput (Tokens/Segundo)
![Throughput](04_comparacion_throughput.png)
*Capacidad de procesamiento: tokens por segundo.*

---

## 🔍 Análisis Detallado

"""

        # Análisis por modelo
        for modelo in sorted(df_ok['modelo'].unique()):
            df_m = df_ok[df_ok['modelo'] == modelo]

            latencia_promedio = df_m['wall_time_seconds'].mean()
            latencia_std = df_m['wall_time_seconds'].std()
            tokens_promedio = df_m['tokens_total'].mean() if 'tokens_total' in df_m.columns else 0
            throughput = tokens_promedio / latencia_promedio if latencia_promedio > 0 else 0

            reporte += f"### {modelo}\n\n"
            reporte += f"**Consultas ejecutadas:** {len(df_m)}\n\n"
            reporte += "**Latencia:**\n"
            reporte += f"- Promedio: {latencia_promedio:.3f}s\n"
            reporte += f"- Desv. Estándar: {latencia_std:.3f}s\n"
            reporte += f"- Rango: {df_m['wall_time_seconds'].min():.3f}s — {df_m['wall_time_seconds'].max():.3f}s\n\n"
            reporte += "**Tokens:**\n"
            reporte += f"- Promedio: {tokens_promedio:.0f} tokens/consulta\n"
            reporte += f"- Rango: {df_m['tokens_total'].min():.0f} — {df_m['tokens_total'].max():.0f}\n\n"
            reporte += f"**Throughput:** {throughput:.2f} tokens/segundo\n\n"

        reporte += "\n---\n\n"

        # Análisis comparativo
        reporte += """## 🏆 Análisis Comparativo

### Velocidad (Latencia)
"""

        modelos_sorted = sorted(df_ok.groupby('modelo')['wall_time_seconds'].mean().items(),
                               key=lambda x: x[1])
        for i, (modelo, latencia) in enumerate(modelos_sorted, 1):
            reporte += f"{i}. **{modelo}** — {latencia:.3f}s\n"

        reporte += "\n### Eficiencia (Tokens por consulta)\n"

        modelos_sorted_tokens = sorted(df_ok.groupby('modelo')['tokens_total'].mean().items(),
                                       key=lambda x: x[1])
        for i, (modelo, tokens) in enumerate(modelos_sorted_tokens, 1):
            reporte += f"{i}. **{modelo}** — {tokens:.0f} tokens\n"

        reporte += "\n### Throughput (Tokens/Segundo)\n"

        throughputs = {}
        for modelo in df_ok['modelo'].unique():
            df_m = df_ok[df_ok['modelo'] == modelo]
            latencia_promedio = df_m['wall_time_seconds'].mean()
            tokens_promedio = df_m['tokens_total'].mean()
            throughputs[modelo] = tokens_promedio / latencia_promedio if latencia_promedio > 0 else 0

        modelos_sorted_throughput = sorted(throughputs.items(), key=lambda x: x[1], reverse=True)
        for i, (modelo, tp) in enumerate(modelos_sorted_throughput, 1):
            reporte += f"{i}. **{modelo}** — {tp:.2f} tokens/segundo\n"

        reporte += """
---

## 📋 Recomendaciones

### Criterios de Selección

| Criterio | Mejor Modelo | Caso de Uso |
|----------|--------------|------------|
| **Velocidad** | """ + modelos_sorted[0][0] + """ | Consultas tiempo-real, baja latencia crítica |
| **Eficiencia** | """ + modelos_sorted_tokens[0][0] + """ | Recursos limitados, costo optimizado |
| **Throughput** | """ + modelos_sorted_throughput[0][0] + """ | Alto volumen de consultas concurrentes |
| **Balance** | (Revisar trade-off) | Producción general |

### Próximos Pasos

1. ✅ **Ejecutar pruebas de exactitud médica** con verdades esperadas
2. ✅ **Validar que exactitud ≥ 95%** antes de producción
3. ✅ **Seleccionar modelo** basado en balance velocidad/calidad
4. ✅ **Documentar decisión** en checkpoint

---

## 📌 Notas Técnicas

- Todas las latencias son **wall-clock time** (tiempo de pared)
- Los tokens incluyen entrada + salida
- El throughput es teórico basado en latencia promedio
- Los gráficos usan matplotlib con resolución 100 DPI

---

**Generado:** {}
**Archivo:** REPORTE_BENCHMARK.md
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(reporte)

        print(f"[OK] Reporte Markdown generado: {output_file}\n")
        return reporte

    except Exception as e:
        print(f"[ERROR] Error generando reporte Markdown: {e}")
        import traceback
        traceback.print_exc()
        return ""


if __name__ == "__main__":
    # Ejecutar análisis completo si se llama directamente
    print("\n[INFO] Ejecutando análisis completo...\n")

    # Cargar datos
    df = cargar_benchmark_jsonl("outputs/benchmark.jsonl")
    if df is not None and len(df) > 0:
        # Generar todos los reportes
        generar_resumen_por_modelo(df)
        generar_graficos_comparativos(df, "outputs")
        generar_tabla_comparativa(df, "outputs/TABLA_COMPARATIVA_MODELOS.txt")
        generar_reporte_markdown(df, "outputs/REPORTE_BENCHMARK.md")

        print("\n✅ ANÁLISIS COMPLETADO")
        print("\nArchivos generados:")
        print("  - outputs/01_comparacion_latencia.png")
        print("  - outputs/02_comparacion_tokens.png")
        print("  - outputs/03_tradeoff_latencia_tokens.png")
        print("  - outputs/04_comparacion_throughput.png")
        print("  - outputs/TABLA_COMPARATIVA_MODELOS.txt")
        print("  - outputs/REPORTE_BENCHMARK.md")
    else:
        print("[ERROR] No se pudieron cargar datos de benchmark")
