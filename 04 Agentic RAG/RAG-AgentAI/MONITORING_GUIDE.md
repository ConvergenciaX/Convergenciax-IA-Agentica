# GUÍA DE MONITOREO EN VIVO — Ver qué está haciendo RAG-AgentAI

Esta guía te permite **monitorear en tiempo real** cada componente mientras subes documentos y haces preguntas.

---

## 🎬 Setup: Abre 4 terminales

Para ver todo lo que sucede, abre **4 ventanas PowerShell/CMD**:

```
Terminal 1: Ollama (servidor LLM + embeddings)
Terminal 2: ChromaDB (vector store)
Terminal 3: RAG-AgentAI (app.py)
Terminal 4: Logs en vivo (tail del archivo)
```

### Terminal 1: Ollama (con logs)

```powershell
# Abre en una terminal
ollama serve
```

**Qué esperar:**
```
[GIN] 2025-09-07 22:31:11 | 200 | 245.3ms | 127.0.0.1 | POST /api/embeddings
[GIN] 2025-09-07 22:31:12 | 200 | 3.2s   | 127.0.0.1 | POST /api/chat
```

Esto significa:
- `POST /api/embeddings` = OllamaEmbeddings generando vectores
- `POST /api/chat` = LLM respondiendo preguntas

---

### Terminal 2: ChromaDB (nativa en Windows)

```powershell
# Activa el entorno (si no lo hiciste)
C:\workspace-vc\env-llm-ia\Scripts\activate

# Inicia ChromaDB en puerto 8000
chroma run --host localhost --port 8000 --path ./chroma_data --log-path ./chroma.log
```

**Qué esperar:**
```
Starting Chroma using DirectClient.
Saving data to: ./chroma_data
Chroma is running at http://localhost:8000

(logs adicionales cuando se indexan documentos)
```

**Verificar que está activo:**
```powershell
# En otra terminal, haz un request de heartbeat
curl http://localhost:8000/api/v2/heartbeat
# Respuesta esperada: {}  (200 OK)
```

---

### Terminal 3: RAG-AgentAI app.py

```powershell
# Navega a la carpeta del proyecto
cd C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\04 Agentic RAG\RAG-AgentAI

# Activa entorno
C:\workspace-vc\env-llm-ia\Scripts\activate

# Ejecuta con logs en vivo
python app.py 2>&1 | Tee-Object -FilePath app_console.log
```

**Qué esperar:**
```
INFO     | utils.logging | Logging initialized (level=INFO, file=logs\rag_agentai.log)
INFO     | __main__ | === DocChat RAG Initialization ===
INFO     | document_processor.file_handler | DocumentProcessor initialized (cache: logs\document_cache)
...
Launching server locally at http://127.0.0.1:5020 ...
```

Cuando abras la UI y subas un documento:
```
INFO | Processing 1 file(s)
INFO | ✓ File validation passed (total: 2.3MB)
INFO | Procesados 156 fragmentos de documento
INFO | Connecting to Chroma at http://localhost:8000, collection 'rag_agentai_documents'
INFO | ✓ Vector store (Chroma) created successfully
INFO | Building hybrid retriever from 156 documents
```

---

### Terminal 4: Logs en vivo (Get-Content con -Wait)

```powershell
# En otra terminal (sin activar entorno)
Get-Content -Path C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\04 Agentic RAG\RAG-AgentAI\logs\rag_agentai.log -Tail 50 -Wait
```

Esto te **sigue los logs en tiempo real** mientras la app corre. Verás:
```
22:31:41 | INFO     | __main__ | Procesando pregunta: ¿Cuál es el PUE en Singapur?...
22:31:42 | DEBUG    | agents.relevance_checker | Recuperando top-20 documentos...
22:31:43 | DEBUG    | agents.relevance_checker | Evaluando relevancia con LLM...
22:31:45 | DEBUG    | agents.research_agent | Generando respuesta...
22:31:48 | DEBUG    | agents.verification_agent | Verificando respuesta...
22:31:50 | INFO     | __main__ | Pipeline completado exitosamente
```

---

## 📊 Monitoreo por fase

### **FASE 1: Carga & Parsing del documento**

**En Terminal 4 (Logs):**
```
INFO | Processing 1 file(s)
DEBUG | ✓ File validation passed (total: 2.3MB)
```

**En Terminal 3 (App console):**
Verás que **VRAM sube** en Task Manager:
```
Antes:  VRAM usada = 4 GB
Subiendo PDF con imágenes...
Después: VRAM usada = 6-7 GB  ← Docling + easyocr activo
```

**¿Dónde buscar evidencia?**
- ✅ **Task Manager** → Processes → `python.exe` → "GPU memory" sube
- ✅ **Logs**: "Document parsed: 156 chunks extracted"
- ✅ **Archivo**: `logs/document_cache/<hash>.pkl` aparece (binario, no legible)

---

### **FASE 2: Chunking semántico**

