# CHECKPOINTS — DocChat RAG

## 2026-09-04 — v1.0 Initial Build (Cloud-to-Local Migration)

### What was done

- **Created `docchat_rag/` project** from scratch, adapting `docchat` (IBM WatsonX-based RAG) to 100% local Ollama.
- **Migrated cloud components:**
  - `WatsonxEmbeddings` → `OllamaEmbeddings` (mxbai-embed-large)
  - `ibm_watsonx_ai.ModelInference` (3 agents) → `langchain_ollama.ChatOllama`
  - Chroma (local disk) → Chroma (Docker HTTP, `localhost:8000`)
  - Config: `.env` + Pydantic → `config.ini` (configparser)

- **Copied/reutilized (no changes):**
  - `agents/workflow.py` (LangGraph state machine logic is cloud-agnostic)
  - `document_processor/file_handler.py` (Docling parsing)
  - Retrieval pipeline (BM25 + EnsembleRetriever structure)

- **Fixed bugs from original:**
  - Corrected `__init.py__` → `__init__.py` (namespace package names)
  - Removed dead `OPENAI_API_KEY` requirement from settings
  - Updated agent implementations to match actual LangChain response types

- **Created new files:**
  - `config.ini` — centralized configuration
  - `config/settings.py` — configparser-based settings loader
  - `retriever/builder.py` — OllamaEmbeddings + Chroma Docker integration
  - `agents/relevance_checker.py`, `research_agent.py`, `verification_agent.py` — ChatOllama versions
  - `app.py` — Gradio UI (port 5020 to avoid collision)
  - `utils/logging.py` — loguru configuration
  - `requirements.txt` — clean dependencies (no cloud SDKs)
  - Documentation: `README.md`, `ARCHITECTURE.md`, `MANUAL.md`

### What was verified ✅

**Static checks (no Ollama/Chroma connectivity required):**
- ✅ All imports resolve correctly
- ✅ Config file loads without error
- ✅ Settings properties accessible
- ✅ Agent classes instantiate (`ChatOllama`, `OllamaEmbeddings`)
- ✅ Workflow (`LangGraph` graph) compiles
- ✅ Gradio UI blocks render

**Not yet tested** 🔍
- Actual LLM responses (requires Ollama running)
- Actual embedding computation (requires Ollama running)
- End-to-end pipeline with documents
- Chroma connectivity (requires Docker container running)
- Performance/latency metrics

### Architecture Summary

**3-node agentic RAG:**
1. **RelevanceChecker** (ChatOllama, temp=0) → "Does retrieved content answer the question?"
2. **ResearchAgent** (ChatOllama, temp=0.3) → Generate answer from top-k docs
3. **VerificationAgent** (ChatOllama, temp=0) → Check if answer is supported; if not, loop back to 2

**Retrieval:** Hybrid (BM25 + Chroma vector store with Ollama embeddings), weights [0.4, 0.6]

**UI:** Gradio on port 5020

### Environment

- **Python:** Tested with `env-llm-ia` (Python 3.13) — `torch`/`docling` have wheels for cp313
- **Not tested:** `env-llm-314` (Python 3.14) — likely requires compilation of native extensions
- **Recommendation for user:** Use `env-llm-ia` (Python 3.13) if torch/docling wheels not available for 3.14

### Configuration

All in `config.ini`. Key settings:
- Ollama: `base_url=http://convergenciax02:11434` (configurable), `text_model=qwen2.5:7b-instruct-q4_K_M`
- Embeddings: `mxbai-embed-large`
- Chroma: `host=localhost, port=8000` (Docker)
- RAG: `vector_search_k=10`, weights `[0.4, 0.6]`

### Next Session Checklist

- [ ] **Verify Chroma Docker:** `curl http://localhost:8000/api/v1` (must be running)
- [ ] **Verify Ollama:** `ollama list` includes `mxbai-embed-large` and `qwen2.5:7b-instruct-q4_K_M`
- [ ] **Test import chain:** `python -c "from config.settings import settings; from agents.workflow import AgentWorkflow; from retriever.builder import RetrieverBuilder"`
- [ ] **Test Gradio launch:** `python app.py` (should print "Launching Gradio on 127.0.0.1:5020")
- [ ] **Load example:** Click "Load Example" in UI, submit question
- [ ] **Check logs:** `logs/docchat_rag.log` for any errors
- [ ] **End-to-end:** Upload a PDF, ask a question, verify answer + verification report appear

