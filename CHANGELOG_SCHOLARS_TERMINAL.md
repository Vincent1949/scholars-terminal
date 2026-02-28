# Changelog - Scholar's Terminal

All notable changes to Scholar's Terminal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-02-28

### 🎉 Initial Public Release

**Scholar's Terminal is now open source!** Transform your personal library into an AI-powered knowledge base.

### Added

#### Core Features
- **Universal Search** - Query your entire library with natural language
- **Precise Citations** - Get exact page numbers and source references
- **Open in PDF** - Click to view diagrams and figures in context
- **Multiple Source Types** - Index books, code, papers, and documents together
- **YAML Configuration** - Easy setup, no coding required
- **Resume Support** - Interrupted builds can pick up where they left off
- **Cross-Platform** - Works on Windows, macOS, and Linux

#### Technical Stack
- **Backend:** FastAPI + Python 3.8+
- **Frontend:** React 18 + Vite
- **Vector Database:** ChromaDB for semantic search
- **LLM:** Ollama for local, privacy-first AI
- **Document Processing:** PyPDF2 for text extraction

#### Database Building
- Progress tracking with JSON state files
- Enhanced metadata extraction (page numbers, figures)
- Configurable chunk sizes and file limits
- Support for large files (up to 400MB PDFs)
- Smart duplicate detection via file hashing

#### User Interface
- Clean, modern React interface
- Real-time search results
- Source attribution with page numbers
- PDF viewer integration
- Dark mode support

### Documentation
- Comprehensive README with quick start
- Database setup guide
- Configuration reference
- Feature documentation (Open PDF Feature)
- Contributing guidelines
- Example scripts

### Configuration
- Environment-based configuration (.env support)
- Flexible path configuration
- Multiple Ollama model support
- Configurable chunking parameters

---

## Development History

### Pre-Release Development (Jan-Feb 2026)
- Developed core indexing system
- Built React frontend
- Integrated ChromaDB vector database
- Added Ollama LLM support
- Created configuration system
- Implemented PDF metadata extraction
- Built progress tracking system
- Extensive testing with 13,000+ file library

---

## Future Roadmap

### Planned for v2.1.0
- [ ] EPUB file support
- [ ] DOCX file support
- [ ] Enhanced code indexing
- [ ] Multi-language support
- [ ] Advanced filtering options

### Under Consideration
- [ ] Cloud sync options
- [ ] Collaborative features
- [ ] Mobile app
- [ ] Browser extension
- [ ] API for third-party integrations

---

## Migration Notes

### For Existing Users
If you've been using Scholar's Terminal before this public release:

1. **Database Compatibility:** Your existing vector databases are compatible
2. **Configuration:** Migrate to `.env` file for paths (see `.env.example`)
3. **Scripts:** Old launch scripts still work, but consider using the new standardized versions

### Breaking Changes
- None for v2.0.0 (initial release)

---

## Acknowledgments

Built with:
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Ollama](https://ollama.ai/) - Local LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - UI framework
- [Vite](https://vitejs.dev/) - Frontend build tool

---

**Note:** This changelog will be updated with each release. For detailed commit history, see the Git log.
