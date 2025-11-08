.PHONY: gqs seed eval metrics help

help:
	@echo "RAG Lab Development Commands:"
	@echo ""
	@echo "  make seed        Generate GQS seed from repo docs"
	@echo "  make eval        Run evaluation harness against API"
	@echo "  make metrics     Start Prometheus metrics exporter"
	@echo "  make help        Show this help message"

seed gqs:
	@bash scripts/make_gqs.sh

eval:
	@bash scripts/run_evals.sh

metrics:
	@python3 evals/gqs_metrics.py
