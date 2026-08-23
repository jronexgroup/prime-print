import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import async_session
from app.models import Shop
from app.ws.connection import manager

router = APIRouter()

device_shop_map: dict[str, str] = {}


@router.websocket("/ws/agent/{device_id}")
async def agent_websocket(websocket: WebSocket, device_id: str):
    await manager.connect(device_id, websocket)

    async with async_session() as db:
        result = await db.execute(
            select(Shop).where(Shop.device_id == device_id)
        )
        shop = result.scalar_one_or_none()
        if shop:
            device_shop_map[device_id] = shop.shop_id

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "agent_ready":
                pass

            elif msg_type == "print_complete":
                from app.services.job_manager import JobManager
                doc_id = data.get("document_id")
                if doc_id:
                    async with async_session() as db:
                        await JobManager.transition_document(db, doc_id, "COMPLETED")
                        await db.commit()

            elif msg_type == "print_failed":
                from app.services.job_manager import JobManager
                doc_id = data.get("document_id")
                error = data.get("error", "Print failed")
                if doc_id:
                    async with async_session() as db:
                        await JobManager.transition_document(
                            db, doc_id, "FAILED", error=error
                        )
                        await db.commit()

    except WebSocketDisconnect:
        manager.disconnect(device_id)
        device_shop_map.pop(device_id, None)
