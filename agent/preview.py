import logging
import threading
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

logger = logging.getLogger("runova_agent")


class PreviewWindow:
    def __init__(self):
        self.root = None
        self._lock = threading.Lock()

    def show(self, document_id: str, document_type: str, pdf_path: str, on_confirm, on_reject):
        with self._lock:
            if self.root and self.root.winfo_exists():
                return

            self.root = tk.Tk()
            self.root.title("Runova Print Agent")
            self.root.geometry("500x600")
            self.root.resizable(False, False)

            header = tk.Frame(self.root, bg="#1a73e8", height=60)
            header.pack(fill="x")
            header.pack_propagate(False)
            tk.Label(
                header, text="Runova Print", bg="#1a73e8", fg="white",
                font=("Segoe UI", 16, "bold")
            ).pack(expand=True)

            info_frame = tk.Frame(self.root, pady=20)
            info_frame.pack(fill="x", padx=20)

            tk.Label(
                info_frame, text="New Document Ready",
                font=("Segoe UI", 14, "bold")
            ).pack()

            tk.Label(
                info_frame, text=f"Type: {document_type.replace('_', ' ').title()}",
                font=("Segoe UI", 12), fg="#666"
            ).pack(pady=(8, 0))

            tk.Label(
                info_frame, text=f"ID: {document_id[:8]}...",
                font=("Segoe UI", 10), fg="#999"
            ).pack(pady=(4, 0))

            preview_frame = tk.Frame(self.root, bg="#f0f0f0", height=300)
            preview_frame.pack(fill="x", padx=20, pady=10)
            preview_frame.pack_propagate(False)

            tk.Label(
                preview_frame, text="[PDF Preview]\nOpen file to view",
                bg="#f0f0f0", fg="#999", font=("Segoe UI", 11)
            ).pack(expand=True)

            btn_frame = tk.Frame(self.root, pady=20)
            btn_frame.pack(fill="x")

            confirm_btn = tk.Button(
                btn_frame, text="CONFIRM & PRINT", bg="#34a853", fg="white",
                font=("Segoe UI", 12, "bold"), padx=30, pady=12,
                command=lambda: self._handle_confirm(on_confirm, document_id, pdf_path)
            )
            confirm_btn.pack(side="left", padx=(20, 10), expand=True, fill="x")

            reject_btn = tk.Button(
                btn_frame, text="REJECT", bg="#ea4335", fg="white",
                font=("Segoe UI", 12, "bold"), padx=30, pady=12,
                command=lambda: self._handle_reject(on_reject, document_id)
            )
            reject_btn.pack(side="right", padx=(10, 20), expand=True, fill="x")

            self.root.protocol("WM_DELETE_WINDOW", lambda: None)
            self.root.mainloop()

    def _handle_confirm(self, callback, document_id, pdf_path):
        callback(document_id, pdf_path)
        if self.root:
            self.root.destroy()
            self.root = None

    def _handle_reject(self, callback, document_id):
        callback(document_id)
        if self.root:
            self.root.destroy()
            self.root = None

    def close(self):
        with self._lock:
            if self.root:
                self.root.destroy()
                self.root = None
