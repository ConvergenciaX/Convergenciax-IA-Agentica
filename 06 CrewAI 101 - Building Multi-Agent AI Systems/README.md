# CrewAI 101: Construyendo Sistemas Multi-Agente (Versión Ollama Local)

## Descripción General

Este es un tutorial práctico sobre **CrewAI**, un framework de vanguardia para crear y gestionar equipos de agentes autónomos de IA. En este laboratorio, construiremos un pipeline de creación de contenido impulsado por GenAI que transforma investigación bruta en publicaciones de blog pulidas e informativas.

**Características principales:**
- ✅ 100% en español (prompts, instrucciones y salidas)
- ✅ Ollama local (sin dependencia de APIs cloud)
- ✅ Sistema multiagente secuencial (Investigador → Escritor)
- ✅ Configuración parametrizable vía `config.ini`
- ✅ Logging estructurado
- ✅ Ejercicios de extensión incluidos

## Requisitos Previos

### 1. Ollama Local Instalado y Ejecutándose

```bash
# En Windows
ollama serve

# En otra terminal, verifica que Ollama está corriendo
ollama list
```

**Modelos recomendados:**
- `qwen2.5:7b` (recomendado: velocidad y calidad balanceadas)
- `llama2` (alternativa)
- `neural-chat`

Si no tienes el modelo descargado, instálalo:
```bash
ollama pull qwen2.5:7b
```

### 2. Python 3.13 (env-llm-ia)

⚠️ **IMPORTANTE:** Usar **Python 3.13 (`env-llm-ia`)**, NO 3.14 (`env-llm-314`).  
Razón: `tiktoken` y `regex` no tienen wheels compilados para Python 3.14 en Windows.

```bash
# Verificar versión
C:\workspace-vc\env-llm-ia\Scripts\python.exe --version
# Salida esperada: Python 3.13.x
```

### 3. Entorno Virtual Activado

```bash
# Usar OBLIGATORIAMENTE env-llm-ia (Python 3.13)
C:\workspace-vc\env-llm-ia\Scripts\python.exe -m pip install --upgrade pip
```

## Instalación

### 1. Instalar Dependencias

Ejecuta la celda de instalación en el notebook (segunda sección):

```python
%pip install langchain==0.3.20 | tail -n 1 
%pip install crewai==0.80.0 | tail -n 1
%pip install langchain-community==0.3.19 | tail -n 1 
%pip install crewai-tools==0.38.0 | tail -n 1
%pip install langchain-ollama==0.2.0 | tail -n 1
%pip install python-dotenv | tail -n 1
```

### 2. Configuración (Todo en config.ini)

Todas las configuraciones se leen de `config.ini`. No necesitas `.env`.

**Si usas Serper para búsqueda web:**
1. Edita `config.ini`
2. En sección `[serper]`, agrega tu API key:
   ```ini
   [serper]
   api_key = tu_api_key_aqui
   ```
3. Los agentes ahora tendrán acceso a búsqueda web

## Estructura del Proyecto

```
06 CrewAI 101 - Building Multi-Agent AI Systems/
├── 📓 CrewAI 101 - Multi-Agent AI Systems_LLM_local.ipynb  ⭐ PRINCIPAL
│   └── 8 celdas, 100% español, config.ini integrado, env-llm-ia
├── ⚙️  config.ini                               # Parametrización centralizada
├── 📦 requirements.txt                          # Dependencias Python
├── 📚 README.md                                 # Guía principal (esta)
├── 📖 MANUAL.md                                 # Detalles técnicos
├── 🚀 QUICKSTART.md                             # Inicio en 3 minutos
├── 📋 EJEMPLOS.md                               # 20+ casos de uso
├── 🆘 SOLUCION_ERRORES.md                       # Troubleshooting
├── 📁 checkpoint/                               # Snapshots de estado
│   └── CHECKPOINTS.md
├── 📁 logs/                                     # Directorio de logs (se crea automáticamente)
└── 📁 outputs/                                  # Directorio de salidas (se crea automáticamente)
```

