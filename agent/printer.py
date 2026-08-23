import os
import platform
import subprocess
import logging

logger = logging.getLogger("agent")
SYSTEM = platform.system()


def download_pdf(server_url: str, document_id: str, dest_dir: str) -> str | None:
    import requests
    try:
        url = f"{server_url}/api/v1/pdf/{document_id}"
        logger.info(f"Downloading PDF from {url}")
        resp = requests.get(url, stream=True, timeout=30)
        if resp.status_code == 200:
            dest_path = os.path.join(dest_dir, f"{document_id}.pdf")
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"PDF saved to {dest_path}")
            return dest_path
        logger.error(f"Download failed: HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Download error: {e}")
    return None


def open_pdf(pdf_path: str) -> bool:
    """Open PDF in default viewer (non-blocking)."""
    try:
        if SYSTEM == "Windows":
            os.startfile(pdf_path)
            return True
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", pdf_path])
            return True
        else:
            subprocess.Popen(["xdg-open", pdf_path])
            return True
    except Exception as e:
        logger.error(f"Open PDF error: {e}")
        return False


def print_pdf(pdf_path: str, printer_name: str = None) -> bool:
    """Send PDF to system printer."""
    try:
        if SYSTEM == "Windows":
            if printer_name:
                subprocess.run(
                    ["rundll32.exe", "shell32.dll,ShellExec_rundll32", "pdf.dll,PrintPDF", pdf_path],
                    timeout=30, capture_output=True,
                )
            else:
                os.startfile(pdf_path, "print")
            return True
        elif SYSTEM == "Darwin":
            cmd = ["lpr"]
            if printer_name:
                cmd += ["-P", printer_name]
            cmd.append(pdf_path)
            subprocess.run(cmd, check=True, timeout=30)
            return True
        else:
            cmd = ["lp"]
            if printer_name:
                cmd += ["-d", printer_name]
            cmd.append(pdf_path)
            subprocess.run(cmd, check=True, timeout=30)
            return True
    except Exception as e:
        logger.error(f"Print error: {e}")
        return False
