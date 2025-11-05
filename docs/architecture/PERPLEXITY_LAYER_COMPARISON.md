# Perplexity Layer Comparison & Roadmap

## 🎯 Overview

This document compares our RAG Lab implementation with Perplexity AI's "answer engine" architecture and provides a roadmap for building a true "Perplexity Layer" for educational purposes.

---

## 📊 Feature Comparison: RAG Lab v1.2 vs. Perplexity AI

| Feature | **Perplexity AI** | **RAG Lab v1.2** | Status | Priority |
|---------|-------------------|------------------|--------|----------|
| **Query Understanding (LLM)** | ✅ GPT-4, Claude, Gemini, Sonar | ✅ Llama 3.1:8b, Qwen2.5:14b | ✅ **HAVE IT** | - |
| **Multi-Query Decomposition** | ✅ Break complex queries into sub-queries | ✅ 3-5 sub-queries for 30+ word prompts | ✅ **HAVE IT** | - |
| **Hybrid Retrieval** | ✅ Own crawlers + Google/Bing APIs | ✅ SearXNG (9+ engines) | ✅ **HAVE IT** | - |
| **RAG Architecture** | ✅ Retrieval-Augmented Generation | ✅ Vector + BM25 + Hybrid + KG | ✅ **HAVE IT** | - |
| **Quality Domain Boosting** | ✅ Boost .edu, .gov, Wikipedia | ✅ Same (1.3-1.4x boost) | ✅ **HAVE IT** | - |
| **Spam Filtering** | ✅ Filter low-quality results | ✅ Filter spam, ads, short content | ✅ **HAVE IT** | - |
| **Result Deduplication** | ✅ By URL | ✅ By URL | ✅ **HAVE IT** | - |
| **Inline Citations** | ✅ Clickable source links | ✅ Source cards with URLs | ✅ **HAVE IT** | - |
| **Conversational Follow-ups** | ✅ Thread context maintained | ✅ Chat history maintained | ✅ **HAVE IT** | - |
| **Answer Synthesis** | ✅ LLM generates comprehensive answer | ✅ LLM generates detailed answer | ✅ **HAVE IT** | - |
| **Real-time Freshness** | ✅ 10,000s updates/sec | ⚠️ SearXNG (slower, but real-time) | ⚠️ **PARTIAL** | 🔴 Low |
| **Custom Crawlers** | ✅ Own web crawlers | ❌ Rely on SearXNG engines | ❌ **MISSING** | 🟡 Medium |
| **Dynamic Model Selection** | ✅ Auto-pick best model per query | ❌ User selects model | ❌ **MISSING** | 🟢 High |
| **Follow-up Suggestions** | ✅ Generate related questions | ❌ Not implemented | ❌ **MISSING** | 🟢 High |
| **Inline Citation Format** | ✅ `[1]`, `[2]` in text | ⚠️ Source cards only | ⚠️ **PARTIAL** | 🟢 High |
| **Query Intent Classification** | ✅ Factual, opinion, how-to, etc. | ❌ Not implemented | ❌ **MISSING** | 🟡 Medium |
| **Result Summarization** | ✅ LLM summarizes each source | ❌ Raw snippets only | ❌ **MISSING** | 🟡 Medium |
| **API for Developers** | ✅ Perplexity API | ❌ No public API yet | ❌ **MISSING** | 🔴 Low |
| **Educational Transparency** | ❌ Black box | ✅ Full metrics, waterfall charts | ✅ **BETTER!** | ✅ Done |

---

## 🎓 What Makes This Educational?

### **Key Insight:**
Perplexity AI is essentially a **sophisticated RAG system with web search**. By building our own version, students learn:

1. **How "Answer Engines" Work**
   - Not magic - it's RAG + web search + LLM synthesis
   - Query decomposition for complex questions
   - Quality filtering and source ranking

2. **Why Perplexity Feels "Smarter" Than ChatGPT**
   - Real-time web access (not just training data)
   - Multi-query parallel search
   - Inline citations (verifiable answers)
   - Domain authority signals

3. **The Architecture Behind Modern AI Search**
   - Hybrid retrieval (vector + keyword + web)
   - LLM as orchestrator (not just generator)
   - RAG as the core technique

4. **Trade-offs in System Design**
   - Speed vs. accuracy
   - Custom crawlers vs. external APIs
   - Model size vs. quality
   - Cost vs. performance

---

## 🚀 Implementation Roadmap

### **Phase 1: Quick Wins (1-2 hours)** 🟢 HIGH PRIORITY

#### **1.1 Inline Citation Format**
**Current:** Source cards at bottom
**Target:** Perplexity-style `[1]`, `[2]` inline citations

