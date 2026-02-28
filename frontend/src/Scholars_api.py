"""
Scholar's Terminal - Backend API with Multi-Database Support
Bridges React frontend with multiple ChromaDB knowledge bases, Ollama, and automated research scanning

VERSION 3.0 - Multi-Database Edition
- Supports both Scholar's Terminal DB and RAG Newsletter DB
- Source filtering across all databases
- Research scanner integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import chromadb
from chromadb.config import Settings
import httpx
import asyncio
import sys
import os
from pathlib import Path

# Add research_scanner to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent  # D:\Claude\Projects\scholars-terminal
sys.path.insert(0, str(PROJECT_ROOT))

# Import research scanner components
# DISABLED: research_scanner module not available
# from research_scanner.api_routes import create_research_router
# from research_scanner.scheduler import start_scheduler

# ==================================================================
#  MULTI-DATABASE CONFIGURATION
# ==================================================================

DATABASE_CONFIGS = {
    "scholar_terminal": {
        "path": r"D:\Claude\Projects\scholars-terminal\data\scholar_terminal_db",
        "description": "Scholar's Terminal working database",
        "collections": ["books", "research_papers"]
    },
    "rag_db": {
        "path": r"D:\rag_db",
        "description": "Main knowledge base (newsletters, books)",
        "collections": ["newsletters", "knowledge_base", "docs"]
    }
}

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"

# ==================================================================
#  FASTAPI APP SETUP
# ==================================================================

app = FastAPI(title="Scholar's Terminal API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://localhost:8080", "http://localhost:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize multiple ChromaDB clients
chroma_clients = {}
print("\n[STARTUP] Initializing Multi-Database System...")
print("=" * 60)

for db_name, config in DATABASE_CONFIGS.items():
    try:
        client = chromadb.PersistentClient(
            path=config["path"],
            settings=Settings(anonymized_telemetry=False)
        )
        chroma_clients[db_name] = client
        
        collections = client.list_collections()
        total_docs = sum(c.count() for c in collections)
        
        print(f"[OK] {db_name}: {config['path']}")
        print(f"   Collections: {[c.name for c in collections]}")
        print(f"   Total Documents: {total_docs:,}")
        print()
    except Exception as e:
        print(f"[FAIL] {db_name}: Failed to connect - {e}")
        print()

print("=" * 60)
print(f"[DATABASES] Active databases: {len(chroma_clients)}/{len(DATABASE_CONFIGS)}")
print()

# ==================================================================
#  RESEARCH SCANNER INTEGRATION
# ==================================================================

# DISABLED: research_scanner module not available
# app.include_router(create_research_router(), prefix="/api/research", tags=["research"])
# print("[RESEARCH] Research Scanner routes registered at /api/research/*")
print("[RESEARCH] Research Scanner module disabled (not installed)")

# ==================================================================
#  REQUEST/RESPONSE MODELS
# ==================================================================

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[ChatMessage]
    use_knowledge_base: bool = True
    num_results: int = 5
    source_filter: str = "all"  # Options: all, scholar_terminal, rag_db, books, newsletters, research, github
    database_filter: str = "all"  # NEW: all, scholar_terminal, rag_db

class Citation(BaseModel):
    title: str
    author: Optional[str] = "Unknown"
    page: Optional[str] = "N/A"
    relevance: float
    content: str

class ChatResponse(BaseModel):
    message: ChatMessage
    citations: Optional[List[dict]] = None
    model: str
    databases_searched: List[str] = []
    
    class Config:
        arbitrary_types_allowed = True

# ==================================================================
#  MULTI-DATABASE SEARCH FUNCTIONS
# ==================================================================

def get_databases_to_search(database_filter: str) -> List[str]:
    """Determine which databases to search based on filter"""
    if database_filter == "all":
        return list(chroma_clients.keys())
    elif database_filter in chroma_clients:
        return [database_filter]
    else:
        return list(chroma_clients.keys())  # Fallback to all

def get_collections_to_search(source_filter: str, database_name: str) -> List[tuple]:
    """
    Determine which collections to search based on source filter
    Returns list of (collection_name, source_filter_value) tuples
    """
    client = chroma_clients.get(database_name)
    if not client:
        return []
    
    available_collections = [c.name for c in client.list_collections()]
    collections_to_search = []
    
    if source_filter == "all":
        # Search all available collections
        for coll_name in available_collections:
            collections_to_search.append((coll_name, None))
    
    elif source_filter == "books":
        # Search books collection
        if "books" in available_collections:
            collections_to_search.append(("books", None))
        if "knowledge_base" in available_collections:
            collections_to_search.append(("knowledge_base", None))
    
    elif source_filter == "newsletters":
        # Search newsletters collection
        if "newsletters" in available_collections:
            collections_to_search.append(("newsletters", None))
    
    elif source_filter == "research":
        # Search research papers
        if "research_papers" in available_collections:
            collections_to_search.append(("research_papers", None))
    
    elif source_filter in ["arxiv", "semantic_scholar", "huggingface", "pubmed"]:
        # Specific research source
        if "research_papers" in available_collections:
            collections_to_search.append(("research_papers", source_filter))
    
    elif source_filter == "github":
        # GitHub repos
        if "books" in available_collections:
            collections_to_search.append(("books", "github"))
    
    else:
        # Unknown filter, search all
        for coll_name in available_collections:
            collections_to_search.append((coll_name, None))
    
    return collections_to_search


def search_knowledge_base(query: str, n_results: int = 5, source_filter: str = "all", database_filter: str = "all") -> tuple:
    """
    Search across multiple databases and collections with filtering
    Returns: (citations_list, databases_searched_list)
    """
    all_citations = []
    databases_searched = []
    
    # Determine which databases to search
    databases_to_search = get_databases_to_search(database_filter)
    
    print(f"\n[SEARCH] Query: '{query[:60]}...'")
    print(f"[FILTER] Source: {source_filter}, Database: {database_filter}")
    print(f"[DATABASES] Searching: {databases_to_search}")
    
    # Search each database
    for db_name in databases_to_search:
        client = chroma_clients.get(db_name)
        if not client:
            continue
        
        databases_searched.append(db_name)
        
        # Get collections to search in this database
        collections_to_search = get_collections_to_search(source_filter, db_name)
        
        print(f"\n[{db_name.upper()}] Searching {len(collections_to_search)} collections")
        
        # Search each collection
        for collection_name, source_value in collections_to_search:
            try:
                collection = client.get_collection(name=collection_name)
                print(f"  |- {collection_name}: {collection.count():,} docs", end="")
                
                # Build query parameters
                query_params = {
                    "query_texts": [query],
                    "n_results": min(n_results * 2, 20),
                    "include": ["documents", "metadatas", "distances"]
                }
                
                # Add source filter if specified
                if source_value:
                    query_params["where"] = {"source": source_value}
                    print(f" [filter: source={source_value}]", end="")
                
                results = collection.query(**query_params)
                
                # Process results
                if results and results["documents"] and results["documents"][0]:
                    num_results = len(results["documents"][0])
                    print(f" -> {num_results} results")
                    
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        distance = results["distances"][0][i] if results["distances"] else 0
                        
                        # Convert distance to relevance score
                        relevance = max(0, 1 - (distance / 2))
                        
                        # Determine content type
                        is_research = metadata.get("content_type") == "research_paper" or \
                                     metadata.get("source") in ["arxiv", "semantic_scholar", "huggingface", "pubmed"]
                        is_newsletter = collection_name == "newsletters"
                        
                        # Build citation
                        if is_research:
                            all_citations.append({
                                "content_type": "research_paper",
                                "database": db_name,
                                "collection": collection_name,
                                "title": metadata.get("title", "Untitled Paper"),
                                "authors": metadata.get("authors", "Unknown"),
                                "source": metadata.get("source", "unknown"),
                                "published_date": metadata.get("published_date"),
                                "url": metadata.get("url", ""),
                                "relevance_score": relevance,
                                "summary_excerpt": doc[:200] + "...",
                            })
                        elif is_newsletter:
                            all_citations.append({
                                "content_type": "newsletter",
                                "database": db_name,
                                "collection": collection_name,
                                "title": metadata.get("title", "Newsletter Article"),
                                "source": metadata.get("newsletter_name", "Unknown"),
                                "date": metadata.get("date", ""),
                                "url": metadata.get("url", ""),
                                "relevance": round(relevance, 2),
                                "content": doc[:500] + "..." if len(doc) > 500 else doc,
                            })
                        else:
                            # Regular book citation
                            all_citations.append({
                                "content_type": "book",
                                "database": db_name,
                                "collection": collection_name,
                                "title": metadata.get("book", metadata.get("source", "Unknown")),
                                "author": metadata.get("author", "Unknown"),
                                "page": str(metadata.get("page", "N/A")),
                                "relevance": round(relevance, 2),
                                "content": doc[:500] + "..." if len(doc) > 500 else doc,
                            })
                else:
                    print(" -> 0 results")
                    
            except Exception as e:
                print(f" -> Error: {e}")
                continue
    
    # Sort by relevance and return top n_results
    all_citations.sort(key=lambda x: x.get("relevance_score", x.get("relevance", 0)), reverse=True)
    final_citations = all_citations[:n_results]
    
    print(f"\n[RESULTS] Total: {len(all_citations)} -> Returning top {len(final_citations)}")
    
    return final_citations, databases_searched


def build_augmented_prompt(query: str, citations: list) -> str:
    """Build a RAG-augmented prompt with context from knowledge base"""
    if not citations:
        return query
    
    context_parts = []
    for i, citation in enumerate(citations, 1):
        content_type = citation.get("content_type", "book")
        
        if content_type == "research_paper":
            title = citation.get("title", "Untitled")
            authors = citation.get("authors", "Unknown")
            summary = citation.get("summary_excerpt", "")
            context_parts.append(f"[Source {i}: Research - {title} by {authors}]\n{summary}\n")
        
        elif content_type == "newsletter":
            title = citation.get("title", "Untitled")
            source = citation.get("source", "Unknown")
            content = citation.get("content", "")
            context_parts.append(f"[Source {i}: Newsletter - {source} - {title}]\n{content}\n")
        
        else:
            # Book
            title = citation.get("title", "Untitled")
            content = citation.get("content", "")
            context_parts.append(f"[Source {i}: Book - {title}]\n{content}\n")
    
    context = "\n".join(context_parts)
    
    return f"""Based on the following sources from the knowledge base, please answer the question.

