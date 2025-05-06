"""
Core Module for EduSummarizeAI.

This package contains the core functionality for the application, including:
- PDF text extraction
- Chapter summarization
- Interactive learning
- Worksheet generation
"""

# Import core components for easier access
from core.pdf_extractor import PDFExtractor
from core.summarizer import ChapterSummarizer
from core.interactive_learning import InteractiveLearning
from core.worksheet_generator import WorksheetGenerator

__all__ = [
    'PDFExtractor',
    'ChapterSummarizer',
    'InteractiveLearning',
    'WorksheetGenerator'
]
