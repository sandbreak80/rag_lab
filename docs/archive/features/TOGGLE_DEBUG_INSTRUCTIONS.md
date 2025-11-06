# Toggle Debug Instructions 🔍

The new intelligence feature toggles aren't working. Let's debug step by step.

## Step 1: Open Browser DevTools

1. Open http://localhost:3000 in your browser
2. Press **F12** to open DevTools
3. Go to the **Console** tab
4. Look for the initial config log: `🔍 ConfigStore initialized with:`

## Step 2: Check Initial State

Run this in the browser console:

```javascript
// Check what's in localStorage
console.log('LocalStorage:', JSON.parse(localStorage.getItem('rag_config') || '{}'));

// Check current Zustand state
const state = window.__ZUSTAND_STORES__?.[0]?.getState?.() || {};
console.log('Zustand State:', {
  usePromptEnhancement: state.usePromptEnhancement,
  useAutoModelRouting: state.useAutoModelRouting,
  useVectorDB: state.useVectorDB,
  useResearchAgent: state.useResearchAgent,
  useWebSearch: state.useWebSearch,
  useGraph: state.useGraph,
});
```

## Step 3: Test toggleFeature Function Directly

```javascript
// Get the Zustand store
const store = window.__ZUSTAND_STORES__?.[0];

if (store) {
  const state = store.getState();

  // Test toggle
  console.log('BEFORE:', state.usePromptEnhancement);
  state.toggleFeature('usePromptEnhancement');

  // Wait a bit for state update
  setTimeout(() => {
    const newState = store.getState();
    console.log('AFTER:', newState.usePromptEnhancement);
  }, 100);
}
```

## Step 4: Clear LocalStorage and Reset

If the above doesn't work, try clearing localStorage:

```javascript
// Clear old config
localStorage.removeItem('rag_config');

// Reload page
location.reload();
```

## Step 5: Manual State Check

After reload, check if defaults are loaded:

```javascript
const store = window.__ZUSTAND_STORES__?.[0];
if (store) {
  const state = store.getState();
  console.log('Full State:', {
    usePromptEnhancement: state.usePromptEnhancement,
    useAutoModelRouting: state.useAutoModelRouting,
    useVectorDB: state.useVectorDB,
    useResearchAgent: state.useResearchAgent,
    toggleFeature: typeof state.toggleFeature,
  });
}
```

## Expected Results

- `usePromptEnhancement` should be `false` (default)
- `useAutoModelRouting` should be `false` (default)
- `useVectorDB` should be `true` (default)
- `useResearchAgent` should be `true` (default)
- `toggleFeature` should be `function`

## If Still Not Working

Check the React component rendering:

```javascript
// Find the Settings Panel in React DevTools
// Check if the extracted values are correct
// Check if onClick handlers are attached

// You can also try clicking the button and checking if the event fires
document.querySelector('button#prompt-enhancement')?.addEventListener('click', (e) => {
  console.log('BUTTON CLICKED!', e);
});
```

## Nuclear Option: Reset Everything

```bash
# On the server, clear the frontend volume
docker volume rm rag_lab_frontend-data 2>/dev/null || true

# Rebuild from scratch
cd /home/ubuntu/rag_lab
docker compose down frontend
docker compose up -d --build frontend
```

## Report Back

After running these tests, report:
1. What the initial state shows
2. Whether toggleFeature exists and is a function
3. Whether calling it manually works
4. Any console errors you see

