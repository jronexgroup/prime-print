from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    document_id: str
    document_type: Optional[str] = None
    status: str
    preview_url: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    job_id: str
    shop_id: str
    status: str
    documents: List[DocumentResponse] = []
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    documents: List[DocumentResponse] = []

    class Config:
        from_attributes = True


class ShopCreate(BaseModel):
    shop_name: str
    device_id: Optional[str] = None


class ShopResponse(BaseModel):
    shop_id: str
    shop_name: str
    device_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PendingJobsResponse(BaseModel):
    jobs: List[JobResponse]


class DocumentConfirmResponse(BaseModel):
    document_id: str
    status: str


class DocumentRejectResponse(BaseModel):
    document_id: str
    status: str
    message: str


class ErrorResponse(BaseModel):
    error: dict
