from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime

class NotesRequest(BaseModel):
    document_id: str
    detail_level: Literal["brief", "detailed"] = "detailed"

class NotesResponse(BaseModel):
    document_name: str
    summary: str
    key_concepts: List[str]
    bullet_points: List[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
