"""
Interactive Learning Module for EduSummarizeAI.

This module handles the interactive concept understanding and learning process.
"""

import os
import json
from typing import Dict#, List, Tuple, Optional
import logging
from core.summarizer import ChapterSummarizer
from db.database import DatabaseManager#, Concept

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InteractiveLearning:
    """Class to handle interactive learning sessions."""
    
    def __init__(self, db_manager: DatabaseManager, summarizer: ChapterSummarizer):
        """
        Initialize the InteractiveLearning.
        
        Args:
            db_manager: Database manager instance.
            summarizer: ChapterSummarizer instance for generating explanations.
        """
        self.db_manager = db_manager
        self.summarizer = summarizer
        logger.info("Initialized InteractiveLearning module")
    
    def start_learning_session(self, chapter_id: int) -> Dict:
        """
        Start a learning session for a chapter.
        
        Args:
            chapter_id: ID of the chapter.
            
        Returns:
            Dictionary with chapter info and concepts.
        """
        logger.info(f"Starting learning session for chapter ID: {chapter_id}")
        
        # Get chapter from database
        chapter = self.db_manager.get_chapter(chapter_id)
        if not chapter:
            logger.error(f"Chapter not found: {chapter_id}")
            raise ValueError(f"Chapter not found: {chapter_id}")
        
        # Get chapter summary
        summary = self.db_manager.get_summary(chapter_id)
        if not summary:
            logger.info(f"No summary found for chapter {chapter_id}, generating new summary")
            
            # Generate summary
            summary_text = self.summarizer.summarize_chapter(chapter.content)
            summary = self.db_manager.create_summary(chapter_id, summary_text)
            
            # Extract concepts
            concepts_data = self.summarizer.extract_concepts(summary_text)
            
            # Create concepts in database
            for concept_data in concepts_data:
                self.db_manager.create_concept(
                    chapter_id=chapter_id,
                    name=concept_data["name"],
                    explanation=concept_data["explanation"],
                    example=concept_data.get("example", ""),
                    analogy=concept_data.get("analogy", "")
                )
        
        # Get all concepts for the chapter
        concepts = self.db_manager.get_concepts_by_chapter(chapter_id)
        
        # Update user progress
        self.db_manager.update_user_progress(chapter.book_id, chapter_id)
        
        # Prepare response
        return {
            "chapter": {
                "id": chapter.id,
                "title": chapter.title,
                "number": chapter.chapter_number
            },
            "summary": summary.content,
            "concepts": [
                {
                    "id": concept.id,
                    "name": concept.name,
                    "explanation": concept.explanation,
                    "example": concept.example,
                    "analogy": concept.analogy,
                    "is_understood": concept.is_understood
                }
                for concept in concepts
            ]
        }
    
    def process_concept_understanding(self, concept_id: int, understood: bool) -> Dict:
        """
        Process user's understanding of a concept.
        
        Args:
            concept_id: ID of the concept.
            understood: Whether the user understood the concept.
            
        Returns:
            Updated concept with simpler explanation if not understood.
        """
        logger.info(f"Processing concept understanding for concept ID: {concept_id}, understood: {understood}")
        
        # Get concept from database
        concept = self.db_manager.get_concept(concept_id)
        if not concept:
            logger.error(f"Concept not found: {concept_id}")
            raise ValueError(f"Concept not found: {concept_id}")
        
        # If understood, mark as understood
        if understood:
            self.db_manager.mark_concept_understood(concept_id, True)
            return {
                "id": concept.id,
                "name": concept.name,
                "is_understood": True
            }
        
        # If not understood, generate simpler explanation
        concept_data = {
            "id": concept.id,
            "name": concept.name,
            "explanation": concept.explanation,
            "example": concept.example,
            "analogy": concept.analogy
        }
        
        simpler_concept = self.summarizer.explain_concept_simpler(concept_data)
        
        return {
            "id": concept.id,
            "name": concept.name,
            "is_understood": False,
            "simpler_explanation": simpler_concept.get("simpler_explanation", "")
        }
    
    def get_chapter_progress(self, chapter_id: int) -> Dict:
        """
        Get progress statistics for a chapter.
        
        Args:
            chapter_id: ID of the chapter.
            
        Returns:
            Dictionary with progress statistics.
        """
        logger.info(f"Getting progress for chapter ID: {chapter_id}")
        
        # Get all concepts for the chapter
        concepts = self.db_manager.get_concepts_by_chapter(chapter_id)
        
        # Calculate progress
        total_concepts = len(concepts)
        understood_concepts = sum(1 for concept in concepts if concept.is_understood)
        progress_percentage = (understood_concepts / total_concepts * 100) if total_concepts > 0 else 0
        
        return {
            "total_concepts": total_concepts,
            "understood_concepts": understood_concepts,
            "progress_percentage": progress_percentage,
            "concepts": [
                {
                    "id": concept.id,
                    "name": concept.name,
                    "is_understood": concept.is_understood
                }
                for concept in concepts
            ]
        }
    
    def get_book_progress(self, book_id: int) -> Dict:
        """
        Get progress statistics for a book.
        
        Args:
            book_id: ID of the book.
            
        Returns:
            Dictionary with progress statistics.
        """
        logger.info(f"Getting progress for book ID: {book_id}")
        
        # Get all chapters for the book
        chapters = self.db_manager.get_chapters_by_book(book_id)
        
        # Get user progress
        user_progress = self.db_manager.get_user_progress(book_id)
        completed_chapters = []
        if user_progress and user_progress.completed_chapters:
            try:
                completed_chapters = json.loads(user_progress.completed_chapters)
            except json.JSONDecodeError:
                completed_chapters = []
        
        # Calculate chapter progress
        chapter_progress = []
        total_concepts = 0
        total_understood = 0
        
        for chapter in chapters:
            # Get progress for chapter
            chapter_stats = self.get_chapter_progress(chapter.id)
            
            # Update totals
            total_concepts += chapter_stats["total_concepts"]
            total_understood += chapter_stats["understood_concepts"]
            
            # Add to chapter progress
            chapter_progress.append({
                "chapter_id": chapter.id,
                "chapter_title": chapter.title,
                "chapter_number": chapter.chapter_number,
                "progress_percentage": chapter_stats["progress_percentage"],
                "is_completed": chapter.id in completed_chapters
            })
        
        # Calculate overall progress
        overall_percentage = (total_understood / total_concepts * 100) if total_concepts > 0 else 0
        
        return {
            "book_id": book_id,
            "overall_progress": overall_percentage,
            "total_chapters": len(chapters),
            "completed_chapters": len(completed_chapters),
            "chapter_progress": chapter_progress
        }
    
    def reset_chapter_progress(self, chapter_id: int) -> Dict:
        """
        Reset progress for a chapter.
        
        Args:
            chapter_id: ID of the chapter.
            
        Returns:
            Success message.
        """
        logger.info(f"Resetting progress for chapter ID: {chapter_id}")
        
        # Get all concepts for the chapter
        concepts = self.db_manager.get_concepts_by_chapter(chapter_id)
        
        # Reset understanding for all concepts
        for concept in concepts:
            self.db_manager.mark_concept_understood(concept.id, False)
        
        # Get chapter
        chapter = self.db_manager.get_chapter(chapter_id)
        if chapter:
            # Update user progress to remove this chapter from completed
            user_progress = self.db_manager.get_user_progress(chapter.book_id)
            if user_progress and user_progress.completed_chapters:
                try:
                    completed_chapters = json.loads(user_progress.completed_chapters)
                    if chapter_id in completed_chapters:
                        completed_chapters.remove(chapter_id)
                        user_progress.completed_chapters = json.dumps(completed_chapters)
                        self.db_manager.update_user_progress(chapter.book_id)
                except json.JSONDecodeError:
                    pass
        
        return {"message": f"Progress reset for chapter ID: {chapter_id}"}


