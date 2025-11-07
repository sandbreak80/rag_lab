# Implementation Plan: Phase 1 - Foundations

**Project:** RAG Lab → World-Class  
**Phase:** 1 (Weeks 1-2)  
**Status:** 🚨 READY TO START  
**Target:** Contract enforcement + Provenance + Policy gates  

---

## Overview

Phase 1 establishes the **behavioral foundation** that everything else builds on:
- ✅ Contract Sentinel (no more essay mode)
- ✅ Immutable Evidence (full provenance)
- ✅ Recency Gate (temporal guarantees)
- ✅ Domain Filtering (quality sources)

---

## Task Breakdown

### 1A: Contract Sentinel (3-4 days)

#### Files to Create:
```
services/common/contract_sentinel.py      # Core logic
services/common/schemas.py                # Artifact schemas A-G
tests/test_contract_sentinel.py           # Unit tests
```

#### Files to Modify:
```
services/chat-service/app/service.py      # Add middleware
services/api-gateway/app/routes/chat.py   # Parse contract markers
```

#### Implementation Steps:

**Step 1: Define Contract Markers** (2 hours)
```python
# services/common/contract_sentinel.py

import re
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class ContractRequirement:
    """Parsed contract requirements from prompt"""
    requires_schemas: List[str]  # ["A", "B", "C", ...]
    requires_global_contract: bool
    marker_found: str  # The actual marker text
    
CONTRACT_MARKERS = [
    r"\[GLOBAL CONTRACT REQUIRED\]",
    r"must produce all artifacts",
    r"schemas? [A-G]",
    r"with full logs",
]

def parse_contract_requirements(prompt: str) -> Optional[ContractRequirement]:
    """
    Detect contract markers in prompt.
    Returns ContractRequirement if markers found, None otherwise.
    """
    for marker_pattern in CONTRACT_MARKERS:
        match = re.search(marker_pattern, prompt, re.IGNORECASE)
        if match:
            # Check for specific schemas
            schema_match = re.findall(r'schema[s]?\s+([A-G])', prompt, re.IGNORECASE)
            return ContractRequirement(
                requires_schemas=list(set(schema_match)) if schema_match else ["A", "B", "C", "D", "E", "F", "G"],
                requires_global_contract="global contract" in prompt.lower(),
                marker_found=match.group(0)
            )
    return None
```

**Step 2: Define Artifact Schemas** (3 hours)
```python
# services/common/schemas.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class SchemaA_Planner:
    """Schema A: Planner JSON"""
    original_query: str
    subtasks: List[Dict[str, Any]]
    routing_decisions: Dict[str, Any]
    estimated_complexity: str  # "low", "medium", "high"
    requires_recency: bool
    timestamp: str
    
@dataclass
class SchemaB_RetrievalLog:
    """Schema B: Retrieval Log"""
    queries_internal: int
    queries_web: int
    queries_research: int
    sources_found: int
    sources_after_dedup: int
    sources_after_filter: int
    timings_ms: Dict[str, int]
    policies_applied: List[str]
    timestamp: str
    
@dataclass
class SchemaC_EvidenceMap:
    """Schema C: Evidence Map with claim→source mapping"""
    claims: List[Dict[str, Any]]  # [{"claim": "...", "evidence_ids": [1, 2]}]
    evidence: List[Dict[str, Any]]  # Evidence objects with IDs
    total_claims: int
    total_evidence: int
    timestamp: str
    
@dataclass
class SchemaD_KnowledgeGraphLog:
    """Schema D: KG Log"""
    entities_extracted: int
    relationships_found: int
    disambiguations: List[Dict[str, str]]  # [{"entity": "MCP", "expanded": "Model Context Protocol"}]
    hops_performed: int
    timestamp: str
    status: str = "success"
    
@dataclass
class SchemaE_ChunkingReport:
    """Schema E: Chunking Report"""
    total_chunks: int
    avg_chunk_size: int
    chunking_strategy: str
    sample_chunks: List[Dict[str, Any]]
    params: Dict[str, Any]
    timestamp: str
    status: str = "success"
    
@dataclass
class SchemaF_GuardrailReport:
    """Schema F: Guardrail Report"""
    flags: List[Dict[str, Any]]
    actions_taken: List[str]
    risk_level: str  # "none", "low", "medium", "high"
    passed: bool
    timestamp: str
    error: Optional[str] = None
    
@dataclass
class SchemaG_ABGrading:
    """Schema G: A/B Grading (7-dimension)"""
    coverage: float
    grounding: float
    recency: float
    retrieval_quality: float
    decision_adherence: float
    structure: float
    conciseness: float
    overall: float
    delta_vs_baseline: Optional[float] = None
    ci_95: Optional[List[float]] = None
    timestamp: str = None
    
@dataclass
class GlobalContract:
    """Full contract response with all schemas"""
    schema_a: SchemaA_Planner
    schema_b: SchemaB_RetrievalLog
    schema_c: SchemaC_EvidenceMap
    schema_d: SchemaD_KnowledgeGraphLog
    schema_e: SchemaE_ChunkingReport
    schema_f: SchemaF_GuardrailReport
    schema_g: Optional[SchemaG_ABGrading] = None
    sha256: str = None  # Hash of entire response for reproducibility
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: asdict(v) if hasattr(v, '__dataclass_fields__') else v 
                for k, v in asdict(self).items()}
```

