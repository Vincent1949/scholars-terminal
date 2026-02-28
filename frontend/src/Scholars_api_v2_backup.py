"""
Scholar's Terminal - Backend API with Research Scanner Integration
Bridges React frontend with ChromaDB knowledge base, Ollama, and automated research scanning
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import chromadb
from chromadb.config import Settings
import httpx
import asyncio
import sys
import os
from pathlib import Path

# Add research_scanner to Python path
# __file__ is in frontend/src/, go up 2 levels to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent  # D:\Claude\Projects\scholars-terminal
sys.path.insert(0, str(PROJECT_ROOT))  # Add project root to path

# Import research scanner components
from research_scanner.api_routes import create_research_router
from research_scanner.scheduler import start_scheduler

# Configuration
CHROMA_DB_PATH = r"D:\Claude\Projects\scholars-terminal\data\vector_db"
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"

app = FastAPI(title="Scholar's Terminal API", version="2.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ChromaDB client
try:
    chroma_client = chromadb.PersistentClient(
        path=CHROMA_DB_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    print(f"[OK] Connected to ChromaDB at {CHROMA_DB_PATH}")
    
    # List available collections
    collections = chroma_client.list_collections()
    print(f"[COLLECTIONS] Available collections: {[c.name for c in collections]}")
except Exception as e:
    print(f"[ERROR] Failed to connect to ChromaDB: {e}")
    chroma_client = None


# ==================================================================
#  RESEARCH SCANNER INTEGRATION
# ==================================================================

# Add research scanner API routes
app.include_router(create_research_router(), prefix="/api/research", tags=["research"])
print("[RESEARCH] Research Scanner routes registered at /api/research/*")

# Start background scheduler (optional - uncomment to enable)
# This will scan daily at 3 AM + once on startup
# scheduler = start_scheduler()
# print("[SCHEDULER] Research Scanner scheduler started (daily at 3 AM)")

# ==================================================================
#  ORIGINAL SCHOLAR'S TERMINAL API (unchanged)
# ==================================================================

# Request/Response Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[ChatMessage]
    use_knowledge_base: bool = True
    num_results: int = 5
    source_filter: str = "all"  # NEW: all, books, research, arxiv, semantic_scholar, huggingface, pubmed

class Citation(BaseModel):
    title: str
    author: Optional[str] = "Unknown"
    page: Optional[str] = "N/A"
    relevance: float
    content: str

class ChatResponse(BaseModel):
    message: ChatMessage
    citations: Optional[List[dict]] = None  # Changed to dict to support both book and research paper formats
    model: str
    
    class Config:
        arbitrary_types_allowed = True


def get_collection():
    """Get the knowledge base collection"""
    if not chroma_client:
        return None
    
    # Try common collection names
    collection_names = ["knowledge_base", "books", "documents", "default"]
    
    for name in collection_names:
        try:
            collection = chroma_client.get_collection(name=name)
            print(f"[COLLECTION] Using collection: {name} ({collection.count()} documents)")
            return collection
        except:
            continue
    
    # If no named collection, try to get the first available
    collections = chroma_client.list_collections()
    if collections:
        collection = collections[0]
        print(f"[COLLECTION] Using first available collection: {collection.name}")
        return collection
    
    return None


def search_knowledge_base(query: str, n_results: int = 5, source_filter: str = "all") -> list:
    """Search ChromaDB for relevant documents with source filtering"""
    if not chroma_client:
        return []
    
    try:
        all_citations = []
        
        # Determine which collections to search based on filter
        if source_filter == "all":
            # Search both books and research papers
            collections_to_search = [("books", None, None), ("research_papers", None, None)]
        elif source_filter == "books-only":
            # Only books (filter by source in metadata - compatible with current DB)
            collections_to_search = [("books", None, "book")]
        elif source_filter == "github":
            # Only GitHub repos (filter by source in metadata - compatible with current DB)
            collections_to_search = [("books", None, "github")]
        elif source_filter == "books":
            # Legacy: both books and github from books collection
            collections_to_search = [("books", None, None)]
        elif source_filter == "research":
            # All research papers, no source filter
            collections_to_search = [("research_papers", None, None)]
        elif source_filter in ["arxiv", "semantic_scholar", "huggingface", "pubmed"]:
            # Specific research source
            collections_to_search = [("research_papers", source_filter, None)]
        else:
            collections_to_search = [("books", None, None)]
        
        # Search each collection
        for collection_name, source_name, source_type in collections_to_search:
            try:
                collection = chroma_client.get_collection(name=collection_name)
                print(f"[SEARCH] Searching collection: {collection_name} ({collection.count()} docs)")
            except Exception as e:
                print(f"[WARN] Could not get collection {collection_name}: {e}")
                continue  # Collection doesn't exist, skip it
            
            # Build query params
            query_params = {
                "query_texts": [query],
                "n_results": min(n_results * 2, 20),  # Get more results, filter later
                "include": ["documents", "metadatas", "distances"]
            }
            
            # Add source filter if specified (books-only or github)
            if source_type:
                # Use 'source' field for current database compatibility
                query_params["where"] = {"source": source_type}
                print(f"[FILTER] Filtering by source={source_type}")
                results = collection.query(**query_params)
            # Or add source filter if specified (for research papers)
            elif source_name:
                try:
                    # Try with exact source match first
                    query_params["where"] = {"source": source_name}
                    results = collection.query(**query_params)
                    
                    # If no results, try without filter as fallback
                    if not results or not results["documents"] or not results["documents"][0]:
                        print(f"⚠️  No results with source={source_name}, trying without filter...")
                        del query_params["where"]
                        results = collection.query(**query_params)
                except Exception as e:
                    print(f"⚠️  Source filter failed, trying without: {e}")
                    if "where" in query_params:
                        del query_params["where"]
                    results = collection.query(**query_params)
            else:
                # No source filter, just search
                results = collection.query(**query_params)
            
            # Process results
            print(f"✅ Collection {collection_name}: {len(results['documents'][0]) if results and results['documents'] else 0} results")
            
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    # If we have a source filter, check if this result matches
                    if source_name and metadata.get("source") != source_name:
                        continue  # Skip non-matching sources
                    
                    # Convert distance to relevance score (0-1, higher is better)
                    relevance = max(0, 1 - (distance / 2))
                    
                    # Check if this is a research paper or book
                    is_research = metadata.get("content_type") == "research_paper" or \
                                 metadata.get("source") in ["arxiv", "semantic_scholar", "huggingface", "pubmed"]
                    
                    if is_research:
                        # Research paper citation with rich metadata
                        all_citations.append({
                            "content_type": "research_paper",
                            "title": metadata.get("title", "Untitled Paper"),
                            "authors": metadata.get("authors", "Unknown"),
                            "source": metadata.get("source", "unknown"),
                            "published_date": metadata.get("published_date"),
                            "url": metadata.get("url", ""),
                            "paper_id": metadata.get("paper_id", ""),
                            "citation_count": metadata.get("citation_count", 0),
                            "relevance_score": metadata.get("relevance_score", relevance),
                            "topics": metadata.get("topics", ""),
                            "summary_excerpt": metadata.get("summary_excerpt", doc[:200] + "..."),
                            "chunk_id": metadata.get("chunk_id", ""),
                        })
                    else:
                        # Regular book citation
                        all_citations.append({
                            "content_type": "book",
                            "title": metadata.get("book", metadata.get("source", metadata.get("filename", "Unknown Source"))),
                            "author": metadata.get("author", "Unknown"),
                            "page": str(metadata.get("page", metadata.get("chunk_id", "N/A"))),
                            "relevance": round(relevance, 2),
                            "content": doc[:500] + "..." if len(doc) > 500 else doc,
                            "chunk_id": metadata.get("chunk_id", ""),
                        })
        
        # Sort by relevance and return top n_results
        all_citations.sort(key=lambda x: x.get("relevance_score", x.get("relevance", 0)), reverse=True)
        final_citations = all_citations[:n_results]
        
        print(f"[RESULTS] Returning {len(final_citations)} citations (from {len(all_citations)} total)")
        if final_citations:
            print(f"   Top citation: {final_citations[0].get('title', 'Unknown')[:50]}...")
        
        return final_citations
    
    except Exception as e:
        print(f"[ERROR] Search error: {e}")
        import traceback
        traceback.print_exc()
        return []


def build_augmented_prompt(query: str, citations: list) -> str:
    """Build a RAG-augmented prompt with context from knowledge base"""
    if not citations:
        return query
    
    context_parts = []
    for i, citation in enumerate(citations, 1):
        # Handle both dict and Citation object formats
        if isinstance(citation, dict):
            content_type = citation.get("content_type", "book")
            
            if content_type == "research_paper":
                # Research paper format
                title = citation.get("title", "Untitled")
                authors = citation.get("authors", "Unknown")
                summary = citation.get("summary_excerpt", "")
                context_parts.append(f"[Source {i}: {title} by {authors}]\n{summary}\n")
            else:
                # Book format
                title = citation.get("title", "Untitled")
                content = citation.get("content", "")
                context_parts.append(f"[Source {i}: {title}]\n{content}\n")
        else:
            # Legacy Citation object
            context_parts.append(f"[Source {i}: {citation.title}]\n{citation.content}\n")
    
    context = "\n".join(context_parts)
    
    augmented_prompt = f"""Based on the following sources from the knowledge base, please answer the question.