# Example usage
if __name__ == "__main__":
    # For testing purposes
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python interactive_learning.py <chapter_id> [api_key]")
        sys.exit(1)
        
    # Get API key from environment variable or command line
    api_key = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        print("Error: Google API key is required. Set GOOGLE_API_KEY environment variable or pass as argument.")
        sys.exit(1)
        
    # Initialize components
    db_manager = DatabaseManager()
    summarizer = ChapterSummarizer(api_key)
    
    # Initialize interactive learning
    learning = InteractiveLearning(db_manager, summarizer)
    
    # Start learning session
    chapter_id = int(sys.argv[1])
    session = learning.start_learning_session(chapter_id)
    
    print("\n--- LEARNING SESSION ---\n")
    print(f"Chapter: {session['chapter']['title']}")
    print(f"Concepts: {len(session['concepts'])}")
    
    # Simulate interactive learning
    for concept in session['concepts']:
        print(f"\nConcept: {concept['name']}")
        print(f"Explanation: {concept['explanation'][:100]}...")
        understood = input("Do you understand this concept? (y/n): ").lower() == 'y'
        
        result = learning.process_concept_understanding(concept['id'], understood)
        
        if not understood:
            print("\nSimpler explanation:")
            print(result['simpler_explanation'])
    
    # Get progress
    progress = learning.get_chapter_progress(chapter_id)
    print(f"\nYour progress: {progress['progress_percentage']:.1f}% ({progress['understood_concepts']}/{progress['total_concepts']} concepts)")