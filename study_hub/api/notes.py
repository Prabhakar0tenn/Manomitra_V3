from fastapi import APIRouter
from models.notes import NotesRequest, NotesResponse
from services.notes_service import generate_study_notes

router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("/generate", response_model=NotesResponse)
async def generate_notes_endpoint(request: NotesRequest):
    result = generate_study_notes(request.document_id, request.detail_level)
    return result
