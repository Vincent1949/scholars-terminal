# Research Paper Review System - User Guide

## 🎯 Overview

The Review System adds a **staging/approval workflow** before papers are permanently added to your database.

### New Workflow:
```
Scan → Filter (≥0.3) → STAGING → Manual Review → Approve/Reject → ChromaDB
```

**Benefits:**
- ✅ Preview papers before committing
- ✅ Sort by relevance, date, citations, or topic
- ✅ Batch approve/reject operations
- ✅ Auto-approve high-quality papers
- ✅ Keep database clean and curated

---

## 🚀 Quick Start

### 1. Check Staged Papers
```bash
curl http://localhost:8000/api/review/staged
```

### 2. Preview a Paper
```bash
curl http://localhost:8000/api/review/staged/PAPER_ID
```

### 3. Approve Papers
```bash
curl -X POST http://localhost:8000/api/review/approve \
  -H "Content-Type: application/json" \
  -d '{"paper_ids": ["paper1", "paper2"]}'
```

### 4. Reject Papers
```bash
curl -X POST http://localhost:8000/api/review/reject \
  -H "Content-Type: application/json" \
  -d '{"paper_ids": ["paper1"], "reason": "Not relevant"}'
```

---

## 💻 CLI Tool Usage

### Install Dependencies
```bash
pip install click rich --break-system-packages
```

### List Staged Papers
```bash
cd D:\Claude\Projects\scholars-terminal\research_scanner
python -m review_cli list --sort relevance --limit 20
```

**Sort options:**
- `relevance` - Highest quality first (default)
- `date` - Newest first
- `citations` - Most cited first
- `topic` - Grouped by research area

### Preview Paper Details
```bash
python -m review_cli preview PAPER_ID
```

Shows:
- Full title and authors
- Publication date and source
- Topics and categories
- Relevance score and citation count
- Summary and URLs

### Interactive Review Mode
```bash
python -m review_cli interactive --sort relevance
```

**Actions per paper:**
- `a` - Approve (add to permanent database)
- `r` - Reject (remove from staging)
- `s` - Skip (leave in staging for later)
- `q` - Quit review session

### Batch Operations
```bash
# Approve multiple papers
python -m review_cli approve paper1 paper2 paper3

# Reject multiple papers
python -m review_cli reject paper1 paper2 --reason "Off-topic"
```

### Auto-Approve High-Quality Papers
```bash
python -m review_cli auto-approve \
  --min-relevance 0.8 \
  --min-citations 100 \
  --max-papers 10
```

Automatically approves papers that meet ALL criteria:
- Relevance score ≥ 0.8
- Citation count ≥ 100
- Up to 10 papers max

### View Statistics
```bash
python -m review_cli stats
```

Shows:
- Papers in staging (awaiting review)
- Papers approved (in database)
- Papers rejected (declined)
- Total processed

---

## 🌐 API Endpoints

### GET `/api/review/staged`
List papers in staging area

**Query Parameters:**
- `sort_by` - Sort order: relevance, date, citations, topic (default: relevance)
- `limit` - Max papers to return (1-100, default: 20)
- `topic` - Filter by topic (optional)

**Example:**
```bash
curl "http://localhost:8000/api/review/staged?sort_by=citations&limit=10"
```

---

### GET `/api/review/staged/{paper_id}`
Get detailed preview of a paper

**Example:**
```bash
curl http://localhost:8000/api/review/staged/arxiv:2602.12345
```

**Response includes:**
- Full metadata (title, authors, dates, topics)
- Complete summary and content
- URLs (paper, PDF, source)
- Citation count and relevance score

---

### POST `/api/review/approve`
Approve papers and move to permanent database

**Body:**
```json
{
  "paper_ids": ["paper1", "paper2", "paper3"]
}
```

**Response:**
```json
{
  "message": "Processed 3 papers",
  "approved": 3,
  "failed": 0
}
```

---

### POST `/api/review/reject`
Reject papers and remove from staging

**Body:**
```json
{
  "paper_ids": ["paper1"],
  "reason": "Not relevant to current research"
}
```

**Response:**
```json
{
  "message": "Processed 1 papers",
  "rejected": 1,
  "failed": 0
}
```

Rejected papers are logged to: `data/rejected_papers.json`

---

### POST `/api/review/auto-approve`
Auto-approve high-quality papers

