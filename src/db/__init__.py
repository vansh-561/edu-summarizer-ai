"""
Database Module for EduSummarizeAI.

This package contains database functionality for the application, including:
- Database models
- CRUD operations
- User progress tracking
"""

# Import database components for easier access
from db.database import DatabaseManager, Book, Chapter, Summary, Concept, Worksheet, UserProgress

__all__ = [
    'DatabaseManager',
    'Book',
    'Chapter',
    'Summary',
    'Concept',
    'Worksheet',
    'UserProgress'
]
