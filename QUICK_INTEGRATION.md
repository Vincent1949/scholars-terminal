# Quick Integration Guide - Open PDF Feature

Add "Open PDF" functionality to your existing Scholar's Terminal in **3 simple steps**.

---

## Step 1: Add Enhanced Metadata Module (5 minutes)

Copy `enhanced_metadata.py` to your backend directory:

```
scholars-terminal/
├── backend/
│   ├── enhanced_metadata.py  ← Add this file
│   ├── knowledge_chatbot.py
│   └── ...
```

That's it for Step 1. No code changes yet.

---

## Step 2: Update API Response (10 minutes)

### Option A: Minimal Change (Just add page numbers)

Edit `Scholars_api.py` or `knowledge_chatbot.py`:

```python
# At the top, add import
from enhanced_metadata import OpenPDFActionFormatter

# Find your search endpoint
@router.post("/api/search")
async def search_knowledge_base(query: str):
    # Your existing search code
    results = collection.query(
        query_texts=[query],
        n_results=5
    )
    
    # Your existing LLM answer generation
    answer = generate_answer_with_llm(query, results)
    
    # ===== ADD THIS =====
    # Format sources with Open PDF actions
    formatted_response = OpenPDFActionFormatter.format_response_with_actions(
        answer=answer,
        sources=results['metadatas'][0]  # Your search result metadata
    )
    
    return formatted_response  # Instead of your old response
    # ===== END ADD =====
```

### Option B: Full Integration (If rebuilding database)

Also update `build_database.py`:

```python
from enhanced_metadata import EnhancedMetadataExtractor

# In your process_file function, when creating metadata:
metadata = EnhancedMetadataExtractor.create_enhanced_metadata(
    file_path=file_path,
    source_name=source_name,
    source_type=source_type,
    chunk_index=chunk_index,
    chunk_text=chunk_text,
    page_number=page_num  # If you track pages
)
```

---

## Step 3: Add Backend Endpoint (5 minutes)

Add this to your `Scholars_api.py`:

```python
import subprocess
import platform
import os
from pydantic import BaseModel

class OpenPDFRequest(BaseModel):
    file_path: str
    page: int

@router.post("/api/open-pdf")
async def open_pdf(request: OpenPDFRequest):
    """Open PDF file at specified page"""
    
    try:
        # Check file exists
        if not os.path.exists(request.file_path):
            return {
                "success": False,
                "error": "PDF file not found"
            }
        
        # Open PDF based on OS
        system = platform.system()
        
        if system == "Windows":
            subprocess.Popen(['start', '', request.file_path], shell=True)
        elif system == "Darwin":  # macOS
            subprocess.Popen(['open', request.file_path])
        else:  # Linux
            subprocess.Popen(['xdg-open', request.file_path])
        
        return {
            "success": True,
            "message": f"Opened {os.path.basename(request.file_path)}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

**That's all the backend changes!**

---

## Step 4: Update Frontend (15 minutes)

### Option A: Minimal (Just add button)

In your search results component:

```jsx
// Wherever you display search results
{sources.map((source, index) => (
  <div key={index} className="source-card">
    <h4>{source.filename}</h4>
    
    {/* ADD THIS */}
    {source.page_number && (
      <p>Page {source.page_number}</p>
    )}
    
    {source.action && source.action.type === 'open_pdf' && (
      <button onClick={() => handleOpenPDF(source.action)}>
        {source.action.label}
      </button>
    )}
    {/* END ADD */}
  </div>
))}
```

Add the handler:

```jsx
const handleOpenPDF = async (action) => {
  try {
    const response = await fetch('/api/open-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_path: action.file_path,
        page: action.page
      })
    });
    
    const result = await response.json();
    
    if (!result.success) {
      alert(`Error: ${result.error}`);
    }
  } catch (error) {
    console.error('Failed to open PDF:', error);
  }
};
```

### Option B: Full Featured (Use provided component)

Copy `OpenPDFComponent.jsx` to your frontend and use it:

```jsx
import { SearchResults } from './components/OpenPDFComponent';

// In your app
<SearchResults
  answer={searchResult.answer}
  sources={searchResult.sources}
  visual_content_note={searchResult.visual_content_note}
