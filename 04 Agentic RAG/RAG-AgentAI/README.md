# RAG-AgentAI: Agente IA de Recuperación Aumentada (100% Local)

**Estado:** ✅ Listo para usar | **Lenguaje:** Español | **LLM Local:** Ollama | **Base de Datos:** ChromaDB Nativo | **Modo:** 🔒 100% Offline (sin HuggingFace)

Agente IA que responde preguntas basándose **SOLO** en documentos que subes. Funciona **100% localmente** (sin cloud), con interacción completamente en español, **sin ninguna llamada saliente a HuggingFace o proveedores externos** — solo Ollama local + ChromaDB local + Docling con modelos pre-cacheados.

---

## 🚀 Inicio Rápido (5 minutos)

### 1. Requisitos previos ✅
- Windows 11 con Python 3.13 en `C:\workspace-vc\env-llm-ia`
- Docker Desktop (para Chroma)
- Ollama instalado

### 2. Instalación

**Opción A: Automática (recomendado)**
```powershell
# PowerShell en C:\Claude\dev-ia\RAG-AgentAI
powershell -ExecutionPolicy Bypass -File INSTALL.ps1
```

**Opción B: Manual**
```powershell
# 1. Activa environment
C:\workspace-vc\env-llm-ia\Scripts\activate

# 2. Instala dependencias
pip install -r requirements.txt

# 3. Valida que todo está correcto
python validate_smoke_test.py
```

### 3. Inicia la app
```powershell
python app.py
# Abre: http://127.0.0.1:5020
```

---

---

## ✨ NUEVO — Tres Características Adicionales (2026-09-09)

Acaba de ser integradas tres mejoras mayores a la interfaz:

### 📤 Feature 1: Cargar y Optimizar Documentos
- **Ubicación:** Tab "📚 Explorar Documentos" (abajo)
- **Qué hace:** Subir PDFs/DOCX con control por-documento de OCR + títulos personalizados
- **Ventaja:** Controla OCR sin modificar config.ini. Indexa texto-solo 3-5x más rápido
- **Comando rápido:** Upload → uncheck OCR (opcional) → enter title (opcional) → "📥 Indexar documento(s)"

### ✅ Feature 2: Usar TODAS las Colecciones
- **Ubicación:** Tab "❓ Consultar Colecciones" (arriba)
- **Qué hace:** Checkbox para seleccionar TODAS las colecciones de un clic
- **Ventaja:** Búsqueda rápida sin multi-select manual
- **Comando rápido:** Check "✅ Usar TODAS las colecciones" → pregunta → "Enviar ❓"

### 🩺 Feature 3: Estado de ChromaDB
- **Ubicación:** Tab "❓ Consultar Colecciones" (abajo)
- **Qué hace:** Panel de salud en vivo con heartbeat, host:port, colecciones, chunks
- **Ventaja:** Monitor sin logs, verifica indexación, troubleshoot sin terminal
- **Comando rápido:** Click "🔄 Verificar salud" → ver estado ✅/❌ + tabla de colecciones

**📖 Documentación de Nuevas Features:**
- **[SETUP_3FEATURES.md](SETUP_3FEATURES.md)** — Guía completa: qué habilita cada feature, cómo usarlas, troubleshooting
- **[checkpoint/CHECKPOINT_20260909_3FEATURES.md](checkpoint/CHECKPOINT_20260909_3FEATURES.md)** — Detalles técnicos, code changes, testing

---

## 📚 Documentación

> **Lee esto antes de usar la app**

1. **[SETUP.md](SETUP.md)** — 🔧 Cómo preparar el entorno (Ollama, Chroma, modelos)
   - Paso a paso para Windows
   - Troubleshooting de conexión
   - Verificación de recursos

2. **[OPERACION_OFFLINE.md](OPERACION_OFFLINE.md)** — 🔒 **Cómo funciona offline (sin HuggingFace)**
   - Setup de modelos locales (una sola vez)
   - Verificación de operación 100% local
   - Troubleshooting si aparecen errores de red
   - **Leer si quieres entender cómo eliminamos la dependencia de HuggingFace**

3. **[MANUAL.md](MANUAL.md)** — 📖 Guía de uso completa
   - Interfaz Gradio
   - Los 3 agentes (relevancia, investigación, verificación)
   - Cómo optimizar parámetros
   - FAQ

4. **[FLUJO_COMPLETO.md](FLUJO_COMPLETO.md)** — 🔄 Explica qué sucede en cada fase
   - Qué hace Docling + GPU (parsing)
   - Cómo ChromaDB almacena datos
   - Dónde entra Ollama (embeddings + LLM)
   - Cómo monitorear cada componente

5. **[MONITORING_GUIDE.md](MONITORING_GUIDE.md)** — 👁️ Observa en vivo lo que está pasando
   - Setup de 4 terminales (Ollama, ChromaDB, App, Logs)
   - Casos de prueba paso a paso
   - Qué esperar en cada terminal
   - Troubleshooting y rendimiento esperado
   - **Comienza aquí si quieres ver todo funcionando**

6. **[ARCHITECTURE_DETAILED.md](ARCHITECTURE_DETAILED.md)** — 🏗️ Arquitectura técnica
   - Diagrama de flujo
   - Componentes y cómo trabajan
   - Data flow detallado
   - Decisiones de diseño

---

## 🎯 ¿Cómo funciona?

```
1. Subes documentos (PDF, DOCX, TXT, MD)
           ↓
2. El agente busca información relevante (BM25 + embeddings vectoriales)
           ↓
3. Tres agentes IA trabajan en paralelo:
   a) RelevanceChecker: "¿Puedo responder esto?"
   b) ResearchAgent: "Aquí está la respuesta"
   c) VerificationAgent: "¿Está soportada?"
           ↓
4. Recibe respuesta verificada en español
```

