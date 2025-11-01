"""
Entity/Concept Extractor: Extract subjects, entities, and concepts from documents

Uses:
- Regex patterns for common entities (acronyms, proper nouns)
- Frequency analysis for important terms
- Optional: LLM-based concept extraction for deep semantic understanding

This enables knowledge graph to connect documents by shared subjects/concepts,
not just explicit wikilinks.
"""

import re
import requests
from typing import List, Dict, Set, Tuple
from collections import Counter
from pathlib import Path

import config


class EntityExtractor:
    """Extract entities and concepts from text"""

    def __init__(self, use_llm: bool = False, llm_model: str = None):
        """
        Initialize entity extractor

        Args:
            use_llm: Use LLM for concept extraction (slow but thorough)
            llm_model: LLM model for extraction (default: llama3.2:3b)
        """
        self.use_llm = use_llm
        self.llm_model = llm_model or config.CHAT_MODEL

        # Common stop words to exclude
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'from', 'by', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'it',
            'its', 'their', 'there', 'here', 'when', 'where', 'who', 'what', 'which',
            'how', 'why', 'if', 'then', 'than', 'so', 'not', 'no', 'yes', 'more',
            'most', 'very', 'much', 'many', 'some', 'any', 'all', 'both', 'each',
            'other', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'once', 'also', 'just', 'now'
        }

        # Patterns for entity recognition
        self.acronym_pattern = re.compile(r'\b[A-Z]{2,}\b')  # RAG, LLM, API
        self.proper_noun_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')  # John Smith
        self.technical_term_pattern = re.compile(r'\b[a-z]+(?:[A-Z][a-z]*)+\b')  # camelCase, PascalCase
        self.code_identifier_pattern = re.compile(r'\b[a-z_]+(?:_[a-z]+)+\b')  # snake_case

    def extract_entities(self, text: str, title: str = "") -> Dict[str, List[str]]:
        """
        Extract entities and concepts from text

        Args:
            text: Document text
            title: Document title (gets highest priority)

        Returns:
            Dict with entity types:
            {
                'acronyms': ['RAG', 'LLM', 'API'],
                'proper_nouns': ['John Smith', 'OpenAI'],
                'technical_terms': ['camelCase', 'embeddings'],
                'key_concepts': ['machine learning', 'neural networks'],
                'subjects': ['artificial intelligence', 'programming']
            }
        """
        entities = {
            'acronyms': [],
            'proper_nouns': [],
            'technical_terms': [],
            'key_concepts': [],
            'subjects': []
        }

        # 1. Extract acronyms (RAG, LLM, API, etc.)
        acronyms = self.acronym_pattern.findall(text)
        entities['acronyms'] = list(set(acr for acr in acronyms if len(acr) >= 2))[:20]

        # 2. Extract proper nouns (names, products, etc.)
        proper_nouns = self.proper_noun_pattern.findall(text)
        entities['proper_nouns'] = list(set(proper_nouns))[:20]

        # 3. Extract technical terms (camelCase, PascalCase)
        technical_terms = self.technical_term_pattern.findall(text)
        entities['technical_terms'] = list(set(technical_terms))[:20]

        # 4. Extract key concepts via frequency analysis
        key_concepts = self._extract_key_concepts(text, title)
        entities['key_concepts'] = key_concepts[:15]

        # 5. Extract subjects (multi-word important phrases)
        subjects = self._extract_subjects(text)
        entities['subjects'] = subjects[:10]

        # 6. Optional: LLM-based concept extraction
        if self.use_llm:
            try:
                llm_concepts = self._llm_extract_concepts(text, title)
                # Merge with existing concepts
                entities['subjects'].extend(llm_concepts)
                entities['subjects'] = list(set(entities['subjects']))[:15]
            except Exception as e:
                print(f"⚠️  LLM concept extraction failed: {e}")

        return entities

    def _extract_key_concepts(self, text: str, title: str) -> List[str]:
        """Extract key concepts using frequency analysis"""
        # Tokenize (simple word extraction)
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        # Filter stop words
        words = [w for w in words if w not in self.stop_words and len(w) >= 3]

        # Count frequencies
        word_freq = Counter(words)

        # Title words get bonus weight
        if title:
            title_words = re.findall(r'\b[a-z]{3,}\b', title.lower())
            for word in title_words:
                if word not in self.stop_words:
                    word_freq[word] += 10  # Boost title words

        # Get top concepts
        top_concepts = [word for word, count in word_freq.most_common(20) if count >= 2]

        return top_concepts

    def _extract_subjects(self, text: str) -> List[str]:
        """Extract multi-word subjects (bigrams, trigrams)"""
        # Extract potential subjects (2-3 word phrases)
        # Pattern: adjective/noun + noun or noun + noun
        subject_pattern = re.compile(
            r'\b(?:[a-z]+\s+){1,2}(?:learning|intelligence|engineering|processing|'
            r'generation|retrieval|embedding|search|model|network|system|algorithm|'
            r'optimization|training|architecture|framework|pipeline|service|database|'
            r'graph|index|vector|query|document|chunk|parser|tokenizer)\b',
            re.IGNORECASE
        )

        subjects = subject_pattern.findall(text)

        # Count and filter
        subject_freq = Counter(s.lower().strip() for s in subjects)
        top_subjects = [subj for subj, count in subject_freq.most_common(15) if count >= 2]

        return top_subjects

    def _llm_extract_concepts(self, text: str, title: str, max_chars: int = 2000) -> List[str]:
        """Use LLM to extract main concepts and subjects"""
        # Truncate text for LLM
        sample = text[:max_chars] if len(text) > max_chars else text

        prompt = f"""Extract the main subjects and concepts from this document.
List ONLY the key topics, technologies, or concepts discussed.

Document: {title}
Content: {sample}

Return a comma-separated list of 5-10 key concepts/subjects.
Example: "machine learning, neural networks, backpropagation, gradient descent"

Concepts:"""

        try:
            response = requests.post(
                f"{config.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 100
                    }
                },
                timeout=30
            )
            response.raise_for_status()

            result = response.json()['response'].strip()

            # Parse concepts
            concepts = [c.strip().lower() for c in result.split(',')]
            concepts = [c for c in concepts if c and len(c) > 3]

            return concepts[:10]

        except Exception as e:
            print(f"   LLM extraction failed: {e}")
            return []


