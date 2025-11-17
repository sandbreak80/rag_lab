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
VECTOR_LIST_URL = VECTOR_DB_URL + "/list"


class IngestResponse(BaseModel):
    """Response from document ingestion"""
    files: int
    chunks_indexed: int
    status: str = "success"


class DocumentListResponse(BaseModel):
    """Response from document list endpoint with pagination"""
    documents: list[str]
    count: int  # Count of items in this page
    total: int  # Total number of documents
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


async def _read_file(file: UploadFile) -> str:
    """Read uploaded file content with proper PDF/DOCX parsing"""
    data = await file.read()
    filename = file.filename or "unknown"
    content_type = file.content_type or ""

    # Handle PDF files - use docling-service for better parsing
    if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        try:
            # Use docling-service for high-quality PDF parsing
            DOCLING_SERVICE_URL = os.getenv("DOCLING_SERVICE_URL", "http://docling-service:8004")

            async with httpx.AsyncClient(timeout=600.0) as client:  # 10 min timeout for large PDFs
                # Send file as multipart/form-data
                files = {"file": (filename, data, "application/pdf")}

                response = await client.post(
                    f"{DOCLING_SERVICE_URL}/parse",
                    files=files,
                    timeout=600.0
                )
                response.raise_for_status()
                result = response.json()

                if result.get("success"):
                    markdown = result.get("markdown", "")
                    metadata = result.get("metadata", {})
                    num_pages = metadata.get("num_pages", 0)
                    parser = metadata.get("parser", "unknown")

                    if markdown and len(markdown.strip()) > 50:
                        logger.info(f"✅ Extracted {len(markdown)} chars from PDF {filename} using {parser} ({num_pages} pages)")
                        return markdown
                    else:
                        logger.warning(f"⚠️  PDF {filename} extracted but text too short or empty")
                        return ""
                else:
                    error = result.get("error", "Unknown error")
                    logger.error(f"Docling service failed for {filename}: {error}")
                    # Fallback to pypdf
                    logger.info(f"Falling back to pypdf for {filename}")
                    return await _read_file_pypdf_fallback(data, filename)

        except httpx.TimeoutException:
            logger.error(f"Docling service timeout for {filename}")
            return await _read_file_pypdf_fallback(data, filename)
        except httpx.HTTPError as e:
            logger.warning(f"Docling service error for {filename}: {e}, falling back to pypdf")
            return await _read_file_pypdf_fallback(data, filename)
        except Exception as e:
            logger.error(f"Failed to parse PDF {filename} with docling: {e}", exc_info=True)
            return await _read_file_pypdf_fallback(data, filename)

    # Handle text files (UTF-8 decode)
    try:
        text = data.decode("utf-8", errors="ignore")
        if text and len(text.strip()) > 50:
            return text
        else:
            logger.warning(f"⚠️  File {filename} decoded but text too short or empty")
            return ""
    except Exception as e:
        logger.warning(f"Failed to decode {filename}: {e}")
        return ""


async def _read_file_pypdf_fallback(data: bytes, filename: str) -> str:
    """Fallback PDF parser using pypdf"""
    try:
        from pypdf import PdfReader
        import io
        pdf_reader = PdfReader(io.BytesIO(data))
        text_parts = []
        for page in pdf_reader.pages:
            try:
                text_parts.append(page.extract_text())
            except Exception as e:
                logger.warning(f"Failed to extract text from page in {filename}: {e}")
                continue
        text = "\n\n".join(text_parts)
        if text and len(text.strip()) > 50:
            logger.info(f"✅ Extracted {len(text)} chars from PDF {filename} using pypdf fallback ({len(pdf_reader.pages)} pages)")
            return text
        else:
            logger.warning(f"⚠️  PDF {filename} extracted but text too short or empty")
            return ""
    except ImportError:
        logger.error("pypdf not installed! Install with: pip install pypdf")
        return ""
    except Exception as e:
        logger.error(f"Failed to parse PDF {filename} with pypdf: {e}", exc_info=True)
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


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20
):
    """
    List documents in the vector database with pagination.

    Query Parameters:
        page: Page number (1-indexed, default: 1)
        page_size: Number of documents per page (default: 20, max: 100)

    Returns:
        DocumentListResponse with paginated list of document IDs and pagination metadata
    """
    try:
        # Validate pagination params
        page = max(1, page)
        page_size = max(1, min(100, page_size))  # Clamp between 1 and 100

        async with httpx.AsyncClient(timeout=30.0) as client:  # Increased timeout for large datasets
            # Query vector DB for paginated list of unique document IDs
            response = await client.get(
                VECTOR_LIST_URL,
                params={"page": page, "page_size": page_size}
            )
            response.raise_for_status()
            data = response.json()

            # Extract paginated results
            documents = data.get("documents", [])
            total = data.get("total", len(documents))
            total_pages = data.get("total_pages", 1)

            return DocumentListResponse(
                documents=documents,
                count=len(documents),
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        # Return empty list on error rather than failing
        return DocumentListResponse(
            documents=[],
            count=0,
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0
        )
