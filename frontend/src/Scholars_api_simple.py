"""
Scholar's Terminal - Backend API with Multi-Database Support (Simplified)
No research_scanner dependency - pure multi-database RAG system
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import chromadb
from chromadb.config import Settings
import httpx

# ==================================================================
#  MULTI-DATABASE CONFIGURATION
# ==================================================================

DATABASE_CONFIGS = {
    "scholar_terminal": {
        "path": r"D:\Claude\Projects\scholars-terminal\data\scholar_terminal_db",
        "description": "Scholar's Terminal working database",
    },
    "rag_db": {
        "path": r"D:\rag_db",
        "description": "Main knowledge base (newsletters, books)",
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
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://localhost:8080", "http://localhost:9000", "http://localhost:49152", "http://localhost:50000"],
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
        print(f"[ERROR] {db_name}: Failed to connect - {e}")
        print()

print("=" * 60)
print(f"[DATABASES] Active databases: {len(chroma_clients)}/{len(DATABASE_CONFIGS)}")
print()

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
    source_filter: str = "all"
    database_filter: str = "all"

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
        return list(chroma_clients.keys())

def get_collections_to_search(source_filter: str, database_name: str) -> List[tuple]:
    """Determine which collections to search"""
    client = chroma_clients.get(database_name)
    if not client:
        return []
    
    available_collections = [c.name for c in client.list_collections()]
    collections_to_search = []
    
    if source_filter == "all":
        for coll_name in available_collections:
            collections_to_search.append((coll_name, None))
    elif source_filter == "books":
        if "books" in available_collections:
            collections_to_search.append(("books", None))
        if "knowledge_base" in available_collections:
            collections_to_search.append(("knowledge_base", None))
    elif source_filter == "newsletters":
        if "newsletters" in available_collections:
            collections_to_search.append(("newsletters", None))
    elif source_filter == "research":
        if "research_papers" in available_collections:
            collections_to_search.append(("research_papers", None))
    else:
        for coll_name in available_collections:
            collections_to_search.append((coll_name, None))
    
    return collections_to_search

def search_knowledge_base(query: str, n_results: int = 5, source_filter: str = "all", database_filter: str = "all") -> tuple:
    """Search across multiple databases"""
    all_citations = []
    databases_searched = []
    
    databases_to_search = get_databases_to_search(database_filter)
    
    print(f"\n[SEARCH] Query: '{query[:60]}...'")
    print(f"[DATABASES] Searching: {databases_to_search}")
    
    for db_name in databases_to_search:
        client = chroma_clients.get(db_name)
        if not client:
            continue
        
        databases_searched.append(db_name)
        collections_to_search = get_collections_to_search(source_filter, db_name)
        
        for collection_name, source_value in collections_to_search:
            try:
                collection = client.get_collection(name=collection_name)
                
                query_params = {
                    "query_texts": [query],
                    "n_results": min(n_results * 2, 20),
                    "include": ["documents", "metadatas", "distances"]
                }
                
                if source_value:
                    query_params["where"] = {"source": source_value}
                
                results = collection.query(**query_params)
                
                if results and results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        distance = results["distances"][0][i] if results["distances"] else 0
                        relevance = max(0, 1 - (distance / 2))
                        
                        is_newsletter = collection_name == "newsletters"
                        
                        if is_newsletter:
                            all_citations.append({
                                "content_type": "newsletter",
                                "database": db_name,
                                "title": metadata.get("title", "Newsletter Article"),
                                "source": metadata.get("newsletter_name", "Unknown"),
                                "date": metadata.get("date", ""),
                                "url": metadata.get("url", ""),
                                "relevance": round(relevance, 2),
                                "content": doc[:500] + "..." if len(doc) > 500 else doc,
                            })
                        else:
                            all_citations.append({
                                "content_type": "book",
                                "database": db_name,
                                "title": metadata.get("book", metadata.get("source", "Unknown")),
                                "author": metadata.get("author", "Unknown"),
                                "page": str(metadata.get("page", "N/A")),
                                "relevance": round(relevance, 2),
                                "content": doc[:500] + "..." if len(doc) > 500 else doc,
                            })
                    
            except Exception as e:
                print(f"[ERROR] {collection_name}: {e}")
                continue
    
    all_citations.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    return all_citations[:n_results], databases_searched

def build_augmented_prompt(query: str, citations: list) -> str:
    """Build RAG prompt with context"""
    if not citations:
        return query
    
    context_parts = []
    for i, citation in enumerate(citations, 1):
        content_type = citation.get("content_type", "book")
        
        if content_type == "newsletter":
            title = citation.get("title", "Untitled")
            source = citation.get("source", "Unknown")
            content = citation.get("content", "")
            context_parts.append(f"[Source {i}: Newsletter - {source} - {title}]\n{content}\n")
        else:
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
    """Health check"""
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
        "service": "Scholar's Terminal API v3.0 (Multi-Database)",
        "databases_connected": len(chroma_clients),
        "total_documents": total_docs,
        "database_stats": db_stats,
    }

@app.get("/api/models")
async def get_models():
    """Get Ollama models"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OLLAMA_URL}/api/tags", timeout=10.0)
            data = response.json()
            return {"models": data.get("models", [])}
        except Exception as e:
            return {"models": [{"name": DEFAULT_MODEL}]}

@app.post("/api/search")
async def search(query: str, n_results: int = 5, source_filter: str = "all", database_filter: str = "all"):
    """Search databases"""
    citations, databases_searched = search_knowledge_base(query, n_results, source_filter, database_filter)
    return {
        "query": query, 
        "results": citations, 
        "databases_searched": databases_searched
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat with RAG"""
    user_message = request.messages[-1].content if request.messages else ""
    
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
            augmented_prompt = build_augmented_prompt(user_message, citations)
            augmented_messages[-1] = ChatMessage(role="user", content=augmented_prompt)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": request.model,
                    "messages": [{"role": m.role, "content": m.content} for m in augmented_messages],
                    "stream": False,
                },
                timeout=300.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code)
            
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
            
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Ollama error: {e}")

if __name__ == "__main__":
    import uvicorn
    print("\n[STARTUP] Starting Scholar's Terminal API v3.0...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
