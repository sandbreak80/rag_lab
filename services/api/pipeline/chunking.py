"""
Agentic chunking pipeline with LLM-driven boundary detection and overlap
"""
from __future__ import annotations
import time
import math
import re
import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import httpx

from .tokenizer import count_tokens
from ..metrics import (
    CHUNKING_DOCS_TOTAL,
    CHUNKING_CHUNKS_TOTAL,
    CHUNKING_TOKENS_TOTAL,
    CHUNKING_AGENT_CALLS_TOTAL,
    CHUNKING_DURATION_SECONDS,
    CHUNK_SIZE_TOKENS
)
from ..otel import span

logger = logging.getLogger(__name__)

# Default regex for detecting section boundaries (headings, lists, etc.)
DEFAULT_BOUNDARY_REGEX = r"(?m)^(#{1,6}\s+.+|[A-Z].{3,}\n[-=]{3,}|^\d+[\.)]\s+.+$)"


@dataclass
class Chunk:
    """A single chunk with text and metadata"""
    text: str
    meta: Dict[str, Any]


async def _ollama_sections(
    text: str,
    model: str,
    timeout_ms: int,
    ollama_url: str = "http://ollama:11434"
) -> List[Dict[str, Any]]:
    """
    Ask Ollama LLM to propose semantic section boundaries.

    Returns list of {"start": int, "end": int, "title": str, "confidence": float}
    in character offsets.

    Args:
        text: Document text
        model: Ollama model name
        timeout_ms: Timeout in milliseconds
        ollama_url: Ollama API URL

    Returns:
        List of section boundaries
    """
    # Truncate very long texts for the agent
    text_for_agent = text[:120000]

    prompt = (
        "You are a document segmenter. Given TEXT, propose semantic sections.\n"
        "Return JSON array of objects with keys: start_char, end_char, title, confidence (0-1).\n"
        "Rules:\n"
        "- Prefer headings, topic shifts, tables, lists\n"
        "- Keep sections ~400-600 tokens if possible\n"
        "- Boundaries must be non-overlapping and cover text end-to-end\n"
        "- Return ONLY the JSON array, no other text\n\n"
        f"TEXT:\n{text_for_agent}\n\n"
        "JSON:"
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for consistent boundaries
            "num_predict": 2000  # Enough for boundary JSON
        }
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_ms/1000) as client:
            r = await client.post(f"{ollama_url}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()

        # Extract JSON from response
        response_text = data.get("response", "[]")

        # Try to find JSON array in response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            body = json.loads(json_match.group(0))
        else:
            body = json.loads(response_text)

    except Exception as e:
        logger.warning(f"Ollama sections failed: {e}")
        return []

    # Parse and validate sections
    sections = []
    for s in body:
        try:
            start = int(s.get("start_char", 0))
            end = int(s.get("end_char", 0))
            if 0 <= start < end <= len(text):
                sections.append({
                    "start": start,
                    "end": end,
                    "title": str(s.get("title", ""))[:200],
                    "confidence": float(s.get("confidence", 0.5))
                })
        except (ValueError, TypeError) as e:
            logger.debug(f"Skipping invalid section: {e}")
            continue

    return sections


def _regex_sections(text: str) -> List[Dict[str, Any]]:
    """
    Fallback: detect sections using regex for headings/lists.

    Args:
        text: Document text

    Returns:
        List of section boundaries
    """
    spans = []
    for m in re.finditer(DEFAULT_BOUNDARY_REGEX, text):
        spans.append(m.start())

    if not spans or spans[0] != 0:
        spans = [0] + spans

    spans = sorted(set(spans))

    sections = []
    for i, st in enumerate(spans):
        en = spans[i+1] if i+1 < len(spans) else len(text)
        sections.append({
            "start": st,
            "end": en,
            "title": "",
            "confidence": 0.35
        })

    return sections


def _window_with_overlap(
    text: str,
    target_tokens: int,
    overlap_tokens: int
) -> List[Dict[str, int]]:
    """
    Fixed-size windows with overlap as final fallback.

    Args:
        text: Document text
        target_tokens: Target chunk size in tokens
        overlap_tokens: Overlap between chunks in tokens

    Returns:
        List of window boundaries
    """
    toks = count_tokens(text)

    if toks <= target_tokens:
        return [{"start": 0, "end": len(text)}]

    # Calculate number of windows needed
    stride = target_tokens - overlap_tokens
    n = math.ceil((toks - overlap_tokens) / stride)

    windows = []
    for i in range(n):
        # Approximate character positions from token positions
        start_frac = max(0, (i * stride) / toks)
        end_frac = min(1, (i * stride + target_tokens) / toks)

        st = int(start_frac * len(text))
        en = int(end_frac * len(text))

        # Ensure we don't create empty windows
        if en > st:
            windows.append({"start": st, "end": en})

    return windows


async def make_chunks(
    *,
    doc_id: str,
    text: str,
    meta: Dict[str, Any],
    mode: str,
    target_tokens: int,
    overlap_tokens: int,
    agent_model: str,
    max_sections: int,
    timeout_ms: int,
    ollama_url: str = "http://ollama:11434"
) -> List[Chunk]:
    """
    Agentic chunking with overlap; falls back to regex then fixed windows.
    Emits Prometheus metrics + OTel spans.

    Args:
        doc_id: Document identifier
        text: Document text
        meta: Base metadata dict
        mode: "agentic" or "fixed"
        target_tokens: Target chunk size
        overlap_tokens: Overlap between chunks
        agent_model: Ollama model for boundary detection
        max_sections: Maximum sections to process
        timeout_ms: Timeout for agent calls
        ollama_url: Ollama API URL

    Returns:
        List of Chunk objects with text and metadata
    """
    t0 = time.perf_counter()
    CHUNKING_DOCS_TOTAL.labels(mode=mode).inc()

    with span("chunking", attributes={
        "rag.chunking.mode": mode,
        "rag.chunking.target_tokens": target_tokens,
        "rag.chunking.overlap_tokens": overlap_tokens,
        "rag.chunking.agent_model": agent_model,
        "rag.chunking.doc_id": doc_id,
    }) as root_span:

        sections = []

        # Strategy 1: Agentic (LLM-driven boundaries)
        if mode == "agentic":
            with span("chunking.agent_propose"):
                try:
                    sections = await _ollama_sections(
                        text, agent_model, timeout_ms, ollama_url
                    )
                    if sections:
                        CHUNKING_AGENT_CALLS_TOTAL.labels(
                            model=agent_model, status="success"
                        ).inc()
                        logger.info(f"Agentic chunking found {len(sections)} sections")
                    else:
                        CHUNKING_AGENT_CALLS_TOTAL.labels(
                            model=agent_model, status="empty"
                        ).inc()
                except Exception as e:
                    CHUNKING_AGENT_CALLS_TOTAL.labels(
                        model=agent_model, status="error"
                    ).inc()
                    root_span.set_attribute("rag.chunking.agent_error", str(e)[:200])
                    logger.warning(f"Agentic chunking failed: {e}")

        # Strategy 2: Regex-based (headings/lists)
        if not sections:
            with span("chunking.regex_headings"):
                sections = _regex_sections(text)
                logger.info(f"Regex chunking found {len(sections)} sections")

        # Strategy 3: Fixed windows (last resort)
        if not sections:
            with span("chunking.fixed_windows"):
                windows = _window_with_overlap(text, target_tokens, overlap_tokens)
                sections = [
                    {
                        "start": w["start"],
                        "end": w["end"],
                        "title": "",
                        "confidence": 0.2
                    }
                    for w in windows
                ]
                logger.info(f"Fixed chunking created {len(sections)} windows")

        # Create chunks from sections
        chunks: List[Chunk] = []
        total_tokens = 0

        for i, s in enumerate(sections[:max_sections]):
            st, en = s["start"], s["end"]
            chunk_text = text[st:en]

            # Skip empty chunks
            if not chunk_text.strip():
                continue

            tok = count_tokens(chunk_text)
            total_tokens += tok
            CHUNK_SIZE_TOKENS.observe(tok)

            # Build chunk metadata (ChromaDB only supports primitive types)
            meta_ext = {
                **meta,
                "chunking_mode": mode,
                "chunk_index": i,
                "chunk_total_est": min(len(sections), max_sections),
                "overlap_tokens": overlap_tokens,
                "target_tokens": target_tokens,
                "agent_model": agent_model if mode == "agentic" else "",
                "boundary_title": s.get("title", ""),
                "boundary_confidence": float(s.get("confidence", 0.0)),
                "char_start": st,
                "char_end": en,
                "token_count": tok,
            }

            chunks.append(Chunk(chunk_text, meta_ext))

        # Record metrics
        CHUNKING_CHUNKS_TOTAL.labels(mode=mode).inc(len(chunks))
        CHUNKING_TOKENS_TOTAL.labels(mode=mode).inc(total_tokens)

        duration = time.perf_counter() - t0
        CHUNKING_DURATION_SECONDS.labels(mode=mode).observe(duration)

        # Add span attributes
        root_span.set_attribute("rag.chunking.num_chunks", len(chunks))
        root_span.set_attribute("rag.chunking.total_tokens", total_tokens)
        root_span.set_attribute("rag.chunking.duration_ms", int(duration * 1000))

        logger.info(
            f"Chunking complete: {len(chunks)} chunks, "
            f"{total_tokens} tokens, {duration:.2f}s"
        )

        return chunks

