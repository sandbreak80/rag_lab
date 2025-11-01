# 🎨 Multi-Tab UI Implementation Plan

**Date:** November 1, 2025  
**Status:** In Progress  
**Current File:** `src/templates/index.html` (2,552 lines)

---

## 📋 Requirements

### User Requirements:
1. ✅ **Add rerank_top_k to config** (DONE - in presets.json)
2. ✅ **Add web_search config** (DONE - docs & pages_per_doc in presets.json)
3. ⏳ **Build multi-tab UI** (IN PROGRESS)
4. ⏳ **Move lab guide to dedicated tab**
5. ⏳ **Keep current style and theme** (dark glassmorphic design)

---

## 🎯 Tab Structure

### Tab 1: Chat (Main interaction)
**Content:**
- File upload section (existing)
- Chat interface (existing)
- Quick metrics summary (compact)

**Purpose:** Primary interaction point for students

---

### Tab 2: Settings
**Content:**
- RAG Component Toggles (existing settings panel content)
  - Query Expansion
  - BM25 Search
  - Hybrid Fusion
  - Knowledge Graph
  - LLM Re-ranking
  - Web Search ⭐ NEW
- RAG Configuration Sliders
  - Top-K (5-50)
  - Rerank Top-K (5-20) ⭐ NEW
  - Web Search Docs (1-10) ⭐ NEW
  - Web Search Pages/Doc (1-5) ⭐ NEW
- LLM Settings (existing)
  - Model selector
  - Temperature
  - Max Tokens
  - Context Window
- Preset Buttons (existing)

**Purpose:** Complete configuration control

---

### Tab 3: Metrics & History
**Content:**
- Current metrics dashboard (existing)
- Query history (new)
- Performance trends (new)
- Comparison mode button (existing)

**Purpose:** Performance analysis and comparison

---

### Tab 4: Lab Guide
**Content:**
- Interactive lab guide (existing lab-guide panel)
- 6 sections with progress tracking
- Reset progress button
- Production preset button

**Purpose:** Educational content and exercises

---

## 🎨 Design Specifications

### Tab Bar Design:
```css
- Position: Top of container (below header)
- Style: Glassmorphic (matching header)
- Background: var(--glass-bg) with backdrop-filter: blur(20px)
- Border: 1px solid var(--glass-border)
- Border-radius: 20px 20px 0 0
- Tabs: Inline flex, equal width
- Active tab: Accent gradient, border-bottom highlight
- Inactive tabs: Semi-transparent, hover effect
```

### Tab Content Design:
```css
- Background: var(--glass-bg)
- Backdrop-filter: blur(20px)
- Border: 1px solid var(--glass-border)
- Border-radius: 0 0 20px 20px
- Padding: 24px
- Shadow: 0 8px 32px rgba(0, 0, 0, 0.3)
```

### Animation:
```css
- Tab switch: Fade in/out (0.2s ease)
- Active indicator: Slide transition (0.3s ease)
```

---

## 🔧 Implementation Steps

### Step 1: Add Tab Navigation HTML (NEXT)
```html
<div class="tab-navigation">
    <button class="tab-btn active" data-tab="chat">
        💬 Chat
    </button>
    <button class="tab-btn" data-tab="settings">
        ⚙️ Settings
    </button>
    <button class="tab-btn" data-tab="metrics">
        📊 Metrics
    </button>
    <button class="tab-btn" data-tab="lab">
        🎓 Lab Guide
    </button>
</div>
```

### Step 2: Wrap Existing Content in Tab Containers
```html
<div class="tab-content active" id="tab-chat">
    <!-- File upload -->
    <!-- Chat interface -->
    <!-- Compact metrics -->
</div>

<div class="tab-content" id="tab-settings">
    <!-- Settings panel content (move from collapsible) -->
</div>

<div class="tab-content" id="tab-metrics">
    <!-- Metrics dashboard (move from collapsible) -->
    <!-- Add history section -->
</div>

<div class="tab-content" id="tab-lab">
    <!-- Lab guide (move from collapsible) -->
</div>
```

### Step 3: Add Tab Styling CSS
- Tab navigation bar
- Tab buttons (active/inactive states)
- Tab content containers
- Transitions and animations

### Step 4: Add Tab Switching JavaScript
```javascript
function switchTab(tabName) {
    // Hide all tab contents
    // Show selected tab content
    // Update active tab button
    // Save to localStorage
}

// Initialize on page load
// Restore last active tab from localStorage
```

### Step 5: Update Settings Tab with New Controls
- Add web_search toggle
- Add rerank_top_k slider
- Add web_search_docs slider
- Add web_search_pages_per_doc slider

### Step 6: Update Config State Management
```javascript
currentConfig = {
    use_query_expansion: false,
    use_bm25: false,
    use_hybrid: false,
    use_graph: false,
    use_reranking: false,
    use_web_search: false,  // NEW
    top_k: 10,
    rerank_top_k: 10,  // NEW
    web_search_docs: 5,  // NEW
    web_search_pages_per_doc: 2  // NEW
}
```

### Step 7: Test All Tabs
- Tab switching works
- Settings persist across tabs
- Metrics update correctly
- Lab guide progress saves
- Styling consistent

---

## 📁 Files to Modify

### Primary:
- `src/templates/index.html` (2,552 lines)
  - Add tab navigation
  - Restructure content into tabs
  - Add new settings controls
  - Update JavaScript

### Supporting:
- `src/static/settings-panel.css` (might rename to tabs.css)
- Create new `src/static/tabs.css` for tab-specific styling

---

## ✅ Completed So Far

- ✅ Added `rerank_top_k` to all presets (5-15)
- ✅ Added `use_web_search` toggle to all presets
- ✅ Added `web_search_docs` (3-10) to all presets
- ✅ Added `web_search_pages_per_doc` (1-5) to all presets
- ✅ Added `web_search` to feature_impacts
- ✅ Committed config updates

---

## ⏳ Next Steps

1. Create `src/static/tabs.css` with tab navigation styles
2. Update `src/templates/index.html`:
   - Add tab navigation bar
   - Wrap content in tab containers
   - Add new settings controls (rerank_top_k, web_search)
   - Update JavaScript (tab switching, config management)
3. Test tab switching and persistence
4. Test all settings controls
5. Validate metrics display in tab
6. Validate lab guide in tab

---

## 🎯 Success Criteria

- ✅ 4 tabs: Chat, Settings, Metrics, Lab Guide
- ✅ Tab switching smooth (fade animation)
- ✅ Settings persist across tabs
- ✅ New config options work (rerank_top_k, web_search)
- ✅ Styling matches current theme (dark glassmorphic)
- ✅ Responsive (works on mobile)
- ✅ localStorage persistence (last active tab, progress)

---

## 🚧 Current Challenge

**File Size:** `index.html` is 2,552 lines  
**Strategy:** Incremental updates using search_replace  
**Risk:** Large file might make edits challenging  
**Mitigation:** Well-targeted search strings, test after each change

---

**Status:** Ready to proceed with tab implementation  
**Next Action:** Create tabs.css stylesheet


