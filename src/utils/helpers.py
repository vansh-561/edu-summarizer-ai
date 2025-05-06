"""
Helper Functions for EduSummarizeAI.

This module provides utility functions used across the application.
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional#,Any
#from pathlib import Path
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory.
    """
    os.makedirs(directory_path, exist_ok=True)
    logger.debug(f"Ensured directory exists: {directory_path}")

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove invalid characters.
    
    Args:
        filename: Original filename.
        
    Returns:
        Sanitized filename.
    """
    # Replace invalid characters with underscore
    sanitized = re.sub(r'[^\w\s-]', '', filename).strip().replace(' ', '_')
    return sanitized

def load_json_file(file_path: str) -> Dict:
    """
    Load a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Dictionary containing the JSON data.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON file: {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {str(e)}")
        return {}

def save_json_file(data: Dict, file_path: str) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Dictionary to save.
        file_path: Path to save the JSON file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory_exists(directory)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved JSON file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {str(e)}")
        return False

def format_timestamp(timestamp: Optional[datetime.datetime] = None) -> str:
    """
    Format a timestamp for display or filename use.
    
    Args:
        timestamp: Datetime object to format. Uses current time if None.
        
    Returns:
        Formatted timestamp string.
    """
    if timestamp is None:
        timestamp = datetime.datetime.now()
    return timestamp.strftime("%Y%m%d_%H%M%S")

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate.
        max_length: Maximum length.
        suffix: Suffix to add to truncated text.
        
    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def extract_concepts_from_markdown(markdown_text: str) -> List[Dict[str, str]]:
    """
    Extract concepts from a markdown-formatted summary.
    
    Args:
        markdown_text: Markdown text containing concepts.
        
    Returns:
        List of concept dictionaries.
    """
    concepts = []
    
    # Look for concept sections (## [Concept Name])
    concept_sections = re.findall(r'##\s+(.+?)\n(.*?)(?=##|\Z)', markdown_text, re.DOTALL)
    
    for name, content in concept_sections:
        # Extract explanation, example, and analogy
        explanation = ""
        example = ""
        analogy = ""
        
        explanation_match = re.search(r'\*\*Explanation\*\*:\s*(.*?)(?=\*\*|\n\n|\Z)', content, re.DOTALL)
        if explanation_match:
            explanation = explanation_match.group(1).strip()
            
        example_match = re.search(r'\*\*Example/Application\*\*:\s*(.*?)(?=\*\*|\n\n|\Z)', content, re.DOTALL)
        if example_match:
            example = example_match.group(1).strip()
            
        analogy_match = re.search(r'\*\*Analogy\*\*:\s*(.*?)(?=\*\*|\n\n|\Z)', content, re.DOTALL)
        if analogy_match:
            analogy = analogy_match.group(1).strip()
        
        concepts.append({
            "name": name.strip(),
            "explanation": explanation,
            "example": example,
            "analogy": analogy
        })
    
    return concepts

def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        File extension (without the dot).
    """
    return os.path.splitext(file_path)[1][1:].lower()

def is_valid_api_key(api_key: str) -> bool:
    """
    Check if an API key is valid (basic format check).
    
    Args:
        api_key: API key to check.
        
    Returns:
        True if the API key has a valid format, False otherwise.
    """
    # Basic check for Google API key format (typically starts with "AIza")
    return bool(api_key and len(api_key) > 20 and api_key.startswith("AIza"))


# Example usage
if __name__ == "__main__":
    # Test helper functions
    print(f"Sanitized filename: {sanitize_filename('My File Name! @#$%.pdf')}")
    print(f"Truncated text: {truncate_text('This is a long text that needs to be truncated', 20)}")
    print(f"Current timestamp: {format_timestamp()}")
