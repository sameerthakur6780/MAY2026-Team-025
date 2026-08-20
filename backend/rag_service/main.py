"""FastAPI RAG microservice (Render / HF Spaces friendly)."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from rag.cache.redis_cache import cache_stats
from rag.pipeline.ingest import ingest_pdf_bytes
from rag.pipeline.query import answer_question
from rag.schemas import IngestResult, QueryRequest, QueryResponse
from rag.store.pinecone_store import RagStoreError

app = FastAPI(title="SmartBatch RAG Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "rag"}


@app.get("/cache/stats")
def cache_status():
    return cache_stats()


@app.post("/ingest", response_model=IngestResult)
async def ingest(
    file: UploadFile = File(...),
    subject: str = Form(...),
    grade: int = Form(...),
    title: str = Form("Untitled"),
    resource_id: int | None = Form(None),
    force: bool = Form(False),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")
    try:
        pdf_bytes = await file.read()
        return ingest_pdf_bytes(
            pdf_bytes,
            subject=subject,
            grade=grade,
            title=title,
            resource_id=resource_id,
            force=force,
        )
    except RagStoreError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest):
    try:
        return answer_question(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
