# DocChat RAG — Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Gradio Web UI (Port 5020)                                      │
│  ├─ File upload (PDF/DOCX/TXT/MD)                              │
│  ├─ Question input textbox                                      │
│  └─ Answer + Verification report output                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  DocumentProcessor (Docling)                                     │
│  ├─ Parses files → Markdown                                     │
│  ├─ Chunks by headers (#, ##)                                   │
│  └─ Caches to disk (SHA256 dedup)                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  RetrieverBuilder (Hybrid)                                       │
│  ├─ OllamaEmbeddings (mxbai-embed-large via Ollama)            │
│  ├─ Chroma Vector Store (Docker, HTTP)                         │
│  ├─ BM25 Retriever (keyword search)                             │
│  └─ EnsembleRetriever (weights: 0.4 BM25 + 0.6 vector)         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  AgentWorkflow (LangGraph State Machine)                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Node 1: RelevanceChecker                                 │   │
│  │ └─ LLM: ChatOllama (qwen2.5:7b, temp=0.0)               │   │
│  │ └─ Decision: CAN_ANSWER | PARTIAL | NO_MATCH           │   │
│  └─────────┬───────────────────────────────────────────────┘   │
│            │                                                    │
│      ┌─────▼──────────────────┐   ┌────────────────────┐      │
│      │ If relevant:           │   │ If not relevant:   │      │
│      │ Continue to Node 2      │   │ End (no answer)    │      │
│      └─────┬──────────────────┘   └────────────────────┘      │
│            │                                                    │
│  ┌─────────▼─────────────────────────────────────────────────┐ │
│  │ Node 2: ResearchAgent                                     │ │
│  │ └─ LLM: ChatOllama (qwen2.5:7b, temp=0.3)                │ │
│  │ └─ Generates answer from top-k retrieved chunks          │ │
│  │ └─ Output: draft_answer                                   │ │
│  └─────────┬─────────────────────────────────────────────────┘ │
│            │                                                    │
│  ┌─────────▼─────────────────────────────────────────────────┐ │
│  │ Node 3: VerificationAgent                                │ │
│  │ └─ LLM: ChatOllama (qwen2.5:7b, temp=0.0)               │ │
│  │ └─ Fact-checks: Is answer supported by docs?            │ │
│  │ └─ Output: "Supported: YES/NO/PARTIAL, ..."            │ │
│  └─────────┬─────────────────────────────────────────────────┘ │
│            │                                                    │
│      ┌─────▼──────────────────┐   ┌──────────────────┐        │
│      │ If answer supported:   │   │ If not supported:│        │
│      │ End (output answer)    │   │ Loop back to 2   │        │
│      │                        │   │ (re-research)    │        │
│      └────────────────────────┘   └────────┬─────────┘        │
│                                            │                   │
│                                    (max 1 retry)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                             │
                      ┌──────▼─────┐
                      │   Output   │
                      │ - Answer   │
                      │ - Report   │
                      └────────────┘
```

## Data Flow

### 1. Document Ingestion

```
User uploads files
    ↓
DocumentProcessor.process()
    ├─ SHA256 hash of content
    ├─ Check cache (disk)
    │  ├─ If cached & fresh → load .pkl
    │  └─ If not cached → Docling parse
    ├─ Docling: file → Markdown
    ├─ MarkdownHeaderTextSplitter: Markdown → chunks by # headers
    ├─ Dedup chunks (content hash)
    └─ Return: List[LangChain Document]
```

### 2. Retrieval Setup

```
Chunks → RetrieverBuilder.build_hybrid_retriever()
    ├─ OllamaEmbeddings (mxbai-embed-large)
    │  └─ Embed each chunk
    ├─ Chroma.from_documents()
    │  ├─ Connect to Chroma Docker (HTTP)
    │  ├─ Store embeddings + chunks in "docchat_documents" collection
    │  └─ Persist in Chroma (not local disk)
    ├─ BM25Retriever.from_documents()
    │  └─ Build keyword index
    └─ EnsembleRetriever([BM25, Chroma], weights=[0.4, 0.6])
       ↓ returns top-10 most relevant chunks
```

### 3. Question Processing (State Machine)

```
Question → AgentWorkflow.full_pipeline()
    ├─ initial_state = {question, documents, retriever, ...}
    │
    ├─ Node 1: check_relevance_step()
    │  └─ RelevanceChecker.check(question, retriever, k=20)
    │     ├─ retriever.invoke(question) → top 20 docs
    │     ├─ Prompt: "Can these docs answer this question?"
    │     ├─ LLM response: "CAN_ANSWER" / "PARTIAL" / "NO_MATCH"
    │     └─ state["is_relevant"] = True/False
    │
    ├─ Conditional: is_relevant?
    │  ├─ False → END (return generic "not related" message)
    │  └─ True → research
    │
    ├─ Node 2: _research_step()
    │  └─ ResearchAgent.research(question, retriever)
    │     ├─ retriever.invoke(question) → top-k docs
    │     ├─ Limit to max_context_docs (5)
    │     ├─ Prompt: "Answer this based ONLY on the docs"
    │     └─ LLM response: detailed answer
    │
    ├─ Node 3: _verification_step()
    │  └─ VerificationAgent.verify(question, answer, retriever)
    │     ├─ retriever.invoke(question) → docs
    │     ├─ Prompt: "Is this answer supported by the docs?"
    │     └─ LLM response: "Supported: YES/NO/PARTIAL, ..."
    │
    └─ Conditional: "Supported: NO" in report?
       ├─ True → re_research (loop back to Node 2, max 1x)
       └─ False → END (output answer + report)
```

## Component Details

### DocumentProcessor

**File:** `document_processor/file_handler.py`

- **Docling:** Parses PDF/DOCX/TXT/MD to Markdown (handles OCR via EasyOCR)
- **MarkdownHeaderTextSplitter:** Splits on `#` and `##` headers (semantic chunking)
- **Cache:** `.pkl` files keyed by content SHA256, expires after 7 days
- **Deduplication:** Cross-file chunk dedup via content hash

### RetrieverBuilder

**File:** `retriever/builder.py`

- **OllamaEmbeddings:** Embeddings via local Ollama (model: `mxbai-embed-large`)
  - Dimension: ~1024D (depends on model)
  - Computed locally, no API calls
  
- **Chroma:** Vector store (Docker, HTTP client)
  - Collection: `docchat_documents`
  - Connection: `http://localhost:8000` (configurable)
  - Persists embeddings + metadata
  
- **BM25Retriever:** Sparse retrieval (keywords)
  - Built from chunks after embedding
  - Independent of Ollama
  
- **EnsembleRetriever:** Combines both
  - Weights: [0.4 BM25, 0.6 Chroma vector]
  - Configurable in `config.ini`

### Agents (LLM-based nodes)

All use `ChatOllama` (LangChain wrapper) instead of raw Ollama/WatsonX SDK.

#### RelevanceChecker

**File:** `agents/relevance_checker.py`

- Model: `qwen2.5:7b` (from `config.ini`)
- Temperature: 0.0 (deterministic)
- Output: Single word classification
- Logic: "Do the docs discuss this topic?"

#### ResearchAgent

**File:** `agents/research_agent.py`

- Model: `qwen2.5:7b`
- Temperature: 0.3 (some variation)
- Max tokens: 300
- Logic: "Generate the best answer from these docs"

#### VerificationAgent

**File:** `agents/verification_agent.py`

- Model: `qwen2.5:7b`
- Temperature: 0.0 (deterministic)
- Max tokens: varies (could be shorter)
- Logic: "Is this answer supported by the docs?"

### Workflow Orchestration

**File:** `agents/workflow.py`

- LangGraph `StateGraph` with 3 nodes
- State type: `TypedDict` with all pipeline data
- Conditional edges implement re-research loop
- Compiled once at initialization (efficient)

## Configuration Points

**File:** `config.ini`

| Section | Key | Default | Purpose |
|---------|-----|---------|---------|
| `[ollama]` | `base_url` | `http://convergenciax02:11434` | Ollama endpoint |
| | `text_model` | `qwen2.5:7b-instruct-q4_K_M` | LLM for all 3 agents |
| | `temperature` | `0.1` | Default temp (individual agents override) |
| `[embeddings]` | `embedding_model` | `mxbai-embed-large` | Embedding model |
| `[chroma]` | `host` / `port` | `localhost` / `8000` | Chroma Docker connection |
| | `collection_name` | `docchat_documents` | Vector collection |
| `[rag]` | `vector_search_k` | `10` | Docs to retrieve |
| | `ensemble_weights` | `0.4,0.6` | BM25 and vector weights |
| | `max_context_docs` | `5` | Docs passed to LLM |
| `[gradio]` | `server_port` | `5020` | Web UI port |
| `[logging]` | `level` | `INFO` | Log verbosity |

## Performance Characteristics

**Typical latency (per question):**

- Retrieval: 0.1-0.5s (BM25 + Chroma)
- LLM calls: 5-30s (depending on model + hardware)
- **Total:** ~10-45s for full pipeline

**Bottleneck:** LLM inference (Ollama response time)

**Optimization levers:**

1. Smaller/faster model (e.g., `qwen2.5:7b` vs `qwen3:32b`)
2. Reduce `max_context_docs` (fewer docs → shorter context → faster LLM)
3. Reduce `vector_search_k` (fewer docs to consider)
4. Increase Ollama `keep_alive` to avoid model reloads
5. Use GPU (e.g., NVIDIA CUDA) for Ollama and Chroma

## Error Handling

All components log to:
- **`logs/docchat_rag.log`** (file, rotated)
- **stdout** (console, real-time)

Errors are caught and logged at each stage; pipeline doesn't halt on partial failures.

---

See `MANUAL.md` for tuning and troubleshooting guide.
