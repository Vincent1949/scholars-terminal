# Research Scanner Integration - Quick Start Guide

## Status: ✅ Files Prepared, Ready to Install

### What's Been Done

1. ✅ **requirements.txt** updated with research scanner dependencies:
   - apscheduler>=3.10.0
   - sentence-transformers>=3.0.0

2. ✅ **Scholars_api_integrated.py** created with research scanner routes:
   - All original functionality preserved
   - Research scanner API added at `/api/research/*`
   - Scheduler prepared (commented out by default)

### Installation Steps

#### Step 1: Install New Dependencies
```bash
cd D:\Claude\Projects\scholars-terminal
pip install apscheduler sentence-transformers
```

#### Step 2: Backup and Replace API File
```bash
# Backup your original
copy frontend\src\Scholars_api.py frontend\src\Scholars_api_BACKUP.py

# Replace with integrated version
copy frontend\src\Scholars_api_integrated.py frontend\src\Scholars_api.py
```

#### Step 3: Test the Integration (CLI)
```bash
# Navigate to research scanner
cd research_scanner

# Test source connectivity
python scanner.py test-sources

# Expected output:
# Testing source connectivity...
#   ✓ arXiv: 2 papers returned
#   ✓ Semantic Scholar: 2 papers returned
#   ✓ HuggingFace: 2 papers returned
```

#### Step 4: Start the Backend
```bash
# From project root
cd D:\Claude\Projects\scholars-terminal
python frontend\src\Scholars_api.py
```

You should see:
```
🎓 Starting Scholar's Terminal API v2.0 (with Research Scanner)...
📚 ChromaDB: D:\Claude\Projects\scholars-terminal\data\vector_db
🤖 Ollama: http://localhost:11434
🌐 API: http://localhost:8000
📖 Docs: http://localhost:8000/docs
🔬 Research API: http://localhost:8000/api/research/status
✅ Connected to ChromaDB at D:\Claude\Projects\scholars-terminal\data\vector_db
🔬 Research Scanner routes registered at /api/research/*
```

#### Step 5: Test the Research Scanner API

Open browser to: http://localhost:8000/docs

Try these endpoints:
- `GET /api/research/status` - Check scanner configuration
- `GET /api/research/latest` - View recently indexed papers
- `POST /api/research/scan` - Run a manual scan (this will take 5-15 min)
- `GET /api/research/search?q=RAG` - Search indexed papers

Or use curl:
```bash
# Check status
curl http://localhost:8000/api/research/status

# Search papers
curl http://localhost:8000/api/research/search?q=RAG

# Run manual scan
curl -X POST http://localhost:8000/api/research/scan
```

### Configuration (Optional)

Edit `research_scanner/config.py` to customize:

**Topics:** Add/remove research interests
```python
TopicConfig(
    name="Your Topic Name",
    keywords=["keyword1", "keyword2"],
    weight=1.5,
    arxiv_categories=["cs.AI"],
)
```

**Scanning Frequency:**
```python
days_lookback: int = 7  # How far back to check
relevance_threshold: float = 0.3  # 0.0-1.0 filter
max_papers_per_scan: int = 50  # Safety cap
```

**Enable Scheduler** (optional):
In `Scholars_api.py`, uncomment these lines:
```python
# scheduler = start_scheduler()
# print("⏰ Research Scanner scheduler started (daily at 3 AM)")
```

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│  1. Scanner fetches papers from arXiv, Semantic         │
│     Scholar, HuggingFace based on your topics           │
├─────────────────────────────────────────────────────────┤
│  2. Papers run through 2-pass filter:                   │
│     - Quick keyword check                               │
│     - Ollama relevance scoring (0.0-1.0)                │
├─────────────────────────────────────────────────────────┤
│  3. Papers above threshold (0.3) get full summaries     │
│     from Ollama with structured extraction              │
├─────────────────────────────────────────────────────────┤
│  4. Summaries + papers indexed into ChromaDB           │
│     "research_papers" collection                        │
├─────────────────────────────────────────────────────────┤
│  5. Papers available via:                               │
│     - Research search API                               │
│     - Main Scholar's Terminal chat (same DB)            │
│     - Direct collection queries                         │
└─────────────────────────────────────────────────────────┘
```

### Your First Scan

After starting the backend, run your first scan:

```bash
# Via API
curl -X POST http://localhost:8000/api/research/scan

# Or via CLI
cd research_scanner
python scanner.py scan --verbose
```

**Expect:**
- Scan takes 5-15 minutes depending on:
  - Number of new papers found
  - Ollama model speed (llama3.2)
  - Network latency to paper APIs

**Output:**
```
STEP 1: Fetching papers from sources...
[arXiv] Found: 45, New: 38, Skipped: 7
[Semantic Scholar] Found: 52, New: 44, Skipped: 8
Total unique new papers: 82

STEP 2: Scoring relevance and generating summaries...
  ✓ [0.75] Retrieval-Augmented Generation for Knowledge-Intensive NLP
  ✓ [0.68] Efficient Vector Search with Binary Quantization
  ✗ [0.22] Unrelated Paper Title (below threshold)
...

STEP 3: Indexing into ChromaDB...
Indexed: 24 papers
```

### Verify Papers Are Indexed

```bash
# Check how many papers in research collection
python research_scanner/scanner.py status

# Search for specific topic
python research_scanner/scanner.py search "RAG"
```

### Troubleshooting

**"Module not found" errors:**
```bash
pip install -r requirements.txt
```

**Ollama timeout:**
- Increase timeout in `config.py`: `ollama_timeout: int = 600`
- Or use faster model: `ollama_model: str = "llama3.2"`

**No papers found:**
- Check `config.py` topics match your interests
- Lower threshold: `relevance_threshold: float = 0.2`
- Increase lookback: `days_lookback: int = 14`

**ChromaDB errors:**
- Ensure ChromaDB path exists: `D:\Claude\Projects\scholars-terminal\data\vector_db`
- Check permissions on data directory

### Next Steps

Once working:
1. Enable the scheduler for automatic daily scans
2. Customize topics in config.py to your research interests
3. Integrate search into your React frontend
4. Adjust relevance_threshold based on quality of results

### Support Files Created

- `frontend/src/Scholars_api_integrated.py` - New API with scanner
- `frontend/src/Scholars_api_BACKUP.py` - Original backup (after you copy)
- `requirements.txt` - Updated with scanner deps
- `research_scanner/` - All scanner code (already in place)
