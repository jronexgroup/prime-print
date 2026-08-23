from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Document, Job, Shop


class JobManager:

    VALID_TRANSITIONS = {
        "UPLOADED": ["VALIDATING"],
        "VALIDATING": ["PROCESSING", "FAILED"],
        "PROCESSING": ["READY", "FAILED"],
        "READY": ["PREVIEW"],
        "PREVIEW": ["CONFIRMED", "FAILED"],
        "CONFIRMED": ["PRINTING"],
        "PRINTING": ["COMPLETED", "FAILED"],
        "FAILED": ["UPLOADED", "MANUAL_REVIEW"],
        "COMPLETED": [],
        "MANUAL_REVIEW": [],
    }

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        return target in cls.VALID_TRANSITIONS.get(current, [])

    @classmethod
    async def create_job(cls, db: AsyncSession, shop_id: str, file_count: int) -> Job:
        job = Job(shop_id=shop_id, status="UPLOADED")
        db.add(job)
        await db.flush()
        return job

    @classmethod
    async def transition_job(
        cls, db: AsyncSession, job_id: str, target_status: str
    ) -> Job:
        result = await db.execute(
            select(Job).where(Job.job_id == job_id).options(selectinload(Job.documents))
        )
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if not cls.can_transition(job.status, target_status):
            raise ValueError(
                f"Cannot transition from {job.status} to {target_status}"
            )
        job.status = target_status
        if target_status in ("COMPLETED", "FAILED"):
            job.completed_at = datetime.now(timezone.utc)
        return job

    @classmethod
    async def transition_document(
        cls, db: AsyncSession, document_id: str, target_status: str, error: str = None
    ) -> Document:
        result = await db.execute(
            select(Document).where(Document.document_id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        doc.status = target_status
        if error:
            doc.error_message = error
        return doc

    @classmethod
    async def get_job(
        cls, db: AsyncSession, job_id: str
    ) -> Optional[Job]:
        result = await db.execute(
            select(Job).where(Job.job_id == job_id).options(selectinload(Job.documents))
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_pending_jobs(cls, db: AsyncSession, shop_id: str):
        result = await db.execute(
            select(Job)
            .where(Job.shop_id == shop_id, Job.status.in_(["READY", "PREVIEW"]))
            .options(selectinload(Job.documents))
            .order_by(Job.created_at)
        )
        return result.scalars().all()

    @classmethod
    async def are_all_documents_complete(cls, db: AsyncSession, job_id: str) -> bool:
        result = await db.execute(
            select(Document).where(Document.job_id == job_id)
        )
        docs = result.scalars().all()
        return all(d.status in ("COMPLETED", "FAILED") for d in docs)
