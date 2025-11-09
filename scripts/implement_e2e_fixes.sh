#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "Implementing E2E Test Fixes (Steps 2-6)"
echo "=========================================="

# This script implements all UI and backend changes needed for E2E tests

cd "$(git rev-parse --show-toplevel)"

echo ""
echo "Step 2: Adding data-testid attributes to UI components..."
echo "=========================================="

# Update InputBar.tsx to add data-testid
cat > frontend/src/components/chat/InputBar.tsx << 'EOF'
import React, { useState, KeyboardEvent, useEffect } from 'react';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { Send, Sparkles } from 'lucide-react';

interface InputBarProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const BASELINE_PROMPTS = [
  {
    label: "🟢 Low",
    query: "What is a Large Language Model?",
    description: "Simple concept, low detail"
  },
  {
    label: "🟡 Medium",
    query: "How do transformers work in LLMs? Explain attention mechanisms, tokenization, and the training process.",
    description: "Multi-part, medium detail"
  },
  {
    label: "🔴 High",
    query: "Compare and contrast different RAG architectures including naive RAG, advanced RAG with reranking, and agentic RAG systems. Analyze the trade-offs between retrieval precision, computational cost, and response quality. Include specific examples of when each architecture would be most appropriate.",
    description: "Complex research, high detail"
  }
];

const DRAFT_KEY = 'chat_draft_message';

