#!/usr/bin/env python3
from prometheus_client import Counter, Gauge, start_http_server
import time, json, os, pathlib

PORT = int(os.getenv("GQS_METRICS_PORT","9309"))
start_http_server(PORT)

FRESH_VIOL = Counter("gqs_freshness_violations_total","Questions that required ≥2 sources ≤48h and failed")
PROV_MISSING = Counter("gqs_provenance_missing_total","Responses missing immutable origin_tool or evidence_map")
LAT_P95 = Gauge("gqs_p95_latency_seconds","P95 latency from last run")
CIT_RATE = Gauge("gqs_citation_rate","Proportion of answers with ≥1 citation")

# The harness can write a rolling summary file; this exporter reads it.
SUMMARY = pathlib.Path("evals/.last_summary.json")

def loop():
    while True:
        if SUMMARY.exists():
            j=json.loads(SUMMARY.read_text())
            LAT_P95.set(j.get("p95_latency_s", 0.0))
            CIT_RATE.set(j.get("citation_rate", 0.0))
            FRESH_VIOL.inc(j.get("freshness_violations", 0))
            PROV_MISSING.inc(j.get("provenance_missing", 0))
        time.sleep(10)

if __name__ == "__main__":
    loop()