**Nota:** El notebook original `CrewAI 101 - Multi-Agent AI Systems.ipynb` se mantiene como referencia.

## Cómo Ejecutar

### Opción Única: Jupyter Notebook

```bash
# Terminal 1: Inicia Ollama
ollama serve

# Terminal 2: Activa el entorno correcto (Python 3.13, NO 3.14)
C:\workspace-vc\env-llm-ia\Scripts\python.exe -m jupyter notebook

# En el navegador, abre:
# CrewAI 101 - Multi-Agent AI Systems_LLM_local.ipynb

# Ejecuta las celdas secuencialmente (1 → 2 → 3 → ... → 8)
```

**Notas:**
- Usar **env-llm-ia** (Python 3.13), NO env-llm-314
- Ollama DEBE estar ejecutándose en otra terminal
- El notebook está 100% en español
- Todas las configuraciones se leen desde `config.ini`

## Flujo de Ejecución

El notebook incluye estos pasos principales:

### 1. **Setup (Configuración)**
   - Instalar librerías requeridas
   - Configurar variables de entorno
   - Cargar Ollama LLM

### 2. **Agentes (Definición)**
   ```
   - Analista Investigador Senior
     └─ Rol: Recopilar información y analizarla
     └─ Objetivo: Descubrir información de vanguardia
   
   - Estratega de Contenido Tecnológico
     └─ Rol: Escribir contenido atractivo
     └─ Objetivo: Crear artículos bien estructurados
   ```

### 3. **Tareas (Asignación)**
   ```
   Tarea 1: research_task
   └─ Descripción: Analiza desarrollos en {topic}
   └─ Asignado a: research_agent
   
   Tarea 2: writer_task
   └─ Descripción: Crea artículo de blog basado en investigación
   └─ Asignado a: writer_agent
   ```

### 4. **Crew (Orquestación)**
   ```
   Modo: Sequential
   └─ Primero ejecuta research_task
   └─ Luego ejecuta writer_task con salida de research
   └─ Devuelve resultado final
   ```

### 5. **Ejecución**
   ```python
   result = crew.kickoff(inputs={"topic": "tu_tema_aqui"})
   ```

## Ejemplos de Temas a Investigar

```python
# Opción 1: Tecnología
crew.kickoff(inputs={"topic": "avances recientes en inteligencia artificial"})

# Opción 2: Ciencia
crew.kickoff(inputs={"topic": "descubrimientos en computación cuántica"})

# Opción 3: Sustentabilidad
crew.kickoff(inputs={"topic": "energías renovables en 2025"})

# Opción 4: Negocios
crew.kickoff(inputs={"topic": "tendencias de transformación digital"})
```

## Estructura de Salida

Después de ejecutar `crew.kickoff()`, obtendrás:

```
result.raw
├─ Contenido final del último agente (Artículo de Blog)

result.tasks_output[0]
├─ Salida de la tarea de investigación
├─ Descripción de la tarea
└─ Agente que la ejecutó

result.tasks_output[1]
├─ Salida de la tarea de escritura
├─ Descripción de la tarea
└─ Agente que la ejecutó

result.token_usage
├─ total_tokens: Tokens totales usados
├─ prompt_tokens: Tokens de input
└─ completion_tokens: Tokens generados
```

## Configuración del Modelo

### Cambiar Modelo Ollama

Edita la celda de configuración del LLM:

```python
llm = LLM(
    model="ollama/tu_modelo_aqui",  # Cambia esto
    base_url="http://localhost:11434",
    temperature=0.7,
    max_tokens=2000,
)
```

**Modelos disponibles:**
```
qwen2.5:7b      # Recomendado (rápido y preciso)
llama2          # Equilibrado
neural-chat     # Conversacional
mistral:7b      # Especializado
```

### Ajustar Temperatura

