"""
Database Initializer and Updater for Unified Knowledge Chatbot
Automatically scans for new documents and updates vector databases
"""

import os
import sys
import logging
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import re

# Document processing imports
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import docx

# Vector database imports
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class DocumentProcessor:
    """Process various document formats"""

    def __init__(self):
        self.supported_extensions = {
            # Documents
            ".pdf",
            ".epub",
            ".txt",
            ".md",
            ".docx",
            ".html",
            ".htm",
            ".rtf",
            ".mobi",
            # Code files
            ".py",
            ".js",
            ".ts",
            ".json",
            ".yml",
            ".yaml",
            ".css",
            ".jsx",
            ".tsx",
            ".sh",
            ".bat",
            ".ps1",
            ".sql",
            ".r",
            ".ipynb",
        }

    def extract_text_from_pdf(self, file_path: Path) -> str:
        try:
            text = []
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return ""

    def extract_text_from_epub(self, file_path: Path) -> str:
        try:
            book = epub.read_epub(file_path)
            text = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    text.append(soup.get_text())
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Error reading EPUB {file_path}: {e}")
            return ""

    def extract_text_from_docx(self, file_path: Path) -> str:
        try:
            doc = docx.Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            return ""

    def extract_text_from_txt(self, file_path: Path) -> str:
        try:
            encodings = ["utf-8", "latin-1", "windows-1252", "iso-8859-1"]
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            return ""
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return ""

    def process_document(self, file_path: Path) -> Optional[str]:
        ext = file_path.suffix.lower()

        if ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext == ".epub":
            return self.extract_text_from_epub(file_path)
        elif ext == ".docx":
            return self.extract_text_from_docx(file_path)
        elif ext in [".txt", ".md", ".rtf"]:
            return self.extract_text_from_txt(file_path)
        elif ext in [".html", ".htm"]:
            return self.extract_text_from_txt(file_path)
        # Code and config files - treat as plain text
        elif ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yml", ".yaml", 
                     ".css", ".sh", ".bat", ".ps1", ".sql", ".r", ".ipynb",
                     ".toml", ".ini", ".cfg", ".xml", ".c", ".cpp", ".h", ".hpp",
                     ".java", ".go", ".rs", ".rb", ".php", ".swift", ".kt"]:
            return self.extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file format: {ext}")
            return None


