from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import HOST, PORT
from app.database import init_db
from app.api.upload import router as upload_router
from app.api.jobs import router as jobs_router
from app.api.shop import router as shop_router
from app.ws.agent import router as ws_router
from app.services.file_manager import start_cleanup_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    cleanup_task = start_cleanup_task()
    yield
    cleanup_task.cancel()


app = FastAPI(
    title="Runova Print",
    description="Automated document-to-print pipeline",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(upload_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(shop_router, prefix="/api/v1")
app.include_router(ws_router)

static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "runova-print"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
