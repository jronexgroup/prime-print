import logging
import os
import subprocess
import tempfile
from pathlib import Path

import requests

logger = logging.getLogger("runova_agent")


def download_pdf(server_url: str, document_id: str, dest_dir: str) -> str | None:
    try:
        url = f"{server_url}/documents/{document_id}/pdf"
        resp = requests.get(url, stream=True, timeout=30)
        if resp.status_code == 200:
            dest_path = os.path.join(dest_dir, f"{document_id}.pdf")
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return dest_path
        logger.error(f"Download failed: {resp.status_code}")
    except Exception as e:
        logger.error(f"Download error: {e}")
    return None


def print_pdf(pdf_path: str, printer_name: str = None) -> bool:
    try:
        if os.name == "nt":
            if printer_name:
                subprocess.run(
                    [
                        "rundll32.exe",
                        "shell32.dll,ShellExec_pdf",
                        "print",
                        f"/d {printer_name}",
                        pdf_path,
                    ],
                    check=True,
                    timeout=30,
                )
            else:
                os.startfile(pdf_path, "print")
            return True
        else:
            if printer_name:
                subprocess.run(["lp", "-d", printer_name, pdf_path], check=True, timeout=30)
            else:
                subprocess.run(["lp", pdf_path], check=True, timeout=30)
            return True
    except Exception as e:
        logger.error(f"Print error: {e}")
        return False
