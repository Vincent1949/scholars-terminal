"""
Scholar's Terminal - Backend API
Bridges React frontend with ChromaDB knowledge base and Ollama
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import chromadb
from chromadb.config import Settings
import httpx
import asyncio

# Configuration
CHROMA_DB_PATH = r"D:\Claude\Projects\scholars-terminal\data\vector_db"
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"

app = FastAPI(title="Scholar's Terminal API", version="1.0.0")

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
    print(f"✅ Connected to ChromaDB at {CHROMA_DB_PATH}")
    
    # List available collections
    collections = chroma_client.list_collections()
    print(f"📚 Available collections: {[c.name for c in collections]}")
except Exception as e:
    print(f"❌ Failed to connect to ChromaDB: {e}")
    chroma_client = None


# Request/Response Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[ChatMessage]
    use_knowledge_base: bool = True
    num_results: int = 5

class Citation(BaseModel):
    title: str
    author: Optional[str] = "Unknown"
    page: Optional[str] = "N/A"
    relevance: float
    content: str

class ChatResponse(BaseModel):
    message: ChatMessage
    citations: Optional[List[Citation]] = None
    model: str


def get_collection():
    """Get the knowledge base collection"""
    if not chroma_client:
        return None
    
    # Try common collection names
    collection_names = ["knowledge_base", "books", "documents", "default"]
    
    for name in collection_names:
        try:
            collection = chroma_client.get_collection(name=name)
            print(f"📖 Using collection: {name} ({collection.count()} documents)")
            return collection
        except:
            continue
    
    # If no named collection, try to get the first available
    collections = chroma_client.list_collections()
    if collections:
        collection = collections[0]
        print(f"📖 Using first available collection: {collection.name}")
        return collection
    
    return None


def search_knowledge_base(query: str, n_results: int = 5) -> List[Citation]:
    """Search ChromaDB for relevant documents"""
    collection = get_collection()
    if not collection:
        return []
    
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        citations = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0
                
                # Convert distance to relevance score (0-1, higher is better)
                relevance = max(0, 1 - (distance / 2))
                
                citations.append(Citation(
                    title=metadata.get("book", metadata.get("source", metadata.get("filename", "Unknown Source"))),
                    author=metadata.get("author", "Unknown"),
                    page=str(metadata.get("page", metadata.get("chunk_id", "N/A"))),
                    relevance=round(relevance, 2),
                    content=doc[:500] + "..." if len(doc) > 500 else doc
                ))
        
        return citations
    
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []


def build_augmented_prompt(query: str, citations: List[Citation]) -> str:
    """Build a RAG-augmented prompt with context from knowledge base"""
    if not citations:
        return query
    
    context_parts = []
    for i, citation in enumerate(citations, 1):
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
        "service": "Scholar's Terminal API",
        "chromadb_connected": chroma_client is not None,
        "document_count": doc_count,
        "ollama_url": OLLAMA_URL
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
async def search(query: str, n_results: int = 5):
    """Search the knowledge base"""
    citations = search_knowledge_base(query, n_results)
    return {"query": query, "results": citations}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with optional RAG augmentation"""
    
    # Get the latest user message
    user_message = request.messages[-1].content if request.messages else ""
    
    # Search knowledge base if enabled
    citations = []
    augmented_messages = request.messages.copy()
    
    if request.use_knowledge_base and user_message:
        citations = search_knowledge_base(user_message, request.num_results)
        
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
    print("\n🎓 Starting Scholar's Terminal API...")
    print(f"📚 ChromaDB: {CHROMA_DB_PATH}")
    print(f"🤖 Ollama: {OLLAMA_URL}")
    print(f"🌐 API: http://localhost:8000")
    print(f"📖 Docs: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)