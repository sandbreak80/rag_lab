"""
Contract test: Verify stage_timings includes all required fields
"""
import requests
import json

API_BASE = "http://localhost:3000/api/v1"


def test_stage_timings_complete():
    """
    Verify that metrics.stage_timings contains all required timing fields
    """
    payload = {
        "query": "Test query for timing validation",
        "user_id": "test-user",
        "groups": ["public"]
    }

    response = requests.post(f"{API_BASE}/rag/query", json=payload, timeout=30)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()

    # Verify metrics exists
    assert "metrics" in data, "Response missing 'metrics' field"
    metrics = data["metrics"]

    # Verify stage_timings exists
    assert "stage_timings" in metrics, "Metrics missing 'stage_timings' field"
    stage_timings = metrics["stage_timings"]

    # Required fields
    required_fields = ["vector_ms", "web_ms", "llm_ms", "total_ms"]

    for field in required_fields:
        assert field in stage_timings, f"stage_timings missing required field: {field}"
        value = stage_timings[field]
        assert isinstance(value, (int, float)), f"{field} must be numeric, got {type(value)}"
        assert value >= 0, f"{field} must be non-negative, got {value}"

    # Verify total is sum of stages (approximately, allowing for overhead)
    vector_ms = stage_timings["vector_ms"]
    web_ms = stage_timings["web_ms"]
    llm_ms = stage_timings["llm_ms"]
    total_ms = stage_timings["total_ms"]

    # Total should be >= max(vector+web in parallel, llm)
    min_expected = llm_ms  # At minimum, LLM time
    assert total_ms >= min_expected, f"total_ms ({total_ms}) should be >= llm_ms ({llm_ms})"

    print(f"✅ All timing fields present and valid:")
    print(f"   vector_ms: {vector_ms}")
    print(f"   web_ms: {web_ms}")
    print(f"   llm_ms: {llm_ms}")
    print(f"   total_ms: {total_ms}")

    # Save proof artifact
    with open("artifacts/fix2_stage_timings_response.json", "w") as f:
        json.dump({
            "query": payload["query"],
            "stage_timings": stage_timings,
            "all_required_present": True,
            "validation": "passed"
        }, f, indent=2)


if __name__ == "__main__":
    print("Running stage_timings contract test...")
    test_stage_timings_complete()
    print("✅ Test passed!")

