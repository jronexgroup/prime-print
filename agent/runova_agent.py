import logging
import sys
import threading
import uuid

import requests

from websocket_client import WebSocketClient
from printer import download_pdf, print_pdf
from preview import PreviewWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("runova_agent")

SERVER_URL = "http://localhost:8000"
DEVICE_ID = str(uuid.uuid4())
POLL_INTERVAL = 5


class RunovaAgent:
    def __init__(self):
        self.server_url = SERVER_URL
        self.device_id = DEVICE_ID
        self.shop_id = None
        self.ws_client = None
        self.preview = PreviewWindow()
        self._running = False

    def run(self):
        logger.info(f"Starting Runova Print Agent (device: {self.device_id[:8]}...)")
        logger.info(f"Server: {self.server_url}")

        self.shop_id = self._setup_shop()
        if not self.shop_id:
            logger.error("Failed to setup shop. Exiting.")
            return

        self._running = True
        self.ws_client = WebSocketClient(
            self.server_url, self.device_id, self._on_ws_message
        )

        ws_thread = threading.Thread(target=lambda: self._run_ws(), daemon=True)
        ws_thread.start()

        poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        poll_thread.start()

        logger.info("Agent is running. Press Ctrl+C to stop.")
        try:
            while self._running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            self._running = False
            if self.ws_client:
                self.ws_client.disconnect()

    def _run_ws(self):
        import asyncio
        asyncio.run(self.ws_client.connect())

    def _setup_shop(self) -> str | None:
        try:
            resp = requests.get(f"{self.server_url}/api/v1/shop/{self.device_id}")
            if resp.status_code == 200:
                shop = resp.json()
                logger.info(f"Found existing shop: {shop['shop_name']}")
                return shop["shop_id"]

            resp = requests.post(
                f"{self.server_url}/api/v1/shop",
                json={"shop_name": f"Shop {self.device_id[:8]}", "device_id": self.device_id},
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
            logger.info(f"New job received: {job_id}")
            self._process_job(job_id)

        elif msg_type == "job_updated":
            logger.info(f"Job updated: {data.get('job_id')}")

    def _process_job(self, job_id: str):
        try:
            resp = requests.get(f"{self.server_url}/api/v1/jobs/{job_id}")
            if resp.status_code != 200:
                return

            job = resp.json()
            for doc in job.get("documents", []):
                if doc["status"] == "READY":
                    self._handle_ready_document(job_id, doc)
        except Exception as e:
            logger.error(f"Job processing error: {e}")

    def _handle_ready_document(self, job_id: str, doc: dict):
        doc_id = doc["document_id"]
        doc_type = doc.get("document_type", "unknown")

        import tempfile
        temp_dir = tempfile.mkdtemp()

        pdf_path = download_pdf(self.server_url, doc_id, temp_dir)
        if not pdf_path:
            logger.error(f"Failed to download PDF for {doc_id}")
            return

        logger.info(f"Document ready: {doc_type} ({doc_id[:8]}...)")

        self.preview.show(
            document_id=doc_id,
            document_type=doc_type,
            pdf_path=pdf_path,
            on_confirm=self._on_confirm,
            on_reject=self._on_reject,
        )

    def _on_confirm(self, document_id: str, pdf_path: str):
        logger.info(f"Printing document {document_id[:8]}...")

        success = print_pdf(pdf_path)
        if success:
            import asyncio
            asyncio.run(self.ws_client.send({
                "type": "print_complete",
                "document_id": document_id,
            }))
            logger.info("Print complete")
        else:
            import asyncio
            asyncio.run(self.ws_client.send({
                "type": "print_failed",
                "document_id": document_id,
                "error": "Print failed",
            }))

    def _on_reject(self, document_id: str):
        logger.info(f"Document {document_id[:8]} rejected")
        try:
            requests.patch(
                f"{self.server_url}/api/v1/jobs/0/documents/{document_id}/reject"
            )
        except Exception:
            pass

    def _poll_loop(self):
        import time
        while self._running:
            try:
                resp = requests.get(
                    f"{self.server_url}/api/v1/shop/{self.shop_id}/pending"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for job in data.get("jobs", []):
                        if job["status"] in ("READY", "PREVIEW"):
                            for doc in job.get("documents", []):
                                if doc["status"] == "READY":
                                    self._handle_ready_document(job["job_id"], doc)
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Runova Print Agent")
    parser.add_argument("--server", default=SERVER_URL, help="Server URL")
    parser.add_argument("--device-id", default=None, help="Device ID")
    args = parser.parse_args()

    if args.server:
        SERVER_URL = args.server
    if args.device_id:
        DEVICE_ID = args.device_id

    agent = RunovaAgent()
    agent.run()
