# OPERACIÓN OFFLINE — RAG-AgentAI 100% Local sin HuggingFace

**Versión:** 2.0 | **Actualizado:** 2026-09-06

---

## 🎯 Objetivo

RAG-AgentAI corre **completamente local** sin depender de internet para:
- ✅ LLM (Ollama corriendo localmente)
- ✅ Vector Store (ChromaDB nativo en Windows)
- ✅ Embeddings (Ollama local)
- ✅ Parsing de documentos (Docling con modelos locales)
- ✅ OCR en imágenes (EasyOCR con modelos locales)

**No hay llamadas salientes a HuggingFace, OpenAI, o ningún proveedor cloud en tiempo de ejecución.**

---

## 📋 Setup de offline (3 pasos, una sola vez)

### Paso 1: Instalar dependencias Python
```powershell
cd C:\workspace-vc\...\RAG-AgentAI
C:\workspace-vc\env-llm-ia\Scripts\activate
pip install -r requirements.txt --only-binary :all:
```

### Paso 2: Pre-descargar modelos de Docling (1.5 GB)
```powershell
# CON INTERNET DISPONIBLE (una sola vez)
python scripts/download_local_models.py

# Crea: ./models/docling/
```

### Paso 3: Pre-cachear modelos de EasyOCR (opcional, ~500 MB)
```powershell
# CON INTERNET DISPONIBLE (una sola vez)
# Sube un PDF con imágenes en la UI
# Verás logs: "Processing file: document.pdf"
# La PRIMERA ejecución tarda 30-60 seg (OCR descarga modelos)
# Los modelos se cachean automáticamente en ./models/easyocr/

# Después: cambiar config.ini si deseas desactivar OCR en modo offline
```

---

## 🔧 Configuración (en `config.ini`)

```ini
[document_processor]
# Ruta con modelos de Docling (layout, tablas, detectores)
# Se crea ejecutando: python scripts/download_local_models.py
docling_artifacts_path = ./models/docling

# Habilitar OCR (reconocer texto en imágenes dentro de PDFs)
# = true: detecta + extrae texto de gráficos/tablas (lento, con GPU)
# = false: solo texto de PDFs "textuales" (rápido)
do_ocr = true

# Ruta con modelos de EasyOCR (se pre-cachean automáticamente en primer uso)
docling_ocr_models_path = ./models/easyocr
```

---

## 🔐 Componentes offline

### 1. **Ollama (LLM + Embeddings)** — Ya local por default

```
Flujo:
  [Usuario] → pregunta → [Ollama en localhost:11434]
                           ↓ (corre en GPU si está disponible)
                           [Respuesta]
```

**Configuración (config.ini):**
```ini
[ollama]
base_url = http://localhost:11434
text_model = qwen2.5:7b-instruct-q4_K_M  (o el que prefieras)
embedding_model = mxbai-embed-large
```

### 2. **ChromaDB (Vector Store)** — Nativo en Windows

```
Flujo:
  [Embeddings] → http://localhost:8000 → ChromaDB almacena
  [Búsqueda]   → localhost:8000/api/v2/query (local)
```

**Comando para arrancar:**
```powershell
chroma run --host localhost --port 8000 --path ./chroma_data
```

**Configuración (config.ini):**
```ini
[chroma]
host = localhost
port = 8000
```

### 3. **Docling (Parsing PDF/DOCX)** — Con modelos locales

**Antes (sin este cambio):**
```
[PDF subido] → Docling intenta descargar de HuggingFace
                ↓ (si no hay internet, falla o espera timeout)
                [Error o delay 30+ segundos]
```

**Ahora (con Docling offline):**
```
[PDF subido] → Docling usa ./models/docling/ (local)
                ↓ (instantáneo, no hay red)
                [Parsing completo]
```

**Modelos descargados (1.5 GB):**
```
./models/docling/
├── [modelos de layout]
├── [modelos de tablas]
├── [modelos de detección]
└── (etc.)
```

**Cómo sucede:**
```python
# En document_processor/file_handler.py:
pipeline_options = PdfPipelineOptions(
    artifacts_path="./models/docling",  ← Local, no HuggingFace
    do_ocr=True,
)
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
```