```python
temperature=0.5  # Más determinista, menos creativo
temperature=0.7  # Balance (recomendado)
temperature=0.9  # Más creativo, menos preciso
```

## Búsqueda Web (Serper)

### Opción 1: Sin Búsqueda Web (Predeterminado)

El agente usará solo su conocimiento preentrenado. Esto funciona bien para temas generales.

### Opción 2: Con Búsqueda Web

1. Obtén una API key en [serper.dev](https://serper.dev)
2. Copia tu clave en `.env`:
   ```
   SERPER_API_KEY=tu_api_key_aqui
   ```
3. El agente investigador ahora usará búsqueda web en tiempo real

## Logging y Debugging

Los logs se guardan en `logs/crewai.log`:

```
Nivel de log: INFO (configurable en config.ini)
Incluye:
- Inicio/fin de agentes
- Ejecución de tareas
- Errores y advertencias
```

Ver logs en tiempo real:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Ejercicios

El notebook incluye 3 ejercicios para extender el sistema:

### Ejercicio 1: Crear Agente de Redes Sociales
Agrega un tercer agente que cree posts cortos para LinkedIn y Twitter.

### Ejercicio 2: Crear Tarea de Estrategia Social
Define una tarea que genere 2-3 posts para redes sociales basados en el artículo.

### Ejercicio 3: Crew Completo
Integra el nuevo agente al crew y ejecuta con 3 tareas secuenciales.

(Soluciones incluidas en el notebook bajo cada ejercicio)

## Troubleshooting

### Problema: "ConnectionError: Failed to connect to Ollama"

**Solución:**
```bash
# Asegúrate que Ollama está ejecutándose
ollama serve

# Verifica en otra terminal
ollama list

# Si no está respondiendo, reinicia
ollama serve --host 0.0.0.0:11434
```

### Problema: "Model not found"

**Solución:**
```bash
# Descarga el modelo
ollama pull qwen2.5:7b

# Verifica disponibles
ollama list
```

### Problema: "ImportError: No module named 'crewai'"

**Solución:**
```bash
# Reinstala las dependencias
pip install crewai==0.80.0
pip install langchain-ollama==0.2.0
```

### Problema: Notebook lento o timeouts

**Soluciones:**
- Reduce `max_tokens` en config.ini
- Usa un modelo más pequeño (ej. llama2 en lugar de qwen2.5:7b)
- Abre Ollama con más memoria: `ollama serve --memory 8000`

## Extensiones Propuestas

1. **Guardar salida a archivo**
   ```python
   with open("output.txt", "w", encoding="utf-8") as f:
       f.write(result.raw)
   ```

2. **Procesar múltiples temas**
   ```python
   temas = ["IA", "Computación Cuántica", "Sostenibilidad"]
   for tema in temas:
       result = crew.kickoff(inputs={"topic": tema})
   ```

3. **Agregar Procesamiento de PDF**
   ```python
   from crewai_tools import PDFSearchTool
   ```

4. **Modo Jerárquico**
   ```python
   process=Process.hierarchical  # En lugar de sequential
   ```

## Documentación de Referencia

- [CrewAI Docs](https://docs.crewai.com/)
- [LangChain Docs](https://python.langchain.com/)
- [Ollama Docs](https://github.com/ollama/ollama)

## Autor y Atribución

**Versión Original:** Karan Goswami & Kunal Makwana (IBM Skills Network)

**Adaptación a Ollama + Español:** Esta versión ha sido adaptada para:
- Usar Ollama local en lugar de APIs cloud
- 100% interfaz en español
- Configuración parametrizable
- Logging estructurado

## Licencia

Este proyecto educativo sigue los términos de la versión original de IBM Skills Network.

---

**Estado:** ✅ Funcional con Ollama local

**Última actualización:** 2026-09-16

**Ambiente:** Python 3.13 (`env-llm-ia`) — OBLIGATORIO

**Notebook:** `CrewAI 101 - Multi-Agent AI Systems_LLM_local.ipynb` (8 celdas, 100% español)
