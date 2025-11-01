# 🐛 Bug Tracker - Multi-Tab UI Issues

**Date:** November 1, 2025  
**Status:** Active Bug Fixing  
**Priority:** HIGH

---

## 🎯 Defect List

### BUG-001: Tabs Not Changing Content
**Status:** 🔴 OPEN  
**Priority:** P0 - Critical  
**Description:** Some tabs don't change the page content when clicked  
**Root Cause:** Tab content not properly moved/shown in tab containers  
**Fix Required:** JavaScript to show/hide correct content per tab  
**Test Method:** Playwright automation  
**Assigned To:** In Progress

---

### BUG-002: Model Name Not Updating in Header
**Status:** 🔴 OPEN  
**Priority:** P1 - High  
**Description:** When different model is selected, model name at top of page doesn't update  
**Root Cause:** Model change event not triggering header update  
**Fix Required:** Add event listener to update header on model change  
**Test Method:** API + Playwright  
**Assigned To:** In Progress

---

### BUG-003: Gear Icon Non-Functional
**Status:** 🔴 OPEN  
**Priority:** P1 - High  
**Description:** Gear icon (settings toggle) now does nothing  
**Root Cause:** Settings panel hidden, toggle button not updated for tabs  
**Fix Required:** Remove old toggle button OR redirect to Settings tab  
**Test Method:** Playwright  
**Assigned To:** In Progress

---

### BUG-004: Lab Guide Icon Non-Functional
**Status:** 🔴 OPEN  
**Priority:** P1 - High  
**Description:** Lab guide icon now does nothing  
**Root Cause:** Lab guide toggle button not updated for tabs  
**Fix Required:** Remove old toggle button OR redirect to Lab tab  
**Test Method:** Playwright  
**Assigned To:** In Progress

---

### BUG-005: Settings Tab Empty
**Status:** 🔴 OPEN  
**Priority:** P0 - Critical  
**Description:** Settings tab has no controls to change configuration  
**Root Cause:** Settings panel content not moved into Settings tab  
**Fix Required:** Move/duplicate settings controls into tab-settings container  
**Test Method:** Playwright + Manual  
**Assigned To:** In Progress

---

### BUG-006: Web Search Not Working + Missing Config
**Status:** 🔴 OPEN  
**Priority:** P1 - High  
**Description:**  
- Web search functionality not working  
- Missing UI controls for web_search_docs (results returned)  
- Missing UI controls for web_search_pages_per_doc  
**Root Cause:**  
- Web search integration incomplete  
- UI controls for web_search settings not added  
**Fix Required:**  
1. Add web_search toggle to Settings tab  
2. Add web_search_docs slider (1-10)  
3. Add web_search_pages_per_doc slider (1-5)  
4. Validate web search API integration  
**Test Method:** API + Playwright  
**Assigned To:** In Progress

---

### BUG-007: "RAG Configuration" & "Performance Analytics" at Bottom
**Status:** 🔴 OPEN  
**Priority:** P2 - Medium  
**Description:** "RAG Configuration" and "Performance Analytics" titles appear at bottom of every tab, non-functional  
**Root Cause:** Placeholder divs from tab structure still showing  
**Fix Required:** Remove placeholder content, show actual panels  
**Test Method:** Playwright  
**Assigned To:** In Progress

---

### BUG-008: Lab Guide Content Incomplete
**Status:** 🔴 OPEN  
**Priority:** P1 - High  
**Description:**  
- Lab guide only shows 6 sections  
- Expanded lab content not reflected  
- Should show comprehensive exercises and fundamentals  
**Root Cause:** Lab guide content not updated with new educational materials  
**Fix Required:**  
1. Integrate AI_FUNDAMENTALS content  
2. Add MODEL_COMPARISON_EXERCISE  
3. Add all 11+ exercises  
4. Update progress tracking  
**Test Method:** Manual review + Playwright  
**Assigned To:** In Progress

---

### BUG-009: No Performance Metrics in UI
**Status:** 🔴 OPEN  
**Priority:** P0 - Critical  
**Description:** No metrics visible in UI for performance as previously defined  
**Root Cause:** Metrics dashboard not properly displayed in Metrics tab  
**Fix Required:**  
1. Show metrics dashboard in Metrics tab  
2. Ensure metrics update after queries  
3. Show latency breakdown  
4. Show component status  
**Test Method:** API + Playwright  
**Assigned To:** In Progress

---

## 🎯 Fix Strategy

### Phase 1: Critical Path (P0 Bugs)
1. **BUG-001:** Fix tab content visibility (JavaScript)  
2. **BUG-005:** Populate Settings tab with controls  
3. **BUG-009:** Show metrics dashboard in Metrics tab  

### Phase 2: High Priority (P1 Bugs)
4. **BUG-002:** Fix model name update in header  
5. **BUG-003:** Remove/redirect gear icon  
6. **BUG-004:** Remove/redirect lab guide icon  
7. **BUG-006:** Fix web search + add config UI  
8. **BUG-008:** Enhance lab guide content  

### Phase 3: Medium Priority (P2 Bugs)
9. **BUG-007:** Remove placeholder text at bottom  

---

## 🧪 Testing Plan

### Playwright Tests:
```python
# test_tabs.py
async def test_tab_switching():
    # Click each tab, verify content changes
    
async def test_settings_visible():
    # Go to Settings tab, verify controls present
    
async def test_metrics_visible():
    # Go to Metrics tab, verify dashboard present
    
async def test_lab_guide_visible():
    # Go to Lab tab, verify guide present
    
async def test_model_change_updates_header():
    # Change model, verify header updates
    
async def test_web_search_config():
    # Verify web search toggles and sliders present
```

### API Tests:
```bash
# Test web search endpoint
curl -X POST http://localhost:8009/search -d '{"query":"test"}'

# Test search with web search enabled
curl -X POST http://localhost:8002/search_with_config \
  -H "Content-Type: application/json" \
  -d '{"query":"test","config":{"use_web_search":true}}'
```

---

## 📊 Progress Tracker

**Total Bugs:** 9  
**Fixed:** 0  
**In Progress:** 9  
**Open:** 9  

**Status:** 0% Complete

---

## 🚀 Next Steps

1. ✅ Create bug tracker (DONE)
2. ⏳ Start with BUG-001 (tab switching)
3. ⏳ Use Playwright to investigate
4. ⏳ Fix issues systematically
5. ⏳ Test each fix
6. ⏳ Update bug status
7. ⏳ Repeat until all fixed

---

**Let's start fixing!** 🔧

