"""
Scholar's Terminal - File Watcher Service
==========================================
Monitors D:/Books and D:/GitHub for new/modified files
and automatically indexes them into ChromaDB.

Compatible with the existing 12.9M chunk collection:
- Embedding: nomic-embed-text (768-dim) via Ollama
- Chunking: 1000 words, 200 word overlap
- Collection: books

Author: Claude & Vincent
Date: December 2025
"""

import os
import sys
import time
import logging
import hashlib
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Third-party imports
import chromadb
import httpx

# Optional imports for different file types
try:
    import fitz  # PyMuPDF for PDFs
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PyMuPDF not available. PDF processing disabled.")

try:
    from ebooklib import epub
    import ebooklib
    from bs4 import BeautifulSoup
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    print("Warning: ebooklib not available. EPUB processing disabled.")

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    IMAGE_AVAILABLE = True
except ImportError:
    IMAGE_AVAILABLE = False
    print("Warning: Pillow not available. Image metadata extraction disabled.")

# =============================================================================
# CONFIGURATION
# =============================================================================

# Paths to monitor
WATCH_PATHS = [
    Path("D:/Books"),
    Path("D:/GitHub")
]

# ChromaDB configuration (must match existing collection)
CHROMA_PATH = Path(r"D:\Claude\Projects\scholars-terminal\data\vector_db")
COLLECTION_NAME = "books"
COLLECTION_NAME_GITHUB = "github"

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"  # 768-dim embeddings

# Chunking parameters (must match existing)
CHUNK_SIZE_WORDS = 1000
CHUNK_OVERLAP_WORDS = 200

# File watcher database (tracks what's been indexed)
WATCHER_DB = Path(r"D:\Claude\Projects\scholars-terminal\data\watcher_index.db")

# Supported file extensions by category
FILE_EXTENSIONS = {
    'documents': ['.pdf', '.epub', '.txt', '.md', '.rst', '.doc', '.docx'],
    'code': ['.py', '.js', '.ts', '.jsx', '.tsx', '.css', '.html', '.htm', 
             '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs', '.rb',
             '.php', '.swift', '.kt', '.scala', '.r', '.sql', '.sh', '.bash',
             '.yaml', '.yml', '.json', '.xml', '.toml', '.ini', '.cfg'],
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff']
}

# Polling interval (seconds)
POLL_INTERVAL = 60  # Check every minute

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'D:\Claude\Projects\scholars-terminal\logs\watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATABASE FOR TRACKING INDEXED FILES
# =============================================================================