**En Terminal 4 (Logs):**
```
INFO | Procesados 156 fragmentos de documento
```

**¿Qué significan los números?**
- 156 fragmentos = PDF se dividió en 156 chunks semánticos
- Esto es **normal** para un PDF de 2-3 MB

**¿Dónde buscar evidencia?**
- ✅ **Logs**: "Procesados N fragmentos"

---

### **FASE 3: Indexación en ChromaDB (Embeddings)**

**En Terminal 1 (Ollama):**
```
[GIN] 2025-09-07 22:31:43 | 200 | 2456ms | 127.0.0.1 | POST /api/embeddings
[GIN] 2025-09-07 22:31:44 | 200 | 2123ms | 127.0.0.1 | POST /api/embeddings
...
```

Verás **múltiples requests a /api/embeddings** (uno por chunk). Cada uno tarda 1-5 segundos según el tamaño del chunk.

**En Terminal 2 (ChromaDB):**
Probablemente no verás logs visibles, pero internamente está recibiendo y guardando los vectores.

**En Terminal 4 (Logs):**
```
INFO | Initializing OllamaEmbeddings with model='mxbai-embed-large', base_url='http://localhost:11434'
INFO | ✓ OllamaEmbeddings initialized
INFO | Connecting to Chroma at http://localhost:8000, collection 'rag_agentai_documents'
INFO | ✓ Vector store (Chroma) created successfully
```

**¿Dónde buscar evidencia?**
- ✅ **Terminal Ollama**: requests a `/api/embeddings`
- ✅ **Task Manager**: VRAM sube (mxbai-embed-large ocupa ~1 GB)
- ✅ **Archivos**: `./chroma_data/` crece (archivos .parquet, .bin)
- ✅ **Logs**: "Vector store (Chroma) created successfully"

**Para inspeccionar qué hay en ChromaDB:**
```powershell
# Cuenta cuántos documentos hay
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/collections" -Method GET
$response | ConvertTo-Json
```

---

### **FASE 4: Búsqueda & Respuesta (3 Agentes + LLM)**

Cuando el usuario **hace una pregunta**:

**En Terminal 4 (Logs):**
```
22:31:41 | INFO     | __main__ | Procesando pregunta: ¿Cuál es el PUE?...

---Paso 1: RelevanceChecker---
22:31:42 | DEBUG    | agents.relevance_checker | Recuperando top-20 documentos...
22:31:43 | DEBUG    | agents.relevance_checker | Resultado: MATCH

---Paso 2: ResearchAgent---
22:31:44 | DEBUG    | agents.research_agent | Generando respuesta...

---Paso 3: VerificationAgent---
22:31:47 | DEBUG    | agents.verification_agent | Resultado: Soportado: SI
```

**En Terminal 1 (Ollama):**
```
[GIN] 2025-09-07 22:31:42 | 200 | 123ms  | 127.0.0.1 | POST /api/embeddings
[GIN] 2025-09-07 22:31:43 | 200 | 8456ms | 127.0.0.1 | POST /api/chat    ← ResearchAgent
[GIN] 2025-09-07 22:31:48 | 200 | 5123ms | 127.0.0.1 | POST /api/chat    ← VerificationAgent
```

- `POST /api/embeddings` = búsqueda vectorial
- `POST /api/chat` = LLM respondiendo

**En Task Manager:**
```
python.exe VRAM: 4-6 GB (LLM cargado en GPU)
```

**¿Dónde buscar evidencia?**
- ✅ **Terminal Ollama**: múltiples `/api/chat` requests
- ✅ **Task Manager**: VRAM sube cuando LLM genera
- ✅ **Terminal 3 (App console)**: respuesta aparece en la UI
- ✅ **Logs**: "Pipeline completado exitosamente"

---

## 🧪 Casos de prueba para entender el flujo

### **Test 1: Documento simple + pregunta directa**

```
1. Sube: GETTING_STARTED.md (TXT simple, sin imágenes)
   → Espera: No hay OCR, parsing es rápido (~5 seg)
   
2. Pregunta: "¿Qué es RAG?"
   → Espera: Búsqueda encuentra la palabra "RAG" en el texto
             RelevanceChecker dice "MATCH"
             ResearchAgent responde basado en el documento
             
3. Monitorea:
   - Terminal Ollama: 1 request de embeddings (pequeño)
   - Terminal ChromaDB: ~50 chunks guardados
   - VRAM: sube sólo cuando LLM genera
```

### **Test 2: PDF con imágenes + pregunta específica**

```
1. Sube: google-2024-environmental-report.pdf (~5 MB con gráficos)
   → Espera: easyocr se activa, VRAM sube a 6-8 GB
             parsing tarda ~30-60 seg (extrae OCR de gráficos)
   
2. Pregunta: "¿Cuál fue el PUE en Singapur 2022?"
   → Espera: Vector search encuentra chunks sobre "PUE" + "Singapur"
             LLM extrae el número específico (1.15)
             
3. Monitorea:
   - Terminal Ollama: muchos requests de embeddings
   - Terminal ChromaDB: ~200-500 chunks (PDF es grande)
   - VRAM: permanece alta (>5 GB) mientras LLM procesa
```

