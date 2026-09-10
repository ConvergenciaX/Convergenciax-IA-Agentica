# MANUAL — RAG-AgentAI: Guía de Uso y Arquitectura

**Versión:** 1.0  
**Python:** 3.13 (env-llm-ia)  
**Actualizado:** 2026-09-05

> **Antes de usar este manual:** Completa **SETUP.md** primero. Este documento asume que tienes Python, Ollama, Chroma y dependencies instaladas.

---

## 📖 Índice

1. [Inicio Rápido (5 min)](#inicio-rápido)
2. [Interfaz Gradio](#interfaz-gradio)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Parámetros de Configuración](#parámetros-de-configuración)
5. [Workflow de Procesamiento](#workflow-de-procesamiento)
6. [Entendiendo los Logs](#entendiendo-los-logs)
7. [Debugging y Optimización](#debugging-y-optimización)
8. [FAQ](#faq)

---

## 🚀 Inicio Rápido

### Ejecutar la aplicación

```powershell
# 1. Abre PowerShell en C:\Claude\dev-ia\RAG-AgentAI
cd C:\Claude\dev-ia\RAG-AgentAI

# 2. Activa environment
C:\workspace-vc\env-llm-ia\Scripts\activate

# 3. Verifica que Ollama está corriendo
ollama list  # Debería mostrar los dos modelos

# 4. Verifica que Chroma está corriendo
curl http://localhost:8000/api/v1  # HTTP 200

# 5. Inicia la app
python app.py

# Esperado:
# INFO:     Uvicorn running on http://127.0.0.1:5020
```

### Usar la app (interfaz web)

1. Abre navegador: `http://127.0.0.1:5020`
2. Selecciona un **ejemplo** (dropdown "Cargar Ejemplo") O sube tus propios documentos
3. Escribe tu pregunta en español
4. Presiona **"Enviar"**
5. Espera 10-30 segundos (depende de GPU y tamaño de documentos)
6. Verás dos outputs:
   - **Respuesta:** Texto generado por el LLM
   - **Reporte de Verificación:** "Soportado: SI/NO/PARCIAL" + análisis

---

## 🎨 Interfaz Gradio

La interfaz web tiene tres zonas:

### Zona de entrada (izquierda)

```
┌─────────────────────────────────┐
│ 📤 Cargar Documentos            │ ← Sube PDF/DOCX/TXT/MD
│ (click para seleccionar)        │
│                                 │
├─────────────────────────────────┤
│ 📋 Cargar Ejemplo              │ ← Dropdown con ejemplos
│ ▼ [Seleccionar ejemplo...]     │   pre-cargados
│                                 │
├─────────────────────────────────┤
│ 💬 Tu Pregunta                  │ ← Escribe tu pregunta
│ [___________________]           │   en español
│                                 │
│     [Enviar]  [Limpiar]        │ ← Botones
└─────────────────────────────────┘
```

**Formatos de documentos soportados:**
- ✅ `.pdf` (con OCR para imágenes)
- ✅ `.docx` (Word)
- ✅ `.txt` (texto plano)
- ✅ `.md` (Markdown)

### Zona de salida (derecha)

```
┌─────────────────────────────────┐
│ 📝 RESPUESTA                    │
│                                 │
│ [Texto generado por el LLM]     │ ← Respuesta a tu pregunta
│                                 │ (basada en documentos)
├─────────────────────────────────┤
│ ✅ REPORTE DE VERIFICACIÓN     │
│                                 │
│ Soportado: SI/NO/PARCIAL       │ ← ¿Está la respuesta en
│ Relevante: SI/NO               │   los documentos?
│ Resumen: ...                    │
└─────────────────────────────────┘
```

---

## 🏗️ Arquitectura del Sistema

### Flujo general

```
Documento (PDF/DOCX/TXT/MD)
    ↓ [DocumentProcessor + Docling]
Markdown + OCR
    ↓ [MarkdownHeaderTextSplitter]
Chunks (divididos por # headers)
    ↓ [Chroma + OllamaEmbeddings]
Vector Store (BD local con embeddings)
    ↓
┌──────────────────────────────────┐
│ Pregunta del usuario (español)   │
└────────────────┬─────────────────┘
                 ↓
        [3-Agent Workflow]
                 │
    ┌────────────┼────────────┐
    ↓            ↓            ↓
  Node 1       Node 2       Node 3
  Relevancia  Investigación Verificación
  Checker     Agent         Agent
  (temp=0.0)  (temp=0.3)   (temp=0.0)
    │            │            │
    └────────────┼────────────┘
                 ↓
        Respuesta Verificada
    (+ Reporte de Verificación)
```

### Los 3 agentes (nodos del workflow)

#### 1️⃣ RelevanceChecker (Verificador de Relevancia)
- **Rol:** Decide si los documentos pueden responder la pregunta
- **Modelo:** `qwen2.5:7b` (temp=0.0, determinístico)
- **Entrada:** Pregunta + top 20 documentos recuperados
- **Salida:** `CAN_ANSWER`, `PARTIAL`, o `NO_MATCH`
- **Lógica:** Si `NO_MATCH` → termina y devuelve "No encontré información relevante"

**Ejemplo:**
```
Pregunta: "¿Cuál es la eficiencia PUE en 2022?"
Documentos recuperados: (Google 2024 Environmental Report)
→ RelevanceChecker: "CAN_ANSWER" ✓
→ Continúa a Node 2
```

#### 2️⃣ ResearchAgent (Investigador)
- **Rol:** Genera la respuesta basada SOLO en documentos
- **Modelo:** `qwen2.5:7b` (temp=0.3, con variación)
- **Entrada:** Pregunta + top 5 documentos más relevantes
- **Salida:** Respuesta detallada en español
- **Restricción:** "SOLO basándote en los documentos"

**Ejemplo:**
```
Pregunta: "¿Cuál es la eficiencia PUE en 2022?"
Documentos: [Doc 1: "PUE 2022: 1.12", Doc 2: "Regional average...", ...]
→ ResearchAgent:
   "Según el documento, la eficiencia PUE en 2022 fue de 1.12..."
```

#### 3️⃣ VerificationAgent (Verificador)
- **Rol:** Verifica que la respuesta esté realmente soportada por documentos
- **Modelo:** `qwen2.5:7b` (temp=0.0, determinístico)
- **Entrada:** Pregunta + Respuesta + documentos
- **Salida:** Reporte con `Soportado: SI/NO/PARCIAL`
- **Lógica especial:** Si `NO` → vuelve a Node 2 (máximo 1 retry)

**Ejemplo:**
```
Pregunta: "¿Cuál es la eficiencia PUE en 2022?"
Respuesta: "La eficiencia PUE en 2022 fue de 1.12"
Documentos: (mismos que Node 2)
→ VerificationAgent:
   "Soportado: SI
    Relevante: SI
    Resumen: La respuesta está explícitamente mencionada en Doc 1"
```

### Retriever híbrido (búsqueda de documentos)

La búsqueda usa **dos estrategias en paralelo**:

**1. BM25 (búsqueda por palabras clave)**
- Busca documentos que contienen palabras de la pregunta
- Rápido, no requiere embeddings
- Peso: 40%

**2. Vector Search (búsqueda semántica)**
- Convierte pregunta y documentos a vectores (embeddings)
- Busca documentos con significado similar (aunque usen palabras diferentes)
- Requiere `mxbai-embed-large` model
- Peso: 60%

**Resultado:** EnsembleRetriever combina ambos → top 10 documentos más relevantes

---

## ⚙️ Parámetros de Configuración

Todos en **`config.ini`**. Cambiar aquí NO requiere tocar el código.

### Sección `[ollama]` — Modelo y inferencia

```ini
[ollama]
base_url = http://localhost:11434    # URL de Ollama
timeout = 180                        # Timeout en segundos
keep_alive = 10m                     # Cuánto tiempo guardar modelo en VRAM

text_model = qwen2.5:7b-instruct-q4_K_M  # Modelo para los 3 agentes
temperature = 0.1                    # Default (individual agents overriden)
top_p = 0.9                          # Nucleus sampling (diversidad)
num_predict = 300                    # Max tokens por respuesta
```

**Tuning:**
- **temperature:** 0.0 = determinístico (siempre igual respuesta) | 1.0 = creativo (diferente c/vez)
  - RelevanceChecker: siempre 0.0
  - ResearchAgent: típicamente 0.3
  - VerificationAgent: siempre 0.0
- **top_p:** Reduce si respuestas son demasiado divergentes
- **num_predict:** Aumenta si respuestas se cortan, disminuye si es muy lento

### Sección `[embeddings]` — Conversión a vectores

```ini
[embeddings]
embedding_model = mxbai-embed-large
```

**Opciones:**
- `mxbai-embed-large` (670 MB) ← Recomendado (buena calidad)
- `nomic-embed-text` (274 MB) ← Más rápido pero menos preciso

### Sección `[chroma]` — Base de datos

```ini
[chroma]
host = localhost
port = 8000
collection_name = rag_agentai_documents
```

**Si Chroma es remoto:**
```ini
host = 192.168.x.x      # IP del servidor Chroma
port = 8000             # Mismo puerto
```

### Sección `[rag]` — Recuperación de documentos

```ini
[rag]
vector_search_k = 10         # Documentos a recuperar
ensemble_weights = 0.4,0.6   # Pesos BM25 y vector
max_context_docs = 5         # Documentos a pasar al LLM
```

**Tuning:**
- Aumentar `vector_search_k` (ej. 15) si respuestas están incompletas
- Disminuir `vector_search_k` (ej. 5) si es muy lento
- Disminuir `max_context_docs` (ej. 3) para respuestas más rápidas pero menos contexto

### Sección `[gradio]` — Interfaz web

```ini
[gradio]
server_name = 127.0.0.1      # IP (127.0.0.1 = localhost)
server_port = 5020           # Puerto web
share = false                # Si true, genera URL pública (no recomendado)
```

### Sección `[logging]` — Logs

```ini
[logging]
level = INFO                 # DEBUG (verbose) | INFO (normal) | WARNING | ERROR
log_dir = logs               # Carpeta de logs
log_file = rag_agentai.log   # Nombre del archivo
log_max_size_mb = 10         # Tamaño antes de rotar
log_backup_count = 5         # Archivos rotados a mantener
```

---

## 🔄 Workflow de Procesamiento

Paso a paso, qué ocurre cuando presionas "Enviar":

### Paso 1: Carga de documentos (primera vez con un archivo)

```
Usuario sube PDF → SHA256 hash del contenido
                ↓
            ¿Está en caché?
            ↙        ↘
           NO        SI
           ↓         ↓
        Docling   Cargar
        parse     .pkl
           ↓
      Markdown
           ↓
   MarkdownHeaderTextSplitter
   (chunks por # headers)
           ↓
   Embeddings (mxbai-embed-large)
           ↓
   Chroma store (colección rag_agentai_documents)
           ↓
   Cache en disk (.pkl)
```

**Tiempo típico:** 10-60 segundos (depende del tamaño del PDF)

### Paso 2: Recuperación (buscar documentos relevantes)

```
Pregunta usuario
    ↓
BM25 search ← Búsqueda por palabras
    ↓
Vector search ← Búsqueda semántica
    ↓
EnsembleRetriever (pesos 0.4, 0.6)
    ↓
Top 10 documentos más relevantes
    ↓
Ir a Paso 3 (3-agent workflow)
```

**Tiempo típico:** 0.1-0.5 segundos

### Paso 3: 3-Agent Workflow

```
RelevanceChecker (LLM call 1)
    ├─ Recupera top 20 docs
    ├─ Prompt: "¿Pueden estos docs responder?"
    ├─ Espera respuesta LLM (~2-5 seg)
    └─ Si NO_MATCH → Responde "No encontré información" → FIN

    ↓ (Si CAN_ANSWER o PARTIAL)

ResearchAgent (LLM call 2)
    ├─ Recupera top 5 docs
    ├─ Prompt: "Responde SOLO basándote en estos docs"
    ├─ Espera respuesta LLM (~5-10 seg)
    └─ Genera answer (~300 tokens)

    ↓

VerificationAgent (LLM call 3)
    ├─ Recupera top docs
    ├─ Prompt: "¿Está esta respuesta soportada?"
    ├─ Espera respuesta LLM (~2-5 seg)
    └─ Genera verification report

    ↓ (Si Soportado: NO)

Re-research (máximo 1 retry)
    └─ Vuelve a ResearchAgent con contexto diferente
```

**Tiempo total típico:** 15-30 segundos (según GPU y tamaño de contexto)

---

## 📊 Entendiendo los Logs

Los logs están en `logs/rag_agentai.log` y también en stdout.

### Formato

```
2026-09-05 14:32:10.123 | INFO     | Inicializando DocumentProcessor
2026-09-05 14:32:15.456 | DEBUG    | SHA256 hash: abc123def...
2026-09-05 14:32:45.789 | INFO     | ✓ Pipeline completado exitosamente
```

### Leer logs para debugging

**Inicio normal:**
```
INFO:     Uvicorn running on http://127.0.0.1:5020
```

**Carga de documento:**
```
INFO     | Processing: google-2024-environmental-report.pdf
DEBUG    | SHA256 hash: a1b2c3d4e5f6g7h8...
DEBUG    | Loading from cache (PKL)
INFO     | ✓ Docling parsed (N chunks)
```

**Pregunta procesada:**
```
INFO     | Iniciando pipeline completo: '¿Cuál es la eficiencia PUE?'
DEBUG    | → Paso 1: check_relevance
DEBUG    | Resultado: CAN_ANSWER
DEBUG    | → Paso 2: research
DEBUG    | → Paso 3: verification
INFO     | ✓ Pipeline completado exitosamente
```

**Error típico:**
```
ERROR    | ❌ Error in verification: Connection refused to http://localhost:8000
```

→ **Solución:** Verifica que Docker Chroma está corriendo (`docker ps`)

---

## 🔧 Debugging y Optimización

### Si las respuestas son lentas

**1. Reducir cantidad de documentos:**
```ini
[rag]
vector_search_k = 5        # Reduce de 10 a 5
max_context_docs = 3       # Reduce de 5 a 3
```

**2. Cambiar modelo a versión más pequeña:**
```ini
text_model = qwen2.5:3b-instruct  # Cambiar de 7b a 3b (más rápido)
```

**3. Verificar GPU:**
```powershell
nvidia-smi  # Ver uso de VRAM y temperatura
```

### Si las respuestas son incompletas o genéricas

**1. Aumentar documentos:**
```ini
vector_search_k = 15       # Aumenta de 10 a 15
max_context_docs = 7       # Aumenta de 5 a 7
```

**2. Aumentar temperature ligeramente:**
```ini
[ollama]
temperature = 0.15         # Cambiar de 0.1 a 0.15 (ligeramente más creativo)
```

### Si aparecen errores de conexión

**1. Ollama no responde:**
```powershell
# Verificar:
ollama list

# Si falla, reiniciar:
ollama serve
```

**2. Chroma no responde:**
```powershell
# Verificar:
curl http://localhost:8000/api/v1

# Si falla, reiniciar:
docker restart <container_id>
# O crear nuevo:
docker run -d -p 8000:8000 chromadb/chroma:latest
```

### Limpiar base de datos (empezar de cero)

**⚠️ Esto borra todos los documentos cargados:**

```powershell
# Opción 1: Desde UI - carga documentos nuevos (sobrescribe automáticamente)

# Opción 2: Borrar colección manualmente
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8000)
client.delete_collection('rag_agentai_documents')
print('✓ Colección borrada')
"

# Luego vuelve a cargar documentos
```

---

## ❓ FAQ

### P: ¿Puedo cambiar el idioma a inglés?
**R:** Los prompts están en español porque ese es el default del sistema. Para cambiar:
1. Edita `agents/relevance_checker.py`, `research_agent.py`, `verification_agent.py`
2. Cambia los prompts (líneas con `"""Eres un...`)
3. Reinicia la app

**Recomendación:** Mantén en español (es más natural para el equipo).

### P: ¿Cuánta VRAM necesita?
**R:**
- `qwen2.5:3b`: ~3 GB
- `qwen2.5:7b` (recomendado): ~6-7 GB
- `qwen2.5:14b`: ~13-15 GB
- `mxbai-embed-large`: ~1 GB

**Total:** 7-8 GB (recomendado para 7b + embeddings)

### P: ¿Puedo usar otros modelos?
**R:** Sí. Actualiza `config.ini`:
```ini
text_model = mistral:7b-instruct
# o
text_model = llama2:13b-chat
```

Luego descarga: `ollama pull <model-name>`

### P: ¿Qué pasa si sube un documento de 1000 páginas?
**R:** 
- Primera carga: 1-3 minutos (depende de GPU)
- Recuperación: ~0.5 segundos (consultas posteriores)
- LLM processes solo top-5 chunks (controlado por `max_context_docs`)

### P: ¿Puedo usar esto en producción?
**R:** No directamente. Para producción:
- Agrega autenticación (Gradio share=true no es seguro)
- Usa HTTPS (certs SSL)
- Ejecuta detrás de un proxy (nginx/apache)
- Monitorea logs y recursos

### P: ¿Los datos quedan guardados?
**R:** 
- Documentos: En Chroma (base de datos vectorial)
- Embeddings: En Chroma
- Conversaciones: NO se guardan (son stateless)
- Logs: En `logs/rag_agentai.log`

Para borrar: Ver sección "Limpiar base de datos"

---

## 📞 Soporte y Siguiente

- **Problemas:** Ver **Troubleshooting** en SETUP.md
- **Logs:** `logs/rag_agentai.log`
- **Código:** Revisar comentarios en `agents/`, `retriever/`, `document_processor/`
- **Arquitectura:** Ver **ARCHITECTURE.md**

**Próximos pasos:**
1. ✅ Ejecuta con ejemplos
2. ✅ Sube tus propios documentos
3. ✅ Ajusta `config.ini` para tu caso de uso
4. ✅ Monitorea logs y latencias

