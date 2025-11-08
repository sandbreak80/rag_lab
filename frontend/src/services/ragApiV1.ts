/**
 * RAG API v1 Client - New observability contract
 * Routes through Nginx as same-origin /api (no CORS issues)
 */

const API_BASE = process.env.NEXT_PUBLIC_RAG_API || '/api';

export interface RagRequest {
  query: string;
  user_id: string;
  groups?: string[];
  dept?: string | null;
  top_k?: number;
  ab_bucket?: 'A' | 'B' | null;
}

export interface Citation {
  doc_id: string;
  version: string;
  chunk_id: string;
  char_range: [number, number];
  source_uri: string;
  origin_tool: 'rag' | 'web_search' | 'research_agent';
}

export interface RagResponse {
  answer: string;
  citations: Citation[];
  artifacts: {
    planner?: any;
    retrieval_log?: any;
    evidence_map?: any;
    recency?: any;
    guardrail_report?: any;
    ab_eval?: any;
  };
  metrics: {
    latency_ms: number;
    tokens_in: number;
    tokens_out: number;
    model: string;
    cost_usd: number;
  };
  security_status: 'ok' | 'degraded' | 'blocked';
  request_id: string;
  trace_id: string;
  contract_version: string;
}

export async function askRagV1(req: RagRequest): Promise<RagResponse> {
  const response = await fetch(`${API_BASE}/v1/rag/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...req,
      groups: req.groups || [],
    }),
  });

  if (!response.ok) {
    throw new Error(`RAG API v1 error: ${response.status}`);
  }

  return response.json();
}

// Health checks
export async function checkHealth(): Promise<{ status: string; service: string; version: string }> {
  const response = await fetch(`${API_BASE}/live`);
  return response.json();
}

export async function checkReadiness(): Promise<any> {
  const response = await fetch(`${API_BASE}/ready`);
  return response.json();
}

