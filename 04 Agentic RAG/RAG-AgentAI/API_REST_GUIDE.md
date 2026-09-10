# API REST Guide — RAG-AgentAI

**Version:** 1.0.0  
**Purpose:** Query RAG system from external tools (Postman, cURL, Python, JavaScript, etc.)  
**Port:** 8000  

---

## 🚀 Quick Start

### 1. Install FastAPI
```bash
pip install fastapi uvicorn
```

### 2. Start API Server
```bash
python api_server.py
# Output: Starting API server on http://127.0.0.1:8000
```

### 3. Test Health
```bash
curl http://127.0.0.1:8000/health
```

### 4. Interactive Docs
Open in browser:
```
http://127.0.0.1:8000/docs
```

---

## 📡 Endpoints

### Health & Info

#### GET `/health`
Check API and ChromaDB status.

**Response:**
```json
{
  "status": "ok",
  "api": "running",
  "chromadb": {
    "heartbeat_ok": true,
    "heartbeat_ms": 4.2,
    "host": "localhost",
    "port": 8000,
    "total_collections": 3,
    "total_chunks": 1247
  }
}
```

#### GET `/info`
Get API information and endpoints.

**Response:**
```json
{
  "name": "RAG-AgentAI",
  "version": "1.0.0",
  "endpoints": {...},
  "settings": {...}
}
```

---

### Collections Management

#### GET `/collections`
List all indexed collections.

**Response:**
```json
[
  {"name": "my_document_a1b2", "chunks": 312},
  {"name": "financial_c3d4", "chunks": 425},
  {"name": "deepseek_e5f6", "chunks": 510}
]
```

#### GET `/collections/{collection_name}`
Get info about specific collection.

**Example:**
```bash
curl http://127.0.0.1:8000/collections/my_document_a1b2
```

**Response:**
```json
{"name": "my_document_a1b2", "chunks": 312}
```

#### DELETE `/collections/{collection_name}`
Delete a collection (for updating).

**Example:**
```bash
curl -X DELETE http://127.0.0.1:8000/collections/my_document_a1b2
```

**Response:**
```json
{
  "success": true,
  "message": "Collection 'my_document_a1b2' deleted successfully",
  "remaining_collections": ["financial_c3d4", "deepseek_e5f6"]
}
```

---

### Query

#### POST `/query`
Query the RAG system across collections.

**Request Body:**
```json
{
  "question": "¿Cuáles son los puntos principales?",
  "collections": ["my_document_a1b2", "financial_c3d4"]
}
```

**Optional:**
- Omit `collections` to search ALL collections
- Pass empty list `[]` to use all collections

**Response:**
```json
{
  "answer": "Los puntos principales son...",
  "verification": "Fuente verificada en documentos indexados",
  "collections_used": ["my_document_a1b2", "financial_c3d4"],
  "chunks_retrieved": 5
}
```

---

## 💻 Examples

### cURL

**List Collections:**
```bash
curl http://127.0.0.1:8000/collections
```

**Query (All Collections):**
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key points?"
  }'
```

**Query (Specific Collections):**
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key points?",
    "collections": ["doc1", "doc2"]
  }'
```

**Delete Collection:**
```bash
curl -X DELETE http://127.0.0.1:8000/collections/my_old_doc
```

---

### Postman

#### Import Collection
1. Open Postman
2. Click "Import" → "Paste raw text"
3. Paste this:

```json
{
  "info": {
    "name": "RAG-AgentAI API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "http://127.0.0.1:8000/health"
      }
    },
    {
      "name": "List Collections",
      "request": {
        "method": "GET",
        "url": "http://127.0.0.1:8000/collections"
      }
    },
    {
      "name": "Query (All Collections)",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "url": "http://127.0.0.1:8000/query",
        "body": {
          "mode": "raw",
          "raw": "{\"question\": \"What are the key points?\"}"
        }
      }
    },
    {
      "name": "Delete Collection",
      "request": {
        "method": "DELETE",
        "url": "http://127.0.0.1:8000/collections/collection_name_here"
      }
    }
  ]
}
```

#### Manual Setup in Postman

