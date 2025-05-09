# EduSummarizeAI

An AI-powered educational tool that summarizes textbooks and generates practice worksheets.

## Overview

EduSummarizeAI is an application that helps students and educators extract value from educational textbooks. Users can upload PDF books, and the system will:

- Extract and organize text by chapters
- Generate comprehensive summaries with key concepts explained
- Provide interactive learning with concept understanding tracking
- Create customized practice worksheets with various question types
- Track learning progress across books and chapters


## Features

- **PDF Processing**: Extract text from uploaded books and automatically detect chapter boundaries
- **AI-Powered Summarization**: Generate concise chapter summaries with concept explanations, examples, and analogies
- **Interactive Learning**: Check concept understanding and provide simpler explanations when needed
- **Worksheet Generation**: Create printable worksheets with multiple question types (MCQs, short answers, etc.)
- **Progress Tracking**: Save and resume learning sessions across different books


## Technology Stack

- **Backend**: Python with Langchain and Google Gemini API
- **PDF Processing**: pdfplumber for text extraction
- **Document Generation**: ReportLab for PDF worksheet creation
- **Database**: SQLAlchemy for data persistence
- **UI**: Streamlit for the web interface


## Project Structure

```
edu_summarizer_ai/
├── data/               # Storage for uploaded PDFs
├── output/             # Generated worksheets and summaries
├── src/
│   ├── core/           # Core functionality modules
│   ├── db/             # Database models and operations
│   └── utils/          # Helper functions
├── ui/                 # User interface components
└── tests/              # Test modules
```


## Getting Started

### Prerequisites

- Python 3.10+
- Poetry for dependency management
- Google API key for Gemini


### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/edu-summarizer-ai.git
cd edu-summarizer-ai
```

2. Install dependencies
```bash
poetry install
```

3. Set up environment variables
```bash
# Create a .env file with your Google API key
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

4. Run the application
```bash
streamlit run ui/app.py
```

![Homepage](https://github.com/user-attachments/assets/0440f185-4069-47fa-a315-982c434e4779)

![Summary](https://github.com/user-attachments/assets/b3eeba1c-eb42-411e-ada8-ff528477483d)

## Usage

1. Upload a PDF textbook through the web interface
2. Select a chapter to study
3. Review the AI-generated summary with key concepts
4. Mark concepts as understood or request simpler explanations
5. Generate and download practice worksheets
6. Track your progress across different books and chapters

![Progress](https://github.com/user-attachments/assets/c88cb3e0-d5cd-44bb-8d2c-690fbf80484c)

![Worksheet](https://github.com/user-attachments/assets/9600259b-62a8-4644-811c-86c5b968b81a)


  
