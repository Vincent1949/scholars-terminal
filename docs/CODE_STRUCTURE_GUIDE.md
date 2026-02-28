# Scholar's Terminal - Code Structure Guide

## 📁 Project Overview

```
D:\Claude\Projects\ScholarsTerminal\
│
├── 📂 backend/              # Python backend (your main application)
├── 📂 frontend/             # React UI
├── 📂 data/                 # Data storage (including ChromaDB)
├── 📂 docs/                 # Documentation files
├── 📂 tests/                # Test suites
│
├── 📄 README.md             # Main documentation
├── 📄 QUICKSTART.md         # Getting started guide
├── 📄 requirements.txt      # Python dependencies
└── 📄 start.bat             # Launch script
```

---

## 🔧 BACKEND STRUCTURE (Main Application)

### **backend/** - The Heart of Scholar's Terminal

```
backend/
│
├── 📄 knowledge_chatbot.py              # 🌟 MAIN APPLICATION
│   └── Your primary FastAPI application
│       - API endpoints
│       - Query routing
│       - RAG pipeline
│
├── 📄 llm_failover_system.py            # 🤖 LLM Management
│   └── Handles Ollama model failover
│       - Primary/fallback model switching
│       - Automatic retry logic
│
├── 📄 github_processor.py                # 💻 Code Search
│   └── Processes GitHub repositories
│       - Code indexing
│       - Repository scanning
│
├── 📂 config/                            # ⚙️ Configuration
│   └── Settings files
│       - Database paths
│       - Model configurations
│       - API settings
│
├── 📂 extractors/                        # 📚 Document Processing
│   └── Extract text from documents
│       - PDF extraction
│       - EPUB extraction
│       - Text chunking
│
├── 📂 interfaces/                        # 🌐 API Interfaces
│   └── API endpoint definitions
│       - REST endpoints
│       - Request/response models
│
├── 📂 models/                            # 📊 Data Models
│   └── Pydantic models
│       - Document schemas
│       - Query models
│       - Response structures
│
├── 📂 utils/                             # 🔨 Utilities
│   └── Helper functions
│       - File operations
│       - Text processing
│       - Logging
│
└── 📄 .env                               # 🔐 Environment Variables
    └── Your sensitive configuration
        - Database paths
        - API keys
        - Model names
```

---

## 📋 KEY FILES EXPLAINED

### 1. **knowledge_chatbot.py** (MOST IMPORTANT)
**What it does:** This is your main application!

```python
# Inside knowledge_chatbot.py:
# - FastAPI app initialization
# - ChromaDB connection
# - Query processing
# - Response generation
# - API endpoints (/query, /search, etc.)
```

**Key responsibilities:**
- Receives user queries
- Searches ChromaDB for relevant chunks
- Sends context to Ollama
- Returns formatted responses

**Where to start:** This is the entry point when you run:
```bash
uvicorn knowledge_chatbot:app --reload
```

---

### 2. **llm_failover_system.py**
**What it does:** Manages your Ollama models

**Key features:**
- **Primary model:** llama3.2 (fast)
- **Fallback model:** mistral (backup)
- **Auto-switching:** If primary fails, uses fallback
- **Retry logic:** Attempts multiple times before giving up

**Why it's important:** Ensures your chatbot always works, even if one model is unavailable.

---

### 3. **github_processor.py**
**What it does:** Indexes your GitHub repositories

**Process:**
1. Scans `D:\GitHub` directory
2. Extracts code from repositories
3. Chunks code files
4. Stores in ChromaDB
5. Enables code search in queries

**Result:** You can ask:
- "Show me FastAPI authentication examples"
- "How did I implement RAG in my projects?"

---

### 4. **extractors/** Directory
**What it does:** Converts documents into searchable text

**Extractors for:**
- **PDF:** Uses PyMuPDF
- **EPUB:** Uses EbookLib
- **DOCX:** Uses python-docx
- **Text:** Direct processing

