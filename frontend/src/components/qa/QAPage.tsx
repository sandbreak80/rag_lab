import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { ChevronDown, ChevronRight } from 'lucide-react';

const QA_DATA = [
  {
    category: 'RAG Systems',
    questions: [
      {
        q: 'What is RAG?',
        a: 'RAG (Retrieval Augmented Generation) combines document retrieval with LLM generation. It searches relevant documents, then uses them as context for the LLM to generate accurate, grounded responses.',
      },
      {
        q: 'Why use RAG instead of fine-tuning?',
        a: 'RAG is faster to set up, more cost-effective, easier to update with new information, and provides transparency through source citations. Fine-tuning is better for style/tone changes.',
      },
      {
        q: 'What is chunking?',
        a: 'Chunking breaks documents into smaller pieces for embedding and retrieval. Good chunking preserves semantic meaning and context boundaries.',
      },
    ],
  },
  {
    category: 'Search Methods',
    questions: [
      {
        q: 'What is vector search?',
        a: 'Vector search uses embeddings to find semantically similar content. It understands meaning and context, not just exact keyword matches.',
      },
      {
        q: 'What is BM25?',
        a: 'BM25 is a keyword-based search algorithm that ranks documents by term frequency and rarity. It\'s fast and works well for exact matches.',
      },
      {
        q: 'What is hybrid search?',
        a: 'Hybrid search combines vector and BM25 results using Reciprocal Rank Fusion, getting the best of both semantic understanding and exact matching.',
      },
    ],
  },
  {
    category: 'Advanced Features',
    questions: [
      {
        q: 'What does query expansion do?',
        a: 'Query expansion adds synonyms and related terms to your query to improve recall, especially for sparse documents or multi-language content.',
      },
      {
        q: 'How does LLM reranking work?',
        a: 'After initial retrieval, an LLM scores each result for relevance to the query and reorders them. This improves precision by 12%.',
      },
      {
        q: 'What is a knowledge graph in RAG?',
        a: 'A knowledge graph connects documents through relationships (tags, entities, links). It helps with multi-hop questions and document discovery.',
      },
    ],
  },
  {
    category: 'This Lab',
    questions: [
      {
        q: 'What can I learn from this lab?',
        a: 'You\'ll learn RAG fundamentals, experiment with different configurations, measure performance impact, and understand trade-offs between features.',
      },
      {
        q: 'How do I see metrics?',
        a: 'Go to the Metrics tab to see query history, latency breakdowns, token usage, and feature impacts. Export to CSV for analysis.',
      },
      {
        q: 'Can I upload my own documents?',
        a: 'Yes! Go to the Documents tab to upload PDF, Word, PowerPoint, Excel, Text, or Markdown files up to 50MB.',
      },
    ],
  },
];

export function QAPage() {
  const [openCategories, setOpenCategories] = useState<Set<string>>(new Set(['RAG Systems']));
  const [openQuestions, setOpenQuestions] = useState<Set<string>>(new Set());

  const toggleCategory = (category: string) => {
    const newSet = new Set(openCategories);
    if (newSet.has(category)) {
      newSet.delete(category);
    } else {
      newSet.add(category);
    }
    setOpenCategories(newSet);
  };

  const toggleQuestion = (key: string) => {
    const newSet = new Set(openQuestions);
    if (newSet.has(key)) {
      newSet.delete(key);
    } else {
      newSet.add(key);
    }
    setOpenQuestions(newSet);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">❓ Frequently Asked Questions</h1>
        <p className="text-muted-foreground">
          Common questions about RAG systems and this educational lab
        </p>
      </div>

      <div className="space-y-4">
        {QA_DATA.map((category) => (
          <Card key={category.category}>
            <button
              onClick={() => toggleCategory(category.category)}
              className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors"
            >
              <h2 className="text-xl font-semibold">{category.category}</h2>
              {openCategories.has(category.category) ? (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              )}
            </button>

            {openCategories.has(category.category) && (
              <CardContent className="pt-0 pb-4 space-y-2">
                {category.questions.map((qa, idx) => {
                  const key = `${category.category}-${idx}`;
                  const isOpen = openQuestions.has(key);

                  return (
                    <div key={key} className="border rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleQuestion(key)}
                        className="w-full p-3 flex items-start justify-between hover:bg-muted/50 transition-colors text-left"
                      >
                        <span className="font-medium pr-4">{qa.q}</span>
                        {isOpen ? (
                          <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-1" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-1" />
                        )}
                      </button>
                      {isOpen && (
                        <div className="px-3 pb-3 text-sm text-muted-foreground">
                          {qa.a}
                        </div>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