SOURCES:
{context}

QUESTION: {query}

Please provide a comprehensive answer based on the sources above."""

# ==================================================================
#  API ENDPOINTS
# ==================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    total_docs = 0
    db_stats = {}
    
    for db_name, client in chroma_clients.items():
        collections = client.list_collections()
        db_docs = sum(c.count() for c in collections)
        total_docs += db_docs
        db_stats[db_name] = {
            "collections": len(collections),
            "documents": db_docs
        }
    
    return {
        "status": "online",
        "service": "Scholar's Terminal API v3.0 (Multi-Database Edition)",
        "databases_connected": len(chroma_clients),
        "total_documents": total_docs,
        "database_stats": db_stats,
        "ollama_url": OLLAMA_URL,
    }


@app.get("/api/databases")
async def list_databases():
    """List all connected databases and their collections"""
    databases = []
    
    for db_name, client in chroma_clients.items():
        collections = client.list_collections()
        databases.append({
            "name": db_name,
            "path": DATABASE_CONFIGS[db_name]["path"],
            "description": DATABASE_CONFIGS[db_name]["description"],
            "collections": [
                {"name": c.name, "count": c.count()} 
                for c in collections
            ],
            "total_documents": sum(c.count() for c in collections)
        })
    
    return {"databases": databases}


@app.get("/api/tags")
async def get_models():
    """Proxy to Ollama's model list"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OLLAMA_URL}/api/tags", timeout=10.0)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Ollama not available: {e}")