**Process:**
```
Document → Extractor → Raw Text → Chunker → Embeddings → ChromaDB
```

---

### 5. **.env File** (Configuration)
**What it contains:**

```env
# Database
CHROMA_DB_PATH=D:/Claude/Projects/ScholarsTerminal/data/vector_db

# Source paths
BOOKS_PATH=D:/Books
GITHUB_PATH=D:/GitHub

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
PRIMARY_MODEL=llama3.2:latest
FALLBACK_MODEL=mistral:latest

# API
API_HOST=0.0.0.0
API_PORT=8000
```

**Why it matters:** All paths and settings in one place - easy to update!

---

## 🎨 FRONTEND STRUCTURE

```
frontend/
│
├── 📂 src/                    # React source code
│   ├── App.jsx               # Main React component
│   ├── components/           # UI components
│   └── styles/               # CSS/styling
│
├── 📂 public/                 # Static assets
│   └── index.html            # HTML template
│
├── 📄 package.json            # Node dependencies
├── 📄 vite.config.js         # Build configuration
└── 📄 index.html              # Entry point
```

**Tech stack:**
- **React:** UI framework
- **Vite:** Build tool (fast!)
- **Dark theme:** Library aesthetic with amber accents

**Start frontend:**
```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
```

---

## 💾 DATA STRUCTURE

```
data/
└── vector_db/                 # 🔄 CURRENTLY COPYING (62%)
    ├── chroma.sqlite3         # Database index
    ├── embeddings/            # Vector embeddings
    └── metadata/              # Document metadata
```

**What's inside:**
- **13 million chunks** from 9,000+ books
- **Vector embeddings** for semantic search
- **Metadata:** Source, author, page numbers
- **108 GB total** (your entire library!)

---

## 📚 DOCS STRUCTURE

```
docs/
└── Various documentation files
    - API guides
    - User manuals
    - Technical specs
```

---

## 🧪 TESTS STRUCTURE

```
tests/
├── test_knowledge_chatbot.py  # Main app tests
├── test_*.py                  # Other test files
└── fixtures/                  # Test data
```

**Run tests:**
```bash
cd backend
pytest tests/
```

---

## 🔄 HOW IT ALL WORKS TOGETHER

### Query Flow:

```
1. USER QUERY
   ↓
2. FRONTEND (React)
   - User types query
   - Sends POST request
   ↓
3. BACKEND (knowledge_chatbot.py)
   - Receives query
   - Routes to appropriate handler
   ↓
4. CHROMADB (vector_db/)
   - Semantic search
   - Returns relevant chunks (top 5-10)
   ↓
5. LLM (llm_failover_system.py)
   - Sends chunks + query to Ollama
   - Primary: llama3.2
   - Fallback: mistral if needed
   ↓
6. RESPONSE
   - LLM generates answer
   - Includes source citations
   - Returns to frontend
   ↓
7. DISPLAY
   - Shows answer with sources
   - Links to original documents
```

---

## 📍 IMPORTANT FILE PATHS

### Main Application
```
backend/knowledge_chatbot.py
```

### Configuration
```
backend/.env
backend/config/
```

### Database
```
data/vector_db/
```

### Startup Scripts
```
start.bat                    # Start everything
start_backend.bat           # Backend only
check_database.bat          # Check DB status
```

---

## 🎯 QUICK REFERENCE: What Does What?

| Component | Purpose | Location |
|-----------|---------|----------|
| **Main App** | FastAPI server, query handling | `backend/knowledge_chatbot.py` |
| **LLM Manager** | Ollama model failover | `backend/llm_failover_system.py` |
| **Code Search** | GitHub indexing | `backend/github_processor.py` |
| **Extractors** | Document processing | `backend/extractors/` |
| **Database** | ChromaDB storage | `data/vector_db/` |
| **Frontend** | React UI | `frontend/src/` |
| **Config** | Settings & env vars | `backend/.env` |
| **Tests** | Test suites | `tests/` |

