"""
Text extraction module supporting PDF, DOCX, and TXT resume files.
"""

import os
import fitz  # PyMuPDF
import docx  # python-docx

def extract_text_from_resume(file_input):
    """
    Determines file type and extracts clean plain text.
    
    Args:
        file_input: File path string or Gradio File wrapper object.
        
    Returns:
        tuple: (extracted_text, error_message)
    """
    if not file_input:
        return None, "No file provided."

    file_path = file_input.name if hasattr(file_input, 'name') else str(file_input)

    if not os.path.exists(file_path):
        return None, f"File not found at path: {file_path}"

    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == ".pdf":
            doc = fitz.open(file_path)
            pages_text = [page.get_text() for page in doc]
            text = "\n".join(pages_text).strip()
            if not text:
                return None, "PDF file appears to be empty or contains scanned images without OCR text."
            return text, None

        elif ext in [".docx", ".doc"]:
            doc = docx.Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            text = "\n".join(paragraphs).strip()
            if not text:
                return None, "DOCX file appears to be empty."
            return text, None

        elif ext in [".txt", ".md"]:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read().strip()
                if not text:
                    return None, "Text file is empty."
                return text, None
        else:
            return None, f"Unsupported file format '{ext}'. Please upload a PDF, DOCX, or TXT file."
            
    except Exception as e:
        return None, f"Failed to extract text from file: {str(e)}"
