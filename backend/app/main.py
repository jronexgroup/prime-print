from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import HOST, PORT, UPLOAD_DIR, OUTPUT_DIR
from app.database import init_db
from app.api.upload import router as upload_router
from app.api.jobs import router as jobs_router
from app.api.shop import router as shop_router
from app.ws.agent import router as ws_router
from app.services.file_manager import start_cleanup_task

ROOT_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
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

static_dir = ROOT_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
outputs_dir = ROOT_DIR / "backend" / "outputs"
outputs_dir.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/outputs", StaticFiles(directory=str(outputs_dir)), name="outputs")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "runova-print"}


@app.get("/")
async def serve_frontend():
    return FileResponse(str(ROOT_DIR / "frontend" / "index.html"))


@app.get("/frontend/{file_path:path}")
async def serve_frontend_files(file_path: str):
    full_path = ROOT_DIR / "frontend" / file_path
    if full_path.exists() and full_path.is_file():
        return FileResponse(str(full_path))
    return FileResponse(str(ROOT_DIR / "frontend" / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
