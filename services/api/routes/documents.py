"""Document upload and management endpoints"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/v1/documents")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document for ingestion into the RAG system.
    
    Currently returns a stub response. Wire to ingestion queue when ready.
    """
    try:
        # Validate file type
        allowed_types = ['text/plain', 'text/markdown', 'application/pdf', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        # Validate file size (50MB max)
        contents = await file.read()
        if len(contents) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        
        # TODO: Wire to ingestion service/queue
        logger.info(f"Document upload: {file.filename} ({len(contents)} bytes)")
        
        return JSONResponse({
            "status": "queued",
            "filename": file.filename,
            "size_bytes": len(contents),
            "message": "Document queued for ingestion (stub - not yet processing)"
        }, status_code=202)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/v1/documents")
async def list_documents():
    """List uploaded documents (stub)"""
    return {
        "documents": [],
        "message": "Document listing not yet implemented"
    }

@router.delete("/v1/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document (stub)"""
    raise HTTPException(status_code=501, detail="Document deletion not yet implemented")
