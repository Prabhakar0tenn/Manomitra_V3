from pydantic import BaseModel, Field
from typing import Dict, List, Literal

class QuizRequest(BaseModel):
    document_id: str
    num_questions: int = 5
    difficulty: Literal["easy", "medium", "hard"] = "medium"

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str

class QuizResponse(BaseModel):
    document_name: str
    total_questions: int
    questions: List[QuizQuestion]