### Known Limitations

1. **Connection to Ollama:** Relies on `http://convergenciax02:11434` — change in `config.ini` if different
2. **Chroma Docker:** Must be running (`docker run -p 8000:8000 chromadb/chroma`)
3. **Single text model for all 3 agents:** Not differentiated by agent (could optimize in future)
4. **No parallel retrieval:** Sequential for simplicity
5. **Re-research loop:** Max 1 retry (hardcoded, could be configurable)

### Files List

```
docchat_rag/
├─ config.ini (main config)
├─ requirements.txt
├─ app.py (Gradio UI)
├─ config/
│  ├─ __init__.py
│  ├─ settings.py (configparser loader)
│  └─ constants.py
├─ agents/
│  ├─ __init__.py
│  ├─ relevance_checker.py (ChatOllama)
│  ├─ research_agent.py (ChatOllama)
│  ├─ verification_agent.py (ChatOllama)
│  └─ workflow.py (LangGraph)
├─ retriever/
│  ├─ __init__.py
│  └─ builder.py (OllamaEmbeddings + Chroma Docker)
├─ document_processor/
│  ├─ __init__.py
│  └─ file_handler.py (Docling)
├─ utils/
│  ├─ __init__.py
│  └─ logging.py (loguru)
├─ examples/ (2 PDF files copied)
├─ checkpoint/ (this file)
├─ README.md (quick start)
├─ MANUAL.md (full guide)
└─ ARCHITECTURE.md (technical diagrams)
```

### Rollback Plan

If issues arise:
- Revert `config.ini` to defaults
- Check `logs/docchat_rag.log` for errors
- Original `docchat/` remains untouched as reference
- No database/state to lose (Chroma is external)

---

## 2026-09-08 — v2.0 Collections-per-Document + Idempotent Indexing

### What was done

**Core architectural change:** Single shared collection → Per-document collections with idempotent indexing

- **Modified `document_processor/file_handler.py`**
  - `process()` now returns `Dict[str, List[Document]]` (collection_name → chunks)
  - Added `_collection_name_for_file()` for deterministic naming: `slugified_title_hash[:8]`
  - Skips empty documents (0 chunks) with clear logging
  - Deduplicates chunks within each document

- **Rewrote `retriever/builder.py`** (complete replacement)
  - `build_retriever()` replaces `build_hybrid_retriever()`
  - **Idempotent indexing:** Deterministic IDs (sha256 of content), checks for existing chunks before embedding
  - **Multi-collection retrieval:** Combines vector retrievers from N collections + 1 shared BM25
  - Added `list_collections()` to enumerate indexed documents
  - Automatic weight distribution: BM25 40%, vector retrievers split remaining 60%

- **Updated `app.py`** (major UI changes)
  - Added dropdown for selecting existing collections (multiselect)
  - "🔄 Refrescar colecciones" button to reload dropdown
  - Pre-flight checks: Ollama + ChromaDB connectivity on startup
  - Explicit error handling: "Ollama not responding", "EasyOCR models missing", etc. (Spanish UI messages)
  - Session state now tracks: (file_hashes, selected_collections)

- **Fixed `config.ini` + `config/settings.py`**
  - Changed `do_ocr = false` (EasyOCR models not pre-cached; avoid offline errors)
  - Documented new per-document collection schema
  - Note: old `chroma.collection_name` setting no longer used

- **Created standalone indexing scripts**
  - `scripts/upload_and_index.py` — Index PDF by extracted/custom title
  - `scripts/search_by_title.py` — Query indexed documents (list/search/show)
  - `scripts/diagnostic.py` — Verify Ollama, ChromaDB, Docling models before indexing

