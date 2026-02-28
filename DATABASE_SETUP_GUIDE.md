# Building Your Knowledge Base

Scholar's Terminal uses a flexible configuration system that allows you to index content from multiple sources: books, code repositories, research papers, personal documents, or any other text-based content.

## Quick Start

### 1. Configure Your Sources

Edit `database_config.yaml` to point to your content:

```yaml
sources:
  - name: "My Books"
    path: "/path/to/your/books"
    type: "books"
    enabled: true
    extensions:
      - .pdf
      - .txt
      - .md
```

### 2. Build the Database

```bash
python build_database.py
```

### 3. Start Scholar's Terminal

```bash
python Scholars_api.py
```

That's it! Your knowledge base is ready to search.

---

## Detailed Configuration Guide

### Understanding Sources

Each "source" in `database_config.yaml` represents a folder containing content you want to search. You can have as many sources as you want.

### Source Configuration

Each source has these properties:

```yaml
- name: "Friendly Name"          # What to call this source
  path: "/path/to/folder"        # Where the files are
  type: "books"                  # Type: books, code, research, documents
  enabled: true                  # true = index it, false = skip it
  extensions:                    # Which file types to process
    - .pdf
    - .txt
  description: "Optional notes"  # For your reference
```

### Common Scenarios

#### Scenario 1: Technical Books Collection

```yaml
- name: "Technical Books"
  path: "D:/Books/Technical"
  type: "books"
  enabled: true
  extensions:
    - .pdf
    - .epub
    - .mobi
  description: "Programming and computer science books"
```

#### Scenario 2: Code Repositories

```yaml
- name: "My GitHub Projects"
  path: "C:/Users/YourName/GitHub"
  type: "code"
  enabled: true
  extensions:
    - .py
    - .js
    - .java
    - .cpp
    - .md
  description: "Source code for documentation search"
```

#### Scenario 3: Research Papers

```yaml
- name: "Research Papers"
  path: "/Users/yourname/Documents/Papers"
  type: "research"
  enabled: true
  extensions:
    - .pdf
  description: "Academic papers and publications"
```

#### Scenario 4: Multiple Book Collections

```yaml
sources:
  - name: "Technical Books"
    path: "D:/Books/Technical"
    type: "books"
    enabled: true
    extensions: [.pdf, .epub]
  
  - name: "Fiction"
    path: "D:/Books/Fiction"
    type: "books"
    enabled: true
    extensions: [.pdf, .epub]
  
  - name: "Reference Materials"
    path: "D:/Books/Reference"
    type: "books"
    enabled: true
    extensions: [.pdf]
```

### Path Formats

**Windows:**
```yaml
path: "C:/Users/YourName/Documents"  # Forward slashes work
path: "D:\\Books"                     # Or backslashes (escaped)
```

**Mac/Linux:**
```yaml
path: "/Users/yourname/Documents"
path: "/home/yourname/books"
```

**Relative paths:**
```yaml
path: "./my-books"                    # Relative to project directory
```

---

## File Types Support

### Supported File Types

| Extension | Description | Notes |
|-----------|-------------|-------|
| `.pdf` | PDF documents | Most common for books/papers |
| `.txt` | Plain text | Fast to process |
| `.md` | Markdown | Great for documentation |
| `.py` | Python code | For code search |
| `.js` | JavaScript | For code search |
| `.ts` | TypeScript | For code search |
| `.java` | Java code | For code search |
| `.cpp` | C++ code | For code search |

### Adding File Types

To process additional file types, add them to the `extensions` list:

```yaml
extensions:
  - .pdf
  - .txt
  - .md
  - .rst      # ReStructuredText
  - .tex      # LaTeX documents
  - .html     # HTML files
```

**Note:** All text-based files are supported. Binary formats (images, videos) are ignored.

---

## Advanced Settings

### Processing Settings

Control how files are chunked:

```yaml
processing:
  chunk_size: 1000          # Characters per chunk (default: 1000)
  chunk_overlap: 200        # Overlap between chunks (default: 200)
  min_chunk_size: 100       # Skip chunks smaller than this
  max_chunks_per_file: 5000 # Safety limit per file (default: 5000)
  batch_size: 100           # Documents per batch to database (default: 100)
```

#### Understanding the Parameters

**chunk_size: 1000**
- How many characters per searchable chunk
- 1000 chars ≈ 200 words ≈ 1 paragraph
- **Larger (1500-2000):** Better for finding broad concepts, fewer chunks
- **Smaller (500-800):** Better for precise information, more chunks

