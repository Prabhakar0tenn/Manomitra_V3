from utils.db import db_manager
from utils.gemini_client import answer_from_context
from fastapi import HTTPException

def get_chat_response(question: str, document_id: str) -> dict:
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
    
    result = answer_from_context(question, context, doc_name)
    result["document_id"] = document_id
    
    return result
