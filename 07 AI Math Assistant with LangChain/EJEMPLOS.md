# EJEMPLOS — IA Agente - Tools y Math

## Casos de Uso y Patrones de Consulta

---

## 1. Operaciones Matemáticas Simples

### 1.1 Suma

**Consulta**:
```
¿Cuánto es 5 + 3 + 10?
```

**Ejecución interna**:
1. LLM: "Necesito invocar sumar_numeros"
2. Tool: `sumar_numeros("5 + 3 + 10")` → extrae `[5, 3, 10]` → suma → `18`
3. Respuesta: "5 + 3 + 10 = 18"

**Variantes**:
- "Suma estos números: 100, 50, 25" → `175`
- "¿Cuál es la suma de ocho y doce?" → `20`
- "5 y 3 y 10" → `18`

---

### 1.2 Resta

**Consulta**:
```
Réstame 50 menos 12 menos 8
```

**Ejecución**:
1. LLM: "Invoco restar_numeros"
2. Tool: `restar_numeros("50 menos 12 menos 8")` → `50 - 12 - 8 = 30`
3. Respuesta: "50 - 12 - 8 = 30"

**Variantes**:
- "¿Cuánto es cien menos treinta?" → `70`
- "20 - 5 - 3" → `12`
- "Resta 15 de 100" → `85`

---

### 1.3 Multiplicación

**Consulta**:
```
Multiplica tres por cuatro por dos
```

**Ejecución**:
1. LLM: "Invoco multiplicar_numeros"
2. Tool: `multiplicar_numeros("3 por 4 por 2")` → `3 × 4 × 2 = 24`
3. Respuesta: "3 × 4 × 2 = 24"

**Variantes**:
- "7 × 8" → `56`
- "Multiplica estos números: 2, 3, 5" → `30`
- "¿Cuál es el producto de 9 y 11?" → `99`

---

### 1.4 División

**Consulta**:
```
¿Cuánto es 100 dividido entre 5 dividido entre 2?
```

**Ejecución**:
1. LLM: "Invoco dividir_numeros"
2. Tool: `dividir_numeros("100 ÷ 5 ÷ 2")` → `100 ÷ 5 = 20`, `20 ÷ 2 = 10`
3. Respuesta: "100 ÷ 5 ÷ 2 = 10"

**Variantes**:
- "50 / 10" → `5`
- "Divide mil entre cien" → `10`
- "¿Cuál es 144 dividido entre 12?" → `12`

---

### 1.5 Potencia (Ejercicio)

**Consulta**:
```
¿Cuánto es 2 elevado a 5?
```

**Ejecución**:
1. LLM: "Invoco calcular_potencia"
2. Tool: `calcular_potencia("2 elevado a 5")` → `2^5 = 32`
3. Respuesta: "2 elevado a 5 = 32"

**Variantes**:
- "3 al cuadrado" → `9`
- "10^3" → `1000`
- "¿Cuál es 4 elevado al cuadrado?" → `16`

---

## 2. Operaciones Combinadas

### 2.1 Suma y Multiplicación

**Consulta**:
```
Suma 5 y 3, luego multiplica el resultado por 2
```

**Ejecución interna**:
1. LLM razona: "Primero suma, luego multiplica"
2. Tool 1: `sumar_numeros("5 y 3")` → `8`
3. Tool 2: `multiplicar_numeros("8 por 2")` → `16`
4. Respuesta: "La suma de 5 y 3 es 8, multiplicado por 2 = 16"

---

### 2.2 Resta y División

**Consulta**:
```
Resta 50 menos 10, luego divide entre 5
```

**Ejecución**:
1. Tool 1: `restar_numeros("50 menos 10")` → `40`
2. Tool 2: `dividir_numeros("40 entre 5")` → `8`
3. Respuesta: "50 - 10 = 40, 40 ÷ 5 = 8"

---

## 3. Combinación con Búsqueda Wikipedia

### 3.1 Datos Contextuales + Operaciones

**Consulta**:
```
¿Cuál es la población de Perú? Multiplícala por 0.5
```

**Ejecución interna**:
1. LLM: "Necesito buscar la población de Perú"
2. Tool 1: `buscar_wikipedia("Perú población")` → "La población de Perú es aproximadamente 34 millones"
3. LLM extrae: `34 millones`
4. Tool 2: `multiplicar_numeros("34 por 0.5")` → `17`
5. Respuesta: "La población de Perú es ~34 millones. Multiplicada por 0.5 = 17 millones"

---

### 3.2 Buscar + Sumar

**Consulta**:
```
¿Cuál es la altura del Monte Everest? Sumale 1000 metros
```

**Ejecución**:
1. Wikipedia: "Monte Everest: 8848 metros"
2. Suma: `8848 + 1000 = 9848`
3. Respuesta: "El Monte Everest mide 8848m. Más 1000m = 9848m"

