# MANUAL TÉCNICO — IA Agente - Tools y Math

## Tabla de Contenidos

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Flujo de Ejecución](#flujo-de-ejecución)
3. [Módulos y Componentes](#módulos-y-componentes)
4. [Extender el Proyecto](#extender-el-proyecto)
5. [Performance y Optimización](#performance-y-optimización)
6. [Debugging](#debugging)

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      USUARIO (Español)                      │
│                   "¿Cuánto es 5 + 3?"                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│               ReAct Agent (LangGraph)                        │
│  • Razona: "Necesito sumar números"                         │
│  • Actúa: Invoca sumar_numeros("5 y 3")                     │
│  • Observa: "El resultado es 8"                             │
│  • Responde: (en español)                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ↓                               ↓
    ┌─────────────┐            ┌──────────────────┐
    │ Math Tools  │            │ Wikipedia Tool   │
    │ (@tool)     │            │ (contexto)       │
    │             │            │                  │
    │ • sumar     │            │ • buscar_wikipedia
    │ • restar    │            │ (sin API key)    │
    │ • multiplicar
    │ • dividir   │            │                  │
    │ • potencia  │            │                  │
    └──────┬──────┘            └────────┬─────────┘
           │                            │
           └────────┬───────────────────┘
                    │
                    ↓
        ┌───────────────────────┐
        │  Ollama Local         │
        │  (llama3.1:8b)        │
        │  http://localhost:114 │
        │  34                   │
        └───────────────────────┘
```

### Capas de Abstracción

| Capa | Componente | Responsabilidad |
|---|---|---|
| **UI/Entrada** | Usuario (texto en español) | Formular consultas |
| **Orquestación** | ReAct Agent (LangGraph) | Decidir qué herramienta usar, cuándo |
| **Lógica** | @tool decorators (Python) | Implementar algoritmos (suma, regex, etc.) |
| **Contexto** | Wikipedia API | Datos externos sin credenciales |
| **Inferencia** | Ollama + llama3.1:8b | Generar razonamientos y respuestas |
| **Config** | config.ini | Parametrización externalizada |
| **Observabilidad** | Logging (archivo + consola) | Trazabilidad y debugging |

---

## Flujo de Ejecución

### Inicialización (Celdas 1-5)

```python
# Celda 1: Cargar config.ini
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# Celda 4: Logging
logger = logging.getLogger('ai_math_agent')
logger.addHandler(FileHandler(...))  # Archivo + consola

# Celda 5: LLM Ollama
llm = ChatOllama(
    model="llama3.1:8b-instruct-q2_K",
    num_ctx=8192  # ← CRÍTICO: evita truncamiento
)
```

### Definición de Herramientas (Celdas 6-7)

```python
@tool
def sumar_numeros(expresion: str) -> float:
    """Suma números extraídos de texto."""
    # 1. Regex: extraer números
    numeros = re.findall(r'-?\d+\.?\d*', expresion)
    # 2. Convertir a float
    # 3. Sumar
    resultado = sum(float(n) for n in numeros)
    # 4. Log
    logger.info(f"Suma: {expresion} = {resultado}")
    return resultado
```

**Nota**: Cada `@tool` tiene docstring (visto por el LLM para entender cuándo usarlo).

### Creación del Agente (Celda 9)

```python
agent = create_react_agent(
    model=llm,
    tools=[sumar, resta, multiplicacion, division, wikipedia_tool],
    prompt="Eres un asistente matemático experto..."
)
```

`create_react_agent` genera internamente:
- Un grafo de estado que maneja "tool calling"
- Un prompt de sistema que describe las herramientas
- Un loop de razonamiento + actuación

### Ejecución de Consulta (Celda 10)

```python
response = agent.invoke({
    "messages": [("user", "¿Cuánto es 5 + 3?")]
})

respuesta_final = response["messages"][-1].content
# → "5 + 3 = 8"
```

**Internamente**:
1. LLM recibe: `"¿Cuánto es 5 + 3?"` + descripción de tools
2. LLM decide: "Necesito invocar `sumar_numeros('5 y 3')`"
3. Tool ejecuta: `sumar_numeros('5 y 3')` → `8.0`
4. LLM observa: "sumar_numeros devolvió 8"
5. LLM responde: "5 + 3 = 8"

---

## Módulos y Componentes

### Celda 1: Configuración

**Dependencias**: `configparser`, `pathlib`

**Funcionalidad**:
- Lee `config.ini` con encoding UTF-8
- Crea directorios `logs/` y `outputs/` si no existen
- Imprime configuración cargada

**Parámetros críticos**:
- `[ollama] model_name`: Qué modelo usar
- `[ollama] base_url`: Dónde está Ollama
- `[ollama] temperature`: 0.0 (determinismo) vs. 0.7+ (creatividad)

### Celda 4: Logging

**Dependencias**: `logging`, `logging.handlers.RotatingFileHandler`

**Funcionalidad**:
- Crea logger con dos handlers: archivo (rotado) + consola
- Archivo: `logs/ai_math_YYYYMMDD.log` (máx 10 MB, 5 backups)
- Consola: formato simple `LEVEL: message`

**Uso**:
```python
logger.info("✅ LLM inicializado")
logger.error("❌ Error al conectar con Ollama")
```

### Celda 5: LLM

**Dependencias**: `langchain_ollama.ChatOllama`

**Parámetro crítico**: `num_ctx=8192`

Sin esto, qwen2.5 (y potencialmente otros modelos) truncan los prompts de tool-calling, causando `ValueError: Invalid response from LLM call`.

### Celdas 6-7: Tools Matemáticas

**Patrón comum**:
```python
@tool
def nombre_herramienta(parametro: str) -> float:
    """Docstring visible al LLM."""
    # 1. Extraer números vía regex
    numeros = re.findall(r'-?\d+\.?\d*', parametro)
    # 2. Operación
    resultado = operacion(numeros)
    # 3. Log
    logger.info(f"Operación: {parametro} = {resultado}")
    return resultado
```

**Regex explicado**:
- `-?`: Número negativo opcional
- `\d+`: Uno o más dígitos
- `\.?`: Punto decimal opcional
- `\d*`: Cero o más dígitos decimales

Ejemplo: `"5 y 3"` → `['5', '3']` → `[5.0, 3.0]`

### Celda 7b: Tool Wikipedia

```python
wikipedia_tool = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper()  # Sin API key
)
```

`WikipediaAPIWrapper` usa la API pública (https://en.wikipedia.org/w/api.php), sin credenciales.

### Celda 9: ReAct Agent

```python
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt="Eres un asistente matemático..."
)
```

**¿Qué hace internamente?**
- Crea un `StateGraph` con nodos: ["agent", "action", "error"]
- El nodo "agent" invoca al LLM
- El nodo "action" ejecuta herramientas
- Itera hasta que el LLM responda (sin invocar más tools)

**Diferencia vs. initialize_agent (deprecado)**:
- `initialize_agent`: API imperativa (paso a paso)
- `create_react_agent`: API declarativa (LangGraph, estado explícito)

---

## Extender el Proyecto

### 1. Agregar una Nueva Herramienta

**Ejemplo: Raíz cuadrada**

```python
import math

@tool
def calcular_raiz_cuadrada(numero_str: str) -> float:
    """Calcula la raíz cuadrada de un número."""
    numeros = re.findall(r'\d+\.?\d*', numero_str)
    if numeros:
        resultado = math.sqrt(float(numeros[0]))
        logger.info(f"Raíz cuadrada: √{numeros[0]} = {resultado}")
        return resultado
    return 0

# Agregar a la lista de tools
tools.append(calcular_raiz_cuadrada)

# Recrear agente
agent = create_react_agent(model=llm, tools=tools)
```

### 2. Agregar una Herramienta Integrada (ej. Serper para búsqueda web)

```python
from langchain_community.tools import SerperDevTool

# PRECAUCIÓN: Requiere SERPER_API_KEY en config.ini o entorno
serper_key = config.get('serper', 'api_key', fallback=None)
if serper_key:
    search_tool = SerperDevTool(serpapi_api_key=serper_key)
    tools.append(search_tool)
```

### 3. Extender el Prompt del Agente

```python
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt="""
Eres un asistente matemático EXPERTO. Debes:
1. Analizar la consulta en ESPAÑOL
2. Decidir qué herramientas usar
3. Combinar resultados si es necesario
4. Responder en ESPAÑOL de forma clara

IMPORTANTE:
- Si necesitas contexto (población, área, etc.), usa Wikipedia
- Redondea resultados a 2 decimales
- Siempre justifica tu respuesta
    """
)
```

### 4. Aplicar Reflection (Auto-crítica)

```python
# Crear un segundo agente para evaluar la respuesta
evaluador = create_react_agent(
    model=llm,
    tools=[],  # Solo razonamiento, sin tools
    prompt="Eres un evaluador de respuestas matemáticas. Verifica si la respuesta es correcta."
)

# En la celda de ejecución
response = agent.invoke({"messages": [("user", consulta)]})
respuesta_inicial = response["messages"][-1].content

# Auto-evaluar
evaluacion = evaluador.invoke({"messages": [
    ("user", f"Evalúa esta respuesta: {respuesta_inicial}")
]})

# Si no pasa, refinear
if "error" in evaluacion["messages"][-1].content.lower():
    respuesta_refinada = agent.invoke({"messages": [
        ("user", f"{consulta} (revisa tu respuesta anterior)")
    ]})
```

---

## Performance y Optimización

### Latencia

**Tipicamente**:
- Consultas simples (1 operación): ~1-2s
- Consultas medianas (2-3 operaciones): ~2-5s
- Consultas complejas (con Wikipedia): ~5-10s

**Desglose**:
- Ollama LLM inference: ~1-2s
- Tool execution: <100ms (suma/resta)
- Wikipedia lookup: ~2-3s (I/O)

### Memory Footprint

| Componente | Estimado |
|---|---|
| Ollama llama3.1:8b (Q2K) | ~5 GB VRAM |
| LangChain + dependencias | ~500 MB |
| Estado del agente | ~10-50 MB |
| **Total** | **~5.5 GB** |

Cómodo en RTX 3050 (6 GB).

### Optimizaciones

1. **Usar qwen2.5 en lugar de llama3.1**:
   - Más ligero (4 GB Q2K)
   - Pero requiere `num_ctx=8192` explícito (ya incluido)

2. **Cachear resultados de Wikipedia**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def buscar_wikipedia_cached(query):
       return wikipedia_tool.run(query)
   ```

3. **Batch processing** (si hay múltiples consultas):
   ```python
   consultas = ["¿Cuánto es 5+3?", "¿Cuánto es 10-2?", ...]
   resultados = [agent.invoke({"messages": [("user", q)]}) for q in consultas]
   ```

---

## Debugging

### Activar Debug Logging

```python
# Celda de configuración
logger.setLevel(logging.DEBUG)
```

Esto imprimirá:
- Invocaciones de tools: `DEBUG: Invocando sumar_numeros('5 y 3')`
- Respuestas del LLM: `DEBUG: LLM response: ...`

### Inspeccionar Estado del Agente

```python
response = agent.invoke({"messages": [("user", consulta)]})

# Ver todos los mensajes (no solo el último)
for i, msg in enumerate(response["messages"]):
    print(f"[{i}] {msg.type}: {msg.content[:100]}...")
```

### Probar Tool en Aislamiento

```python
# Testear sumar_numeros sin agente
resultado = sumar_numeros("5 y 3")
print(f"Directo: {resultado}")  # → 8.0

# Verificar que es lo que el agente recibe
```

### Inspeccionar Prompts del LLM

```python
# Ver qué prompt recibe realmente el LLM
from langchain.schema import SystemMessage

prompt_visto_por_llm = "Eres un asistente..." + describe_tools(tools)
print(prompt_visto_por_llm)
```

---

## Referencias Internas

| Celda | Función | Líneas |
|---|---|---|
| 1 | Cargar config | 1-30 |
| 4 | Setup logging | 1-25 |
| 5 | Inicializar LLM | 1-20 |
| 6 | Herramientas matemáticas | 1-70 |
| 7b | Wikipedia | 1-15 |
| 9 | Crear agente | 1-30 |
| 10 | Ejecutar consultas | 1-50 |
| 13 | Ejercicio: potencia | 1-60 |

---

**Última actualización**: 2026-09-18  
**Versión**: 1.0  
**Autor**: ConvergenciaX / Claude Haiku 4.5
