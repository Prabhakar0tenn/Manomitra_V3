from fastapi import APIRouter
from models.quiz import QuizRequest, QuizResponse
from services.quiz_service import generate_study_quiz

router = APIRouter(prefix="/quiz", tags=["quiz"])

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz_endpoint(request: QuizRequest):
    result = generate_study_quiz(request.document_id, request.num_questions, request.difficulty)
    return result