**Step 3: Implement Sentinel Middleware** (4 hours)
```python
# services/chat-service/app/service.py (additions)

from services.common.contract_sentinel import parse_contract_requirements
from services.common.schemas import GlobalContract, SchemaA_Planner, ...

def enforce_contract(prompt: str, response_data: dict) -> dict:
    """
    Enforce contract requirements.
    If prompt has contract markers, ensure all schemas present.
    """
    contract_req = parse_contract_requirements(prompt)
    
    if not contract_req:
        # No contract required, return as-is
        return response_data
    
    # Contract required - build GlobalContract
    artifacts = response_data.get("artifacts", {})
    
    # Ensure all required schemas present (create stubs if missing)
    global_contract = GlobalContract(
        schema_a=artifacts.get("schema_a") or create_stub_schema_a("missing"),
        schema_b=artifacts.get("schema_b") or create_stub_schema_b("missing"),
        schema_c=artifacts.get("schema_c") or create_stub_schema_c("missing"),
        schema_d=artifacts.get("schema_d") or create_stub_schema_d("missing"),
        schema_e=artifacts.get("schema_e") or create_stub_schema_e("missing"),
        schema_f=artifacts.get("schema_f") or create_stub_schema_f("missing"),
        schema_g=artifacts.get("schema_g"),  # Optional
        sha256=compute_sha256(response_data)
    )
    
    response_data["artifacts"] = global_contract.to_dict()
    response_data["contract_enforced"] = True
    
    return response_data

def create_stub_schema_a(reason: str) -> SchemaA_Planner:
    """Create stub when planner fails"""
    return SchemaA_Planner(
        original_query="N/A",
        subtasks=[],
        routing_decisions={},
        estimated_complexity="unknown",
        requires_recency=False,
        timestamp=datetime.now().isoformat(),
        status="missing",
        failure_note=reason
    )

# Similar stubs for B-F...
```

**Step 4: Add Tests** (2 hours)
```python
# tests/test_contract_sentinel.py

def test_contract_marker_detection():
    prompt = "What is MCP? [GLOBAL CONTRACT REQUIRED]"
    req = parse_contract_requirements(prompt)
    assert req is not None
    assert req.requires_global_contract
    
def test_no_contract_marker():
    prompt = "What is MCP?"
    req = parse_contract_requirements(prompt)
    assert req is None
    
def test_schema_enforcement():
    prompt = "Test [GLOBAL CONTRACT REQUIRED]"
    response = {"answer": "..."}
    enforced = enforce_contract(prompt, response)
    assert "artifacts" in enforced
    assert "schema_a" in enforced["artifacts"]
```

#### Acceptance Criteria:
- [ ] Prompts with contract markers trigger schema emission
- [ ] Missing schemas emit stubs with failure notes
- [ ] Hash (SHA-256) included for reproducibility
- [ ] Tests pass

---

### 1B: Immutable Evidence Object (4-5 days)

#### Files to Create:
```
services/common/evidence.py               # Evidence dataclass
services/common/evidence_tracker.py       # Evidence ID management
tests/test_evidence.py                    # Unit tests
```

