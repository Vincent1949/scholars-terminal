# knowledge_chatbot.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Knowledge Base Chatbot - Complete Memory Optimized Edition
Enhanced with real embeddings, better memory management, and robust error handling.
"""

import os
import gc
import json
import time
import uuid
import hashlib
import logging
import sqlite3
import traceback
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import gradio as gr
import chromadb
import fitz  # PyMuPDF
import numpy as np

# Optional dependencies with safe fallback
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    ebooklib = None
    epub = None
    EPUB_AVAILABLE = False

try:
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    VOICE_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

# Logging Setup
LOGS_DIR = Path("./logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("kb_chatbot")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    from logging.handlers import RotatingFileHandler
    fh = RotatingFileHandler(
        LOGS_DIR / "chatbot.log", 
        maxBytes=10_000_000, 
        backupCount=5
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def log_memory_usage(operation: str = ""):
    """Log current memory usage for debugging"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"Memory usage {operation}: {memory_mb:.1f} MB")
    except ImportError:
        pass

# Configuration
CONFIG_PATH = Path("./config.yaml")

def load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load YAML configuration with fallback to defaults"""
    default_config = {
        "providers": {
            "embeddings": ["openai", "sentence_transformers", "local"],
            "llms": ["openai", "local"]
        },
        "thresholds": {
            "max_failures_before_backoff": 3,
            "backoff_base_seconds": 0.2
        },
        "processing": {
            "max_pages_per_pdf": 20,
            "chunk_size": 800,
            "chunk_overlap": 150,
            "batch_size": 100,
            "memory_cleanup_interval": 50
        },
        "chromadb": {
            "collection_name": "knowledge_chunks",
            "distance_function": "cosine",
            "persist_directory": "./data/vector_db"
        }
    }
    
    if not YAML_AVAILABLE or not path.exists():
        logger.warning(f"Using default config")
        return default_config
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        
        def deep_merge(default: dict, user: dict) -> dict:
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        return deep_merge(default_config, user_config)
        
    except Exception as e:
        logger.warning(f"Could not load config.yaml: {e}")
        return default_config

CONFIG = load_yaml_config(CONFIG_PATH)

# Enhanced Embedding Manager
class EnhancedEmbeddingManager:
    """Manages multiple embedding providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_order = config.get("providers", {}).get("embeddings", ["sentence_transformers", "local"])
        self.failure_counts = defaultdict(int)
        self.current_provider = None
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize embedding providers"""
        
        if OPENAI_AVAILABLE and "openai" in self.provider_order:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.providers["openai"] = self._embed_openai
                    logger.info("OpenAI embeddings initialized")
                except Exception as e:
                    logger.warning(f"OpenAI failed: {e}")
        
        if SENTENCE_TRANSFORMERS_AVAILABLE and "sentence_transformers" in self.provider_order:
            try:
                model_name = "all-MiniLM-L6-v2"
                self.sentence_model = SentenceTransformer(model_name)
                self.providers["sentence_transformers"] = self._embed_sentence_transformers
                logger.info(f"Sentence Transformers initialized with {model_name}")
            except Exception as e:
                logger.warning(f"Sentence Transformers failed: {e}")
        
        if "local" in self.provider_order:
            self.providers["local"] = self._embed_stub
            logger.info("Stub embeddings available as fallback")
        
        for provider in self.provider_order:
            if provider in self.providers:
                self.current_provider = provider
                break
                
        if not self.current_provider:
            raise RuntimeError("No embedding providers available")
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """OpenAI embeddings"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.embeddings.create(
                input=texts,
                model="text-embedding-ada-002"
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    def _embed_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Sentence Transformers embeddings"""
        try:
            embeddings = self.sentence_model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Sentence Transformers failed: {e}")
            raise
    
    def _embed_stub(self, texts: List[str]) -> List[List[float]]:
        """Fallback stub embeddings"""
        embeddings = []
        for text in texts:
            hash_obj = hashlib.sha256(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            dim = 384
            embedding = []
            for i in range(dim):
                byte_idx = i % len(hash_bytes)
                embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
            embeddings.append(embedding)
        return embeddings
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed texts with failover"""
        if not texts:
            return []
        
        for provider in self.provider_order:
            if provider not in self.providers:
                continue
            try:
                embeddings = self.providers[provider](texts)
                self.current_provider = provider
                if provider in self.failure_counts:
                    self.failure_counts[provider] = 0
                return embeddings
            except Exception as e:
                self.failure_counts[provider] += 1
                logger.warning(f"Provider '{provider}' failed: {e}")
        
        raise RuntimeError("All embedding providers failed")
    
    def embed_one(self, text: str) -> List[float]:
        """Embed single text"""
        return self.embed([text])[0]
    
    def get_status(self) -> Dict[str, Any]:
        """Get status"""
        return {
            "current_provider": self.current_provider,
            "available_providers": list(self.providers.keys()),
            "failure_counts": dict(self.failure_counts),
            "provider_order": self.provider_order
        }

