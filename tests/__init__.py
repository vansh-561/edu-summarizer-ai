"""
Tests Package for EduSummarizeAI.

This package contains test modules for the application components.
"""

# Import test modules for easier access
from tests.main import (
    TestPDFExtractor,
    TestDatabaseManager,
    TestChapterSummarizer,
    TestWorksheetGenerator,
    TestHelpers,
    TestIntegration
)

__all__ = [
    'TestPDFExtractor',
    'TestDatabaseManager',
    'TestChapterSummarizer',
    'TestWorksheetGenerator',
    'TestHelpers',
    'TestIntegration'
]