```python
# services/chat/app/service.py

def format_answer_with_inline_citations(answer, sources):
    """
    Transform answer to include inline citations like Perplexity

    Example:
    "RAG stands for Retrieval-Augmented Generation [1]. It combines
    vector search [2] with LLM generation [3]."
    """
    # Use LLM to insert citations
    citation_prompt = f"""Add inline citations to this answer using [1], [2], [3] format.

ANSWER:
{answer}

SOURCES:
{format_sources_for_citation(sources)}

Return the answer with [N] citations inserted after each fact. Be precise."""

    return llm_generate(citation_prompt)
```

**UI Changes:**
- Display citations as superscript numbers
- Click citation → scroll to source card
- Hover citation → show source preview

#### **1.2 Follow-up Question Suggestions**
**Current:** User must think of next question
**Target:** Generate 3-5 related questions automatically

```python
# services/chat/app/service.py

def generate_follow_up_questions(query, answer, sources):
    """
    Generate 3-5 related questions based on the conversation

    Example:
    Q: "What is RAG?"
    A: "RAG stands for..."

    Follow-ups:
    1. "How does vector search work in RAG?"
    2. "What are the limitations of RAG systems?"
    3. "How does RAG compare to fine-tuning?"
    """
    follow_up_prompt = f"""Generate 3-5 follow-up questions a curious student might ask.

ORIGINAL QUESTION: {query}
ANSWER PROVIDED: {answer[:500]}

Rules:
1. Each question should explore a related concept
2. Progress from basic to advanced
3. Be specific and actionable
4. No yes/no questions

FOLLOW-UP QUESTIONS:"""

    questions = llm_generate(follow_up_prompt)
    return parse_questions(questions)
```

**UI Changes:**
- Display follow-ups below answer
- Click to ask automatically
- Track which follow-ups are popular (analytics)

#### **1.3 Dynamic Model Selection**
**Current:** User manually selects model
**Target:** Auto-pick best model based on query type

```python
# services/chat/app/service.py

def classify_query_intent(query):
    """
    Classify query to select best model

    Categories:
    - coding: Code examples, debugging, algorithms
    - math: Calculations, proofs, equations
    - creative: Stories, poems, brainstorming
    - factual: Definitions, explanations, how-to
    - research: Complex multi-topic questions
    """
    # Use lightweight model for classification
    classification_prompt = f"""Classify this query into ONE category:

CATEGORIES:
- coding: Programming, algorithms, debugging
- math: Calculations, equations, proofs
- creative: Writing, brainstorming, stories
- factual: Definitions, explanations
- research: Complex multi-topic analysis

QUERY: {query}

CATEGORY:"""

    category = llm_generate(classification_prompt, model="llama3.2:1b")
    return category.strip().lower()

def select_best_model(intent):
    """Select optimal model for query type"""
    model_map = {
        'coding': 'qwen2.5:14b',      # Best for code
        'math': 'llama3.1:8b',         # Best for reasoning
        'creative': 'gemma2:9b',       # Best for creative writing
        'factual': 'llama3.1:8b',      # Balanced
        'research': 'qwen2.5:14b',     # Best for complex analysis
    }
    return model_map.get(intent, 'llama3.1:8b')
```

**UI Changes:**
- Show "Using [Model] for [Intent]" badge
- Explain why model was chosen (educational!)
- Allow override if user wants

---

### **Phase 2: Medium Effort (3-5 hours)** 🟡 MEDIUM PRIORITY

#### **2.1 Query Intent Classification UI**
- Display detected intent badge
- Show confidence score
- Explain model selection reasoning

#### **2.2 Result Summarization**
- LLM summarizes each web result (1-2 sentences)
- Show summary in source card
- "Read full article" link

#### **2.3 Answer Quality Scoring**
- Rate answer quality (1-5 stars)
- Track which configurations produce best answers
- A/B test different prompts

---

### **Phase 3: Major Effort (1-2 days)** 🔴 LOW PRIORITY

#### **3.1 Custom Crawler Integration**
- Direct Google/Bing API integration
- Custom crawler for specific domains
- Real-time freshness (streaming updates)

#### **3.2 Public API**
- Authentication (API keys)
- Rate limiting
- Usage analytics
- Billing (optional)

#### **3.3 Advanced Features**
- Multi-modal search (images, videos)
- Voice input/output
- Collaborative research (teams)

---

## 📚 Educational Value

### **What Students Learn:**

#### **1. System Architecture**
```
User Query
    ↓
Query Understanding (LLM)
    ↓
Intent Classification → Model Selection
    ↓
Multi-Query Decomposition (if complex)
    ↓
Parallel Search (RAG + Web)
    ↓
Quality Filtering & Ranking
    ↓
Answer Synthesis (LLM)
    ↓
Citation Insertion
    ↓
Follow-up Generation
    ↓
Response to User
```

