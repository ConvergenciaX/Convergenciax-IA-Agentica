# Setup Guide — RAG-AgentAI with Three New UI Features

**Date:** 2026-09-09  
**Python Version:** 3.13+ (required)  
**Platform:** Windows 11  

---

## 🎯 What's New

Three major UI features are now available (as of 2026-09-09):

1. **📤 Cargar y Optimizar** — Upload documents with per-document OCR control
2. **✅ Usar TODAS** — Single-click checkbox to select all collections
3. **🩺 Estado de ChromaDB** — Real-time health monitoring panel

All three features are **fully integrated** and require only standard dependencies (already in `requirements.txt`).

---

## 📦 Prerequisites

### System Requirements
- Windows 11
- Python 3.13 (not 3.14, due to PyTorch compatibility)
- 6+ GB RAM (8+ recommended for LLM inference)
- Optional: GPU with CUDA support (RTX 3050+, A4500, etc.)

### External Services (Required)

#### 1. Ollama (LLM & Embeddings)
```bash
# Install: https://ollama.ai
ollama pull qwen2.5:7b-instruct-q4_K_M       # or qwen2.5:14b for better quality
ollama pull mxbai-embed-large                # Embeddings model

# Run in terminal:
ollama serve
# Listens on http://localhost:11434
```

#### 2. ChromaDB (Vector Store)
```bash
# Install via pip (inside Python env):
pip install chromadb

# Run in terminal:
chroma run --host localhost --port 8000
# Listens on http://localhost:8000
```

#### 3. Docling Models (Document Parsing - OFFLINE)
```bash
# Run once to download models locally:
python scripts/download_local_models.py

# This downloads to ./models/docling/ (offline operation)
```

#### 4. EasyOCR Models (Optional - for OCR Feature)
```bash
# Run once if you'll use OCR on scanned documents:
python scripts/download_easyocr_models.py

# This downloads to ./models/easyocr/ (offline operation)
# If you skip this, disable OCR in Feature 1 checkbox
```

---

## 🚀 Installation & Setup

### Step 1: Install Python Dependencies

```bash
# Activate Python 3.13 environment
C:\workspace-vc\env-llm-ia\Scripts\activate

# Install dependencies (one-time)
cd "C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\04 Agentic RAG\RAG-AgentAI"
python -m pip install -r requirements.txt

# Verify installation
python -c "import gradio, docling, chromadb, langchain_ollama; print('✓ All deps OK')"
```

**Dependencies Included:**
- `langchain` 0.3.16+ → RAG framework
- `gradio` 5.13.2 → UI web server
- `chromadb` 0.6.3 → Vector store (HTTP client)
- `docling` 2.15.0+ → PDF/DOCX parsing
- `easyocr` 1.7.2 → OCR for images (optional)
- `requests` 2.32.3 → Health checks (Feature 3)

### Step 2: Start External Services

**Terminal 1 — Ollama:**
```bash
ollama serve
# Output: Listening on http://localhost:11434
```

**Terminal 2 — ChromaDB:**
```bash
# Activate env first
C:\workspace-vc\env-llm-ia\Scripts\activate

chroma run --host localhost --port 8000
# Output: Listening on http://localhost:8000
```

**Terminal 3 — RAG-AgentAI App:**
```bash
cd "C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\04 Agentic RAG\RAG-AgentAI"
C:\workspace-vc\env-llm-ia\Scripts\python.exe app.py
# Output: Launching Gradio server on http://127.0.0.1:5020
```

### Step 3: Download Required Models (One-Time)

```bash
# Docling models (required for document parsing)
C:\workspace-vc\env-llm-ia\Scripts\python.exe scripts/download_local_models.py

# EasyOCR models (optional, needed only if using Feature 1 with OCR)
C:\workspace-vc\env-llm-ia\Scripts\python.exe scripts/download_easyocr_models.py
```

**Output:**
```
✓ Models downloaded to ./models/docling/
✓ Models downloaded to ./models/easyocr/ (if OCR)
```

### Step 4: Verify All Services

```bash
# In RAG-AgentAI Terminal (or separate Terminal):
C:\workspace-vc\env-llm-ia\Scripts\python.exe scripts/diagnostic.py

# Output:
# ✓ Ollama: OK (http://localhost:11434)
# ✓ ChromaDB: OK (http://localhost:8000)
# ✓ Docling artifacts: OK (./models/docling/)
# ✓ EasyOCR models: OK (./models/easyocr/)
```

### Step 5: Open Browser

```
http://127.0.0.1:5020
```

---

## 🎮 Using the Three New Features

### Feature 1: 📤 Cargar y Optimizar Documentos

**Location:** "📚 Explorar Documentos" tab → scroll down to "📤 Cargar y Optimizar Documentos"

**How to Use:**
1. Click on "📁 Subir documentos para indexar"
2. Select one or more PDF/DOCX/TXT/MD files
3. **Optional:** Uncheck "🖼️ Activar OCR" for text-only PDFs (faster: 3-5x)
4. **Optional:** Enter a "Título personalizado" to name the collection
5. Click "📥 Indexar documento(s)"
6. See status: "✅ Éxito: Indexadas X colección(es)"
7. **Automatic:** All 3 dropdown menus across the app refresh with new collection

