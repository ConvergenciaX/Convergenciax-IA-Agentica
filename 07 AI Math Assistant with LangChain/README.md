# IA Agente - Tools y Math

**Asistente Matemático con LangChain Tool Calling y Ollama Local**

---

## 📋 Resumen Ejecutivo

Este proyecto implementa un **agente inteligente** que utiliza **herramientas personalizadas** para resolver problemas matemáticos complejos, integrando búsquedas contextuales en Wikipedia, todo ejecutado **100% en local** sin dependencias cloud.

### Características Principales

- ✅ **Tool Calling (@tool)**: Decoradores de LangChain para convertir funciones Python en herramientas dinámicas
- ✅ **ReAct Agent**: Razonamiento + Actuación — el LLM decide qué herramienta usar y cómo combinarlas
- ✅ **Ollama Local**: LLM llama3.1:8b ejecutado sin credenciales cloud
- ✅ **4 Operaciones Matemáticas**: sumar, restar, multiplicar, dividir (con extracción de números vía regex)
- ✅ **Búsqueda Wikipedia**: Sin API keys, información contextual en tiempo real
- ✅ **Configuración Parametrizada**: `config.ini` reutilizable (patrón CrewAI 101)
- ✅ **Logging Estructurado**: Archivo + consola con rotación automática
- ✅ **100% Español**: Prompts, comentarios, documentación en español

---

## 🚀 Inicio Rápido (3 minutos)

### 1. Prerrequisitos

- **Ollama instalado** y ejecutándose (`ollama serve` en otra terminal)
- **Modelo descargado**: `ollama pull llama3.1:8b-instruct-q2_K`
- **Ambiente Python 3.14**: `C:\workspace-vc\env-llm-314\Scripts\python.exe`

### 2. Instalar Dependencias

```bash
C:\workspace-vc\env-llm-314\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Ejecutar Notebook

```bash
C:\workspace-vc\env-llm-314\Scripts\python.exe -m jupyter notebook
```

Luego abre: `AI Math Assistant - LangChain Tool Calling_LLM_local.ipynb`

Ejecuta las celdas en orden (1 → 14). Deberías ver:
- ✅ Celdas 1-5: Configuración e inicialización
- ✅ Celdas 6-9: Definición y pruebas de herramientas
- ✅ Celdas 10-12: Ejecución de consultas ejemplo
- ✅ Celdas 13-14: Ejercicio de extensión (potencia)

### 4. Verificar Salida

```bash
ls logs/              # → ai_math_YYYYMMDD.log
ls outputs/           # → resultado_YYYYMMDD_HHMMSS.txt
```

---

## 📚 Estructura del Proyecto

```
07 AI Math Assistant with LangChain/
├── AI Math Assistant - LangChain Tool Calling_LLM_local.ipynb  # Notebook principal (14 celdas)
├── AI-Math-Assistant Tool Calling.ipynb                        # Original IBM (referencia, sin tocar)
│
├── config.ini                                                   # Configuración parametrizada
├── requirements.txt                                             # Dependencias
│
├── README.md          # ← Este archivo (guía de usuario)
├── MANUAL.md          # Detalles técnicos y arquitectura
├── QUICKSTART.md      # Inicio en 3 minutos (resumido)
├── EJEMPLOS.md        # Casos de uso y patrones
├── SOLUCION_ERRORES.md # Troubleshooting
│
├── checkpoint/
│   ├── CHECKPOINTS.md           # Histórico de hitos
│   └── CHECKPOINT_2026-09-18.md # Snapshot inicial del proyecto
│
├── logs/              # Se crean en ejecución
└── outputs/           # Se crean en ejecución
```

---

## 🔧 Configuración

### config.ini

Edita `config.ini` para personalizar el comportamiento:

```ini
[ollama]
base_url = http://localhost:11434
model_name = llama3.1:8b-instruct-q2_K
temperature = 0.0          # Determinismo para matemática exacta
max_tokens = 2000

[logging]
log_level = INFO           # DEBUG, INFO, WARNING, ERROR

[execution]
verbose = true             # Mostrar pasos del agente
show_agent_thoughts = true # Mostrar razonamiento
```

**Nota**: `temperature = 0.0` (no 0.7) porque en problemas matemáticos, necesitamos respuestas **deterministas**, no creativas. Si ejecutas con qwen2.5 o encuentras truncamiento, verifica que Ollama tenga `num_ctx=8192` (ya incluido en el código).

---

## 🛠️ Herramientas Disponibles

### Operaciones Matemáticas

| Herramienta | Entrada | Salida | Ejemplo |
|---|---|---|---|
| `sumar_numeros` | Texto con números | Suma | "5 y 3 y 10" → 18 |
| `restar_numeros` | Texto con números | Resta secuencial | "20 menos 5 menos 3" → 12 |
| `multiplicar_numeros` | Texto con números | Producto | "4 por 5 por 2" → 40 |
| `dividir_numeros` | Texto con números | División secuencial | "100 dividido 5 dividido 2" → 10 |
| `calcular_potencia` | Texto con base y exponente | Potencia | "2 elevado a 3" → 8 |

### Contexto

| Herramienta | Descripción | Requisitos |
|---|---|---|
| `buscar_wikipedia` | Búsqueda de artículos | Sin API key (API pública) |

---

## 💡 Conceptos Clave

### 1. **Tool Calling (@tool)**

```python
@tool
def sumar_numeros(expresion: str) -> float:
    """Suma números extraídos de texto."""
    numeros = re.findall(r'-?\d+\.?\d*', expresion)
    return sum(float(n) for n in numeros)
