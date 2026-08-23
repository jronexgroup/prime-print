from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Document, Job
from app.schemas import (
    DocumentConfirmResponse,
    DocumentRejectResponse,
    JobStatusResponse,
)
from app.services.job_manager import JobManager

router = APIRouter(tags=["jobs"])


def _preview_url(doc_id: str) -> str:
    return f"/api/v1/preview/{doc_id}"


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await JobManager.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        documents=[
            {
                "document_id": d.document_id,
                "document_type": d.document_type,
                "status": d.status,
                "preview_url": _preview_url(d.document_id) if d.preview_path else None,
                "error_message": d.error_message,
            }
            for d in job.documents
        ],
    )


@router.patch(
    "/jobs/{job_id}/documents/{document_id}/confirm",
    response_model=DocumentConfirmResponse,
)
async def confirm_document(
    job_id: str,
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    doc = await JobManager.transition_document(db, document_id, "CONFIRMED")
    await db.commit()

    all_done = await JobManager.are_all_documents_complete(db, job_id)
    if all_done:
        try:
            await JobManager.transition_job(db, job_id, "CONFIRMED")
            await db.commit()
        except ValueError:
            pass

    return DocumentConfirmResponse(document_id=doc.document_id, status=doc.status)


@router.patch(
    "/jobs/{job_id}/documents/{document_id}/reject",
    response_model=DocumentRejectResponse,
)
async def reject_document(
    job_id: str,
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    doc = await JobManager.transition_document(
        db, document_id, "FAILED", error="Rejected by shopkeeper"
    )
    await db.commit()

    all_done = await JobManager.are_all_documents_complete(db, job_id)
    if all_done:
        try:
            await JobManager.transition_job(db, job_id, "FAILED")
            await db.commit()
        except ValueError:
            pass

    return DocumentRejectResponse(
        document_id=doc.document_id,
        status=doc.status,
        message="Document rejected",
    )
