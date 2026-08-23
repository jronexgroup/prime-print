import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import CLEANUP_INTERVAL_MINUTES, FILE_RETENTION_HOURS, OUTPUT_DIR, UPLOAD_DIR


def cleanup_old_files():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FILE_RETENTION_HOURS)
    cutoff_ts = cutoff.timestamp()

    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if path.is_file() and path.stat().st_mtime < cutoff_ts:
                path.unlink(missing_ok=True)


async def _cleanup_loop():
    while True:
        try:
            cleanup_old_files()
        except Exception:
            pass
        await asyncio.sleep(CLEANUP_INTERVAL_MINUTES * 60)


def start_cleanup_task():
    task = asyncio.create_task(_cleanup_loop())
    return task