**When to Use OCR:**
- ✅ **Enable OCR** if document has:
  - Scanned pages (image-based text)
  - Embedded images with text
  - Tables in graphic format
  - Handwritten annotations
- ❌ **Disable OCR** if document is:
  - Pure text PDF (copy-paste friendly)
  - DOCX with text (not scanned)
  - Markdown or plain text
  - Result: 3-5x faster indexing

**Requirements:**
- EasyOCR models must be pre-downloaded: `python scripts/download_easyocr_models.py`
- If models missing, you'll see error: "Modelos EasyOCR faltantes"

### Feature 2: ✅ Usar TODAS las Colecciones

**Location:** "❓ Consultar Colecciones" tab → top section

**How to Use:**
1. Type your question in "Tu pregunta"
2. **Option A (Traditional):** Select specific collections from dropdown
   - Click "❓ Enviar"
   - Result: Searches only selected collections
3. **Option B (New):** Check "✅ Usar TODAS las colecciones disponibles"
   - Dropdown is ignored
   - Click "❓ Enviar"
   - Result: Searches ALL indexed collections at once

**Use Case:**
- Quick search without multi-select
- When you've indexed many documents and want comprehensive search
- One-click to search everything

**Note:** Feature works with or without any pre-indexed collections. If no collections exist, error message guides you.

### Feature 3: 🩺 Estado de ChromaDB

**Location:** "❓ Consultar Colecciones" tab → scroll down to "🩺 Estado de ChromaDB"

**How to Use:**
1. Click "🔄 Verificar salud" button
2. See formatted status panel:
   - **Heartbeat:** ✅ OK (4.2ms) or ❌ FAILED
   - **Host:Port:** Connection details
   - **Total Collections:** Count of indexed collections
   - **Total Chunks:** Sum of all chunks across all collections
   - **Table:** Per-collection breakdown with chunk counts

**Troubleshooting:**
- **❌ Heartbeat FAILED:** ChromaDB not running
  - Solution: `chroma run --host localhost --port 8000`
- **❌ Connection timeout:** Network issue or service too slow
  - Solution: Check Chroma is running, verify network
- **0 Collections:** No documents indexed yet
  - Solution: Use Feature 1 to index documents

**Benefits:**
- Monitor index health without logs
- Verify indexing succeeded
- Check collection sizes before querying
- Non-blocking: triggered on demand, not automatic

---

## ⚙️ Configuration

### config.ini

All settings are in `config.ini`. Key settings for new features:

```ini
[document_processor]
# Feature 1: OCR settings
do_ocr = true                                    # Default OCR mode (can be overridden per-document)
docling_artifacts_path = ./models/docling        # Path to Docling models
docling_ocr_models_path = ./models/easyocr       # Path to EasyOCR models

[chroma]
# Feature 3: ChromaDB connection
host = localhost
port = 8000

[gradio]
# UI server
server_name = 127.0.0.1
server_port = 5020
```

### Environment Variables (Offline Mode)

Already set in `app.py` (no action needed):
```python
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
```

This ensures 100% local operation without contacting HuggingFace.

---

## 📊 Verification Checklist

After setup, verify each feature works:

### ✅ Feature 1 Verification

```bash
# Terminal:
python scripts/test_rag_complete.py

# Expected output:
# ✓ DocumentProcessor initialized
# ✓ Processed 1 documento(s)
# ✓ Indexed in ChromaDB
# ✓ Retrieved documents
# ✓ RAG pipeline completed
```

Or in UI:
```
1. Go to "📚 Explorar Documentos" tab
2. Scroll to "📤 Cargar y Optimizar"
3. Upload example PDF
4. Uncheck OCR
5. Click "📥 Indexar documento(s)"
6. Expect: ✅ Success message + collection in dropdowns
```

### ✅ Feature 2 Verification

```
1. Go to "❓ Consultar Colecciones" tab
2. Type a question
3. Check "✅ Usar TODAS las colecciones"
4. Click "Enviar ❓"
5. Expect: Answer from any indexed collection
```

### ✅ Feature 3 Verification

```
1. Go to "❓ Consultar Colecciones" tab
2. Scroll to "🩺 Estado de ChromaDB"
3. Click "🔄 Verificar salud"
4. Expect: 
   - ✅ Heartbeat OK + latency (ms)
   - Host:Port shown
   - Collections and chunks count
   - Markdown table with per-collection breakdown
```

---

## 🔧 Troubleshooting

### Problem: "❌ Ollama NO responde"

**Solution:**
```bash
# Terminal 1:
ollama serve

# Wait 5 seconds for startup
# Then check: curl http://localhost:11434/api/tags
```

### Problem: "❌ ChromaDB NO responde"

**Solution:**
```bash
# Terminal 2:
C:\workspace-vc\env-llm-ia\Scripts\activate
chroma run --host localhost --port 8000

# Wait 3 seconds for startup
# Then check: curl http://localhost:8000/api/v1/heartbeat
```

