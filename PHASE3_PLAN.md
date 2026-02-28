# Phase 3: New Sources Implementation

**Goal:** Add IEEE Xplore, medRxiv, and bioRxiv support

**Why:**
- **IEEE Xplore** → Better aerospace/engineering coverage
- **medRxiv** → Medical preprints (faster than PubMed)
- **bioRxiv** → Biology preprints (faster than PubMed)

---

## Implementation Plan

### 1. IEEE Xplore
**Coverage:** Engineering, computer science, electronics
**API:** IEEE Xplore API (requires API key)
**Format:** JSON REST API
**Rate limits:** 200 calls/day (free tier)

**Implementation complexity:** Medium
- Requires API key (free but registration needed)
- JSON parsing straightforward
- Good documentation

**Will improve:**
- Aerospace template (currently 44% → target 70%+)
- Engineering templates (when added)
- Computer science (supplements arXiv)

### 2. medRxiv
**Coverage:** Medical preprints (not peer-reviewed yet)
**API:** medRxiv API (free, no key required)
**Format:** Similar to bioRxiv
**Rate limits:** Generous (be respectful)

**Implementation complexity:** Easy
- No API key required
- Simple JSON API
- Similar to arXiv structure

**Will improve:**
- Medical templates (faster than PubMed indexing)
- Clinical research (preprints)
- COVID-19 research (heavily used)

### 3. bioRxiv
**Coverage:** Biology preprints
**API:** bioRxiv API (free, no key required)
**Format:** REST API with JSON
**Rate limits:** Generous (be respectful)

**Implementation complexity:** Easy
- No API key required
- Well-documented API
- Can share code with medRxiv (same platform)

**Will improve:**
- Biology templates (faster papers)
- Genetics template
- Biochemistry, molecular biology

---

## Implementation Strategy

### Phase 3A: Core Infrastructure (1 hour)
1. Create base source class extensions
2. Add API configuration
3. Error handling for new sources

### Phase 3B: Implement Sources (2-3 hours)
1. IEEE Xplore implementation
2. medRxiv implementation
3. bioRxiv implementation

### Phase 3C: Integration (1 hour)
1. Update template schemas
2. Add to existing templates
3. Test integration

### Phase 3D: Testing (1-2 hours)
1. Unit tests for each source
2. Integration tests
3. Template validation

---

## Source Specifications

### IEEE Xplore API

**Endpoint:** https://ieeexploreapi.ieee.org/api/v1/search/articles

**Authentication:** API key in header

**Query parameters:**
- `querytext` - Search query
- `max_records` - Results per page (default: 25, max: 200)
- `start_record` - Pagination
- `sort_field` - Sort by relevance, date, etc.
- `content_type` - Conferences, Journals, Standards

**Response format:**
```json
{
  "total_records": 150,
  "articles": [{
    "title": "Paper Title",
    "abstract": "Abstract text...",
    "authors": [{"full_name": "Author Name"}],
    "publication_date": "2024-01-15",
    "doi": "10.1109/...",
    "html_url": "https://ieeexplore.ieee.org/document/...",
    "publisher": "IEEE",
    "content_type": "Conferences"
  }]
}
```

**Rate limits:**
- Free tier: 200 calls/day
- Paid tier: Higher limits

**Setup required:**
- Register at https://developer.ieee.org/
- Get API key
- Add to .env file

### medRxiv API

**Endpoint:** https://api.medrxiv.org/details/medrxiv/[date]/[date]/[cursor]

**Authentication:** None required

**Query method:**
- Date range queries
- Subject area filtering
- Full-text search

**Response format:**
```json
{
  "collection": [{
    "rel_title": "Paper Title",
    "rel_abs": "Abstract...",
    "rel_authors": [{"author_name": "Name"}],
    "rel_date": "2024-01-15",
    "rel_doi": "10.1101/...",
    "rel_link": "https://www.medrxiv.org/content/...",
    "category": "infectious diseases"
  }]
}
```

**Rate limits:**
- Be respectful (1 request/second recommended)

**Setup required:**
- None (public API)

### bioRxiv API

**Endpoint:** https://api.biorxiv.org/details/biorxiv/[date]/[date]/[cursor]

**Same as medRxiv** (same platform, different content)

**Categories:**
- Molecular Biology
- Genetics
- Neuroscience
- Bioinformatics
- etc.

---

## Configuration Updates

### .env additions

```bash
# IEEE Xplore
IEEE_API_KEY=your_key_here
IEEE_MAX_RESULTS=25
IEEE_ENABLED=false

# medRxiv
MEDRXIV_ENABLED=false

# bioRxiv
BIORXIV_ENABLED=false
```

### Template schema additions

```yaml
sources:
  # Existing sources
  arxiv:
    enabled: true
    categories: [...]
  
  pubmed:
    enabled: true
    queries: [...]
  
  huggingface:
    enabled: true
  
  # NEW SOURCES
  ieee:
    enabled: false
    queries: ["query1", "query2"]
    content_types: ["Conferences", "Journals"]
  
  medrxiv:
    enabled: false
    subject_areas: ["infectious diseases", "cardiology"]
  
  biorxiv:
    enabled: false
    subject_areas: ["molecular biology", "genetics"]
```

---

## Priority Order

**For v1.1 Launch:**

1. **bioRxiv** (easiest, high impact for bio templates)
2. **medRxiv** (easy, similar to bioRxiv)
3. **IEEE** (medium difficulty, API key needed)

**Rationale:**
- bioRxiv and medRxiv are quick wins (no API key)
- IEEE provides good value but needs setup
- Can launch with bioRxiv/medRxiv, add IEEE as v1.2

---

## Expected Impact

**With new sources:**

| Template | Current | With bioRxiv/medRxiv | With IEEE |
|----------|---------|---------------------|-----------|
| Biology | 86.7% | **90%+** | 86.7% |
| Medical | 74% | **85%+** | 74% |
| Aerospace | 44% | 44% | **70%+** |

**Additional benefits:**
- Faster paper discovery (preprints ahead of peer review)
- Broader coverage (IEEE for engineering)
- Better relevance (source diversity)

---

## Implementation Notes

### Shared Code Pattern

bioRxiv and medRxiv can share base class:

```python
class BioRxivBase:
    """Shared implementation for bioRxiv and medRxiv"""
    
    def __init__(self, base_url):
        self.base_url = base_url
    
    def fetch_papers(self, start_date, end_date, cursor=0):
        # Shared fetch logic
        pass
    
    def parse_response(self, response):
        # Shared parsing logic
        pass

class BioRxivSource(BioRxivBase):
    def __init__(self):
        super().__init__("https://api.biorxiv.org")

class MedRxivSource(BioRxivBase):
    def __init__(self):
        super().__init__("https://api.medrxiv.org")
```

### IEEE Specific

Needs separate implementation due to different API:

```python
class IEEESource:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
    
    def fetch_papers(self, query, max_results=25):
        headers = {"x-api-key": self.api_key}
        # Implementation
        pass
```

---

## Starting Implementation NOW...
