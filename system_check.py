"""
System Check Script
Verify all dependencies and configurations for the AI Knowledge Base system
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("  ⚠️  Warning: Python 3.10+ recommended")
        return False
    else:
        print("  ✓ Version OK")
        return True

def check_module(module_name, package_name=None):
    """Check if a module can be imported"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"  ✓ {package_name}")
        return True
    except ImportError:
        print(f"  ✗ {package_name} - NOT INSTALLED")
        return False

def check_dependencies():
    """Check all required Python packages"""
    print("\nChecking Python packages...")
    
    dependencies = [
        ("PyPDF2", "PyPDF2"),
        ("ebooklib", "ebooklib"),
        ("bs4", "beautifulsoup4"),
        ("chromadb", "chromadb"),
        ("langchain.text_splitter", "langchain"),
        ("sentence_transformers", "sentence-transformers"),
        ("openai", "openai"),
    ]
    
    all_ok = True
    for module, package in dependencies:
        if not check_module(module, package):
            all_ok = False
    
    return all_ok

def check_environment():
    """Check environment variables"""
    print("\nChecking environment variables...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"  ✓ OPENAI_API_KEY is set ({api_key[:8]}...)")
        return True
    else:
        print("  ⚠️  OPENAI_API_KEY not set")
        print("     Set it with: export OPENAI_API_KEY='your-key-here'")
        return False

def check_directories():
    """Check required directories"""
    print("\nChecking directories...")
    
    books_dir = Path(r"D:\Books")
    if books_dir.exists():
        # Count files
        file_count = sum(1 for _ in books_dir.rglob('*') if _.is_file())
        print(f"  ✓ Books directory exists: {books_dir}")
        print(f"    Contains {file_count} files")
        
        # Count by extension
        pdf_count = len(list(books_dir.rglob('*.pdf')))
        epub_count = len(list(books_dir.rglob('*.epub')))
        txt_count = len(list(books_dir.rglob('*.txt')))
        
        if pdf_count > 0:
            print(f"    PDFs: {pdf_count}")
        if epub_count > 0:
            print(f"    EPUBs: {epub_count}")
        if txt_count > 0:
            print(f"    TXTs: {txt_count}")
        
        books_ok = True
    else:
        print(f"  ⚠️  Books directory not found: {books_dir}")
        print("     Update BOOKS_DIR in document_processor.py")
        books_ok = False
    
    db_dir = Path("./chroma_db")
    if db_dir.exists():
        print(f"  ✓ Database directory exists: {db_dir}")
    else:
        print(f"  ℹ️  Database directory not found (will be created on first run)")
    
    return books_ok

def check_database():
    """Check ChromaDB database"""
    print("\nChecking database...")
    
    db_path = Path("./chroma_db")
    if not db_path.exists():
        print("  ℹ️  Database not initialized yet")
        print("     Run document_processor.py to create it")
        return False
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_collection(name="knowledge_base")
        count = collection.count()
        
        print(f"  ✓ Database initialized")
        print(f"    Contains {count} chunks")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️  Database exists but couldn't access it: {e}")
        return False

def check_system_resources():
    """Check system resources"""
    print("\nChecking system resources...")
    
    try:
        import psutil
        
        # RAM
        ram = psutil.virtual_memory()
        ram_gb = ram.total / (1024**3)
        ram_available_gb = ram.available / (1024**3)
        print(f"  RAM: {ram_gb:.1f}GB total, {ram_available_gb:.1f}GB available")
        
        # CPU
        cpu_count = psutil.cpu_count()
        print(f"  CPU: {cpu_count} cores")
        
        # Disk space
        disk = psutil.disk_usage('.')
        disk_free_gb = disk.free / (1024**3)
        print(f"  Disk space: {disk_free_gb:.1f}GB free")
        
        if ram_gb < 8:
            print("  ⚠️  Warning: Less than 8GB RAM")
        
        return True
        
    except ImportError:
        print("  ℹ️  Install psutil for detailed system info")
        return True

def main():
    """Run all checks"""
    print("="*60)
    print("AI Knowledge Base - System Check")
    print("="*60)
    
    results = {
        "Python version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Environment": check_environment(),
        "Directories": check_directories(),
        "Database": check_database(),
        "System resources": check_system_resources()
    }
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    for check, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ All checks passed! System is ready.")
    else:
        print("\n⚠️  Some checks failed. See details above.")
        print("\nTo install missing packages:")
        print("  pip install -r requirements.txt")
    
    print("="*60)

if __name__ == "__main__":
    main()