#### Files to Modify:
```
services/vector-db/app/service.py         # Emit Evidence objects
services/web-search/app/service.py        # Emit Evidence objects
services/research-agent/app/service.py    # Emit Evidence objects
services/reranker/app/service.py          # Preserve Evidence
services/chat-service/app/service.py      # Build Evidence Map
```

#### Implementation Steps:

**Step 1: Define Evidence Class** (2 hours)
```python
# services/common/evidence.py

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
import hashlib

@dataclass(frozen=True)
class Evidence:
    """
    Immutable evidence object with full provenance.
    Set once at retrieval, never mutated.
    """
    # Identity
    id: int  # Unique ID for citation
    
    # Origin
    origin_tool: Literal["web_search", "rag", "research_agent", "file", "api"]
    
    # Source metadata
    url: str
    domain: str
    title: str
    
    # Temporal
    published_at: Optional[datetime]
    fetched_at: datetime
    
    # Quality signals
    is_primary: bool  # Official docs, GitHub repos, etc.
    authority_score: float  # 0-1
    
    # Content
    content_snippet: str  # Max 500 chars
    full_text_available: bool
    
    # Additional metadata
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "origin_tool": self.origin_tool,
            "url": self.url,
            "domain": self.domain,
            "title": self.title,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "fetched_at": self.fetched_at.isoformat(),
            "is_primary": self.is_primary,
            "authority_score": self.authority_score,
            "content_snippet": self.content_snippet,
            "metadata": self.metadata
        }
    
    @property
    def citation_text(self) -> str:
        """Format for display: [#n] Title (domain) [published_date]"""
        date_str = f" [{self.published_at.strftime('%Y-%m-%d')}]" if self.published_at else ""
        return f"[#{self.id}] {self.title} ({self.domain}){date_str}"
    
    def compute_hash(self) -> str:
        """Unique hash for deduplication"""
        key = f"{self.domain}|{self.title}|{self.url}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
```

**Step 2: Evidence Tracker** (2 hours)
```python
# services/common/evidence_tracker.py

from typing import List, Dict
from services.common.evidence import Evidence

class EvidenceTracker:
    """
    Manages Evidence objects across pipeline.
    Ensures immutability and deduplication.
    """
    def __init__(self):
        self.evidence: List[Evidence] = []
        self.evidence_by_id: Dict[int, Evidence] = {}
        self.evidence_by_hash: Dict[str, Evidence] = {}
        self.next_id = 1
        
    def add(self, evidence: Evidence) -> Evidence:
        """
        Add evidence with auto-assigned ID.
        Deduplicates by hash.
        Returns the (possibly existing) Evidence object.
        """
        ev_hash = evidence.compute_hash()
        
        if ev_hash in self.evidence_by_hash:
            # Already exists, return existing
            return self.evidence_by_hash[ev_hash]
        
        # New evidence - assign ID
        new_evidence = Evidence(
            id=self.next_id,
            **{k: v for k, v in evidence.__dict__.items() if k != 'id'}
        )
        
        self.evidence.append(new_evidence)
        self.evidence_by_id[new_evidence.id] = new_evidence
        self.evidence_by_hash[ev_hash] = new_evidence
        self.next_id += 1
        
        return new_evidence
    
    def get_by_id(self, evidence_id: int) -> Optional[Evidence]:
        return self.evidence_by_id.get(evidence_id)
    
    def to_schema_c(self) -> dict:
        """Export as Schema C (Evidence Map)"""
        return {
            "evidence": [ev.to_dict() for ev in self.evidence],
            "total_evidence": len(self.evidence),
            "by_origin": self._count_by_origin(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _count_by_origin(self) -> Dict[str, int]:
        from collections import Counter
        return dict(Counter(ev.origin_tool for ev in self.evidence))
```

**Step 3: Modify Retrievers** (4 hours)
```python
# services/vector-db/app/service.py

from services.common.evidence import Evidence

def search_documents(query: str) -> List[Evidence]:
    """
    Search vector DB and return Evidence objects.
    """
    results = chroma_collection.query(query_texts=[query], n_results=10)
    
    evidence_list = []
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        evidence = Evidence(
            id=0,  # Will be assigned by tracker
            origin_tool="rag",
            url=metadata.get('file_path', 'internal://document'),
            domain="internal",
            title=metadata.get('file_name', 'Document'),
            published_at=None,
            fetched_at=datetime.now(),
            is_primary=False,
            authority_score=results['distances'][0][i],
            content_snippet=doc[:500],
            full_text_available=True,
            metadata=metadata
        )
        evidence_list.append(evidence)
    
    return evidence_list
```

