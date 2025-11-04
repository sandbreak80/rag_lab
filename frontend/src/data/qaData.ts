// Comprehensive Q&A Data extracted from project documentation
// Total: 100+ questions across 9 categories

export interface QAItem {
  id: string;
  question: string;
  answer: string;
  category: string;
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  relatedQuestions?: string[];
  codeExample?: string;
  links?: { text: string; url: string }[];
  estimatedReadTime: number; // minutes
}

export const QA_CATEGORIES = [
  { id: 'getting-started', name: 'Getting Started', icon: '🚀' },
  { id: 'rag-fundamentals', name: 'RAG Fundamentals', icon: '📚' },
  { id: 'search-retrieval', name: 'Search & Retrieval', icon: '🔍' },
  { id: 'knowledge-graphs', name: 'Knowledge Graphs', icon: '🕸️' },
  { id: 'performance', name: 'Performance & Optimization', icon: '⚡' },
  { id: 'models-config', name: 'Models & Configuration', icon: '🎛️' },
  { id: 'security', name: 'Security & Enterprise', icon: '🔒' },
  { id: 'troubleshooting', name: 'Troubleshooting', icon: '🔧' },
  { id: 'advanced', name: 'Advanced Topics', icon: '🎓' },
];

export const QA_DATA: QAItem[] = [
  // ============================================================================
  // GETTING STARTED (10 Q&A)
  // ============================================================================
  {
    id: 'gs-1',
    question: 'What is this RAG Lab?',
    answer: 'This is an enterprise-grade educational lab for learning Retrieval-Augmented Generation (RAG) systems. It features 14 microservices, interactive UI with real-time metrics, and comprehensive hands-on exercises. Built for Splunk/Cisco field teams, it demonstrates production-ready RAG architecture with full observability.',
    category: 'getting-started',
    tags: ['overview', 'introduction'],
    difficulty: 'beginner',
    estimatedReadTime: 1,
    relatedQuestions: ['gs-2', 'rag-1'],
  },
  {
    id: 'gs-2',
    question: 'How do I get started?',
    answer: `Getting started is simple:
1. Navigate to the Chat tab
2. Type a question in the input box
3. Click "Ask" or press Enter
4. Watch the system retrieve relevant documents and generate an answer
5. View the waterfall chart to see performance breakdown

For first-time users, try the Quick Start tutorial in the Lab Guide tab.`,
    category: 'getting-started',
    tags: ['tutorial', 'first-steps'],
    difficulty: 'beginner',
    estimatedReadTime: 1,
    relatedQuestions: ['gs-1', 'gs-4'],
  },
  {
    id: 'gs-3',
    question: 'What are the system requirements?',
    answer: `**Minimum Requirements:**
- 8GB RAM (16GB recommended)
- 4 CPU cores
- 10GB free disk space
- Docker & Docker Compose

**Recommended for GPU:**
- 16GB NVIDIA GPU (RTX 4080, A4000, etc.)
- CUDA 11.8+
- nvidia-container-toolkit

**Supported OS:**
- macOS (M1/M2/M3 or Intel)
- Linux (Ubuntu 20.04+)
- Windows (WSL2)`,
    category: 'getting-started',
    tags: ['requirements', 'setup'],
    difficulty: 'beginner',
    estimatedReadTime: 1,
  },
  {
    id: 'gs-4',
    question: 'How do I upload documents?',
    answer: `To upload documents:
1. Go to the **Documents** tab
2. Click the upload area or drag-and-drop files
3. Supported formats: PDF, Word, Excel, PowerPoint, Text, Markdown
4. Max file size: 50MB per file
5. Wait for processing (shows progress bar)
6. Documents are automatically chunked, embedded, and indexed

**Tip:** Upload technical documentation, research papers, or your own notes for best results.`,
    category: 'getting-started',
    tags: ['documents', 'upload', 'ingestion'],
    difficulty: 'beginner',
    estimatedReadTime: 1,
    relatedQuestions: ['rag-5', 'rag-6'],
  },
  {
    id: 'gs-5',
    question: 'How do I ask questions?',
    answer: `Asking questions is simple:
1. Type your question in natural language
2. Be specific for better results
3. Use complete sentences
4. Ask one question at a time

**Good Questions:**
- "What is vector search and how does it work?"
- "Explain the difference between BM25 and semantic search"
- "How do I optimize RAG performance?"

**Less Effective:**
- "search" (too vague)
- "tell me everything" (too broad)`,
    category: 'getting-started',
    tags: ['queries', 'questions'],
    difficulty: 'beginner',
    estimatedReadTime: 1,
  },
  {
    id: 'gs-6',
    question: 'Where can I see metrics?',
    answer: `Metrics are available in multiple places:

**1. Inline Metrics (Chat Tab):**
- Appears after each response
- Shows waterfall chart with component breakdown
- Click "Performance Breakdown" to expand

**2. Metrics Tab:**
- Full query history
- Detailed performance analysis
- Export to CSV
- Filter by date/config

**3. Prompt Logs Tab:**
- All queries logged
- Security analysis
- Export to Splunk format

**4. Settings Tab:**
- Real-time system stats
- Model information
- Configuration impact estimates`,
    category: 'getting-started',
    tags: ['metrics', 'monitoring', 'performance'],
    difficulty: 'beginner',
    estimatedReadTime: 2,
    relatedQuestions: ['perf-1', 'perf-2'],
  },
  {
    id: 'gs-7',
    question: 'How do I export data?',
    answer: `You can export data in multiple formats:

**Metrics Export (Metrics Tab):**
- Click "Export to CSV"
- Includes all query history, latency, configs
- Open in Excel or Google Sheets

**Prompt Logs Export (Prompt Logs Tab):**
- Click "Export to Splunk"
- JSON format compatible with Splunk
- Includes queries, configs, performance, security flags

**Documents:**
- Currently no bulk export
- View individual documents in Documents tab`,
    category: 'getting-started',
    tags: ['export', 'data', 'splunk'],
    difficulty: 'beginner',
    estimatedReadTime: 1,
  },
  {
    id: 'gs-8',
    question: 'How do I reset the system?',
    answer: `To reset different parts of the system:

**Reset Knowledge Graph:**
1. Go to Documents tab
2. Click "Reset KG" button
3. Confirm deletion
4. Rebuild with desired algorithm

**Reset All Documents:**
1. Stop Docker containers
2. Delete \`/data/chromadb\` volume
3. Restart containers
4. Re-upload documents

**Reset Configuration:**
1. Go to Settings tab
2. Click "Reset to Defaults" button
3. Or load the "Minimal" preset

**Full System Reset:**
\`\`\`bash
docker compose down -v  # Removes all data
docker compose up -d    # Fresh start
\`\`\``,
    category: 'getting-started',
    tags: ['reset', 'cleanup'],
    difficulty: 'beginner',
    estimatedReadTime: 2,
    codeExample: 'docker compose down -v && docker compose up -d',
  },
  {
    id: 'gs-9',
    question: 'What is the difference between tabs?',
    answer: `**Chat Tab:** Ask questions and get AI-generated answers with sources

**Documents Tab:** Upload files, view ingested documents, manage knowledge graph

**Settings Tab:** Configure RAG features, select models, adjust parameters

**Metrics Tab:** View query history, performance analysis, export data

**Prompt Logs Tab:** Security analysis, query logging, Splunk export

**Lab Guide Tab:** Interactive learning tutorials and exercises

**Q&A Tab:** Searchable knowledge base of common questions

**Feedback Tab:** Submit feedback and feature requests`,
    category: 'getting-started',
    tags: ['ui', 'navigation'],
    difficulty: 'beginner',
    estimatedReadTime: 1,
  },
  {
    id: 'gs-10',
    question: 'Where can I get help?',
    answer: `Multiple resources available:

**In-App:**
- Q&A Tab: Searchable knowledge base
- Lab Guide: Interactive tutorials
- Tooltips: Hover over features for explanations

**Documentation:**
- README.md: Quick start guide
- docs/QUICK_START.md: Detailed setup
- docs/PROJECT_COMPLETE.md: Full feature list
- docs/ARCHITECTURE.md: Technical deep dive

**Troubleshooting:**
- Check Troubleshooting section in Q&A
- View logs: \`docker compose logs -f\`
- Check service health: \`docker compose ps\`

**Community:**
- GitHub Issues: Report bugs or request features
- GitHub Discussions: Ask questions`,
    category: 'getting-started',
    tags: ['help', 'support', 'documentation'],
    difficulty: 'beginner',
    estimatedReadTime: 2,
  },

  // ============================================================================
  // RAG FUNDAMENTALS (15 Q&A)
  // ============================================================================
  {
    id: 'rag-1',
    question: 'What is RAG (Retrieval-Augmented Generation)?',
    answer: `RAG combines information retrieval with LLM generation to create accurate, grounded responses.

**The Problem:**
LLMs have limitations:
- Knowledge cutoff (training data is frozen)
- Hallucination (generate plausible but incorrect info)
- No personal context (doesn't know your documents)

**The Solution:**
RAG adds three steps:
1. **Retrieve:** Find relevant documents from your knowledge base
2. **Augment:** Add found context to the LLM prompt
3. **Generate:** LLM generates answer using your specific context

**Example:**
Without RAG: "I don't have information about your API redesign"
With RAG: "Based on your meeting notes from Jan 15, you decided to use REST over GraphQL..."`,
    category: 'rag-fundamentals',
    tags: ['rag', 'basics', 'overview'],
    difficulty: 'beginner',
    estimatedReadTime: 2,
    relatedQuestions: ['rag-2', 'rag-3'],
  },
  {
    id: 'rag-2',
    question: 'How does RAG work?',
    answer: `RAG works in two phases:

**Phase 1: Indexing (One-Time Setup)**
1. Parse documents (extract text, metadata)
2. Chunk into smaller pieces (semantic units)
3. Generate embeddings (convert text to vectors)
4. Store in vector database (ChromaDB)
5. Build indices (vector, BM25, knowledge graph)

**Phase 2: Query Processing (Real-Time)**
1. User asks a question
2. Query expansion (add synonyms)
3. Hybrid search (vector + BM25)
4. Knowledge graph enhancement (find related docs)
5. Context assembly (top results)
6. LLM generation (answer with context)
7. Stream to user

**Total Time:** ~1-2 seconds for balanced config`,
    category: 'rag-fundamentals',
    tags: ['rag', 'workflow', 'pipeline'],
    difficulty: 'intermediate',
    estimatedReadTime: 3,
    relatedQuestions: ['rag-1', 'rag-5', 'rag-6'],
  },
  {
    id: 'rag-3',
    question: 'RAG vs Fine-Tuning: When to use each?',
    answer: `**RAG (Retrieval-Augmented Generation)**
✅ Add knowledge without retraining
✅ Update instantly (just add documents)
✅ Cost-effective ($0 with local models)
✅ Transparent (see sources)
✅ Works with any amount of data
❌ Requires good retrieval
❌ Limited by context window

**Fine-Tuning**
✅ Change model behavior/style
✅ Learn domain-specific patterns
✅ No retrieval needed
❌ Expensive (requires retraining)
❌ Slow to update (days/weeks)
❌ Needs thousands of examples
❌ Can still hallucinate

**Use RAG for:** Knowledge augmentation, Q&A systems, document search
**Use Fine-Tuning for:** Style/tone changes, domain adaptation, specific tasks`,
    category: 'rag-fundamentals',
    tags: ['rag', 'fine-tuning', 'comparison'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
  },
  {
    id: 'rag-4',
    question: 'What are embeddings?',
    answer: `Embeddings convert text into numerical vectors that capture semantic meaning.

**How It Works:**
\`\`\`
Text: "Machine learning is awesome"
Embedding: [0.123, -0.456, 0.789, ..., 0.234]  (768 dimensions)
\`\`\`

**Why Useful:**
Similar texts have similar vectors:
- "ML is awesome" → 0.92 similarity (high)
- "Pizza is delicious" → 0.15 similarity (low)

**This Lab Uses:**
- Model: nomic-embed-text
- Dimensions: 768
- Context: 8192 tokens
- Speed: ~25ms per chunk

**Key Insight:** Embeddings enable semantic search - finding documents by meaning, not just keywords.`,
    category: 'rag-fundamentals',
    tags: ['embeddings', 'vectors', 'semantic'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-1', 'search-2'],
    codeExample: `// Generate embedding
const embedding = await ollama.embeddings({
  model: "nomic-embed-text",
  prompt: "Machine learning is awesome"
});
// Returns: [0.123, -0.456, ..., 0.234]`,
  },
  {
    id: 'rag-5',
    question: 'What is chunking and why is it important?',
    answer: `Chunking breaks documents into smaller pieces for embedding and retrieval.

**Why Chunk:**
- LLM context windows are limited (8K-128K tokens)
- Better granularity = more precise retrieval
- Smaller chunks = faster search

**Two Approaches:**

**1. Fixed-Size Chunking (Simple)**
- Split every N characters
- Add overlap for context
- Fast but breaks mid-sentence

**2. Agentic Chunking (This Lab)**
- Analyzes document structure
- Respects boundaries (headings, code blocks)
- Preserves semantic coherence
- +15% recall improvement

**Example:**
Document → [Chunk 1: Introduction], [Chunk 2: Methods], [Chunk 3: Results]

Each chunk gets its own embedding for precise retrieval.`,
    category: 'rag-fundamentals',
    tags: ['chunking', 'preprocessing'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['rag-4', 'rag-6', 'adv-1'],
  },
  {
    id: 'rag-6',
    question: 'What is a vector database?',
    answer: `A vector database stores and searches embeddings efficiently.

**What It Does:**
- Stores high-dimensional vectors (embeddings)
- Enables fast similarity search
- Scales to millions of vectors

**This Lab Uses ChromaDB:**
- Algorithm: HNSW (Hierarchical Navigable Small World)
- Complexity: O(log N) search time
- Recall: 95%+ at top-10
- Memory: ~300KB per 1000 vectors

**Why Not Regular Database:**
Traditional databases can't efficiently find "similar" vectors. Vector databases use specialized indices (HNSW, IVF) for fast nearest-neighbor search.

**Alternative:** Pinecone (cloud), Weaviate (complex), Qdrant (faster but harder)`,
    category: 'rag-fundamentals',
    tags: ['vector-database', 'chromadb', 'storage'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['rag-4', 'search-1'],
  },
  {
    id: 'rag-7',
    question: 'How are documents indexed?',
    answer: `Documents go through a 6-step indexing pipeline:

**1. Discovery**
- Walk directory tree
- Find supported files (PDF, Word, Markdown, etc.)

**2. Parsing**
- Extract text content
- Parse metadata (title, tags, dates)
- Identify structure (headings, code, lists)

**3. Chunking**
- Break into semantic units
- Preserve context boundaries
- ~800 characters per chunk

**4. Embedding**
- Generate vectors for each chunk
- Use nomic-embed-text model
- Batch process (10 at a time)

**5. Indexing**
- Store in ChromaDB (vector index)
- Build BM25 index (keyword search)
- Create knowledge graph (relationships)

**6. Persistence**
- Save to disk (/data/chromadb)
- Survives container restarts

**Time:** ~2-5 seconds per document`,
    category: 'rag-fundamentals',
    tags: ['indexing', 'ingestion', 'pipeline'],
    difficulty: 'intermediate',
    estimatedReadTime: 3,
    relatedQuestions: ['rag-5', 'rag-6', 'gs-4'],
  },
  {
    id: 'rag-8',
    question: 'What is semantic search?',
    answer: `Semantic search finds documents by meaning, not just keywords.

**How It Works:**
1. Convert query to embedding (vector)
2. Compare with document embeddings
3. Return most similar (cosine similarity)

**Example:**
Query: "machine learning"
Finds:
✅ "ML is a subset of AI" (synonym)
✅ "Neural networks learn patterns" (related concept)
✅ "SVM classifier" (technical term)

But misses:
❌ "ML-2025-Project" (exact acronym in filename)

**This is why hybrid search (semantic + keyword) is better!**

**Similarity Metric:** Cosine similarity (0.0-1.0)
- 1.0 = identical
- 0.7+ = very similar
- < 0.5 = unrelated`,
    category: 'rag-fundamentals',
    tags: ['semantic-search', 'vector-search'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-1', 'search-3', 'rag-4'],
  },
  {
    id: 'rag-9',
    question: 'What is a context window?',
    answer: `The context window is the maximum amount of text an LLM can process at once.

**Measured in tokens** (roughly 0.75 words per token):
- 4K tokens ≈ 3,000 words ≈ 6 pages
- 8K tokens ≈ 6,000 words ≈ 12 pages
- 32K tokens ≈ 24,000 words ≈ 48 pages
- 128K tokens ≈ 96,000 words ≈ 192 pages

**This Lab's Models:**
- llama3.2:1b → 128K context
- llama3.2:3b → 128K context
- llama3.1:8b → 128K context
- qwen2.5:14b → 32K context

**Trade-off:** Larger context = more GPU memory
- 8B model + 128K context ≈ 10GB GPU
- 14B model + 32K context ≈ 11GB GPU

**For RAG:** Larger context allows more retrieved documents in the prompt.`,
    category: 'rag-fundamentals',
    tags: ['context-window', 'tokens', 'llm'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['models-6', 'models-7'],
  },
  {
    id: 'rag-10',
    question: 'How does LLM generation work in RAG?',
    answer: `LLM generation is the final step in RAG:

**Process:**
1. Assemble context from retrieved documents
2. Build prompt with context + question
3. Send to LLM (Ollama)
4. Stream response to user

**Prompt Template:**
\`\`\`
Context:
[Retrieved Document 1]
[Retrieved Document 2]
...

Question: {user_question}

Answer based on the context provided:
\`\`\`

**This Lab Uses:**
- Model: llama3.1:8b (default)
- Temperature: 0.7 (balanced creativity)
- Streaming: Yes (real-time output)
- Max tokens: 2000

**Key Insight:** The LLM doesn't "know" your documents. It only sees what's in the prompt (retrieved context).`,
    category: 'rag-fundamentals',
    tags: ['llm', 'generation', 'prompts'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['rag-1', 'rag-2', 'models-1'],
    codeExample: `const prompt = \`Context: \${retrievedDocs}

Question: \${userQuestion}

Answer based only on the context:\`;

const response = await ollama.generate({
  model: "llama3.1:8b",
  prompt,
  stream: true
});`,
  },
  {
    id: 'rag-11',
    question: 'What is prompt engineering?',
    answer: `Prompt engineering is designing effective instructions for LLMs.

**Key Principles:**
1. **Be Specific:** Clear, detailed instructions
2. **Provide Context:** Give relevant background
3. **Set Format:** Specify output structure
4. **Give Examples:** Show desired behavior
5. **Constrain Output:** Limit hallucination

**Example - Bad Prompt:**
"Tell me about AI"

**Example - Good Prompt:**
"Based on the provided documents, explain the three main types of machine learning (supervised, unsupervised, reinforcement) with one example each. Use simple language suitable for beginners."

**This Lab's Prompt:**
- Provides retrieved context
- Asks specific question
- Instructs to cite sources
- Requests comprehensive answers
- Encourages educational tone`,
    category: 'rag-fundamentals',
    tags: ['prompts', 'prompt-engineering'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
  },
  {
    id: 'rag-12',
    question: 'What is hallucination and how does RAG prevent it?',
    answer: `**Hallucination:** When an LLM generates plausible but incorrect information.

**Examples:**
- Inventing fake citations
- Making up statistics
- Fabricating events that never happened
- Confidently stating wrong facts

**How RAG Prevents Hallucination:**

1. **Grounding:** Provides actual documents as context
2. **Source Attribution:** Shows which documents were used
3. **Prompt Instructions:** "Answer based ONLY on provided context"
4. **Verification:** Users can check sources
5. **Transparency:** Full citation trail

**Not 100% Foolproof:**
- LLM can still misinterpret context
- Can combine facts incorrectly
- May ignore "only use context" instruction

**Best Practice:** Always verify critical information by checking sources.`,
    category: 'rag-fundamentals',
    tags: ['hallucination', 'grounding', 'accuracy'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['rag-1', 'rag-10', 'rag-13'],
  },
  {
    id: 'rag-13',
    question: 'What is grounding in RAG?',
    answer: `Grounding means tying LLM outputs to actual source documents.

**Ungrounded Response:**
"Machine learning was invented in 1950 by Alan Turing."
(May be incorrect, no source)

**Grounded Response:**
"According to 'ML-History.md', machine learning emerged in the 1950s with early work by Arthur Samuel on checkers-playing programs."
(Cites source, verifiable)

**How This Lab Grounds Responses:**
1. Retrieves relevant documents
2. Includes them in LLM prompt
3. Instructs LLM to cite sources
4. Shows sources in UI
5. Allows users to verify

**Benefits:**
- Reduces hallucination
- Increases trust
- Enables verification
- Provides transparency`,
    category: 'rag-fundamentals',
    tags: ['grounding', 'sources', 'citations'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['rag-12', 'rag-1'],
  },
  {
    id: 'rag-14',
    question: 'What is the difference between training, fine-tuning, and RAG?',
    answer: `**Training (From Scratch):**
- Build a new model from random weights
- Requires massive datasets (billions of tokens)
- Takes weeks/months on supercomputers
- Cost: Millions of dollars
- Use: Creating foundation models (GPT, Llama)

**Fine-Tuning:**
- Adjust existing model for specific task/domain
- Requires thousands of examples
- Takes hours/days on GPUs
- Cost: Hundreds to thousands of dollars
- Use: Adapt model behavior, style, domain

**RAG (Retrieval-Augmented Generation):**
- Use existing model + add retrieval
- No training required
- Works with any amount of data
- Takes minutes to set up
- Cost: Free (with local models)
- Use: Add knowledge, Q&A systems

**This Lab:** Uses RAG with pre-trained Llama models. No training or fine-tuning needed!`,
    category: 'rag-fundamentals',
    tags: ['training', 'fine-tuning', 'rag', 'comparison'],
    difficulty: 'intermediate',
    estimatedReadTime: 3,
  },
  {
    id: 'rag-15',
    question: 'What are the limitations of RAG?',
    answer: `RAG is powerful but has limitations:

**1. Retrieval Quality**
- Only as good as your search
- Can miss relevant documents
- Sensitive to query phrasing

**2. Context Window**
- Limited by LLM's context size
- Can't include all documents
- Must choose top-K results

**3. Latency**
- Adds retrieval time (~50-200ms)
- Slower than pure LLM
- Advanced features add more latency

**4. Document Quality**
- Garbage in, garbage out
- Poorly written docs → poor answers
- Outdated docs → outdated answers

**5. Multi-Hop Reasoning**
- Struggles with complex queries
- May need multiple retrievals
- Knowledge graphs help but aren't perfect

**6. Cost (If Using APIs)**
- Embedding costs
- Vector DB costs
- LLM API costs

**Mitigation:** This lab addresses many limitations with hybrid search, knowledge graphs, and local models.`,
    category: 'rag-fundamentals',
    tags: ['limitations', 'trade-offs'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
  },

  // ============================================================================
  // SEARCH & RETRIEVAL (12 Q&A)
  // ============================================================================
  {
    id: 'search-1',
    question: 'What is vector search?',
    answer: `Vector search finds documents by semantic similarity using embeddings.

**How It Works:**
1. Convert query to vector (embedding)
2. Compare with all document vectors
3. Return most similar (cosine similarity)
4. Rank by similarity score

**Strengths:**
✅ Understands meaning and context
✅ Finds synonyms ("ML" → "machine learning")
✅ Discovers related concepts
✅ Language-agnostic (works across languages)

**Weaknesses:**
❌ May miss exact keyword matches
❌ Slower than keyword search
❌ Requires embeddings (storage cost)
❌ Less transparent (why this result?)

**This Lab:**
- Uses ChromaDB with HNSW index
- nomic-embed-text embeddings (768-dim)
- ~35ms average search time
- 95%+ recall at top-10`,
    category: 'search-retrieval',
    tags: ['vector-search', 'semantic-search', 'embeddings'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-2', 'search-3', 'rag-4', 'rag-8'],
  },
  {
    id: 'search-2',
    question: 'What is BM25?',
    answer: `BM25 is a probabilistic ranking function for keyword search.

**Formula Components:**
1. **IDF (Inverse Document Frequency):** Rare words matter more
2. **TF (Term Frequency):** How often word appears in doc
3. **Length Normalization:** Penalize long documents

**Strengths:**
✅ Fast (no embeddings needed)
✅ Transparent (see why it matched)
✅ Great for exact matches
✅ Handles rare terms well

**Weaknesses:**
❌ Doesn't understand synonyms
❌ Misses semantic relationships
❌ Keyword-dependent

**Example:**
Query: "neural network"
- Finds: "neural network", "neural_network.py"
- Misses: "deep learning", "AI models"

**This Lab:**
- Uses rank-bm25 library
- ~15ms average search time
- Complements vector search in hybrid mode`,
    category: 'search-retrieval',
    tags: ['bm25', 'keyword-search', 'ranking'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-1', 'search-3', 'search-4'],
    codeExample: `# BM25 scoring
score = IDF(term) × TF(term, doc) × (k1 + 1) / 
        (TF(term, doc) + k1 × (1 - b + b × doc_len/avg_len))`,
  },
  {
    id: 'search-3',
    question: 'What is hybrid search?',
    answer: `Hybrid search combines vector search (semantic) and BM25 (keyword) for best results.

**Why Hybrid:**
- Vector: Finds semantic matches
- BM25: Finds exact matches
- Together: Best of both worlds!

**How It Works:**
1. Run vector search → Top 20 results
2. Run BM25 search → Top 20 results
3. Merge with RRF (Reciprocal Rank Fusion)
4. Return top 10 combined results

**Performance:**
- +20% recall vs vector-only
- +15% recall vs BM25-only
- ~50ms total (both searches run in parallel)

**Example:**
Query: "machine learning"
- Vector finds: "ML basics", "neural networks"
- BM25 finds: "machine_learning.py", "ML-2025-Project"
- Hybrid finds: ALL of the above!

**This Lab:** Hybrid is the default and recommended for most use cases.`,
    category: 'search-retrieval',
    tags: ['hybrid-search', 'rrf', 'fusion'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-1', 'search-2', 'search-4'],
  },
  {
    id: 'search-4',
    question: 'What is Reciprocal Rank Fusion (RRF)?',
    answer: `RRF is an algorithm for merging results from multiple search methods.

**The Problem:**
How to combine vector scores (0.0-1.0) with BM25 scores (0.0-∞)?
They're on different scales!

**RRF Solution:**
Use rank position instead of scores:

\`\`\`python
def rrf_score(rank, k=60):
    return 1.0 / (k + rank)

# Example
doc1: rank 1 in vector, rank 3 in BM25
score = 1/(60+1) + 1/(60+3) = 0.0323

doc2: rank 2 in vector, rank 1 in BM25
score = 1/(60+2) + 1/(60+1) = 0.0325

# doc2 wins (high in both)
\`\`\`

**Why RRF:**
✅ No parameter tuning
✅ Scale-invariant
✅ Empirically proven effective
✅ Fast to compute

**Alternative:** Weighted average (requires tuning)`,
    category: 'search-retrieval',
    tags: ['rrf', 'fusion', 'ranking'],
    difficulty: 'advanced',
    estimatedReadTime: 2,
    relatedQuestions: ['search-3'],
    codeExample: `function rrfScore(rank: number, k = 60): number {
  return 1.0 / (k + rank);
}

// Combine scores from multiple searches
const combinedScore = 
  rrfScore(vectorRank) + 
  rrfScore(bm25Rank) + 
  rrfScore(graphRank);`,
  },
  {
    id: 'search-5',
    question: 'How do I improve recall?',
    answer: `Recall = (Relevant docs found) / (Total relevant docs)

**Strategies to Improve Recall:**

**1. Enable Hybrid Search** (+20% recall)
- Combines vector + BM25
- Catches both semantic and exact matches

**2. Enable Query Expansion** (+5% recall)
- Adds synonyms and related terms
- Helps with vocabulary mismatch

**3. Enable Knowledge Graph** (+2-5% recall)
- Finds related documents via relationships
- Good for multi-hop queries

**4. Increase top_k** (retrieve more docs)
- Default: 10 documents
- Try: 15-20 for comprehensive coverage
- Trade-off: More noise, slower

**5. Better Chunking**
- Use agentic chunking (+15% vs fixed)
- Preserve semantic boundaries

**6. Upload More Documents**
- More content = better coverage

**This Lab:** Enable "Quality" or "Production" preset for best recall.`,
    category: 'search-retrieval',
    tags: ['recall', 'optimization', 'quality'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-6', 'perf-8', 'perf-9'],
  },
  {
    id: 'search-6',
    question: 'How do I improve precision?',
    answer: `Precision = (Relevant docs found) / (Total docs returned)

**Strategies to Improve Precision:**

**1. Enable LLM Re-ranking** (+10-15% precision)
- LLM scores each result for relevance
- Re-orders by relevance
- Warning: Adds 2000ms latency!

**2. Better Query Phrasing**
- Be specific
- Use complete sentences
- Include key terms

**3. Reduce top_k** (return fewer docs)
- Default: 10 documents
- Try: 5 for higher precision
- Trade-off: May miss some relevant docs

**4. Use Metadata Filters**
- Filter by document type
- Filter by date range
- Filter by tags/authors

**5. Better Document Quality**
- Well-written, structured docs
- Clear headings and sections
- Relevant metadata

**Trade-off:** Precision vs Recall
- Higher precision → Lower recall
- Balance based on use case`,
    category: 'search-retrieval',
    tags: ['precision', 'optimization', 'quality'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-5', 'search-9', 'perf-8'],
  },
  {
    id: 'search-7',
    question: 'What is query expansion?',
    answer: `Query expansion enhances queries by adding related terms and synonyms.

**How It Works:**
1. Analyze original query
2. Generate related terms/synonyms
3. Search with expanded query
4. Merge and deduplicate results

**Example:**
Original: "RAG"
Expanded: "RAG retrieval augmented generation LLM context document embedding search semantic"

**Why Better:**
- "retrieval" → finds docs without "RAG" acronym
- "augmented generation" → finds conceptual explanations
- "embedding" → finds technical implementation

**Impact:**
- +5-10% recall
- ~10ms latency cost
- Minimal downside

**This Lab:** Query expansion is enabled in Balanced, Quality, and Production presets.`,
    category: 'search-retrieval',
    tags: ['query-expansion', 'optimization'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-5'],
  },
  {
    id: 'search-8',
    question: 'When should I use vector-only vs hybrid search?',
    answer: `**Use Vector-Only When:**
- Speed is critical (< 50ms)
- Queries are conceptual
- Documents are well-written
- Synonyms matter more than exact matches

**Use Hybrid When:**
- Quality matters more than speed
- Need both semantic and exact matches
- Documents have technical terms/acronyms
- General-purpose search (RECOMMENDED)

**Comparison:**

| Aspect | Vector | Hybrid |
|--------|--------|--------|
| Latency | ~35ms | ~50ms |
| Recall | 80% | 95% |
| Precision | 85% | 90% |
| Use Case | Speed-critical | General purpose |

**This Lab Default:** Hybrid (best balance)

**Try It:** Compare "Minimal" (vector-only) vs "Balanced" (hybrid) presets to see the difference!`,
    category: 'search-retrieval',
    tags: ['vector-search', 'hybrid-search', 'comparison'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-1', 'search-3'],
  },
  {
    id: 'search-9',
    question: 'What is re-ranking and when should I use it?',
    answer: `Re-ranking uses an LLM to re-order search results for better precision.

**How It Works:**
1. Get initial results (vector/BM25/hybrid)
2. Send all results + query to LLM
3. LLM scores each result for relevance
4. Re-order by LLM scores
5. Return top-K after reranking

**Impact:**
✅ +10-15% precision
✅ Better handling of complex queries
✅ Reduces noise in results

**Cost:**
❌ +2000ms latency (very expensive!)
❌ High token usage
❌ Doesn't scale to high QPS

**When to Use:**
- Critical queries (legal, medical, research)
- Low query volume (< 10 queries/min)
- Offline analysis
- Quality benchmarking

**When NOT to Use:**
- Real-time applications
- High QPS systems
- Speed-critical use cases

**This Lab:** Disabled by default. Enable in "Maximum" preset for quality comparison.`,
    category: 'search-retrieval',
    tags: ['reranking', 'llm', 'optimization'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['search-6', 'perf-4'],
  },
  {
    id: 'search-10',
    question: 'How many results should I retrieve (top_k)?',
    answer: `top_k determines how many documents to retrieve from search.

**Trade-offs:**

**Low top_k (5):**
✅ Higher precision (less noise)
✅ Faster processing
✅ Fits in smaller context windows
❌ May miss relevant docs (lower recall)

**Medium top_k (10):** ⭐ RECOMMENDED
✅ Good balance
✅ Fits in most context windows
✅ Acceptable recall and precision

**High top_k (20):**
✅ Higher recall (more coverage)
❌ More noise (lower precision)
❌ Larger context needed
❌ Slower processing

**This Lab Defaults:**
- Minimal: 5
- Balanced: 10
- Quality: 15
- Maximum: 20

**Rule of Thumb:** Start with 10, adjust based on:
- Document collection size
- Query complexity
- Context window size
- Speed requirements`,
    category: 'search-retrieval',
    tags: ['top-k', 'configuration', 'optimization'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['search-5', 'search-6'],
  },
  {
    id: 'search-11',
    question: 'What is HNSW and why does it matter?',
    answer: `HNSW (Hierarchical Navigable Small World) is a graph-based algorithm for fast nearest-neighbor search.

**The Problem:**
Brute force vector search is O(N) - compare query to every vector.
Too slow for large datasets!

**HNSW Solution:**
Build a multi-layer graph where:
- Nodes = vectors
- Edges = connect similar vectors
- Layers = different granularities

**Search Process:**
1. Start at top layer (coarse)
2. Find approximate nearest
3. Descend to next layer (finer)
4. Refine search
5. Repeat until bottom layer

**Performance:**
- Build: O(N log N)
- Search: O(log N)
- 100-1000x faster than brute force!
- 95%+ recall at top-10

**This Lab:** ChromaDB uses HNSW by default. You get fast search automatically!`,
    category: 'search-retrieval',
    tags: ['hnsw', 'algorithms', 'performance'],
    difficulty: 'advanced',
    estimatedReadTime: 2,
    relatedQuestions: ['search-1', 'rag-6'],
  },
  {
    id: 'search-12',
    question: 'What is cosine similarity?',
    answer: `Cosine similarity measures the angle between two vectors.

**Formula:**
\`\`\`
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)
\`\`\`

**Range:**
- 1.0 = Identical (same direction)
- 0.7-0.9 = Very similar
- 0.5-0.7 = Somewhat similar
- < 0.5 = Unrelated
- 0.0 = Orthogonal (completely different)

**Example:**
\`\`\`
A = [1, 2, 3]  # "machine learning"
B = [1, 2, 2]  # "ML is great"
C = [0, 0, 1]  # "pizza"

similarity(A, B) = 0.98  # Very similar
similarity(A, C) = 0.71  # Somewhat similar
\`\`\`

**Why Cosine:**
✅ Scale-invariant (magnitude doesn't matter)
✅ Fast to compute
✅ Works well for text embeddings
✅ Intuitive range [0, 1]

**This Lab:** Uses cosine similarity for all vector comparisons.`,
    category: 'search-retrieval',
    tags: ['cosine-similarity', 'similarity', 'algorithms'],
    difficulty: 'advanced',
    estimatedReadTime: 2,
    relatedQuestions: ['search-1', 'rag-4'],
    codeExample: `function cosineSimilarity(a: number[], b: number[]): number {
  const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
  const magA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
  const magB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
  return dotProduct / (magA * magB);
}`,
  },

  // Continue with remaining categories...
  // I'll create a separate file for the remaining 70+ Q&A to keep this manageable
];

// Helper function to get Q&A by category
export function getQAByCategory(categoryId: string): QAItem[] {
  return QA_DATA.filter(qa => qa.category === categoryId);
}

// Helper function to search Q&A
export function searchQA(searchTerm: string): QAItem[] {
  const term = searchTerm.toLowerCase();
  return QA_DATA.filter(qa => 
    qa.question.toLowerCase().includes(term) ||
    qa.answer.toLowerCase().includes(term) ||
    qa.tags.some(tag => tag.toLowerCase().includes(term))
  );
}

// Helper function to get related questions
export function getRelatedQuestions(qaId: string): QAItem[] {
  const qa = QA_DATA.find(q => q.id === qaId);
  if (!qa || !qa.relatedQuestions) return [];
  return QA_DATA.filter(q => qa.relatedQuestions?.includes(q.id));
}

// Get popular questions (most referenced)
export function getPopularQuestions(limit = 10): QAItem[] {
  const referenceCounts = new Map<string, number>();
  
  QA_DATA.forEach(qa => {
    qa.relatedQuestions?.forEach(relatedId => {
      referenceCounts.set(relatedId, (referenceCounts.get(relatedId) || 0) + 1);
    });
  });
  
  return QA_DATA
    .map(qa => ({ qa, count: referenceCounts.get(qa.id) || 0 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit)
    .map(item => item.qa);
}

