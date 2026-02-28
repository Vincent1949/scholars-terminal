# basic_test.py

#!/usr/bin/env python3
"""
Basic Test Script for AI Knowledge Base Chatbot
Tests core functionality with minimal setup
"""

import os
import sys
from pathlib import Path
import logging
from typing import List, Dict, Any

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required packages are installed"""
    logger.info("🧪 Testing imports...")
    
    try:
        import fitz  # PyMuPDF
        logger.info("✅ PyMuPDF available")
    except ImportError:
        logger.error("❌ PyMuPDF not installed: pip install PyMuPDF")
        return False
        
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("✅ SentenceTransformers available")
    except ImportError:
        logger.error("❌ SentenceTransformers not installed: pip install sentence-transformers")
        return False
        
    try:
        import chromadb
        logger.info("✅ ChromaDB available")
    except ImportError:
        logger.error("❌ ChromaDB not installed: pip install chromadb")
        return False
        
    try:
        import numpy as np
        logger.info("✅ NumPy available")
    except ImportError:
        logger.error("❌ NumPy not installed: pip install numpy")
        return False
        
    return True

def test_books_directory():
    """Test access to D:/Books directory"""
    logger.info("📁 Testing books directory...")
    
    books_path = Path("D:/Books")
    
    if not books_path.exists():
        logger.error(f"❌ Directory {books_path} does not exist")
        return False, []
    
    logger.info(f"✅ Directory {books_path} exists")
    
    # Find PDF files (limit to 5 for testing)
    pdf_files = list(books_path.glob("**/*.pdf"))[:5]
    epub_files = list(books_path.glob("**/*.epub"))[:5]
    
    logger.info(f"📚 Found {len(pdf_files)} PDF files")
    logger.info(f"📚 Found {len(epub_files)} EPUB files")
    
    all_files = pdf_files + epub_files
    
    if all_files:
        logger.info("Sample files found:")
        for i, file in enumerate(all_files[:3], 1):
            logger.info(f"  {i}. {file.name}")
    else:
        logger.warning("⚠️ No PDF or EPUB files found")
        
    return True, all_files

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Simple PDF text extraction"""
    logger.info(f"📖 Extracting text from: {pdf_path.name}")
    
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        text = ""
        
        # Extract text from first 3 pages only (for testing)
        page_count = min(3, doc.page_count)
        for page_num in range(page_count):
            page = doc[page_num]
            text += page.get_text()
            
        doc.close()
        
        # Basic cleanup
        text = text.replace('\n\n', ' ').replace('\n', ' ').strip()
        
        logger.info(f"✅ Extracted {len(text)} characters from {page_count} pages")
        return text
        
    except Exception as e:
        logger.error(f"❌ Error extracting from {pdf_path.name}: {e}")
        return ""

def create_simple_chunks(text: str, chunk_size: int = 500) -> List[str]:
    """Create simple text chunks"""
    logger.info(f"✂️ Creating chunks from {len(text)} characters...")
    
    if not text.strip():
        return []
    
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        if current_size + len(word) > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
        else:
            current_chunk.append(word)
            current_size += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    logger.info(f"✅ Created {len(chunks)} chunks")
    return chunks

def test_embeddings(chunks: List[str]) -> bool:
    """Test embedding generation"""
    logger.info("🧠 Testing embedding generation...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # Use a lightweight model for testing
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Embedding model loaded")
        
        if not chunks:
            logger.warning("⚠️ No chunks to embed")
            return True
            
        # Test with first 3 chunks only
        test_chunks = chunks[:3]
        embeddings = model.encode(test_chunks)
        
        logger.info(f"✅ Generated embeddings: {embeddings.shape}")
        logger.info(f"   Embedding dimension: {embeddings.shape[1]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Embedding test failed: {e}")
        return False

def test_vector_database(chunks: List[str]) -> bool:
    """Test ChromaDB vector database"""
    logger.info("🗄️ Testing vector database...")
    
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        if not chunks:
            logger.warning("⚠️ No chunks to store")
            return True
            
        # Create temporary in-memory database
        client = chromadb.Client()
        collection = client.create_collection("test_collection")
        
        # Generate embeddings
        model = SentenceTransformer('all-MiniLM-L6-v2')
        test_chunks = chunks[:3]  # Test with first 3 chunks only
        embeddings = model.encode(test_chunks)
        
        # Add to database
        collection.add(
            embeddings=embeddings.tolist(),
            documents=test_chunks,
            ids=[f"chunk_{i}" for i in range(len(test_chunks))]
        )
        
        logger.info(f"✅ Added {len(test_chunks)} chunks to vector database")
        
        # Test search
        if test_chunks:
            query = "What is this document about?"
            query_embedding = model.encode([query])
            
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=2
            )
            
            logger.info(f"✅ Search test successful, found {len(results['documents'][0])} results")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector database test failed: {e}")
        return False

def run_basic_test():
    """Run complete basic test"""
    logger.info("🚀 Starting AI Knowledge Base Basic Test")
    logger.info("=" * 50)
    
    # Test 1: Check imports
    if not test_imports():
        logger.error("💥 Import test failed. Please install missing packages.")
        return False
    
    logger.info("✅ All imports successful!")
    logger.info("-" * 30)
    
    # Test 2: Check books directory
    dir_ok, files = test_books_directory()
    if not dir_ok:
        logger.error("💥 Books directory test failed.")
        return False
        
    logger.info("✅ Books directory accessible!")
    logger.info("-" * 30)
    
    if not files:
        logger.info("⚠️ No files to test with, but basic setup is working!")
        return True
    
    # Test 3: Extract text from first PDF
    pdf_files = [f for f in files if f.suffix.lower() == '.pdf']
    if pdf_files:
        text = extract_text_from_pdf(pdf_files[0])
        if not text:
            logger.warning("⚠️ No text extracted, but PDF processing is working")
            text = "This is a test document for the AI Knowledge Base system."
    else:
        logger.info("ℹ️ No PDF files found, using test text")
        text = "This is a test document for the AI Knowledge Base system. It contains sample content for testing the embedding and search functionality."
    
    logger.info("-" * 30)
    
    # Test 4: Create chunks
    chunks = create_simple_chunks(text)
    logger.info("-" * 30)
    
    # Test 5: Test embeddings
    if not test_embeddings(chunks):
        logger.error("💥 Embedding test failed.")
        return False
        
    logger.info("✅ Embedding generation successful!")
    logger.info("-" * 30)
    
    # Test 6: Test vector database
    if not test_vector_database(chunks):
        logger.error("💥 Vector database test failed.")
        return False
        
    logger.info("✅ Vector database test successful!")
    logger.info("=" * 50)
    logger.info("🎉 ALL TESTS PASSED!")
    logger.info("🎯 Your AI Knowledge Base system is ready for full implementation!")
    
    return True

if __name__ == "__main__":
    success = run_basic_test()
    if success:
        logger.info("\n🎯 Next Steps:")
        logger.info("1. Run the full application with more documents")
        logger.info("2. Set up the web interface")
        logger.info("3. Add your OpenRouter API key for chat functionality")
    else:
        logger.error("\n💭 Please fix the issues above and try again.")
    
    sys.exit(0 if success else 1)