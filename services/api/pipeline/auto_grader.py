"""
Enhanced Auto-Grader for A/B Testing
Uses LLM-as-judge to evaluate RAG responses across multiple dimensions
"""
import logging
import json
import re
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
        # Build grading prompt
        grading_prompt = build_grading_prompt(
            prompt, response_a, response_b, sources_a, sources_b
        )

        # Use LLM for grading
        messages = [
            {
                "role": "system",
                "content": "You are an expert RAG evaluator. Evaluate responses objectively and return structured JSON."
            },
            {
                "role": "user",
                "content": grading_prompt
            }
        ]

        llm_response = await llm.generate(
            messages=messages,
            model=model,
            temperature=0.1,  # Low temperature for consistency
            max_tokens=1500,  # Enough for detailed evaluation
            use_mock=False  # Use real LLM for grading
        )

        # Parse JSON from response
        result = parse_grading_result(llm_response.text)

        # Add metadata
        result["model_used"] = model
        result["grading_method"] = "llm-as-judge"

        return result

    except Exception as e:
        logger.warning(f"LLM grading failed, falling back to heuristics: {e}", exc_info=True)
        # Fallback to heuristic grading
        return heuristic_grade_responses(
            prompt, response_a, response_b, sources_a, sources_b
        )


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

    return f"""You are an expert RAG evaluator. Compare two responses to the same query.

QUERY: "{prompt}"

RESPONSE A:
{response_a[:2000]}  # Truncate if too long
Sources: {sources_a_summary}

RESPONSE B:
{response_b[:2000]}  # Truncate if too long
Sources: {sources_b_summary}

Evaluate each response on these dimensions (0.0-1.0 scale):
1. answer_quality: Completeness, accuracy, clarity, structure
2. relevance: How well it addresses the query
3. faithfulness: Grounded in sources, proper citations, no hallucinations
4. completeness: All aspects of query covered
5. conciseness: Appropriate length, no redundancy
6. source_quality: Relevance and diversity of sources

Return ONLY valid JSON in this exact format:
{{
  "response_a": {{
    "answer_quality": 0.85,
    "relevance": 0.90,
    "faithfulness": 0.88,
    "completeness": 0.82,
    "conciseness": 0.90,
    "source_quality": 0.85,
    "overall_score": 0.87,
    "strengths": ["Clear structure", "Good citations"],
    "weaknesses": ["Missing some details"]
  }},
  "response_b": {{
    "answer_quality": 0.80,
    "relevance": 0.85,
    "faithfulness": 0.82,
    "completeness": 0.78,
    "conciseness": 0.88,
    "source_quality": 0.80,
    "overall_score": 0.82,
    "strengths": ["Comprehensive", "Well-organized"],
    "weaknesses": ["Some redundancy"]
  }},
  "winner": "A",
  "explanation": "Response A wins because it has better faithfulness and relevance, with clearer citations and more accurate information."
}}

Return ONLY the JSON, no other text."""


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
            "grading_method": "heuristic-fallback"
        }

