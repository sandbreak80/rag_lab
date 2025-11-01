# 🎯 AI Discovery Questions for Customer Conversations

**For Splunk/Cisco Field Teams**  
**Target Audience:** Architects, Solutions Engineers, Sales Engineers, Sales Leaders

---

## 📋 Purpose

This guide provides structured discovery questions to uncover customer AI/RAG opportunities and position Splunk Observability Cloud as the solution.

**Use this when:**
- Initial customer conversations about AI
- Qualifying AI opportunities
- Understanding customer maturity
- Identifying pain points
- Building business cases

---

## 🎓 How to Use This Guide

### 1. **Set Context** (2 minutes)
*"I'd like to understand your AI journey - where you are today, where you're heading, and what challenges you're facing. This will help me show you how Splunk can accelerate your success."*

### 2. **Progress Through Sections** (15-20 minutes)
- Start with "Current State" (establish baseline)
- Move to "Technical Environment" (understand architecture)
- Explore "Pain Points" (uncover needs)
- Discuss "Future Plans" (identify opportunities)
- Address "Risk & Governance" (position observability)

### 3. **Listen More Than Talk** (80/20 rule)
- Ask questions, take notes
- Listen for pain points and hot buttons
- Resist the urge to pitch too early
- Build trust through understanding

### 4. **Connect to Solutions**
- Reference this lab when appropriate
- Offer to demo specific capabilities
- Provide relevant case studies
- Schedule follow-up with proof points

---

## 🔍 Discovery Question Framework

### Section 1: Current State Assessment

#### General AI Adoption
1. **"Are you currently using AI or LLMs in production?"**
   - ✅ **Yes:** "Tell me about your use cases. What's working well?"
   - ❌ **No:** "Have you experimented with AI? What's held you back from production?"
   - 🤔 **Exploring:** "What use cases are you evaluating? What's your timeline?"

2. **"What AI technologies are you using today?"**
   - Listen for: OpenAI, Anthropic, local LLMs (Ollama, LLaMA), AWS Bedrock, Azure OpenAI
   - Follow-up: "Why did you choose [vendor]? Are you satisfied?"

3. **"How many AI applications do you have?"**
   - 0-1: Early stage (education focus)
   - 2-5: Growing (observability need emerging)
   - 6+: Mature (observability critical)

4. **"Who owns AI initiatives at your organization?"**
   - Listen for: IT, Data Science, Engineering, Business Units
   - Indicates: Organizational maturity, decision-makers, budget owners

#### RAG Specific
5. **"Are you using Retrieval Augmented Generation (RAG)?"**
   - ✅ **Yes:** "What documents are you querying? How's the quality?"
   - ❌ **No:** "Are you aware of RAG? Would you like a brief explanation?"
   - Follow-up: Show this lab as reference architecture

6. **"If using RAG: What vector database are you using?"**
   - Listen for: Pinecone, Weaviate, ChromaDB, Milvus, Elasticsearch
   - Follow-up: "How are you monitoring it? How do you know it's working well?"

7. **"How are you handling document ingestion and chunking?"**
   - Listen for: Custom scripts, LangChain, LlamaIndex, manual processes
   - Pain points: Quality, consistency, maintenance

8. **"Are you using hybrid search (vector + keyword)?"**
   - ✅ **Yes:** "How do you balance the two? How do you know it's optimal?"
   - ❌ **No:** "Have you considered it? It typically improves precision by 15-25%."

---

### Section 2: Technical Environment

#### Infrastructure
9. **"Where are your AI workloads running?"**
   - Cloud (AWS, Azure, GCP)
   - On-premise
   - Hybrid
   - **Why it matters:** Impacts monitoring approach, cost, compliance

10. **"What type of compute are you using?"**
    - GPUs (NVIDIA A100, H100, etc.)
    - CPUs only
    - Serverless (Lambda, Cloud Functions)
    - **Why it matters:** Performance monitoring needs differ

11. **"Are you using containers or serverless?"**
    - Containers (Docker, Kubernetes)
    - Serverless (Lambda, etc.)
    - VMs
    - **Why it matters:** Observability strategy, instrumentation approach

#### Models & Frameworks
12. **"What models are you running?"**
    - Hosted (OpenAI, Anthropic, Cohere)
    - Self-hosted (Ollama, vLLM, TGI)
    - Fine-tuned
    - **Why it matters:** Cost, latency, compliance implications

13. **"What frameworks are you using?"**
    - LangChain, LlamaIndex, Haystack
    - Custom code
    - **Why it matters:** Integration points, instrumentation ease