#### **2. Key Concepts**
- **Answer Engines vs. Search Engines:** Synthesis vs. links
- **RAG as Foundation:** All modern AI search uses RAG
- **LLM Orchestration:** LLM as coordinator, not just generator
- **Quality Signals:** Domain authority, freshness, citations
- **User Experience:** Conversational, iterative, transparent

#### **3. Real-World Applications**
- Customer support chatbots
- Research assistants
- Legal document analysis
- Medical literature review
- Code documentation search

---

## 🧪 Lab Exercises

### **Exercise 1: Compare Search Strategies**
**Goal:** Understand when to use different approaches

**Tasks:**
1. Ask same question with:
   - Web search OFF (RAG only)
   - Web search ON (single query)
   - Web search ON (multi-query)
2. Compare results, latency, quality
3. Document trade-offs

**Questions:**
- When is RAG-only sufficient?
- When do you need web search?
- When is multi-query worth the latency?

### **Exercise 2: Model Selection Impact**
**Goal:** Understand model specialization

**Tasks:**
1. Ask coding question → observe model selection
2. Ask creative question → observe model selection
3. Ask math question → observe model selection
4. Override model choice, compare results

**Questions:**
- How much does model choice matter?
- Can smaller models handle simple queries?
- When is the largest model necessary?

### **Exercise 3: Citation Quality**
**Goal:** Understand source verification

**Tasks:**
1. Ask factual question
2. Verify each citation
3. Rate source quality (1-5)
4. Identify any hallucinations

**Questions:**
- Are citations accurate?
- Do sources support claims?
- How to detect hallucinations?

---

## 🎯 Success Metrics

### **User Experience:**
- ✅ Answer quality (user ratings)
- ✅ Citation accuracy (% correct)
- ✅ Follow-up relevance (click rate)
- ✅ Response time (< 5s for simple, < 10s for complex)

### **System Performance:**
- ✅ Web search success rate (> 95%)
- ✅ Model selection accuracy (> 90%)
- ✅ Multi-query deduplication (< 10% duplicates)
- ✅ Quality filtering effectiveness (spam rate < 5%)

### **Educational Impact:**
- ✅ Student understanding (quiz scores)
- ✅ Engagement (time spent in lab)
- ✅ Completion rate (% finish exercises)
- ✅ Feedback quality (detailed responses)

---

## 🔮 Future Vision

### **The Ultimate "Perplexity Layer":**

1. **Real-time Knowledge Base**
   - Custom crawlers for AI news, papers, blogs
   - Automatic ingestion and indexing
   - Freshness guarantees (< 1 hour for new content)

2. **Multi-Modal Search**
   - Image search (diagrams, charts)
   - Video search (lectures, demos)
   - Code search (GitHub, StackOverflow)

3. **Collaborative Research**
   - Team workspaces
   - Shared knowledge bases
   - Annotation and commenting

4. **Advanced Analytics**
   - Query pattern analysis
   - Knowledge gap identification
   - Personalized recommendations

---

## 📖 References

### **Perplexity AI Architecture:**
- Query understanding with LLMs (GPT-4, Claude, Gemini, Sonar)
- Hybrid retrieval (own crawlers + Google/Bing APIs)
- RAG with real-time web access
- Inline citations for transparency
- Conversational follow-ups
- Dynamic model selection

### **Key Differences:**
- **Perplexity:** Production system, 10,000s updates/sec, own crawlers
- **RAG Lab:** Educational system, transparency, full metrics, customizable

### **Our Advantage:**
- ✅ Full transparency (see every step)
- ✅ Customizable (change any component)
- ✅ Educational (learn by doing)
- ✅ Open source (no black boxes)

---

## 🚀 Getting Started

### **Phase 1 Implementation (Next Steps):**

1. **Inline Citations** (30 min)
   - Modify `services/chat/app/service.py`
   - Add citation insertion prompt
   - Update frontend to display `[N]` format

2. **Follow-up Questions** (30 min)
   - Add follow-up generation function
   - Update API response format
   - Add UI component for suggestions

3. **Dynamic Model Selection** (60 min)
   - Add intent classification
   - Implement model selection logic
   - Update UI to show model choice

**Total Time:** ~2 hours
**Impact:** 🚀 **HUGE** - Feels like Perplexity!

---

**Version:** 1.2.0
**Date:** November 5, 2025
**Status:** 📋 Planning → 🚧 Ready to Implement
**Next:** Custom Crawler / "Skill" System (see CUSTOM_CRAWLER_DESIGN.md)

