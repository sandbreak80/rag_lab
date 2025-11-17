# A/B Testing Page - Implementation Plan

**Last Updated:** November 17, 2025
**Status:** Design Complete - Ready for Implementation

---

## 📋 Implementation Checklist

### **Phase 1: Backend API (Week 1)**

#### **1.1 Prompt Library API**
- [ ] Create `services/api/routes/ab_testing.py`
- [ ] Add `GET /v1/ab-testing/prompts` endpoint
- [ ] Add `GET /v1/ab-testing/prompts/{id}` endpoint
- [ ] Load prompts from `frontend/src/data/promptLibrary.ts` (or move to backend)
- [ ] Add filtering/search capabilities

#### **1.2 A/B Test Execution API**
- [ ] Add `POST /v1/ab-testing/run` endpoint
- [ ] Support parallel execution (two simultaneous queries)
- [ ] Support sequential execution
- [ ] Return both results with metrics
- [ ] Handle errors gracefully (partial results)

#### **1.3 Auto-Grader API**
- [ ] Create `services/api/pipeline/auto_grader.py` (enhanced)
- [ ] Add `POST /v1/ab-testing/grade` endpoint
- [ ] Implement LLM-based grading using local model
- [ ] Grade 6 dimensions:
  - Answer Quality
  - Relevance
  - Faithfulness
  - Completeness
  - Conciseness
  - Source Quality
- [ ] Return structured JSON with scores and explanation
- [ ] Add fallback to heuristic scoring if LLM fails

#### **1.4 Test History API**
- [ ] Add `GET /v1/ab-testing/history` endpoint
- [ ] Add `POST /v1/ab-testing/save` endpoint
- [ ] Add `GET /v1/ab-testing/results/{test_id}` endpoint
- [ ] Store results in database or file system
- [ ] Support pagination and filtering

#### **1.5 Batch Testing API**
- [ ] Add `POST /v1/ab-testing/batch` endpoint
- [ ] Support running multiple prompts
- [ ] Return aggregated results
- [ ] Support progress tracking (WebSocket or polling)

---

### **Phase 2: Frontend Components (Week 2)**

#### **2.1 Page Structure**
- [ ] Create `frontend/src/pages/ABTestingPage.tsx`
- [ ] Add route in `App.tsx`
- [ ] Add navigation tab in `TabNavigation.tsx`
- [ ] Create layout with step-by-step flow

#### **2.2 Prompt Library Browser**
- [ ] Create `PromptLibraryBrowser.tsx`
- [ ] Display 20 prompts in grid/list view
- [ ] Add category filters
- [ ] Add complexity/difficulty filters
- [ ] Add search functionality
- [ ] Add preview modal
- [ ] Add "Use Custom Prompt" option

#### **2.3 Configuration Selector**
- [ ] Create `ConfigurationSelector.tsx`
- [ ] Support preset selection
- [ ] Support custom configuration
- [ ] Show configuration preview
- [ ] Add "Copy" and "Swap" buttons

#### **2.4 Test Runner**
- [ ] Create `ABTestRunner.tsx`
- [ ] Execute both queries
- [ ] Show progress indicators
- [ ] Handle errors
- [ ] Support cancellation

#### **2.5 Comparison View**
- [ ] Create `ComparisonView.tsx`
- [ ] Create `ResultPanel.tsx`
- [ ] Side-by-side layout
- [ ] Synchronized scrolling
- [ ] Expandable sections

---

### **Phase 3: Metrics & Visualization (Week 3)**

#### **3.1 Metrics Comparison Table**
- [ ] Create `MetricsComparisonTable.tsx`
- [ ] Display all metrics side-by-side
- [ ] Calculate percentage differences
- [ ] Highlight winners
- [ ] Add tooltips for metric explanations

#### **3.2 Auto-Grader Results**
- [ ] Create `AutoGraderResults.tsx`
- [ ] Display dimension scores
- [ ] Show overall winner
- [ ] Display explanation
- [ ] Show strengths/weaknesses
- [ ] Add radar chart

#### **3.3 Comparison Charts**
- [ ] Create `ComparisonCharts.tsx`
- [ ] Latency waterfall comparison
- [ ] Source distribution charts
- [ ] Quality radar chart
- [ ] Token usage charts
- [ ] Use Chart.js or Recharts

---

### **Phase 4: Advanced Features (Week 4)**

#### **4.1 Test History**
- [ ] Create `TestHistory.tsx`
- [ ] Display saved tests
- [ ] Filter and search
- [ ] Re-run functionality
- [ ] Delete tests

#### **4.2 Batch Testing**
- [ ] Create `BatchTestRunner.tsx`
- [ ] Select multiple prompts
- [ ] Run batch test
- [ ] Show progress
- [ ] Display results table
- [ ] Export results

#### **4.3 Export & Sharing**
- [ ] Add export to JSON
- [ ] Add export to CSV
- [ ] Add PDF report generation
- [ ] Add shareable links

