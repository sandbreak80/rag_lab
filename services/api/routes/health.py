"""Health check endpoints with dependency validation"""
import time
import socket
from typing import Dict
import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Cache for /ready checks (10 second TTL)
_last_ready_check = {"ts": 0, "ok": False, "detail": {}}

# Service dependencies to check
DEPENDENCIES = [
    ("vector_db", "http://vector-db:8005/health"),
    ("embedding", "http://embedding-service:8006/health"),
    ("ollama", "http://ollama:11434/api/tags"),
    ("searxng", "http://searxng:8080/"),
    ("otel_collector", "http://otel-collector:13133/"),
]

def tcp_probe(host: str, port: int, timeout: float = 1.0) -> bool:
    """Quick TCP connection check"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

async def http_probe(url: str, timeout: float = 2.0) -> int:
    """Quick HTTP GET check, returns status code or 0 on error"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            return r.status_code
    except Exception:
        return 0

# NOTE: /live endpoint is defined in app.py with full details (service, version)
# This avoids duplication and ensures consistent response format

@router.get("/ready")
async def readiness():
    """Returns 200 only when all dependencies are healthy (cached 10s)"""
    now = time.time()
    
    # Return cached result if fresh
    if now - _last_ready_check["ts"] < 10:
        status = "ready" if _last_ready_check["ok"] else "degraded"
        status_code = 200 if _last_ready_check["ok"] else 503
        return JSONResponse(
            {"status": status, "dependencies": _last_ready_check["detail"]},
            status_code=status_code
        )
    
    # Check all dependencies
    all_ok = True
    detail = {}
    
    for name, url in DEPENDENCIES:
        try:
            status_code = await http_probe(url, timeout=2.0)
            detail[name] = status_code
            all_ok = all_ok and (200 <= status_code < 400)
        except Exception as e:
            all_ok = False
            detail[name] = f"ERR:{type(e).__name__}"
    
    # Update cache
    _last_ready_check.update({"ts": now, "ok": all_ok, "detail": detail})
    
    status = "ready" if all_ok else "degraded"
    status_code = 200 if all_ok else 503
    
    return JSONResponse(
        {"status": status, "dependencies": detail},
        status_code=status_code
    )

@router.get("/health")
async def health():
    """Combined health check (always returns 200 but shows status)"""
    deps = {}
    
    for name, url in DEPENDENCIES:
        try:
            status_code = await http_probe(url, timeout=2.0)
            deps[name] = status_code
        except Exception as e:
            deps[name] = f"ERR:{type(e).__name__}"
    
    all_ok = all(isinstance(v, int) and 200 <= v < 400 for v in deps.values())
    
    return {
        "status": "ok" if all_ok else "degraded",
        "dependencies": deps
    }
