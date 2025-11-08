# GQS CSV Schema (Grounded Question Set)

Required header (exact order):
question_id,question_text,difficulty,category,intent,expected_citations,answer_type,answer_spec,perms_tag,notes

- question_id: stable slug (e.g., arch-overview-001)
- question_text: the exact user question
- difficulty: beginner|intermediate|advanced
- category: architecture|ingestion|retrieval|rerank|synthesis|observability|security|governance|devops|infra|data
- intent: navigational|definition|procedural|diagnostic|policy|config|troubleshooting
- expected_citations: semicolon-separated list of source anchors
  Format: path#anchor|line_start-line_end
  Examples:
    docs/ARCHITECTURE.md#retrieval-orchestrator|120-185
    docker-compose.yml#service:api-gateway|N/A
- answer_type: extractive|abstractive|linkcard|mixed
- answer_spec: JSON with constraints (e.g., {"bullets":5,"must_include":["SLO","P95"]})
- perms_tag: label controlling ACL test (e.g., public, eng-only, hr-confidential)
- notes: freeform SME comments

All rows must have ≥1 expected_citations. For navigational questions, prefer linkcard answer_type.

