# RAG Lab Evaluation Harness

## Overview

This directory contains the **Golden Question Set (GQS)** infrastructure for RAG Lab, implementing Phase 2: Verification & Hardening.

## Components

### 1. Question Generation (`gqs_autogen.py`)
Auto-generates 200-300 questions from:
- Documentation (markdown files)
- Code comments (TODO/FIXME)
- Docker Compose services
- Function signatures

### 2. Schema Definition (`gqs_schema.md`)
Defines the CSV schema for questions, including:
- Question metadata (ID, text, difficulty, category)
- Expected behavior (citations, answer type)
- Access control (perms_tag)

### 3. Evaluation Harness (`gqs_harness.py`)
Runs questions against the RAG API and validates:
- Citation presence (Schema C - EvidenceMap)
- Freshness compliance (≥2 primary sources ≤48h)
- Security status (Schema F - GuardrailReport)
- A/B dimensions (Schema G - ABEvaluation)

### 4. Metrics Exporter (`gqs_metrics.py`)
Exposes Prometheus metrics on `:9309`:
- `gqs_p95_latency_seconds` - P95 query latency
- `gqs_citation_rate` - Proportion of answers with citations
- `gqs_freshness_violations_total` - Recency gate failures
- `gqs_provenance_missing_total` - Missing origin_tool

### 5. Configuration (`gqs_conf.yaml`)
Defines:
- Freshness requirements (48h, ≥2 primary sources)
- Contract schemas to validate (B, C, F, G)
- A/B evaluation dimensions
- Routing rules by intent

## How to Use

### 1) Auto-generate questions
```bash
make seed
# Outputs: evals/gqs_seed.csv (~200-300 questions)
```

### 2) SME review pass
- Open `evals/gqs_seed.csv`
- Follow `evals/gqs_review_template.md`
- Remove duplicates, fix errors, add edge cases
- Save as `evals/gqs_curated.csv` (optional) or overwrite seed

**Target:** 150-200 curated questions

### 3) Run evaluations against API
```bash
export RAG_API=http://localhost:8080
make eval
# Writes: evals/gqs_report.jsonl
# Prints: Summary with P95 latency and citation rate
```

### 4) Expose metrics for monitoring
```bash
make metrics
# Prometheus endpoint: http://localhost:9309/metrics
```

### 5) Add to Grafana dashboard
Configure Prometheus to scrape `:9309` and create panels for:
- P95 latency trends
- Citation rate over time
- Freshness violation alerts
- Provenance integrity checks

## Phase 2 Exit Criteria

| Requirement                              | Threshold                        | Status |
| ---------------------------------------- | -------------------------------- | ------ |
| Golden Set Coverage                      | ≥ 150 questions                  | ⏳     |
| Hallucination (Severe)                   | < 2%                             | ⏳     |
| P95 Latency (Cold)                       | < 3.5s                           | ⏳     |
| Retrieval Empty Rate                     | < 2% after ACL + recency filters | ⏳     |
| Freshness Gap 90th Percentile            | ≤ 48h                            | ⏳     |
| All artifacts generated in every request | 100%                             | ⏳     |

## File Structure

```
evals/
├── README.md                    # This file
├── gqs_schema.md                # CSV schema definition
├── gqs_review_template.md       # SME review checklist
├── gqs_autogen.py               # Auto-generation script
├── gqs_harness.py               # Evaluation harness
├── gqs_metrics.py               # Prometheus exporter
├── gqs_conf.yaml                # Configuration
├── sample_rubrics.yaml          # Grading rubrics
├── gqs_seed.csv                 # Auto-generated questions (output)
├── gqs_curated.csv              # Human-reviewed questions (optional)
├── gqs_report.jsonl             # Evaluation results (output)
└── .last_summary.json           # Latest metrics summary (output)
```

## Tips

### Question Quality
- Prefer **stable heading anchors** over brittle line ranges
- Add **edge cases** for observability, security, and retrieval
- Tag **10-15 advanced questions** requiring cross-doc synthesis
- Ensure **≥20 navigational questions** for UI validation

### Performance
- Run evaluations in **parallel** with `--workers` flag (future enhancement)
- Use **warm cache** runs to test < 1.8s P95 latency
- Monitor **freshness_hours** parameter impact on pass rate

### Troubleshooting
- If citation rate < 95%, check `evidence_map` field in API response
- If freshness violations spike, investigate ingestion lag
- If provenance missing, verify `origin_tool` immutability in Evidence objects

## Integration with Existing Infrastructure

### Docker Compose
Add GQS metrics exporter to `docker-compose.yml`:
```yaml
gqs-metrics:
  build:
    context: .
    dockerfile: Dockerfile.gqs-metrics
  container_name: rag-gqs-metrics
  networks:
    - rag-network
  ports:
    - "9309:9309"
  volumes:
    - ./evals:/app/evals:ro
  environment:
    - GQS_METRICS_PORT=9309
  restart: unless-stopped
```

### Prometheus
Add scrape config:
```yaml
scrape_configs:
  - job_name: 'gqs-metrics'
    static_configs:
      - targets: ['gqs-metrics:9309']
```

### Grafana
Import dashboard template from `docs/grafana/gqs_dashboard.json` (future)

## Future Enhancements

- [ ] Citation span validator (regex over retrieved chunks)
- [ ] Per-category coverage dashboard (HTML report)
- [ ] Intent router smoke tests (NER-based routing)
- [ ] Parallel evaluation with `--workers` flag
- [ ] A/B comparison report generator
- [ ] Hallucination probe integration
- [ ] Load testing integration (Locust)
- [ ] CI/CD integration (GitHub Actions)

## Related Documentation

- `otel/span_semantics.md` - OTel span attributes
- `docs/WIRE_UP_DESIGN.md` - Full observability contract
- `docs/WIRE_UP_COMPLETE.md` - Implementation status
- `services/common/evidence.py` - Provenance tracking
- `services/common/recency_gate.py` - Freshness evaluation
- `services/api/app.py` - API contract implementation