```python
# services/web-search/app/service.py

def web_search(query: str, domain_policy) -> List[Evidence]:
    """
    Search web and return Evidence objects.
    """
    results = searxng_search(query)
    evidence_list = []
    
    for result in results:
        # Apply domain filtering
        if domain_policy.is_denied(result['url']):
            continue
        
        evidence = Evidence(
            id=0,
            origin_tool="web_search",
            url=result['url'],
            domain=extract_domain(result['url']),
            title=result['title'],
            published_at=parse_date(result.get('publishedDate')),
            fetched_at=datetime.now(),
            is_primary=domain_policy.is_primary(result['url']),
            authority_score=domain_policy.score_authority(result['url']),
            content_snippet=result.get('content', '')[:500],
            full_text_available=False,
            metadata=result
        )
        evidence_list.append(evidence)
    
    return evidence_list
```

**Step 4: Preserve Through Pipeline** (3 hours)
```python
# services/chat-service/app/service.py

def process_query(query: str, settings: dict) -> dict:
    """
    Main query processing with Evidence tracking.
    """
    tracker = EvidenceTracker()
    
    # 1. Retrieve from multiple sources
    rag_results = vector_db_service.search(query)
    for ev in rag_results:
        tracker.add(ev)
    
    web_results = web_search_service.search(query)
    for ev in web_results:
        tracker.add(ev)
    
    # 2. Rerank (preserve Evidence)
    reranked = reranker_service.rerank(tracker.evidence, query)
    # reranked returns List[Evidence] in new order
    
    # 3. Synthesis with citations
    answer, claim_map = synthesize_with_citations(query, reranked)
    # claim_map: [{"claim": "...", "evidence_ids": [1, 2]}, ...]
    
    # 4. Build Schema C
    schema_c = {
        **tracker.to_schema_c(),
        "claims": claim_map,
        "total_claims": len(claim_map)
    }
    
    return {
        "answer": answer,
        "artifacts": {"schema_c": schema_c}
    }
```

#### Acceptance Criteria:
- [ ] All Evidence objects have `origin_tool` preserved
- [ ] Deduplication works (same domain+title = one Evidence)
- [ ] Citations use `[#n]` format
- [ ] Schema C maps claims → evidence IDs
- [ ] Tests pass

---

### 1C: Recency Gate (2-3 days)

#### Files to Create:
```
services/common/routing_policy.py         # Policy definitions
services/common/temporal_detector.py      # Detect temporal queries
tests/test_recency_gate.py                # Unit tests
```

#### Files to Modify:
```
services/query-decomposition/app/service.py  # Tag temporal subtasks
services/model-router/app/service.py         # Enforce recency policy
services/chat-service/app/service.py         # Block if policy violated
```

#### Implementation Steps:

**Step 1: Temporal Detection** (2 hours)
```python
# services/common/temporal_detector.py

import re
from typing import Optional

TEMPORAL_MARKERS = [
    r'\b(latest|recent|new|current)\b',
    r'\b(today|yesterday|this week|last \d+ (hours?|days?|weeks?))\b',
    r'≤\s*\d+\s*(hours?|days?)',
    r'\bin the (last|past) \d+',
]

def detect_temporal_requirement(query: str) -> Optional[dict]:
    """
    Detect if query requires recent information.
    Returns None or {"max_staleness_hours": N, "marker": "..."}
    """
    for pattern in TEMPORAL_MARKERS:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            # Extract time window
            hours = extract_hours_from_match(match.group(0))
            return {
                "max_staleness_hours": hours,
                "marker": match.group(0),
                "requires_recency": True
            }
    return None

def extract_hours_from_match(text: str) -> int:
    """Convert temporal text to hours"""
    if "hour" in text:
        return int(re.search(r'\d+', text).group())
    elif "day" in text:
        return int(re.search(r'\d+', text).group()) * 24
    elif "week" in text:
        return int(re.search(r'\d+', text).group()) * 24 * 7
    elif "latest" in text or "recent" in text:
        return 48  # Default to 48h for "latest"
    return 72  # Default 3 days
```

