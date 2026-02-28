#!/usr/bin/env python3
"""
GitHub Repository Processor for Knowledge Base Chatbot
Processes code, documentation, and project files from GitHub repositories
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
from collections import defaultdict
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except:
    CHROMADB_AVAILABLE = False
    logger.error("ChromaDB not available!")

try:
    from llm_failover_system import LLMFailoverManager
    FAILOVER_AVAILABLE = True
except:
    FAILOVER_AVAILABLE = False
    logger.warning("LLM Failover system not available")
    class LLMFailoverManager:
        pass


class GitHubRepoProcessor:
    """Processes GitHub repositories and code files"""
    
    def __init__(self, github_directory: str = "D:/GitHub"):
        self.github_directory = Path(github_directory)
        
        # Supported file types for processing
        self.code_extensions = {
            # Python
            '.py', '.pyx', '.pyi',
            # JavaScript/TypeScript
            '.js', '.jsx', '.ts', '.tsx', '.mjs',
            # Web
            '.html', '.css', '.scss', '.sass', '.vue',
            # Java/Kotlin
            '.java', '.kt', '.kts',
            # C/C++
            '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp',
            # C#
            '.cs', '.cshtml',
            # Go
            '.go',
            # Rust
            '.rs',
            # Ruby
            '.rb',
            # PHP
            '.php',
            # Swift
            '.swift',
            # R
            '.r', '.R',
            # Scala
            '.scala',
            # Shell
            '.sh', '.bash', '.zsh',
            # SQL
            '.sql',
            # Documentation
            '.md', '.rst', '.txt', '.asciidoc',
            # Config
            '.json', '.yaml', '.yml', '.toml', '.xml', '.ini', '.cfg',
            # Notebooks
            '.ipynb',
            # Docker
            'Dockerfile', '.dockerfile',
            # Other
            '.graphql', '.proto'
        }
        
        # Directories to always skip
        self.skip_directories = {
            '.git', '.svn', '.hg',
            'node_modules', 'bower_components',
            '__pycache__', '.pytest_cache', '.mypy_cache',
            'venv', 'env', '.env', '.virtualenv',
            'build', 'dist', 'target', 'bin', 'obj',
            '.idea', '.vscode', '.vs',
            'vendor', 'packages',
            '.gradle', '.mvn',
            'coverage', '.coverage',
            '.next', '.nuxt',
            'tmp', 'temp', 'cache'
        }
        
        # Files to always skip
        self.skip_files = {
            '.DS_Store', 'Thumbs.db',
            '.gitignore', '.gitattributes',
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
            'poetry.lock', 'Pipfile.lock',
            '.env.example', '.env.local'
        }
        
        # Maximum file size (in MB) to process
        self.max_file_size_mb = 5  # Skip files larger than 5MB
        
    def should_process_file(self, file_path: Path) -> bool:
        """Determine if a file should be processed"""
        
        # Check file name
        if file_path.name in self.skip_files:
            return False
        
        # Check if any parent directory should be skipped
        for parent in file_path.parents:
            if parent.name in self.skip_directories:
                return False
        
        # Check file extension
        if file_path.suffix.lower() not in self.code_extensions:
            # Check for special files without extensions
            if file_path.name not in ['Dockerfile', 'Makefile', 'README']:
                return False
        
        # Check file size
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                logger.debug(f"Skipping large file: {file_path.name} ({size_mb:.1f} MB)")
                return False
        except:
            return False
        
        return True
    
    def extract_repo_info(self, file_path: Path) -> Dict[str, str]:
        """Extract repository and project information from file path"""
        try:
            relative_path = file_path.relative_to(self.github_directory)
            parts = relative_path.parts
            
            # First folder is typically the repo name
            repo_name = parts[0] if len(parts) > 0 else "unknown"
            
            # Try to detect project type
            file_ext = file_path.suffix.lower()
            
            project_type = "general"
            if file_ext in ['.py', '.pyx', '.pyi']:
                project_type = "python"
            elif file_ext in ['.js', '.jsx', '.ts', '.tsx']:
                project_type = "javascript"
            elif file_ext in ['.java', '.kt']:
                project_type = "java"
            elif file_ext in ['.cpp', '.c', '.h', '.hpp']:
                project_type = "cpp"
            elif file_ext in ['.cs']:
                project_type = "csharp"
            elif file_ext in ['.go']:
                project_type = "go"
            elif file_ext in ['.rs']:
                project_type = "rust"
            elif file_ext in ['.md', '.rst']:
                project_type = "documentation"
            elif file_ext in ['.ipynb']:
                project_type = "notebook"
            
            return {
                'repo_name': repo_name,
                'project_type': project_type,
                'relative_path': str(relative_path),
                'file_type': file_ext or 'no_extension'
            }
        except:
            return {
                'repo_name': 'unknown',
                'project_type': 'general',
                'relative_path': str(file_path),
                'file_type': file_path.suffix or 'no_extension'
            }
    
    def read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with encoding detection"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.debug(f"Error reading {file_path.name}: {e}")
                return None
        
        # If all encodings fail, try reading as binary and decode with errors='ignore'
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
                return content
        except:
            return None
    
    def process_notebook(self, file_path: Path) -> Optional[str]:
        """Extract code and markdown from Jupyter notebooks"""
        try:
            content = self.read_file_content(file_path)
            if not content:
                return None
            
            notebook = json.loads(content)
            
            extracted_text = []
            extracted_text.append(f"# Jupyter Notebook: {file_path.name}\n")
            
            for cell in notebook.get('cells', []):
                cell_type = cell.get('cell_type', '')
                source = cell.get('source', [])
                
                if isinstance(source, list):
                    source = ''.join(source)
                
                if cell_type == 'markdown':
                    extracted_text.append(f"\n## Markdown Cell\n{source}\n")
                elif cell_type == 'code':
                    extracted_text.append(f"\n## Code Cell\n```python\n{source}\n```\n")
            
            return '\n'.join(extracted_text)
            
        except Exception as e:
            logger.debug(f"Error processing notebook {file_path.name}: {e}")
            return None
    
    def create_code_chunks(self, content: str, file_info: Dict[str, str], 
                          chunk_size: int = 1500, overlap: int = 300) -> List[Dict[str, Any]]:
        """Create intelligent chunks from code files"""
        
        chunks = []
        
        # For code files, try to preserve function/class boundaries
        lines = content.split('\n')
        
        # Add file header to first chunk
        header = f"File: {file_info['relative_path']}\n"
        header += f"Repository: {file_info['repo_name']}\n"
        header += f"Type: {file_info['project_type']}\n"
        header += "="*80 + "\n\n"
        
        current_chunk = header
        current_size = len(current_chunk.split())
        
        for i, line in enumerate(lines):
            line_words = len(line.split())
            
            # If adding this line would exceed chunk size, save current chunk
            if current_size + line_words > chunk_size and current_size > chunk_size // 2:
                chunks.append({
                    'content': current_chunk,
                    'metadata': file_info.copy()
                })
                
                # Start new chunk with overlap
                overlap_lines = lines[max(0, i - 20):i]  # Last 20 lines for context
                current_chunk = header + '\n'.join(overlap_lines) + '\n' + line + '\n'
                current_size = len(current_chunk.split())
            else:
                current_chunk += line + '\n'
                current_size += line_words
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk,
                'metadata': file_info.copy()
            })
        
        return chunks
    
    def scan_github_directory(self) -> List[Path]:
        """Scan GitHub directory for processable files"""
        logger.info(f"Scanning {self.github_directory} for GitHub repositories...")
        
        if not self.github_directory.exists():
            logger.error(f"GitHub directory does not exist: {self.github_directory}")
            return []
        
        processable_files = []
        skipped_count = 0
        
        # Walk through all files
        for file_path in self.github_directory.rglob('*'):
            if file_path.is_file():
                if self.should_process_file(file_path):
                    processable_files.append(file_path)
                else:
                    skipped_count += 1
        
        logger.info(f"Found {len(processable_files)} processable files")
        logger.info(f"Skipped {skipped_count} files (wrong type/size/location)")
        
        # Show statistics by file type
        by_extension = defaultdict(int)
        for file_path in processable_files:
            ext = file_path.suffix.lower() or 'no_extension'
            by_extension[ext] += 1
        
        logger.info("\nFiles by type:")
        for ext, count in sorted(by_extension.items(), key=lambda x: x[1], reverse=True)[:15]:
            logger.info(f"  {ext:15s}: {count:5d} files")
        
        return processable_files
    
    def analyze_github_structure(self) -> Dict[str, Any]:
        """Analyze GitHub directory structure"""
        logger.info("\n" + "="*80)
        logger.info("ANALYZING GITHUB DIRECTORY STRUCTURE")
        logger.info("="*80)
        
        files = self.scan_github_directory()
        
        # Analyze by repository
        by_repo = defaultdict(lambda: {'files': 0, 'types': defaultdict(int), 'size_mb': 0})
        
        for file_path in files:
            repo_info = self.extract_repo_info(file_path)
            repo_name = repo_info['repo_name']
            
            by_repo[repo_name]['files'] += 1
            by_repo[repo_name]['types'][repo_info['project_type']] += 1
            
            try:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                by_repo[repo_name]['size_mb'] += size_mb
            except:
                pass
        
        # Sort repos by file count
        sorted_repos = sorted(by_repo.items(), key=lambda x: x[1]['files'], reverse=True)
        
        logger.info(f"\nFound {len(sorted_repos)} repositories:")
        logger.info("-"*80)
        
        for i, (repo_name, stats) in enumerate(sorted_repos[:20], 1):
            types_str = ', '.join([f"{t}({c})" for t, c in sorted(stats['types'].items(), 
                                                                   key=lambda x: x[1], 
                                                                   reverse=True)[:3]])
            logger.info(f"{i:2d}. {repo_name:40s} | {stats['files']:4d} files | "
                       f"{stats['size_mb']:6.1f} MB | {types_str}")
        
        if len(sorted_repos) > 20:
            logger.info(f"... and {len(sorted_repos) - 20} more repositories")
        
        return {
            'total_files': len(files),
            'total_repos': len(sorted_repos),
            'files': files,
            'repos': dict(by_repo)
        }


class GitHubDatabaseIntegrator:
    """Integrates GitHub files into the vector database"""
    
    def __init__(self, db_path: str = "./data/vector_db"):
        self.db_path = Path(db_path)
        self.client = None
        self.collection = None
        self.failover_manager = None
        
    def initialize(self):
        """Initialize database connection"""
        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available!")
            return False
        
        try:
            self.client = chromadb.PersistentClient(path=str(self.db_path))
            self.collection = self.client.get_or_create_collection("knowledge_base")
            
            if FAILOVER_AVAILABLE:
                self.failover_manager = LLMFailoverManager()
                logger.info("Failover manager initialized")
            
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def file_already_processed(self, file_path: Path, github_dir: Path) -> bool:
        """Check if file is already in database"""
        try:
            relative_path = str(file_path.relative_to(github_dir))
            
            # Search for this file in the collection
            results = self.collection.get(
                where={"source_path": relative_path}
            )
            
            return len(results.get('ids', [])) > 0
        except:
            return False
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding using failover system"""
        if self.failover_manager:
            try:
                return self.failover_manager.get_embeddings(text)
            except Exception as e:
                logger.warning(f"Failover embedding failed: {e}")
        
        # Fallback to deterministic embedding
        return self._deterministic_embedding(text)
    
    def _deterministic_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Generate deterministic embedding from text"""
        import hashlib
        import random
        
        h = hashlib.sha256(text.encode('utf-8')).digest()
        seed = int.from_bytes(h[:8], 'big')
        rnd = random.Random(seed)
        return [rnd.uniform(-1.0, 1.0) for _ in range(dim)]
    
    def process_and_add_file(self, file_path: Path, processor: GitHubRepoProcessor) -> bool:
        """Process a single file and add to database"""
        try:
            # Extract repository info
            repo_info = processor.extract_repo_info(file_path)
            
            # Read content
            if file_path.suffix.lower() == '.ipynb':
                content = processor.process_notebook(file_path)
            else:
                content = processor.read_file_content(file_path)
            
            if not content or len(content.strip()) < 50:
                return False
            
            # Create chunks
            chunks_data = processor.create_code_chunks(content, repo_info)
            
            if not chunks_data:
                return False
            
            # Generate embeddings and add to database
            for i, chunk_data in enumerate(chunks_data):
                chunk_text = chunk_data['content']
                metadata = chunk_data['metadata']
                
                # Generate embedding
                embedding = self.get_embedding(chunk_text)
                if not embedding:
                    continue
                
                # Create unique ID
                file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
                chunk_id = f"github_{file_hash}_{i}"
                
                # Enhanced metadata
                full_metadata = {
                    'source': 'github',
                    'source_path': metadata['relative_path'],
                    'repo_name': metadata['repo_name'],
                    'project_type': metadata['project_type'],
                    'file_type': metadata['file_type'],
                    'filename': file_path.name,
                    'chunk_index': i,
                    'primary_subject': 'programming',
                    'subject_hierarchy': f"GitHub > {metadata['repo_name']} > {metadata['project_type']}"
                }
                
                # Add to collection
                self.collection.add(
                    embeddings=[embedding],
                    documents=[chunk_text],
                    ids=[chunk_id],
                    metadatas=[full_metadata]
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            return False


def process_github_repositories(batch_size: int = 500, skip_existing: bool = True):
    """Main function to process GitHub repositories"""
    
    logger.info("="*80)
    logger.info("GITHUB REPOSITORY PROCESSOR")
    logger.info("="*80)
    
    # Initialize processor
    processor = GitHubRepoProcessor()
    
    # Analyze structure
    analysis = processor.analyze_github_structure()
    
    print(f"\nFound {analysis['total_files']} processable files in {analysis['total_repos']} repositories")
    print(f"Batch size: {batch_size}")
    print(f"Skip existing: {skip_existing}")
    
    # Ask for confirmation
    print("\nDo you want to proceed with processing? (y/n): ", end='')
    response = input().strip().lower()
    
    if response != 'y':
        logger.info("Processing cancelled")
        return
    
    # Initialize database integrator
    integrator = GitHubDatabaseIntegrator()
    if not integrator.initialize():
        logger.error("Failed to initialize database!")
        return
    
    # Process files
    files_to_process = analysis['files'][:batch_size]
    
    logger.info(f"\nProcessing {len(files_to_process)} files...")
    logger.info("="*80)
    
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    
    for i, file_path in enumerate(files_to_process, 1):
        if i % 50 == 0:
            logger.info(f"Progress: {i}/{len(files_to_process)} files "
                       f"(✓{processed_count} ⊘{skipped_count} ✗{failed_count})")
        
        # Check if already processed
        if skip_existing and integrator.file_already_processed(file_path, processor.github_directory):
            skipped_count += 1
            continue
        
        # Process file
        success = integrator.process_and_add_file(file_path, processor)
        
        if success:
            processed_count += 1
        else:
            failed_count += 1
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*80)
    logger.info(f"Successfully processed: {processed_count}")
    logger.info(f"Skipped (existing):    {skipped_count}")
    logger.info(f"Failed:                {failed_count}")
    logger.info(f"Total attempted:       {len(files_to_process)}")
    logger.info("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process GitHub repositories')
    parser.add_argument('--batch-size', type=int, default=500,
                       help='Number of files to process (default: 500)')
    parser.add_argument('--no-skip-existing', action='store_true',
                       help='Reprocess files that are already in database')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze structure, do not process files')
    
    args = parser.parse_args()
    
    if args.analyze_only:
        processor = GitHubRepoProcessor()
        processor.analyze_github_structure()
    else:
        process_github_repositories(
            batch_size=args.batch_size,
            skip_existing=not args.no_skip_existing
        )