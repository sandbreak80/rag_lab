"""
Enhanced Auto-Grader for A/B Testing
Uses LLM-as-judge to evaluate RAG responses across multiple dimensions
"""
import logging
import json
import re
import hashlib
import httpx
from typing import Any, Optional
from ..adapters import llm

logger = logging.getLogger(__name__)


async def grade_ab_responses(
    prompt: str,
    response_a: str,
    response_b: str,
    sources_a: list[dict[str, Any]],
    sources_b: list[dict[str, Any]],
    config_a: dict[str, Any],
    config_b: dict[str, Any],
    model: str = "mistral:7b"  # Use larger model for better evaluation quality
) -> dict[str, Any]:
    """
    Grade two responses using LLM-as-judge.

    Returns structured grading results with scores across 6 dimensions:
    1. Answer Quality
    2. Relevance
    3. Faithfulness
    4. Completeness
    5. Conciseness
    6. Source Quality
    """
    try:
        # Log what we're grading for debugging
        logger.info(f"Auto-grading: response_a_len={len(response_a)}, response_b_len={len(response_b)}")
        logger.info(f"Auto-grading: response_a_preview={response_a[:100]}...")
        logger.info(f"Auto-grading: response_b_preview={response_b[:100]}...")

        # Build grading prompt
        grading_prompt = build_grading_prompt(
            prompt, response_a, response_b, sources_a, sources_b
        )

        # Use LLM for grading
        messages = [
            {
                "role": "system",
                "content": "You are an expert RAG evaluator. Evaluate responses objectively and return structured JSON. IMPORTANT: If responses are identical or both are error messages, you must still provide different scores if there are ANY differences (e.g., response length, structure, source count). Do not return identical scores unless the responses are truly identical in every way."
            },
            {
                "role": "user",
                "content": grading_prompt
            }
        ]

        # Add response hashes to detect if responses are actually different
        response_a_hash = hashlib.md5(response_a.encode()).hexdigest()[:8]
        response_b_hash = hashlib.md5(response_b.encode()).hexdigest()[:8]
        logger.info(f"Auto-grading: response_a_hash={response_a_hash}, response_b_hash={response_b_hash}")
        logger.info(f"Auto-grading: responses_identical={response_a == response_b}")

        if response_a == response_b:
            logger.warning("⚠️ Both responses are IDENTICAL - auto-grader will still evaluate but scores may be similar")

        # Use slightly higher temperature to prevent copying, but not too high
        import random
        grading_temperature = 0.5  # Balanced temperature to prevent copying while maintaining consistency
        random_seed = random.randint(1000, 9999)

        logger.info(f"Calling LLM for auto-grading with model={model}, temperature={grading_temperature}, seed={random_seed}")
        logger.info(f"Response A length: {len(response_a)}, Response B length: {len(response_b)}")
        logger.info(f"Response A preview: {response_a[:100]}...")
        logger.info(f"Response B preview: {response_b[:100]}...")

        # Unload large models (like qwen2.5:14b) to free GPU memory for auto-grader
        # This allows us to use mistral:7b for better grading quality
        ollama_url = "http://ollama:11434"
        models_to_unload = ["qwen2.5:14b", "gemma2:9b"]  # Large models that might be loaded
        unloaded_models = []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check which models are currently loaded
                ps_response = await client.get(f"{ollama_url}/api/ps")
                if ps_response.status_code == 200:
                    loaded_models = ps_response.json().get("models", [])
                    loaded_model_names = [m.get("name", "") for m in loaded_models]

                    # Unload large models that might conflict
                    for model_name in models_to_unload:
                        if model_name in loaded_model_names:
                            logger.info(f"Unloading {model_name} to free GPU memory for auto-grader")
                            try:
                                # Ollama doesn't have a direct unload API, but we can trigger it by
                                # making a request that will cause it to unload when memory is needed
                                # Actually, we can use the /api/generate endpoint with keep_alive=0 to unload
                                unload_response = await client.post(
                                    f"{ollama_url}/api/generate",
                                    json={"model": model_name, "prompt": "", "keep_alive": "0"},
                                    timeout=5.0
                                )
                                if unload_response.status_code in [200, 400]:  # 400 is OK if model not loaded
                                    unloaded_models.append(model_name)
                                    logger.info(f"Successfully unloaded {model_name}")
                            except Exception as e:
                                logger.warning(f"Failed to unload {model_name}: {e}")
        except Exception as e:
            logger.warning(f"Failed to check/unload models: {e}. Continuing with auto-grading...")

        # Auto-grader needs larger context window for long prompts (2 responses + sources)
        # Truncate responses if needed to fit within context window
        max_response_length = 1500  # Truncate each response to ~1500 chars to fit in context
        response_a_truncated = response_a[:max_response_length] + "..." if len(response_a) > max_response_length else response_a
        response_b_truncated = response_b[:max_response_length] + "..." if len(response_b) > max_response_length else response_b

        # Rebuild prompt with truncated responses
        grading_prompt = build_grading_prompt(
            prompt, response_a_truncated, response_b_truncated, sources_a, sources_b
        )
        messages = [
            {
                "role": "system",
                "content": "You are an expert RAG evaluator. Evaluate responses objectively and return structured JSON. IMPORTANT: If responses are identical or both are error messages, you must still provide different scores if there are ANY differences (e.g., response length, structure, source count). Do not return identical scores unless the responses are truly identical in every way."
            },
            {
                "role": "user",
                "content": grading_prompt
            }
        ]

        try:
            llm_response = await llm.generate(
                messages=messages,
                model=model,
                temperature=grading_temperature,  # 0.5 to prevent copying while maintaining consistency
                max_tokens=2000,  # Increased from 1500 for more detailed evaluation
                context_window=8192,  # Larger context window for auto-grader (handles 2 full responses + sources)
                use_mock=False  # Use real LLM for grading
            )
        finally:
            # Note: We don't reload the models automatically - Ollama will handle memory management
            # If needed, the models will be reloaded on next use
            if unloaded_models:
                logger.info(f"Auto-grading complete. Unloaded models: {unloaded_models} (will be reloaded on next use)")

        logger.info(f"LLM response received: {len(llm_response.text)} chars")
        logger.info(f"LLM response preview: {llm_response.text[:200]}...")
        logger.info(f"LLM response FULL: {llm_response.text}")  # Log FULL response for debugging

        # Store raw LLM response for debugging/transparency
        raw_llm_output = llm_response.text

        # Check if response is empty or error message
        if not raw_llm_output or len(raw_llm_output.strip()) == 0:
            raise ValueError(f"LLM returned empty response for auto-grading. Model: {model}, Response length: {len(raw_llm_output)}")

        if "unable to generate" in raw_llm_output.lower() or "technical issue" in raw_llm_output.lower():
            raise ValueError(f"LLM returned error response for auto-grading: {raw_llm_output[:200]}")

        # Parse JSON from response
        result = parse_grading_result(raw_llm_output)

        # Add metadata and raw output
        result["model_used"] = model
        result["grading_method"] = "llm-as-judge"
        result["raw_llm_output"] = raw_llm_output  # Include full LLM response

        return result

    except Exception as e:
        logger.error(f"LLM grading failed: {e}", exc_info=True)
        # ALWAYS use LLM grading - do not fall back to heuristics
        # Raise the error so the caller knows LLM grading failed
        raise RuntimeError(
            f"LLM auto-grading failed and cannot proceed without it. "
            f"Error: {str(e)}. "
            f"Please check LLM service availability and try again."
        ) from e


