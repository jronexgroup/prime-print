import logging
import tkinter as tk

logger = logging.getLogger("agent")


def show_popup(doc_id, doc_type, pdf_path, on_confirm, on_reject):
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

    confirm_btn = tk.Button(btn_frame, text="PRINT", bg="#34a853", fg="white",
                            font=("Arial", 12, "bold"), padx=30, pady=10,
                            command=lambda: [on_confirm(), root.destroy()])
    confirm_btn.pack(side="left", padx=(10, 5), expand=True, fill="x")

    reject_btn = tk.Button(btn_frame, text="REJECT", bg="#ea4335", fg="white",
                           font=("Arial", 12, "bold"), padx=30, pady=10,
                           command=lambda: [on_reject(), root.destroy()])
    reject_btn.pack(side="right", padx=(5, 10), expand=True, fill="x")

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
