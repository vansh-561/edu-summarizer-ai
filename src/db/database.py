"""
Database Module for EduSummarizeAI.

This module handles database operations for storing book data, chapters, summaries, 
and user progress.
"""

import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()


class Book(Base):
    """Model for books table."""
    
    __tablename__ = 'books'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}')>"


class Chapter(Base):
    """Model for chapters table."""
    
    __tablename__ = 'chapters'
    
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    book = relationship("Book", back_populates="chapters")
    summary = relationship("Summary", back_populates="chapter", uselist=False, cascade="all, delete-orphan")
    concepts = relationship("Concept", back_populates="chapter", cascade="all, delete-orphan")
    worksheet = relationship("Worksheet", back_populates="chapter", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Chapter(id={self.id}, title='{self.title}')>"


class Summary(Base):
    """Model for chapter summaries."""
    
    __tablename__ = 'summaries'
    
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="summary")
    
    def __repr__(self):
        return f"<Summary(id={self.id}, chapter_id={self.chapter_id})>"


class Concept(Base):
    """Model for concepts extracted from chapters."""
    
    __tablename__ = 'concepts'
    
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'), nullable=False)
    name = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    example = Column(Text, nullable=True)
    analogy = Column(Text, nullable=True)
    is_understood = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="concepts")
    
    def __repr__(self):
        return f"<Concept(id={self.id}, name='{self.name}')>"


class Worksheet(Base):
    """Model for worksheets generated for chapters."""
    
    __tablename__ = 'worksheets'
    
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapters.id'), nullable=False)
    mcqs = Column(Text, nullable=True)  # JSON string storing MCQs
    one_liners = Column(Text, nullable=True)  # JSON string storing one-liner questions
    brief_qa = Column(Text, nullable=True)  # JSON string storing brief Q&A
    match_columns = Column(Text, nullable=True)  # JSON string storing match columns
    file_path = Column(String(512), nullable=True)  # Path to generated worksheet file
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="worksheet")
    
    def __repr__(self):
        return f"<Worksheet(id={self.id}, chapter_id={self.chapter_id})>"


class UserProgress(Base):
    """Model for tracking user progress."""
    
    __tablename__ = 'user_progress'
    
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    last_chapter_id = Column(Integer, ForeignKey('chapters.id'), nullable=True)
    completed_chapters = Column(Text, default="[]")  # JSON string of completed chapter IDs
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<UserProgress(id={self.id}, book_id={self.book_id})>"