class IndexDatabase:
    """Tracks which files have been indexed and their modification times."""
    
    def __init__(self, db_path: Path = WATCHER_DB):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Initialize the tracking database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS indexed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_hash TEXT NOT NULL,
                mod_time REAL NOT NULL,
                file_size INTEGER NOT NULL,
                chunk_count INTEGER NOT NULL,
                indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                source_type TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_file_path ON indexed_files(file_path)
        ''')
        
        conn.commit()
        conn.close()
    
    def get_file_record(self, file_path: str) -> Optional[Dict]:
        """Get record for a file if it exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT file_hash, mod_time, file_size, chunk_count FROM indexed_files WHERE file_path = ?',
            (file_path,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'file_hash': row[0],
                'mod_time': row[1],
                'file_size': row[2],
                'chunk_count': row[3]
            }
        return None
    
    def add_file_record(self, file_path: str, file_hash: str, mod_time: float, 
                        file_size: int, chunk_count: int, source_type: str):
        """Add or update a file record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO indexed_files 
            (file_path, file_hash, mod_time, file_size, chunk_count, source_type, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (file_path, file_hash, mod_time, file_size, chunk_count, source_type))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Get indexing statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*), SUM(chunk_count), SUM(file_size) FROM indexed_files')
        row = cursor.fetchone()
        
        cursor.execute('SELECT source_type, COUNT(*) FROM indexed_files GROUP BY source_type')
        by_type = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_files': row[0] or 0,
            'total_chunks': row[1] or 0,
            'total_size_mb': round((row[2] or 0) / (1024 * 1024), 2),
            'by_type': by_type
        }


# =============================================================================
# TEXT EXTRACTION
# =============================================================================

def extract_text_from_pdf(file_path: Path, max_pages: int = 50) -> str:
    """Extract text from PDF file."""
    if not PDF_AVAILABLE:
        return ""
    
    try:
        doc = fitz.open(str(file_path))
        text_parts = []
        
        page_count = min(max_pages, doc.page_count)
        for page_num in range(page_count):
            page = doc[page_num]
            text_parts.append(page.get_text())
        
        doc.close()
        return "\n".join(text_parts)
    
    except Exception as e:
        logger.error(f"Error extracting PDF {file_path.name}: {e}")
        return ""


def extract_text_from_epub(file_path: Path) -> str:
    """Extract text from EPUB file."""
    if not EPUB_AVAILABLE:
        return ""
    
    try:
        book = epub.read_epub(str(file_path))
        text_parts = []
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text_parts.append(soup.get_text())
        
        return "\n".join(text_parts)
    
    except Exception as e:
        logger.error(f"Error extracting EPUB {file_path.name}: {e}")
        return ""


def extract_text_from_code(file_path: Path) -> str:
    """Extract text from code files with structure preservation."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # Add file metadata as header
        header = f"# File: {file_path.name}\n# Path: {file_path}\n# Language: {file_path.suffix}\n\n"
        
        return header + content
    
    except Exception as e:
        logger.error(f"Error reading code file {file_path.name}: {e}")
        return ""


def extract_text_from_text(file_path: Path) -> str:
    """Extract text from plain text files."""
    try:
        return file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Error reading text file {file_path.name}: {e}")
        return ""


def extract_metadata_from_image(file_path: Path) -> str:
    """Extract metadata from image files."""
    if not IMAGE_AVAILABLE:
        return f"Image file: {file_path.name}"
    
    try:
        img = Image.open(file_path)
        
        metadata_parts = [
            f"Image: {file_path.name}",
            f"Format: {img.format}",
            f"Size: {img.size[0]}x{img.size[1]}",
            f"Mode: {img.mode}"
        ]
        
        # Extract EXIF data if available
        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, (str, int, float)):
                    metadata_parts.append(f"{tag}: {value}")
        
        img.close()
        return "\n".join(metadata_parts)
    
    except Exception as e:
        logger.error(f"Error extracting image metadata {file_path.name}: {e}")
        return f"Image file: {file_path.name}"


def extract_text(file_path: Path) -> Tuple[str, str]:
    """Extract text from any supported file type.
    
    Returns: (text_content, source_type)
    """
    suffix = file_path.suffix.lower()
    
    if suffix == '.pdf':
        return extract_text_from_pdf(file_path), 'pdf'
    elif suffix == '.epub':
        return extract_text_from_epub(file_path), 'epub'
    elif suffix in FILE_EXTENSIONS['code']:
        return extract_text_from_code(file_path), 'code'
    elif suffix in FILE_EXTENSIONS['images']:
        return extract_metadata_from_image(file_path), 'image'
    elif suffix in ['.txt', '.md', '.rst']:
        return extract_text_from_text(file_path), 'text'
    else:
        return extract_text_from_text(file_path), 'other'


# =============================================================================
# CHUNKING
# =============================================================================

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, 
               overlap: int = CHUNK_OVERLAP_WORDS) -> List[str]:
    """Split text into overlapping chunks by word count.
    
    Matches the existing collection's chunking strategy.
    """
    if not text.strip():
        return []
    
    words = text.split()
    chunks = []
    
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        if chunk_words:
            chunks.append(' '.join(chunk_words))
        
        i += chunk_size - overlap
        if i >= len(words):
            break
    
    return chunks if chunks else [text]


# =============================================================================
# EMBEDDING GENERATION
# =============================================================================

def get_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using Ollama's nomic-embed-text model."""
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={
                    "model": EMBED_MODEL,
                    "prompt": text
                }
            )
            response.raise_for_status()
            return response.json()["embedding"]
    
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None


def get_embeddings_batch(texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
    """Generate embeddings for multiple texts."""
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for text in batch:
            emb = get_embedding(text)
            embeddings.append(emb)
        
        # Small delay between batches
        if i + batch_size < len(texts):
            time.sleep(0.1)
    
    return embeddings


# =============================================================================
# FILE DISCOVERY
# =============================================================================

def get_file_hash(file_path: Path) -> str:
    """Generate a hash of file content for change detection."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


def discover_files(watch_paths: List[Path]) -> List[Dict[str, Any]]:
    """Discover all supported files in watch paths."""
    all_extensions = set()
    for exts in FILE_EXTENSIONS.values():
        all_extensions.update(exts)
    
    files = []
    
    for watch_path in watch_paths:
        if not watch_path.exists():
            logger.warning(f"Watch path does not exist: {watch_path}")
            continue
        
        for ext in all_extensions:
            for file_path in watch_path.glob(f"**/*{ext}"):
                try:
                    stat = file_path.stat()
                    files.append({
                        'path': file_path,
                        'mod_time': stat.st_mtime,
                        'file_size': stat.st_size,
                        'extension': file_path.suffix.lower()
                    })
                except Exception as e:
                    logger.warning(f"Could not stat {file_path}: {e}")
    
    return files


def find_new_or_modified_files(discovered: List[Dict], index_db: IndexDatabase) -> List[Dict]:
    """Find files that are new or have been modified since last index."""
    to_process = []
    
    for file_info in discovered:
        file_path = str(file_info['path'])
        record = index_db.get_file_record(file_path)
        
        if record is None:
            # New file
            to_process.append(file_info)
        elif file_info['mod_time'] > record['mod_time']:
            # Modified file
            to_process.append(file_info)
        elif file_info['file_size'] != record['file_size']:
            # Size changed (safety check)
            to_process.append(file_info)
    
    return to_process


# =============================================================================
# INDEXING
# =============================================================================

def index_file(file_info: Dict, collection, index_db: IndexDatabase) -> int:
    """Index a single file into ChromaDB.
    
    Returns: number of chunks indexed
    """
    file_path = file_info['path']
    logger.info(f"Indexing: {file_path.name}")
    
    # Extract text
    text, source_type = extract_text(file_path)
    if not text.strip():
        logger.warning(f"No text extracted from {file_path.name}")
        return 0
    
    # Create chunks
    chunks = chunk_text(text)
    if not chunks:
        logger.warning(f"No chunks created for {file_path.name}")
        return 0
    
    # Generate embeddings
    embeddings = []
    for chunk in chunks:
        emb = get_embedding(chunk)
        if emb is None:
            logger.error(f"Failed to generate embedding for {file_path.name}")
            return 0
        embeddings.append(emb)
    
    # Create IDs and metadata
    file_hash = get_file_hash(file_path)
    base_id = hashlib.sha1(str(file_path).encode()).hexdigest()[:12]
    
    ids = [f"{base_id}_{i:05d}" for i in range(len(chunks))]
    
    # Extract subject from path (for D:\Books structure)
    relative_parts = []
    for watch_path in WATCH_PATHS:
        try:
            rel = file_path.relative_to(watch_path)
            relative_parts = rel.parts[:-1]  # Exclude filename
            break
        except ValueError:
            continue
    
    primary_subject = relative_parts[-1].lower() if relative_parts else "general"
    subject_hierarchy = " > ".join(relative_parts) if relative_parts else "general"
    
    metadatas = [{
        'source': str(file_path),
        'title': file_path.stem,
        'chunk_index': i,
        'primary_subject': primary_subject,
        'subject_hierarchy': subject_hierarchy,
        'source_type': source_type,
        'file_extension': file_path.suffix.lower()
    } for i in range(len(chunks))]
    
    # Add to ChromaDB in batches
    batch_size = 500
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        try:
            collection.add(
                ids=ids[i:end],
                documents=chunks[i:end],
                embeddings=embeddings[i:end],
                metadatas=metadatas[i:end]
            )
        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {e}")
            return 0
    
    # Record in tracking database
    index_db.add_file_record(
        file_path=str(file_path),
        file_hash=file_hash,
        mod_time=file_info['mod_time'],
        file_size=file_info['file_size'],
        chunk_count=len(chunks),
        source_type=source_type
    )
    
    logger.info(f"Indexed {len(chunks)} chunks from {file_path.name}")
    return len(chunks)


# =============================================================================
# WATCHER SERVICE
# =============================================================================

class FileWatcher:
    """Main file watcher service."""
    
    def __init__(self):
        self.index_db = IndexDatabase()
        self.chroma_client = None
        self.collection = None
        self.running = False
        self._stop_event = threading.Event()
    
    def initialize(self) -> bool:
        """Initialize ChromaDB connection."""
        try:
            logger.info(f"Connecting to ChromaDB at {CHROMA_PATH}")
            self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
            self.collection = self.chroma_client.get_collection(COLLECTION_NAME)
            
            count = self.collection.count()
            logger.info(f"Connected to collection '{COLLECTION_NAME}' with {count:,} documents")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return False
    
    def run_once(self) -> Dict:
        """Run a single indexing pass.
        
        Returns: statistics about what was indexed
        """
        stats = {
            'files_discovered': 0,
            'files_to_process': 0,
            'files_indexed': 0,
            'chunks_added': 0,
            'errors': 0
        }
        
        # Discover files
        logger.info("Discovering files...")
        discovered = discover_files(WATCH_PATHS)
        stats['files_discovered'] = len(discovered)
        logger.info(f"Found {len(discovered)} files total")
        
        # Find new/modified files
        to_process = find_new_or_modified_files(discovered, self.index_db)
        stats['files_to_process'] = len(to_process)
        
        if not to_process:
            logger.info("No new or modified files to index")
            return stats
        
        logger.info(f"Processing {len(to_process)} new/modified files")
        
        # Index each file
        for file_info in to_process:
            try:
                chunks = index_file(file_info, self.collection, self.index_db)
                if chunks > 0:
                    stats['files_indexed'] += 1
                    stats['chunks_added'] += chunks
            except Exception as e:
                logger.error(f"Error indexing {file_info['path']}: {e}")
                stats['errors'] += 1
        
        logger.info(f"Indexing complete: {stats['files_indexed']} files, {stats['chunks_added']} chunks")
        return stats
    
    def run_continuous(self, interval: int = POLL_INTERVAL):
        """Run continuous monitoring loop."""
        self.running = True
        self._stop_event.clear()
        
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")
        logger.info(f"Watching: {', '.join(str(p) for p in WATCH_PATHS)}")
        
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait for interval or stop signal
            self._stop_event.wait(interval)
        
        self.running = False
        logger.info("File watcher stopped")
    
    def stop(self):
        """Stop the continuous monitoring loop."""
        logger.info("Stopping file watcher...")
        self._stop_event.set()
    
    def get_status(self) -> Dict:
        """Get current watcher status."""
        db_stats = self.index_db.get_stats()
        
        collection_count = 0
        if self.collection:
            try:
                collection_count = self.collection.count()
            except:
                pass
        
        return {
            'running': self.running,
            'watch_paths': [str(p) for p in WATCH_PATHS],
            'chroma_path': str(CHROMA_PATH),
            'collection_name': COLLECTION_NAME,
            'collection_count': collection_count,
            'indexed_by_watcher': db_stats
        }


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scholar's Terminal File Watcher")
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=POLL_INTERVAL, 
                        help=f'Polling interval in seconds (default: {POLL_INTERVAL})')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("📚 Scholar's Terminal - File Watcher")
    print("=" * 60)
    
    watcher = FileWatcher()
    
    if args.status:
        if watcher.initialize():
            status = watcher.get_status()
            print(json.dumps(status, indent=2))
        return
    
    if not watcher.initialize():
        print("Failed to initialize. Exiting.")
        sys.exit(1)
    
    print(f"Watch Paths: {', '.join(str(p) for p in WATCH_PATHS)}")
    print(f"ChromaDB: {CHROMA_PATH}")
    print(f"Collection: {COLLECTION_NAME}")
    print("=" * 60 + "\n")
    
    if args.once:
        stats = watcher.run_once()
        print(f"\nResults: {json.dumps(stats, indent=2)}")
    else:
        try:
            watcher.run_continuous(args.interval)
        except KeyboardInterrupt:
            print("\nShutting down...")
            watcher.stop()


if __name__ == "__main__":
    main()