### 4. **EasyOCR (OCR en imágenes)** — Con modelos cacheados

**Proceso:**
1. **Primera ejecución (con internet):** EasyOCR descarga automáticamente sus modelos (~500 MB) al procesar un PDF con imágenes
2. **Subsiguientes ejecuciones:** Usa el caché local en `./models/easyocr/`
3. **Con `HF_HUB_OFFLINE=1`:** Si faltan modelos, falla rápido (no intenta red)

**Configuración (en código, `document_processor/file_handler.py`):**
```python
ocr_options=EasyOcrOptions(
    model_storage_directory="./models/easyocr",
    download_enabled=False,  ← NUNCA descargar en runtime (ya debe estar cacheado)
    use_gpu=True,            ← Usar GPU si está disponible
)
```

---

## 🛡️ Variables de entorno offline (en `app.py`)

**Al arrancar la app:**
```python
# app.py, antes de importar librerías que usan HuggingFace:
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
```

**¿Qué hacen?**
- `HF_HUB_OFFLINE=1` → Docling, huggingface_hub, etc. **no intentan conectarse a huggingface.co**
- `TRANSFORMERS_OFFLINE=1` → transformers library usa caché local, no red
- **Beneficio:** Si algo intenta contactar la red, falla **instantáneamente** en vez de esperar 30+ segundos de timeout

---

## ✅ Verificación: ¿Está offline?

### Test 1: Verificar variables de entorno

```powershell
# En los logs de app.py, deberías ver:
# INFO | Modo offline: HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1
```

### Test 2: Verificar carpetas de modelos

```powershell
# Ambas existen:
Get-ChildItem ./models/
# Esperado:
# Mode  Name
# ----  ----
# d----  docling
# d----  easyocr (si ya procesaste PDF con OCR)
```

### Test 3: Desconectar la red y verificar que funciona

```powershell
# 1. Desconecta WiFi (o desenchufa cable)
# 2. O activa modo avión (si es laptop)

# 3. Arranca la app (debe funcionar normalmente)
python app.py

# 4. Sube un PDF en http://127.0.0.1:5020
# 5. Verifica que se procesa sin errores de conexión

# 6. Abre logs en otra terminal:
Get-Content -Path logs/rag_agentai.log -Tail 50 -Wait

# Si ves "Vector store (Chroma) created successfully" SIN errores de conexión,
# entonces está 100% offline ✅
```

### Test 4: Verificar que modo offline es respetado

```powershell
# Para confirmar que REALMENTE está usando caché local y no intentando red:

# A) En logs, buscar "HuggingFace", "download", "snapshot_download"
# Si NO APARECEN → ✅ offline mode activo

# B) En Windows, abre Resource Monitor → Network tab
# Al procesar un PDF, NO debe haber conexiones hacia:
#   - huggingface.co
#   - cdn.huggingface.co
#   - api.huggingface.co
# (solo localhost:8000 para ChromaDB, localhost:11434 para Ollama)
```

---

## 🔄 Flujo completo offline

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Preparación (una sola vez, CON internet)          │
└─────────────────────────────────────────────────────────────┘
    │
    ├─ pip install requirements.txt
    ├─ python scripts/download_local_models.py       (1.5 GB → ./models/docling/)
    └─ Procesar PDF con OCR una vez                  (~500 MB → ./models/easyocr/)

┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Operación (100% OFFLINE, SIN internet)             │
└─────────────────────────────────────────────────────────────┘
    │
    ├─ Ollama: ollama serve
    ├─ ChromaDB: chroma run --port 8000
    └─ App: python app.py
            ↓
    [Usuario sube PDF]
            ↓
    ┌─────────────────────────────────┐
    │ DocumentProcessor.__init__()     │
    │ Carga pipeline de Docling        │
    │ artifacts_path = ./models/docling│
    │ (SIN contactar HuggingFace)      │
    └─────────────────────────────────┘
            ↓
    [Docling procesa PDF]
    (modelos de layout, tablas = cacheados localmente)
            ↓
    [Chunking semántico]
    (MarkdownHeaderTextSplitter = local, no red)
            ↓
    [Ollama genera embeddings]
    (http://localhost:11434 = red local)
            ↓
    [ChromaDB almacena vectores]
    (http://localhost:8000 = red local)
            ↓
    [Usuario hace pregunta]
            ↓
    [RelevanceChecker, ResearchAgent, VerificationAgent]
    (todos usan Ollama en localhost:11434)
            ↓
    [Respuesta generada]

    ✅ TODO OFFLINE - Sin una sola llamada hacia el exterior
```

---

## 🚨 Troubleshooting: Si aparecen errores de red

| Síntoma | Causa | Solución |
|---------|-------|----------|
| "OSError: download_path doesn't exist" o "File not found in artifacts_path" | `./models/docling/` no existe o está vacío | Ejecutar `python scripts/download_local_models.py` con internet |
| "Cannot download from HuggingFace" | `HF_HUB_OFFLINE=1` no está seteado | Verificar que app.py tiene `os.environ.setdefault("HF_HUB_OFFLINE", "1")` |
| EasyOCR intenta descargar en runtime | `download_enabled=True` en config | Cambiar a `download_enabled=False` en `document_processor/file_handler.py` |
| "Connection timeout" o delay de 30+ seg | Docling intenta contactar HF a pesar de offline mode | Verificar que `artifacts_path` apunta a la ruta correcta en config.ini |

---

## 📊 Espacio en disco requerido

| Componente | Tamaño | Ubicación | Notas |
|-----------|--------|-----------|-------|
| **Docling models** | ~1.5 GB | `./models/docling/` | Descargados una vez, reutilizados siempre |
| **EasyOCR models** | ~500 MB | `./models/easyocr/` | Solo si `do_ocr=true` y procesaste PDF con imágenes |
| **ChromaDB data** | Varía | `./chroma_data/` | Crece con cada PDF indexado (~1-2 MB/100 chunks) |
| **Ollama models** | 4-16 GB | `~/.ollama/models/` | LLM + Embeddings, depende del modelo |
| **Logs** | ~50 MB | `./logs/` | Rotados automáticamente |
| **Document cache** | ~100 MB | `./logs/document_cache/` | Pickles de PDFs procesados |
| **TOTAL** | **~8-20 GB** | Distribuido | La mayoría (~8-16 GB) son modelos Ollama |

---

## 🎓 Resumen técnico

RAG-AgentAI **sin** este cambio:
```
⚠️ Docling sin artifacts_path → StandardPdfPipeline.download_models_hf()
   → huggingface_hub.snapshot_download(repo_id="ds4sd/docling-models")
   → Intenta contactar huggingface.co en cada instanciación
   → Si no hay internet: falla o timeout 30+ segundos
```

RAG-AgentAI **con** este cambio (ahora):
```
✅ Docling con artifacts_path="./models/docling" → Usa caché local
   → StandardPdfPipeline.__init__(): if artifacts_path is None (no entra)
   → Nunca llama download_models_hf()
   → Funciona 100% offline
```

**Clave técnica:** La clase `StandardPdfPipeline` en Docling tiene esta lógica:
```python
# docling/pipeline/standard_pdf_pipeline.py:48-51
if pipeline_options.artifacts_path is None:
    self.artifacts_path = self.download_models_hf()  ← ¡Solo si NO pasamos artifacts_path!
else:
    self.artifacts_path = Path(pipeline_options.artifacts_path)  ← ¡Aquí nunca descarga!
```

Por eso es **crucial** pasar `artifacts_path` explícitamente en el `PdfPipelineOptions` —
si no lo pasamos, Docling intenta descargar.

---

## 📚 Documentación relacionada

- **SETUP.md → Paso 2.5** — Cómo pre-descargar modelos (esta guía lo resume)
- **FLUJO_COMPLETO.md → Fase 1** — Cómo funciona el parsing (actualizado para mencionar offline)
- **CODE_WALKTHROUGH.md → DocumentProcessor** — Código con anotaciones
- **config.ini → [document_processor]** — Parámetros configurables

---

**Resultado final:** RAG-AgentAI corre 100% localmente, con soberanía total del dato/IA. 🚀
