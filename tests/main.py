"""
Main Test Module for EduSummarizeAI.

This module contains test cases for the application components.
"""

import os
import sys
import unittest
import tempfile
import json
#from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.pdf_extractor import PDFExtractor
from src.core.summarizer import ChapterSummarizer
from src.core.interactive_learning import InteractiveLearning
from src.core.worksheet_generator import WorksheetGenerator
from src.db.database import DatabaseManager
from src.utils.helpers import sanitize_filename, extract_concepts_from_markdown

# Configure test environment
TEST_PDF_PATH = os.path.join(os.path.dirname(__file__), "resources", "sample_textbook.pdf")
TEST_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


class TestPDFExtractor(unittest.TestCase):
    """Test cases for PDFExtractor."""
    
    def setUp(self):
        """Set up test environment."""
        # Skip tests if test PDF doesn't exist
        if not os.path.exists(TEST_PDF_PATH):
            self.skipTest("Test PDF not found. Please add a sample PDF at tests/resources/sample_textbook.pdf")
        
        self.extractor = PDFExtractor(TEST_PDF_PATH)
        self.temp_dir = tempfile.mkdtemp()
    
    def test_extract_text(self):
        """Test text extraction from PDF."""
        pages = self.extractor.extract_text()
        self.assertIsInstance(pages, list)
        self.assertGreater(len(pages), 0)
        self.assertIsInstance(pages[0], str)
    
    def test_detect_chapters(self):
        """Test chapter detection."""
        self.extractor.extract_text()
        chapters = self.extractor.detect_chapters()
        self.assertIsInstance(chapters, dict)
        
        # If no chapters detected, test custom ranges
        if not chapters:
            custom_ranges = {"Chapter 1": (0, 5), "Chapter 2": (6, 10)}
            chapters = self.extractor.detect_chapters(custom_ranges=custom_ranges)
            self.assertEqual(len(chapters), len(custom_ranges))
    
    def test_save_chapters(self):
        """Test saving chapters to files."""
        self.extractor.extract_text()
        self.extractor.detect_chapters()
        json_path = self.extractor.save_chapters(self.temp_dir)
        self.assertTrue(os.path.exists(json_path))
        
        # Check JSON content
        with open(json_path, 'r', encoding='utf-8') as f:
            chapters_data = json.load(f)
        self.assertIsInstance(chapters_data, dict)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager."""
    
    def setUp(self):
        """Set up test environment."""
        # Use in-memory SQLite database for testing
        self.db_manager = DatabaseManager(":memory:")
    
    def test_book_operations(self):
        """Test book CRUD operations."""
        # Create book
        book = self.db_manager.create_book("Test Book", "/path/to/test.pdf")
        self.assertIsNotNone(book.id)
        self.assertEqual(book.title, "Test Book")
        
        # Get book
        retrieved_book = self.db_manager.get_book(book.id)
        self.assertEqual(retrieved_book.title, book.title)
        
        # Get all books
        books = self.db_manager.get_all_books()
        self.assertGreaterEqual(len(books), 1)
    
    def test_chapter_operations(self):
        """Test chapter CRUD operations."""
        # Create book
        book = self.db_manager.create_book("Test Book", "/path/to/test.pdf")
        
        # Create chapter
        chapter = self.db_manager.create_chapter(
            book.id, 1, "Test Chapter", "This is test chapter content."
        )
        self.assertIsNotNone(chapter.id)
        self.assertEqual(chapter.title, "Test Chapter")
        
        # Get chapter
        retrieved_chapter = self.db_manager.get_chapter(chapter.id)
        self.assertEqual(retrieved_chapter.title, chapter.title)
        
        # Get chapters by book
        chapters = self.db_manager.get_chapters_by_book(book.id)
        self.assertEqual(len(chapters), 1)
    
    def test_summary_operations(self):
        """Test summary CRUD operations."""
        # Create book and chapter
        book = self.db_manager.create_book("Test Book", "/path/to/test.pdf")
        chapter = self.db_manager.create_chapter(
            book.id, 1, "Test Chapter", "This is test chapter content."
        )
        
        # Create summary
        summary = self.db_manager.create_summary(
            chapter.id, "This is a test summary."
        )
        self.assertIsNotNone(summary.id)
        
        # Get summary
        retrieved_summary = self.db_manager.get_summary(chapter.id)
        self.assertEqual(retrieved_summary.content, summary.content)
    
    def test_concept_operations(self):
        """Test concept CRUD operations."""
        # Create book and chapter
        book = self.db_manager.create_book("Test Book", "/path/to/test.pdf")
        chapter = self.db_manager.create_chapter(
            book.id, 1, "Test Chapter", "This is test chapter content."
        )
        
        # Create concept
        concept = self.db_manager.create_concept(
            chapter.id, "Test Concept", "This is a test explanation.",
            "This is a test example.", "This is a test analogy."
        )
        self.assertIsNotNone(concept.id)
        
        # Mark concept as understood
        updated_concept = self.db_manager.mark_concept_understood(concept.id, True)
        self.assertTrue(updated_concept.is_understood)
        
        # Get concepts by chapter
        concepts = self.db_manager.get_concepts_by_chapter(chapter.id)
        self.assertEqual(len(concepts), 1)


@unittest.skipIf(not TEST_API_KEY, "API key not available")
class TestChapterSummarizer(unittest.TestCase):
    """Test cases for ChapterSummarizer."""
    
    def setUp(self):
        """Set up test environment."""
        if not TEST_API_KEY:
            self.skipTest("API key not available. Set GOOGLE_API_KEY environment variable.")
        
        self.summarizer = ChapterSummarizer(TEST_API_KEY)
    
    def test_summarize_short_text(self):
        """Test summarization of a short text."""
        test_text = """
        This is a test chapter about machine learning. Machine learning is a field of artificial intelligence
        that uses statistical techniques to give computer systems the ability to "learn" from data, without
        being explicitly programmed. The name machine learning was coined in 1959 by Arthur Samuel.
        
        Supervised learning is the machine learning task of learning a function that maps an input to an output
        based on example input-output pairs. It infers a function from labeled training data.
        
        Unsupervised learning is a type of machine learning algorithm used to draw inferences from datasets
        consisting of input data without labeled responses.
        """
        
        summary = self.summarizer.summarize_chapter(test_text)
        self.assertIsInstance(summary, str)
        self.assertIn("machine learning", summary.lower())
    
    def test_extract_concepts(self):
        """Test concept extraction from summary."""
        test_summary = """
        # CHAPTER SUMMARY
        This chapter introduces machine learning concepts.
        
        # KEY CONCEPTS
        
        ## Machine Learning
        - **Explanation**: A field of AI that enables systems to learn from data.
        - **Example/Application**: Email spam filtering.
        - **Analogy**: Like teaching a child through examples.
        
        ## Supervised Learning
        - **Explanation**: Learning from labeled examples.
        - **Example/Application**: Predicting house prices.
        - **Analogy**: Learning with a teacher.
        """
        
        concepts = self.summarizer.extract_concepts(test_summary)
        self.assertIsInstance(concepts, list)
        self.assertGreaterEqual(len(concepts), 1)
        self.assertIn("name", concepts[0])
        self.assertIn("explanation", concepts[0])


@unittest.skipIf(not TEST_API_KEY, "API key not available")
class TestWorksheetGenerator(unittest.TestCase):
    """Test cases for WorksheetGenerator."""
    
    def setUp(self):
        """Set up test environment."""
        if not TEST_API_KEY:
            self.skipTest("API key not available. Set GOOGLE_API_KEY environment variable.")
        
        self.generator = WorksheetGenerator(TEST_API_KEY)
        self.temp_dir = tempfile.mkdtemp()
    
    def test_generate_worksheet_content(self):
        """Test worksheet content generation."""
        test_summary = "This is a test summary about machine learning concepts."
        test_concepts = [
            {
                "name": "Machine Learning",
                "explanation": "A field of AI that enables systems to learn from data.",
                "example": "Email spam filtering.",
                "analogy": "Like teaching a child through examples."
            }
        ]
        
        worksheet_content = self.generator.generate_worksheet_content(test_summary, test_concepts)
        self.assertIsInstance(worksheet_content, dict)
        self.assertIn("mcqs", worksheet_content)
        self.assertIn("one_liners", worksheet_content)
    
    def test_generate_pdf_worksheet(self):
        """Test PDF worksheet generation."""
        test_content = {
            "mcqs": [
                {
                    "question": "What is machine learning?",
                    "options": ["A", "B", "C", "D"],
                    "answer": "A",
                    "difficulty": "easy"
                }
            ],
            "one_liners": [
                {
                    "question": "Define AI.",
                    "answer": "Intelligence demonstrated by machines.",
                    "difficulty": "medium"
                }
            ],
            "brief_qa": [
                {
                    "question": "Explain supervised learning.",
                    "answer": "Learning from labeled examples.",
                    "difficulty": "hard"
                }
            ],
            "match_columns": {
                "column1": ["A", "B"],
                "column2": ["1", "2"],
                "matches": {"A": "1", "B": "2"}
            }
        }
        
        output_path = os.path.join(self.temp_dir, "test_worksheet.pdf")
        pdf_path = self.generator.generate_pdf_worksheet(test_content, output_path, "Test Chapter")
        self.assertTrue(os.path.exists(pdf_path))
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestHelpers(unittest.TestCase):
    """Test cases for helper functions."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        dirty_name = "My File Name! @#$%.pdf"
        clean_name = sanitize_filename(dirty_name)
        self.assertEqual(clean_name, "My_File_Name_pdf")
    
    def test_extract_concepts_from_markdown(self):
        """Test concept extraction from markdown."""
        markdown_text = """
        # CHAPTER SUMMARY
        This is a summary.
        
        # KEY CONCEPTS
        
        ## Concept 1
        - **Explanation**: This is explanation 1.
        - **Example/Application**: This is example 1.
        - **Analogy**: This is analogy 1.
        
        ## Concept 2
        - **Explanation**: This is explanation 2.
        - **Example/Application**: This is example 2.
        - **Analogy**: This is analogy 2.
        """
        
        concepts = extract_concepts_from_markdown(markdown_text)
        self.assertEqual(len(concepts), 2)
        self.assertEqual(concepts[0]["name"], "Concept 1")
        self.assertEqual(concepts[1]["name"], "Concept 2")