14. **"How many queries per second are you handling?"**
    - <10 QPS: Small scale (cost less critical)
    - 10-100 QPS: Medium scale (observability emerging need)
    - 100+ QPS: Large scale (observability CRITICAL)

---

### Section 3: Pain Points & Challenges

#### Quality & Accuracy
15. **"How do you measure the quality of your AI responses?"**
    - ✅ **Measuring:** "What metrics? How do you track over time?"
    - ❌ **Not measuring:** "How do you know if quality degrades? What if users get bad answers?"
    - **Pain point:** Most customers don't measure quality systematically

16. **"Have you experienced hallucinations or incorrect answers?"**
    - ✅ **Yes:** "How often? How do you detect them? What's the business impact?"
    - ❌ **No:** "How do you know? Are you tracking groundedness/faithfulness?"
    - **Position Splunk:** "We track groundedness score in real-time to prevent hallucinations."

17. **"How do you handle answer relevance?"**
    - Listen for: Manual review, user feedback, no formal process
    - **Pain point:** Manual processes don't scale

18. **"Do you use re-ranking to improve precision?"**
    - ✅ **Yes:** "What approach? How do you measure impact?"
    - ❌ **No:** "Would 10-20% precision improvement justify the cost?"

#### Performance & Latency
19. **"What's your latency SLA for AI responses?"**
    - <500ms: Real-time (chatbots, customer support)
    - 500ms-2s: Interactive (search, recommendations)
    - 2s+: Batch/async (reports, analysis)
    - **Why it matters:** Determines optimization priorities

20. **"Have you experienced performance degradation?"**
    - ✅ **Yes:** "How did you find out? How long to fix?"
    - ❌ **No:** "How would you know if it happened? What's your monitoring strategy?"
    - **Pain point:** Reactive vs proactive monitoring

21. **"What's causing your slowest queries?"**
    - Don't know: "Would you like to see exactly where time is spent?" (Show lab metrics dashboard)
    - Know: "How did you discover this? How long did investigation take?"

22. **"Are GPU/infrastructure bottlenecks impacting performance?"**
    - Listen for: GPU utilization issues, memory constraints, scaling challenges
    - **Position Splunk:** "We correlate application latency with GPU/infrastructure metrics instantly."

#### Cost & Efficiency
23. **"What's your monthly AI spend?"**
    - <$1K: Small scale
    - $1K-$10K: Growing (cost awareness starting)
    - $10K-$100K: Significant (cost optimization critical)
    - $100K+: Enterprise (CFO/CIO involved)

24. **"Do you know your cost per query/answer?"**
    - ✅ **Yes:** "How are you tracking it? Trending?"
    - ❌ **No:** "Would you like to see cost per query tracked in real-time?"
    - **Pain point:** Most customers guess at costs

25. **"Have costs increased unexpectedly?"**
    - ✅ **Yes:** "How did you discover it? What caused it?"
    - ❌ **No:** "Do you have alerts if costs spike?"

26. **"Are you optimizing token usage?"**
    - Prompt compression, caching, context window management
    - **Opportunity:** Show cost optimization in this lab

#### Operations & Monitoring
27. **"How do you monitor your AI applications today?"**
    - Nothing: "What happens when something breaks?"
    - Basic logging: "How do you correlate logs across services?"
    - APM (Datadog, New Relic, etc.): "Do they track groundedness, hallucinations, cost?"
    - **Pain point:** Traditional APM doesn't understand AI metrics

28. **"How long does it take to troubleshoot issues?"**
    - Minutes: Rare (highly instrumented)
    - Hours: Common (manual investigation)
    - Days: Pain point (no visibility)
    - **Position Splunk:** "We reduce time-to-resolution from hours to minutes with correlated metrics."

29. **"How do you know if your RAG pipeline is degrading?"**
    - Proactive monitoring: Rare
    - User complaints: Common (reactive)
    - **Pain point:** Most customers learn from users, not monitoring

30. **"Do you have alerts for AI-specific issues?"**
    - Groundedness drop, latency spike, cost spike, high error rate
    - **Most customers:** No AI-specific alerts

---

### Section 4: Future Plans & Roadmap

#### Growth & Scale
31. **"What's your AI roadmap for the next 12 months?"**
    - Listen for: New use cases, scaling plans, budget increases
    - **Opportunity:** Position Splunk for growth

32. **"How many new AI applications are you planning?"**
    - 0-2: Modest growth
    - 3-5: Significant growth (observability need increasing)
    - 6+: Aggressive growth (observability CRITICAL)