---

## 4. Casos Especiales

### 4.1 Números Negativos

**Consulta**:
```
¿Cuánto es -5 más 3?
```

**Ejecución**:
1. Regex extrae: `[-5, 3]`
2. Suma: `-5 + 3 = -2`
3. Respuesta: "-5 + 3 = -2"

---

### 4.2 Números Decimales

**Consulta**:
```
Multiplica 3.5 por 2.5
```

**Ejecución**:
1. Regex extrae: `[3.5, 2.5]`
2. Multiplica: `3.5 × 2.5 = 8.75`
3. Respuesta: "3.5 × 2.5 = 8.75"

---

### 4.3 Números Escritos en Palabras

**Consulta**:
```
¿Cuánto es dos más tres?
```

**Desafío**: El regex extrae números, no palabras. LLM debe interpretar "dos" → 2, "tres" → 3.

**Ejecución**:
1. LLM: "Reconozco 'dos' y 'tres' como números"
2. LLM reformula: "dos más tres" → llama a la herramienta con formato parseado
3. Tool: Dependiendo de cómo el LLM envíe la consulta, puede parsear correctamente

**Nota**: Si el LLM no interpreta bien palabras, mejorar el prompt del agente (celda 9).

---

## 5. Patrones Avanzados

### 5.1 Cadena de Razonamientos (Reflection)

**Consulta**:
```
Verifica: ¿Es correcto que 5 + 3 = 8?
```

**Ejecución**:
1. Tool: `sumar_numeros("5 y 3")` → `8`
2. LLM: "Sí, 5 + 3 = 8 es correcto"
3. Respuesta con justificación

---

### 5.2 Múltiples Consultas Secuenciales

```python
consultas = [
    "¿Cuánto es 5 + 3?",
    "Multiplica el resultado por 2",
    "Suma 10 al resultado anterior"
]

for i, consulta in enumerate(consultas):
    response = agent.invoke({"messages": [("user", consulta)]})
    print(f"[{i+1}] {consulta} → {response['messages'][-1].content}")
```

**Salida**:
```
[1] ¿Cuánto es 5 + 3? → 8
[2] Multiplica el resultado por 2 → 16
[3] Suma 10 al resultado anterior → 26
```

---

## 6. Anti-Patrones (Qué NO Hacer)

### ❌ Consulta Ambigua

```
"Haz matemática"
```

**Problema**: El LLM no sabe qué operación hacer.  
**Solución**: Sé específico: "¿Cuánto es 5 + 3?"

### ❌ Esperar Interpretación de Palabras sin Preparación

```
"¿Cuánto es cincuenta dividido entre diez?"
```

**Problema**: Regex `\d+` no captura "cincuenta".  
**Solución**: El LLM reformula internamente, pero no es 100% confiable. Mejor: "¿Cuánto es 50 ÷ 10?"

### ❌ Operaciones sin Tool Relevante

```
"¿Cuál es la raíz cuadrada de 16?"
```

**Problema**: No hay herramienta `calcular_raiz_cuadrada`.  
**Solución**: Agregarla (ver MANUAL.md → Extender).

---

## 7. Metricas de Éxito

Para verificar que el agente funciona correctamente:

| Métrica | Expected | Síntoma de Error |
|---|---|---|
| **Latencia** | 1-5s por consulta | >10s → Ollama lento |
| **Accuracy** | 100% en operaciones simples | Resultados incorrectos → Bug en tool |
| **Logs** | Archivos en `logs/` | No hay logs → Config error |
| **Salida** | Archivo en `outputs/` | No hay archivo → `save_results=false` |
| **Cobertura** | Usa al menos 1 tool | Agente no invoca tools → Prompt débil |

---

## 8. Benchmarking

Ejecutar multiples consultas y medir performance:

```python
import time
from datetime import datetime

consultas_benchmark = [
    "¿Cuánto es 5 + 3?",
    "Resta 100 menos 25",
    "Multiplica 7 por 8",
    "Divide 1000 entre 10",
    "¿Cuál es la población de Japón?"
]

resultados = []
for consulta in consultas_benchmark:
    inicio = time.time()
    response = agent.invoke({"messages": [("user", consulta)]})
    latencia = time.time() - inicio
    
    resultados.append({
        "consulta": consulta,
        "latencia_ms": int(latencia * 1000),
        "resultado": response["messages"][-1].content[:50]
    })

# Guardar benchmark
with open("benchmark.json", "w") as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)
```

**Resultado esperado**:
```json
[
  {"consulta": "¿Cuánto es 5 + 3?", "latencia_ms": 1850, "resultado": "5 + 3 = 8"},
  {"consulta": "¿Cuál es la población de Japón?", "latencia_ms": 5200, "resultado": "La población de Japón es aproximadamente 125 millones"}
]
```

---

**Última actualización**: 2026-09-18  
**Versión**: 1.0