---

## 🔧 Technical Implementation Details

### **Backend: Auto-Grader Enhancement**

**File:** `services/api/pipeline/auto_grader.py`

```python
async def grade_ab_responses(
    prompt: str,
    response_a: str,
    response_b: str,
    sources_a: list,
    sources_b: list,
    config_a: dict,
    config_b: dict,
    llm_client
) -> dict:
    """
    Grade two responses using LLM-as-judge

    Returns structured grading results
    """
    grading_prompt = build_grading_prompt(
        prompt, response_a, response_b, sources_a, sources_b
    )

    # Use local LLM for grading
    result = await llm_client.generate(
        model="llama3.2:3b",  # Fast enough for grading
        prompt=grading_prompt,
        temperature=0.1,  # Low temperature for consistency
        response_format="json"
    )

    return parse_grading_result(result)
```

### **Frontend: State Management**

**File:** `frontend/src/stores/abTestingStore.ts`

```typescript
interface ABTestingStore {
  selectedPrompt: PromptLibraryItem | null;
  configA: RAGConfig;
  configB: RAGConfig;
  testResults: ABTestResult | null;
  testHistory: ABTestResult[];
  isRunning: boolean;

  setPrompt: (prompt: PromptLibraryItem) => void;
  setConfigA: (config: RAGConfig) => void;
  setConfigB: (config: RAGConfig) => void;
  runTest: () => Promise<void>;
  saveTest: (result: ABTestResult) => void;
  loadHistory: () => Promise<void>;
}
```

---

## 📊 Missing Features to Consider

### **1. Real-Time Metrics**
- GPU utilization during test
- Memory usage tracking
- Network I/O monitoring
- Token generation speed

### **2. Advanced Quality Metrics**
- **Hallucination Detection**: Compare claims to sources
- **Citation Accuracy**: Verify citations are valid
- **Source Overlap Analysis**: Which sources are shared?
- **Response Similarity**: Semantic similarity between responses

### **3. Cost Analysis**
- Token cost estimation
- GPU cost per query
- Total cost comparison
- Cost per quality point

### **4. Statistical Significance**
- Run multiple iterations
- Calculate confidence intervals
- Statistical significance testing
- Variance analysis

### **5. Learning Recommendations**
- "Based on your tests, try..."
- "Configuration A is better for X because..."
- "To improve Y, consider..."
- Links to relevant documentation

### **6. Comparison Modes**
- **Diff Mode**: Highlight differences
- **Unified View**: Show both in single scroll
- **Focus Mode**: Full-screen one result
- **Split View**: Adjustable split ratio

### **7. Advanced Filtering**
- Filter by test date
- Filter by winner
- Filter by prompt category
- Filter by configuration type

### **8. Collaboration Features**
- Share test results
- Comment on tests
- Compare with classmates
- Leaderboard (best configurations)

---

## 🎯 Success Metrics

### **Functional Success:**
- ✅ All 20 prompts load correctly
- ✅ A/B tests execute successfully
- ✅ Auto-grader returns consistent results
- ✅ Metrics display accurately
- ✅ Charts render correctly
- ✅ History saves and loads

### **Performance Success:**
- Page load < 2 seconds
- Test execution < 30 seconds (both queries)
- Auto-grading < 10 seconds
- Smooth UI interactions

### **Educational Success:**
- Students can easily compare configurations
- Clear winner indication
- Explanatory text helps learning
- Prompts cover diverse scenarios

---

## 🚨 Potential Challenges & Solutions

### **Challenge 1: Auto-Grader Consistency**
**Problem:** LLM grading may be inconsistent
**Solution:**
- Use low temperature (0.1)
- Structured output (JSON mode)
- Fallback to heuristic scoring
- Cache results for same inputs

### **Challenge 2: Parallel Execution**
**Problem:** Running two queries simultaneously may overload system
**Solution:**
- Queue system for parallel requests
- Rate limiting
- Option to run sequentially
- Progress indicators

### **Challenge 3: Large Response Comparison**
**Problem:** Long responses hard to compare
**Solution:**
- Collapsible sections
- Diff highlighting
- Side-by-side with sync scroll
- Summary view option

### **Challenge 4: Test History Storage**
**Problem:** Storing many test results
**Solution:**
- Local storage for recent (last 10)
- Backend storage for persistent
- Pagination
- Cleanup old tests

---

## 📝 Next Steps

1. **Review Design** - Get approval on design document
2. **Create Prompt Library** - Finalize 20 prompts
3. **Backend API** - Implement endpoints
4. **Frontend MVP** - Basic A/B testing page
5. **Auto-Grader** - Implement LLM-based grading
6. **Visualizations** - Add charts and comparisons
7. **Polish** - Refine UI/UX
8. **Testing** - Comprehensive testing
9. **Documentation** - User guide and lab exercises

---

**Status:** Design Complete - Ready for Implementation Review

