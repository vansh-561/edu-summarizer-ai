"""
Worksheet Generator Module for EduSummarizeAI.

This module handles the generation of practice worksheets for chapters.
"""

import os
import re
import json
from typing import Dict, List, Tuple#, Optional
import logging
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER#,TA_LEFT 
from reportlab.lib.units import inch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WorksheetGenerator:
    """Class to handle worksheet generation using Gemini API."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-pro-preview-03-25"):
        """
        Initialize the WorksheetGenerator.
        
        Args:
            api_key: Google API key for Gemini.
            model_name: Gemini model to use.
        """
        self.api_key = api_key
        self.model_name = model_name
        
        # Configure Google Generative AI
        genai.configure(api_key=self.api_key)
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.3,
            max_output_tokens=8192  # Maximum for generating a full worksheet
        )
        
        logger.info(f"Initialized WorksheetGenerator with model: {model_name}")
    
    def _create_worksheet_prompt(self) -> PromptTemplate:
        """
        Create a prompt template for worksheet generation.
        
        Returns:
            PromptTemplate for worksheet generation.
        """
        worksheet_template = """
        You are an educational AI assistant tasked with creating a practice worksheet for students.
        
        Based on the following chapter summary and concepts, generate a comprehensive worksheet with:
        
        1. 20 Multiple-Choice Questions (MCQs) with 4 options each. Include the correct answer.
        2. 10 One-Word or One-Liner Questions. Include answers.
        3. 10 Brief Question-Answers (50-100 words each).
        4. 10 Match-the-Column Questions (two columns, 10 pairs). Include the correct matches.
        
        Ensure questions cover all key concepts and vary in difficulty (easy, medium, and hard).
        Format the output in a clear, structured JSON format like this:
        
        ```
        {
            "mcqs": [
                {
                    "question": "Question text?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer": "Option A",
                    "difficulty": "easy"
                },
                ...
            ],
            "one_liners": [
                {
                    "question": "Question text?",
                    "answer": "Answer text",
                    "difficulty": "medium"
                },
                ...
            ],
            "brief_qa": [
                {
                    "question": "Question text?",
                    "answer": "Detailed answer (50-100 words)",
                    "difficulty": "hard"
                },
                ...
            ],
            "match_columns": {
                "column1": ["Item 1", "Item 2", ...],
                "column2": ["Match 1", "Match 2", ...],
                "matches": {
                    "Item 1": "Match 1",
                    "Item 2": "Match 2",
                    ...
                }
            }
        }
        ```
        
        Chapter Summary and Concepts:
        {chapter_content}
        
        Output only the JSON. Do not include any other text, explanation or markdown formatting.
        """
        
        return PromptTemplate(
            input_variables=["chapter_content"],
            template=worksheet_template
        )
    
    def generate_worksheet_content(self, chapter_summary: str, concepts: List[Dict]) -> Dict:
        """
        Generate worksheet content using Gemini.
        
        Args:
            chapter_summary: Summary of the chapter.
            concepts: List of concepts extracted from the chapter.
            
        Returns:
            Dictionary containing worksheet content.
        """
        logger.info("Generating worksheet content")
        
        # Combine summary and concepts into a single text
        concepts_text = "\n\n".join([
            f"Concept: {concept['name']}\n"
            f"Explanation: {concept['explanation']}\n"
            f"Example: {concept.get('example', '')}\n"
            f"Analogy: {concept.get('analogy', '')}"
            for concept in concepts
        ])
        
        chapter_content = f"{chapter_summary}\n\nKEY CONCEPTS:\n{concepts_text}"
        
        try:
            # Create the prompt
            worksheet_prompt = self._create_worksheet_prompt()
            
            # Create and run the chain
            worksheet_chain = LLMChain(llm=self.llm, prompt=worksheet_prompt)
            worksheet_json_str = worksheet_chain.run(chapter_content=chapter_content)
            
            # Extract the JSON part from the response
            json_match = re.search(r'``````', worksheet_json_str, re.DOTALL)
            if json_match:
                worksheet_json_str = json_match.group(1)
            else:
                # Try to find any JSON object
                json_match = re.search(r'\{\s*"mcqs".*\}', worksheet_json_str, re.DOTALL)
                if json_match:
                    worksheet_json_str = json_match.group(0)
                    
            # Parse the JSON
            worksheet_content = json.loads(worksheet_json_str)
            
            logger.info("Successfully generated worksheet content")
            return worksheet_content
            
        except Exception as e:
            logger.error(f"Error generating worksheet content: {str(e)}")
            # Return a basic structure in case of error
            return {
                "mcqs": [],
                "one_liners": [],
                "brief_qa": [],
                "match_columns": {"column1": [], "column2": [], "matches": {}}
            }
    
    def generate_pdf_worksheet(self, worksheet_content: Dict, output_path: str, chapter_title: str) -> str:
        """
        Generate a PDF worksheet from the content.
        
        Args:
            worksheet_content: Dictionary containing worksheet content.
            output_path: Path to save the PDF.
            chapter_title: Title of the chapter.
            
        Returns:
            Path to the generated PDF.
        """
        logger.info(f"Generating PDF worksheet for: {chapter_title}")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create the PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            
            section_style = ParagraphStyle(
                'SectionStyle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=12,
                spaceAfter=8
            )
            
            question_style = ParagraphStyle(
                'QuestionStyle',
                parent=styles['Normal'],
                fontSize=11,
                spaceBefore=6,
                leftIndent=20
            )
            
            # Create the content
            content = []
            
            # Title
            content.append(Paragraph(f"Practice Worksheet: {chapter_title}", title_style))
            content.append(Spacer(1, 0.25*inch))
            
            # Multiple Choice Questions
            content.append(Paragraph("Section 1: Multiple Choice Questions", section_style))
            for i, mcq in enumerate(worksheet_content.get("mcqs", [])):
                question_text = f"{i+1}. {mcq['question']}"
                content.append(Paragraph(question_text, question_style))
                
                # Options
                options = mcq.get("options", [])
                for j, option in enumerate(options):
                    option_text = f"    {chr(65+j)}) {option}"
                    content.append(Paragraph(option_text, styles['Normal']))
                
                content.append(Spacer(1, 0.1*inch))
            
            # One-Liner Questions
            content.append(Paragraph("Section 2: One-Word or One-Liner Questions", section_style))
            for i, one_liner in enumerate(worksheet_content.get("one_liners", [])):
                question_text = f"{i+1}. {one_liner['question']}"
                content.append(Paragraph(question_text, question_style))
                content.append(Spacer(1, 0.1*inch))
            
            # Brief Q&A
            content.append(Paragraph("Section 3: Brief Questions and Answers", section_style))
            for i, qa in enumerate(worksheet_content.get("brief_qa", [])):
                question_text = f"{i+1}. {qa['question']}"
                content.append(Paragraph(question_text, question_style))
                content.append(Spacer(1, 0.2*inch))
            
            # Match Columns
            content.append(Paragraph("Section 4: Match the Columns", section_style))
            
            match_columns = worksheet_content.get("match_columns", {})
            col1 = match_columns.get("column1", [])
            col2 = match_columns.get("column2", [])
            
            if col1 and col2:
                # Create a table for match columns
                table_data = [["Column A", "Column B"]]
                for i in range(min(len(col1), len(col2))):
                    table_data.append([f"{i+1}. {col1[i]}", f"{chr(65+i)}. {col2[i]}"])
                
                table = Table(table_data, colWidths=[2.5*inch, 2.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                    ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                content.append(table)
            
            # Build the PDF
            doc.build(content)
            
            logger.info(f"Successfully generated PDF worksheet at: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating PDF worksheet: {str(e)}")
            raise
    
    def generate_answer_key(self, worksheet_content: Dict, output_path: str, chapter_title: str) -> str:
        """
        Generate an answer key PDF for the worksheet.
        
        Args:
            worksheet_content: Dictionary containing worksheet content.
            output_path: Path to save the answer key PDF.
            chapter_title: Title of the chapter.
            
        Returns:
            Path to the generated answer key PDF.
        """
        logger.info(f"Generating answer key for: {chapter_title}")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create the PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=12
            )
            
            section_style = ParagraphStyle(
                'SectionStyle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=12,
                spaceAfter=8
            )
            
            answer_style = ParagraphStyle(
                'AnswerStyle',
                parent=styles['Normal'],
                fontSize=11,
                spaceBefore=2,
                leftIndent=20
            )
            
            # Create the content
            content = []
            
            # Title
            content.append(Paragraph(f"Answer Key: {chapter_title}", title_style))
            content.append(Spacer(1, 0.25*inch))
            
            # Multiple Choice Questions
            content.append(Paragraph("Section 1: Multiple Choice Questions", section_style))
            for i, mcq in enumerate(worksheet_content.get("mcqs", [])):
                answer_text = f"{i+1}. {mcq['question']} - Answer: {mcq['answer']}"
                content.append(Paragraph(answer_text, answer_style))
            
            content.append(Spacer(1, 0.2*inch))
            
            # One-Liner Questions
            content.append(Paragraph("Section 2: One-Word or One-Liner Questions", section_style))
            for i, one_liner in enumerate(worksheet_content.get("one_liners", [])):
                answer_text = f"{i+1}. {one_liner['question']} - Answer: {one_liner['answer']}"
                content.append(Paragraph(answer_text, answer_style))
            
            content.append(Spacer(1, 0.2*inch))
            
            # Brief Q&A
            content.append(Paragraph("Section 3: Brief Questions and Answers", section_style))
            for i, qa in enumerate(worksheet_content.get("brief_qa", [])):
                question_text = f"{i+1}. {qa['question']}"
                answer_text = f"Answer: {qa['answer']}"
                content.append(Paragraph(question_text, answer_style))
                content.append(Paragraph(answer_text, styles['Normal']))
                content.append(Spacer(1, 0.1*inch))
            
            # Match Columns
            content.append(Paragraph("Section 4: Match the Columns", section_style))
            
            match_columns = worksheet_content.get("match_columns", {})
            matches = match_columns.get("matches", {})
            
            if matches:
                for i, (item, match) in enumerate(matches.items()):
                    match_text = f"{i+1}. {item} → {match}"
                    content.append(Paragraph(match_text, answer_style))
            
            # Build the PDF
            doc.build(content)
            
            logger.info(f"Successfully generated answer key at: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating answer key: {str(e)}")
            raise
    
    def generate_worksheet(self, chapter_summary: str, concepts: List[Dict], 
                          output_dir: str, chapter_title: str) -> Tuple[str, str]:
        """
        Generate a complete worksheet with answer key.
        
        Args:
            chapter_summary: Summary of the chapter.
            concepts: List of concepts extracted from the chapter.
            output_dir: Directory to save the worksheet files.
            chapter_title: Title of the chapter.
            
        Returns:
            Tuple of (worksheet_path, answer_key_path).
        """
        logger.info(f"Generating complete worksheet for: {chapter_title}")
        
        # Generate worksheet content
        worksheet_content = self.generate_worksheet_content(chapter_summary, concepts)
        
        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', chapter_title).strip().replace(' ', '_')
        
        # Generate PDF worksheet
        worksheet_path = os.path.join(output_dir, f"{safe_title}_worksheet.pdf")
        self.generate_pdf_worksheet(worksheet_content, worksheet_path, chapter_title)
        
        # Generate answer key
        answer_key_path = os.path.join(output_dir, f"{safe_title}_answer_key.pdf")
        self.generate_answer_key(worksheet_content, answer_key_path, chapter_title)
        
        return worksheet_path, answer_key_path


# Example usage
if __name__ == "__main__":
    # For testing purposes
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python worksheet_generator.py <path_to_summary_file> [api_key]")
        sys.exit(1)
        
    # Get API key from environment variable or command line
    api_key = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        print("Error: Google API key is required. Set GOOGLE_API_KEY environment variable or pass as argument.")
        sys.exit(1)
        
    # Read summary text
    summary_path = sys.argv[1]
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_text = f.read()
    
    # Mock concepts for testing
    mock_concepts = [
        {
            "name": "Example Concept 1",
            "explanation": "This is an explanation of concept 1",
            "example": "This is an example of concept 1",
            "analogy": "This is an analogy for concept 1"
        },
        {
            "name": "Example Concept 2",
            "explanation": "This is an explanation of concept 2",
            "example": "This is an example of concept 2",
            "analogy": "This is an analogy for concept 2"
        }
    ]
    
    # Generate worksheet
    generator = WorksheetGenerator(api_key)
    worksheet_path, answer_key_path = generator.generate_worksheet(
        summary_text, 
        mock_concepts, 
        "./output", 
        "Sample Chapter"
    )
    
    print(f"Worksheet generated at: {worksheet_path}")
    print(f"Answer key generated at: {answer_key_path}")
