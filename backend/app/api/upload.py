import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, UPLOAD_DIR
from app.database import get_db
from app.models import Document, Job, Shop
from app.schemas import JobResponse
from app.services.job_manager import JobManager

router = APIRouter(tags=["upload"])


def validate_file(file: UploadFile) -> None:
    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": f"File type '{ext}' is not supported.",
                    "retryable": False,
                }
            },
        )


async def process_job_background(job_id: str):
    from app.processing.pipeline import process_document
    from app.database import async_session

    async with async_session() as db:
        result = await db.execute(
            select(Document).where(Document.job_id == job_id)
        )
        documents = result.scalars().all()

        for doc in documents:
            try:
                await JobManager.transition_document(db, doc.document_id, "VALIDATING")
                await db.commit()

                await JobManager.transition_document(db, doc.document_id, "PROCESSING")
                await db.commit()

                output = process_document(doc.input_path)

                doc.output_path = output["output_path"]
                doc.preview_path = output["preview_path"]
                doc.document_type = output["document_type"]
                await JobManager.transition_document(db, doc.document_id, "READY")
                await db.commit()

            except Exception as e:
                import traceback
                traceback.print_exc()
                await JobManager.transition_document(
                    db, doc.document_id, "FAILED", error=str(e)
                )
                await db.commit()

        job = await JobManager.get_job(db, job_id)
        all_done = await JobManager.are_all_documents_complete(db, job_id)
        if all_done:
            has_failed = any(d.status == "FAILED" for d in job.documents)
            target = "FAILED" if has_failed else "READY"
            await JobManager.transition_job(db, job_id, target)
            await db.commit()


def _preview_url(doc_id: str) -> str:
    return f"/api/v1/preview/{doc_id}"


@router.post("/upload/{shop_id}", response_model=JobResponse, status_code=201)
async def upload_documents(
    shop_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Shop).where(Shop.shop_id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    for f in files:
        validate_file(f)

    job = await JobManager.create_job(db, shop_id, len(files))
    await db.flush()

    document_ids = []
    for f in files:
        ext = Path(f.filename or "upload.jpg").suffix or ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / filename

        content = await f.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "message": f"File '{f.filename}' exceeds {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.",
                        "retryable": False,
                    }
                },
            )

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

        doc = Document(
            job_id=job.job_id,
            input_path=str(file_path),
            status="UPLOADED",
        )
        db.add(doc)
        await db.flush()
        document_ids.append(doc.document_id)

    await db.commit()

    result = await db.execute(
        select(Document).where(Document.job_id == job.job_id)
    )
    documents = result.scalars().all()

    background_tasks.add_task(process_job_background, job.job_id)

    return JobResponse(
        job_id=job.job_id,
        shop_id=shop_id,
        status=job.status,
        documents=[
            {
                "document_id": d.document_id,
                "document_type": d.document_type,
                "status": d.status,
                "preview_url": _preview_url(d.document_id) if d.preview_path else None,
                "error_message": d.error_message,
            }
            for d in documents
        ],
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