@app.post("/api/search")
async def search(query: str, n_results: int = 5, source_filter: str = "all", database_filter: str = "all"):
    """Search across multiple databases with filtering"""
    citations, databases_searched = search_knowledge_base(query, n_results, source_filter, database_filter)
    return {
        "query": query, 
        "results": citations, 
        "source_filter": source_filter,
        "database_filter": database_filter,
        "databases_searched": databases_searched
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with multi-database RAG augmentation"""
    
    # Get the latest user message
    user_message = request.messages[-1].content if request.messages else ""
    
    # Search knowledge base if enabled
    citations = []
    databases_searched = []
    augmented_messages = request.messages.copy()
    
    if request.use_knowledge_base and user_message:
        citations, databases_searched = search_knowledge_base(
            user_message, 
            request.num_results, 
            request.source_filter,
            request.database_filter
        )
        
        if citations:
            # Replace the last user message with the augmented version
            augmented_prompt = build_augmented_prompt(user_message, citations)
            augmented_messages[-1] = ChatMessage(role="user", content=augmented_prompt)
    
    # Call Ollama
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": request.model,
                    "messages": [{"role": m.role, "content": m.content} for m in augmented_messages],
                    "stream": False,
                    "keep_alive": "10m"
                },
                timeout=300.0
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
                model=request.model,
                databases_searched=databases_searched
            )
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Ollama request timed out")
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Ollama error: {e}")


if __name__ == "__main__":
    import uvicorn
    print("\n[STARTUP] Starting Scholar's Terminal API v3.0...")
    print(f"[API] http://localhost:8000")
    print(f"[DOCS] http://localhost:8000/docs")
    print(f"[RESEARCH] http://localhost:8000/api/research/status\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