def test_entity_extractor():
    """Test the entity extractor"""
    print("🧪 Testing Entity Extractor\n")

    test_text = """
# Retrieval-Augmented Generation (RAG) Systems

## Introduction to RAG

RAG combines large language models (LLMs) with information retrieval.
OpenAI's GPT-4 and Anthropic's Claude use similar architectures.

Key concepts include:
- Vector embeddings using nomic-embed-text
- Semantic search with ChromaDB
- Hybrid search combining BM25 and vector search
- Agentic chunking for intelligent document processing

## Implementation Details

The RAG pipeline uses Python with FastAPI for the REST API.
John Smith's research on neural embeddings informed our approach.

Common acronyms: API, REST, HTTP, JSON, SQL

Technical components:
- embedding_service: Generates vector embeddings
- search_service: Performs hybrid retrieval
- llm_reranker: Re-ranks search results
"""

    extractor = EntityExtractor(use_llm=False)

    print("📄 Input text length:", len(test_text))
    print("\n🔍 Extracting entities...\n")

    entities = extractor.extract_entities(test_text, title="RAG Systems Guide")

    print("✅ Extracted Entities:\n")

    for entity_type, values in entities.items():
        if values:
            print(f"{entity_type.upper()}:")
            for val in values[:10]:
                print(f"  • {val}")
            print()


if __name__ == '__main__':
    test_entity_extractor()

