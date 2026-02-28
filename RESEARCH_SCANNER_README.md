# Research Scanner - Universal Research Paper Discovery System

**Automated research paper tracking for ANY field of study.**

Track cutting-edge research in your domain with automated scanning from arXiv, PubMed, HuggingFace, and more. Built-in review workflow ensures only high-quality papers enter your database.

---

## 🎯 Key Features

✅ **Domain-Agnostic** - Works for ANY research field  
✅ **8+ Pre-built Templates** - AI, Medicine, Physics, Chemistry, Biology, Aerospace, Art, Psychology  
✅ **Multi-Source Scanning** - arXiv, PubMed, HuggingFace (extensible)  
✅ **AI-Powered Relevance** - Ollama LLM scores and summarizes papers  
✅ **Review Workflow** - Stage, preview, approve/reject before adding  
✅ **Vector Search** - ChromaDB for semantic paper search  
✅ **REST API + CLI** - Use programmatically or interactively  
✅ **Fully Customizable** - Add your own topics, sources, and criteria  

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install chromadb fastapi uvicorn requests beautifulsoup4 feedparser click rich pyyaml --break-system-packages
```

### 2. Install Ollama (for AI summarization)
```bash
# Download from https://ollama.ai
ollama pull llama3.2
```

### 3. Run Setup Wizard
```bash
python setup_wizard.py
```

**The wizard will:**
- Show 8+ research domains to choose from
- Let you preview topics and sources
- Allow custom topic addition
- Configure settings
- Save your configuration

### 4. Start the Server
```bash
python Scholars_api.py
```

### 5. Run Your First Scan
```bash
curl -X POST http://localhost:8000/api/research/scan
```

### 6. Review Papers
```bash
python review_papers.py interactive
```

---

## 📚 Available Research Domains

### 1. AI & Machine Learning
- **Topics:** RAG, AI Agents, Transformers, LLMs, Multimodal AI, Code Generation
- **Sources:** arXiv (cs.AI, cs.CL, cs.LG), HuggingFace, PubMed
- **Perfect for:** AI researchers, ML engineers, data scientists

### 2. Medical - Cardiac Surgery
- **Topics:** Minimally Invasive, CABG, Valve Procedures, Surgical Techniques
- **Sources:** PubMed (with MeSH terms)
- **Perfect for:** Cardiac surgeons, cardiothoracic fellows, medical researchers

### 3. Aerospace Engineering
- **Topics:** Propulsion Systems, Aerodynamics, Spacecraft Design, GNC
- **Sources:** arXiv (physics.flu-dyn, astro-ph)
- **Perfect for:** Aerospace engineers, propulsion researchers, flight dynamics specialists

### 4. Biology - Genetics & Genomics
- **Topics:** CRISPR, Gene Editing, Sequencing, Epigenetics, Gene Expression
- **Sources:** arXiv (q-bio.GN), PubMed
- **Perfect for:** Geneticists, molecular biologists, bioinformaticians

### 5. Chemistry - Materials Science
- **Topics:** Nanomaterials, Catalysis, Energy Materials, Polymer Chemistry
- **Sources:** arXiv (cond-mat, physics.chem-ph), PubMed
- **Perfect for:** Chemists, materials scientists, catalysis researchers

### 6. Art Conservation & Restoration
- **Topics:** Conservation Materials, Scientific Analysis, Preventive Conservation
- **Sources:** PubMed (conservation chemistry)
- **Perfect for:** Art conservators, museum scientists, cultural heritage specialists

### 7. Physics - Quantum & Condensed Matter
- **Topics:** Quantum Computing, Superconductivity, Quantum Materials, Entanglement
- **Sources:** arXiv (quant-ph, cond-mat)
- **Perfect for:** Physicists, quantum researchers, materials theorists

### 8. Social Sciences - Psychology
- **Topics:** Cognitive Psychology, Neuroscience, Mental Health, Developmental Psychology
- **Sources:** arXiv (q-bio.NC), PubMed
- **Perfect for:** Psychologists, neuroscientists, cognitive scientists

---

## 🛠️ System Architecture

```
Research Scanner
│
├── Templates System
│   ├── 8+ Pre-built Domain Templates (YAML)
│   ├── Custom Template Creation
│   └── Template Manager
│
├── Multi-Source Scanning
│   ├── arXiv (70+ categories)
│   ├── HuggingFace (daily papers)
│   ├── PubMed (MeSH terms, queries)
│   └── Extensible (add more sources)
│
├── AI Processing
│   ├── Relevance Scoring (Ollama LLM)
│   ├── Summarization (Ollama LLM)
│   └── Topic Matching (weighted keywords)
│
├── Storage & Search
│   ├── ChromaDB (vector database)
│   ├── Staging Collection (review)
│   └── Permanent Collection (approved)
│
└── Interfaces
    ├── REST API (FastAPI)
    ├── CLI Tool (Click + Rich)
    └── Review Workflow