# Document Processor
class MemoryOptimizedDocumentProcessor:
    """Enhanced document processor"""
    
    def __init__(self, books_directory: str = "D:/Books", config: Dict[str, Any] = None):
        self.books_directory = Path(books_directory)
        self.config = config or {}
        self.processing_config = self.config.get("processing", {})
        
        self.supported_formats = [".pdf", ".epub"]
        self.max_pages_per_pdf = self.processing_config.get("max_pages_per_pdf", 20)
        self.chunk_size = self.processing_config.get("chunk_size", 800)
        self.chunk_overlap = self.processing_config.get("chunk_overlap", 150)
        self.memory_cleanup_interval = self.processing_config.get("memory_cleanup_interval", 50)
        
        self.processed_count = 0
        
        logger.info(f"Document processor initialized: {self.books_directory}")
        logger.info(f"Config: max_pages={self.max_pages_per_pdf}, chunk_size={self.chunk_size}")
    
    def find_all_documents(self) -> List[Path]:
        """Find all supported documents"""
        if not self.books_directory.exists():
            logger.error(f"Directory {self.books_directory} does not exist!")
            return []
        
        logger.info(f"Scanning {self.books_directory} for documents...")
        
        all_files = []
        for ext in self.supported_formats:
            pattern = f"**/*{ext}"
            files = list(self.books_directory.glob(pattern))
            all_files.extend(files)
            logger.info(f"Found {len(files)} {ext} files")
        
        all_files.sort(key=lambda p: str(p).lower())
        logger.info(f"Total documents found: {len(all_files)}")
        return all_files
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata"""
        try:
            relative_path = file_path.relative_to(self.books_directory)
            path_parts = relative_path.parts[:-1]
            primary_subject = path_parts[-1].lower() if path_parts else "general"
            subject_hierarchy = " > ".join(path_parts) if path_parts else "general"
            stat = file_path.stat()
            
            return {
                "path": str(file_path),
                "filename": file_path.name,
                "relative_path": str(relative_path),
                "primary_subject": primary_subject,
                "subject_hierarchy": subject_hierarchy,
                "file_size": stat.st_size,
                "modified_time": stat.st_mtime,
                "file_extension": file_path.suffix.lower()
            }
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return {
                "path": str(file_path),
                "filename": file_path.name,
                "relative_path": str(file_path),
                "primary_subject": "general",
                "subject_hierarchy": "general",
                "file_size": 0,
                "modified_time": 0,
                "file_extension": file_path.suffix.lower()
            }
    
    def extract_text_from_pdf_memory_safe(self, pdf_path: Path) -> str:
        """Extract text from PDF"""
        doc = None
        try:
            doc = fitz.open(str(pdf_path))
            text_parts = []
            page_count = min(self.max_pages_per_pdf, doc.page_count)
            
            for page_num in range(page_count):
                try:
                    page = doc[page_num]
                    text = page.get_text()
                    if text and len(text.strip()) > 10:
                        cleaned_text = ' '.join(text.split())
                        text_parts.append(cleaned_text)
                    del page
                except Exception as e:
                    logger.warning(f"Error on page {page_num}: {e}")
                    continue
            
            full_text = " ".join(text_parts)
            if len(full_text.strip()) < 50:
                logger.warning(f"Insufficient text from {pdf_path.name}: {len(full_text)} chars")
                return ""
            
            logger.debug(f"Extracted {len(full_text)} chars from {pdf_path.name}")
            return full_text
        except Exception as e:
            logger.error(f"Error extracting from {pdf_path}: {e}")
            return ""
        finally:
            if doc:
                try:
                    doc.close()
                except:
                    pass
            del doc
            if self.processed_count % self.memory_cleanup_interval == 0:
                gc.collect()
    
    def extract_text_from_epub_memory_safe(self, epub_path: Path) -> str:
        """Extract text from EPUB"""
        if not EPUB_AVAILABLE:
            logger.warning(f"EPUB not available for {epub_path.name}")
            return ""
        
        try:
            book = epub.read_epub(str(epub_path))
            text_parts = []
            chapter_count = 0
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    try:
                        html_content = item.get_content().decode('utf-8')
                        import re
                        text = re.sub('<[^<]+?>', '', html_content)
                        text = re.sub(r'\s+', ' ', text)
                        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
                        
                        if text and len(text.strip()) > 50:
                            text_parts.append(text.strip())
                            chapter_count += 1
                        
                        if chapter_count >= self.max_pages_per_pdf:
                            break
                    except Exception as e:
                        logger.warning(f"Error extracting chapter: {e}")
                        continue
            
            full_text = " ".join(text_parts)
            if len(full_text.strip()) < 100:
                logger.warning(f"Insufficient text from {epub_path.name}")
                return ""
            
            logger.debug(f"Extracted {len(full_text)} chars from {epub_path.name}")
            return full_text
        except Exception as e:
            logger.error(f"Error extracting EPUB {epub_path}: {e}")
            return ""
        finally:
            if self.processed_count % self.memory_cleanup_interval == 0:
                gc.collect()
    
    def create_smart_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create intelligent chunks"""
        if not text or len(text.strip()) < 50:
            return []
        
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text.strip()) >= 100:
                    chunks.append(self._create_chunk_with_metadata(chunk_text, metadata, len(chunks)))
                
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text.strip()) >= 100:
                chunks.append(self._create_chunk_with_metadata(chunk_text, metadata, len(chunks)))
        
        logger.debug(f"Created {len(chunks)} chunks from {metadata['filename']}")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        sentence_endings = re.compile(r'[.!?]+(?:\s+|$)')
        sentences = sentence_endings.split(text)
        
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                cleaned_sentences.append(sentence)
        return cleaned_sentences
    
    def _create_chunk_with_metadata(self, text: str, file_metadata: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        """Create chunk with metadata"""
        chunk_id = f"{hashlib.md5(file_metadata['path'].encode()).hexdigest()[:8]}_{chunk_index}"
        return {
            "id": chunk_id,
            "text": text,
            "metadata": {
                **file_metadata,
                "chunk_index": chunk_index,
                "chunk_id": chunk_id,
                "text_length": len(text),
                "created_at": datetime.now().isoformat()
            }
        }
    
    def process_document_batch(self, file_paths: List[Path], progress_callback=None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Process batch of documents"""
        processed_chunks = []
        batch_stats = {
            "processed": 0,
            "errors": 0,
            "skipped": 0,
            "total_chunks": 0,
            "memory_cleanups": 0
        }
        
        for i, file_path in enumerate(file_paths):
            try:
                if progress_callback:
                    progress = (i + 1) / len(file_paths)
                    progress_callback(progress, f"Processing {file_path.name}...")
                
                metadata = self.extract_metadata(file_path)
                
                if file_path.suffix.lower() == ".pdf":
                    text = self.extract_text_from_pdf_memory_safe(file_path)
                elif file_path.suffix.lower() == ".epub":
                    text = self.extract_text_from_epub_memory_safe(file_path)
                else:
                    logger.warning(f"Unsupported file type: {file_path}")
                    batch_stats["skipped"] += 1
                    continue
                
                if not text:
                    logger.warning(f"No text extracted from {file_path}")
                    batch_stats["skipped"] += 1
                    continue
                
                chunks = self.create_smart_chunks(text, metadata)
                processed_chunks.extend(chunks)
                
                batch_stats["processed"] += 1
                batch_stats["total_chunks"] += len(chunks)
                
                if i % self.memory_cleanup_interval == 0 and i > 0:
                    gc.collect()
                    batch_stats["memory_cleanups"] += 1
                    log_memory_usage(f"after {i} files")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                batch_stats["errors"] += 1
                continue
        
        gc.collect()
        log_memory_usage("batch complete")
        return processed_chunks, batch_stats

# Vector Database
class EnhancedVectorDatabase:
    """ChromaDB vector database"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.chromadb_config = config.get("chromadb", {})
        self.collection_name = self.chromadb_config.get("collection_name", "knowledge_chunks")
        self.persist_directory = Path(self.chromadb_config.get("persist_directory", "./data/vector_db"))
        self.client = None
        self.collection = None
        self.embedding_manager = None
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Vector database at: {self.persist_directory}")
    
    def initialize(self, embedding_manager: EnhancedEmbeddingManager) -> bool:
        """Initialize ChromaDB"""
        try:
            self.embedding_manager = embedding_manager
            self.client = chromadb.PersistentClient(path=str(self.persist_directory))
            
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(name=self.collection_name)
                logger.info(f"Created collection: {self.collection_name}")
            
            try:
                count = self.collection.count()
                logger.info(f"Collection contains {count} items")
            except Exception as e:
                logger.warning(f"Could not get count: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def add_chunks_batch(self, chunks: List[Dict[str, Any]], batch_size: int = 50) -> Tuple[int, int]:
        """Add chunks in batches"""
        if not chunks or not self.collection or not self.embedding_manager:
            return 0, 0
        
        added_count = 0
        error_count = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            try:
                texts = [chunk["text"] for chunk in batch]
                metadatas = [chunk["metadata"] for chunk in batch]
                ids = [chunk["id"] for chunk in batch]
                embeddings = self.embedding_manager.embed(texts)
                
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                added_count += len(batch)
                logger.debug(f"Added batch {i//batch_size + 1}: {len(batch)} chunks")
                del texts, metadatas, ids, embeddings
                gc.collect()
            except Exception as e:
                logger.error(f"Error adding batch: {e}")
                error_count += len(batch)
                continue
        
        logger.info(f"Added {added_count} chunks, {error_count} errors")
        return added_count, error_count
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        if not self.collection or not self.embedding_manager:
            return []
        
        try:
            query_embedding = self.embedding_manager.embed_one(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(documents)
                distances = results["distances"][0] if results["distances"] else [0.0] * len(documents)
                
                for doc, metadata, distance in zip(documents, metadatas, distances):
                    formatted_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity": 1.0 - distance,
                        "distance": distance
                    })
            return formatted_results
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if not self.collection:
            return {"error": "Not initialized"}
        
        try:
            count = self.collection.count()
            sample = self.collection.get(limit=min(100, count)) if count > 0 else {"metadatas": []}
            
            subjects = defaultdict(int)
            file_types = defaultdict(int)
            
            for metadata in (sample.get("metadatas") or []):
                if isinstance(metadata, dict):
                    subjects[metadata.get("primary_subject", "unknown")] += 1
                    file_types[metadata.get("file_extension", "unknown")] += 1
            
            return {
                "total_chunks": count,
                "subjects": dict(subjects),
                "file_types": dict(file_types),
                "embedding_provider": self.embedding_manager.current_provider if self.embedding_manager else "unknown"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

# State Manager
class ProcessingStateManager:
    """Manages processing state"""
    
    def __init__(self, state_file: str = "./data/processing_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self.load_state()
    
    def load_state(self) -> Dict[str, Any]:
        """Load state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_processed_index": 0,
            "total_processed": 0,
            "total_errors": 0,
            "last_run": None,
            "completed_files": set()
        }
    
    def save_state(self):
        """Save state"""
        try:
            state_to_save = self.state.copy()
            if isinstance(state_to_save.get("completed_files"), set):
                state_to_save["completed_files"] = list(state_to_save["completed_files"])
            with open(self.state_file, 'w') as f:
                json.dump(state_to_save, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def update_progress(self, processed_index: int, file_path: str, success: bool = True):
        """Update progress"""
        self.state["last_processed_index"] = processed_index
        self.state["total_processed"] += 1 if success else 0
        self.state["total_errors"] += 0 if success else 1
        self.state["last_run"] = datetime.now().isoformat()
        
        if "completed_files" not in self.state:
            self.state["completed_files"] = set()
        elif isinstance(self.state["completed_files"], list):
            self.state["completed_files"] = set(self.state["completed_files"])
        
        if success:
            self.state["completed_files"].add(str(file_path))
    
    def is_file_processed(self, file_path: str) -> bool:
        """Check if processed"""
        completed = self.state.get("completed_files", set())
        if isinstance(completed, list):
            completed = set(completed)
        return str(file_path) in completed
    
    def get_resume_index(self) -> int:
        """Get resume index"""
        return self.state.get("last_processed_index", 0)
    
    def reset_state(self):
        """Reset state"""
        self.state = {
            "last_processed_index": 0,
            "total_processed": 0,
            "total_errors": 0,
            "last_run": None,
            "completed_files": set()
        }
        self.save_state()

# Main Chatbot
class EnhancedKnowledgeChatbot:
    """Main chatbot class"""
    
    def __init__(self, config_path: str = "./config.yaml"):
        self.config = load_yaml_config(Path(config_path))
        self.embedding_manager = EnhancedEmbeddingManager(self.config)
        self.doc_processor = MemoryOptimizedDocumentProcessor(
            books_directory="D:/Books",
            config=self.config
        )
        self.vector_db = EnhancedVectorDatabase(self.config)
        self.state_manager = ProcessingStateManager()
        self.is_initialized = False
        self.processing_status = "Not initialized"
        logger.info("Chatbot initialized")
    
    def initialize_system(self) -> Tuple[bool, str]:
        """Initialize system"""
        try:
            log_memory_usage("init start")
            if not self.vector_db.initialize(self.embedding_manager):
                return False, "Failed to initialize database"
            
            self.is_initialized = True
            self.processing_status = "System ready"
            
            stats = self.vector_db.get_collection_stats()
            embedding_status = self.embedding_manager.get_status()
            
            msg = f"System ready! DB: {stats.get('total_chunks', 0)} chunks, Embeddings: {embedding_status['current_provider']}"
            log_memory_usage("init complete")
            return True, msg
        except Exception as e:
            logger.error(f"Init failed: {e}")
            return False, str(e)
    
    def process_documents_batch(self, batch_size: int = 100, resume: bool = True, progress_callback=None) -> Tuple[bool, str]:
        """Process documents"""
        try:
            if not self.is_initialized:
                success, msg = self.initialize_system()
                if not success:
                    return False, msg
            
            all_files = self.doc_processor.find_all_documents()
            if not all_files:
                return False, "No documents found"
            
            start_index = self.state_manager.get_resume_index() if resume else 0
            total_files = len(all_files)
            
            if start_index >= total_files:
                return True, f"All {total_files} documents processed"
            
            logger.info(f"Processing {total_files - start_index} documents from {start_index}")
            
            processed_total = 0
            error_total = 0
            
            for batch_start in range(start_index, total_files, batch_size):
                batch_end = min(batch_start + batch_size, total_files)
                batch_files = all_files[batch_start:batch_end]
                
                if progress_callback:
                    progress_callback(batch_start / total_files, f"Batch {batch_start//batch_size + 1}...")
                
                logger.info(f"Processing batch {batch_start}-{batch_end}")
                
                unprocessed = [f for f in batch_files if not self.state_manager.is_file_processed(str(f))]
                if not unprocessed:
                    continue
                
                chunks, stats = self.doc_processor.process_document_batch(unprocessed, progress_callback)
                
                if chunks:
                    added, errors = self.vector_db.add_chunks_batch(chunks)
                    logger.info(f"Added {added} chunks ({errors} errors)")
                
                for i, file_path in enumerate(batch_files):
                    self.state_manager.update_progress(batch_start + i, str(file_path), True)
                
                processed_total += stats["processed"]
                error_total += stats["errors"]
                self.state_manager.save_state()
                
                del chunks
                gc.collect()
                log_memory_usage(f"batch {batch_start//batch_size + 1}")
            
            stats = self.vector_db.get_collection_stats()
            msg = f"Complete! Processed: {processed_total}, Errors: {error_total}, Total chunks: {stats.get('total_chunks', 0)}"
            
            if progress_callback:
                progress_callback(1.0, msg)
            return True, msg
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return False, str(e)
    
    def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search documents"""
        if not self.is_initialized or not self.vector_db.collection:
            return []
        
        try:
            results = self.vector_db.search_similar(query, n_results=limit)
            enhanced = []
            for result in results:
                metadata = result.get("metadata", {})
                enhanced.append({
                    "content": result["content"],
                    "source": metadata.get("filename", "Unknown"),
                    "subject": metadata.get("primary_subject", "general"),
                    "subject_hierarchy": metadata.get("subject_hierarchy", ""),
                    "similarity": result["similarity"],
                    "relevance_score": result["similarity"],
                    "file_path": metadata.get("relative_path", ""),
                    "chunk_index": metadata.get("chunk_index", 0)
                })
            return enhanced
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        try:
            db_stats = self.vector_db.get_collection_stats()
            embedding_status = self.embedding_manager.get_status()
            state = self.state_manager.state.copy()
            if isinstance(state.get("completed_files"), set):
                state["completed_files"] = len(state["completed_files"])
            
            memory_info = {}
            try:
                import psutil
                process = psutil.Process()
                memory_info = {
                    "memory_mb": round(process.memory_info().rss / 1024 / 1024, 1),
                    "memory_percent": round(process.memory_percent(), 1)
                }
            except:
                pass
            
            return {
                "initialized": self.is_initialized,
                "processing_status": self.processing_status,
                "database": db_stats,
                "embeddings": embedding_status,
                "processing_state": state,
                "memory": memory_info,
                "config": {
                    "chunk_size": self.doc_processor.chunk_size,
                    "max_pages": self.doc_processor.max_pages_per_pdf,
                    "books_dir": str(self.doc_processor.books_directory)
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def reset_processing_state(self) -> str:
        """Reset state"""
        try:
            self.state_manager.reset_state()
            return "State reset"
        except Exception as e:
            return f"Error: {e}"

# Gradio Interface
def create_enhanced_interface():
    """Create interface"""
    chatbot = None
    
    def get_chatbot():
        nonlocal chatbot
        if chatbot is None:
            chatbot = EnhancedKnowledgeChatbot()
        return chatbot
    
    def initialize_system():
        cb = get_chatbot()
        success, message = cb.initialize_system()
        status = cb.get_system_status()
        return message, status
    
    def process_documents(batch_size, resume, progress=gr.Progress()):
        cb = get_chatbot()
        def update_progress(value, status):
            progress(value, desc=status)
        success, message = cb.process_documents_batch(int(batch_size), resume, update_progress)
        status = cb.get_system_status()
        return message, status
    
    def search_documents(query, max_results):
        if not query.strip():
            return "Please enter a search query"
        cb = get_chatbot()
        results = cb.search_documents(query, limit=int(max_results))
        if not results:
            return "No results found"
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"**Result {i}** (Similarity: {result['similarity']:.3f})\n"
                f"**Source:** {result['source']}\n"
                f"**Subject:** {result['subject']} ({result['subject_hierarchy']})\n"
                f"**Content:** {result['content'][:500]}...\n---"
            )
        return "\n\n".join(formatted)
    
    def get_system_status():
        cb = get_chatbot()
        return cb.get_system_status()
    
    def reset_system():
        cb = get_chatbot()
        return cb.reset_processing_state()
    
    with gr.Blocks(title="AI Knowledge Base Chatbot", theme=gr.themes.Soft()) as demo:
        gr.HTML("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; border-radius: 10px; margin-bottom: 20px;">
            <h1>AI Knowledge Base Chatbot</h1>
            <p>Memory-optimized with EPUB and PDF support</p>
        </div>
        """)
        
        with gr.Tabs():
            with gr.TabItem("System Management"):
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### Initialization")
                        init_btn = gr.Button("Initialize System", variant="primary")
                        init_status = gr.Textbox(label="Status", value="Click Initialize", interactive=False)
                        
                        gr.Markdown("### Document Processing")
                        with gr.Row():
                            batch_size = gr.Slider(50, 500, 100, 50, label="Batch Size")
                            resume_processing = gr.Checkbox(label="Resume", value=True)
                        
                        process_btn = gr.Button("Process Documents", variant="secondary")
                        process_status = gr.Textbox(label="Status", interactive=False, lines=3)
                        
                        gr.Markdown("### Control")
                        with gr.Row():
                            status_btn = gr.Button("Refresh Status")
                            reset_btn = gr.Button("Reset State", variant="stop")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### System Status")
                        system_status = gr.JSON(label="Status", value={})
                        gr.HTML("""
                        <div style="padding: 15px; background: #f0f8ff; border-radius: 8px; margin-top: 10px;">
                            <h4>Features</h4>
                            <ul>
                                <li>EPUB & PDF processing</li>
                                <li>Real embeddings</li>
                                <li>Memory management</li>
                                <li>Resume support</li>
                            </ul>
                        </div>
                        """)
            
            with gr.TabItem("Search"):
                with gr.Row():
                    with gr.Column(scale=2):
                        search_query = gr.Textbox(label="Query", placeholder="Search...", lines=2)
                        with gr.Row():
                            search_btn = gr.Button("Search", variant="primary")
                            max_results = gr.Slider(1, 20, 5, 1, label="Max Results")
                        search_results = gr.Markdown(label="Results", value="Enter a query")
                    
                    with gr.Column(scale=1):
                        gr.HTML("""
                        <div style="padding: 15px; background: #f0fff0; border-radius: 8px;">
                            <h4>Search</h4>
                            <ul>
                                <li>Semantic search</li>
                                <li>Subject filtering</li>
                                <li>Similarity scores</li>
                            </ul>
                        </div>
                        """)
        
        init_btn.click(fn=initialize_system, outputs=[init_status, system_status])
        process_btn.click(fn=process_documents, inputs=[batch_size, resume_processing], outputs=[process_status, system_status])
        search_btn.click(fn=search_documents, inputs=[search_query, max_results], outputs=[search_results])
        search_query.submit(fn=search_documents, inputs=[search_query, max_results], outputs=[search_results])
        status_btn.click(fn=get_system_status, outputs=[system_status])
        reset_btn.click(fn=reset_system, outputs=[process_status])
        
        gr.HTML("""
        <div style="text-align: center; margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
            <p><strong>Enhanced AI Knowledge Base Chatbot</strong></p>
        </div>
        """)
    
    return demo

if __name__ == "__main__":
    logger.info("Starting Enhanced AI Knowledge Base Chatbot...")
    
    missing = []
    if not OPENAI_AVAILABLE:
        missing.append("openai")
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        missing.append("sentence-transformers")
    if not EPUB_AVAILABLE:
        missing.append("ebooklib")
    
    if missing:
        print("\n" + "=" * 60)
        print("OPTIONAL DEPENDENCIES MISSING:")
        for dep in missing:
            print(f"  - {dep}")
        print("System will work with available components.")
        print("=" * 60 + "\n")
    
    demo = create_enhanced_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        inbrowser=True
    )