@unittest.skipIf(not TEST_API_KEY, "API key not available")
class TestIntegration(unittest.TestCase):
    """Integration tests for the application."""
    
    def setUp(self):
        """Set up test environment."""
        if not TEST_API_KEY:
            self.skipTest("API key not available. Set GOOGLE_API_KEY environment variable.")
        
        # Skip tests if test PDF doesn't exist
        if not os.path.exists(TEST_PDF_PATH):
            self.skipTest("Test PDF not found. Please add a sample PDF at tests/resources/sample_textbook.pdf")
        
        # Create temporary directory for output
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize components
        self.db_manager = DatabaseManager(":memory:")
        self.extractor = PDFExtractor(TEST_PDF_PATH)
        self.summarizer = ChapterSummarizer(TEST_API_KEY)
        self.worksheet_generator = WorksheetGenerator(TEST_API_KEY)
        self.interactive_learning = InteractiveLearning(self.db_manager, self.summarizer)
    
    def test_end_to_end_flow(self):
        """Test the end-to-end flow of the application."""
        # 1. Extract text from PDF
        pages = self.extractor.extract_text()
        self.assertGreater(len(pages), 0)
        
        # 2. Detect chapters
        chapters = self.extractor.detect_chapters()
        if not chapters:
            # If no chapters detected, use custom ranges
            chapters = self.extractor.detect_chapters(custom_ranges={"Chapter 1": (0, len(pages)-1)})
        
        # 3. Create book in database
        book = self.db_manager.create_book("Test Book", TEST_PDF_PATH)
        
        # 4. Create chapter in database
        chapter_name = list(chapters.keys())[0]
        chapter_text = chapters[chapter_name]
        chapter = self.db_manager.create_chapter(book.id, 1, chapter_name, chapter_text)
        
        # 5. Start learning session (generates summary and concepts)
        session = self.interactive_learning.start_learning_session(chapter.id)
        self.assertIn("summary", session)
        self.assertIn("concepts", session)
        
        # 6. Generate worksheet
        if session["concepts"]:
            concepts_data = [
                {
                    "name": concept["name"],
                    "explanation": concept["explanation"],
                    "example": concept["example"],
                    "analogy": concept["analogy"]
                }
                for concept in session["concepts"]
            ]
            
            worksheet_path, answer_key_path = self.worksheet_generator.generate_worksheet(
                session["summary"],
                concepts_data,
                self.temp_dir,
                chapter_name
            )
            
            self.assertTrue(os.path.exists(worksheet_path))
            self.assertTrue(os.path.exists(answer_key_path))
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
