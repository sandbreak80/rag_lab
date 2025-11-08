#!/usr/bin/env bash
set -euo pipefail
export RAG_LAB_ROOT="${RAG_LAB_ROOT:-.}"
python3 evals/gqs_autogen.py
echo "Seed written to evals/gqs_seed.csv"

