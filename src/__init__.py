"""
EduSummarizeAI - AI-powered educational tool for summarizing content and generating practice worksheets.

This package provides functionality for:
- Extracting text from PDF books
- Summarizing chapters with key concepts
- Interactive learning with concept understanding tracking
- Generating practice worksheets
- Tracking learning progress
"""

__version__ = "0.1.0"
__author__ = "vansh-561"

# Import core components for easier access
from src.core import PDFExtractor, ChapterSummarizer, InteractiveLearning, WorksheetGenerator
from src.db.database import DatabaseManager
from ui.app import EduSummarizeApp

__all__ = [
    'PDFExtractor',
    'ChapterSummarizer',
    'InteractiveLearning',
    'WorksheetGenerator',
    'DatabaseManager',
    'EduSummarizeApp'
]