33. **"Are you planning to scale existing AI applications?"**
    - 2x: "Your monitoring needs will double. How are you preparing?"
    - 5x: "At that scale, you'll need proactive monitoring."
    - 10x+: "You'll need enterprise AI observability. Let me show you how."

#### Technology Evolution
34. **"Are you exploring new AI models or vendors?"**
    - Listen for: Model comparison needs, multi-model strategies
    - **Lab opportunity:** Show model comparison exercise

35. **"Are you considering fine-tuning or training custom models?"**
    - ✅ **Yes:** Mention Splunk AI Toolkit (MLTK) + DSDL integration
    - ❌ **No:** "RAG is often cheaper and faster than fine-tuning. Have you compared?"

36. **"Are you planning to use agentic AI or multi-step workflows?"**
    - Listen for: Complex orchestration, tool use, multi-agent systems
    - **Pain point:** Debugging multi-step AI is HARD without observability

#### Business Outcomes
37. **"What business metrics are tied to your AI initiatives?"**
    - Customer satisfaction, support ticket deflection, revenue impact
    - **Why it matters:** Connects AI performance to business value

38. **"How do you report AI ROI to leadership?"**
    - Listen for: Metrics used, reporting frequency, stakeholders
    - **Opportunity:** Show how Splunk provides exec-level dashboards

39. **"What would make your AI initiative a 'home run'?"**
    - Listen for: Success criteria, must-haves, nice-to-haves
    - **Position Splunk:** Map capabilities to their definition of success

---

### Section 5: Risk, Governance & Compliance

#### Security & Compliance
40. **"Are you handling sensitive data (PII, PHI, financial)?"**
    - ✅ **Yes:** "How do you ensure compliance? How do you audit AI decisions?"
    - ❌ **No:** "Do you plan to? Regulations are tightening."
    - **Position Splunk:** Audit trails, data lineage, compliance reporting

41. **"Do you have AI governance policies?"**
    - ✅ **Yes:** "How do you enforce them? How do you know they're followed?"
    - ❌ **No:** "Is leadership asking about AI risk? We can help."

42. **"How do you audit AI decisions for bias or fairness?"**
    - Most customers: No formal process
    - **Opportunity:** Splunk provides audit trails and analysis

#### Risk Management
43. **"What's your biggest fear about AI in production?"**
    - Hallucinations, security breach, cost overruns, regulatory issues
    - **Position Splunk:** "We help mitigate all of these with observability."

44. **"Have you had any AI incidents or outages?"**
    - ✅ **Yes:** "Tell me about it. How did you respond? What did you learn?"
    - ❌ **No:** "How would you know if quality degraded by 20%?"

45. **"How quickly can you rollback or disable a problematic AI feature?"**
    - Listen for: Deployment processes, kill switches, monitoring triggers
    - **Pain point:** Many customers have slow response times

---

## 🎯 Conversation Patterns & Techniques

### Pattern 1: The "How Do You Know?" Technique
When customer says something positive, ask "How do you know?"

**Example:**
- Customer: *"Our RAG system is working great!"*
- You: *"That's awesome! How do you measure 'great'? What metrics are you tracking?"*
- Customer: *"Well, users seem happy..."*
- You: *"So it's user feedback? How do you track that systematically? What if quality degrades tomorrow - how would you know?"*

**Result:** Exposes lack of observability

---

### Pattern 2: The "What If?" Technique
Introduce hypothetical scenarios to uncover risk awareness

**Example:**
- You: *"What if your groundedness score dropped from 0.95 to 0.70 overnight? How would you know?"*
- Customer: *"Hmm, we'd probably hear from users..."*
- You: *"So users would get bad answers for hours before you knew? What's the business impact of that?"*

**Result:** Creates urgency for observability

---

### Pattern 3: The "Show Me" Technique
Offer to demo specific capabilities during discovery

**Example:**
- Customer: *"We're struggling with latency..."*
- You: *"I'd love to show you something. We have a live RAG system right here - watch what happens when I query it..."*
  [Open lab, run query, show metrics dashboard]
- You: *"See how we break down latency by component? Vector search 40ms, BM25 30ms, reranking 180ms. Reranking is your bottleneck. This took 5 seconds to diagnose. How long would it take you?"*

**Result:** Demonstrates value immediately

---

### Pattern 4: The "Cost Visibility" Technique
Uncover cost concerns even if customer doesn't mention them

