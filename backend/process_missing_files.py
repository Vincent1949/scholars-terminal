#!/usr/bin/env python3
"""
Process Missing Files - Identifies and processes the few remaining files
"""

import sys
import logging
from pathlib import Path

# Add the current directory to the path so we can import from test_knowledge_chatbot
sys.path.insert(0, str(Path(__file__).parent))

# Import from the test module we created earlier
try:
    from test_knowledge_chatbot import DatabaseVerifier
    TEST_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Error: Cannot import DatabaseVerifier from test_knowledge_chatbot.py")
    print(f"Make sure test_knowledge_chatbot.py is in the same directory!")
    print(f"Import error: {e}")
    sys.exit(1)

# Import from the main chatbot module
try:
    from knowledge_chatbot import DocumentProcessor, VectorDatabase
    CHATBOT_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Error: Cannot import from knowledge_chatbot.py")
    print(f"Make sure knowledge_chatbot.py is in the same directory!")
    print(f"Import error: {e}")
    sys.exit(1)

# Import failover system
try:
    from llm_failover_system import LLMFailoverManager
    FAILOVER_AVAILABLE = True
except ImportError:
    print("Warning: LLM Failover system not available")
    FAILOVER_AVAILABLE = False
    class LLMFailoverManager:
        pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_and_process_missing_files():
    """Find the 9 missing files and process them"""
    
    logger.info("="*80)
    logger.info("FINDING AND PROCESSING MISSING FILES")
    logger.info("="*80)
    
    # Initialize verifier
    verifier = DatabaseVerifier()
    if not verifier.initialize_db_connection():
        logger.error("Failed to connect to database!")
        return
    
    # Get comparison results
    comparison = verifier.compare_source_vs_database()
    missing_files = comparison.get('missing_files', [])
    
    if not missing_files:
        logger.info("✓ No missing files! Database is complete.")
        return
    
    logger.info(f"\nFound {len(missing_files)} missing files:")
    logger.info("-"*80)
    for i, file_info in enumerate(missing_files, 1):
        logger.info(f"{i}. {file_info['relative_path']}")
        logger.info(f"   Size: {file_info['size_mb']:.2f} MB | Format: {file_info['format']}")
    logger.info("-"*80)
    
    # Ask user if they want to process
    print("\nDo you want to process these missing files now? (y/n): ", end='')
    response = input().strip().lower()
    
    if response != 'y':
        logger.info("Skipping processing. Exiting.")
        return
    
    # Initialize processing components
    logger.info("\nInitializing processing components...")
    
    doc_processor = DocumentProcessor()
    vector_db = VectorDatabase()
    
    if FAILOVER_AVAILABLE:
        failover_manager = LLMFailoverManager()
    else:
        failover_manager = None
    
    if not vector_db.initialize(failover_manager):
        logger.error("Failed to initialize vector database!")
        return
    
    # Process each missing file
    logger.info(f"\nProcessing {len(missing_files)} files...")
    logger.info("="*80)
    
    processed_count = 0
    failed_count = 0
    
    for i, file_info in enumerate(missing_files, 1):
        file_path = Path(file_info['path'])
        
        logger.info(f"\n[{i}/{len(missing_files)}] Processing: {file_path.name}")
        logger.info(f"  Path: {file_info['relative_path']}")
        logger.info(f"  Size: {file_info['size_mb']:.2f} MB")
        
        try:
            # Extract text
            if file_path.suffix.lower() == '.pdf':
                logger.info("  Extracting text from PDF...")
                text = doc_processor.extract_text_from_pdf(file_path)
                
                if not text or len(text.strip()) < 100:
                    logger.warning(f"  ⚠ Extracted text too short ({len(text)} chars) - may be scanned/image PDF")
                    failed_count += 1
                    continue
                
                logger.info(f"  ✓ Extracted {len(text)} characters")
                
                # Create chunks
                logger.info("  Creating text chunks...")
                chunks = doc_processor.create_chunks(text)
                logger.info(f"  ✓ Created {len(chunks)} chunks")
                
                if not chunks:
                    logger.warning("  ⚠ No chunks created")
                    failed_count += 1
                    continue
                
                # Create document info structure
                primary_subject, subject_hierarchy = doc_processor.extract_subject_from_path(file_path)
                
                doc_info = {
                    'path': file_path,
                    'primary_subject': primary_subject,
                    'subject_hierarchy': subject_hierarchy,
                    'filename': file_path.name,
                    'relative_path': file_info['relative_path'],
                    'file_size': file_path.stat().st_size
                }
                
                # Add to database
                logger.info("  Adding to vector database...")
                vector_db.add_document_with_structure(doc_info, chunks)
                logger.info(f"  ✓ Successfully added to database!")
                
                processed_count += 1
                
            elif file_path.suffix.lower() == '.epub':
                logger.info("  EPUB format - currently unsupported, skipping")
                failed_count += 1
            else:
                logger.warning(f"  Unsupported format: {file_path.suffix}")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"  ✗ Error processing file: {e}")
            failed_count += 1
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*80)
    logger.info(f"Successfully processed: {processed_count}")
    logger.info(f"Failed/Skipped:        {failed_count}")
    logger.info(f"Total database size:   {vector_db.document_count} documents")
    logger.info("="*80)


