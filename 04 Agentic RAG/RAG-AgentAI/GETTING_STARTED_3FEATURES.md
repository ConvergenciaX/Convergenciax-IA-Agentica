# Getting Started — Three New Features (5 minutes)

**Status:** ✅ Ready to Use  
**Date:** September 9, 2026  
**Features:** 📤 Upload & Optimize | ✅ Use All Collections | 🩺 Health Monitor

---

## 🎯 Quick Start

### Step 1: Start Services (3 Terminals)

**Terminal 1 — Ollama:**
```bash
ollama serve
# Wait for "Listening on http://localhost:11434"
```

**Terminal 2 — ChromaDB:**
```bash
C:\workspace-vc\env-llm-ia\Scripts\activate
chroma run --host localhost --port 8000
# Wait for "Listening on http://localhost:8000"
```

**Terminal 3 — RAG-AgentAI App:**
```bash
cd "C:\workspace-vc\LLM\CognitiveClass\convergenciax-langchaint-LLM\04 Agentic RAG\RAG-AgentAI"
C:\workspace-vc\env-llm-ia\Scripts\python.exe app.py
# Wait for "Launching Gradio server on http://127.0.0.1:5020"
```

### Step 2: Open Browser

```
http://127.0.0.1:5020
```

---

## 🚀 Test Each Feature (2 minutes each)

### Feature 1️⃣: 📤 Cargar y Optimizar Documentos

**Goal:** Upload a document with custom settings

**Steps:**
1. Go to tab: **"📚 Explorar Documentos"**
2. Scroll down to: **"📤 Cargar y Optimizar Documentos"**
3. Click **"📁 Subir documentos para indexar"** → choose any PDF
4. ☐ **Uncheck** "🖼️ Activar OCR" (for text-only PDF = faster)
5. (Optional) Enter **"Título personalizado"**: `My First Document`
6. Click **"📥 Indexar documento(s)"**
7. ✅ **Expected:** See "✅ Éxito: Indexadas 1 colección(es)"
8. **Verify:** All 3 dropdowns (Explorar, Preguntar, Consultar) now show new collection

**What You Learned:**
- Upload documents directly from UI (no scripts needed)
- Control OCR per-document
- Rename collections without changing filenames

---

### Feature 2️⃣: ✅ Usar TODAS las Colecciones

**Goal:** Search ALL indexed collections with one checkbox

**Steps:**
1. Go to tab: **"❓ Consultar Colecciones"**
2. Type question: **"¿Cuáles son los puntos principales?"**
3. ☑ **Check** "✅ Usar TODAS las colecciones disponibles"
4. Click **"Enviar ❓"**
5. ✅ **Expected:** Get answer from ANY indexed document
6. **Verify:** Answer appears even though you didn't manually select collections

**What You Learned:**
- One-click search across all collections
- Traditional multi-select still works (Feature works both ways)
- No need to manage dropdown selections

---

### Feature 3️⃣: 🩺 Estado de ChromaDB

**Goal:** Check ChromaDB health and collection stats

**Steps:**
1. Go to tab: **"❓ Consultar Colecciones"**
2. Scroll down to: **"🩺 Estado de ChromaDB"**
3. Click **"🔄 Verificar salud"**
4. ✅ **Expected Output:**
   ```
   **Heartbeat:** ✅ OK (4.2ms)
   Host:Port: `localhost:8000`
   Total Collections: 1
   Total Chunks: 247
   
   | Collection | Chunks |
   |---|---|
   | `my_first_document_a1b2` | 247 |
   ```
5. **Verify:** All data matches what you indexed

**What You Learned:**
- Monitor ChromaDB without logs
- See per-collection chunk counts
- Troubleshoot connection issues
- No page-load delays (on-demand check)

---

## ❌ Error Handling

### "Modelos EasyOCR faltantes" (Feature 1 with OCR)

**Fix:**
```bash
C:\workspace-vc\env-llm-ia\Scripts\python.exe scripts/download_easyocr_models.py
```

Or just **uncheck OCR** for text-only PDFs.

### "❌ Heartbeat: FAILED" (Feature 3)

