# 🔬 Exercise 11: Model Comparison - Enterprise AI Decision Making

**For:** Solutions Engineers, Architects, Sales Engineering Leaders  
**Time:** 45-60 minutes  
**Goal:** Learn to recommend the right model size for enterprise use cases

---

## 🎯 Learning Objectives

By completing this exercise, you will:
- Understand model size vs performance trade-offs
- Calculate infrastructure costs for different models
- Recommend models based on customer requirements
- Confidently discuss "bigger isn't always better"

---

## 💼 Enterprise Context

**Customer Question:** *"Should we use GPT-4 or can a smaller model work?"*

**Your Answer After This Exercise:** *"Based on your [use case/volume/latency requirements], I recommend [specific model] because [data-driven reasoning]. Here's how we proved it..."*

---

## Part 1: Model Discovery (10 min)

### Task: Explore Available Models

1. **Query Ollama for models** (in terminal or via UI API)
```bash
curl http://localhost:11434/api/tags
```

2. **Record available models:**

| Model Name | Parameters | Context Window | Downloaded? |
|------------|------------|----------------|-------------|
| llama3.2:1b | 1B | 2048 | ☐ |
| llama3.2:3b | 3B | 4096 | ☐ |
| llama3.2:8b | 8B | 8192 | ☐ |
| mistral:7b | 7B | 8192 | ☐ |
| (others) | | | |

---

## Part 2: Baseline Testing (15 min)

### Test Query Set

Use these enterprise-relevant queries:

1. **Product Documentation:** "What are the system requirements?"
2. **Policy Question:** "What is our remote work policy?"
3. **Technical Support:** "How do I troubleshoot connection errors?"
4. **Customer Success:** "What features were added in the latest release?"

### Task: Test Each Model

For EACH model, run ALL 4 queries and record:

#### Model: llama3.2:1b

| Query | Latency (ms) | Quality (1-10) | Answer Complete? | Tokens Generated |
|-------|-------------|----------------|------------------|------------------|
| 1. System requirements | _____ | _____ | ☐ Yes ☐ No | _____ |
| 2. Remote work policy | _____ | _____ | ☐ Yes ☐ No | _____ |
| 3. Troubleshooting | _____ | _____ | ☐ Yes ☐ No | _____ |
| 4. Latest features | _____ | _____ | ☐ Yes ☐ No | _____ |
| **Average** | _____ | _____ | ___/4 | _____ |

#### Model: llama3.2:3b

| Query | Latency (ms) | Quality (1-10) | Answer Complete? | Tokens Generated |
|-------|-------------|----------------|------------------|------------------|
| 1. System requirements | _____ | _____ | ☐ Yes ☐ No | _____ |
| 2. Remote work policy | _____ | _____ | ☐ Yes ☐ No | _____ |
| 3. Troubleshooting | _____ | _____ | ☐ Yes ☐ No | _____ |
| 4. Latest features | _____ | _____ | ☐ Yes ☐ No | _____ |
| **Average** | _____ | _____ | ___/4 | _____ |

#### Model: llama3.2:8b

| Query | Latency (ms) | Quality (1-10) | Answer Complete? | Tokens Generated |
|-------|-------------|----------------|------------------|------------------|
| 1. System requirements | _____ | _____ | ☐ Yes ☐ No | _____ |
| 2. Remote work policy | _____ | _____ | ☐ Yes ☐ No | _____ |
| 3. Troubleshooting | _____ | _____ | ☐ Yes ☐ No | _____ |
| 4. Latest features | _____ | _____ | ☐ Yes ☐ No | _____ |
| **Average** | _____ | _____ | ___/4 | _____ |

---

## Part 3: Performance Analysis (10 min)

### Comparison Matrix

Fill in based on your test results:

| Metric | 1B Model | 3B Model | 8B Model | Winner |
|--------|----------|----------|----------|--------|
| **Avg Latency** | _____ ms | _____ ms | _____ ms | _____ |
| **Avg Quality** | _____/10 | _____/10 | _____/10 | _____ |
| **Complete Answers** | ___/4 | ___/4 | ___/4 | _____ |
| **Tokens/second** | _____ | _____ | _____ | _____ |
| **Instructions Following** | ⭐___ | ⭐___ | ⭐___ | _____ |

### Analysis Questions

**Q1: Which model is fastest?**  
A: _________________

**Q2: Which model has best quality?**  
A: _________________

**Q3: Is the quality improvement worth the latency increase?**

```
8B vs 3B:
- Quality improvement: _____% better
- Latency increase: _____ms slower (_____x slower)
- Worth it? ☐ Yes ☐ No

Reasoning:




```

**Q4: At what point do diminishing returns kick in?**

```
1B → 3B: +_____% quality for +_____ms
3B → 8B: +_____% quality for +_____ms

Best bang for buck: _____ model
```

---

## Part 4: Infrastructure Sizing (10 min)

### Enterprise Scenario

