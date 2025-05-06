"""
Main UI Application for EduSummarizeAI.

This module provides the Streamlit-based user interface for the application.
"""

import os
import sys
#import json
import streamlit as st
#from typing import Dict, List, Optional
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pdf_extractor import PDFExtractor
from core.summarizer import ChapterSummarizer
from core.interactive_learning import InteractiveLearning
from core.worksheet_generator import WorksheetGenerator
from db.database import DatabaseManager


# Access environment variables
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

st.set_option('client.showErrorDetails', False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EduSummarizeApp:
    """Main application class for EduSummarizeAI."""
    
    def __init__(self):
        """Initialize the application."""
        # Set page config
        st.set_page_config(
            page_title="EduSummarizeAI",
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        if "initialized" not in st.session_state:
            st.session_state.initialized = False
            st.session_state.api_key = os.environ.get("GOOGLE_API_KEY", "")
            st.session_state.current_book = None
            st.session_state.current_chapter = None
            st.session_state.current_concept = None
            st.session_state.db_manager = None
            st.session_state.summarizer = None
            st.session_state.interactive_learning = None
            st.session_state.worksheet_generator = None
        
        # Initialize components if API key is available
        if st.session_state.api_key and not st.session_state.initialized:
            self._initialize_components()
    
    def _initialize_components(self):
        """Initialize application components."""
        try:
            # Initialize database manager
            st.session_state.db_manager = DatabaseManager()
            
            # Initialize Gemini components
            st.session_state.summarizer = ChapterSummarizer(st.session_state.api_key)
            st.session_state.worksheet_generator = WorksheetGenerator(st.session_state.api_key)
            
            # Initialize interactive learning
            st.session_state.interactive_learning = InteractiveLearning(
                st.session_state.db_manager,
                st.session_state.summarizer
            )
            
            st.session_state.initialized = True
            logger.info("Application components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            st.error(f"Error initializing application: {str(e)}")
    
    def run(self):
        """Run the application."""
        # Display title
        st.title("📚 EduSummarizeAI")
        st.write("AI-powered educational tool for summarizing content and generating practice worksheets")
        
        # Sidebar
        self._render_sidebar()
        
        # Check if API key is set
        if not st.session_state.api_key:
            st.warning("Please enter your Google API key in the sidebar to continue.")
            return
        
        # Check if components are initialized
        if not st.session_state.initialized:
            self._initialize_components()
            if not st.session_state.initialized:
                st.error("Failed to initialize application components. Please check your API key.")
                return
        
        # Main content
        if st.session_state.current_book is None:
            self._render_book_list()
        elif st.session_state.current_chapter is None:
            self._render_chapter_list()
        else:
            self._render_chapter_content()
    
    def _render_sidebar(self):
        """Render the sidebar."""
        with st.sidebar:
            st.header("Settings")
            
            # API Key input
            api_key = st.text_input(
                "Google API Key",
                value=st.session_state.api_key,
                type="password",
                help="Enter your Google API key for Gemini"
            )
            
            if api_key != st.session_state.api_key:
                st.session_state.api_key = api_key
                st.session_state.initialized = False
                st.rerun()
            
            st.divider()
            
            # Upload PDF
            st.header("Upload Book")
            uploaded_file = st.file_uploader("Upload PDF Book", type=["pdf"])
            
            if uploaded_file is not None:
                with st.spinner("Processing PDF..."):
                    # Save uploaded file
                    save_dir = Path("data/uploads")
                    save_dir.mkdir(parents=True, exist_ok=True)
                    file_path = save_dir / uploaded_file.name
                    
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process PDF
                    self._process_uploaded_pdf(file_path, uploaded_file.name)
            
            st.divider()
            
            # Navigation
            st.header("Navigation")
            
            if st.button("📚 Book List"):
                st.session_state.current_book = None
                st.session_state.current_chapter = None
                st.rerun()
            
            if st.session_state.current_book is not None:
                if st.button("📖 Chapter List"):
                    st.session_state.current_chapter = None
                    st.rerun()
    
    def _process_uploaded_pdf(self, file_path: Path, file_name: str):
        """
        Process an uploaded PDF file.
        
        Args:
            file_path: Path to the saved PDF file.
            file_name: Name of the uploaded file.
        """
        try:
            # Extract book title from filename
            book_title = file_name.replace(".pdf", "")
            
            # Create book in database
            book = st.session_state.db_manager.create_book(book_title, str(file_path))
            
            # Extract text from PDF
            extractor = PDFExtractor(str(file_path))
            extractor.extract_text()
            chapters = extractor.detect_chapters()
            
            # Save chapters to database
            for chapter_name, chapter_text in chapters.items():
                # Extract chapter number
                chapter_num = 1
                if "Chapter" in chapter_name:
                    try:
                        chapter_num = int(chapter_name.replace("Chapter", "").strip())
                    except ValueError:
                        pass
                
                # Create chapter in database
                st.session_state.db_manager.create_chapter(
                    book.id,
                    chapter_num,
                    chapter_name,
                    chapter_text
                )
            
            st.sidebar.success(f"Successfully processed '{book_title}' with {len(chapters)} chapters")
            
            # Set as current book
            st.session_state.current_book = book.id
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            st.sidebar.error(f"Error processing PDF: {str(e)}")
    
    def _render_book_list(self):
        """Render the book list page."""
        st.header("📚 Your Books")
        
        # Get all books
        books = st.session_state.db_manager.get_all_books()
        
        if not books:
            st.info("No books found. Upload a PDF book using the sidebar.")
            return
        
        # Display books in a grid
        cols = st.columns(3)
        for i, book in enumerate(books):
            with cols[i % 3]:
                st.subheader(book.title)
                
                # Get progress
                progress = st.session_state.interactive_learning.get_book_progress(book.id)
                
                # Display progress
                st.progress(progress["overall_progress"] / 100)
                st.write(f"Progress: {progress['overall_progress']:.1f}%")
                st.write(f"Chapters: {progress['completed_chapters']}/{progress['total_chapters']}")
                
                if st.button("Open Book", key=f"open_book_{book.id}"):
                    st.session_state.current_book = book.id
                    st.rerun()
    
    def _render_chapter_list(self):
        """Render the chapter list page."""
        # Get book
        book = st.session_state.db_manager.get_book(st.session_state.current_book)
        if not book:
            st.error("Book not found")
            st.session_state.current_book = None
            st.rerun()
            return
        
        st.header(f"📖 {book.title}")
        
        # Get chapters
        chapters = st.session_state.db_manager.get_chapters_by_book(book.id)
        
        if not chapters:
            st.info("No chapters found in this book.")
            return
        
        # Get progress
        progress = st.session_state.interactive_learning.get_book_progress(book.id)
        chapter_progress = {cp["chapter_id"]: cp for cp in progress["chapter_progress"]}
        
        # Display chapters
        for chapter in chapters:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                chapter_prog = chapter_progress.get(chapter.id, {"progress_percentage": 0})
                st.subheader(f"Chapter {chapter.chapter_number}: {chapter.title}")
                st.progress(chapter_prog["progress_percentage"] / 100)
                st.write(f"Progress: {chapter_prog['progress_percentage']:.1f}%")
            
            with col2:
                st.write("")
                st.write("")
                if st.button("Study Chapter", key=f"study_{chapter.id}"):
                    st.session_state.current_chapter = chapter.id
                    st.rerun()
            
            st.divider()
    
    def _render_chapter_content(self):
        """Render the chapter content page."""
        # Get chapter
        chapter = st.session_state.db_manager.get_chapter(st.session_state.current_chapter)
        if not chapter:
            st.error("Chapter not found")
            st.session_state.current_chapter = None
            st.rerun()
            return
        
        # Get book
        book = st.session_state.db_manager.get_book(chapter.book_id)
        
        # Start learning session
        learning_session = st.session_state.interactive_learning.start_learning_session(chapter.id)
        
        # Display chapter info
        st.header(f"📖 {book.title} - Chapter {chapter.chapter_number}: {chapter.title}")
        
        # Create tabs
        summary_tab, concepts_tab, worksheet_tab = st.tabs(["Summary", "Interactive Learning", "Worksheet"])
        
        # Summary tab
        with summary_tab:
            st.markdown(learning_session["summary"])
        
        # Concepts tab
        with concepts_tab:
            st.subheader("Key Concepts")
            
            # Get progress
            progress = st.session_state.interactive_learning.get_chapter_progress(chapter.id)
            st.progress(progress["progress_percentage"] / 100)
            st.write(f"Progress: {progress['progress_percentage']:.1f}% ({progress['understood_concepts']}/{progress['total_concepts']} concepts)")
            
            # Display concepts
            for concept in learning_session["concepts"]:
                with st.expander(f"📌 {concept['name']}", expanded=not concept["is_understood"]):
                    st.markdown(f"**Explanation**: {concept['explanation']}")
                    
                    if concept["example"]:
                        st.markdown(f"**Example**: {concept['example']}")
                    
                    if concept["analogy"]:
                        st.markdown(f"**Analogy**: {concept['analogy']}")
                    
                    # Understanding buttons
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if concept["is_understood"]:
                            st.success("✅ Marked as understood")
                        else:
                            if st.button("I understand this", key=f"understand_{concept['id']}"):
                                result = st.session_state.interactive_learning.process_concept_understanding(
                                    concept["id"], True
                                )
                                st.rerun()
                    
                    with col2:
                        if not concept["is_understood"]:
                            if st.button("I need a simpler explanation", key=f"simpler_{concept['id']}"):
                                result = st.session_state.interactive_learning.process_concept_understanding(
                                    concept["id"], False
                                )
                                
                                # Display simpler explanation
                                if "simpler_explanation" in result:
                                    st.markdown("### Simpler Explanation")
                                    st.markdown(result["simpler_explanation"])
        
        # Worksheet tab
        with worksheet_tab:
            st.subheader("Practice Worksheet")
            
            # Check if worksheet exists
            worksheet = st.session_state.db_manager.get_worksheet(chapter.id)
            
            if worksheet and worksheet.file_path and os.path.exists(worksheet.file_path):
                # Display download buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    with open(worksheet.file_path, "rb") as f:
                        st.download_button(
                            "Download Worksheet",
                            f,
                            file_name=f"{chapter.title}_worksheet.pdf",
                            mime="application/pdf"
                        )
                
                # Get answer key path
                answer_key_path = worksheet.file_path.replace("_worksheet.pdf", "_answer_key.pdf")
                
                with col2:
                    if os.path.exists(answer_key_path):
                        with open(answer_key_path, "rb") as f:
                            st.download_button(
                                "Download Answer Key",
                                f,
                                file_name=f"{chapter.title}_answer_key.pdf",
                                mime="application/pdf"
                            )
            else:
                # Generate worksheet button
                if st.button("Generate Worksheet"):
                    with st.spinner("Generating worksheet..."):
                        try:
                            # Get summary
                            summary = st.session_state.db_manager.get_summary(chapter.id)
                            
                            # Get concepts
                            concepts = st.session_state.db_manager.get_concepts_by_chapter(chapter.id)
                            concepts_data = [
                                {
                                    "name": concept.name,
                                    "explanation": concept.explanation,
                                    "example": concept.example,
                                    "analogy": concept.analogy
                                }
                                for concept in concepts
                            ]
                            
                            # Create output directory
                            output_dir = Path(f"output/worksheets/{book.id}/{chapter.id}")
                            output_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Generate worksheet
                            worksheet_path, answer_key_path = st.session_state.worksheet_generator.generate_worksheet(
                                summary.content,
                                concepts_data,
                                str(output_dir),
                                chapter.title
                            )
                            
                            # Save worksheet to database
                            st.session_state.db_manager.create_worksheet(
                                chapter.id,
                                file_path=worksheet_path
                            )
                            
                            st.success("Worksheet generated successfully!")
                            st.rerun()
                            
                        except Exception as e:
                            logger.error(f"Error generating worksheet: {str(e)}")
                            st.error(f"Error generating worksheet: {str(e)}")


if __name__ == "__main__":
    app = EduSummarizeApp()
    app.run()