```

---

## 📖 Usage Examples

### CLI Commands

```bash
# Setup
python setup_wizard.py                    # Interactive domain selection

# Scanning
curl -X POST http://localhost:8000/api/research/scan   # Trigger scan
curl http://localhost:8000/api/research/status         # Check status

# Reviewing
python review_papers.py list              # List staged papers
python review_papers.py interactive       # Interactive review
python review_papers.py stats             # Show statistics

# Searching
curl "http://localhost:8000/api/research/search?q=CRISPR&n=5"
curl "http://localhost:8000/api/research/latest?n=10"
```

### Python API

```python
from research_scanner.template_manager import TemplateManager
from research_scanner.reviewer import PaperReviewer

# Load a template
manager = TemplateManager()
template = manager.load_template('biology_genetics')

# Review papers
reviewer = PaperReviewer()
papers = reviewer.get_staged_papers(sort_by='relevance')

# Approve high-quality papers
for paper in papers:
    if paper['relevance_score'] > 0.8 and paper['citation_count'] > 100:
        reviewer.approve_paper(paper['id'])
```

---

## 🎨 Creating Custom Templates

### Option 1: Use Setup Wizard
```bash
python setup_wizard.py
# Select a base template
# Add custom topics interactively
```

### Option 2: Create YAML Manually

```yaml
domain: "Your Research Field"
description: "Description of what you track"

sources:
  arxiv:
    enabled: true
    categories:
      - "your.category"
  
  pubmed:
    enabled: true
    queries:
      - "your search query"

topics:
  - name: "Your Topic"
    keywords:
      - "keyword1"
      - "keyword2"
    weight: 1.5

relevance_threshold: 0.3
days_lookback: 7
max_papers_per_scan: 50
```

Save to: `research_scanner/templates/your_template.yaml`

---

## 🔧 Configuration

### Global Settings
Edit `research_scanner/config.py`:
- Ollama URL and model
- ChromaDB path
- Scan schedule (cron)
- Default thresholds

### Per-Domain Settings
Each template has:
- **relevance_threshold** - Minimum relevance score (0.0-1.0)
- **days_lookback** - How far back to scan
- **max_papers_per_scan** - Maximum papers per source
- **topic weights** - Importance of each topic

---

## 📊 Review Workflow

```
Scan → Filter → STAGING → Preview → Approve/Reject → DATABASE
```

### Sorting Options
- **relevance** - Highest quality first
- **citations** - Most cited first
- **date** - Newest first
- **topic** - Grouped by research area

### Approval Strategies

**Manual Review:**
```bash
python review_papers.py interactive
# Preview each paper
# Approve (a), Reject (r), Skip (s), or Quit (q)
```

**Auto-Approve High-Quality:**
```bash
python review_papers.py auto-approve \
  --min-relevance 0.9 \
  --min-citations 200 \
  --max-papers 10