class DatabaseManager:
    """Class to manage database operations."""
    
    def __init__(self, db_path=None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to 'edusummarizeai.db'
                    in the current directory.
        """
        if db_path is None:
            db_path = os.path.join(os.getcwd(), 'edusummarizeai.db')
            
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine,expire_on_commit=False)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at {db_path}")
    
    def create_book(self, title, file_path):
        """
        Create a new book entry.
        
        Args:
            title: Title of the book.
            file_path: Path to the PDF file.
            
        Returns:
            Book object.
        """
        session = self.Session()
        try:
            book = Book(title=title, file_path=file_path)
            session.add(book)
            session.commit()
            logger.info(f"Created book: {title}")
            return book
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating book: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_book(self, book_id):
        """
        Get a book by ID.
        
        Args:
            book_id: ID of the book.
            
        Returns:
            Book object or None if not found.
        """
        session = self.Session()
        try:
            book = session.query(Book).filter(Book.id == book_id).first()
            return book
        finally:
            session.close()
            
    def get_all_books(self):
        """
        Get all books.
        
        Returns:
            List of Book objects.
        """
        session = self.Session()
        try:
            books = session.query(Book).all()
            return books
        finally:
            session.close()
            
    def create_chapter(self, book_id, chapter_number, title, content):
        """
        Create a new chapter entry.
        
        Args:
            book_id: ID of the book the chapter belongs to.
            chapter_number: Chapter number.
            title: Title of the chapter.
            content: Text content of the chapter.
            
        Returns:
            Chapter object.
        """
        session = self.Session()
        try:
            chapter = Chapter(
                book_id=book_id,
                chapter_number=chapter_number,
                title=title,
                content=content
            )
            session.add(chapter)
            session.commit()
            logger.info(f"Created chapter: {title}")
            return chapter
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating chapter: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_chapter(self, chapter_id):
        """
        Get a chapter by ID.
        
        Args:
            chapter_id: ID of the chapter.
            
        Returns:
            Chapter object or None if not found.
        """
        session = self.Session()
        try:
            chapter = session.query(Chapter).filter(Chapter.id == chapter_id).first()
            return chapter
        finally:
            session.close()
            
    def get_chapters_by_book(self, book_id):
        """
        Get all chapters for a book.
        
        Args:
            book_id: ID of the book.
            
        Returns:
            List of Chapter objects.
        """
        session = self.Session()
        try:
            chapters = session.query(Chapter).filter(Chapter.book_id == book_id).order_by(Chapter.chapter_number).all()
            return chapters
        finally:
            session.close()
            
    def create_summary(self, chapter_id, content):
        """
        Create a summary for a chapter.
        
        Args:
            chapter_id: ID of the chapter.
            content: Summary content.
            
        Returns:
            Summary object.
        """
        session = self.Session()
        try:
            summary = Summary(chapter_id=chapter_id, content=content)
            session.add(summary)
            session.commit()
            logger.info(f"Created summary for chapter ID: {chapter_id}")
            return summary
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating summary: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_summary(self, chapter_id):
        """
        Get summary for a chapter.
        
        Args:
            chapter_id: ID of the chapter.
            
        Returns:
            Summary object or None if not found.
        """
        session = self.Session()
        try:
            summary = session.query(Summary).filter(Summary.chapter_id == chapter_id).first()
            return summary
        finally:
            session.close()
            
    def create_concept(self, chapter_id, name, explanation, example=None, analogy=None):
        """
        Create a concept for a chapter.
        
        Args:
            chapter_id: ID of the chapter.
            name: Name of the concept.
            explanation: Explanation of the concept.
            example: Example of the concept.
            analogy: Analogy for the concept.
            
        Returns:
            Concept object.
        """
        session = self.Session()
        try:
            concept = Concept(
                chapter_id=chapter_id,
                name=name,
                explanation=explanation,
                example=example,
                analogy=analogy
            )
            session.add(concept)
            session.commit()
            logger.info(f"Created concept: {name}")
            return concept
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating concept: {str(e)}")
            raise
        finally:
            session.close()
            
    def mark_concept_understood(self, concept_id, understood=True):
        """
        Mark a concept as understood.
        
        Args:
            concept_id: ID of the concept.
            understood: Whether the concept is understood.
            
        Returns:
            Updated Concept object.
        """
        session = self.Session()
        try:
            concept = session.query(Concept).filter(Concept.id == concept_id).first()
            if concept:
                concept.is_understood = understood
                session.commit()
                logger.info(f"Marked concept {concept_id} as {'understood' if understood else 'not understood'}")
            return concept
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating concept: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_concepts_by_chapter(self, chapter_id):
        """
        Get all concepts for a chapter.
        
        Args:
            chapter_id: ID of the chapter.
            
        Returns:
            List of Concept objects.
        """
        session = self.Session()
        try:
            concepts = session.query(Concept).filter(Concept.chapter_id == chapter_id).all()
            return concepts
        finally:
            session.close()
            
    def create_worksheet(self, chapter_id, mcqs=None, one_liners=None, brief_qa=None, match_columns=None, file_path=None):
        """
        Create a worksheet for a chapter.
        
        Args:
            chapter_id: ID of the chapter.
            mcqs: JSON string of MCQs.
            one_liners: JSON string of one-liner questions.
            brief_qa: JSON string of brief Q&A.
            match_columns: JSON string of match columns.
            file_path: Path to the generated worksheet file.
            
        Returns:
            Worksheet object.
        """
        session = self.Session()
        try:
            # Convert dictionaries to JSON strings if necessary
            if isinstance(mcqs, dict):
                mcqs = json.dumps(mcqs)
            if isinstance(one_liners, dict):
                one_liners = json.dumps(one_liners)
            if isinstance(brief_qa, dict):
                brief_qa = json.dumps(brief_qa)
            if isinstance(match_columns, dict):
                match_columns = json.dumps(match_columns)
                
            worksheet = Worksheet(
                chapter_id=chapter_id,
                mcqs=mcqs,
                one_liners=one_liners,
                brief_qa=brief_qa,
                match_columns=match_columns,
                file_path=file_path
            )
            session.add(worksheet)
            session.commit()
            logger.info(f"Created worksheet for chapter ID: {chapter_id}")
            return worksheet
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating worksheet: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_worksheet(self, chapter_id):
        """
        Get worksheet for a chapter.
        
        Args:
            chapter_id: ID of the chapter.
            
        Returns:
            Worksheet object or None if not found.
        """
        session = self.Session()
        try:
            worksheet = session.query(Worksheet).filter(Worksheet.chapter_id == chapter_id).first()
            return worksheet
        finally:
            session.close()
            
    def update_user_progress(self, book_id, chapter_id=None):
        """
        Update user progress for a book.
        
        Args:
            book_id: ID of the book.
            chapter_id: ID of the last accessed chapter.
            
        Returns:
            UserProgress object.
        """
        session = self.Session()
        try:
            progress = session.query(UserProgress).filter(UserProgress.book_id == book_id).first()
            
            if not progress:
                # Create new progress record
                progress = UserProgress(book_id=book_id, last_chapter_id=chapter_id, completed_chapters="[]")
                session.add(progress)
            else:
                # Update existing progress
                if chapter_id:
                    progress.last_chapter_id = chapter_id
                    
                    # Add to completed chapters if not already there
                    completed = json.loads(progress.completed_chapters)
                    if chapter_id not in completed:
                        completed.append(chapter_id)
                        progress.completed_chapters = json.dumps(completed)
                    
            session.commit()
            logger.info(f"Updated progress for book ID: {book_id}")
            return progress
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating progress: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_user_progress(self, book_id):
        """
        Get user progress for a book.
        
        Args:
            book_id: ID of the book.
            
        Returns:
            UserProgress object or None if not found.
        """
        session = self.Session()
        try:
            progress = session.query(UserProgress).filter(UserProgress.book_id == book_id).first()
            return progress
        finally:
            session.close()


# Example usage
if __name__ == "__main__":
    # For testing purposes
    db_manager = DatabaseManager('test.db')
    
    # Example operations
    book = db_manager.create_book("Sample Book", "/path/to/sample.pdf")
    chapter = db_manager.create_chapter(book.id, 1, "Chapter 1", "Sample chapter content")
    summary = db_manager.create_summary(chapter.id, "This is a summary of Chapter 1")
    concept = db_manager.create_concept(
        chapter.id, 
        "Sample Concept", 
        "This is an explanation of the concept",
        "This is an example",
        "This is an analogy"
    )
    worksheet = db_manager.create_worksheet(
        chapter.id,
        mcqs=json.dumps([{"question": "Sample MCQ?", "options": ["A", "B", "C", "D"], "answer": "A"}]),
        one_liners=json.dumps([{"question": "Sample one-liner?", "answer": "Answer"}]),
        brief_qa=json.dumps([{"question": "Sample Q?", "answer": "Sample A"}]),
        match_columns=json.dumps({"column1": ["A", "B"], "column2": ["1", "2"], "matches": {"A": "1", "B": "2"}})
    )
    progress = db_manager.update_user_progress(book.id, chapter.id)
    
    print(f"Created book: {book}")
    print(f"Created chapter: {chapter}")
    print(f"Created summary: {summary}")
    print(f"Created concept: {concept}")
    print(f"Created worksheet: {worksheet}")
    print(f"Updated progress: {progress}")