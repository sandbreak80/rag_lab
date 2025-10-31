"""
Agentic Chunking: LLM-powered semantic chunking for better RAG performance

Uses LLM to intelligently determine chunk boundaries based on:
- Semantic cohesion (keep related concepts together)
- Document structure (respect headings, code blocks, lists)
- Context preservation (don't split mid-thought)
"""

import re
import json
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

import config


@dataclass
class SemanticUnit:
    """A semantically coherent unit of content"""
    text: str
    start_pos: int
    end_pos: int
    unit_type: str  # paragraph, code_block, list, heading, table
    section: Optional[str] = None  # Parent section heading
    topics: List[str] = None  # Key topics/concepts
    
    def __post_init__(self):
        if self.topics is None:
            self.topics = []


@dataclass
class ChunkWithContext:
    """A chunk enriched with contextual metadata"""
    text: str
    metadata: Dict[str, Any]
    semantic_units: List[SemanticUnit]
    
    def __len__(self):
        return len(self.text)


class AgenticChunker:
    """LLM-powered semantic chunking for markdown documents"""
    
    def __init__(self, 
                 llm_model: str = None,
                 target_chunk_size: int = None,
                 max_chunk_size: int = None,
                 ollama_url: str = None):
        """
        Initialize agentic chunker
        
        Args:
            llm_model: Model for analysis (default: llama3.2:3b)
            target_chunk_size: Target size in chars (default: 1000)
            max_chunk_size: Max size in chars (default: 1500)
            ollama_url: Ollama API URL
        """
        self.model = llm_model or config.CHAT_MODEL
        self.target_size = target_chunk_size or 1000
        self.max_size = max_chunk_size or 1500
        self.ollama_url = ollama_url or config.OLLAMA_BASE_URL
        
        # Regex patterns for structure detection
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'```[\w]*\n.*?\n```', re.DOTALL)
        self.list_pattern = re.compile(r'^[\s]*[-*+]\s+.+$', re.MULTILINE)
        self.numbered_list_pattern = re.compile(r'^[\s]*\d+\.\s+.+$', re.MULTILINE)
        self.table_pattern = re.compile(r'\|.+\|', re.MULTILINE)
    
    def chunk_markdown(self, 
                      content: str, 
                      doc_metadata: Dict[str, Any]) -> List[ChunkWithContext]:
        """
        Intelligently chunk markdown content using LLM analysis
        
        Args:
            content: Markdown content to chunk
            doc_metadata: Document metadata (title, tags, etc.)
            
        Returns:
            List of chunks with contextual metadata
        """
        if not content or len(content.strip()) == 0:
            return []
        
        # For very short content, return as single chunk
        if len(content) <= self.target_size:
            return [ChunkWithContext(
                text=content,
                metadata=self._create_chunk_metadata(doc_metadata, 0, 1),
                semantic_units=[SemanticUnit(
                    text=content,
                    start_pos=0,
                    end_pos=len(content),
                    unit_type='complete_document'
                )]
            )]
        
        try:
            # Step 1: Analyze document structure
            structure = self._analyze_structure(content, doc_metadata)
            
            # Validate structure
            if not isinstance(structure, dict):
                raise ValueError(f"structure must be dict, got {type(structure)}")
            
            # Step 2: Identify semantic units
            units = self._identify_semantic_units(content, structure)
            
            # Validate units
            if not isinstance(units, list):
                raise ValueError(f"units must be list, got {type(units)}")
            
            # Step 3: Group units into optimal chunks
            chunks = self._create_chunks(units, doc_metadata)
            
            return chunks
            
        except Exception as e:
            import traceback
            print(f"⚠️  Agentic chunking failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            if hasattr(e, '__traceback__'):
                print(f"   Traceback: {traceback.format_exc().splitlines()[-3]}")
            print(f"   Falling back to simple chunking")
            return self._fallback_chunking(content, doc_metadata)
    
    def _analyze_structure(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze document structure using LLM
        
        Returns structure info: headings, sections, special blocks
        """
        # Extract structural elements with regex first (fast)
        headings = self._extract_headings(content)
        code_blocks = self._extract_code_blocks(content)
        lists = self._extract_lists(content)
        
        # For complex documents, use LLM for deeper analysis
        # DISABLED: LLM analysis is slow and timing out, regex is sufficient
        # if len(content) > 2000 and len(headings) > 3:
        #     try:
        #         llm_structure = self._llm_analyze_structure(content, metadata)
        #         return {
        #             'headings': headings,
        #             'code_blocks': code_blocks,
        #             'lists': lists,
        #             'sections': llm_structure.get('sections', []),
        #             'topics': llm_structure.get('topics', []),
        #             'document_type': llm_structure.get('document_type', 'general')
        #         }
        #     except Exception as e:
        #         print(f"   LLM structure analysis failed: {e}, using regex only")
        
        # Return regex-based structure
        return {
            'headings': headings,
            'code_blocks': code_blocks,
            'lists': lists,
            'sections': self._infer_sections_from_headings(headings, content),
            'topics': [],
            'document_type': 'general'
        }
    
    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """Extract markdown headings"""
        headings = []
        for match in self.heading_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append({
                'level': level,
                'text': text,
                'position': match.start()
            })
        return headings
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract code blocks"""
        blocks = []
        for match in self.code_block_pattern.finditer(content):
            blocks.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group(0)
            })
        return blocks
    
    def _extract_lists(self, content: str) -> List[Dict[str, Any]]:
        """Extract lists (bullet and numbered)"""
        lists = []
        
        # Find bullet lists
        for match in self.list_pattern.finditer(content):
            lists.append({
                'start': match.start(),
                'end': match.end(),
                'type': 'bullet'
            })
        
        # Find numbered lists
        for match in self.numbered_list_pattern.finditer(content):
            lists.append({
                'start': match.start(),
                'end': match.end(),
                'type': 'numbered'
            })
        
        return sorted(lists, key=lambda x: x['start'])
    
    def _infer_sections_from_headings(self, headings: List[Dict], content: str) -> List[Dict]:
        """Infer document sections from headings"""
        if not headings:
            return [{'heading': None, 'start': 0, 'end': len(content)}]
        
        sections = []
        for i, heading in enumerate(headings):
            start = heading['position']
            end = headings[i + 1]['position'] if i + 1 < len(headings) else len(content)
            sections.append({
                'heading': heading['text'],
                'level': heading['level'],
                'start': start,
                'end': end
            })
        
        return sections
    
    def _llm_analyze_structure(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze document structure (for complex docs)"""
        # Truncate content for LLM analysis (use first 2000 chars)
        sample = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""Analyze this markdown document structure. Return JSON only.

Document: {metadata.get('title', 'Untitled')}
Content sample:
{sample}

Identify:
1. Main sections/topics
2. Document type (tutorial, reference, notes, meeting, guide, etc.)
3. Key concepts discussed

Return JSON:
{{
  "sections": ["section1", "section2"],
  "topics": ["topic1", "topic2"],
  "document_type": "type"
}}"""

        try:
            response = self._call_llm(prompt, max_tokens=300)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception as e:
            print(f"   LLM analysis error: {e}")
        
        return {'sections': [], 'topics': [], 'document_type': 'general'}
    
    def _identify_semantic_units(self, content: str, structure: Dict[str, Any]) -> List[SemanticUnit]:
        """
        Identify semantic units (coherent pieces of content)
        
        Uses structure analysis to find natural boundaries
        """
        units = []
        
        # Validate structure is a dict
        if not isinstance(structure, dict):
            print(f"⚠️  structure is not a dict: {type(structure)}")
            # Fallback: treat entire content as one section
            return self._split_by_paragraphs(content, 0, None)
        
        # Get structural boundaries
        code_blocks = structure.get('code_blocks', [])
        sections = structure.get('sections', [])
        
        # Process each section
        for section in sections:
            # Validate section is a dict
            if not isinstance(section, dict):
                print(f"⚠️  section is not a dict: {type(section)}")
                continue
            
            section_start = section.get('start', 0)
            section_end = section.get('end', len(content))
            section_heading = section.get('heading')
            section_content = content[section_start:section_end]
            
            # Check if section contains code blocks
            section_code_blocks = [
                cb for cb in code_blocks 
                if isinstance(cb, dict) and 
                   'start' in cb and 'end' in cb and
                   cb['start'] >= section_start and cb['end'] <= section_end
            ]
            
            if section_code_blocks:
                # Handle sections with code blocks carefully
                units.extend(self._split_section_with_code(
                    section_content, section_start, section_heading, section_code_blocks
                ))
            else:
                # Split by paragraphs
                units.extend(self._split_by_paragraphs(
                    section_content, section_start, section_heading
                ))
        
        return units
    
    def _split_section_with_code(self, 
                                 content: str, 
                                 offset: int,
                                 section_heading: str,
                                 code_blocks: List[Dict]) -> List[SemanticUnit]:
        """Split section that contains code blocks"""
        units = []
        current_pos = 0
        
        # Validate code_blocks is a list of dicts
        if not isinstance(code_blocks, list):
            print(f"⚠️  code_blocks is not a list: {type(code_blocks)}")
            return self._split_by_paragraphs(content, offset, section_heading)
        
        for cb in code_blocks:
            if not isinstance(cb, dict):
                print(f"⚠️  code block is not a dict: {type(cb)}")
                continue
            # Text before code block
            if cb['start'] - offset > current_pos:
                text_before = content[current_pos:cb['start'] - offset]
                if text_before.strip():
                    units.append(SemanticUnit(
                        text=text_before.strip(),
                        start_pos=offset + current_pos,
                        end_pos=cb['start'],
                        unit_type='text',
                        section=section_heading
                    ))
            
            # Code block itself (keep intact)
            units.append(SemanticUnit(
                text=cb['text'],
                start_pos=cb['start'],
                end_pos=cb['end'],
                unit_type='code_block',
                section=section_heading
            ))
            
            current_pos = cb['end'] - offset
        
        # Remaining text after last code block
        if current_pos < len(content):
            remaining = content[current_pos:]
            if remaining.strip():
                units.append(SemanticUnit(
                    text=remaining.strip(),
                    start_pos=offset + current_pos,
                    end_pos=offset + len(content),
                    unit_type='text',
                    section=section_heading
                ))
        
        return units
    
    def _split_by_paragraphs(self, 
                            content: str, 
                            offset: int,
                            section_heading: str) -> List[SemanticUnit]:
        """Split content by paragraphs (double newline)"""
        units = []
        paragraphs = re.split(r'\n\s*\n', content)
        
        current_pos = 0
        for para in paragraphs:
            if not para.strip():
                current_pos += len(para) + 2  # +2 for \n\n
                continue
            
            # Determine unit type
            unit_type = 'paragraph'
            if self.list_pattern.search(para) or self.numbered_list_pattern.search(para):
                unit_type = 'list'
            elif self.table_pattern.search(para):
                unit_type = 'table'
            
            units.append(SemanticUnit(
                text=para.strip(),
                start_pos=offset + current_pos,
                end_pos=offset + current_pos + len(para),
                unit_type=unit_type,
                section=section_heading
            ))
            
            current_pos += len(para) + 2  # +2 for \n\n
        
        return units
    
    def _create_chunks(self, 
                      units: List[SemanticUnit], 
                      doc_metadata: Dict[str, Any]) -> List[ChunkWithContext]:
        """Group semantic units into optimal chunks"""
        if not units:
            return []
        
        chunks = []
        current_chunk_units = []
        current_size = 0
        
        for unit in units:
            unit_size = len(unit.text)
            
            # Special handling for large units (code blocks, tables, or any oversized content)
            if unit_size > self.max_size:
                # Close current chunk if any
                if current_chunk_units:
                    chunks.append(self._build_chunk(current_chunk_units, doc_metadata, len(chunks)))
                    current_chunk_units = []
                    current_size = 0
                
                # Split large unit into smaller pieces
                if unit_size > self.max_size * 2:
                    # Very large unit - split it
                    print(f"   ⚠️  Very large unit ({unit_size} chars), splitting...")
                    split_units = self._split_large_unit(unit)
                    for split_unit in split_units:
                        chunks.append(self._build_chunk([split_unit], doc_metadata, len(chunks)))
                else:
                    # Moderately large unit - keep as single chunk
                    chunks.append(self._build_chunk([unit], doc_metadata, len(chunks)))
                continue
            
            # Check if adding this unit would exceed max size
            if current_size + unit_size > self.max_size:
                # Close current chunk
                if current_chunk_units:
                    chunks.append(self._build_chunk(current_chunk_units, doc_metadata, len(chunks)))
                current_chunk_units = [unit]
                current_size = unit_size
            
            # Check if we should close chunk at target size (natural boundary)
            elif current_size + unit_size > self.target_size and current_chunk_units:
                # Close at natural boundary
                chunks.append(self._build_chunk(current_chunk_units, doc_metadata, len(chunks)))
                current_chunk_units = [unit]
                current_size = unit_size
            
            else:
                # Add to current chunk
                current_chunk_units.append(unit)
                current_size += unit_size
        
        # Add remaining units
        if current_chunk_units:
            chunks.append(self._build_chunk(current_chunk_units, doc_metadata, len(chunks)))
        
        return chunks
    
    def _split_large_unit(self, unit: SemanticUnit) -> List[SemanticUnit]:
        """Split a very large semantic unit into smaller pieces"""
        text = unit.text
        target_size = self.max_size
        
        # Try splitting by paragraphs first
        paragraphs = text.split('\n\n')
        
        # If no paragraphs (single block), split by sentences
        if len(paragraphs) == 1:
            paragraphs = text.split('. ')
            separator = '. '
        else:
            separator = '\n\n'
        
        # If still one piece, force split by character count
        if len(paragraphs) == 1:
            split_units = []
            for i in range(0, len(text), target_size):
                chunk_text = text[i:i + target_size]
                split_units.append(SemanticUnit(
                    text=chunk_text,
                    start_pos=unit.start_pos + i,
                    end_pos=unit.start_pos + i + len(chunk_text),
                    unit_type=unit.unit_type,
                    section=unit.section
                ))
            return split_units
        
        # Group paragraphs into chunks
        split_units = []
        current_text = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > target_size and current_text:
                # Create a split unit
                split_units.append(SemanticUnit(
                    text=separator.join(current_text),
                    start_pos=unit.start_pos,
                    end_pos=unit.start_pos + current_size,
                    unit_type=unit.unit_type,
                    section=unit.section
                ))
                current_text = [para]
                current_size = para_size
            else:
                current_text.append(para)
                current_size += para_size + len(separator)
        
        # Add remaining
        if current_text:
            split_units.append(SemanticUnit(
                text=separator.join(current_text),
                start_pos=unit.start_pos,
                end_pos=unit.end_pos,
                unit_type=unit.unit_type,
                section=unit.section
            ))
        
        return split_units if split_units else [unit]
    
    def _build_chunk(self, 
                    units: List[SemanticUnit], 
                    doc_metadata: Dict[str, Any],
                    chunk_index: int) -> ChunkWithContext:
        """Build a chunk from semantic units"""
        # Combine unit texts
        chunk_text = '\n\n'.join(unit.text for unit in units)
        
        # Gather metadata - handle both string and dict sections
        sections = []
        for u in units:
            if u.section:
                # Handle both string and dict section types
                if isinstance(u.section, str):
                    sections.append(u.section)
                elif isinstance(u.section, dict) and 'heading' in u.section:
                    sections.append(u.section['heading'])
        sections = list(set(sections))  # Remove duplicates
        
        unit_types = list(set(u.unit_type for u in units))
        
        metadata = self._create_chunk_metadata(doc_metadata, chunk_index, None)
        metadata.update({
            'sections': sections,
            'unit_types': unit_types,
            'num_units': len(units),
        })
        
        return ChunkWithContext(
            text=chunk_text,
            metadata=metadata,
            semantic_units=units
        )
    
    def _create_chunk_metadata(self, 
                              doc_metadata: Dict[str, Any],
                              chunk_index: int,
                              total_chunks: Optional[int]) -> Dict[str, Any]:
        """Create metadata for a chunk"""
        metadata = {
            'chunk_index': chunk_index,
            'chunking_method': 'agentic',
        }
        
        if total_chunks is not None:
            metadata['total_chunks'] = total_chunks
        
        # Extract simple metadata from doc (handle both dict formats)
        if 'title' in doc_metadata:
            metadata['title'] = doc_metadata['title']
        if 'file_name' in doc_metadata:
            metadata['file_name'] = doc_metadata['file_name']
        
        return metadata
    
    def _fallback_chunking(self, content: str, doc_metadata: Dict[str, Any]) -> List[ChunkWithContext]:
        """Fallback to simple paragraph-based chunking if agentic fails"""
        print("   Using fallback paragraph-based chunking")
        
        # Split by paragraphs
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        current_text = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            if current_size + para_size > self.max_size and current_text:
                # Create chunk
                chunk_text = '\n\n'.join(current_text)
                chunks.append(ChunkWithContext(
                    text=chunk_text,
                    metadata=self._create_chunk_metadata(doc_metadata, len(chunks), None),
                    semantic_units=[SemanticUnit(
                        text=chunk_text,
                        start_pos=0,
                        end_pos=len(chunk_text),
                        unit_type='fallback'
                    )]
                ))
                current_text = [para]
                current_size = para_size
            else:
                current_text.append(para)
                current_size += para_size
        
        # Add remaining
        if current_text:
            chunk_text = '\n\n'.join(current_text)
            chunks.append(ChunkWithContext(
                text=chunk_text,
                metadata=self._create_chunk_metadata(doc_metadata, len(chunks), None),
                semantic_units=[SemanticUnit(
                    text=chunk_text,
                    start_pos=0,
                    end_pos=len(chunk_text),
                    unit_type='fallback'
                )]
            ))
        
        return chunks
    
    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Call Ollama LLM"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent analysis
                        "num_predict": max_tokens
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            raise Exception(f"LLM call failed: {e}")


def test_agentic_chunker():
    """Test the agentic chunker"""
    print("🧪 Testing Agentic Chunker\n")
    
    test_content = """# Machine Learning Basics

## Introduction

Machine learning is a subset of artificial intelligence. It focuses on building systems that learn from data.

There are three main types:
- Supervised learning
- Unsupervised learning
- Reinforcement learning

## Code Example

Here's a simple example:

```python
import numpy as np
from sklearn.linear_model import LinearRegression

# Create model
model = LinearRegression()
model.fit(X_train, y_train)
```

## Applications

Machine learning is used in:
1. Image recognition
2. Natural language processing
3. Recommendation systems

Each application has unique challenges and requirements.

## Conclusion

This is just the beginning of your ML journey!
"""
    
    chunker = AgenticChunker()
    
    metadata = {
        'title': 'ML Basics',
        'file_name': 'ml_basics.md'
    }
    
    print("📄 Input content length:", len(test_content))
    print("\n🔄 Chunking...")
    
    chunks = chunker.chunk_markdown(test_content, metadata)
    
    print(f"\n✅ Created {len(chunks)} chunks:\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}:")
        print(f"  Length: {len(chunk.text)} chars")
        print(f"  Units: {len(chunk.semantic_units)}")
        print(f"  Types: {chunk.metadata.get('unit_types', [])}")
        print(f"  Sections: {chunk.metadata.get('sections', [])}")
        print(f"  Preview: {chunk.text[:100]}...")
        print()


if __name__ == '__main__':
    test_agentic_chunker()