**Example:**
- You: *"Quick question - do you know what you spent on AI last month?"*
- Customer: *"Roughly $15K, I think."*
- You: *"Do you know which queries are most expensive? Or what your cost per query is?"*
- Customer: *"No, not really."*
- You: *"Would you like to see cost per query tracked in real-time? Let me show you..."*

**Result:** Opens cost optimization conversation

---

### Pattern 5: The "Scale Challenge" Technique
Project future pain based on growth plans

**Example:**
- Customer: *"We're planning to 10x our AI usage next year."*
- You: *"Wow, ambitious! So if you're doing 1000 queries/day now, you'll be at 10,000/day. At that scale:*
  - *How will you know if quality degrades?*
  - *How will you manage costs?*
  - *How will you troubleshoot performance issues?*
  - *Your current manual approach won't scale. Let me show you how Splunk automates this..."*

**Result:** Positions Splunk as essential for growth

---

## 📊 Scoring & Qualification

After discovery, score the opportunity:

### High Priority (Immediate Follow-up)
- ✅ AI in production (multiple use cases)
- ✅ Experiencing pain (quality, latency, cost)
- ✅ Growing rapidly (2x+ in 12 months)
- ✅ No comprehensive monitoring
- ✅ Budget authority identified
- ✅ Timeline <90 days

**Action:** Schedule POC, offer lab access, bring in specialist

---

### Medium Priority (Nurture)
- ✅ AI in pilot/early production
- ⚠️ Some pain points (but manageable)
- ⚠️ Modest growth plans
- ⚠️ Basic monitoring (logs, basic APM)
- ⚠️ Budget TBD
- ⚠️ Timeline 90-180 days

**Action:** Share lab access, educational content, stay engaged

---

### Low Priority (Long-term)
- ❌ AI in exploration phase only
- ❌ No significant pain
- ❌ No growth plans
- ❌ No budget
- ❌ No timeline

**Action:** Educate, share resources, check in quarterly

---

## 🎤 Conversation Closers

### After Discovery, Transition to Next Steps

**Option 1: Demo This Lab**
*"Based on what you've shared, I think you'd really benefit from seeing our AI reference architecture lab. It's a fully instrumented RAG system with Splunk Observability. Can I show you a 15-minute demo right now?"*

**Option 2: Schedule Deeper Dive**
*"This has been really helpful. I'd like to bring in our AI specialist to do a deeper technical dive. They can show you exactly how we'd monitor your specific use case. Does [date/time] work?"*

**Option 3: Offer Lab Access**
*"Would you like access to our AI lab? It's a hands-on environment where your team can experiment with RAG, compare models, and see Splunk observability in action. It's self-paced, takes 4-5 hours, and you keep the entire system as a reference architecture."*

**Option 4: Propose POC**
*"I think we're ready for a proof of concept. What if we instrumented ONE of your AI applications with Splunk Observability for 30 days? You'd see exactly how it works in your environment. Would that be valuable?"*

---

## 📚 Resources to Share

After discovery, share relevant resources:

### For Technical Stakeholders:
- Lab access (hands-on)
- AI_FUNDAMENTALS.md (concepts)
- Reference architecture diagrams
- Technical integration docs

### For Business Stakeholders:
- ROI calculator
- Case studies
- Executive summary deck
- Cost comparison (Splunk vs alternatives)

### For Everyone:
- Splunk blog posts on AI observability
- This lab as proof of capability
- Invitation to customer workshop

---

## ✅ Discovery Checklist

Before ending the conversation, ensure you have:

- [ ] Identified current AI use cases and scale
- [ ] Understood technical environment (cloud, on-prem, GPUs, etc.)
- [ ] Uncovered 2-3 specific pain points
- [ ] Established growth plans and timeline
- [ ] Identified budget and decision-makers
- [ ] Demonstrated relevant capability (lab demo)
- [ ] Scheduled next step (demo, POC, workshop, specialist call)
- [ ] Shared resources (lab access, docs, case studies)
- [ ] Set follow-up date
- [ ] Logged opportunity in CRM with notes

---

## 🎯 Key Takeaways

**Remember:**
1. **Listen more than talk** (80/20 rule)
2. **Ask "how do you know?" frequently** (exposes gaps)
3. **Demo this lab during discovery** (show, don't tell)
4. **Quantify pain** (time, money, risk)
5. **Connect to their roadmap** (growth creates urgency)
6. **Position Splunk as essential** (not nice-to-have)
7. **Always schedule next step** (momentum is key)

**The goal isn't to pitch Splunk - it's to uncover needs that Splunk solves.**

---

**Use this lab to demonstrate capabilities during discovery - it's your most powerful tool!**

