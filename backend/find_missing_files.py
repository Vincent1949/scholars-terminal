#!/usr/bin/env python3
"""
Simple Missing Files Finder - Standalone version
Finds the 9 missing files without complex imports
"""

import logging
from pathlib import Path
from collections import defaultdict
import chromadb

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_missing_files():
    """Simple standalone function to find missing files"""
    
    logger.info("="*80)
    logger.info("FINDING MISSING FILES")
    logger.info("="*80)
    
    # Settings
    books_directory = Path("D:/Books")
    db_path = Path("./data/vector_db")
    supported_formats = ['.pdf', '.epub']
    
    # Step 1: Scan source files
    logger.info(f"\nScanning {books_directory} for source files...")
    
    all_source_files = []
    for ext in supported_formats:
        files = list(books_directory.glob(f"**/*{ext}"))
        all_source_files.extend(files)
        logger.info(f"Found {len(files)} {ext} files")
    
    logger.info(f"Total source files: {len(all_source_files)}")
    
    # Create lookup by relative path
    source_by_relative_path = {}
    for file_path in all_source_files:
        try:
            rel_path = str(file_path.relative_to(books_directory))
            source_by_relative_path[rel_path] = file_path
        except:
            pass
    
    # Step 2: Connect to database
    logger.info(f"\nConnecting to database at {db_path}...")
    
    try:
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_collection("knowledge_base")
        logger.info("✓ Connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return
    
    # Step 3: Get all files in database
    logger.info("\nGetting files from database...")
    
    all_docs = collection.get()
    
    if not all_docs or not all_docs.get('metadatas'):
        logger.error("Database is empty!")
        return
    
    db_files = set()
    for metadata in all_docs['metadatas']:
        relative_path = metadata.get('relative_path', '')
        if relative_path:
            db_files.add(relative_path)
    
    logger.info(f"Database contains {len(db_files)} unique files")
    
    # Step 4: Find missing files
    logger.info("\nComparing source vs database...")
    
    missing_files = []
    for rel_path, file_path in source_by_relative_path.items():
        if rel_path not in db_files:
            missing_files.append({
                'path': str(file_path),
                'relative_path': rel_path,
                'filename': file_path.name,
                'size_mb': file_path.stat().st_size / (1024 * 1024),
                'format': file_path.suffix
            })
    
    # Step 5: Display results
    logger.info("\n" + "="*80)
    logger.info("RESULTS")
    logger.info("="*80)
    logger.info(f"Total source files:    {len(all_source_files)}")
    logger.info(f"Files in database:     {len(db_files)}")
    logger.info(f"Missing files:         {len(missing_files)}")
    logger.info(f"Coverage:              {(len(db_files)/len(all_source_files)*100):.1f}%")
    logger.info("="*80)
    
    if missing_files:
        logger.info(f"\nMISSING FILES ({len(missing_files)}):")
        logger.info("-"*80)
        
        # Analyze by format
        by_format = defaultdict(list)
        for f in missing_files:
            by_format[f['format']].append(f)
        
        for fmt, files in by_format.items():
            total_size = sum(f['size_mb'] for f in files)
            logger.info(f"\n{fmt.upper()} files: {len(files)} (Total: {total_size:.1f} MB)")
            for i, file_info in enumerate(files, 1):
                logger.info(f"  {i}. {file_info['filename']} ({file_info['size_mb']:.2f} MB)")
                logger.info(f"     Path: {file_info['relative_path']}")
        
        # Analyze by folder
        logger.info("\n" + "-"*80)
        logger.info("MISSING FILES BY FOLDER:")
        by_folder = defaultdict(list)
        for f in missing_files:
            folder = f['relative_path'].split('\\')[0] if '\\' in f['relative_path'] else 'root'
            by_folder[folder].append(f)
        
        for folder, files in sorted(by_folder.items()):
            logger.info(f"\n{folder}: {len(files)} files")
            for f in files:
                logger.info(f"  - {f['filename']}")
        
        # Save to file
        output_file = Path("missing_files_report.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("MISSING FILES REPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Total source files:    {len(all_source_files)}\n")
            f.write(f"Files in database:     {len(db_files)}\n")
            f.write(f"Missing files:         {len(missing_files)}\n\n")
            
            for file_info in missing_files:
                f.write(f"\nFile: {file_info['filename']}\n")
                f.write(f"Path: {file_info['relative_path']}\n")
                f.write(f"Size: {file_info['size_mb']:.2f} MB\n")
                f.write(f"Format: {file_info['format']}\n")
                f.write("-"*80 + "\n")
        
        logger.info(f"\n✓ Detailed report saved to: {output_file}")
    else:
        logger.info("\n✓ No missing files! Database is complete.")
    
    logger.info("\n" + "="*80)


if __name__ == "__main__":
    find_missing_files()