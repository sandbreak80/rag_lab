"""
LLM adapter for answer generation
"""
from typing import Any
from dataclasses import dataclass
import requests
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM generation response with metadata"""
    text: str
    model: str
    provider: str
    tokens_in: int
    tokens_out: int
    tokens_total: int
    cost_usd: float
    temperature: float
    # Ollama verbose metrics
    total_duration_ns: int | None = None  # Total duration in nanoseconds
    load_duration_ns: int | None = None  # Model load duration in nanoseconds
    prompt_eval_count: int | None = None  # Tokens in prompt
    prompt_eval_duration_ns: int | None = None  # Prompt evaluation duration in nanoseconds
    prompt_eval_rate: float | None = None  # Prompt evaluation rate (tokens/s)
    eval_count: int | None = None  # Tokens generated
    eval_duration_ns: int | None = None  # Generation duration in nanoseconds
    eval_rate: float | None = None  # Generation rate (tokens/s)


async def generate_mock(
    messages: list[dict[str, str]],
    model: str = "mock-llm",
    temperature: float = 0.7,
    max_tokens: int = 512
) -> LLMResponse:
    """
    Mock LLM generation with deterministic output.

    NO PAYLOAD LOGGING - only metadata.
    """
    logger.info(f"Mock LLM: model={model}, temp={temperature}, max_tok={max_tokens}, msg_count={len(messages)}")

    # Extract query from last message
    query = messages[-1].get("content", "query") if messages else "query"

    # Deterministic mock answer with citations
    answer = f"""Based on the provided documents, here is the answer to your query:

{query}

This information comes from multiple sources in our knowledge base [1][2]. The primary documentation [1] states that our system follows best practices for handling such requests. Additionally, supplementary materials [2] provide context and examples.

Please note that policies may vary based on specific circumstances [3]."""

    # Mock token counts (rough estimate)
    prompt_tokens = sum(len(m.get("content", "").split()) for m in messages) * 1.3
    completion_tokens = len(answer.split()) * 1.3

    return LLMResponse(
        text=answer,
        model=model,
        provider="mock",
        tokens_in=int(prompt_tokens),
        tokens_out=int(completion_tokens),
        tokens_total=int(prompt_tokens + completion_tokens),
        cost_usd=0.0001,  # Mock cost
        temperature=temperature
    )


async def generate_real(
    messages: list[dict[str, str]],
    model: str = "llama3.2:3b",
    temperature: float = 0.7,
    max_tokens: int = 300,
    ollama_url: str = "http://ollama:11434"
) -> LLMResponse:
    """
    Real LLM generation via Ollama.

    NO PAYLOAD LOGGING - only metadata.
    """
    import httpx
    import time

    try:
        t0 = time.perf_counter()
        # Format for Ollama chat API
        async with httpx.AsyncClient(timeout=30.0) as cx:
            response = await cx.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.perf_counter() - t0) * 1000

        # Extract tokens from response
        prompt_eval_count = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)

        # Extract Ollama verbose metrics (all durations are in nanoseconds)
        total_duration_ns = data.get("total_duration")
        load_duration_ns = data.get("load_duration")
        prompt_eval_duration_ns = data.get("prompt_eval_duration")
        eval_duration_ns = data.get("eval_duration")

        # Get rates from Ollama, or calculate them if not provided
        prompt_eval_rate = data.get("prompt_eval_rate")  # tokens/s
        if not prompt_eval_rate and prompt_eval_count > 0 and prompt_eval_duration_ns:
            # Calculate: tokens / (duration in seconds)
            prompt_eval_rate = prompt_eval_count / (prompt_eval_duration_ns / 1_000_000_000)

        eval_rate = data.get("eval_rate")  # tokens/s
        if not eval_rate and eval_count > 0 and eval_duration_ns:
            # Calculate: tokens / (duration in seconds)
            eval_rate = eval_count / (eval_duration_ns / 1_000_000_000)

        # Rough cost estimate (local Ollama = $0)
        cost_per_1k = 0.0  # Free for local Ollama
        total_tokens = prompt_eval_count + eval_count
        cost_usd = (total_tokens / 1000) * cost_per_1k

        logger.info(
            f"Real LLM: model={model}, tokens_in={prompt_eval_count}, tokens_out={eval_count}, "
            f"latency={latency_ms:.0f}ms, eval_rate={eval_rate:.1f} tok/s" if eval_rate else f"latency={latency_ms:.0f}ms"
        )

        return LLMResponse(
            text=data["message"]["content"],
            model=model,
            provider="ollama",
            tokens_in=prompt_eval_count,
            tokens_out=eval_count,
            tokens_total=total_tokens,
            cost_usd=round(cost_usd, 6),
            temperature=temperature,
            total_duration_ns=total_duration_ns,
            load_duration_ns=load_duration_ns,
            prompt_eval_count=prompt_eval_count if prompt_eval_count > 0 else None,
            prompt_eval_duration_ns=prompt_eval_duration_ns,
            prompt_eval_rate=prompt_eval_rate,
            eval_count=eval_count if eval_count > 0 else None,
            eval_duration_ns=eval_duration_ns,
            eval_rate=eval_rate
        )

    except Exception as e:
        logger.error(f"LLM generation failed: {e}, falling back to error response")
        # Fallback to error response
        return LLMResponse(
            text="I apologize, but I'm unable to generate a response at this time due to a technical issue.",
            model=model,
            provider="ollama",
            tokens_in=0,
            tokens_out=0,
            tokens_total=0,
            cost_usd=0.0,
            temperature=temperature
        )


async def generate(
    messages: list[dict[str, str]],
    model: str = "llama3.1:8b",
    temperature: float = 0.7,
    max_tokens: int = 512,
    use_mock: bool = True
) -> LLMResponse:
    """Main entry point for LLM generation"""
    if use_mock:
        return await generate_mock(messages, model, temperature, max_tokens)
    else:
        return await generate_real(messages, model, temperature, max_tokens, ollama_url="http://ollama:11434")

