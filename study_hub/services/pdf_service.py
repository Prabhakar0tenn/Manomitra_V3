import fitz  # PyMuPDF
import os
import re
from config import settings

def validate_pdf(file_name: str, file_size: int) -> tuple[bool, str]:
    """
    Check if file is valid: extension is .pdf and size <= MAX_FILE_SIZE_MB.
    Returns (is_ok, reason).
    """
    if not file_name.lower().endswith('.pdf'):
        return False, "Only PDF files are accepted"
    
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        return False, f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
        
    return True, ""

def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extracts text from PDF, cleans it, and returns the cleaned text,
    page count, and text length.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at {file_path}")

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError(f"Could not open PDF file: {e}")

    page_count = len(doc)
    page_texts = []

    for idx in range(page_count):
        try:
            page = doc[idx]
            text = page.get_text("text") or ""
            
            # Clean text per page:
            # Strip leading/trailing whitespace
            cleaned = text.strip()
            # Remove null bytes
            cleaned = cleaned.replace('\x00', '')
            # Replace multiple newlines (3+) with double newline
            cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
            # Remove weird unicode characters (surrogates)
            cleaned = cleaned.encode('utf-8', 'ignore').decode('utf-8')
            
            page_texts.append(cleaned)
        except Exception as e:
            # Append empty text or log warning
            page_texts.append("")

    doc.close()
    
    # Format with separators: "--- Page {n} ---"
    formatted_pages = []
    for idx, page_text in enumerate(page_texts):
        page_num = idx + 1
        formatted_pages.append(f"--- Page {page_num} ---\n\n{page_text}")
    
    full_text = "\n\n".join(formatted_pages).strip()
    
    return {
        "text": full_text,
        "page_count": page_count,
        "text_length": len(full_text)
    }