class DatabaseInitializer:
    """Initialize and update vector databases"""

    def __init__(
        self,
        books_path: str,
        github_path: str,
        github_db_path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        # source folders
        self.books_path = Path(books_path)
        self.github_path = Path(github_path)

        # unified vector DB path
        self.db_path = Path(github_db_path)
        self.github_db_path = self.db_path  # keep legacy name

        # ensure directories
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # NEW: chunking defaults so start_chatbot.py doesn't have to pass them
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # components
        self.processor = DocumentProcessor()
        self.model = None
        self.client = None
        self.collection = None

        # tracking
        self.tracking_file = self.db_path.parent / "processed_files.json"
        self.processed_files = self._load_processed_files()

        # stats
        self.stats = {
            "new_files": 0,
            "updated_files": 0,
            "skipped_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
        }

    # ------------------ helpers ------------------ #

    def _load_processed_files(self) -> Dict:
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading tracking file: {e}")
                return {}
        return {}

    def _save_processed_files(self):
        try:
            with open(self.tracking_file, "w") as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tracking file: {e}")

    def _get_file_hash(self, file_path: Path) -> str:
        try:
            stat = file_path.stat()
            hash_string = f"{file_path}_{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(hash_string.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error getting file hash: {e}")
            return ""

    def _chunk_text(self, text: str, source: str) -> List[Dict]:
        """Split text into chunks with metadata"""
        chunks = []

        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return chunks

        words = text.split()

        step = max(1, self.chunk_size - self.chunk_overlap)
        for i in range(0, len(words), step):
            chunk_words = words[i : i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            if len(chunk_text) > 50:
                chunks.append(
                    {
                        "text": chunk_text,
                        "metadata": {
                            "source": source,  # <-- this is the tag we wanted
                            "chunk_index": len(chunks),
                            "timestamp": datetime.now().isoformat(),
                        },
                    }
                )
        return chunks

    def _scan_books(self) -> List[Path]:
        files: List[Path] = []
        for ext in self.processor.supported_extensions:
            files.extend(self.books_path.rglob(f"*{ext}"))
        return files

    def _scan_github(self) -> List[Path]:
        # Comprehensive code and config file extensions
        code_exts = {
            # Python
            ".py", ".pyx", ".pyi",
            # JavaScript/TypeScript
            ".js", ".jsx", ".ts", ".tsx", ".mjs",
            # Web
            ".html", ".css", ".scss", ".vue",
            # Config
            ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".xml",
            # Documentation
            ".md", ".txt", ".rst",
            # Shell
            ".sh", ".bash", ".bat", ".ps1",
            # Other languages
            ".java", ".go", ".rs", ".rb", ".php", ".c", ".cpp", ".h", ".hpp",
            ".sql", ".r", ".kt", ".swift",
            # Notebooks
            ".ipynb",
        }
        files: List[Path] = []
        if not self.github_path.exists():
            return files
        for ext in code_exts:
            files.extend(self.github_path.rglob(f"*{ext}"))
        return files

    # ------------------ database init ------------------ #

    def initialize_database(self):
        """Initialize ChromaDB and embedding model"""
        try:
            logger.info("Initializing database and embedding model...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(anonymized_telemetry=False),
            )
            try:
                # rename to 'knowledge' if you want
                self.collection = self.client.get_collection("books")
                logger.info(
                    f"Loaded existing collection with {self.collection.count()} chunks"
                )
            except:
                self.collection = self.client.create_collection("books")
                logger.info("Created new collection")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    # ------------------ main update ------------------ #

    def scan_and_update(self, max_files: Optional[int] = None):
        """Scan BOTH books + GitHub, ingest with source tags, update DB."""

        # make sure DB/model ready
        self.initialize_database()

        # --- 1) BOOKS ---
        book_files = self._scan_books()
        book_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        if max_files:
            book_files = book_files[:max_files]
        logger.info(f"Found {len(book_files)} book files to process.")

        self._process_file_list(book_files, label="book")

        # --- 2) GITHUB ---
        github_files = self._scan_github()
        if github_files:
            github_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            if max_files:
                github_files = github_files[:max_files]
            logger.info(f"Found {len(github_files)} GitHub files to process.")
            self._process_file_list(github_files, label="github")
        else:
            logger.info("No GitHub files found or GitHub path does not exist.")

        # final save
        self._save_processed_files()
        self._print_statistics()

        return {
            "status": "updated",
            "books_processed": self.stats["new_files"],
            "github_processed": self.stats["updated_files"],
        }

    def _process_file_list(self, files: List[Path], label: str):
        for idx, file_path in enumerate(files, 1):
            try:
                file_hash = self._get_file_hash(file_path)
                file_key = str(file_path)

                if (
                    file_key in self.processed_files
                    and self.processed_files[file_key] == file_hash
                ):
                    self.stats["skipped_files"] += 1
                    continue
                elif file_key in self.processed_files:
                    logger.info(f"File updated: {file_path.name}")
                    self.stats["updated_files"] += 1
                else:
                    logger.info(f"New {label} file: {file_path.name}")
                    self.stats["new_files"] += 1

                text = self.processor.process_document(file_path)
                if not text:
                    continue

                chunks = self._chunk_text(text, label)
                if not chunks:
                    continue

                texts = [c["text"] for c in chunks]
                embeddings = self.model.encode(texts).tolist()
                ids = [f"{label}_{file_hash}_{i}" for i in range(len(chunks))]
                metadatas = [c["metadata"] for c in chunks]

                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                )

                self.stats["total_chunks"] += len(chunks)
                self.processed_files[file_key] = file_hash

                if idx % 10 == 0:
                    self._save_processed_files()
                    logger.info(f"Progress: {idx}/{len(files)} {label} files")

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                self.stats["failed_files"] += 1
    def get_source_counts(self) -> Dict[str, int]:
        """
        Return how many chunks we have per source (book/github) from the unified collection.
        This is for the UI to display.
        """
        if self.collection is None:
           self.initialize_database()

        # WARNING: if you have 100k+ this may be big. But for now it's fine.
        # get all book chunks
        books = self.collection.get(where={"source": "book"}, limit=200000)
        github = self.collection.get(where={"source": "github"}, limit=200000)

        return {
            "book": len(books["ids"]),
            "github": len(github["ids"]),
            "total": self.collection.count(),
        }   
 
    def _print_statistics(self):
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"New files:      {self.stats['new_files']}")
        logger.info(f"Updated files:  {self.stats['updated_files']}")
        logger.info(f"Skipped files:  {self.stats['skipped_files']}")
        logger.info(f"Failed files:   {self.stats['failed_files']}")
        logger.info(f"Total chunks:   {self.stats['total_chunks']}")
        logger.info(f"Database size:  {self.collection.count()} chunks")
        logger.info("=" * 60)
