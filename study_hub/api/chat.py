from fastapi import APIRouter
from models.chat import ChatRequest, ChatResponse
from services.chat_service import get_chat_response

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    result = get_chat_response(request.question, request.document_id)
    return result
