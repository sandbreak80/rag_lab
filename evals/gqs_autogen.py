#!/usr/bin/env python3
import re, os, csv, json, hashlib
from pathlib import Path

ROOT = Path(os.getenv("RAG_LAB_ROOT", ".")).resolve()
DOC_HINTS = [
    ("README.md", "architecture"),
    ("docs", "architecture"),
    ("docs/CURRENT_STATUS.md", "observability"),
    ("docs", "ingestion"),
    ("docker-compose.yml", "devops"),
    ("services", "retrieval"),
    ("infra", "infra"),
    ("src", "retrieval"),
]
CODE_EXT = {".py",".ts",".tsx",".go",".rs",".java",".md",".yml",".yaml",".json",".sh",".bash",".txt"}

CSV_OUT = ROOT / "evals" / "gqs_seed.csv"

def slug(s, n=60):
    s = re.sub(r"[^a-z0-9\-]+", "-", s.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:n]

def hash_id(text):
    return hashlib.sha1(text.encode()).hexdigest()[:8]

def extract_md_questions(path: Path, category: str):
    txt = path.read_text(errors="ignore")
    q = []
    # Headings → definition/navigation prompts
    for m in re.finditer(r"^(#{1,4})\s+(.+)$", txt, flags=re.M):
        level = len(m.group(1)); head = m.group(2).strip()
        base = f"What is {head}?"
        q.append((base, "definition", f"{path.relative_to(ROOT)}#{slug(head)}|N/A", category))
        if any(k in head.lower() for k in ["architecture","orchestrator","index","retrieval","pipeline"]):
            q.append((f"Where is {head} defined and how does it interact with adjacent services?",
                      "navigational", f"{path.relative_to(ROOT)}#{slug(head)}|N/A", category))
    # Tables/lists → procedural prompts
    for m in re.finditer(r"^- .{10,}$", txt, flags=re.M):
        item = m.group(0)[2:].strip()
        q.append((f"How do I perform: {item}?", "procedural", f"{path.relative_to(ROOT)}|N/A", category))
    return q

def extract_compose_questions(path: Path):
    txt = path.read_text(errors="ignore")
    q = []
    for m in re.finditer(r"^\s{0,4}([A-Za-z0-9\-_]+):\s*$", txt, flags=re.M):
        svc = m.group(1)
        q.append((f"Which dependencies and env vars does {svc} require?", "diagnostic",
                  f"{path.relative_to(ROOT)}#service:{svc}|N/A", "devops"))
        q.append((f"What are the startup order and health checks for {svc}?",
                  "procedural", f"{path.relative_to(ROOT)}#service:{svc}|N/A", "devops"))
    return q

def extract_code_questions(path: Path, category: str):
    txt = path.read_text(errors="ignore")
    q = []
    # Comments with TODO/FIXME
    for m in re.finditer(r"(TODO|FIXME)\s*:\s*(.+)", txt):
        item = m.group(2).strip()
        q.append((f"How should we address: {item}?", "diagnostic", f"{path.relative_to(ROOT)}|N/A", category))
    # Functions with names indicating critical paths
    for m in re.finditer(r"def\s+([a-zA-Z0-9_]{6,})\(|([\w\.]+)\s*=\s*async\s*function", txt):
        fn = (m.group(1) or m.group(2)).split(".")[-1]
        if any(k in fn.lower() for k in ["retrieve","rerank","synthesize","guardrail","evidence","otel","abtest"]):
            q.append((f"What does `{fn}()` guarantee and what are its failure modes?",
                      "diagnostic", f"{path.relative_to(ROOT)}|N/A", category))
    return q

def row_for(idx, qt, intent, citation, category):
    qid = f"{slug(category)}-{hash_id(qt)}"
    difficulty = "beginner" if intent in ("navigational","definition") else "intermediate"
    answer_type = "linkcard" if intent=="navigational" else "extractive"
    answer_spec = {"must_include":[]}
    if category in ("observability","security"): answer_spec["must_include"]=["SLO","P95"]
    return {
        "question_id": qid,
        "question_text": qt,
        "difficulty": difficulty,
        "category": category,
        "intent": intent,
        "expected_citations": citation,
        "answer_type": answer_type if intent!="diagnostic" else "mixed",
        "answer_spec": json.dumps(answer_spec),
        "perms_tag": "public",
        "notes": ""
    }

def walk():
    discovered = []
    for path_hint, category in DOC_HINTS:
        p = ROOT / path_hint
        if not p.exists(): continue
        if p.is_file():
            if p.suffix in (".md",):
                discovered += extract_md_questions(p, category)
            elif p.name == "docker-compose.yml":
                discovered += extract_compose_questions(p)
            elif p.suffix in CODE_EXT:
                discovered += extract_code_questions(p, category)
        else:
            for f in p.rglob("*"):
                if f.is_dir(): continue
                if f.suffix not in CODE_EXT: continue
                if f.suffix == ".md":
                    discovered += extract_md_questions(f, category)
                elif f.name == "docker-compose.yml":
                    discovered += extract_compose_questions(f)
                else:
                    discovered += extract_code_questions(f, category)
    # Dedup by (question_text,citation)
    seen = set(); rows = []
    for qt,intent,cit,cat in discovered:
        key = (qt.strip(), cit)
        if key in seen: continue
        seen.add(key)
        rows.append(row_for(len(rows), qt.strip(), intent, cit, cat))
    return rows

def main():
    rows = walk()
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "question_id","question_text","difficulty","category","intent",
            "expected_citations","answer_type","answer_spec","perms_tag","notes"
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {len(rows)} questions → {CSV_OUT}")

if __name__ == "__main__":
    main()