SOURCES:
{context}

QUESTION: {query}

Please provide a comprehensive answer based on the sources above. If the sources don't contain relevant information, you may supplement with your general knowledge but indicate when you're doing so."""
    
    return augmented_prompt


@app.get("/")
async def root():
    """Health check endpoint"""
    collection = get_collection()
    doc_count = collection.count() if collection else 0
    
    return {
        "status": "online",
        "service": "Scholar's Terminal API v2.0 (with Research Scanner)",
        "chromadb_connected": chroma_client is not None,
        "document_count": doc_count,
        "ollama_url": OLLAMA_URL,
        "research_scanner": "enabled"
    }


@app.get("/api/tags")
async def get_models():
    """Proxy to Ollama's model list"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OLLAMA_URL}/api/tags", timeout=10.0)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Ollama not available: {e}")


@app.get("/api/collections")
async def list_collections():
    """List available ChromaDB collections"""
    if not chroma_client:
        raise HTTPException(status_code=503, detail="ChromaDB not connected")
    
    collections = chroma_client.list_collections()
    return {
        "collections": [
            {"name": c.name, "count": c.count()} 
            for c in collections
        ]
    }


@app.post("/api/search")
async def search(query: str, n_results: int = 5, source_filter: str = "all"):
    """Search the knowledge base with optional source filtering"""
    citations = search_knowledge_base(query, n_results, source_filter)
    return {"query": query, "results": citations, "source_filter": source_filter}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with optional RAG augmentation"""
    
    # Get the latest user message
    user_message = request.messages[-1].content if request.messages else ""
    
    # Search knowledge base if enabled
    citations = []
    augmented_messages = request.messages.copy()
    
    if request.use_knowledge_base and user_message:
        print(f"[SEARCH] Searching knowledge base: query='{user_message[:50]}...', filter={request.source_filter}")
        citations = search_knowledge_base(user_message, request.num_results, request.source_filter)
        print(f"[CITATIONS] Found {len(citations)} citations")
        
        if citations:
            # Replace the last user message with the augmented version
            augmented_prompt = build_augmented_prompt(user_message, citations)
            augmented_messages[-1] = ChatMessage(role="user", content=augmented_prompt)
        else:
            print("[WARN] No citations found, using original query")
    
    # Call Ollama
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": request.model,
                    "messages": [{"role": m.role, "content": m.content} for m in augmented_messages],
                    "stream": False,
                    "keep_alive": "10m"  # Keep model loaded for 10 minutes
                },
                timeout=300.0  # 5 minute timeout for long RAG responses
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Ollama request failed")
            
            data = response.json()
            
            return ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content=data["message"]["content"]
                ),
                citations=citations if citations else None,
                model=request.model
            )
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Ollama request timed out")
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Ollama error: {e}")


if __name__ == "__main__":
    import uvicorn
    print("\n[STARTUP] Starting Scholar's Terminal API v2.0 (with Research Scanner)...")
    print(f"[DB] ChromaDB: {CHROMA_DB_PATH}")
    print(f"[LLM] Ollama: {OLLAMA_URL}")
    print(f"[API] API: http://localhost:8000")
    print(f"[DOCS] Docs: http://localhost:8000/docs")
    print(f"[RESEARCH] Research API: http://localhost:8000/api/research/status\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