---

## 🚀 STARTUP SEQUENCE

### Option 1: Full System
```bash
# From project root
start.bat

# This starts:
# 1. Backend API (port 8000)
# 2. Frontend UI (port 5173)
```

### Option 2: Backend Only (for API testing)
```bash
start_backend.bat

# Access API docs:
# http://localhost:8000/docs
```

### Option 3: Manual (for debugging)
```bash
# Terminal 1 - Backend
cd backend
uvicorn knowledge_chatbot:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## 🔍 EXPLORING THE CODE

### Read the Main Application
```bash
# Open in editor
code backend/knowledge_chatbot.py

# Or view in terminal
cat backend/knowledge_chatbot.py
```

### Check Configuration
```bash
cat backend/.env
```

### View Database Structure
```bash
# After copy completes
python -c "import chromadb; client = chromadb.PersistentClient(path='D:/Claude/Projects/ScholarsTerminal/data/vector_db'); print(client.list_collections())"
```

---

## 💡 KEY CONCEPTS

### 1. **RAG (Retrieval-Augmented Generation)**
Your system uses RAG:
- **R**etrieval: Find relevant chunks from 13M documents
- **A**ugmented: Add chunks to query context
- **G**eneration: LLM creates answer with context

### 2. **Vector Embeddings**
Each document chunk becomes a vector (array of numbers):
- Similar content = Similar vectors
- Enables semantic search
- "quantum mechanics" finds related concepts

### 3. **Query Routing**
System intelligently routes queries:
- **Books:** Theory, concepts, research
- **GitHub:** Code examples, implementations
- **Hybrid:** Both when relevant

### 4. **LLM Failover**
Reliability through redundancy:
- Primary model preferred (fast)
- Fallback if primary fails (reliable)
- Always returns a response

---

## 🎓 LEARNING THE CODEBASE

### Start Here (in order):
1. **Read** `README.md` - Overall understanding
2. **Explore** `backend/knowledge_chatbot.py` - Main logic
3. **Check** `backend/.env` - Your configuration
4. **Review** `backend/llm_failover_system.py` - LLM handling
5. **Look at** `backend/extractors/` - Document processing

### Common Modifications:
- **Add new model:** Update `llm_failover_system.py`
- **Change paths:** Update `backend/.env`
- **New document type:** Add to `extractors/`
- **UI changes:** Edit `frontend/src/`

---

## 🛠️ CUSTOMIZATION POINTS

### Easy to Change:
- ✅ LLM models (PRIMARY_MODEL, FALLBACK_MODEL)
- ✅ Database path (CHROMA_DB_PATH)
- ✅ Source directories (BOOKS_PATH, GITHUB_PATH)
- ✅ API port (API_PORT)
- ✅ UI theme colors (frontend/styles/)

### Moderate Changes:
- ⚙️ Query routing logic (knowledge_chatbot.py)
- ⚙️ Chunk size (extractors/)
- ⚙️ Search results count (ChromaDB queries)

### Advanced Changes:
- 🔧 Switch to Milvus (database migration)
- 🔧 Add new data sources
- 🔧 Implement voice features
- 🔧 Add authentication

---

## 📖 NEXT STEPS

After database copy completes:

1. **Test Database**
   ```bash
   python test_installation.py
   ```

2. **Start System**
   ```bash
   start.bat
   ```

3. **Try a Query**
   - Open http://localhost:5173
   - Ask: "What does Feynman say about quantum mechanics?"

4. **Explore Code**
   - Read through `knowledge_chatbot.py`
   - Understand the query flow
   - Customize as needed

---

**Your Scholar's Terminal is a sophisticated RAG system with 13 million document chunks, intelligent query routing, LLM failover, and a clean React UI. All the code is now organized professionally and ready for use!** 🚀

---

**Last Updated:** January 8, 2025  
**Status:** Ready for exploration! (Database still copying)
