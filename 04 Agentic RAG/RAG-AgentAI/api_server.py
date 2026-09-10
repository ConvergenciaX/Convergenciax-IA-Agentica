#!/usr/bin/env python3
"""REST API para RAG-AgentAI — Consulta desde Postman, cURL, etc."""

import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from document_processor.file_handler import DocumentProcessor
from retriever.builder import RetrieverBuilder
from agents.workflow import AgentWorkflow
from config.settings import settings
from utils.logging import logger

# FastAPI app
app = FastAPI(
    title="RAG-AgentAI API",
    description="Local RAG system with Ollama + ChromaDB",
    version="1.0.0"
)

# Enable CORS (para Postman, navegadores, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
retriever_builder = None
workflow = None
processor = None

# Models
class QueryRequest(BaseModel):
    """Query request model."""
    question: str
    collections: Optional[List[str]] = None  # Si None, usa todas las colecciones

class QueryResponse(BaseModel):
    """Query response model."""
    answer: str
    verification: str
    collections_used: List[str]
    chunks_retrieved: int

class CollectionInfo(BaseModel):
    """Collection information model."""
    name: str
    chunks: int

class HealthStatus(BaseModel):
    """ChromaDB health status."""
    heartbeat_ok: bool
    heartbeat_ms: Optional[float]
    host: str
    port: int
    total_collections: int
    total_chunks: int
    error: Optional[str] = None

class DeleteResponse(BaseModel):
    """Delete collection response."""
    success: bool
    message: str
    remaining_collections: List[str]

# Startup
@app.on_event("startup")
async def startup():
    """Initialize components on startup."""
    global retriever_builder, workflow, processor
    logger.info("🚀 RAG-AgentAI API Starting...")

    try:
        retriever_builder = RetrieverBuilder()
        workflow = AgentWorkflow()
        processor = DocumentProcessor()
        logger.info("✅ All components initialized")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise

# Health check
@app.get("/health")
async def health_check() -> Dict:
    """Check API and ChromaDB health."""
    try:
        health = retriever_builder.get_health_status()
        return {
            "status": "ok" if health["heartbeat_ok"] else "error",
            "api": "running",
            "chromadb": health
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "api": "running",
            "error": str(e)
        }

# Collections endpoints
@app.get("/collections", response_model=List[CollectionInfo])
async def list_collections():
    """List all indexed collections."""
    try:
        collections = retriever_builder.list_collections()
        result = []
        for col_name in sorted(collections):
            details = retriever_builder.get_collection_details(col_name)
            if details:
                result.append(CollectionInfo(
                    name=col_name,
                    chunks=details["chunks"]
                ))
        return result
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections/{collection_name}")
async def get_collection_info(collection_name: str) -> CollectionInfo:
    """Get info about specific collection."""
    try:
        details = retriever_builder.get_collection_details(collection_name)
        if not details:
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
        return CollectionInfo(
            name=collection_name,
            chunks=details["chunks"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/collections/{collection_name}", response_model=DeleteResponse)
async def delete_collection(collection_name: str) -> DeleteResponse:
    """Delete a collection (for updating)."""
    try:
        success = retriever_builder.delete_collection(collection_name)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to delete '{collection_name}'")

        remaining = retriever_builder.list_collections()
        return DeleteResponse(
            success=True,
            message=f"Collection '{collection_name}' deleted successfully",
            remaining_collections=remaining
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Query endpoints
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Query the RAG system."""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        # Determine collections to use
        if request.collections:
            collections_to_use = request.collections
        else:
            collections_to_use = retriever_builder.list_collections()

        if not collections_to_use:
            raise HTTPException(status_code=400, detail="No collections available to query")

        logger.info(f"API Query: {request.question[:50]}... (collections: {collections_to_use})")

        # Build retriever
        retriever = retriever_builder.build_retriever(
            collections_to_index={},
            selected_existing=collections_to_use
        )

        # Run RAG pipeline
        result = workflow.full_pipeline(
            question=request.question,
            retriever=retriever
        )

        return QueryResponse(
            answer=result["draft_answer"],
            verification=result["verification_report"],
            collections_used=collections_to_use,
            chunks_retrieved=5  # Aproximado (mejora futura)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Health status endpoint
@app.get("/health/chroma", response_model=HealthStatus)
async def chroma_health() -> HealthStatus:
    """Check ChromaDB health."""
    try:
        health = retriever_builder.get_health_status()
        return HealthStatus(**health)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Info endpoint
@app.get("/info")
async def app_info() -> Dict:
    """Get application information."""
    return {
        "name": "RAG-AgentAI",
        "version": "1.0.0",
        "description": "Local RAG system with Ollama + ChromaDB",
        "endpoints": {
            "health": "GET /health",
            "collections": {
                "list": "GET /collections",
                "get": "GET /collections/{collection_name}",
                "delete": "DELETE /collections/{collection_name}"
            },
            "query": "POST /query",
            "chroma_health": "GET /health/chroma",
            "info": "GET /info",
            "docs": "GET /docs (interactive Swagger UI)"
        },
        "settings": {
            "ollama": settings.OLLAMA_BASE_URL,
            "chroma": f"{settings.CHROMA_HOST}:{settings.CHROMA_PORT}",
            "embedding_model": settings.EMBEDDING_MODEL
        }
    }

if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 80)
    logger.info("RAG-AgentAI REST API")
    logger.info("=" * 80)
    logger.info(f"Starting API server on http://127.0.0.1:8000")
    logger.info(f"Swagger UI: http://127.0.0.1:8000/docs")
    logger.info(f"ReDoc: http://127.0.0.1:8000/redoc")
    logger.info("=" * 80)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
