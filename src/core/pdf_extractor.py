"""
PDF Extraction Module for EduSummarizeAI.

This module handles the extraction of text from PDF books and segmentation into chapters.
"""

import os
import re
import json
import pdfplumber
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFExtractor:
    """Class to handle PDF text extraction and chapter segmentation."""
    
    def __init__(self, pdf_path: str):
        """
        Initialize the PDFExtractor.
        
        Args:
            pdf_path: Path to the PDF file.
        """
        self.pdf_path = pdf_path
        self.raw_text = ""
        self.pages_text = []
        self.chapters = {}
        
    def extract_text(self) -> List[str]:
        """
        Extract text from the PDF file.
        
        Returns:
            List of page texts.
        """
        logger.info(f"Extracting text from {self.pdf_path}")
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.pages_text = [page.extract_text() or "" for page in pdf.pages]
                self.raw_text = "\n".join(self.pages_text)
                
            logger.info(f"Successfully extracted {len(self.pages_text)} pages")
            return self.pages_text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def detect_chapters(self, 
                       chapter_pattern: str = r'(?:Chapter|CHAPTER)\s+(\d+|[IVXLCDM]+)',
                       custom_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> Dict[str, str]:
        """
        Detect and extract chapters from the PDF.
        
        Args:
            chapter_pattern: Regex pattern to identify chapter headings.
            custom_ranges: Optional dictionary mapping chapter names to page ranges.
                           Format: {"Chapter 1": (0, 10), "Chapter 2": (11, 20), ...}
        
        Returns:
            Dictionary mapping chapter names to their text content.
        """
        if not self.pages_text:
            self.extract_text()
            
        if custom_ranges:
            logger.info("Using custom chapter ranges provided by user")
            return self._extract_chapters_by_ranges(custom_ranges)
        
        logger.info(f"Detecting chapters using pattern: {chapter_pattern}")
        
        # Join all pages with page numbers for reference
        full_text = "\n".join([f"[PAGE_{i}]\n{text}" for i, text in enumerate(self.pages_text)])
        
        # Find all chapter headings
        chapter_matches = list(re.finditer(chapter_pattern, full_text))
        
        if not chapter_matches:
            logger.warning("No chapters detected using the pattern. Treating entire document as a single chapter.")
            self.chapters = {"Chapter 1": self.raw_text}
            return self.chapters
        
        # Extract chapter texts
        for i, match in enumerate(chapter_matches):
            chapter_num = match.group(1)
            chapter_name = f"Chapter {chapter_num}"
            start_pos = match.start()
            
            # End position is either the start of the next chapter or the end of the document
            end_pos = chapter_matches[i + 1].start() if i < len(chapter_matches) - 1 else len(full_text)
            
            chapter_text = full_text[start_pos:end_pos]
            self.chapters[chapter_name] = chapter_text.replace('[PAGE_', '\nPage ').replace(']\n', ':\n')
        
        logger.info(f"Successfully extracted {len(self.chapters)} chapters")
        return self.chapters
    
    def _extract_chapters_by_ranges(self, chapter_ranges: Dict[str, Tuple[int, int]]) -> Dict[str, str]:
        """
        Extract chapters based on user-provided page ranges.
        
        Args:
            chapter_ranges: Dictionary mapping chapter names to page ranges (start, end).
        
        Returns:
            Dictionary mapping chapter names to their text content.
        """
        for chapter_name, (start_page, end_page) in chapter_ranges.items():
            if start_page < 0 or end_page >= len(self.pages_text) or start_page > end_page:
                logger.warning(f"Invalid page range for {chapter_name}: ({start_page}, {end_page})")
                continue
                
            chapter_text = "\n".join(self.pages_text[start_page:end_page + 1])
            self.chapters[chapter_name] = chapter_text
            
        return self.chapters
    
    def save_chapters(self, output_dir: str) -> str:
        """
        Save the extracted chapters to JSON and individual text files.
        
        Args:
            output_dir: Directory to save the output files.
        
        Returns:
            Path to the JSON file containing all chapters.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Save as JSON
        book_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        json_path = os.path.join(output_dir, f"{book_name}_chapters.json")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.chapters, f, indent=2)
            
        # Save individual chapter files
        chapters_dir = os.path.join(output_dir, book_name)
        if not os.path.exists(chapters_dir):
            os.makedirs(chapters_dir)
            
        for chapter_name, chapter_text in self.chapters.items():
            safe_name = re.sub(r'[^\w\s-]', '', chapter_name).strip().replace(' ', '_')
            chapter_path = os.path.join(chapters_dir, f"{safe_name}.txt")
            
            with open(chapter_path, 'w', encoding='utf-8') as f:
                f.write(chapter_text)
        
        logger.info(f"Saved chapters to {json_path} and individual files in {chapters_dir}")
        return json_path

# Example usage
if __name__ == "__main__":
    # For testing purposes
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <path_to_pdf>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    extractor = PDFExtractor(pdf_path)
    extractor.extract_text()
    chapters = extractor.detect_chapters()
    
    print(f"Detected {len(chapters)} chapters:")
    for chapter_name in chapters.keys():
        print(f"- {chapter_name}")
    
    # Example of manual chapter definition
    # custom_ranges = {
    #     "Chapter 1": (0, 10),  # Pages 1-11
    #     "Chapter 2": (11, 20), # Pages 12-21
    # }
    # chapters = extractor.detect_chapters(custom_ranges=custom_ranges)
    
    output_path = extractor.save_chapters("./output")
    print(f"Chapters saved to {output_path}")