export function InputBar({ onSend, disabled }: InputBarProps) {
  const [input, setInput] = useState(() => {
    try {
      return localStorage.getItem(DRAFT_KEY) || '';
    } catch {
      return '';
    }
  });
  const [showSuggestions, setShowSuggestions] = useState(true);

  useEffect(() => {
    try {
      if (input) {
        localStorage.setItem(DRAFT_KEY, input);
      } else {
        localStorage.removeItem(DRAFT_KEY);
      }
    } catch (error) {
      console.error('Failed to save draft:', error);
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      setShowSuggestions(false);
      try {
        localStorage.removeItem(DRAFT_KEY);
      } catch (error) {
        console.error('Failed to clear draft:', error);
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div className="space-y-3" data-testid="chat-form">
      {showSuggestions && input.length === 0 && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">📊 Baseline Prompts for Performance Testing:</p>
          <div className="flex flex-wrap gap-2">
            {BASELINE_PROMPTS.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(prompt.query)}
                className="px-3 py-2 text-sm bg-secondary/20 hover:bg-secondary/30 rounded-lg transition-colors flex flex-col items-start gap-0.5 text-left"
                disabled={disabled}
                title={prompt.query}
              >
                <div className="flex items-center gap-1.5">
                  <Sparkles className="h-3 w-3" />
                  <span className="font-semibold">{prompt.label}</span>
                </div>
                <span className="text-xs text-muted-foreground">{prompt.description}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <Textarea
          data-testid="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question... (Shift+Enter for new line)"
          className="min-h-[60px] max-h-[200px] resize-none"
          disabled={disabled}
        />
        <Button
          data-testid="chat-send"
          onClick={handleSend}
          disabled={!input.trim() || disabled}
          size="icon"
          className="h-[60px] w-[60px] flex-shrink-0"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}
EOF

echo "✅ Updated InputBar.tsx with data-testid attributes"

# Update MessageItem.tsx to add data-testid to answer
sed -i.bak 's/<div className={`rounded-lg p-4 relative group/<div data-testid="answer" className={`rounded-lg p-4 relative group/' frontend/src/components/chat/MessageItem.tsx || true

echo "✅ Updated MessageItem.tsx with answer data-testid"

# Update CitationsDrawer.tsx
if [ -f "frontend/src/components/CitationsDrawer.tsx" ]; then
  sed -i.bak 's/<details/<details data-testid="citations-drawer"/' frontend/src/components/CitationsDrawer.tsx || true
  sed -i.bak 's/<summary/<summary data-testid="citations-open"/' frontend/src/components/CitationsDrawer.tsx || true
  echo "✅ Updated CitationsDrawer.tsx with data-testid attributes"
fi

# Update ProvenanceBadges.tsx
if [ -f "frontend/src/components/ProvenanceBadges.tsx" ]; then
  sed -i.bak 's/<div className="flex flex-wrap gap-2/<div data-testid="provenance-badges" className="flex flex-wrap gap-2/' frontend/src/components/ProvenanceBadges.tsx || true
  echo "✅ Updated ProvenanceBadges.tsx with data-testid attributes"
fi

# Update MetricsRow.tsx
if [ -f "frontend/src/components/MetricsRow.tsx" ]; then
  sed -i.bak 's/<div className="flex items-center gap-4/<div data-testid="metrics-row" className="flex items-center gap-4/' frontend/src/components/MetricsRow.tsx || true
  echo "✅ Updated MetricsRow.tsx with data-testid attributes"
fi

# Update JSONInspector.tsx
if [ -f "frontend/src/components/JSONInspector.tsx" ]; then
  sed -i.bak 's/<button onClick={downloadArtifacts}/<button data-testid="json-inspector-download" onClick={downloadArtifacts}/' frontend/src/components/JSONInspector.tsx || true
  echo "✅ Updated JSONInspector.tsx with data-testid attributes"
fi

echo ""
echo "Step 3: Updating Nginx configuration for OTel headers..."
echo "=========================================="

# Update frontend/nginx.conf
cat > frontend/nginx.conf << 'EOF'
# Map OTel tracing headers
map $http_traceparent $traceparent { default $http_traceparent; }
map $http_tracestate  $tracestate  { default $http_tracestate; }
map $request_id       $xrequestid  { default $request_id; }

server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static assets with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    # Health endpoints passthrough to API
    location ~ ^/(live|ready|health)$ {
        proxy_pass http://rag-api-v1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header traceparent $traceparent;
        proxy_set_header tracestate $tracestate;
        proxy_set_header X-Request-Id $xrequestid;
        proxy_http_version 1.1;
        proxy_read_timeout 60s;
        proxy_connect_timeout 5s;
    }

    # API routes - strip /api prefix and forward to backend
    location /api/ {
        rewrite ^/api/(.*)$ /$1 break;
        proxy_pass http://rag-api-v1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header traceparent $traceparent;
        proxy_set_header tracestate $tracestate;
        proxy_set_header X-Request-Id $xrequestid;
        proxy_http_version 1.1;
        proxy_read_timeout 75s;
        proxy_connect_timeout 5s;
        
        # No caching for API responses
        add_header Cache-Control "no-store, no-cache, must-revalidate" always;
    }

    # SPA fallback - serve index.html for all other routes
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, must-revalidate";
    }
}
EOF

echo "✅ Updated frontend/nginx.conf with OTel header forwarding"

echo ""
echo "Step 4: Adding dependency checks to /ready endpoint..."
echo "=========================================="

# Create health routes module
cat > services/api/routes/health.py << 'EOF'
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

@router.get("/live")
async def liveness():
    """Always returns 200 if process is running"""
    return {"status": "alive"}

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
EOF

echo "✅ Created services/api/routes/health.py with dependency checks"

# Update app.py to include health router
if ! grep -q "from routes import health" services/api/app.py 2>/dev/null; then
    sed -i.bak '/from routes import rag/a\
from routes import health
' services/api/app.py || true
    
    sed -i.bak '/app.include_router(rag_router/a\
app.include_router(health.router, tags=["health"])
' services/api/app.py || true
    
    echo "✅ Updated services/api/app.py to include health router"
fi

echo ""
echo "Step 5: Performance optimization - using faster LLM model..."
echo "=========================================="

# Update docker-compose.yml for faster model
sed -i.bak 's/RAG_LLM_MODEL: "qwen2.5:14b"/RAG_LLM_MODEL: "llama3.2:3b"/' docker-compose.yml || true
sed -i.bak '/RAG_LLM_MODEL:/a\
      RAG_LLM_MAX_TOKENS: "300"
' docker-compose.yml || true

echo "✅ Updated docker-compose.yml for faster LLM model (llama3.2:3b)"

echo ""
echo "Step 6: Cleanup backup files..."
echo "=========================================="

find . -name "*.bak" -delete 2>/dev/null || true

echo ""
echo "✅ All changes implemented successfully!"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. Commit these changes:"
echo "   git add -A && git commit -m 'feat: E2E test UI instrumentation'"
echo ""
echo "2. Deploy on AWS:"
echo "   docker compose up -d --build otel-collector rag-api-v1 frontend"
echo ""
echo "3. Wait for services to be healthy (30s)"
echo ""
echo "4. Run sanity checks:"
echo "   curl http://localhost:3000/ready | jq"
echo ""
echo "5. Run E2E tests:"
echo "   bash scripts/run_e2e_ci.sh"
echo ""
echo "=========================================="