```

El decorador `@tool` convierte una función Python en una herramienta que el LLM puede **invocar dinámicamente** basándose en la consulta del usuario.

### 2. **ReAct Agent**

ReAct = **Reasoning + Acting**

```
Usuario: "¿Cuánto es 5 + 3?"
   ↓
LLM Razón: "Necesito sumar 5 y 3"
   ↓
LLM Actúa: Invoca sumar_numeros("5 y 3")
   ↓
Tool Retorna: 8
   ↓
LLM Observa: "El resultado es 8"
   ↓
LLM Responde: "5 + 3 = 8"
```

### 3. **LangGraph create_react_agent**

```python
agent = create_react_agent(
    model=llm,
    tools=[suma, resta, multiplicacion, division, wikipedia]
)
```

Reemplaza el `initialize_agent` deprecado de langchain.agents. Es la API **moderna** de LangChain.

### 4. **Ollama Local + num_ctx=8192**

```python
llm = ChatOllama(
    model="llama3.1:8b-instruct-q2_K",
    base_url="http://localhost:11434",
    num_ctx=8192  # ← Previene truncamiento en tool-calling
)
```

`num_ctx=8192` força a Ollama a usar una ventana de contexto mayor, evitando que los prompts de tool-calling se corten. Lección aprendida de CrewAI 101.

---

## 📖 Documentación Relacionada

| Documento | Contenido |
|---|---|
| **MANUAL.md** | Arquitectura interna, detalles técnicos, extensiones avanzadas |
| **QUICKSTART.md** | Guía de 3 minutos (resumida) |
| **EJEMPLOS.md** | Casos de uso, patrones de consulta, combinaciones de herramientas |
| **SOLUCION_ERRORES.md** | Troubleshooting: "Connection refused", "Model not found", etc. |
| **checkpoint/CHECKPOINT_2026-09-18.md** | Snapshot inicial del proyecto (qué se logró, cómo verificar) |

---

## ❓ Preguntas Frecuentes

**P: ¿Por qué temperature=0.0?**  
R: En matemática exacta, necesitamos respuestas deterministas. 0.0 inhibe creatividad; 0.7 (default) la promueve. Para problemas matemáticos, 0.0 es correcto.

**P: ¿Qué pasa si Ollama se desconecta?**  
R: El notebook fallará en celda 5. Asegúrate de que `ollama serve` esté corriendo en otra terminal.

**P: ¿Puedo usar qwen2.5 en lugar de llama3.1?**  
R: Sí, edita `config.ini` → `model_name = qwen2.5:7b`. **Importante**: qwen2.5 con tool-calling puede truncar sin `num_ctx=8192` (ya incluido en el código).

**P: ¿Cómo agregó una nueva herramienta?**  
R: Define una función con `@tool`, agrégala a la lista `tools = [...]` en la celda de creación del agente. Ver ejercicio de potencia en celda 13 para un ejemplo.

**P: ¿Funciona sin Wikipedia?**  
R: Sí. Wikipedia es opcional. Si `pip install wikipedia` falla, comenta la línea en celda 7b y quita `wikipedia_tool` de la lista de tools.

---

## 🐛 Troubleshooting Rápido

| Síntoma | Causa | Solución |
|---|---|---|
| `ConnectionError: Connection refused` | Ollama no está corriendo | Ejecuta `ollama serve` en otra terminal |
| `Model not found: llama3.1:8b` | Modelo no descargado | `ollama pull llama3.1:8b-instruct-q2_K` |
| `UnicodeDecodeError` al leer config.ini | Encoding incorrecto | Ya está manejado: `encoding='utf-8'` en celda 3 |
| `ValueError: Invalid response from LLM` | Truncamiento de contexto | Verificado: `num_ctx=8192` ya está en celda 5 |

Para más detalles, ver **SOLUCION_ERRORES.md**.

---

## 📊 Performance

**Hardware objetivo**: Laptop RTX 3050 + i5 + 20 GB RAM

- **Latencia por consulta**: ~2-5 segundos (depende de complejidad de herramientas invocadas)
- **Memory footprint**: ~2-3 GB (LLM cargado + espacio de trabajo)
- **Modelo usado**: llama3.1:8b-instruct-q2_K (cuantizado a Q2, ~5 GB)

---

## 📝 Licencia y Atribución

Proyecto derivado de IBM Skills Network notebook "AI-Math-Assistant Tool Calling.ipynb" (134 celdas, inglés, cloud LLMs).

**Adaptación**: 
- Versión local con Ollama (no cloud)
- Condensada a 14 celdas (solo lo esencial)
- 100% traducida al español
- Configuración parametrizada

---

## 🔗 Referencias

- **LangChain Tool Calling**: https://python.langchain.com/docs/concepts/tools/
- **LangGraph ReAct Agent**: https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/
- **Ollama**: https://ollama.ai
- **Wikipedia API**: https://en.wikipedia.org/w/api.php

---

**Última actualización**: 2026-09-18  
**Ambiente**: Python 3.14 (env-llm-314) | **LLM**: Ollama llama3.1:8b local | **Framework**: LangChain 0.3.23 + LangGraph 0.6.1
