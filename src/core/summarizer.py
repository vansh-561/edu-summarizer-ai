"""
Chapter Summarizer Module for EduSummarizeAI.

This module handles the summarization of chapters using Google's Gemini API.
"""

import os
import re
import json
from typing import Dict, List#, Tuple, Optional
import logging
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChapterSummarizer:
    """Class to handle chapter summarization using Gemini API."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-pro-preview-03-25"):
        """
        Initialize the ChapterSummarizer.
        
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
            temperature=0.2,
            max_output_tokens=4096
        )
        
        # Initialize text splitter for long chapters
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=8000,
            chunk_overlap=200,
            length_function=len
        )
        
        logger.info(f"Initialized ChapterSummarizer with model: {model_name}")
    
    def _create_summary_prompt(self) -> PromptTemplate:
        """
        Create a prompt template for chapter summarization.
        
        Returns:
            PromptTemplate for chapter summarization.
        """
        summary_template = """
        You are an educational AI assistant tasked with summarizing textbook chapters for students.
        
        Please summarize the following chapter text in 300-500 words. For each key concept, provide:
        1. A clear explanation of the concept.
        2. A real-world application or example.
        3. An analogy to make it relatable.
        
        Format the output in the following way:
        
        # CHAPTER SUMMARY
        [Provide a high-level summary of the chapter in 2-3 paragraphs]
        
        # KEY CONCEPTS
        
        ## [Concept Name 1]
        - **Explanation**: [Clear explanation of the concept]
        - **Example/Application**: [Real-world example or application]
        - **Analogy**: [Simple analogy to help understand the concept]
        
        ## [Concept Name 2]
        - **Explanation**: [Clear explanation of the concept]
        - **Example/Application**: [Real-world example or application]
        - **Analogy**: [Simple analogy to help understand the concept]
        
        [Continue for all key concepts, usually 4-6 concepts per chapter]
        
        Chapter Text:
        {chapter_text}
        """
        
        return PromptTemplate(
            input_variables=["chapter_text"],
            template=summary_template
        )
    
    def _create_concept_extraction_prompt(self) -> PromptTemplate:
        """
        Create a prompt template for concept extraction.
        
        Returns:
            PromptTemplate for concept extraction.
        """
        concept_template = """
        Extract the key concepts from the following chapter summary. For each concept, provide:
        1. The concept name
        2. The explanation of the concept
        3. The example or application
        4. The analogy used
        
        Format the output as JSON like this:
        ```json
        [
            {
                "name": "Concept Name",
                "explanation": "Explanation text",
                "example": "Example text",
                "analogy": "Analogy text"
            },
            ...
        ]
        ```
        
        Summary Text:
        {summary_text}
        
        Output only the JSON array. Do not include any other text, explanation or markdown formatting.
        """
        
        return PromptTemplate(
            input_variables=["summary_text"],
            template=concept_template
        )
    
    def summarize_chapter(self, chapter_text: str) -> str:
        """
        Summarize a chapter using Gemini.
        
        Args:
            chapter_text: Text content of the chapter.
            
        Returns:
            Summarized chapter text.
        """
        logger.info("Starting chapter summarization")
        
        # Handle long chapters by chunking
        if len(chapter_text) > 10000:
            return self._summarize_long_chapter(chapter_text)
        
        try:
            # Create the prompt
            summary_prompt = self._create_summary_prompt()
            
            # Create and run the chain
            summary_chain = LLMChain(llm=self.llm, prompt=summary_prompt)
            summary = summary_chain.run(chapter_text=chapter_text)
            
            logger.info("Successfully generated chapter summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing chapter: {str(e)}")
            raise
    
    def _summarize_long_chapter(self, chapter_text: str) -> str:
        """
        Summarize a long chapter by splitting it into chunks.
        
        Args:
            chapter_text: Text content of the chapter.
            
        Returns:
            Summarized chapter text.
        """
        logger.info("Chapter is long, splitting into chunks for processing")
        
        try:
            # Split the text into chunks
            chunks = self.text_splitter.split_text(chapter_text)
            logger.info(f"Split chapter into {len(chunks)} chunks")
            
            # Summarize each chunk
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                # Create a specialized prompt for chunk summarization
                chunk_prompt = PromptTemplate(
                    input_variables=["chunk_text"],
                    template="""
                    Summarize this section of a textbook chapter, identifying key concepts, 
                    definitions, and examples. Focus on extracting the essential information.
                    
                    Text section:
                    {chunk_text}
                    
                    Extract and summarize the main points and concepts from this section.
                    """
                )
                
                # Create and run the chain
                chunk_chain = LLMChain(llm=self.llm, prompt=chunk_prompt)
                chunk_summary = chunk_chain.run(chunk_text=chunk)
                chunk_summaries.append(chunk_summary)
            
            # Combine chunk summaries
            combined_summary = "\n\n".join(chunk_summaries)
            
            # Create a final summary from the combined chunk summaries
            final_prompt = PromptTemplate(
                input_variables=["combined_summary"],
                template="""
                You are an educational AI assistant tasked with creating a coherent final summary from 
                partial summaries of a textbook chapter. Reorganize and synthesize the information into 
                a comprehensive, well-structured summary.
                
                For each key concept you identify, provide:
                1. A clear explanation of the concept.
                2. A real-world application or example.
                3. An analogy to make it relatable.
                
                Format the output in the following way:
                
                # CHAPTER SUMMARY
                [Provide a high-level summary of the chapter in 2-3 paragraphs]
                
                # KEY CONCEPTS
                
                ## [Concept Name 1]
                - **Explanation**: [Clear explanation of the concept]
                - **Example/Application**: [Real-world example or application]
                - **Analogy**: [Simple analogy to help understand the concept]
                
                ## [Concept Name 2]
                - **Explanation**: [Clear explanation of the concept]
                - **Example/Application**: [Real-world example or application]
                - **Analogy**: [Simple analogy to help understand the concept]
                
                [Continue for all key concepts, usually 4-6 concepts per chapter]
                
                Partial summaries:
                {combined_summary}
                """
            )
            
            # Create and run the final chain
            final_chain = LLMChain(llm=self.llm, prompt=final_prompt)
            final_summary = final_chain.run(combined_summary=combined_summary)
            
            logger.info("Successfully generated final summary from chunks")
            return final_summary
            
        except Exception as e:
            logger.error(f"Error summarizing long chapter: {str(e)}")
            raise
    
    def extract_concepts(self, summary_text: str) -> List[Dict]:
        """
        Extract concepts from a chapter summary.
        
        Args:
            summary_text: Summarized chapter text.
            
        Returns:
            List of concepts as dictionaries.
        """
        logger.info("Extracting concepts from summary")
        
        try:
            # Create the prompt
            concept_prompt = self._create_concept_extraction_prompt()
            
            # Create and run the chain
            concept_chain = LLMChain(llm=self.llm, prompt=concept_prompt)
            concept_json_str = concept_chain.run(summary_text=summary_text)
            
            # Extract the JSON part from the response
            json_match = re.search(r'```json\s*(.*?)\s*```', concept_json_str, re.DOTALL)
            if json_match:
                concept_json_str = json_match.group(1)
            else:
                # Try to find any JSON array
                json_match = re.search(r'\[\s*\{.*\}\s*\]', concept_json_str, re.DOTALL)
                if json_match:
                    concept_json_str = json_match.group(0)
                    
            # Parse the JSON
            concepts = json.loads(concept_json_str)
            
            logger.info(f"Successfully extracted {len(concepts)} concepts")
            return concepts
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {str(e)}")
            # Return a more structured error response
            return []
    
    def explain_concept_simpler(self, concept: Dict) -> Dict:
        """
        Generate a simpler explanation for a concept.
        
        Args:
            concept: Concept dictionary with name, explanation, example, and analogy.
            
        Returns:
            Updated concept dictionary with a simpler explanation.
        """
        logger.info(f"Generating simpler explanation for concept: {concept['name']}")
        
        try:
            # Create the prompt
            simpler_prompt = PromptTemplate(
                input_variables=["concept_name", "original_explanation"],
                template="""
                Explain the following concept in simpler terms, using a longer explanation (200-300 words) 
                and a new analogy. Make it easy to understand for a beginner who has no prior knowledge 
                of the subject. Use simple language, avoid jargon, and break down complex ideas into smaller parts.
                
                Concept: {concept_name}
                Original explanation: {original_explanation}
                
                Provide:
                1. A simpler explanation (200-300 words)
                2. A new, more relatable analogy
                3. A step-by-step example if applicable
                """
            )
            
            # Create and run the chain
            simpler_chain = LLMChain(llm=self.llm, prompt=simpler_prompt)
            simpler_explanation = simpler_chain.run(
                concept_name=concept["name"],
                original_explanation=concept["explanation"]
            )
            
            # Update the concept with the simpler explanation
            updated_concept = concept.copy()
            updated_concept["simpler_explanation"] = simpler_explanation.strip()
            
            logger.info(f"Successfully generated simpler explanation for concept: {concept['name']}")
            return updated_concept
            
        except Exception as e:
            logger.error(f"Error generating simpler explanation: {str(e)}")
            # Return the original concept
            return concept


