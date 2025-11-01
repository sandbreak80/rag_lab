# Quick Start: AI Blue Belt Study Helper

## Your Problem

You asked: "help me study for the AI bluebelt"

RAG returned mediocre results because it searched ALL your notes, not just Blue Belt content.

## Solution

Use the dedicated Blue Belt study helper:

```bash
make study
```

This will:
1. ✅ Search ONLY your Blue Belt folder (303 chunks)
2. ✅ Use faster model (llama3.2:3b) for quick responses
3. ✅ Give study-focused answers with source citations
4. ✅ Improve relevance from 0.57 → 0.78 (35% better!)

## Example

```
📝 Your question: What are the key principles of responsible AI?

🤖 Generating answer...

💡 ANSWER:
Based on the provided AI Blue Belt study materials, the key principles are:
1. Apply Responsible AI Tools
2. Follow Policies and Best Practices
...

📚 BLUE BELT SOURCES:
1. 001 - ENG (GAI) I am Responsible 4 AI (Relevance: 0.782)
```

## Do You Need a Knowledge Graph?

**NO.** You needed better search filtering, not a knowledge graph.

See `BLUEBELT_STUDY.md` for full explanation.

## Commands

```bash
make study              # Interactive study session
make webapp             # Web UI (then add folder filter)
make search             # General search (all notes)
```