**Customer Requirements:**
- 1,000 employees using the system
- Average: 10 queries per employee per day = 10,000 queries/day
- Peak hours: 8am-10am (40% of daily queries = 4,000 queries in 2 hours)
- Peak QPS: 4,000 queries / 7,200 seconds ≈ 0.6 QPS
- SLA: < 2 second response time

### Calculate Infrastructure Needs

#### Option A: 1B Model

```
Average latency: _____ ms
Max throughput per server: 1000ms / _____ms = _____ QPS

Servers needed for 0.6 QPS: _____ server(s)
Cost per server: $500/month (AWS r6g.xlarge)
Total monthly cost: $_____

Meets SLA? ☐ Yes ☐ No
```

#### Option B: 3B Model

```
Average latency: _____ ms
Max throughput per server: 1000ms / _____ms = _____ QPS

Servers needed for 0.6 QPS: _____ server(s)
Cost per server: $800/month (AWS r6g.2xlarge)
Total monthly cost: $_____

Meets SLA? ☐ Yes ☐ No
```

#### Option C: 8B Model

```
Average latency: _____ ms
Max throughput per server: 1000ms / _____ms = _____ QPS

Servers needed for 0.6 QPS: _____ server(s)
Cost per server: $1200/month (AWS r6g.4xlarge)
Total monthly cost: $_____

Meets SLA? ☐ Yes ☐ No
```

### Cost-Benefit Analysis

| Model | Monthly Cost | Quality | Recommendation |
|-------|-------------|---------|----------------|
| 1B | $_____ | _____/10 | ☐ Recommend |
| 3B | $_____ | _____/10 | ☐ Recommend |
| 8B | $_____ | _____/10 | ☐ Recommend |

**Your Recommendation:** _________________

**Justification (for customer):**
```




```

---

## Part 5: Use Case Matching (10 min)

### Match Models to Enterprise Use Cases

| Use Case | Requirements | Best Model | Why? |
|----------|--------------|------------|------|
| **Customer chatbot** | <500ms, good quality | _____ | _____ |
| **Document Q&A** | <2s, high accuracy | _____ | _____ |
| **Real-time autocomplete** | <100ms, acceptable | _____ | _____ |
| **Complex research** | <5s, best quality | _____ | _____ |
| **Code generation** | <3s, high accuracy | _____ | _____ |
| **Email drafting** | <2s, creative | _____ | _____ |

---

## Part 6: Customer Conversation Prep

### Scenario: Customer Discovery Call

**Customer:** "We want to deploy AI for our 5,000-person support team. Should we use GPT-4 or can we run something locally?"

**Your Response (fill in):**

```
Based on your requirements, I recommend:

Model: _________________

Reasoning:
1. Latency: _________________
2. Cost: _________________
3. Quality: _________________
4. Privacy: _________________

With RAG, this model achieves _____% precision, which is _____ compared to GPT-4 
without RAG. Plus, your data never leaves your environment.

Infrastructure: _____ servers at $_____/month = $_____/month total

vs API costs: 5000 users × 10 queries/day × 30 days = 1.5M queries/month
GPT-4 Turbo: 1.5M × 2000 tokens × $0.01/1K = $_____/month

Local is _____ cheaper and you own the infrastructure.
```

---

## 🎯 Key Takeaways

### For Customer Conversations

**Discovery Questions:**
1. "What's your target response time?" → Size models
2. "How many queries per day?" → Calculate infrastructure
3. "What's your quality threshold?" → Choose model
4. "Any privacy/compliance needs?" → Local vs API

**Value Propositions:**
- "Smaller model + RAG beats larger model without RAG"
- "3B model is the sweet spot for most enterprise use cases"
- "You can upgrade models anytime without retraining"
- "Local deployment = full control + lower costs"

**Objection Handling:**
- **"Bigger is better"** → "Not with RAG. 3B + retrieval beats 70B alone on YOUR documents."
- **"GPT-4 is best"** → "For general knowledge, yes. For YOUR data, local + RAG wins."
- **"We need latest model"** → "Model is just one piece. Pipeline design matters more."

---

## 📊 Results Summary

Complete this final summary:

```
Model Tested: 1B, 3B, 8B

Winner for Speed: _____
Winner for Quality: _____
Winner for Value: _____

Best for Enterprise (balanced): _____

Why? 
_____________________________________________________
_____________________________________________________
_____________________________________________________
```

---

## 🎓 Certification Statement

I have completed this exercise and can now:
- ☐ Explain model size trade-offs to customers
- ☐ Calculate infrastructure costs for different models
- ☐ Recommend models based on requirements
- ☐ Justify "smaller + RAG > bigger alone"

**Name:** _________________  
**Date:** _________________  
**Score:** _____/100 (self-assessed)

---

**🎉 Congratulations!** You can now confidently guide customers on model selection for enterprise RAG deployments.

*For Splunk/Cisco Field Teams - AI Enablement Lab*
