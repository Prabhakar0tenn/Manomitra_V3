import uuid
import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from config import settings
from utils.db import db_manager
from services.pdf_service import validate_pdf, extract_text_from_pdf
from models.document import DocumentMetadataResponse

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # 1. Read file to check size
    contents = await file.read()
    file_size = len(contents)
    
    # Reset file read pointer
    await file.seek(0)
    
    # 2. Validate PDF + size
    is_valid, reason = validate_pdf(file.filename, file_size)
    if not is_valid:
        if "size" in reason.lower() or "limit" in reason.lower():
            raise HTTPException(status_code=413, detail=reason)
        else:
            raise HTTPException(status_code=400, detail=reason)
            
    # Create upload directory if it does not exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate UUID and paths
    document_id = str(uuid.uuid4())
    safe_filename = f"{document_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    # 3. Save file to UPLOAD_DIR
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
        
    # 4. Extract text with PyMuPDF
    try:
        extracted = extract_text_from_pdf(file_path)
        text = extracted["text"]
        page_count = extracted["page_count"]
        text_length = extracted["text_length"]
        
        # Check if text is extracted
        # If no text was extracted (e.g. image-only PDF), raise exception
        # Strip page numbers/headers to see if there's actual content
        raw_text_stripped = re_clean = text.replace("--- Page", "").strip()
        if not raw_text_stripped or len(raw_text_stripped) < 5:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=400, 
                detail="Could not extract text from PDF. Make sure it is not a scanned image-only PDF"
            )
            
        status = "processed"
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to process PDF: {e}")
        
    # 5. Save to database
    doc_record = {
        "document_id": document_id,
        "filename": safe_filename,
        "original_name": file.filename,
        "upload_date": datetime.utcnow(),
        "file_size": file_size,
        "file_path": file_path,
        "page_count": page_count,
        "extracted_text": text,
        "text_length": text_length,
        "status": status
    }
    
    collection = db_manager.get_collection("study_hub_documents")
    collection.insert_one(doc_record)
    
    return {
        "success": True,
        "document_id": document_id,
        "filename": file.filename,
        "page_count": page_count,
        "text_length": text_length,
        "message": "Document processed successfully"
    }

@router.get("", response_model=list[DocumentMetadataResponse])
async def get_documents():
    collection = db_manager.get_collection("study_hub_documents")
    docs = collection.find({}, {"extracted_text": 0})
    
    result = []
    for doc in docs:
        result.append(DocumentMetadataResponse(
            document_id=doc["document_id"],
            original_name=doc["original_name"],
            upload_date=doc["upload_date"],
            page_count=doc["page_count"],
            file_size=doc["file_size"],
            status=doc["status"]
        ))
    return result

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    collection = db_manager.get_collection("study_hub_documents")
    doc = collection.find_one({"document_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    collection.delete_one({"document_id": document_id})
    
    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
            
    return {"success": True, "message": "Document deleted"}