/>
```

**Done!**

---

## Testing Your Integration

### Test 1: Check API Response Format

```bash
# Make a search request
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "volcano diagram"}'
```

**Expected response:**
```json
{
  "answer": "...",
  "sources": [
    {
      "filename": "Earth Science.pdf",
      "page_number": 187,
      "action": {
        "type": "open_pdf",
        "file_path": "D:/Books/Earth Science.pdf",
        "page": 187,
        "label": "Open PDF (page 187)"
      }
    }
  ]
}
```

### Test 2: Check Open PDF Endpoint

```bash
curl -X POST http://localhost:8000/api/open-pdf \
  -H "Content-Type: application/json" \
  -d '{"file_path": "D:/Books/test.pdf", "page": 1}'
```

**Expected:**
- PDF opens in default viewer
- Returns `{"success": true}`

### Test 3: Frontend Integration

1. Search for something: "volcano"
2. Check browser console for response format
3. Click "Open PDF" button
4. Verify PDF opens

---

## Compatibility Matrix

| Component | Requires Rebuild | Breaking Change | Time |
|-----------|------------------|-----------------|------|
| enhanced_metadata.py | No | No | 1 min |
| API formatting | No | No | 5 min |
| Open PDF endpoint | No | No | 5 min |
| Frontend button | No | No | 10 min |
| Full metadata in DB | Yes | No | Hours |

**Key Point:** You can add this feature **WITHOUT rebuilding your database**!

The enhanced metadata is **optional**. The feature will work with your existing database, just without:
- Figure references
- Visual content flags  
- Some page numbers (if not in metadata)

---

## Gradual Rollout Strategy

### Phase 1: Basic (Today - 20 minutes)

✅ Add Open PDF endpoint  
✅ Add basic button to frontend  
✅ Works with existing database  

**Users get:** Click to open PDF (no page number)

### Phase 2: Enhanced Response (Next - 10 minutes)

✅ Add response formatting  
✅ Show page numbers if available  

**Users get:** Click to open PDF at page

### Phase 3: Full Metadata (When convenient - next rebuild)

✅ Rebuild database with enhanced metadata  
✅ Get figure detection  
✅ Get visual content flags  

**Users get:** Full experience with figure references

---

## Minimal Working Example

**Entire backend addition** (one file):

```python
# Add to Scholars_api.py

import subprocess
import platform

@router.post("/api/open-pdf")
async def open_pdf(file_path: str, page: int):
    try:
        if platform.system() == "Windows":
            subprocess.Popen(['start', '', file_path], shell=True)
        else:
            subprocess.Popen(['open', file_path])
        return {"success": True}
    except:
        return {"success": False}
```

**Entire frontend addition** (in your component):

```jsx
// Add button
<button onClick={() => {
  fetch('/api/open-pdf', {
    method: 'POST',
    body: JSON.stringify({
      file_path: source.source,
      page: source.page_number || 1
    })
  });
}}>
  Open PDF
</button>
```

**That's it for basic functionality!**

---

## Common Questions

### Q: Do I need to rebuild my database?

**A:** No! The basic feature works with your existing database. Enhanced features (figure detection, etc.) require rebuild.

### Q: What if my database doesn't have page numbers?

**A:** PDFs will open at page 1. Still useful for finding the right book.

### Q: Does this work with EPUB/TXT files?

**A:** Only PDFs support this feature. Other formats ignored gracefully.

### Q: What about security?

**A:** File path comes from YOUR database, not user input. Safe if your database is trusted.

### Q: Can users open files outside the indexed books?

**A:** No. Only files that are in the database can be opened (your books).

---

## Next Steps

1. **Copy files** to your project
2. **Test backend endpoint** with curl
3. **Add frontend button** to one search result
4. **Test opening a PDF**
5. **Expand to all results** once working
6. **Rebuild database** with enhanced metadata (optional)

**Time to basic functionality:** ~30 minutes  
**Time to full featured:** ~1 hour + rebuild time

---

## Support

See `OPEN_PDF_FEATURE.md` for:
- Detailed architecture
- Cross-platform specifics
- Advanced features
- Troubleshooting guide

**You now have everything you need to add this feature!** 🚀