**Step 2: Routing Policy** (3 hours)
```python
# services/common/routing_policy.py

from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta
from services.common.evidence import Evidence

@dataclass
class RecencyPolicy:
    """Policy for temporal queries"""
    max_staleness_hours_news: int = 48
    max_staleness_days_procedural: int = 30
    min_primary_sources: int = 2
    min_internal_conf_before_web: float = 0.75
    
    def validate_evidence(
        self, 
        evidence_list: List[Evidence], 
        max_staleness_hours: int
    ) -> dict:
        """
        Check if evidence meets recency requirements.
        Returns {"passed": bool, "reason": str, "fresh_count": int}
        """
        now = datetime.now()
        max_age = timedelta(hours=max_staleness_hours)
        
        fresh_primaries = [
            ev for ev in evidence_list
            if ev.is_primary and ev.published_at and (now - ev.published_at) <= max_age
        ]
        
        passed = len(fresh_primaries) >= self.min_primary_sources
        
        return {
            "passed": passed,
            "fresh_primary_count": len(fresh_primaries),
            "required": self.min_primary_sources,
            "reason": "OK" if passed else f"Need {self.min_primary_sources} fresh primaries, found {len(fresh_primaries)}"
        }
```

**Step 3: Enforce in Chat Service** (2 hours)
```python
# services/chat-service/app/service.py

def process_query_with_recency_gate(query: str, settings: dict) -> dict:
    """Process query with recency enforcement"""
    
    # 1. Detect temporal requirement
    temporal_req = detect_temporal_requirement(query)
    
    # 2. Retrieve evidence
    tracker = EvidenceTracker()
    # ... retrieve from sources ...
    
    # 3. If temporal, validate
    if temporal_req:
        policy = RecencyPolicy()
        validation = policy.validate_evidence(
            tracker.evidence,
            temporal_req["max_staleness_hours"]
        )
        
        if not validation["passed"]:
            # GATE FAILED
            return {
                "answer": "⚠️  Cannot provide confident answer: " + validation["reason"],
                "partial": True,
                "artifacts": {
                    "schema_b": {
                        "recency_gate": "FAILED",
                        "reason": validation["reason"],
                        "policy": temporal_req
                    }
                }
            }
    
    # Gate passed or not required, continue...
    return synthesize_answer(query, tracker.evidence)
```

#### Acceptance Criteria:
- [ ] "Latest MCP changes ≤48h" triggers recency detection
- [ ] System blocks finalization if no fresh primaries
- [ ] Partial answer + explanation provided on gate failure
- [ ] Schema B includes recency gate status

---

### 1D: Domain Allow/Deny Lists (1-2 days)

#### Files to Create:
```
services/common/domain_policy.py          # Domain filtering logic
config/domain_allowlist.txt               # Curated allowlist
config/domain_denylist.txt                # SEO spam denylist
tests/test_domain_policy.py               # Unit tests
```

#### Implementation Steps:

**Step 1: Domain Lists** (1 hour)
```
# config/domain_allowlist.txt (primary sources)
github.com
arxiv.org
modelcontextprotocol.io
docs.trychroma.com
pytorch.org
tensorflow.org
python.org
docs.anthropic.com
openai.com/docs
huggingface.co/docs

# config/domain_denylist.txt (SEO spam)
asana.com
indeed.com
grammarly.com
*.indeed.*
upwork.com
freelancer.com
```

**Step 2: Policy Implementation** (3 hours)
```python
# services/common/domain_policy.py

class DomainPolicy:
    """Filter and score domains"""
    
    def __init__(self):
        self.allowlist = self._load_list("config/domain_allowlist.txt")
        self.denylist = self._load_list("config/domain_denylist.txt")
        
    def is_primary(self, url: str) -> bool:
        """Check if URL is from primary source"""
        domain = extract_domain(url)
        return any(allowed in domain for allowed in self.allowlist)
    
    def is_denied(self, url: str) -> bool:
        """Check if URL is denied"""
        domain = extract_domain(url)
        return any(denied in domain for denied in self.denylist)
    
    def score_authority(self, url: str) -> float:
        """Score domain authority 0-1"""
        if self.is_primary(url):
            return 1.0
        elif self.is_denied(url):
            return 0.0
        else:
            return 0.5  # Unknown, neutral
```