def build_grading_prompt(
    prompt: str,
    response_a: str,
    response_b: str,
    sources_a: list[dict[str, Any]],
    sources_b: list[dict[str, Any]]
) -> str:
    """Build the grading prompt for LLM"""

    sources_a_summary = f"{len(sources_a)} sources" if sources_a else "No sources"
    sources_b_summary = f"{len(sources_b)} sources" if sources_b else "No sources"

    # Check for error responses and add warning
    error_warning = ""
    if is_error_response(response_a):
        error_warning += "\n⚠️ WARNING: Response A appears to be an error message. It should receive very low scores (0.0-0.2).\n"
    if is_error_response(response_b):
        error_warning += "\n⚠️ WARNING: Response B appears to be an error message. It should receive very low scores (0.0-0.2).\n"

    # Add unique identifier and randomness to prevent LLM caching/determinism
    import time
    import hashlib
    import random
    timestamp = time.time()
    random_val = random.random()
    unique_id = hashlib.md5(f"{prompt}{response_a[:50]}{response_b[:50]}{timestamp}{random_val}".encode()).hexdigest()[:8]

    # Completely different prompt structure - no template that can be copied
    return f"""Evaluate two RAG responses. ID: {unique_id} Time: {timestamp}

QUERY: {prompt}

=== RESPONSE A ===
Length: {len(response_a)} characters
Sources: {sources_a_summary}
Content:
{response_a[:10000]}

=== RESPONSE B ===
Length: {len(response_b)} characters
Sources: {sources_b_summary}
Content:
{response_b[:10000]}

{error_warning}

TASK: Rate each response on 6 dimensions (0.0 to 1.0):
1. answer_quality - How complete, accurate, clear, and well-structured is it?
2. relevance - How well does it answer the query?
3. faithfulness - Is it grounded in sources? Any hallucinations?
4. completeness - Does it cover all aspects of the query?
5. conciseness - Is the length appropriate? Any redundancy?
6. source_quality - Are sources relevant and diverse?

Calculate overall_score as weighted average: answer_quality*0.25 + relevance*0.20 + faithfulness*0.25 + completeness*0.15 + conciseness*0.10 + source_quality*0.05

List 2-3 specific strengths and 1-2 specific weaknesses for each response.

Determine which response is better (A, B, or tie) and explain why.

Output JSON only:
{{
  "response_a": {{
    "answer_quality": <number>,
    "relevance": <number>,
    "faithfulness": <number>,
    "completeness": <number>,
    "conciseness": <number>,
    "source_quality": <number>,
    "overall_score": <number>,
    "strengths": [<array of strings>],
    "weaknesses": [<array of strings>]
  }},
  "response_b": {{
    "answer_quality": <number>,
    "relevance": <number>,
    "faithfulness": <number>,
    "completeness": <number>,
    "conciseness": <number>,
    "source_quality": <number>,
    "overall_score": <number>,
    "strengths": [<array of strings>],
    "weaknesses": [<array of strings>]
  }},
  "winner": "<A or B or tie>",
  "explanation": "<string>"
}}"""


