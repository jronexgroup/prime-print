import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./runova.db")

IS_RENDER = os.getenv("RENDER", "false").lower() == "true"

if IS_RENDER:
    UPLOAD_DIR = Path("/tmp/runova/uploads")
    OUTPUT_DIR = Path("/tmp/runova/outputs")
    PREVIEW_DIR = Path("/tmp/runova/previews")
else:
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./outputs"))
    PREVIEW_DIR = Path(os.getenv("PREVIEW_DIR", "../static/previews"))

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = set(
    os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,webp,heic").split(",")
)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

CLEANUP_INTERVAL_MINUTES = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "10"))
FILE_RETENTION_HOURS = int(os.getenv("FILE_RETENTION_HOURS", "1"))

A4_WIDTH_PX = 2480
A4_HEIGHT_PX = 3508
DPI = 300