**chunk_overlap: 200**
- How much chunks overlap (prevents splitting concepts)
- 200 chars = ~20% overlap with 1000 char chunks
- **More overlap (300-400):** Better context preservation, larger database
- **Less overlap (100):** Smaller database, risk of splitting important context

**min_chunk_size: 100**
- Skip chunks smaller than this
- Filters out noise (page numbers, headers, footers)
- Usually don't need to change this

**max_chunks_per_file: 5000**
- Maximum chunks to extract from a single file
- **This is important!** Prevents runaway processing
- 5000 chunks × 1000 chars = 5,000,000 chars = ~1000 pages
- **If you see "Reached max chunks" warnings:**
  - Your books are longer than expected (good problem!)
  - Increase to 7500 or 10000 to capture full books
  - Or leave it - 1000 pages is usually enough

**batch_size: 100**
- How many chunks to add to database at once
- **Higher (200-500):** Faster processing, more memory
- **Lower (25-50):** Slower processing, less memory
- 100 is a good balance

#### Real-World Impact

**Example: 500-page technical book**
- Total text: ~1,500,000 characters
- At 1000 chars/chunk: ~1500 chunks
- With max_chunks_per_file = 1000: ❌ Only first 667 pages indexed
- With max_chunks_per_file = 5000: ✅ Full book indexed

**Example: Database size**
- 1000 books × 500 pages average
- 1000 chars/chunk, 200 overlap
- ~1.5 million chunks total
- Database size: ~70-100 GB

### File Size Limits

Prevent processing very large files:

```yaml
limits:
  max_file_size_mb: 150     # Skip files larger than this (default: 150)
  warn_file_size_mb: 50     # Show warning for large files (default: 50)
```

#### Why These Limits?

**max_file_size_mb: 150**
- Prevents processing giant files that might be:
  - Image-heavy PDFs (scanned books with 300+ DPI images)
  - Video/audio files accidentally included
  - Corrupted or invalid files
- Most text-based PDFs are under 150 MB
- **Technical PDFs with diagrams:** 20-80 MB is common
- **Pure text books:** Usually 1-10 MB

**warn_file_size_mb: 50**
- Shows a warning but still processes the file
- Alerts you to unusually large files
- Helps identify image-heavy scans vs. text PDFs

#### When to Adjust

**If you have large technical books:**
```yaml
max_file_size_mb: 250      # Handle large engineering PDFs
warn_file_size_mb: 100     # Only warn for very large files
```

**If you only have text documents:**
```yaml
max_file_size_mb: 50       # Stricter limit
warn_file_size_mb: 20      # Catch image-heavy files
```

**If you want to process everything:**
```yaml
max_file_size_mb: 1000     # Very permissive
warn_file_size_mb: 100     # Only warn for huge files
```

#### File Size Reference

| File Type | Typical Size | Example |
|-----------|--------------|---------|
| Text-only PDF (300 pages) | 1-5 MB | Novel |
| Technical book with diagrams | 20-50 MB | Programming book |
| Engineering textbook | 50-100 MB | Heavy diagrams |
| Scanned book (high quality) | 100-200 MB | Scanned archive |
| Scanned book (very high res) | 200+ MB | Usually unnecessary |

**Recommendation:** Keep defaults (150 MB max, 50 MB warn) - handles 99% of books while filtering obvious problems.

### Exclusions

**Exclude specific directories:**

```yaml
exclude_dirs:
  - node_modules      # JavaScript dependencies
  - __pycache__       # Python cache
  - .git              # Version control
  - tests             # Test files
  - your-folder-name  # Add your own
```

**Exclude specific files:**

```yaml
exclude_files:
  - .gitignore
  - README.md         # If you don't want READMEs
  - "*.log"           # Pattern matching with wildcards
```

---

## Building the Database

### First Build

```bash
python build_database.py
```

**What happens:**
1. Scans all enabled sources
2. Finds files matching your extensions
3. Processes each file (reads, chunks, embeds)
4. Adds chunks to ChromaDB database
5. Saves progress periodically

**Expected time:**
- 1,000 books: ~30-60 minutes
- 10,000 books: ~2-4 hours
- Depends on: file sizes, CPU speed, disk speed

### Resuming Interrupted Builds

If the build is interrupted (power loss, error, Ctrl+C):

```bash
python build_database.py
```

**The script automatically:**
- Loads previous progress
- Skips already-processed files
- Continues where it left off

Progress is saved in `database_build_progress.json`

### Adding New Content

To add new sources or files to an existing database:

