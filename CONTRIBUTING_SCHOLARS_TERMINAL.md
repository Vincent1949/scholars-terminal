# Contributing to Scholar's Terminal

Thank you for your interest in contributing to Scholar's Terminal! This document provides guidelines for contributing to the project.

---

## 🌟 Ways to Contribute

### 1. Report Bugs
Open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version)
- Relevant log files

### 2. Suggest Features
We welcome feature suggestions! Please:
- Check existing issues first
- Describe the use case
- Explain how it would benefit users
- Consider implementation complexity

### 3. Improve Documentation
- Fix typos or unclear sections
- Add examples and tutorials
- Improve installation instructions
- Create video walkthroughs
- Translate documentation

### 4. Submit Code
- Bug fixes
- Performance improvements
- New features
- Test coverage improvements

---

## 🔧 Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Ollama installed
- Git

### Clone and Setup

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/scholars-terminal.git
cd scholars-terminal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Running Tests

```bash
# Backend tests
pytest

# Type checking
mypy backend/

# Code formatting
black backend/
flake8 backend/
```

---

## 📝 Code Style

### Python
- Follow PEP 8
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and small
- Use meaningful variable names

### Example:
```python
def extract_pdf_text(file_path: Path, max_pages: int = None) -> str:
    \"\"\"
    Extract text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        max_pages: Optional limit on pages to process
        
    Returns:
        Extracted text content
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        PyPDF2.PdfReadError: If PDF is corrupted
    \"\"\"
    # Implementation
```

### JavaScript/React
- Use functional components and hooks
- Prefer const over let
- Use meaningful component names
- Add PropTypes or TypeScript types
- Keep components focused

---

## 🔀 Pull Request Process

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes
- Write clear, focused commits
- Add tests for new functionality
- Update documentation
- Ensure all tests pass

### 3. Commit Guidelines
Follow the conventional commits format:

```
feat: Add support for EPUB files
fix: Resolve ChromaDB connection timeout
docs: Update installation instructions
perf: Optimize PDF text extraction
test: Add tests for metadata extraction
```

### 4. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear title and description
- Reference any related issues
- Screenshots for UI changes
- Test results

---

## 🧪 Testing Guidelines

### What to Test
- New features
- Bug fixes
- Edge cases
- Performance improvements

### Test Structure
```python
def test_pdf_extraction_basic():
    \"\"\"Test basic PDF text extraction\"\"\"
    # Arrange
    pdf_path = Path("tests/data/sample.pdf")
    
    # Act
    text = extract_pdf_text(pdf_path)
    
    # Assert
    assert len(text) > 0
    assert "expected content" in text
```

---

## 📚 Documentation

### Update These When Changing Features:
- `README.md` - Main overview
- `docs/INSTALLATION.md` - Setup instructions
- `docs/QUICKSTART.md` - Quick start guide
- `examples/` - Add example scripts
- Inline code comments

### Writing Good Documentation:
- Be clear and concise
- Include examples
- Explain the "why" not just the "how"
- Keep it up to date

---

## 🤝 Code Review

### What We Look For:
- ✅ Code works as intended
- ✅ Tests pass
- ✅ Follows style guidelines
- ✅ Documentation updated
- ✅ No unnecessary complexity
- ✅ Good variable/function names

### Review Process:
1. Automated checks run (tests, linting)
2. Maintainer reviews code
3. Feedback and discussion
4. Revisions if needed
5. Approval and merge

---

## 💡 Getting Help

- **Questions:** Open a GitHub Discussion
- **Bugs:** Open a GitHub Issue
- **Security:** Email vincent.mico@proton.me

---

## 🏆 Recognition

Contributors will be:
- Added to the contributors list
- Mentioned in release notes
- Credited in documentation

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for making Scholar's Terminal better!** 🙏