**Step 3: Apply in Web Search** (1 hour)
```python
# services/web-search/app/service.py

domain_policy = DomainPolicy()

def search_with_filtering(query: str) -> List[Evidence]:
    raw_results = searxng_search(query)
    
    filtered = [
        r for r in raw_results 
        if not domain_policy.is_denied(r['url'])
    ]
    
    # Prioritize primaries
    filtered.sort(key=lambda r: domain_policy.score_authority(r['url']), reverse=True)
    
    return [result_to_evidence(r) for r in filtered]
```

#### Acceptance Criteria:
- [ ] Asana/Indeed URLs filtered out
- [ ] Primary sources (GitHub, official docs) scored 1.0
- [ ] Results sorted by authority score

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/test_contract_sentinel.py
pytest tests/test_evidence.py
pytest tests/test_recency_gate.py
pytest tests/test_domain_policy.py
```

### Integration Tests
```python
# tests/integration/test_phase1.py

def test_temporal_query_enforcement():
    """Test recency gate end-to-end"""
    response = query("Latest MCP changes ≤48h", preset="P4-STRONG")
    
    assert response["artifacts"]["schema_b"]["recency_gate"] in ["PASSED", "FAILED"]
    if response["artifacts"]["schema_b"]["recency_gate"] == "PASSED":
        # Check evidence has fresh primaries
        evidence = response["artifacts"]["schema_c"]["evidence"]
        fresh_primaries = [
            ev for ev in evidence 
            if ev["is_primary"] and is_within_48h(ev["published_at"])
        ]
        assert len(fresh_primaries) >= 2

def test_contract_enforcement():
    """Test contract sentinel"""
    response = query("What is MCP? [GLOBAL CONTRACT REQUIRED]", preset="P4-STRONG")
    
    assert "artifacts" in response
    assert "schema_a" in response["artifacts"]
    assert "schema_b" in response["artifacts"]
    assert "sha256" in response["artifacts"]

def test_provenance_preservation():
    """Test Evidence immutability"""
    response = query("Compare RAG vs web search results", preset="P4-STRONG")
    
    evidence = response["artifacts"]["schema_c"]["evidence"]
    assert any(ev["origin_tool"] == "rag" for ev in evidence)
    assert any(ev["origin_tool"] == "web_search" for ev in evidence)
    
    # Check claims have evidence IDs
    claims = response["artifacts"]["schema_c"]["claims"]
    for claim in claims:
        assert "evidence_ids" in claim
        assert len(claim["evidence_ids"]) > 0

def test_domain_filtering():
    """Test domain deny list"""
    response = query("How to write executive summary", preset="P4-STRONG")
    
    evidence = response["artifacts"]["schema_c"]["evidence"]
    for ev in evidence:
        assert "asana.com" not in ev["domain"]
        assert "indeed.com" not in ev["domain"]
```

### Acceptance Tests (from feedback)
```bash
# Run the exact tests from the feedback document
./tests/acceptance/test_temporal_enforcement.sh
./tests/acceptance/test_denylist_suppression.sh
./tests/acceptance/test_provenance_integrity.sh
```

---

## Timeline

### Week 1
- **Mon-Tue:** Task 1A (Contract Sentinel)
- **Wed-Fri:** Task 1B (Evidence Objects)

### Week 2
- **Mon-Tue:** Task 1C (Recency Gate)
- **Wed:** Task 1D (Domain Filtering)
- **Thu-Fri:** Integration testing + bug fixes

---

## Definition of Done

Phase 1 is complete when:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All acceptance tests (from feedback) pass
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Deployed to AWS for validation
- [ ] Torture prompt produces all schemas A-G

---

## Risks & Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation:** Feature flags for new behavior, gradual rollout

### Risk 2: Performance Impact (Evidence tracking overhead)
**Mitigation:** Profile early, optimize if needed (but correctness > speed)

### Risk 3: Schema Complexity Overwhelming Users
**Mitigation:** UI displays schemas in collapsible sections, not all at once

---

## Next Phase Preview

Phase 2 will add:
- Per-stage timing waterfall
- KG disambiguation logs
- Chunking decision reports
- Guardrail fallback handling

But **Phase 1 must be solid first**. These are the foundations.

---

**Status:** 🚨 READY FOR APPROVAL TO START  
**Estimated Effort:** 80-100 hours (2 weeks, 2 developers)  
**Risk Level:** Medium (refactoring core pipeline)  
**ROI:** High (unlocks all downstream improvements)

