# 🚀 GETTING STARTED — RAG-AgentAI

**Versión:** 1.0  
**Estado:** ✅ Listo para ejecutar  
**Ubicación:** `C:\Claude\dev-ia\RAG-AgentAI`  
**Python:** 3.13 (`C:\workspace-vc\env-llm-ia`)  

---

## ⚡ Los primeros 5 minutos

### Paso 1: Copia y pega en PowerShell

```powershell
# Abre PowerShell en la carpeta del proyecto
cd C:\Claude\dev-ia\RAG-AgentAI

# Ejecuta el instalador automático
powershell -ExecutionPolicy Bypass -File INSTALL.ps1
```

**Esto:**
- ✅ Instala todas las dependencias Python
- ✅ Descarga los modelos Ollama (si quieres)
- ✅ Verifica Chroma Docker
- ✅ Ejecuta smoke test
- ⏱️ Tarda ~10-15 minutos (primera vez)

### Paso 2: Inicia la app

```powershell
# En la misma terminal:
python app.py

# Esperado:
# INFO: Uvicorn running on http://127.0.0.1:5020
```

### Paso 3: Abre el navegador

```
http://127.0.0.1:5020
```

**¡Listo!** Ya puedes:
- 📤 Subir documentos
- 💬 Hacer preguntas en español
- 📝 Ver respuestas verificadas

---

## 📚 Documentación Rápida

| Necesitas | Lee esto |
|-----------|----------|
| **Instalación** | [SETUP.md](SETUP.md) |
| **Cómo usar la app** | [MANUAL.md](MANUAL.md) |
| **Cómo funciona internamente** | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Cambiar parámetros** | [MANUAL.md](MANUAL.md) → Sección "Parámetros de Configuración" |
| **Problemas/Errores** | [SETUP.md](SETUP.md) → Sección "Troubleshooting" |

---

## 🔍 ¿Qué tengo que hacer?

### ✅ Instalación (una sola vez)

```powershell
# 1. PowerShell como admin
cd C:\Claude\dev-ia\RAG-AgentAI

# 2. Ejecuta INSTALL.ps1
powershell -ExecutionPolicy Bypass -File INSTALL.ps1

# Verifica:
python validate_smoke_test.py  # Debe pasar todos los tests
```

### ✅ Antes de cada uso

```powershell
# 1. Abre dos terminales

# Terminal 1: Ollama (si no está ejecutándose)
ollama serve

# Terminal 2: Chroma Docker (si no está ejecutándose)
docker run -d -p 8000:8000 chromadb/chroma:latest

# Terminal 3 (la que usas): La app
cd C:\Claude\dev-ia\RAG-AgentAI
C:\workspace-vc\env-llm-ia\Scripts\activate
python app.py
```

---

## 🎯 Ejemplo de uso completo

### Entrada

```
URL: http://127.0.0.1:5020

1. Selecciona "Cargar Ejemplo" → "Google 2024 Environmental Report"
2. Pregunta: "¿Cuál es la eficiencia PUE en 2022?"
3. Presiona: "Enviar"
```

### Proceso (interno, espera ~15-30 seg)

```
1. Recupera documentos relevantes (BM25 + embeddings vectoriales)
2. RelevanceChecker: ¿Puedo responder esto? → "CAN_ANSWER" ✓
3. ResearchAgent: Genera respuesta basada en documentos → "La eficiencia PUE..."
4. VerificationAgent: ¿Está verificada? → "Soportado: SI" ✓
```

### Salida

```
RESPUESTA:
"Según el documento de Google 2024, la eficiencia PUE fue de 1.12 en 2022,
demostrando una mejora significativa respecto a años anteriores..."

REPORTE DE VERIFICACIÓN:
Soportado: SI
Relevante: SI
Resumen: La respuesta está explícitamente mencionada en el documento Google
Environmental Report 2024.
```

---

## 🛠️ Comando rápido si algo falla

