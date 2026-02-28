"""
Scholar's Terminal - Transform your personal library into an AI-powered knowledge base
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="scholars-terminal",
    version="2.0.0",
    author="Vincent Micó",
    author_email="vincent.mico@proton.me",
    description="Transform your personal library into an AI-powered knowledge base with natural language search",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Vincent1949/scholars-terminal",
    project_urls={
        "Bug Tracker": "https://github.com/Vincent1949/scholars-terminal/issues",
        "Documentation": "https://github.com/Vincent1949/scholars-terminal#readme",
        "Source Code": "https://github.com/Vincent1949/scholars-terminal",
    },
    packages=find_packages(exclude=["tests*", "docs*", "frontend*", "examples*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Documentation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.0.0",
        "chromadb>=0.4.22",
        "PyPDF2>=3.0.1",
        "httpx>=0.26.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
        "tqdm>=4.66.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.12.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.5.0",
        ],
        "enhanced": [
            "sentence-transformers>=2.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scholars-terminal=Scholars_api:main",
            "build-knowledge-base=build_database:main",
        ],
    },
    include_package_data=True,
    keywords=[
        "knowledge base",
        "personal library",
        "semantic search",
        "rag",
        "retrieval augmented generation",
        "ai",
        "vector database",
        "chromadb",
        "ollama",
        "document search",
        "research",
        "education",
    ],
    zip_safe=False,
)
