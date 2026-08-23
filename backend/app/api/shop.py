from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Job, Shop
from app.schemas import JobResponse, PendingJobsResponse, ShopCreate, ShopResponse
from app.services.job_manager import JobManager

router = APIRouter(tags=["shop"])


def _preview_url(doc_id: str) -> str:
    return f"/api/v1/preview/{doc_id}"


@router.post("/shop", response_model=ShopResponse, status_code=201)
async def create_shop(data: ShopCreate, db: AsyncSession = Depends(get_db)):
    shop = Shop(shop_name=data.shop_name, device_id=data.device_id)
    db.add(shop)
    await db.commit()
    await db.refresh(shop)
    return shop


@router.get("/shop/{shop_id}", response_model=ShopResponse)
async def get_shop(shop_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.shop_id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.get("/shop/{shop_id}/pending", response_model=PendingJobsResponse)
async def get_pending_jobs(shop_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.shop_id == shop_id))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    jobs = await JobManager.get_pending_jobs(db, shop_id)

    return PendingJobsResponse(
        jobs=[
            JobResponse(
                job_id=j.job_id,
                shop_id=j.shop_id,
                status=j.status,
                documents=[
                    {
                        "document_id": d.document_id,
                        "document_type": d.document_type,
                        "status": d.status,
                        "preview_url": _preview_url(d.document_id) if d.preview_path else None,
                        "error_message": d.error_message,
                    }
                    for d in j.documents
                ],
                created_at=j.created_at,
                completed_at=j.completed_at,
            )
            for j in jobs
        ]
    )