1. **Edit `database_config.yaml`:**
   - Add new source
   - Or enable a previously disabled source

2. **Run the builder:**
   ```bash
   python build_database.py
   ```

3. **Only new files are processed** (existing files are skipped)

### Starting Fresh

To rebuild from scratch:

1. **Delete the database:**
   ```bash
   rm -rf ./data/vector_db
   ```

2. **Delete progress file:**
   ```bash
   rm database_build_progress.json
   ```

3. **Run the builder:**
   ```bash
   python build_database.py
   ```

---

## Monitoring Progress

### During Build

The builder shows:
```
Processing: My Books
   Found: 1,234 files

Processing My Books: 45%|████▌     | 556/1234 [15:23<17:32, 1.55s/file]
```

### After Build

Final summary shows:
```
📚 My Books:
   Files: 1,234
   Chunks: 567,890

📊 Total Statistics:
   Files processed: 1,234
   Chunks created: 567,890
   Failed files: 5

💾 Database:
   Total documents: 567,890
```

### Log Files

Check `database_build.log` for:
- Detailed progress
- Errors and warnings
- Files that failed to process

---

## Troubleshooting

### "No sources enabled"

**Problem:** All sources have `enabled: false`

**Solution:** Set at least one source to `enabled: true`

### "Source path does not exist"

**Problem:** The path doesn't exist on your system

**Solution:** 
- Check the path is correct
- Use full absolute paths
- Check spelling and capitalization

### "No files found"

**Problem:** No files match your extensions in that path

**Solution:**
- Check `extensions` list matches your files
- Verify files exist in subdirectories
- Check `exclude_dirs` isn't blocking folders

### Build is very slow

**Normal:** Processing thousands of files takes time

**Speed it up:**
- Reduce `chunk_size` (smaller chunks = faster, but less context)
- Increase `batch_size` (more chunks per batch = faster)
- Use faster storage (SSD instead of HDD)
- Close other applications

### Some files fail to process

**Normal:** 1-2% failure rate is expected

**Common causes:**
- Encrypted/password-protected PDFs
- Corrupted files
- Unsupported PDF features
- Very large files (over size limit)

**Check:** Look in `database_build.log` for specific errors

### "Module not found" errors

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Database Location

The database is stored in:
```
./data/vector_db/
```

This folder contains:
- `chroma.sqlite3` - Main database file
- Collection folders (UUID names)

**Size estimates:**
- 1,000 books: ~5-10 GB
- 10,000 books: ~50-100 GB

**Backup:** Copy the entire `vector_db` folder

**Share:** Copy `vector_db` to another machine with Scholar's Terminal

---

## Example Configurations

### For Students

```yaml
sources:
  - name: "Textbooks"
    path: "~/Documents/Textbooks"
    type: "books"
    enabled: true
    extensions: [.pdf]
  
  - name: "Lecture Notes"
    path: "~/Documents/Notes"
    type: "documents"
    enabled: true
    extensions: [.txt, .md]
  
  - name: "Research Papers"
    path: "~/Documents/Research"
    type: "research"
    enabled: true
    extensions: [.pdf]
```

### For Developers

```yaml
sources:
  - name: "Technical Books"
    path: "~/Books/Programming"
    type: "books"
    enabled: true
    extensions: [.pdf, .epub]
  
  - name: "My Projects"
    path: "~/GitHub"
    type: "code"
    enabled: true
    extensions: [.py, .js, .md, .txt]
  
  - name: "Documentation"
    path: "~/Documents/Dev-Notes"
    type: "documents"
    enabled: true
    extensions: [.md, .txt]
```

### For Researchers

```yaml
sources:
  - name: "Journal Articles"
    path: "/data/papers/journals"
    type: "research"
    enabled: true
    extensions: [.pdf]
  
  - name: "Conference Papers"
    path: "/data/papers/conferences"
    type: "research"
    enabled: true
    extensions: [.pdf]
  
  - name: "Preprints"
    path: "/data/papers/arxiv"
    type: "research"
    enabled: true
    extensions: [.pdf]
  
  - name: "Lab Notes"
    path: "/data/notes"
    type: "documents"
    enabled: true
    extensions: [.txt, .md]
```

---

## Next Steps

After building your database:

1. **Start the API:**
   ```bash
   python Scholars_api.py
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open Scholar's Terminal:**
   Visit `http://localhost:5173` in your browser

4. **Start searching!**

---

## Getting Help

- Check `database_build.log` for errors
- Review this guide for configuration help
- See main README.md for general Scholar's Terminal help
- Open an issue on GitHub for bugs/questions
