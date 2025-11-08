#!/usr/bin/env python3
import os, csv, json, time, requests, statistics
from pathlib import Path

API_GATEWAY = os.getenv("RAG_API", "http://localhost:8080")
CSV_IN = Path("evals/gqs_seed.csv")
REPORT_OUT = Path("evals/gqs_report.jsonl")

# Contracts in your system:
# - RetrievalLog (B)
# - EvidenceMap (C)
# - ABEvaluation (G)

def post_json(url, payload, timeout=60):
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

def run_query(row):
    q = row["question_text"]
    perms = row.get("perms_tag","public")
    payload = {
        "query": q,
        "perms_tag": perms,
        "contract_version": "v1",
        "request_id": f"gqs-{row['question_id']}",
        "eval_mode": True,  # ask API to include Schemas B/C/G in response
        "freshness_hours": 48,  # Hybrid recency gate as per your spec
    }
    t0=time.time()
    resp = post_json(f"{API_GATEWAY}/v1/rag/query", payload)
    wall=time.time()-t0
    return resp, wall

def score_record(resp, row):
    # Expect EvidenceMap (C) with claim→citation bindings
    # Expect ABEvaluation (G) with dimensions already computed by your system
    ev = resp.get("evidence_map", {})
    ab = resp.get("ab_evaluation", {})
    guard = resp.get("guardrail_report", {})
    # Minimal independent checks:
    cit_ok = any(ev.get("citations", []))
    degraded = guard.get("security_status") == "degraded"
    dims = ab.get("dimensions", {})
    return {
        "question_id": row["question_id"],
        "citations_present": bool(cit_ok),
        "degraded": degraded,
        "dims": dims
    }

def main():
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with open(CSV_IN, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                resp, wall = run_query(row)
                rec = score_record(resp, row)
                rec["latency_s"]=wall
                rec["request_id"]=resp.get("request_id")
                rec["trace_id"]=resp.get("trace_id")
                results.append(rec)
                with open(REPORT_OUT, "a", encoding="utf-8") as out:
                    out.write(json.dumps(rec)+"\n")
                print(f"{row['question_id']}  {wall:.2f}s  cites={rec['citations_present']}")
            except Exception as e:
                print(f"ERR {row['question_id']}: {e}")

    # quick summary
    lat = [x["latency_s"] for x in results]
    cite_rate = sum(1 for x in results if x["citations_present"]) / max(1,len(results))
    print(f"\nSUMMARY: n={len(results)}  P95={statistics.quantiles(lat, n=20)[-1]:.2f}s  cite_rate={cite_rate:.2%}")

if __name__ == "__main__":
    main()

