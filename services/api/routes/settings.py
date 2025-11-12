"""Settings management endpoints"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/v1/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Current RAG settings"""
    temperature: float
    context_window: int
    top_k: int
    web_search_enabled: bool
    vector_db_enabled: bool
    research_agent_enabled: bool
    prompt_enhancement_enabled: bool


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """
    Get current RAG system settings.

    Returns current configuration values for all toggles and parameters.
    """
    return SettingsResponse(
        temperature=0.7,
        context_window=2048,
        top_k=8,
        web_search_enabled=True,
        vector_db_enabled=True,
        research_agent_enabled=False,
        prompt_enhancement_enabled=False
    )


@router.put("")
async def update_settings(settings: dict[str, Any]):
    """
    Update RAG system settings.

    In a production system, this would persist settings to a database or config file.
    For now, this is a stub that accepts settings but doesn't persist them.

    Returns the updated settings.
    """
    return {
        "status": "success",
        "message": "Settings updated (in-memory only)",
        "settings": settings
    }