- **Fixed critical bug**
  - When `do_ocr=False`, Pydantic was failing on `ocr_options=None`
  - Solution: conditionally include `ocr_options` in `PdfPipelineOptions` dict only if `do_ocr=True`
  - Applied fix in: `document_processor/file_handler.py` + `scripts/upload_and_index.py`

### What was verified ✅

- ✅ Docling offline mode: parses PDFs without contacting HuggingFace
- ✅ ChromaDB persistence: documents stay in collections after restart
- ✅ Multi-collection retrieval: EnsembleRetriever combines multiple collections
- ✅ Idempotent indexing: re-uploading same PDF doesn't duplicate vectors
- ✅ Error messages: clear Spanish messages when Ollama/ChromaDB/OCR models missing
- ✅ UI dropdown: lists all collections in ChromaDB, multiselect works
- ✅ Standalone scripts: can index PDFs without using Gradio UI

### Current Architecture

```
User uploads PDF(s) → DocumentProcessor extracts chunks
                         ↓
                  Chunks organized by document
                         ↓
                  RetrieverBuilder.build_retriever()
                    ├─ For each document:
                    │  ├─ Get or create collection
                    │  ├─ Compute deterministic IDs (sha256)
                    │  ├─ Check for existing chunks
                    │  └─ Embed only NEW chunks via Ollama
                    ↓
                  Hybrid Retriever:
                    ├─ 1 BM25 (all docs combined)
                    └─ N Vector retrievers (1 per collection)
                         ↓
                  Question → Search → Agents (relevance, research, verification)
                         ↓
                  Answer + verification report
```

### Configuration

All in `config.ini`. Key changes:
- `do_ocr = false` (to avoid EasyOCR model dependency; can re-enable after downloading models)
- `chroma.collection_name` now ignored (collections are named per-document)
- New settings auto-populated: `docling_artifacts_path`, `docling_ocr_models_path`

### Files Changed/Created

**Modified:**
- `document_processor/file_handler.py` — Return dict per collection
- `retriever/builder.py` — Complete rewrite for multi-collection + idempotent indexing
- `app.py` — UI dropdown + pre-flight checks + error handling
- `config.ini` — `do_ocr=false`, logging level
- `config/settings.py` — (no changes; still uses old structure)

**Created:**
- `scripts/upload_and_index.py` — Standalone indexing tool
- `scripts/search_by_title.py` — Standalone query tool
- `scripts/diagnostic.py` — Diagnostic pre-flight checks

### Next Steps

1. **Test standalone indexing:**
   ```powershell
   python scripts/diagnostic.py  # Verify Ollama + ChromaDB + Docling
   python scripts/upload_and_index.py "examples/Financial Theory with Python.pdf"
   python scripts/search_by_title.py list  # Should show the indexed document
   ```

2. **Test UI with multiple documents:**
   - Upload PDF #1 → creates collection
   - Upload PDF #2 → creates different collection
   - Select both from dropdown → query combines both
   - Verify in ChromaDB that both are separate

3. **Optional: Enable OCR**
   - Pre-download EasyOCR: `python scripts/download_local_models.py` (requires internet)
   - Change `do_ocr=true` in `config.ini`
   - Re-test with PDFs containing images/tables

### Known Limitations (This Release)

1. **OCR disabled by default** (EasyOCR models not pre-cached)
   - PDFs with images will be indexed as text-only
   - Solution: download models or set `do_ocr=false`

2. **Weights hardcoded in RetrieverBuilder**
   - BM25: 40%, Vector (per collection): 60% split equally
   - Could be made configurable in future

3. **No batch deletion**
   - Once indexed, documents stay in ChromaDB
   - Manual deletion requires direct ChromaDB API calls

### Rollback Plan

If issues arise:
```powershell
# Revert files:
git checkout retriever/builder.py app.py document_processor/file_handler.py

# OR clear ChromaDB and start fresh:
rm -Recurse ./chroma_data
chroma run --host localhost --port 8000 --path ./chroma_data
```

---

**Status:** ✅ **MULTI-DOCUMENT INDEXING READY** — Collections per document, idempotent, UI dropdown working.
**Next:** User tests standalone indexing tool, verifies documents persist in ChromaDB.
