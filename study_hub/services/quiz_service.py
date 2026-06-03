from utils.db import db_manager
from utils.gemini_client import generate_quiz as gemini_generate_quiz
from fastapi import HTTPException

def generate_study_quiz(document_id: str, num_questions: int, difficulty: str) -> dict:
    collection = db_manager.get_collection("study_hub_documents")
    doc = collection.find_one({"document_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    context = doc.get("extracted_text", "")
    if not context or not context.strip():
        raise HTTPException(
            status_code=400, 
            detail="Could not extract text from PDF. Make sure it is not a scanned image-only PDF"
        )
        
    doc_name = doc.get("original_name", "Document")
    
    questions = gemini_generate_quiz(context, doc_name, num_questions, difficulty)
    
    return {
        "document_name": doc_name,
        "total_questions": len(questions),
        "questions": questions
    }