**1. List Collections**
- Method: GET
- URL: `http://127.0.0.1:8000/collections`
- Send

**2. Query**
- Method: POST
- URL: `http://127.0.0.1:8000/query`
- Headers: `Content-Type: application/json`
- Body (raw):
  ```json
  {
    "question": "¿Cuáles son los puntos clave?",
    "collections": ["doc1"]
  }
  ```

**3. Delete Collection**
- Method: DELETE
- URL: `http://127.0.0.1:8000/collections/doc_name`
- Send

---

### Python

```python
import requests

# Base URL
API_URL = "http://127.0.0.1:8000"

# 1. List collections
response = requests.get(f"{API_URL}/collections")
collections = response.json()
print(collections)

# 2. Query
query_data = {
    "question": "What are the main points?",
    "collections": None  # None = all collections
}
response = requests.post(f"{API_URL}/query", json=query_data)
result = response.json()
print(result["answer"])
print(result["verification"])

# 3. Delete collection
response = requests.delete(f"{API_URL}/collections/old_doc")
print(response.json())

# 4. Check health
response = requests.get(f"{API_URL}/health")
print(response.json())
```

### JavaScript/Node.js

```javascript
const API_URL = "http://127.0.0.1:8000";

// List collections
async function listCollections() {
  const response = await fetch(`${API_URL}/collections`);
  const collections = await response.json();
  console.log(collections);
}

// Query
async function query(question, collections = null) {
  const response = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, collections })
  });
  const result = await response.json();
  console.log(result.answer);
  console.log(result.verification);
}

// Delete collection
async function deleteCollection(name) {
  const response = await fetch(`${API_URL}/collections/${name}`, {
    method: "DELETE"
  });
  const result = await response.json();
  console.log(result);
}

// Usage
await listCollections();
await query("What are the main points?");
await deleteCollection("old_doc");
```

---

## 🔄 Common Workflows

### Update a Document

```bash
# 1. Delete old collection
curl -X DELETE http://127.0.0.1:8000/collections/my_doc

# 2. Upload new version via UI
# - Go to http://127.0.0.1:5020
# - Tab: "📚 Explorar Documentos"
# - Upload updated PDF
# - Click "📥 Indexar documento(s)"

# 3. Verify via API
curl http://127.0.0.1:8000/collections
```

### Bulk Query Multiple Collections

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Search across all documents",
    "collections": null
  }'
```

### Monitor Health

```bash
# Every 30 seconds
watch -n 30 'curl -s http://127.0.0.1:8000/health | jq .'
```

---

## 📊 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (missing data, invalid collection) |
| 404 | Collection not found |
| 500 | Server error |

---

## 🔗 Swagger UI

Interactive API documentation available at:
```
http://127.0.0.1:8000/docs
```

Try endpoints directly in the browser!

---

## 🚀 Production Deployment

To expose API to network:

```bash
python api_server.py
# Change 127.0.0.1 to 0.0.0.0 in code
```

Or use Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 api_server:app
```

---

## ⚙️ Configuration

Edit `api_server.py`:
```python
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",      # 0.0.0.0 = network accessible
        port=8000,           # Change port if needed
        log_level="info"
    )
```

---

## 📝 API Workflow Example

```
1. User submits question via Postman
   ↓
2. API receives POST /query request
   ↓
3. RAG-AgentAI processes:
   - Retrieves relevant chunks
   - Runs 3 agents (relevance, research, verification)
   - Returns answer + verification
   ↓
4. API returns JSON response
   ↓
5. Postman displays results
```

---

## 🆘 Troubleshooting

### "Connection refused" error
- Make sure API server is running: `python api_server.py`
- Check port 8000 is not in use: `netstat -an | grep 8000`

### API returns empty collections
- Index documents first via UI (http://127.0.0.1:5020)
- Or use CLI: `python scripts/upload_and_index.py document.pdf`

### Slow queries via API
- Apply performance optimizations (see PERFORMANCE_OPTIMIZATION.md)
- Same bottlenecks as UI (embeddings, CPU vs GPU)

---

**Ready to query via Postman?** Start the API server and visit http://127.0.0.1:8000/docs!
