# FLUJO COMPLETO — RAG-AgentAI: Desde el PDF hasta la Respuesta

**Objetivo:** Entender qué sucede en cada fase cuando subes un documento y haces una pregunta.

---

## 📊 Diagrama del flujo completo

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. CARGA & PARSING (GPU + Docling + HuggingFace)                      │
│                                                                         │
│   [Usuario sube PDF] → Docling convierte a Markdown → easyocr extrae  │
│                       texto + OCR de imágenes                          │
│                       (GPU activa si hay imágenes)                     │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ 2. CHUNKING SEMÁNTICO (MarkdownHeaderTextSplitter)                    │
│                                                                         │
│   Markdown → dividir por encabezados (#, ##) preservando contexto      │
│   Resultado: 50-500 chunks (según tamaño del PDF)                      │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ 3. INDEXACIÓN VECTORIAL (Ollama + ChromaDB)                           │
│                                                                         │
│   Cada chunk → OllamaEmbeddings (mxbai-embed-large) → vector 1024-dim │
│              → ChromaDB guarda vector + metadata + texto original      │
│              → Datos persistidos en ./chroma_data/                     │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│ 4. BÚSQUEDA HÍBRIDA & GENERACIÓN (3 Agentes + LLM)                   │
│                                                                         │
│   [Usuario pregunta] → Recuperador Híbrido:                            │
│                        · BM25 (búsqueda de palabras clave)             │
│                        · Vector Search (Chroma, semántica)             │
│                        · Combina ambos (EnsembleRetriever)             │
│                                                                         │
│                   → Paso 1: RelevanceChecker (¿hay documentos útiles?)│
│                        Llama al LLM via Ollama (temperatura baja)      │
│                                                                         │
│                   → Paso 2: ResearchAgent (generar respuesta)          │
│                        Combina documentos + pregunta → LLM → respuesta │
│                                                                         │
│                   → Paso 3: VerificationAgent (¿respuesta correcta?)  │
│                        Verifica que la respuesta esté en los docs      │
│                        Si NO: re-investigar (máx 1 intento más)        │
│                                                                         │
│   [Usuario ve respuesta + reporte de verificación]                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Fase 1: Carga & Parsing (DocumentProcessor)

### Archivo: `document_processor/file_handler.py`

**¿Qué sucede?**
1. Usuario sube un PDF, DOCX, TXT o MD
2. **Docling** lo convierte a **Markdown estructurado**
3. Si hay **imágenes en el PDF**, se activa **easyocr + GPU** para extraer texto (OCR)
4. Resultado: texto limpio + metadata (títulos, tablas, etc.)

### Componentes usados:
- **Docling**: conversor universal de documentos
  - Soporta: PDF, DOCX, TXT, MD, HTML, images
  - Descarga modelos de HuggingFace automáticamente:
    - `easyocr`: para OCR en imágenes
    - `timm/detectron2`: para detección de layouts (tablas, columnas)
    - `transformers`: para análisis de estructura
  - **Caché:** `~/.cache/huggingface/hub/` (primer uso tarda ~500MB de descarga)

- **GPU (torch)**: se activa si el PDF tiene imágenes con texto
  - Módulos: `easyocr`, `transformers` usan VRAM
  - Sin imágenes: GPU no se necesita

### Ejemplo de log esperado:

```
INFO | DocumentProcessor initialized (cache: logs\document_cache)
INFO | Processing 1 file(s)
DEBUG | ✓ File validation passed (total: 2.3MB)
DEBUG | Cache hit for file: google-2024-environmental-report.pdf (hash: a1b2c3...)
INFO | ✓ Document parsed: 156 chunks extracted
```

### Dónde ver que funciona:
- ✅ **Task Manager**: VRAM sube si hay imágenes (~200-500MB extra)
- ✅ **Logs**: "Procesados N fragmentos de documento"
- ✅ **Cache local**: `logs\document_cache\<hash>.pkl` (almacena chunks parseados)

---

## 🧩 Fase 2: Chunking Semántico (MarkdownHeaderTextSplitter)

### Archivo: `document_processor/file_handler.py` (línea ~80)

**¿Qué sucede?**
1. El Markdown parseado se **divide por encabezados** (# y ##)
2. Se preserva el contexto de jerarquía (sección padre → hijo)
3. Cada chunk tiene **metadatos** (título, número de página, fuente)

### Parámetros de chunking (en `config.ini`, si existen):
```ini
[document_processor]
# chunk_size = 512  # tokens máximos por chunk
# overlap = 100     # solapamiento entre chunks
```

### Ejemplo:

**PDF original:**
```
# Capítulo 1: Sostenibilidad

## 1.1 Datos de centros de datos

PUE efficiency in Singapore facility 2019: 1.23
PUE efficiency in Singapore facility 2022: 1.15
```

**Chunks resultantes:**
1. Chunk 1: "# Capítulo 1: Sostenibilidad" + "## 1.1 Datos de centros de datos" + "PUE efficiency in Singapore facility 2019: 1.23"
2. Chunk 2: "## 1.1 Datos de centros de datos" + "PUE efficiency in Singapore facility 2022: 1.15"

(Nota: se preserva contexto para que búsquedas vectoriales entiendan la relación)

### Dónde ver que funciona:
- ✅ **Logs**: "Procesados 156 fragmentos de documento"
- ✅ **Caché pickle**: `logs\document_cache\<hash>.pkl` contiene los chunks (binario)

---

## 🔗 Fase 3: Indexación Vectorial (Ollama + ChromaDB)

### Archivo: `retriever/builder.py` (línea ~20-41)

**¿Qué sucede?**

1. **Ollama genera embeddings** para cada chunk
   - Modelo: `mxbai-embed-large` (1024 dimensiones)
   - Endpoint: `http://localhost:11434/api/embeddings`
   - Cada chunk → vector numérico de 1024 números

2. **ChromaDB almacena los vectores** (servidor HTTP en `localhost:8000`)
   - Colección: `rag_agentai_documents`
   - Datos persistidos: `./chroma_data/`

### Flujo técnico:

```python
# 1. Conectar a Ollama
embeddings = OllamaEmbeddings(
    model="mxbai-embed-large",
    base_url="http://localhost:11434"
)

# 2. Para CADA chunk, generar vector
vector = embeddings.embed_query(chunk_text)
# Resultado: [0.123, -0.456, 0.789, ..., 0.001] (1024 números)

# 3. Enviar vectores a ChromaDB vía HTTP
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    client_type="http",
    host="localhost",
    port=8000,
    collection_name="rag_agentai_documents"
)
```

### Dónde se guardan los datos:

ChromaDB almacena en:
```
./chroma_data/
├── [collection_uuid]/
│   ├── data/
│   │   ├── [segment_uuid]/
│   │   │   ├── embeddings.bin      ← vectores (float32)
│   │   │   ├── documents.parquet   ← texto original
│   │   │   ├── metadata.parquet    ← título, página, etc.
│   │   │   └── uris.parquet        ← IDs únicos
```

### Log esperado:

```
INFO | Initializing OllamaEmbeddings with model='mxbai-embed-large', base_url='http://localhost:11434'
INFO | ✓ OllamaEmbeddings initialized
INFO | Building hybrid retriever from 156 documents
INFO | Connecting to Chroma at http://localhost:8000, collection 'rag_agentai_documents'
INFO | ✓ Vector store (Chroma) created successfully
```

### Monitorear esta fase:

1. **¿Ollama recibió la petición?**
   ```powershell
   # En otra terminal, mira los logs de Ollama:
   ollama serve
   # Deberías ver: "POST /api/embeddings" requests
   ```

2. **¿ChromaDB guardó los datos?**
   ```powershell
   # Verifica que la carpeta ./chroma_data tenga archivos
   Get-ChildItem -Recurse ./chroma_data
   ```

3. **¿VRAM se usa?**
   - Task Manager → Processes → `python.exe` → VRAM
   - Esperado: mxbai-embed-large ocupa ~1GB con 156 chunks

---

## 🧠 Fase 4: Búsqueda Híbrida & Respuesta (3 Agentes + LLM)

### Archivo: `agents/workflow.py`

**¿Qué sucede?**

Cuando el usuario hace una pregunta, se ejecuta un **pipeline de 3 agentes**:

### **Paso 1: RelevanceChecker** (`agents/relevance_checker.py`)

```
[Usuario pregunta: "¿Cuál es el PUE en Singapur 2022?"]
                    ↓
[Recuperar top-20 chunks más relevantes]
  · BM25: busca "PUE", "Singapur", "2022" (palabra clave)
  · Vector: busca chunks semánticamente similares (via embeddings)
  · Combina: 0.4 * BM25_score + 0.6 * Vector_score
                    ↓
[Llamar al LLM con temperatura baja (0.1)]
  "Dada esta pregunta y estos documentos, ¿son relevantes para responder?"
                    ↓
Respuesta LLM: "SI" → continuar
             "NO"  → retornar "Pregunta no relacionada con documentos"
```

### **Paso 2: ResearchAgent** (`agents/research_agent.py`)

```
[Usuario pregunta: "¿Cuál es el PUE en Singapur 2022?"]
[Recuperar chunks relevantes: 5 mejores resultados]
                    ↓
[Construir prompt para LLM]
  Sistema: "Eres experto en sostenibilidad. Responde en español basándote en los documentos."
  Documentos: [chunk 1, chunk 2, chunk 3, ...]
  Pregunta: "¿Cuál es el PUE en Singapur 2022?"
                    ↓
[Llamar al LLM (ChatOllama)]
  Modelo: qwen2.5:7b-instruct-q4_K_M
  Temperatura: 0.1 (determinístico)
  Top-p: 0.9
  Max tokens: 300
                    ↓
Respuesta LLM: "El PUE en Singapur 2022 fue de 1.15, representando una mejora..."
```

### **Paso 3: VerificationAgent** (`agents/verification_agent.py`)

```
[Respuesta generada: "El PUE en Singapur 2022 fue de 1.15..."]
[Documentos recuperados: [chunk 1, chunk 2, ...]]
                    ↓
[Llamar al LLM para verificar]
  "¿La respuesta anterior está soportada por los documentos?"
  Busca: ¿aparecen 'PUE', 'Singapur', '2022', '1.15' en los chunks?
                    ↓
Respuesta: "SI - Respuesta soportada en documentos"
        o  "NO - Respuesta no aparece. Re-investigar."
                    ↓
Si NO y no hay más reintentos:
  [Ejecutar ResearchAgent de nuevo, intentar mejor respuesta]
                    ↓
[Usuario recibe: respuesta + reporte de verificación]
```

### Log esperado:

```
INFO | Procesando pregunta: ¿Cuál es el PUE en Singapur 2022?...
INFO | Construyendo nuevo recuperador para documentos...
INFO | Procesados 156 fragmentos de documento
INFO | ✓ Recuperador híbrido construido
DEBUG | → Paso 1: check_relevance
DEBUG | → Paso 2: research
DEBUG | Respuesta generada (245 caracteres)
DEBUG | → Paso 3: verification
DEBUG | Reporte de verificación: "Soportado: SI"
INFO | Pipeline completado exitosamente
```

---

## 📦 Dónde se almacenan los datos intermedios

| **Componente** | **Ubicación** | **Contenido** | **Persistencia** |
|---|---|---|---|
| **Chunks parseados** | `logs/document_cache/<hash>.pkl` | Texto chunkeado + metadata | Mientras exista el hash |
| **Vectores + texto** | `./chroma_data/` | Embeddings + documentos originales | Permanente (hasta borrar ChromaDB) |
| **Logs de ejecución** | `logs/rag_agentai.log` | Traces de cada fase | Rotación cada 10MB (5 backups) |
| **Conversación UI** | Memoria de sesión Gradio | Solo la sesión actual del navegador | Se pierde al cerrar navegador |

---

## 🔧 Cómo monitorear cada fase

### **Durante la carga del documento:**

1. **Task Manager** → VRAM debería **subir ~500MB-2GB**
   - Docling carga modelos de HuggingFace
   - easyocr activa si hay imágenes

2. **Logs en tiempo real:**
   ```powershell
   # En otra terminal, mira el archivo de log
   Get-Content -Path logs\rag_agentai.log -Tail 20 -Wait
   ```

3. **ChromaDB recibiendo datos:**
   ```powershell
   # Verifica requests HTTP a localhost:8000
   netstat -ano | findstr 8000
   # Deberías ver ESTABLISHED connections
   ```

### **Durante la generación de respuesta:**

1. **Ollama procesando:**
   - En terminal de Ollama, verás requests de embedding
   - En otra terminal: VRAM sube si se está generando (LLM)

2. **Logs del LLM:**
   ```log
   INFO | Llamando a LLM con temperatura=0.1
   INFO | Token generation: 45 / 300 tokens
   INFO | LLM respuesta recibida
   ```

3. **Tiempo de respuesta:**
   - Embeddings: ~2-5 seg (depende del tamaño de chunks)
   - LLM generation: ~10-30 seg (depende del modelo + longitud)
   - Verificación: ~5-10 seg más

---

## 🎯 Resumen de tecnologías por fase

| **Fase** | **Tecnología** | **CPU/GPU** | **Memoria** | **Red** |
|---|---|---|---|---|
| **1. Parsing** | Docling + easyocr + torch | GPU (si imágenes) | 2-3 GB | HuggingFace (primer uso) |
| **2. Chunking** | MarkdownHeaderTextSplitter | CPU | ~500 MB | Ninguna |
| **3. Embeddings** | OllamaEmbeddings (mxbai-embed-large) | GPU en Ollama | 1 GB | localhost:11434 (HTTP) |
| **3. ChromaDB** | ChromaDB server | CPU | 1-2 GB | localhost:8000 (HTTP) |
| **4. Búsqueda** | BM25 + Vector search | CPU/GPU en ChromaDB | ~1 GB | localhost:8000 (HTTP) |
| **4. LLM** | ChatOllama (qwen2.5:7b) | GPU | 4-8 GB (según modelo) | localhost:11434 (HTTP) |

---

## 🚀 Flujo completo resumido en 10 segundos

```
[PDF subido]
    ↓ (Docling + HuggingFace, GPU si imágenes)
[Texto limpio]
    ↓ (MarkdownHeaderTextSplitter)
[156 chunks semánticos]
    ↓ (OllamaEmbeddings: mxbai-embed-large)
[1024-dim vectors × 156]
    ↓ (ChromaDB en localhost:8000)
[Datos persistidos en ./chroma_data/]

---

[Usuario pregunta]
    ↓ (RelevanceChecker: ¿hay documentos útiles?)
    ↓ (ResearchAgent: generar respuesta del LLM)
    ↓ (VerificationAgent: ¿respuesta correcta?)
[Respuesta + reporte verificación]
```

---

## 📖 Lectura adicional

- **`CODE_WALKTHROUGH.md`**: línea-por-línea del código
- **`CHROMA_VECTORIZATION.md`**: deep-dive en cómo funcionan los embeddings
- **`ARCHITECTURE_DETAILED.md`**: decisiones de diseño y alternativas
- **`MANUAL.md`**: cómo usar la UI
