# DEBUG: Please Check These Things

The code IS deployed with fixes. Here's what to check:

## 1. Clear ALL Browser State

Not just refresh - do THIS:

**Chrome/Edge:**
```
1. Press F12 (open DevTools)
2. Right-click the refresh button
3. Click "Empty Cache and Hard Reload"
```

**OR:**
```
1. Open DevTools (F12)
2. Go to Application tab
3. Click "Clear storage"
4. Check ALL boxes
5. Click "Clear site data"
6. Close DevTools
7. Hard refresh (Ctrl+Shift+R)
```

**Firefox:**
```
1. Ctrl+Shift+Delete
2. Check "Cache" and "Cookies"
3. Time range: "Everything"
4. Clear Now
5. Close and reopen browser
```

## 2. Check What JS Bundle You're Loading

1. Open DevTools (F12)
2. Go to Network tab
3. Refresh page (Ctrl+R)
4. Look for `index-*.js` file
5. **Should be:** `index-BJHmjK2a.js`
6. **If you see:** `index-DOFOeztp.js` or any other hash → Browser is cached

## 3. Check Console for Errors

1. Open DevTools (F12)
2. Go to Console tab
3. Look for red errors
4. Tell me what errors you see

## 4. Test in Incognito/Private Mode

This bypasses ALL cache:

**Chrome/Edge:** Ctrl+Shift+N
**Firefox:** Ctrl+Shift+P
**Safari:** Cmd+Shift+N

Then go to: http://16.146.148.184:3000/

## 5. Verify You're Testing The Right URL

Make sure you're at:
```
http://16.146.148.184:3000/
```

NOT:
```
http://localhost:3000/  ← This won't work!
http://16.146.148.184:8080/  ← This is the API, not the UI!
```

## 6. What EXACTLY Are You Seeing?

Please tell me:

**Sources:**
- [ ] I see "Sources (8)" with 8 documents listed
- [ ] I see "Sources (0)" (empty)
- [ ] I don't see any "Sources" section at all

**Performance:**
- [ ] I see a "Performance Breakdown" dropdown I can click
- [ ] I see "Performance" but it's empty
- [ ] I don't see any performance section

**Answer:**
- [ ] I see an answer to my question
- [ ] I see an error message
- [ ] Nothing happens when I click Send

---

## VERIFICATION: The Code IS Deployed

I verified on the server:

✅ Container built: 2025-11-09 02:30 UTC
✅ JS bundle: index-BJHmjK2a.js
✅ Contains fix: `file_name:s.doc_id` (confirmed in minified code)
✅ HTML loads correct bundle: index-BJHmjK2a.js
✅ Nginx serving: port 3000
✅ API responding: citations returned

**The fixes ARE live. The issue is browser caching.**

Please try Incognito mode and tell me what you see.

