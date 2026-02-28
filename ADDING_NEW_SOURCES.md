# Adding New Research Sources - Quick Guide

## Example: Adding PubMed (Biomedical Research)

I've created `pubmed_source.py` for you. Here's how to activate it:

---

### Step 1: Add Import to scanner.py

**File:** `research_scanner/scanner.py`

**Find this section (around line 24):**
```python
from research_scanner.sources.arxiv_source import ArxivSource
from research_scanner.sources.semantic_scholar_source import SemanticScholarSource
from research_scanner.sources.huggingface_source import HuggingFaceSource
```

**Add this line:**
```python
from research_scanner.sources.pubmed_source import PubMedSource
```

**Then find this section (around line 45):**
```python
        if self.config.huggingface_enabled:
            self.sources.append(HuggingFaceSource())
```

**Add after it:**
```python
        if self.config.pubmed_enabled:
            self.sources.append(PubMedSource(
                email=self.config.pubmed_email,
                api_key=self.config.pubmed_api_key,
            ))
```

---

### Step 2: Add Configuration Options

**File:** `research_scanner/config.py`

**Find the "Sources" section (around line 45):**
```python
    huggingface_enabled: bool = True
    huggingface_max_results: int = 30
```

**Add after it:**
```python
    # PubMed (biomedical literature)
    pubmed_enabled: bool = True
    pubmed_max_results: int = 20
    pubmed_email: str = "vincent@example.com"  # NCBI requires an email
    pubmed_api_key: str = ""  # Optional: get free key for 10 req/sec instead of 3
```

---

### Step 3: Add Topics for PubMed

**File:** `research_scanner/config.py`

**In the DEFAULT_TOPICS list (around line 20), add:**

```python
    TopicConfig(
        name="Neuroscience & Cognition",
        keywords=["neuroscience", "cognitive", "brain", "neural networks", "consciousness"],
        weight=1.2,
        arxiv_categories=[],  # PubMed doesn't use arXiv categories
    ),
    TopicConfig(
        name="Health & Medicine",
        keywords=["healthcare", "medical", "clinical", "diagnosis", "treatment"],
        weight=1.0,
        arxiv_categories=[],
    ),
    TopicConfig(
        name="Psychology",
        keywords=["psychology", "behavior", "mental health", "cognition"],
        weight=1.1,
        arxiv_categories=[],
    ),
```

---

### Step 4: Test It

```bash
cd D:\Claude\Projects\scholars-terminal\research_scanner
python scanner.py test-sources
```

You should see:
```
Testing source connectivity...
  ✓ arXiv: 2 papers returned
  ✓ semantic_scholar: 2 papers returned
  ✓ huggingface: 2 papers returned
  ✓ pubmed: 2 papers returned        ← NEW!
```

---

## Other Easy Sources to Add:

### 1. More arXiv Categories (No coding needed!)

**File:** `config.py` - Just add to existing topics:

```python
TopicConfig(
    name="Quantum Physics",
    keywords=["quantum", "qubit", "entanglement"],
    weight=1.2,
    arxiv_categories=["quant-ph"],
),
TopicConfig(
    name="Astrophysics",
    keywords=["cosmology", "dark matter", "galaxy", "universe"],
    weight=1.0,
    arxiv_categories=["astro-ph"],
),
TopicConfig(
    name="Mathematics",
    keywords=["theorem", "proof", "topology", "algebra"],
    weight=0.9,
    arxiv_categories=["math.CO", "math.GT"],
),
```

### 2. bioRxiv (Biology Preprints)

Similar structure to arXiv, would need a new source file like:
- `biorxiv_source.py` (~150 lines)
- API: https://api.biorxiv.org/

### 3. SSRN (Economics/Social Science)

- `ssrn_source.py` (~150 lines)  
- Topics: Economics, finance, law, management

### 4. PhilPapers (Philosophy)

- `philpapers_source.py` (~150 lines)
- Free API, great categorization

---

## Template for Any New Source:

**Every source needs:**
1. Inherit from `BaseSource`
2. Implement `search(query, max_results)`
3. Implement `fetch_by_topics(topics, days_back, max_results)`
4. Return list of `Paper` objects
5. Handle rate limiting (built into BaseSource)

**PubMed source I created is ~175 lines** - that's the template!

---

## Want me to create more sources?

Just tell me which ones:
- bioRxiv (biology)
- SSRN (economics/finance)
- PhilPapers (philosophy)
- Physics.org RSS (popular science news)
- Any other domain you're interested in!

Each takes ~10 minutes to code and test.