```powershell
# Verificar Ollama
ollama list  # Debe mostrar: mxbai-embed-large y qwen2.5:7b-instruct-q4_K_M

# Verificar Chroma
curl http://localhost:8000/api/v1  # Debe devolver HTTP 200

# Verificar instalación
python validate_smoke_test.py  # Debe pasar todos los tests

# Ver logs si hay error
Get-Content logs/rag_agentai.log -Tail 50  # Últimas 50 líneas
```

---

## 📊 Checklist para validar

```
BEFORE RUNNING:
☐ Python 3.13 verificado: C:\workspace-vc\env-llm-ia\Scripts\python.exe --version
☐ requirements.txt instalados: pip list | Select-String "langchain\|torch\|chromadb"
☐ Ollama corriendo: ollama list (debe mostrar 2 modelos)
☐ Chroma Docker corriendo: docker ps (debe estar en puerto 8000)
☐ Smoke test pasa: python validate_smoke_test.py

AFTER RUNNING:
☐ URL http://127.0.0.1:5020 abre sin error
☐ Carga un ejemplo
☐ Haces una pregunta
☐ Esperas ~15-30 seg
☐ Ves respuesta + reporte de verificación
☐ Logs en logs/rag_agentai.log muestra "✓ Pipeline completado exitosamente"
```

---

## 🆘 Errores Más Comunes

### Error: "Cannot connect to Ollama"
```powershell
# Solución:
ollama serve  # En otra terminal
```

### Error: "Cannot connect to Chroma"
```powershell
# Solución:
docker run -d -p 8000:8000 chromadb/chroma:latest
```

### Error: "Model not found"
```powershell
# Solución:
ollama pull mxbai-embed-large
ollama pull qwen2.5:7b-instruct-q4_K_M
```

### Error: "ModuleNotFoundError: torch"
```powershell
# Solución:
C:\workspace-vc\env-llm-ia\Scripts\activate
pip install -r requirements.txt --force-reinstall
```

Ver [SETUP.md](SETUP.md) para más troubleshooting.

---

## 💡 Próximos pasos después de validar

1. **Lee [MANUAL.md](MANUAL.md)** — Entiende cómo funciona
2. **Sube tus propios documentos** — PDF, DOCX, etc.
3. **Cambia parámetros en config.ini** — Experimenta con temperature, modelos, etc.
4. **Monitorea logs** — Abre `logs/rag_agentai.log` para ver qué hace internamente

---

## 📁 Estructura de carpetas

```
C:\Claude\dev-ia\RAG-AgentAI/
├── README.md                    ← Lee primero
├── GETTING_STARTED.md          ← Este archivo
├── SETUP.md                    ← Cómo instalar
├── MANUAL.md                   ← Cómo usar
├── ARCHITECTURE.md             ← Cómo funciona
│
├── INSTALL.ps1                 ← Script automático de instalación
├── validate_smoke_test.py      ← Script de validación
├── app.py                      ← EJECUTABLE (python app.py)
├── config.ini                  ← CONFIGURACIÓN
├── requirements.txt            ← Dependencies
│
├── agents/                     ← 3 agentes IA
├── retriever/                  ← Búsqueda de documentos
├── document_processor/         ← Parsing de archivos
├── config/                     ← Configuración
├── utils/                      ← Logging
├── logs/                       ← Logs (se crean automáticamente)
└── checkpoint/                 ← Versión y milestones
```

---

## ✅ Validación final

**Si pasaste todos los checks del Checklist arriba, ¡estás listo!**

Ahora puedes:
- ✅ Usar la app normalmente
- ✅ Leer [MANUAL.md](MANUAL.md) para aprender más
- ✅ Cambiar config.ini para optimizar
- ✅ Subir tus propios documentos

**¿Dudas?** Ve a [SETUP.md](SETUP.md) o [MANUAL.md](MANUAL.md).

---

**Creado:** 2026-09-05 | **Versión:** RAG-AgentAI 1.0 | **Python:** 3.13