# Example usage
if __name__ == "__main__":
    # For testing purposes
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python summarizer.py <path_to_chapter_text_file> [api_key]")
        sys.exit(1)
        
    # Get API key from environment variable or command line
    api_key = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        print("Error: Google API key is required. Set GOOGLE_API_KEY environment variable or pass as argument.")
        sys.exit(1)
        
    # Read chapter text
    chapter_path = sys.argv[1]
    with open(chapter_path, 'r', encoding='utf-8') as f:
        chapter_text = f.read()
    
    # Summarize chapter
    summarizer = ChapterSummarizer(api_key)
    summary = summarizer.summarize_chapter(chapter_text)
    
    print("\n--- CHAPTER SUMMARY ---\n")
    print(summary)
    
    # Extract concepts
    concepts = summarizer.extract_concepts(summary)
    
    print("\n--- EXTRACTED CONCEPTS ---\n")
    for i, concept in enumerate(concepts):
        print(f"{i+1}. {concept['name']}")
        print(f"   Explanation: {concept['explanation'][:100]}...")
    
    # Generate simpler explanation for first concept
    if concepts:
        simpler_concept = summarizer.explain_concept_simpler(concepts[0])
        
        print("\n--- SIMPLER EXPLANATION ---\n")
        print(f"Concept: {simpler_concept['name']}")
        print(f"Simpler Explanation: {simpler_concept['simpler_explanation']}")