def parse_grading_result(response_text: str) -> dict[str, Any]:
    """Parse JSON from LLM response with robust error handling"""
    if not response_text or len(response_text.strip()) == 0:
        raise ValueError("Cannot parse empty response text")

    # Log the raw response for debugging
    logger.debug(f"Parsing grading result. Response length: {len(response_text)}")
    logger.debug(f"Response preview (first 500 chars): {response_text[:500]}")

    try:
        # Strategy 1: Try to find JSON object in response (most common case)
        # Look for opening brace followed by content and closing brace
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            logger.debug(f"Found JSON match: {json_str[:200]}...")
            
            # Try to fix common JSON issues before parsing
            # Replace single quotes with double quotes (but be careful with apostrophes in text)
            # Only replace single quotes that are clearly property names or string delimiters
            json_str_fixed = json_str
            
            # Fix single quotes around property names: 'key': -> "key":
            json_str_fixed = re.sub(r"'(\w+)':", r'"\1":', json_str_fixed)
            # Fix single quotes around string values: 'value' -> "value" (but not in the middle of words)
            json_str_fixed = re.sub(r":\s*'([^']*)'", r': "\1"', json_str_fixed)
            # Fix trailing commas before closing braces/brackets
            json_str_fixed = re.sub(r',(\s*[}\]])', r'\1', json_str_fixed)
            
            try:
                result = json.loads(json_str_fixed)
                logger.debug("Successfully parsed JSON after fixing common issues")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed after fixes. Error: {e}. Trying original...")
                # Try original if fixes didn't work
                result = json.loads(json_str)
        else:
            # Strategy 2: Try parsing the whole response if it starts with {
            if response_text.strip().startswith('{'):
                logger.debug("No JSON match found, trying to parse entire response")
                result = json.loads(response_text.strip())
            else:
                # Strategy 3: Try to find JSON using more aggressive regex
                # Look for content between first { and last }
                first_brace = response_text.find('{')
                last_brace = response_text.rfind('}')
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    json_str = response_text[first_brace:last_brace + 1]
                    logger.debug(f"Extracted JSON using brace positions: {json_str[:200]}...")
                    # Apply same fixes
                    json_str = re.sub(r"'(\w+)':", r'"\1":', json_str)
                    json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
                    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                    result = json.loads(json_str)
                else:
                    raise ValueError(f"No JSON found in response. Response preview: {response_text[:500]}")

        # Validate structure
        if "response_a" not in result or "response_b" not in result:
            raise ValueError(f"Missing response_a or response_b in result. Keys found: {list(result.keys())}")

        # Normalize structure - ensure scores are nested
        for key in ["response_a", "response_b"]:
            if "scores" not in result[key]:
                # If scores are at top level, nest them
                if "answer_quality" in result[key]:
                    scores = {k: v for k, v in result[key].items()
                             if k in ["answer_quality", "relevance", "faithfulness",
                                     "completeness", "conciseness", "source_quality"]}
                    result[key] = {
                        "scores": scores,
                        "overall_score": result[key].get("overall_score", 0),
                        "strengths": result[key].get("strengths", []),
                        "weaknesses": result[key].get("weaknesses", [])
                    }

        # Calculate overall scores if not present
        for key in ["response_a", "response_b"]:
            if "overall_score" not in result[key] or result[key]["overall_score"] == 0:
                scores = result[key].get("scores", {})
                overall = (
                    scores.get("answer_quality", 0) * 0.25 +
                    scores.get("relevance", 0) * 0.20 +
                    scores.get("faithfulness", 0) * 0.25 +
                    scores.get("completeness", 0) * 0.15 +
                    scores.get("conciseness", 0) * 0.10 +
                    scores.get("source_quality", 0) * 0.05
                )
                result[key]["overall_score"] = round(overall, 3)

        # Determine winner if not present
        if "winner" not in result:
            score_a = result["response_a"]["overall_score"]
            score_b = result["response_b"]["overall_score"]
            if abs(score_a - score_b) < 0.05:
                result["winner"] = "tie"
            elif score_a > score_b:
                result["winner"] = "A"
            else:
                result["winner"] = "B"

        return result

    except json.JSONDecodeError as e:
        # Log detailed error information for debugging
        error_msg = str(e)
        error_pos = getattr(e, 'pos', None)
        error_line = getattr(e, 'lineno', None)
        error_col = getattr(e, 'colno', None)
        
        logger.error(f"JSON parsing failed: {error_msg}")
        logger.error(f"Error position: pos={error_pos}, line={error_line}, col={error_col}")
        
        # Log the problematic JSON section
        if error_pos is not None and error_pos < len(response_text):
            start = max(0, error_pos - 100)
            end = min(len(response_text), error_pos + 100)
            logger.error(f"Problematic JSON section (around error): {response_text[start:end]}")
        
        # Log full response for debugging (truncated if too long)
        if len(response_text) < 2000:
            logger.error(f"Full response text: {response_text}")
        else:
            logger.error(f"Full response text (first 1000 chars): {response_text[:1000]}")
            logger.error(f"Full response text (last 1000 chars): {response_text[-1000:]}")
        
        raise ValueError(
            f"Failed to parse JSON from LLM response. "
            f"Error: {error_msg} "
            f"(line {error_line}, column {error_col}). "
            f"Response preview: {response_text[:500]}"
        ) from e
    except Exception as e:
        logger.error(f"Failed to parse grading result: {e}", exc_info=True)
        logger.error(f"Response text (first 500 chars): {response_text[:500]}")
        raise


