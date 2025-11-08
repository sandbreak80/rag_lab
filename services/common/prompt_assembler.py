"""
Prompt Assembly Engine with Versioning and Context Management

Handles:
- Prompt template management with versioning
- Context packaging within token limits
- Diff tracking for A/B testing
- Dynamic template selection based on query type
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
from enum import Enum

from services.common.evidence import Evidence


class PromptTemplate(str, Enum):
    """Available prompt templates"""
    QA_STANDARD = "qa_standard"
    QA_DETAILED = "qa_detailed"
    SUMMARIZATION = "summarization"
    RESEARCH = "research"
    CONVERSATIONAL = "conversational"


@dataclass
class PromptVersion:
    """Versioned prompt template"""
    template_id: str
    version: str
    template: str
    system_prompt: str
    max_tokens: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_hash(self) -> str:
        """Get content hash for diff tracking"""
        content = f"{self.template}||{self.system_prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class PromptAssembler:
    """
    Assembles prompts from templates + evidence with context management.
    
    Features:
    - Template versioning (A/B testing)
    - Context window management (truncation)
    - Token counting
    - Source attribution
    - Diff tracking
    """
    
    # Template registry
    TEMPLATES = {
        PromptTemplate.QA_STANDARD: PromptVersion(
            template_id="qa_standard",
            version="1.0.0",
            system_prompt=(
                "You are a helpful AI assistant. Answer questions accurately using "
                "the provided context. If you're unsure, say so. Always cite sources."
            ),
            template=(
                "Context:\n{context}\n\n"
                "Question: {query}\n\n"
                "Answer (with sources):"
            ),
            max_tokens=4096
        ),
        PromptTemplate.QA_DETAILED: PromptVersion(
            template_id="qa_detailed",
            version="1.0.0",
            system_prompt=(
                "You are an expert AI assistant. Provide comprehensive, well-structured "
                "answers with detailed explanations. Always cite sources and explain your reasoning."
            ),
            template=(
                "# Context Information\n{context}\n\n"
                "# User Question\n{query}\n\n"
                "# Instructions\n"
                "Provide a detailed answer that:\n"
                "1. Directly addresses the question\n"
                "2. Cites specific sources using [1], [2], etc.\n"
                "3. Explains your reasoning\n"
                "4. Acknowledges limitations or uncertainties\n\n"
                "# Your Answer:"
            ),
            max_tokens=8192
        ),
        PromptTemplate.RESEARCH: PromptVersion(
            template_id="research",
            version="1.0.0",
            system_prompt=(
                "You are a research assistant. Synthesize information from multiple "
                "sources, identify patterns, and provide evidence-based insights."
            ),
            template=(
                "# Research Materials\n{context}\n\n"
                "# Research Question\n{query}\n\n"
                "Synthesize the research materials to answer the question. Include:\n"
                "- Key findings from each source\n"
                "- Patterns and connections\n"
                "- Evidence quality assessment\n"
                "- Gaps in knowledge\n\n"
                "Research Summary:"
            ),
            max_tokens=8192
        ),
    }
    
    def __init__(self, token_counter=None):
        """
        Initialize prompt assembler.
        
        Args:
            token_counter: Function to count tokens (query, text) -> int
        """
        self.token_counter = token_counter or self._simple_token_count
    
    def assemble(
        self,
        query: str,
        evidence: List[Evidence],
        template: PromptTemplate = PromptTemplate.QA_STANDARD,
        max_context_tokens: int = 4096,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Assemble prompt from template + evidence.
        
        Args:
            query: User query
            evidence: Retrieved evidence list
            template: Which template to use
            max_context_tokens: Max tokens for context
            include_metadata: Include source metadata
        
        Returns:
            Dict with:
            - prompt: Full assembled prompt
            - system_prompt: System message
            - context: Formatted context
            - sources: Source attribution list
            - token_count: Estimated tokens
            - truncated: Whether context was truncated
        """
        prompt_version = self.TEMPLATES[template]
        
        # Format context with token budget
        context, sources, truncated = self._format_context(
            evidence,
            max_context_tokens,
            include_metadata
        )
        
        # Assemble full prompt
        full_prompt = prompt_version.template.format(
            context=context,
            query=query
        )
        
        # Count tokens
        total_tokens = self.token_counter(
            prompt_version.system_prompt + full_prompt
        )
        
        return {
            'prompt': full_prompt,
            'system_prompt': prompt_version.system_prompt,
            'context': context,
            'sources': sources,
            'token_count': total_tokens,
            'truncated': truncated,
            'template_id': prompt_version.template_id,
            'template_version': prompt_version.version,
            'template_hash': prompt_version.get_hash()
        }
    
    def _format_context(
        self,
        evidence: List[Evidence],
        max_tokens: int,
        include_metadata: bool
    ) -> tuple[str, List[Dict], bool]:
        """
        Format evidence into context string within token budget.
        
        Returns:
            (context_string, source_list, was_truncated)
        """
        context_parts = []
        sources = []
        current_tokens = 0
        truncated = False
        
        for idx, e in enumerate(evidence, 1):
            # Format source
            source_info = {
                'index': idx,
                'origin': e.origin_tool.value,
                'score': e.score,
            }
            
            if e.url:
                source_info['url'] = e.url
            if e.title:
                source_info['title'] = e.title
            if e.domain:
                source_info['domain'] = e.domain
            
            # Format content block
            header = f"[{idx}]"
            if include_metadata:
                if e.title:
                    header += f" {e.title}"
                if e.url:
                    header += f" ({e.domain or e.url})"
                elif e.doc_id:
                    header += f" (Document: {e.doc_id})"
            
            content_block = f"{header}\n{e.content}\n"
            
            # Check token budget
            block_tokens = self.token_counter(content_block)
            if current_tokens + block_tokens > max_tokens:
                truncated = True
                break
            
            context_parts.append(content_block)
            sources.append(source_info)
            current_tokens += block_tokens
        
        context = "\n".join(context_parts)
        return context, sources, truncated
    
    def _simple_token_count(self, text: str) -> int:
        """Simple token estimator (4 chars = 1 token)"""
        return len(text) // 4
    
    def get_template_diff(
        self,
        template_a: PromptTemplate,
        template_b: PromptTemplate
    ) -> Dict[str, Any]:
        """
        Compare two template versions for A/B testing.
        
        Returns diff showing changes.
        """
        version_a = self.TEMPLATES[template_a]
        version_b = self.TEMPLATES[template_b]
        
        return {
            'template_a': {
                'id': version_a.template_id,
                'version': version_a.version,
                'hash': version_a.get_hash()
            },
            'template_b': {
                'id': version_b.template_id,
                'version': version_b.version,
                'hash': version_b.get_hash()
            },
            'system_prompt_changed': version_a.system_prompt != version_b.system_prompt,
            'template_changed': version_a.template != version_b.template,
            'max_tokens_changed': version_a.max_tokens != version_b.max_tokens
        }