```

**Batch Operations:**
```bash
python review_papers.py approve paper1 paper2 paper3
python review_papers.py reject paper4 --reason "Off-topic"
```

---

## 🌐 API Endpoints

### Research Scanner
- `POST /api/research/scan` - Trigger manual scan
- `GET /api/research/status` - Get scanner status
- `GET /api/research/latest?n=10` - Get latest papers
- `GET /api/research/search?q=query` - Search papers
- `GET /api/research/topics` - List configured topics

### Review System
- `GET /api/review/staged` - List papers awaiting review
- `GET /api/review/staged/{id}` - Preview paper details
- `POST /api/review/approve` - Approve papers
- `POST /api/review/reject` - Reject papers
- `POST /api/review/auto-approve` - Auto-approve high-quality
- `GET /api/review/stats` - Get review statistics

---

## 📁 Project Structure

```
research-scanner/
├── research_scanner/
│   ├── templates/           # Domain templates
│   │   ├── ai_ml.yaml
│   │   ├── medical_cardiac.yaml
│   │   ├── aerospace.yaml
│   │   └── ...
│   ├── sources/             # Paper sources
│   │   ├── arxiv_source.py
│   │   ├── pubmed_source.py
│   │   └── huggingface_source.py
│   ├── template_manager.py  # Template system
│   ├── reviewer.py          # Review workflow
│   ├── indexer.py           # ChromaDB integration
│   ├── summarizer.py        # Ollama LLM
│   └── config.py            # Configuration
├── setup_wizard.py          # Interactive setup
├── review_papers.py         # CLI review tool
├── Scholars_api.py          # FastAPI server
└── README.md                # This file
```

---

## 🎓 Real-World Example

### AI Researcher Workflow

**Day 1 - Setup:**
```bash
python setup_wizard.py
# Select: AI & Machine Learning
# Scan completes in ~7 minutes
# Found: 24 new papers
```

**Day 2 - Review:**
```bash
python review_papers.py list --sort relevance
# See: 24 papers sorted by quality
# Preview top 5 papers
# Auto-approve papers with relevance > 0.9 (12 papers)
# Manually review remainder (12 papers)
# Reject 3 off-topic papers
# Approve 9 relevant papers
# Total approved: 21 papers
```

**Day 3 - Search:**
```bash
curl "http://localhost:8000/api/research/search?q=RAG+retrieval&n=5"
# Get: 5 most relevant RAG papers from your database
```

**Ongoing:**
- Daily auto-scan at 3 AM
- Weekly review session (15 min)
- Database grows: ~70-100 papers/week

---

## 💡 Pro Tips

1. **Start Narrow, Expand Later** - Begin with specific topics, add more as needed
2. **Use High Thresholds Initially** - Start with 0.4-0.5 relevance, lower if needed
3. **Review Weekly** - Don't let staging area overflow
4. **Auto-Approve Strategically** - Use for highly-cited, recent papers
5. **Track Rejections** - Learn from patterns in `rejected_papers.json`
6. **Customize Keywords** - Add domain-specific terminology
7. **Mix Sources** - arXiv for preprints, PubMed for medical, etc.

---

## 🚧 Roadmap

### Coming Soon
- [ ] IEEE Xplore integration (engineering papers)
- [ ] medRxiv/bioRxiv (medical/biology preprints)
- [ ] JSTOR integration (humanities)
- [ ] ChemRxiv (chemistry preprints)
- [ ] Web UI for review workflow
- [ ] Email notifications for new papers
- [ ] Slack/Discord integration
- [ ] Citation graph visualization
- [ ] Paper recommendation engine

---

## 📄 License

MIT License - Use freely for research and commercial projects

---

## 🤝 Contributing

We welcome contributions! Especially:
- New domain templates
- Additional paper sources
- Improved relevance algorithms
- UI/UX enhancements

---

## 📞 Support

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Email:** [your-email]

---

**Built with ❤️ for researchers, by researchers**

*Stop missing important papers. Start discovering what matters.*
