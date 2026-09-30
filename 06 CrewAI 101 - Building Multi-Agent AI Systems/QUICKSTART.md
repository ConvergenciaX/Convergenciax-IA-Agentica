# 🚀 QUICKSTART: CrewAI con Ollama (Ejecución Rápida)

## Requisitos Previos (1 minuto)

### 1. Ollama Ejecutándose

```powershell
# Abre PowerShell y ejecuta:
ollama serve
```

Deja esta ventana abierta. Ollama escuchará en `http://localhost:11434`

### 2. Python 3.14+ Instalado

```powershell
# En otra ventana de PowerShell, verifica:
C:\workspace-vc\env-llm-314\Scripts\python.exe --version
# Output esperado: Python 3.14.x
```

## Instalación (2 minutos)

### Paso 1: Instalar Dependencias

```powershell
# Activar entorno
C:\workspace-vc\env-llm-314\Scripts\activate

# Instalar paquetes
pip install crewai==0.80.0 langchain==0.3.20 langchain-ollama==0.2.0 crewai-tools==0.38.0 python-dotenv
```

### Paso 2: Descargar Modelo (Si no lo tienes)

```powershell
# En una terminal con Ollama ejecutándose
ollama pull qwen2.5:7b

# O usa otro modelo
ollama pull llama2
```

## Ejecución (Opciones)

### Opción 1: Script Directo (Más Simple)

```powershell
# Opción A: Ejecución por defecto
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py

# Opción B: Con tema personalizado
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --topic "energías renovables"

# Opción C: Con modelo diferente
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --model llama2 --topic "computación cuántica"

# Opción D: Modo verbose (ver detalles)
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --verbose
```

### Opción 2: Con Script Batch (Windows)

```powershell
# Doble-click en run.bat
# O desde PowerShell:
.\run.bat --topic "tu tema aquí"
```

### Opción 3: Con Script Bash (Linux/Mac)

```bash
chmod +x run.sh
./run.sh --topic "tu tema aquí"
```

## Ejemplos de Ejecución

### Ejemplo 1: Tema por Defecto (IA Generativa)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py
```

**Salida:**
```
════════════════════════════════════════════════════════════════════════════════
🚀 CREWAI 101: CONSTRUYENDO SISTEMAS MULTI-AGENTE CON OLLAMA LOCAL
════════════════════════════════════════════════════════════════════════════════

📂 Cargando configuración...
🔧 Inicializando LLM con Ollama...
✅ LLM configurado exitosamente
   Modelo: qwen2.5:7b
   URL: http://localhost:11434

📋 Creando agentes...
✅ Agente Investigador creado
✅ Agente Escritor creado

[... ejecución continúa ...]

📄 RESULTADO FINAL: ARTÍCULO DE BLOG
════════════════════════════════════════════════════════════════════════════════

[Artículo aquí...]
```

### Ejemplo 2: Tema Personalizado

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --topic "sostenibilidad y cambio climático"
```

### Ejemplo 3: Modelo Diferente + Tema

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --model llama2 --topic "blockchain y criptomonedas"
```

### Ejemplo 4: Temperatura Creativa

```powershell
# Más creativo (temperatura alta)
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --temperature 0.9 --topic "ficción científica"

# Más determinista (temperatura baja)
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --temperature 0.3 --topic "física cuántica"
```

### Ejemplo 5: Modo Verbose (Debugging)

```powershell
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --verbose
```

## Archivos Generados

Después de ejecutar, encontrarás:

```
06 CrewAI 101 - Building Multi-Agent AI Systems/
├── outputs/
│   └── resultado_20260913_142530.txt     ← Resultado guardado
└── logs/
    └── crewai_20260913_142530.log        ← Log de ejecución
```

## Estructura de Salida

El resultado incluye:

1. **Encabezado**: Tema, fecha, modelo usado
2. **Investigación**: Hallazgos y tendencias clave
3. **Artículo**: Contenido final bien estructurado
4. **Estadísticas**: Tokens utilizados

## Referencia Rápida de Argumentos

```
--topic TEXT          Tema a investigar (default: "avances recientes en IA")
--model TEXT          Modelo Ollama (default: "qwen2.5:7b")
--temperature FLOAT   Temperatura 0.0-1.0 (default: 0.7)
--verbose             Mostrar salida detallada
--save                Guardar resultado en archivo (default: True)
-h, --help            Mostrar ayuda
```

## Modelos Disponibles

```
qwen2.5:7b          ⭐ Recomendado (rápido + preciso)
llama2              Equilibrado
neural-chat         Conversacional
mistral:7b          Especializado
codellama           Para código
```

Para instalar otro modelo:
```powershell
ollama pull mistral:7b
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --model mistral:7b
```

## Troubleshooting Rápido

### ❌ "ConnectionError: Failed to connect to Ollama"

**Solución:**
```powershell
# En otra terminal, asegúrate de que Ollama está ejecutándose
ollama serve
```

### ❌ "Model not found"

**Solución:**
```powershell
# Descarga el modelo
ollama pull qwen2.5:7b
```

### ❌ "ModuleNotFoundError: No module named 'crewai'"

**Solución:**
```powershell
# Reinstala las dependencias
C:\workspace-vc\env-llm-314\Scripts\python.exe -m pip install crewai==0.80.0
```

### ⚠️ Ejecución muy lenta

**Soluciones:**
- Usar modelo más pequeño: `--model llama2`
- Reducir temperatura: `--temperature 0.5`
- Verificar recursos del sistema (RAM, GPU)

## Archivos de Configuración

### config.ini

```ini
[ollama]
base_url = http://localhost:11434
model_name = qwen2.5:7b
temperature = 0.7
max_tokens = 2000
```

Edita este archivo para cambiar valores por defecto permanentemente.

### .env (Opcional)

Para usar búsqueda web con Serper:

1. Obtén API key en https://serper.dev
2. Crea archivo `.env`:
   ```
   SERPER_API_KEY=tu_api_key_aqui
   ```
3. El agente ahora usará búsqueda web en tiempo real

## Ejemplos Interesantes

```powershell
# Tema tecnológico
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --topic "tendencias DevOps 2025"

# Tema científico
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --topic "descubrimientos en neurociencia"

# Tema de negocios
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --topic "transformación digital en empresas"

# Tema creativo
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --temperature 0.9 --topic "el futuro de la educación"

# Tema técnico preciso
C:\workspace-vc\env-llm-314\Scripts\python.exe crewai_ollama.py --temperature 0.3 --topic "protocolos criptográficos"
```

## Próximos Pasos

1. **Explorar modelos:** Instala y prueba diferentes modelos
2. **Configurar Serper:** Habilita búsqueda web para información actual
3. **Extender el sistema:** Agrega más agentes o tareas
4. **Automatizar:** Crea scripts para procesar múltiples temas

## Documentación Completa

Para información más detallada:
- `README.md` — Guía completa de usuario
- `MANUAL.md` — Guía técnica detallada
- `crewai_ollama.py` — Código fuente comentado

---

**¡Listo! Ahora puedes ejecutar CrewAI con Ollama local directamente desde la línea de comandos. 🚀**
