from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import HOST, PORT, UPLOAD_DIR, OUTPUT_DIR, PREVIEW_DIR, IS_RENDER
from app.database import init_db
from app.api.upload import router as upload_router
from app.api.jobs import router as jobs_router
from app.api.shop import router as shop_router
from app.ws.agent import router as ws_router
from app.services.file_manager import start_cleanup_task

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
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


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "runova-print"}


@app.get("/api/v1/preview/{document_id}")
async def serve_preview(document_id: str):
    preview_path = PREVIEW_DIR / f"{document_id}.jpg"
    if not preview_path.exists():
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Preview not found"})
    return FileResponse(str(preview_path), media_type="image/jpeg")


@app.get("/api/v1/pdf/{document_id}")
async def serve_pdf(document_id: str):
    pdf_path = OUTPUT_DIR / f"{document_id}.pdf"
    if not pdf_path.exists():
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "PDF not found"})
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=f"{document_id}.pdf",
    )


@app.get("/")
async def root():
    return FileResponse(str(ROOT_DIR / "frontend" / "index.html"))


@app.get("/frontend/{file_path:path}")
async def serve_frontend(file_path: str):
    full_path = ROOT_DIR / "frontend" / file_path
    if full_path.is_file():
        return FileResponse(str(full_path))
    return FileResponse(str(ROOT_DIR / "frontend" / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
