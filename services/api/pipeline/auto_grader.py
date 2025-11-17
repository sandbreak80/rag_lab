"""
Enhanced Auto-Grader for A/B Testing
Uses LLM-as-judge to evaluate RAG responses across multiple dimensions
"""
import logging
import json
import re
import hashlib
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
    model: str = "llama3.2:3b"
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

        # Use normal temperature for consistent grading
        import random
        grading_temperature = 0.3  # Normal temperature for consistent evaluation
        random_seed = random.randint(1000, 9999)

        logger.info(f"Calling LLM for auto-grading with model={model}, temperature={grading_temperature}, seed={random_seed}")
        logger.info(f"Response A length: {len(response_a)}, Response B length: {len(response_b)}")
        logger.info(f"Response A preview: {response_a[:100]}...")
        logger.info(f"Response B preview: {response_b[:100]}...")

        llm_response = await llm.generate(
            messages=messages,
            model=model,
            temperature=grading_temperature,  # 0.3 for consistent evaluation
            max_tokens=2000,  # Increased from 1500 for more detailed evaluation
            use_mock=False  # Use real LLM for grading
        )

        logger.info(f"LLM response received: {len(llm_response.text)} chars")
        logger.info(f"LLM response preview: {llm_response.text[:200]}...")
        logger.info(f"LLM response FULL: {llm_response.text}")  # Log FULL response for debugging

        # Store raw LLM response for debugging/transparency
        raw_llm_output = llm_response.text

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

    return f"""You are an expert RAG evaluator. Compare two responses to the same query.
{error_warning}

EVALUATION ID: {unique_id} (This is a unique identifier for this evaluation - evaluate each response independently)
TIMESTAMP: {timestamp} (Evaluate each response independently - do not use cached scores)

QUERY: "{prompt}"

RESPONSE A (Length: {len(response_a)} chars):
{response_a[:10000]}  # First 10,000 chars (full response may be longer)
Sources: {sources_a_summary}

RESPONSE B (Length: {len(response_b)} chars):
{response_b[:10000]}  # First 10,000 chars (full response may be longer)
Sources: {sources_b_summary}

NOTE: Response lengths may differ significantly. Evaluate the FULL content provided, not just length.

Evaluate each response on these dimensions (0.0-1.0 scale):
1. answer_quality: Completeness, accuracy, clarity, structure
2. relevance: How well it addresses the query
3. faithfulness: Grounded in sources, proper citations, no hallucinations
4. completeness: All aspects of query covered
5. conciseness: Appropriate length, no redundancy
6. source_quality: Relevance and diversity of sources

CRITICAL: You must ACTUALLY EVALUATE the responses above. Do NOT copy example values.
Analyze the actual content, quality, and characteristics of Response A and Response B.
Assign scores based on YOUR evaluation, not on any template or example.

Return ONLY valid JSON in this exact format (replace the placeholder values with YOUR actual evaluation):
{{
  "response_a": {{
    "answer_quality": <YOUR_SCORE_0.0_to_1.0>,
    "relevance": <YOUR_SCORE_0.0_to_1.0>,
    "faithfulness": <YOUR_SCORE_0.0_to_1.0>,
    "completeness": <YOUR_SCORE_0.0_to_1.0>,
    "conciseness": <YOUR_SCORE_0.0_to_1.0>,
    "source_quality": <YOUR_SCORE_0.0_to_1.0>,
    "overall_score": <CALCULATED_WEIGHTED_AVERAGE>,
    "strengths": ["<specific strength 1>", "<specific strength 2>"],
    "weaknesses": ["<specific weakness 1>", "<specific weakness 2>"]
  }},
  "response_b": {{
    "answer_quality": <YOUR_SCORE_0.0_to_1.0>,
    "relevance": <YOUR_SCORE_0.0_to_1.0>,
    "faithfulness": <YOUR_SCORE_0.0_to_1.0>,
    "completeness": <YOUR_SCORE_0.0_to_1.0>,
    "conciseness": <YOUR_SCORE_0.0_to_1.0>,
    "source_quality": <YOUR_SCORE_0.0_to_1.0>,
    "overall_score": <CALCULATED_WEIGHTED_AVERAGE>,
    "strengths": ["<specific strength 1>", "<specific strength 2>"],
    "weaknesses": ["<specific weakness 1>", "<specific weakness 2>"]
  }},
  "winner": "<A or B or tie>",
  "explanation": "<YOUR detailed explanation of why one response is better, or why they tie>"
}}

IMPORTANT:
- Replace ALL <YOUR_SCORE_0.0_to_1.0> placeholders with actual numeric scores from YOUR evaluation
- Replace ALL <specific strength/weakness> placeholders with actual observations from the responses
- Replace <CALCULATED_WEIGHTED_AVERAGE> with the calculated weighted average
- Replace <A or B or tie> with the actual winner
- Replace <YOUR detailed explanation> with your actual reasoning

Return ONLY the JSON with real values, no other text."""


def parse_grading_result(response_text: str) -> dict[str, Any]:
    """Parse JSON from LLM response"""
    try:
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
        else:
            result = json.loads(response_text)

        # Validate structure
        if "response_a" not in result or "response_b" not in result:
            raise ValueError("Missing response_a or response_b in result")

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

    except Exception as e:
        logger.error(f"Failed to parse grading result: {e}")
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