**Query Parameters:**
- `min_relevance` - Minimum relevance score (0.0-1.0, default: 0.8)
- `min_citations` - Minimum citation count (default: 100)
- `max_papers` - Maximum papers to approve (1-50, default: 10)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/review/auto-approve?min_relevance=0.9&min_citations=200&max_papers=5"
```

---

### GET `/api/review/stats`
Get review statistics

**Response:**
```json
{
  "staged": 25,
  "approved": 124,
  "rejected": 18,
  "total_processed": 142
}
```

---

## 📊 Typical Workflows

### Workflow 1: Daily Review (5 minutes)
```bash
# 1. List top papers by relevance
python -m review_cli list --sort relevance --limit 20

# 2. Auto-approve obvious winners
python -m review_cli auto-approve --min-relevance 0.9 --min-citations 200

# 3. Interactive review of remaining
python -m review_cli interactive
```

### Workflow 2: Topic-Focused Review
```bash
# 1. Filter by topic
curl "http://localhost:8000/api/review/staged?topic=RAG&limit=30"

# 2. Review papers in that topic
python -m review_cli list --topic "Retrieval-Augmented Generation"

# 3. Batch approve relevant ones
python -m review_cli approve paper1 paper2 paper3
```

### Workflow 3: Quality Curation
```bash
# 1. Sort by citations (find influential papers)
python -m review_cli list --sort citations --limit 50

# 2. Preview high-citation papers
python -m review_cli preview PAPER_ID

# 3. Approve high-quality research
python -m review_cli approve PAPER_ID
```

### Workflow 4: Quick Cleanup
```bash
# 1. Check stats
python -m review_cli stats

# 2. Auto-approve best papers
python -m review_cli auto-approve --max-papers 20

# 3. Bulk reject low-relevance
curl -X POST http://localhost:8000/api/review/reject \
  -H "Content-Type: application/json" \
  -d '{"paper_ids": ["low1", "low2"], "reason": "Below threshold"}'
```

---

## 🔧 Configuration

### Change Staging Behavior

Edit `research_scanner/indexer.py`:

```python
# Current: Auto-add to permanent collection
collection = self.client.get_or_create_collection("research_papers")

# New: Add to staging for review
collection = self.client.get_or_create_collection("research_papers_staging")
```

### Adjust Auto-Approve Criteria

Create custom approval rules:

```python
from research_scanner.reviewer import PaperReviewer

reviewer = PaperReviewer()

# Example: Approve recent, well-cited RAG papers
papers = reviewer.get_staged_papers(limit=100)
for paper in papers:
    if ('RAG' in paper['topics'] and 
        paper['citation_count'] > 50 and
        paper['published_date'] > '2025-01-01'):
        reviewer.approve_paper(paper['id'])
```

---

## 📂 File Locations

```
D:\Claude\Projects\scholars-terminal\
├── research_scanner/
│   ├── reviewer.py          - Core review logic
│   ├── review_routes.py     - API endpoints
│   └── review_cli.py        - CLI tool
├── data/
│   ├── vector_db/           - ChromaDB database
│   │   ├── research_papers_staging/  - Staged papers
│   │   └── research_papers/          - Approved papers
│   └── rejected_papers.json - Rejection log
└── Scholars_api.py          - Main API server
```

---

## 💡 Pro Tips

### Tip 1: Review Right After Scanning
```bash
# Trigger scan
curl -X POST http://localhost:8000/api/research/scan

# Wait ~7 minutes, then review
python -m review_cli interactive
```

### Tip 2: Use Relevance Thresholds
- **0.9+** - Extremely relevant, auto-approve
- **0.7-0.9** - Relevant, review manually
- **0.5-0.7** - Marginally relevant, likely reject
- **<0.5** - Not relevant, auto-reject

### Tip 3: Track Rejections
Check what you've rejected:
```bash
cat D:\Claude\Projects\scholars-terminal\data\rejected_papers.json
```

Learn from patterns to adjust topics/keywords.

### Tip 4: Weekly Cleanup
Set a reminder to review staged papers weekly:
```bash
# Monday morning ritual
python -m review_cli stats
python -m review_cli auto-approve
python -m review_cli interactive
```

---

## 🎯 Next Steps

1. **Install CLI dependencies:**
   ```bash
   pip install click rich --break-system-packages
   ```

2. **Try the CLI:**
   ```bash
   cd D:\Claude\Projects\scholars-terminal\research_scanner
   python -m review_cli list
   ```

3. **Start your first review:**
   ```bash
   python -m review_cli interactive
   ```

4. **Integrate into daily routine:**
   - Morning: Check staged papers
   - Auto-approve high-quality
   - Interactive review of remainder
   - Keep database curated!

---

**Your Scholar's Terminal now has professional research curation! 🎓**