### **Test 3: Documento irrelevante**

```
1. Sube: un recibo de supermercado (PDF sin relación)
   
2. Pregunta: "¿Qué datos sobre PUE hay?"
   → Espera: RelevanceChecker dice "NO_MATCH"
             UI responde: "Esta pregunta no está relacionada con los documentos"
             
3. Monitorea:
   - No hay LLM call (se detiene en RelevanceChecker)
   - Logs muestran: "Resultado: NO_MATCH → finalizando"
```

---

## 🔍 Troubleshooting: ¿Qué hacer si algo no funciona?

| **Síntoma** | **Causa probable** | **Verificación** | **Fix** |
|---|---|---|---|
| No hay logs de `/api/embeddings` en Ollama | OllamaEmbeddings no se conecta | ¿ChromaDB levanta? `netstat -ano \| findstr 11434` | Reinicia Ollama, verifica `http://localhost:11434/api/tags` |
| ChromaDB recibe petición pero no guarda | Permisos en `./chroma_data/` | `Get-Item ./chroma_data` | Borra `./chroma_data`, reinicia ChromaDB |
| LLM tarda >1 minuto en responder | Modelo muy grande para GPU disponible | Task Manager: VRAM maxed out? | Cambia a modelo más pequeño en `config.ini` |
| "No documentos relevantes" aunque hay PDF | Chunking no está preservando contexto | Logs: "Procesados N fragmentos"? | Revisa `FLUJO_COMPLETO.md` Fase 2 |
| VRAM sube de golpe sin razón | Docling descargando modelos HuggingFace | ¿Primer PDF subido? | Normal, tarda 2-3 minutos la primera vez |

---

## 📈 Expectativas de rendimiento

| **Operación** | **Tiempo esperado** | **VRAM típico** | **Variables** |
|---|---|---|---|
| Parsing PDF 2 MB (sin imágenes) | 5-10 seg | +200 MB | Complejidad de layout |
| Parsing PDF 5 MB (con imágenes) | 30-60 seg | +2 GB | Cantidad de gráficos |
| Embeddings 156 chunks | 60-120 seg | +1 GB | Tamaño promedio del chunk |
| Búsqueda vectorial | <1 seg | ~0 MB | (muy rápido) |
| ResearchAgent (generar respuesta) | 10-30 seg | +3-4 GB | Longitud de la respuesta |
| VerificationAgent | 5-10 seg | +3 GB | Verificación de claims |
| **Total: subir doc + pregunta** | **2-3 minutos** | **6-8 GB pico** | First-time slower (HF models) |

---

## 💡 Interpretar los números

### **Embeddings: ¿qué es un vector de 1024 dimensiones?**

```python
# Un embedding se ve así (simplificado):
chunk_text = "El PUE en Singapur 2022 fue de 1.15"

embedding = OllamaEmbeddings.embed_query(chunk_text)
# Resultado:
[0.123, -0.456, 0.789, 0.012, -0.345, ..., 0.001]  ← 1024 números

# Estos números capturan el "significado" del texto
# Chunks similares tienen embeddings similares
```

### **Búsqueda vectorial: cómo ChromaDB encuentra documentos**

```
Pregunta: "¿PUE en Singapur?"
Embedding de pregunta: [0.100, -0.400, 0.800, ...]  (1024 números)

ChromaDB calcula: similaridad = coseno_similarity(
    pregunta_embedding,
    [chunk1_embedding, chunk2_embedding, ...]
)

Resultado:
- Chunk "PUE Singapur 2022": 0.87 similitud ✓ TOP 1
- Chunk "CFE Asia Pacific": 0.65 similitud
- Chunk "Política de compras": 0.12 similitud
```

---

## 🎯 Checklist para validar que todo funciona

- [ ] **Ollama activo**: `ollama serve` en Terminal 1, sin errores
- [ ] **ChromaDB activo**: `chroma run` en Terminal 2, "Chroma is running"
- [ ] **App activa**: `python app.py` en Terminal 3, "Launching server"
- [ ] **Logs en vivo**: Terminal 4 muestra logs en tiempo real
- [ ] **PDF sube sin errores**: UI acepta archivo, logs muestran "Procesados N fragmentos"
- [ ] **Embeddings generados**: Terminal 1 (Ollama) muestra requests `/api/embeddings`
- [ ] **ChromaDB recibe datos**: Terminal 2 o `./chroma_data/` crece
- [ ] **LLM responde**: Terminal 1 (Ollama) muestra `/api/chat`, respuesta aparece en UI
- [ ] **Logs muestran pasos**: Terminal 4 muestra "Paso 1: check_relevance", "Paso 2: research", "Paso 3: verification"

Si todos estos pasan, **RAG-AgentAI está funcionando correctamente**.

