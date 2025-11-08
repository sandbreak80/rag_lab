"""
Artifact Base Classes - ID Correlation & Versioning

All artifacts (Schemas A-G) inherit from ArtifactBase to ensure:
1. Consistent trace_id/request_id across all artifacts
2. contract_version and schema_version for breaking change tracking
3. Timestamps for audit trails
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


CONTRACT_VERSION = "2.0.0"  # Bump on breaking changes to request/response contract
DEFAULT_SCHEMA_VERSION = "1.0.0"  # Bump on breaking changes to artifact structure


@dataclass
class ArtifactBase:
    """
    Base class for all observability artifacts (Schemas A-G).
    
    Ensures ID correlation and versioning across the pipeline.
    """
    # ID Correlation
    trace_id: str
    request_id: str
    
    # Versioning
    contract_version: str = CONTRACT_VERSION
    schema_version: str = DEFAULT_SCHEMA_VERSION
    
    # Audit
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self):
        """Override in subclasses to add artifact-specific fields"""
        return {
            'trace_id': self.trace_id,
            'request_id': self.request_id,
            'contract_version': self.contract_version,
            'schema_version': self.schema_version,
            'timestamp': self.timestamp
        }


@dataclass
class OrchestrationContext:
    """
    Context object passed through the entire pipeline.
    
    Carries IDs, tenant info, budgets, policy, and timing state.
    """
    # IDs (immutable after creation)
    trace_id: str
    request_id: str
    
    # Request metadata
    tenant: str
    user_id: str
    query: str
    
    # Strategy
    plan_id: str
    
    # Settings snapshot (for reproducibility)
    settings_snapshot: dict
    
    # Budgets (resource limits)
    budgets: 'Budgets'
    
    # Policy (behavioral constraints)
    policy: 'Policy'
    
    # A/B test
    ab_test: 'ABTest'
    
    # Timing
    start_time: float
    
    # Budget consumption tracking (mutable)
    budget_use: dict = field(default_factory=lambda: {"web_queries": 0, "internal_queries": 0, "kg_queries": 0})
    
    def to_dict(self):
        return {
            'trace_id': self.trace_id,
            'request_id': self.request_id,
            'tenant': self.tenant,
            'user_id': self.user_id,
            'query': self.query,
            'plan_id': self.plan_id,
            'settings_snapshot': self.settings_snapshot,
            'budgets': self.budgets.__dict__ if hasattr(self.budgets, '__dict__') else self.budgets,
            'policy': self.policy.__dict__ if hasattr(self.policy, '__dict__') else self.policy,
            'ab_test': self.ab_test.__dict__ if hasattr(self.ab_test, '__dict__') else self.ab_test,
            'start_time': self.start_time,
            'budget_use': self.budget_use
        }

