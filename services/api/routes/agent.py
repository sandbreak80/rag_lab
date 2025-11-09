"""Research agent endpoints (stubs)"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class AgentRequest(BaseModel):
    query: str
    max_depth: int = 3

@router.post("/v1/agent/start")
async def start_agent(request: AgentRequest):
    """
    Start a research agent session.
    
    Returns 501 until agent service is fully wired.
    """
    raise HTTPException(
        status_code=501, 
        detail={
            "error": "agent_disabled",
            "message": "Research agent service not yet implemented",
            "feature": "coming_soon"
        }
    )

@router.get("/v1/agent/{session_id}")
async def get_agent_status(session_id: str):
    """Get agent session status (stub)"""
    raise HTTPException(status_code=501, detail="agent_disabled")

@router.delete("/v1/agent/{session_id}")
async def cancel_agent(session_id: str):
    """Cancel agent session (stub)"""
    raise HTTPException(status_code=501, detail="agent_disabled")