def show_detailed_missing_analysis():
    """Show detailed analysis of what's missing and why"""
    
    logger.info("="*80)
    logger.info("DETAILED MISSING FILES ANALYSIS")
    logger.info("="*80)
    
    verifier = DatabaseVerifier()
    if not verifier.initialize_db_connection():
        return
    
    comparison = verifier.compare_source_vs_database()
    missing_files = comparison.get('missing_files', [])
    
    if not missing_files:
        logger.info("✓ No missing files!")
        return
    
    # Analyze by format
    by_format = {}
    for file_info in missing_files:
        fmt = file_info['format']
        if fmt not in by_format:
            by_format[fmt] = []
        by_format[fmt].append(file_info)
    
    logger.info("\nMissing Files by Format:")
    logger.info("-"*80)
    for fmt, files in by_format.items():
        total_size = sum(f['size_mb'] for f in files)
        logger.info(f"{fmt:10s}: {len(files):3d} files ({total_size:.1f} MB total)")
    
    # Analyze by folder
    by_folder = {}
    for file_info in missing_files:
        rel_path = file_info['relative_path']
        folder = rel_path.split('\\')[0] if '\\' in rel_path else 'root'
        if folder not in by_folder:
            by_folder[folder] = []
        by_folder[folder].append(file_info)
    
    logger.info("\nMissing Files by Folder:")
    logger.info("-"*80)
    for folder, files in sorted(by_folder.items()):
        logger.info(f"{folder:30s}: {len(files):3d} files")
        for file_info in files[:3]:  # Show first 3
            logger.info(f"  - {file_info['filename']} ({file_info['size_mb']:.2f} MB)")
    
    # Analyze by size
    large_files = [f for f in missing_files if f['size_mb'] > 50]
    small_files = [f for f in missing_files if f['size_mb'] < 1]
    
    if large_files:
        logger.info(f"\nLarge Missing Files (>50MB): {len(large_files)}")
        for file_info in large_files:
            logger.info(f"  - {file_info['filename']}: {file_info['size_mb']:.1f} MB")
    
    if small_files:
        logger.info(f"\nSmall Missing Files (<1MB): {len(small_files)}")
        for file_info in small_files[:5]:
            logger.info(f"  - {file_info['filename']}: {file_info['size_mb']:.2f} MB")
    
    logger.info("\n" + "="*80)


if __name__ == "__main__":
    print("\nMissing Files Analysis and Processing Tool")
    print("="*80)
    print("Options:")
    print("  1. Show detailed analysis of missing files")
    print("  2. Process missing files now")
    print("  3. Both (analysis then processing)")
    print("="*80)
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        show_detailed_missing_analysis()
    elif choice == '2':
        find_and_process_missing_files()
    elif choice == '3':
        show_detailed_missing_analysis()
        print("\n")
        find_and_process_missing_files()
    else:
        print("Invalid choice. Exiting.")