**Fix:**
- Check that ChromaDB is running (Terminal 2)
- Restart: `chroma run --host localhost --port 8000`

### "No hay colecciones disponibles" (Feature 2 with no docs)

**Fix:**
- Index at least one document using Feature 1 first

### "❌ Ollama NO responde"

**Fix:**
- Check that Ollama is running (Terminal 1)
- Restart: `ollama serve`

---

## 📊 What's Happening Behind the Scenes

### Feature 1: 📤 Upload & Optimize

```
User uploads PDF
    ↓
DocumentProcessor(do_ocr_override=checkbox_value)
    ↓
Docling parses (offline, no HuggingFace)
    ↓
EasyOCR optional (if enabled)
    ↓
Chunks embedded via Ollama
    ↓
Stored in ChromaDB with custom collection name
    ↓
All dropdowns refresh automatically
```

**Code:** `document_processor/file_handler.py` + `app.py:index_from_explore()`

### Feature 2: ✅ Use All Collections

```
User checks "Use All" checkbox
    ↓
process_collection_query() gets fresh collection list
    ↓
Ignores dropdown selection
    ↓
Builds retriever over ALL collections
    ↓
RAG pipeline searches every document
    ↓
Returns answer from best match
```

**Code:** `app.py:process_collection_query(use_all=True)`

### Feature 3: 🩺 Health Monitor

```
User clicks "🔄 Verificar salud"
    ↓
HTTP GET to http://localhost:8000/api/v1/heartbeat
    ↓
Measure latency with time.perf_counter()
    ↓
Count collections via ChromaDB client
    ↓
Sum chunks per collection
    ↓
Format as Markdown table
    ↓
Display with ✅/❌ status
```

**Code:** `retriever/builder.py:get_health_status()` + `app.py:check_chroma_health()`

---

## 🔄 Complete Workflow (5 minutes)

1. **Start services** (Ollama, ChromaDB, App)
2. **Use Feature 1:** Upload document → set OCR → custom title → index
3. **Use Feature 2:** Check "Use All" → ask question → get answer
4. **Use Feature 3:** Check health → see stats + per-collection table
5. **Iterate:** Upload more docs → search them all → monitor health

---

## ✅ Verification Checklist

- [ ] Ollama running (Terminal 1 shows "Listening")
- [ ] ChromaDB running (Terminal 2 shows "Listening")
- [ ] App running (Terminal 3 shows Gradio URL)
- [ ] Feature 1: Upload successful → status shows ✅
- [ ] Feature 2: All collections search works → get answer
- [ ] Feature 3: Health check works → see table with chunks

---

## 🎓 Next Steps

### Learn More

- **[SETUP_3FEATURES.md](SETUP_3FEATURES.md)** — Detailed setup & configuration
- **[QUICK_REFERENCE.md](checkpoint/QUICK_REFERENCE.md)** — Quick reference for all features
- **[CHECKPOINT_20260909_3FEATURES.md](checkpoint/CHECKPOINT_20260909_3FEATURES.md)** — Technical implementation details

### Extend Features

- Add OCR model pre-check before enabling OCR
- Add collection deletion UI
- Add periodic background health monitoring
- Add collection merge/combine

### Troubleshoot

- Check `logs/rag_agentai.log` for detailed errors
- Run `python scripts/diagnostic.py` for pre-flight checks
- Check `config.ini` for connection settings

---

## 🎉 You're Ready!

All three features are **fully integrated** and working. No additional setup needed.

**Next action:** Open http://127.0.0.1:5020 and try Feature 1 → Feature 2 → Feature 3

---

## 📞 Need Help?

| Issue | Solution |
|-------|----------|
| App won't start | Check Python 3.13 is active: `python --version` |
| Ollama won't connect | Run `ollama serve` in Terminal 1 |
| ChromaDB won't connect | Run `chroma run --host localhost --port 8000` in Terminal 2 |
| OCR models missing | Run `python scripts/download_easyocr_models.py` |
| Health check fails | Make sure ChromaDB is running + logs/ directory exists |
| Can't find documents | Use Feature 1 to index at least one document first |

---

**Version:** 2026-09-09  
**Status:** ✅ Production Ready  
**Estimated Time to First Success:** 5 minutes