### Problem: "Modelos EasyOCR faltantes" (Feature 1)

**Solution:**
```bash
C:\workspace-vc\env-llm-ia\Scripts\python.exe scripts/download_easyocr_models.py

# Or disable OCR:
# - In Feature 1, uncheck "🖼️ Activar OCR"
# - Or in config.ini: do_ocr = false
```

### Problem: "No hay colecciones disponibles" (Feature 2)

**Solution:**
- Index at least one document first using Feature 1
- Or use main "💬 Preguntar" tab to upload and process documents

### Problem: "❌ Heartbeat: FAILED" (Feature 3)

**Solution:**
- Ensure ChromaDB is running (see "ChromaDB NO responde" above)
- Check host:port in config.ini matches running service
- Restart ChromaDB service

### Problem: App crashes on startup

**Solution:**
```bash
# Check Python 3.13 is active:
python --version
# Should output: Python 3.13.x

# Reinstall dependencies:
python -m pip install --upgrade -r requirements.txt

# Check imports:
python -c "import app; print('OK')"
```

---

## 📚 Scripts Reference

All scripts assume you're in RAG-AgentAI directory:

```bash
# Download Docling models (one-time, required)
python scripts/download_local_models.py

# Download EasyOCR models (one-time, optional for OCR in Feature 1)
python scripts/download_easyocr_models.py

# Pre-flight health checks
python scripts/diagnostic.py

# Upload and index a PDF (alternative to Feature 1 UI)
python scripts/upload_and_index.py examples/sample.pdf -t "My Custom Title"

# Search indexed collections (alternative to Feature 2 UI)
python scripts/search_by_title.py query my_collection "question here"

# Inspect ChromaDB contents (alternative to Feature 3 UI)
python scripts/inspect_chroma.py

# Full end-to-end test
python scripts/test_rag_complete.py
```

---

## 🌐 API/Integration Reference

### Feature 3: Health Status Response

If you call `retriever_builder.get_health_status()` in code:

```python
health = {
    "heartbeat_ok": True,
    "heartbeat_ms": 4.2,
    "host": "localhost",
    "port": 8000,
    "total_collections": 3,
    "total_chunks": 1247,
    "collections_detail": [
        {"name": "doc1_a1b2", "count": 312},
        {"name": "doc2_c3d4", "count": 425},
        {"name": "doc3_e5f6", "count": 510},
    ],
    "error": None
}
```

### Feature 1: DocumentProcessor with OCR Override

```python
from document_processor.file_handler import DocumentProcessor

# Create processor with custom OCR setting
processor = DocumentProcessor(do_ocr_override=False)  # Disable OCR

# Process files
collections = processor.process([file1, file2])
# Returns: {"collection_name": [Document, Document, ...], ...}
```

---

## 📝 Logs & Debugging

### Where Logs Go

```
logs/
├── rag_agentai.log           # Main application log
└── rag_agentai.log.1         # Rotated backups (up to 5 files)
```

### Log Level Configuration

In `config.ini`:
```ini
[logging]
level = DEBUG    # DEBUG (verbose), INFO, WARNING, ERROR
```

### Useful Log Entries to Watch

```log
# Feature 1 indexing:
[INFO] Indexando 2 doc(s) desde Explorar tab
[INFO]   OCR override: False, Custom title: 'My Document'
[INFO] ✓ Indexados 1 colección(es)

# Feature 2 querying:
[INFO] Usando TODAS las colecciones: ['doc1_a1b2', 'doc2_c3d4']

# Feature 3 health check:
[INFO] ✓ ChromaDB heartbeat OK (4.2ms)
[INFO] ✓ ChromaDB: 3 collections, 1247 chunks
```

---

## ✅ Final Checklist

Before using the app, ensure:

- [ ] Python 3.13 installed and activated
- [ ] `requirements.txt` installed: `pip install -r requirements.txt`
- [ ] Ollama running: `ollama serve` (Terminal 1)
- [ ] ChromaDB running: `chroma run --host localhost --port 8000` (Terminal 2)
- [ ] Models downloaded: `python scripts/download_local_models.py`
- [ ] Models verified: `python scripts/diagnostic.py` shows all ✓
- [ ] App starts: `python app.py` (Terminal 3)
- [ ] Browser opens: http://127.0.0.1:5020

---

## 🎉 Ready to Go!

All three features are **fully functional** and integrated. No additional setup needed beyond standard RAG-AgentAI installation.

**Test them now:**
1. Upload a document (Feature 1)
2. Search all collections (Feature 2)
3. Check health status (Feature 3)

---

## 📞 Support / Troubleshooting

For detailed help:
- Check `CHECKPOINT_20260909_3FEATURES.md` for technical details
- Check `QUICK_REFERENCE.md` for user-facing quick start
- Check logs in `logs/rag_agentai.log` for errors

---

**Version:** 2026-09-09  
**Status:** ✅ Production Ready  
**Last Updated:** September 9, 2026
