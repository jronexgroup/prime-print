import asyncio
import json
import logging
import os
import platform
import sys
import tempfile
import threading
import time
import uuid

import requests

from websocket_client import WebSocketClient
from printer import download_pdf, print_pdf, open_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("agent")

DEFAULT_SERVER = "http://localhost:8000"
SYSTEM = platform.system()


class RunovaAgent:
    def __init__(self, server_url: str, device_id: str):
        self.server_url = server_url.rstrip("/")
        self.device_id = device_id
        self.shop_id = None
        self.ws_client = None
        self._running = False
        self._preview_shown = set()
        self._has_tkinter = self._check_tkinter()

    def _check_tkinter(self):
        try:
            import tkinter
            return True
        except ImportError:
            return False

    def run(self):
        logger.info("=" * 50)
        logger.info("  Runova Print Agent")
        logger.info(f"  Platform:  {SYSTEM}")
        logger.info(f"  Server:    {self.server_url}")
        logger.info(f"  Device:    {self.device_id[:12]}...")
        logger.info(f"  Tkinter:   {'Yes' if self._has_tkinter else 'No (console mode)'}")
        logger.info("=" * 50)

        self.shop_id = self._setup_shop()
        if not self.shop_id:
            logger.error("Failed to setup shop. Check server is running.")
            return

        logger.info(f"Shop ID: {self.shop_id}")
        logger.info("")
        logger.info("Share this URL with customers:")
        logger.info(f"  {self.server_url}/?shop_id={self.shop_id}")
        logger.info("")
        self._running = True

        self.ws_client = WebSocketClient(
            self.server_url, self.device_id, self._on_ws_message
        )

        ws_thread = threading.Thread(target=self._run_ws_loop, daemon=True)
        ws_thread.start()

        poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        poll_thread.start()

        logger.info("Agent running. Press Ctrl+C to stop.")
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self._running = False
            if self.ws_client:
                self.ws_client.stop()

    def _run_ws_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.ws_client.connect())

    def _setup_shop(self) -> str | None:
        try:
            url = f"{self.server_url}/api/v1/shop/{self.device_id}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                shop = resp.json()
                logger.info(f"Found existing shop: {shop['shop_name']}")
                return shop["shop_id"]
        except Exception:
            pass

        try:
            url = f"{self.server_url}/api/v1/shop"
            resp = requests.post(
                url,
                json={"shop_name": f"Shop {self.device_id[:8]}", "device_id": self.device_id},
                timeout=10,
            )
            if resp.status_code == 201:
                shop = resp.json()
                logger.info(f"Created shop: {shop['shop_name']}")
                return shop["shop_id"]
        except Exception as e:
            logger.error(f"Setup error: {e}")
        return None

    def _on_ws_message(self, data: dict):
        msg_type = data.get("type")
        if msg_type == "new_job":
            job_id = data.get("job_id")
            logger.info(f"NEW JOB: {job_id}")
            threading.Thread(target=self._process_job, args=(job_id,), daemon=True).start()

    def _process_job(self, job_id: str):
        try:
            resp = requests.get(f"{self.server_url}/api/v1/jobs/{job_id}", timeout=10)
            if resp.status_code != 200:
                logger.error(f"Failed to get job {job_id}: HTTP {resp.status_code}")
                return
            job = resp.json()
            logger.info(f"Job {job_id}: status={job['status']}, docs={len(job['documents'])}")
            for doc in job.get("documents", []):
                if doc["status"] == "READY" and doc["document_id"] not in self._preview_shown:
                    self._handle_document(doc)
        except Exception as e:
            logger.error(f"Job error: {e}")

    def _handle_document(self, doc: dict):
        doc_id = doc["document_id"]
        doc_type = doc.get("document_type", "unknown")
        self._preview_shown.add(doc_id)

        logger.info(f"Document ready: {doc_type} ({doc_id[:8]}...)")

        temp_dir = tempfile.mkdtemp()
        pdf_path = download_pdf(self.server_url, doc_id, temp_dir)
        if not pdf_path:
            logger.error(f"Failed to download PDF for {doc_id}")
            return

        if self._has_tkinter:
            self._show_popup(doc_id, doc_type, pdf_path)
        else:
            self._show_console(doc_id, doc_type, pdf_path)

    def _show_console(self, doc_id: str, doc_type: str, pdf_path: str):
        logger.info("=" * 50)
        logger.info(f"  DOCUMENT READY: {doc_type.replace('_', ' ').title()}")
        logger.info(f"  PDF: {pdf_path}")
        logger.info("=" * 50)
        logger.info("  Commands:")
        logger.info("    p = Print")
        logger.info("    o = Open PDF")
        logger.info("    s = Skip")
        logger.info("    q = Quit")
        logger.info("=" * 50)

        try:
            while True:
                choice = input("  Your choice: ").strip().lower()
                if choice == "p":
                    logger.info("Printing...")
                    success = print_pdf(pdf_path)
                    if success:
                        logger.info("Print sent!")
                        try:
                            loop = asyncio.new_event_loop()
                            loop.run_until_complete(
                                self.ws_client.send({"type": "print_complete", "document_id": doc_id})
                            )
                            loop.close()
                        except Exception:
                            pass
                    else:
                        logger.error("Print failed!")
                    break
                elif choice == "o":
                    open_pdf(pdf_path)
                    logger.info("PDF opened")
                elif choice == "s":
                    logger.info("Skipped")
                    break
                elif choice == "q":
                    self._running = False
                    break
                else:
                    logger.info("Invalid choice. Enter p, o, s, or q.")
        except (EOFError, KeyboardInterrupt):
            logger.info("Skipped (no input)")

    def _show_popup(self, doc_id: str, doc_type: str, pdf_path: str):
        try:
            import tkinter as tk

            root = tk.Tk()
            root.title("Runova Print")
            root.geometry("420x480")
            root.resizable(False, False)
            root.configure(bg="white")

            header = tk.Frame(root, bg="#1a73e8", height=50)
            header.pack(fill="x")
            header.pack_propagate(False)
            tk.Label(header, text="RUNOVA PRINT", bg="#1a73e8", fg="white",
                     font=("Arial", 14, "bold")).pack(expand=True)

            body = tk.Frame(root, bg="white", pady=20)
            body.pack(fill="both", expand=True, padx=20)

            tk.Label(body, text="New Document Ready", font=("Arial", 16, "bold"),
                     bg="white").pack()
            tk.Label(body, text=f"Type: {doc_type.replace('_', ' ').title()}",
                     font=("Arial", 12), fg="#666", bg="white").pack(pady=(8, 0))
            tk.Label(body, text=f"ID: {doc_id[:8]}...", font=("Arial", 10),
                     fg="#999", bg="white").pack(pady=(4, 0))

            preview_frame = tk.Frame(body, bg="#f0f0f0", height=200)
            preview_frame.pack(fill="x", pady=20)
            preview_frame.pack_propagate(False)
            tk.Label(preview_frame, text=f"[ {pdf_path.split('/')[-1]} ]",
                     bg="#f0f0f0", fg="#666", font=("Arial", 11)).pack(expand=True)

            btn_frame = tk.Frame(root, bg="white", pady=15)
            btn_frame.pack(fill="x")

            def on_confirm():
                logger.info(f"Printing {doc_id[:8]}...")
                success = print_pdf(pdf_path)
                if success:
                    logger.info("Print complete!")
                    try:
                        loop = asyncio.new_event_loop()
                        loop.run_until_complete(
                            self.ws_client.send({"type": "print_complete", "document_id": doc_id})
                        )
                        loop.close()
                    except Exception:
                        pass
                else:
                    logger.error("Print failed!")
                root.destroy()

            def on_reject():
                logger.info(f"Rejected {doc_id[:8]}")
                root.destroy()

            confirm_btn = tk.Button(btn_frame, text="PRINT", bg="#34a853", fg="white",
                                    font=("Arial", 12, "bold"), padx=30, pady=10,
                                    command=on_confirm, cursor="hand2")
            confirm_btn.pack(side="left", padx=(10, 5), expand=True, fill="x")

            reject_btn = tk.Button(btn_frame, text="REJECT", bg="#ea4335", fg="white",
                                   font=("Arial", 12, "bold"), padx=30, pady=10,
                                   command=on_reject, cursor="hand2")
            reject_btn.pack(side="right", padx=(5, 10), expand=True, fill="x")

            root.mainloop()

        except Exception as e:
            logger.warning(f"Popup failed ({e}), falling back to console")
            self._show_console(doc_id, doc_type, pdf_path)

    def _poll_loop(self):
        while self._running:
            try:
                resp = requests.get(
                    f"{self.server_url}/api/v1/shop/{self.shop_id}/pending", timeout=10
                )
                if resp.status_code == 200:
                    jobs = resp.json().get("jobs", [])
                    if jobs:
                        logger.info(f"Poll: {len(jobs)} pending job(s)")
                    for job in jobs:
                        if job["status"] in ("READY", "PREVIEW"):
                            for doc in job.get("documents", []):
                                if doc["status"] == "READY" and doc["document_id"] not in self._preview_shown:
                                    threading.Thread(
                                        target=self._handle_document, args=(doc,), daemon=True
                                    ).start()
            except Exception as e:
                logger.debug(f"Poll error: {e}")
            time.sleep(3)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Runova Print Agent")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Server URL")
    parser.add_argument("--device-id", default=str(uuid.uuid4()), help="Device ID")
    args = parser.parse_args()

    agent = RunovaAgent(args.server, args.device_id)
    agent.run()


if __name__ == "__main__":
    main()
