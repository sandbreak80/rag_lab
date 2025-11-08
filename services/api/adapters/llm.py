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
    model: str = "llama3.1:8b",
    temperature: float = 0.7,
    max_tokens: int = 512,
    ollama_url: str = "http://ollama:11434"
) -> LLMResponse:
    """
    Real LLM generation via Ollama.
    
    NO PAYLOAD LOGGING - only metadata.
    """
    try:
        # Format for Ollama chat API
        response = requests.post(
            f"{ollama_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract tokens from response
        prompt_eval_count = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)
        
        # Rough cost estimate (replace with actual pricing)
        cost_per_1k = 0.0002  # $0.20 per 1M tokens
        total_tokens = prompt_eval_count + eval_count
        cost_usd = (total_tokens / 1000) * cost_per_1k
        
        return LLMResponse(
            text=data["message"]["content"],
            model=model,
            provider="ollama",
            tokens_in=prompt_eval_count,
            tokens_out=eval_count,
            tokens_total=total_tokens,
            cost_usd=round(cost_usd, 6),
            temperature=temperature
        )
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
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

