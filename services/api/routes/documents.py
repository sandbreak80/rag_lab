"""
Document upload and indexing endpoint with agentic chunking
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import asyncio
import os
import logging
import time
import json

from ..config import (
    EMBED_URL,
    VECTOR_DB_URL,
    CHUNKING_MODE,
    CHUNK_TARGET_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    CHUNK_AGENT_MODEL,
    CHUNK_MAX_SECTIONS,
    CHUNK_AGENT_TIMEOUT_MS,
    OLLAMA_URL,
)
from ..pipeline.chunking import make_chunks
from ..otel import span

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/documents", tags=["documents"])

# Service URLs
VECTOR_ADD_URL = VECTOR_DB_URL + "/add"


class IngestResponse(BaseModel):
    """Response from document ingestion"""
    files: int
    chunks_indexed: int
    status: str = "success"


async def _read_file(file: UploadFile) -> str:
    """Read uploaded file content"""
    data = await file.read()
    # TODO: Add proper parser for PDF/DOCX (use pypdf, python-docx, etc.)
    # For now, handle text files and attempt UTF-8 decode
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Failed to decode {file.filename}: {e}")
        return ""


# Removed: Simple chunking replaced by agentic chunking pipeline


@router.post("", response_model=IngestResponse, status_code=201)
async def upload_documents(
    files: list[UploadFile] = File(..., description="One or more files to upload"),
    perms_tag: str = Form("public", description="Permission tag for ACL (public, secret, etc.)"),
    metadata: Optional[str] = Form(None, description="Optional JSON metadata")
):
    """
    Upload and index documents into vector database with multipart/form-data.

    Flow:
    1. Read file content
    2. Chunk text using agentic chunking (800 tokens, 120 overlap)
    3. Generate embeddings
    4. Upsert to vector DB with ACL metadata

    Args:
        files: List of uploaded files (multipart/form-data)
        perms_tag: Permission tag for ACL (default: public)
        metadata: Optional JSON string with additional metadata

    Returns:
        IngestResponse with file count and chunks indexed (201 Created)
    """
    # Parse optional metadata
    extra_meta = {}
    if metadata:
        try:
            extra_meta = json.loads(metadata)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid metadata JSON: {e}")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    total_chunks = 0
    processed_files = 0

    with span("document_upload", attributes={
        "rag.upload.num_files": len(files),
        "rag.upload.chunking_mode": CHUNKING_MODE,
    }) as upload_span:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for f in files:
                try:
                    # 1. Read file
                    text = await _read_file(f)
                    if not text or len(text.strip()) < 50:
                        logger.warning(f"Skipping {f.filename}: empty or too short")
                        continue

                    # 2. Agentic chunking with overlap
                    doc_id = f.filename
                    base_meta = {
                        "document_id": doc_id,
                        "source_uri": f"upload://{f.filename}",
                        "title": f.filename,
                        "file_type": f.content_type or "text/plain",
                        "perms_tag": perms_tag,
                        "acl_allow_groups": perms_tag,  # Use perms_tag for ACL filtering
                        **extra_meta  # Merge in any extra metadata from form
                    }

                    chunk_objects = await make_chunks(
                        doc_id=doc_id,
                        text=text,
                        meta=base_meta,
                        mode=CHUNKING_MODE,
                        target_tokens=CHUNK_TARGET_TOKENS,
                        overlap_tokens=CHUNK_OVERLAP_TOKENS,
                        agent_model=CHUNK_AGENT_MODEL,
                        max_sections=CHUNK_MAX_SECTIONS,
                        timeout_ms=CHUNK_AGENT_TIMEOUT_MS,
                        ollama_url=OLLAMA_URL,
                    )

                    if not chunk_objects:
                        logger.warning(f"Skipping {f.filename}: no chunks generated")
                        continue

                    logger.info(f"Processing {f.filename}: {len(chunk_objects)} chunks")

                    # 3. Embed each chunk
                    embeddings = []
                    chunk_texts = []
                    for chunk in chunk_objects:
                        embed_response = await client.post(
                            EMBED_URL,
                            json={"text": chunk.text}
                        )
                        embed_response.raise_for_status()
                        embedding = embed_response.json()["embedding"]
                        embeddings.append(embedding)
                        chunk_texts.append(chunk.text)

                    # 4. Add to vector DB with full chunk metadata
                    ids = [f"{f.filename}:chunk_{i}" for i in range(len(chunk_objects))]
                    metadatas = [chunk.meta for chunk in chunk_objects]

                    add_response = await client.post(
                        VECTOR_ADD_URL,
                        json={
                            "ids": ids,
                            "documents": chunk_texts,
                            "embeddings": embeddings,
                            "metadatas": metadatas
                        }
                    )
                    add_response.raise_for_status()

                    total_chunks += len(embeddings)
                    processed_files += 1
                    logger.info(f"✅ Indexed {f.filename}: {len(embeddings)} chunks (mode={CHUNKING_MODE})")

                except httpx.HTTPError as e:
                    logger.error(f"HTTP error processing {f.filename}: {e}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Failed to process {f.filename}: {str(e)}"
                    )
                except Exception as e:
                    logger.error(f"Error processing {f.filename}: {e}")
                    # Continue with other files instead of failing entire batch
                    continue

        upload_span.set_attribute("rag.upload.chunks_indexed", total_chunks)
        upload_span.set_attribute("rag.upload.files_processed", processed_files)

    if processed_files == 0:
        raise HTTPException(
            status_code=400,
            detail="No files could be processed"
        )

    return IngestResponse(
        files=processed_files,
        chunks_indexed=total_chunks,
        status="success"
    )


@router.get("")
async def list_documents():
    """
    List all indexed documents.

    TODO: Implement by querying vector DB for unique doc_title metadata
    """
    # Placeholder - would query vector DB for unique documents
    return {
        "documents": [],
        "total": 0,
        "message": "Document listing not yet implemented"
    }
