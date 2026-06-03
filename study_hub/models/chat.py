from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    question: str
    document_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    document_name: str
    document_id: str
