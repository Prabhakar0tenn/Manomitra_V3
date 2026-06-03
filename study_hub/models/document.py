from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class DocumentMetadataResponse(BaseModel):
    document_id: str
    original_name: str
    upload_date: datetime
    page_count: int
    file_size: int
    status: Literal["processed", "failed"]
