# MANUAL TÉCNICO: CrewAI 101 - Ejecución Paso a Paso

## Verificación Previa

### 1. Ollama Ejecutándose

```powershell
# Abre PowerShell como Administrador
ollama serve

# En otra ventana, verifica el modelo
ollama list
```

**Salida esperada:**
```
NAME                    ID              SIZE    MODIFIED
qwen2.5:7b             abc123...       4.3GB   2 days ago
```

### 2. Python 3.13 (env-llm-ia) — OBLIGATORIO

⚠️ **NO usar Python 3.14.** Razón: tiktoken/regex sin wheels para cp314

```powershell
# Verifica versión
C:\workspace-vc\env-llm-ia\Scripts\python.exe --version

# Salida esperada: Python 3.13.x
```

## Instalación Detallada de Dependencias

### Paso 1: Instalar desde requirements.txt

```powershell
cd "C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\06 CrewAI 101 - Building Multi-Agent AI Systems"

# Instalar (usa env-llm-ia, NO env-llm-314)
C:\workspace-vc\env-llm-ia\Scripts\python.exe -m pip install -r requirements.txt

# Verificar
C:\workspace-vc\env-llm-ia\Scripts\python.exe -c "import crewai; print('✅ CrewAI instalado')"
```

### Paso 2: Configurar config.ini (Opcional)

Si usas Serper para búsqueda web:
notepad .env
```

### Paso 2: Instalar Dependencias Principales

```powershell
# Activar entorno
C:\workspace-vc\env-llm-314\Scripts\activate

# Instalar langchain
pip install langchain==0.3.20

# Instalar crewai
pip install crewai==0.80.0

# Instalar integración con comunidad
pip install langchain-community==0.3.19

# Instalar herramientas de crewai
pip install crewai-tools==0.38.0

# Instalar Ollama para langchain
pip install langchain-ollama==0.2.0

# Instalar python-dotenv para variables de entorno
pip install python-dotenv
```

### Paso 3: Verificar Instalación

```python
# Abrir Python interactivo
C:\workspace-vc\env-llm-314\Scripts\python.exe

# Ejecutar en la consola Python:
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool
from langchain_ollama import OllamaLLM

print("✓ Todas las librerías importadas correctamente")
exit()
```

## Ejecución del Notebook

### Opción 1: Jupyter Notebook (Recomendado)

```powershell
# Activar entorno
C:\workspace-vc\env-llm-314\Scripts\activate

# Instalar jupyter si no está instalado
pip install jupyter

# Iniciar Jupyter
jupyter notebook

# Selecciona el kernel "Python 3.14 (env-llm-314)"
# Navega a la carpeta y abre el notebook
```

**En el notebook, ejecuta celdas en este orden:**

1. **Celda de Setup** - Configuración de entorno
2. **Celda de Instalación de Librerías** - Instala dependencias
3. **Celda de Imports** - Carga librerías
4. **Celda de SerperDevTool** - (Opcional) Configura búsqueda web
5. **Celda de LLM** - Configura Ollama
6. **Celda de Agentes** - Define agentes
7. **Celda de Tareas** - Define tareas
8. **Celda de Crew** - Configura crew
9. **Celda de Ejecución** - Ejecuta `crew.kickoff()`
10. **Celdas de Análisis** - Analiza resultados

### Opción 2: VS Code

```powershell
# Instalar extensión Jupyter en VS Code
# Ext ID: ms-toolsai.jupyter

# Abre el archivo .ipynb
# Selecciona kernel: "Python 3.14 env-llm-314"
# Ejecuta celda por celda con Shift+Enter
```

### Opción 3: Línea de Comandos (Sin UI)

```powershell
# Convertir notebook a script Python
jupyter nbconvert --to script "CrewAI 101 - Multi-Agent AI Systems.ipynb"

# Ejecutar script
C:\workspace-vc\env-llm-314\Scripts\python.exe "CrewAI 101 - Multi-Agent AI Systems.py"
```

## Puntos Críticos de Ejecución

### Punto 1: Inicialización del LLM

```python
from crewai import LLM

llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434",
    temperature=0.7,
    max_tokens=2000,
)
# ✓ Debe imprimir: "✓ LLM configurado con Ollama local"
```

**Si falla:** Verifica que Ollama está ejecutándose en otra terminal.

### Punto 2: Creación de Agentes

```python
from crewai import Agent

research_agent = Agent(
    role='Analista Investigador Senior',
    goal='Descubrir información de vanguardia...',
    backstory="""Eres un investigador experto...""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=research_tools
)
# ✓ Debe imprimir: "✓ Agente Investigador creado exitosamente"
```

**Si falla:** Verifica que el LLM está correctamente inicializado.

### Punto 3: Creación de Tareas

```python
from crewai import Task

research_task = Task(
    description="Analiza los principales desarrollos en {topic}...",
    agent=research_agent,
    expected_output="Un reporte exhaustivo sobre {topic}..."
)
# ✓ Debe imprimir: "✓ Tarea de Investigación creada"
```

### Punto 4: Configuración del Crew

```python
from crewai import Crew, Process

crew = Crew(
    agents=[research_agent, writer_agent],
    tasks=[research_task, writer_task],
    process=Process.sequential,
    verbose=True 
)
# ✓ Debe imprimir: "✓ Crew configurado con agentes y tareas"
```

### Punto 5: Ejecución Principal

```python
result = crew.kickoff(inputs={"topic": "avances recientes en inteligencia artificial generativa"})
# ⏳ Esto puede tardar 2-10 minutos dependiendo del modelo
# ✓ Verifica verbose output: debe mostrar ejecución de cada agente/tarea
```

## Monitoreo de Ejecución

### Ver Logs en Tiempo Real

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Estructura de Logs Esperada

```
2026-09-13 14:23:45 - crewai - INFO - Iniciando Crew...
2026-09-13 14:23:46 - crewai.agent - INFO - Analista Investigador Senior ejecutando...
2026-09-13 14:25:12 - crewai.agent - INFO - Estratega de Contenido Tecnológico ejecutando...
2026-09-13 14:26:45 - crewai - INFO - ¡Crew completado exitosamente!
```

## Análisis de Resultados

### Acceder a Salidas

```python
# Salida final del último agente
final_output = result.raw
print(final_output)

# Salidas individuales por tarea
research_output = result.tasks_output[0].raw
writer_output = result.tasks_output[1].raw

# Métricas de tokens
print(f"Tokens totales: {result.token_usage.total_tokens}")
print(f"Tokens de prompt: {result.token_usage.prompt_tokens}")
print(f"Tokens de completación: {result.token_usage.completion_tokens}")
```

### Guardar Resultados

```python
# Guardar en archivo
with open("resultado.txt", "w", encoding="utf-8") as f:
    f.write("INVESTIGACIÓN\n")
    f.write("="*70 + "\n")
    f.write(result.tasks_output[0].raw + "\n\n")
    f.write("ARTÍCULO\n")
    f.write("="*70 + "\n")
    f.write(result.tasks_output[1].raw + "\n")

print("✓ Resultado guardado en resultado.txt")
```

## Cambiar Parámetros

### Cambiar Temperatura

```python
# Menos creativo, más determinista
llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434",
    temperature=0.3,  # ← Cambiar aquí
    max_tokens=2000,
)

# Más creativo
llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434",
    temperature=0.9,  # ← Cambiar aquí
    max_tokens=2000,
)
```

### Cambiar Modelo

```python
# Para usar Llama 2
llm = LLM(
    model="ollama/llama2",  # ← Cambiar aquí
    base_url="http://localhost:11434",
    temperature=0.7,
    max_tokens=2000,
)

# Para usar Mistral
llm = LLM(
    model="ollama/mistral",  # ← Cambiar aquí
    base_url="http://localhost:11434",
    temperature=0.7,
    max_tokens=2000,
)
```

### Cambiar Tema de Investigación

```python
# Tema 1: Tecnología
result = crew.kickoff(inputs={"topic": "IA generativa en 2025"})

# Tema 2: Ciencia
result = crew.kickoff(inputs={"topic": "descubrimientos en computación cuántica"})

# Tema 3: Sustentabilidad
result = crew.kickoff(inputs={"topic": "energías renovables"})
```

## Troubleshooting Avanzado

### Error: "Module not found: langchain_ollama"

```powershell
# Solución: Instalar versión correcta
pip uninstall langchain-ollama
pip install langchain-ollama==0.2.0
```

### Error: "Connection refused" (Ollama)

```powershell
# Verificar que Ollama está ejecutándose
PS C:\> netstat -ano | findstr 11434

# Si no hay resultado, inicia Ollama
ollama serve --host 127.0.0.1:11434
```

### Error: "Timeout" durante ejecución

```python
# Aumentar timeout
llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434",
    temperature=0.7,
    max_tokens=2000,
    request_timeout=120  # Aumentar a 120 segundos
)
```

### Error: "OutOfMemory" en Ollama

```powershell
# Reducir carga en Ollama
# Opción 1: Usar modelo más pequeño
ollama pull llama2:7b

# Opción 2: Aumentar memoria disponible
ollama serve --memory 8000

# Opción 3: Reducir max_tokens en config
max_tokens = 1000
```

## Estadísticas Esperadas

### Tiempo de Ejecución

| Modelo | Duración Esperada | GPU | CPU |
|--------|------------------|-----|-----|
| qwen2.5:7b | 3-5 minutos | RTX 3050 | i5-10400 |
| llama2 | 2-4 minutos | RTX 3050 | i5-10400 |
| mistral | 4-6 minutos | RTX 3050 | i5-10400 |

### Consumo de Tokens

| Componente | Típico |
|-----------|--------|
| Prompt de investigación | 500-800 |
| Respuesta de investigación | 1000-1500 |
| Prompt de escritura | 800-1200 |
| Respuesta de escritura | 800-1200 |
| **Total** | **3100-4700** |

## Scripts de Automatización

### Script: Ejecutar Múltiples Temas

```python
# ejecutar_temas.py
from crewai import Crew, Process, Agent, Task, LLM
from datetime import datetime
import json

temas = [
    "inteligencia artificial generativa",
    "computación cuántica",
    "energías renovables",
    "ciberseguridad",
    "biotecnología"
]

resultados = {}

for tema in temas:
    print(f"\n{'='*70}")
    print(f"Investigando: {tema}")
    print(f"{'='*70}")
    
    result = crew.kickoff(inputs={"topic": tema})
    
    resultados[tema] = {
        "timestamp": datetime.now().isoformat(),
        "articulo": result.raw,
        "tokens": result.token_usage.total_tokens
    }
    
    # Guardar resultado individual
    with open(f"resultado_{tema.replace(' ', '_')}.txt", "w", encoding="utf-8") as f:
        f.write(result.raw)

# Guardar resumen
with open("resumen_temas.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print("\n✓ Todos los temas procesados")
```

### Script: Monitoreo de Recursos

```python
# monitorear.py
import psutil
import ollama

def monitorear_ollama():
    try:
        # Conectar a Ollama
        client = ollama.Client(host='http://localhost:11434')
        
        # Obtener modelos cargados
        response = client.list()
        
        print("Modelos disponibles:")
        for model in response.models:
            print(f"  - {model.name}")
        
        # Monitorear memoria del sistema
        memory = psutil.virtual_memory()
        print(f"\nMemoria del Sistema:")
        print(f"  Usado: {memory.percent}%")
        print(f"  Disponible: {memory.available / (1024**3):.2f} GB")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    monitorear_ollama()
```

---

**Última actualización:** 2026-09-13  
**Versión:** 1.0  
**Estado:** ✅ Funcional