---

## ⚙️ Configuración

Todo en **`config.ini`** — no necesitas tocar código:

```ini
[ollama]
base_url = http://localhost:11434              # Endpoint de Ollama
text_model = qwen2.5:7b-instruct-q4_K_M       # LLM (cambiar por otro si quieres)
temperature = 0.1                             # Determinístico (0.0) vs Creativo (1.0)

[chroma]
host = localhost                              # Donde corre Chroma Docker
port = 8000                                   # Puerto
collection_name = rag_agentai_documents       # Nombre de la BD

[rag]
vector_search_k = 10                          # Documentos a buscar
max_context_docs = 5                          # Documentos al LLM
```

Ver **[MANUAL.md](MANUAL.md)** sección "Parámetros de Configuración" para detalles.

---

## ✨ Características

✅ Documentos: PDF, DOCX, TXT, Markdown (con OCR)  
✅ Búsqueda híbrida: palabras clave + semántica  
✅ Interacción: 100% en español  
✅ Verificación automática: Valida que la respuesta esté en los docs  
✅ Logs detallados: Debugging fácil  
✅ Interfaz web: Gradio (hermosa y responsiva)  
✅ Configuración externalizada: Cambia parámetros sin código  

---

## 📊 Rendimiento

| Acción | Tiempo | GPU |
|--------|--------|-----|
| Carga de PDF (primera vez) | 10-60 seg | Depende tamaño |
| Búsqueda de documentos | <1 seg | CPU |
| LLM responde pregunta | 10-30 seg | RTX 3050 (6GB) |
| **Total** | **20-60 seg** | **Típico** |

Más rápido si:
- Usas GPU más potente (RTX A4500)
- Usas modelo más pequeño (qwen2.5:3b)
- Reduces `vector_search_k` en config.ini

---

## 🔍 Ejemplos de preguntas

```
Sube: google-2024-environmental-report.pdf
Pregunta: "¿Cuál es la eficiencia PUE en 2022?"
→ Respuesta: "Según el documento, la eficiencia PUE fue de 1.12 en 2022"

Sube: tu_contrato.pdf
Pregunta: "¿Cuáles son los términos de pago?"
→ Respuesta: "[Extrae término específico del documento]"
```

---

## 🛠️ Troubleshooting

| Problema | Solución |
|----------|----------|
| "Cannot connect to Ollama" | Ejecuta `ollama serve` en otra terminal |
| "Cannot connect to Chroma" | Ejecuta `docker run -d -p 8000:8000 chromadb/chroma:latest` |
| "Model not found" | Ejecuta `ollama pull qwen2.5:7b-instruct-q4_K_M` |
| Lento | Reduce `vector_search_k` en config.ini, o usa modelo 3b |
| Respuestas incompletas | Aumenta `vector_search_k` o `max_context_docs` |

Ver **[SETUP.md](SETUP.md)** sección Troubleshooting para más detalle.

---

## 📋 Checklist para empezar

- [ ] Python 3.13 verificado
- [ ] Dependencies instaladas (`requirements.txt`)
- [ ] Ollama corriendo (`ollama list` muestra modelos)
- [ ] Chroma Docker corriendo (puerto 8000)
- [ ] Smoke test pasó (`python validate_smoke_test.py`)
- [ ] Leíste [SETUP.md](SETUP.md)
- [ ] Ejecutaste `python app.py`
- [ ] Abriste http://127.0.0.1:5020

---

## 📁 Estructura del proyecto

```
RAG-AgentAI/
├── app.py                    # Interfaz Gradio (punto de entrada)
├── config.ini                # Configuración (Ollama, Chroma, modelos)
├── requirements.txt          # Dependencias Python
├── validate_smoke_test.py    # Script de validación
├── INSTALL.ps1              # Script de instalación automática
│
├── agents/                   # Los 3 agentes (LLM-basados)
│   ├── relevance_checker.py  # ¿Puedo responder?
│   ├── research_agent.py     # Genera respuesta
│   ├── verification_agent.py # ¿Está verificada?
│   └── workflow.py           # Orquestación
│
├── retriever/                # Búsqueda de documentos
│   └── builder.py            # BM25 + Chroma + EnsembleRetriever
│
├── document_processor/       # Procesamiento de archivos
│   └── file_handler.py       # Docling (PDF/DOCX parsing)
│
├── config/                   # Configuración
│   └── settings.py           # Parser de config.ini
│
├── utils/                    # Utilidades
│   └── logging.py            # Loguru (logs)
│
├── logs/                     # Logs (se crean automáticamente)
│   └── rag_agentai.log
│
├── checkpoint/               # Versión y milestones
│   └── CHECKPOINTS.md
│
├── README.md                 # Este archivo
├── SETUP.md                  # Guía de setup
├── MANUAL.md                 # Guía de uso
└── ARCHITECTURE.md           # Arquitectura técnica
```

---

## 📞 Soporte

- **Logs:** `logs/rag_agentai.log` (lee esto si hay errores)
- **Troubleshooting:** [SETUP.md](SETUP.md) → Sección "Troubleshooting"
- **Configuración:** [MANUAL.md](MANUAL.md) → Sección "Parámetros"
- **Arquitectura:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🎓 Aprende cómo funciona

1. Lee **[MANUAL.md](MANUAL.md)** sección "Los 3 Agentes"
2. Mira el código en `agents/` (está comentado)
3. Revisa logs en `logs/rag_agentai.log` mientras haces preguntas
4. Experimenta cambiando `config.ini`

---

**¡Listo!** Sigue [SETUP.md](SETUP.md) para los próximos pasos.