def is_error_response(response: str) -> bool:
    """Detect if response is an error message"""
    error_indicators = [
        "i apologize",
        "unable to generate",
        "technical issue",
        "error generating",
        "failed to",
        "cannot",
        "unable to",
        "sorry, i",
        "i'm sorry"
    ]
    response_lower = response.lower()
    return any(indicator in response_lower for indicator in error_indicators)


def heuristic_grade_responses(
    prompt: str,
    response_a: str,
    response_b: str,
    sources_a: list[dict[str, Any]],
    sources_b: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Fallback heuristic grading when LLM grading fails.
    Uses simple heuristics to score responses.
    """
    def grade_response(response: str, sources: list, prompt: str) -> dict[str, Any]:
        # Check for error responses first - give them very low scores
        if is_error_response(response):
            return {
                "answer_quality": 0.0,
                "relevance": 0.0,
                "faithfulness": 0.0,
                "completeness": 0.0,
                "conciseness": 0.0,
                "source_quality": 0.0,
                "overall_score": 0.0,
                "strengths": [],
                "weaknesses": ["Error response - failed to generate answer"]
            }

        # Answer Quality: length and structure
        word_count = len(response.split())
        has_structure = any(marker in response.lower() for marker in
                          ['because', 'however', 'therefore', 'first', 'second', 'third'])
        answer_quality = min(1.0, (word_count / 200.0) * 0.5 + (0.5 if has_structure else 0))

        # Relevance: keyword overlap with prompt
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())
        overlap = len(prompt_words & response_words) / len(prompt_words) if prompt_words else 0
        relevance = min(1.0, overlap * 1.5)

        # Faithfulness: citation count
        citations = len(re.findall(r'\[\d+\]', response))
        faithfulness = min(1.0, citations / 5.0)

        # Completeness: length relative to prompt complexity
        prompt_complexity = len(prompt.split()) / 20.0
        completeness = min(1.0, word_count / (prompt_complexity * 100))

        # Conciseness: appropriate length (50-300 words ideal)
        if 50 <= word_count <= 300:
            conciseness = 1.0
        elif word_count < 50:
            conciseness = word_count / 50.0
        else:
            conciseness = max(0.5, 1.0 - (word_count - 300) / 500.0)

        # Source Quality: number and diversity
        source_quality = min(1.0, len(sources) / 10.0)

        overall_score = (
            answer_quality * 0.25 +
            relevance * 0.20 +
            faithfulness * 0.25 +
            completeness * 0.15 +
            conciseness * 0.10 +
            source_quality * 0.05
        )

        return {
            "answer_quality": round(answer_quality, 3),
            "relevance": round(relevance, 3),
            "faithfulness": round(faithfulness, 3),
            "completeness": round(completeness, 3),
            "conciseness": round(conciseness, 3),
            "source_quality": round(source_quality, 3),
            "overall_score": round(overall_score, 3),
            "strengths": [],
            "weaknesses": []
        }

    result_a = grade_response(response_a, sources_a, prompt)
    result_b = grade_response(response_b, sources_b, prompt)

    score_a = result_a["overall_score"]
    score_b = result_b["overall_score"]

    if abs(score_a - score_b) < 0.05:
        winner = "tie"
    elif score_a > score_b:
        winner = "A"
    else:
        winner = "B"

    return {
            "response_a": {
                "scores": result_a,
                "overall_score": result_a["overall_score"],
                "strengths": result_a.get("strengths", []),
                "weaknesses": result_a.get("weaknesses", [])
            },
            "response_b": {
                "scores": result_b,
                "overall_score": result_b["overall_score"],
                "strengths": result_b.get("strengths", []),
                "weaknesses": result_b.get("weaknesses", [])
            },
            "winner": winner,
            "explanation": f"Heuristic grading: Response {winner} scored higher ({score_a:.3f} vs {score_b:.3f})",
            "model_used": "heuristic",
            "grading_method": "heuristic-fallback",
            "raw_llm_output": None  # No LLM output for heuristic fallback
        }

