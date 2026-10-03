"""launcher.py — Click-to-run GUI for the AI Business Agent.

Double-click launcher.bat to open this window.
"""
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext

# Force project root as working directory
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Business Agent — Launcher")
        self.geometry("950x650")
        self.minsize(750, 500)

        self.proc = None
        self._stop_flag = False
        self._running = False
        self.msg_queue = queue.Queue()

        self._build_ui()
        self.after(100, self._process_queue)

        self.append(f"Project: {PROJECT_ROOT}\n")
        self.append(f"Python:  {sys.executable}\n\n")

        # API key expiry check
        try:
            from config import settings
            from datetime import datetime, date
            self.append(f"Image provider: {settings.IMAGE_PROVIDER}\n")
            self.append(f"Text provider:  {settings.TEXT_PROVIDER}\n")

            if settings.NVIDIA_KEY_EXPIRY:
                expiry = datetime.strptime(settings.NVIDIA_KEY_EXPIRY, "%Y-%m-%d").date()
                days_left = (expiry - date.today()).days
                if days_left < 0:
                    self.append(f"❌ NVIDIA key EXPIRED {(-days_left)} days ago "
                                f"({expiry}). Get a new one!\n")
                elif days_left <= 30:
                    self.append(f"⚠ NVIDIA key expires in {days_left} days "
                                f"({expiry}). Renew soon.\n")
                else:
                    self.append(f"✓ NVIDIA key valid for {days_left} days "
                                f"(until {expiry}).\n")
            else:
                self.append("⚠ NVIDIA_KEY_EXPIRY not set in .env\n")
        except Exception as e:
            self.append(f"⚠ Could not read settings: {e}\n")

        self.append("\nClick 'RUN ALL REMAINING' to start.\n")
        self.append("Finished ideas are skipped automatically.\n\n")

        self.after(500, self.check_status)

    def _build_ui(self):
        top = tk.Frame(self, bg="#1e1e1e")
        top.pack(fill=tk.X)

        self.run_btn = tk.Button(
            top, text="▶  RUN ALL REMAINING",
            bg="#2e7d32", fg="white",
            activebackground="#1b5e20", activeforeground="white",
            font=("Segoe UI", 11, "bold"),
            padx=14, pady=8,
            command=self.run_all,
        )
        self.run_btn.pack(side=tk.LEFT, padx=6, pady=6)

        self.stop_btn = tk.Button(
            top, text="■  STOP",
            bg="#c62828", fg="white",
            activebackground="#8e0000", activeforeground="white",
            font=("Segoe UI", 11, "bold"),
            padx=14, pady=8,
            state=tk.DISABLED,
            command=self.stop,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=6, pady=6)

        tk.Button(top, text="Check status",
                  font=("Segoe UI", 10), padx=10, pady=8,
                  command=self.check_status).pack(side=tk.LEFT, padx=6, pady=6)

        tk.Button(top, text="Open output folder",
                  font=("Segoe UI", 10), padx=10, pady=8,
                  command=self.open_folder).pack(side=tk.LEFT, padx=6, pady=6)

        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(self, textvariable=self.status_var, anchor="w",
                 bg="#f0f0f0", padx=10, pady=4).pack(fill=tk.X, side=tk.BOTTOM)

        self.log = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, font=("Consolas", 9),
            bg="#111111", fg="#dcdcdc", insertbackground="white",
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.log.configure(state=tk.DISABLED)

    # --- thread-safe logging ---

    def append(self, text):
        self.msg_queue.put(("log", text))

    def _process_queue(self):
        try:
            while True:
                kind, data = self.msg_queue.get_nowait()
                if kind == "log":
                    self.log.configure(state=tk.NORMAL)
                    self.log.insert(tk.END, data)
                    self.log.see(tk.END)
                    self.log.configure(state=tk.DISABLED)
                elif kind == "status":
                    self.status_var.set(data)
                elif kind == "done":
                    self._running = False
                    self.run_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)

    # --- actions ---

    def check_status(self):
        threading.Thread(target=self._check_status_thread, daemon=True).start()

    def _check_status_thread(self):
        try:
            from app.utils.storage import load_json
            ideas_dir = PROJECT_ROOT / "data" / "processed"
            files = sorted(ideas_dir.glob("ideas_*.json"))
            total = done = 0
            for f in files:
                for i in load_json(f).get("ideas", []):
                    total += 1
                    if i.get("image_stock_path"):
                        done += 1
            remaining = total - done
            eta = remaining * 8
            self.append(f"\n[status] Total: {total} | Done: {done} | "
                        f"Remaining: {remaining} | ETA: ~{eta} min\n\n")
            self.msg_queue.put(("status",
                f"{done}/{total} done | {remaining} remaining (~{eta} min)"))
        except Exception as e:
            self.append(f"[status] Error: {e}\n")

    def open_folder(self):
        folder = PROJECT_ROOT / "data" / "ready_to_upload" / "stock"
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))

    def run_all(self):
        if self._running:
            messagebox.showinfo("Busy", "A batch is already running.")
            return
        ok = messagebox.askyesno(
            "Start batch?",
            "This will process ALL remaining ideas.\n\n"
            "It may take 1-3 hours.\n\n"
            "Make sure:\n"
            "  - ComfyUI is running in the Ubuntu window\n"
            "  - Laptop is plugged in\n\n"
            "Start?"
        )
        if not ok:
            return

        self._running = True
        self._stop_flag = False
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.msg_queue.put(("status", "Batch running..."))
        threading.Thread(target=self._batch_loop, daemon=True).start()

    def _batch_loop(self):
        try:
            ideas_dir = PROJECT_ROOT / "data" / "processed"
            files = sorted(ideas_dir.glob("ideas_*.json"))
            n = len(files)

            if n == 0:
                self.append("No ideas files found.\n")
                return

            self.append(f"\n{'=' * 68}\n  BATCH START — {n} file(s)\n{'=' * 68}\n")

            for idx, f in enumerate(files, 1):
                if self._stop_flag:
                    self.append("\n[stopped by user]\n")
                    break

                self.append(f"\n{'-' * 68}\n  FILE {idx}/{n}: {f.name}\n{'-' * 68}\n")
                self.msg_queue.put(("status", f"File {idx}/{n}: {f.name}"))

                self.proc = subprocess.Popen(
                    [sys.executable, "-m", "app.main", "run", str(f), "--all"],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, cwd=str(PROJECT_ROOT),
                )

                for line in self.proc.stdout:
                    self.append(line)
                    if self._stop_flag:
                        self.proc.terminate()
                        break

                self.proc.wait()
                self.proc = None

            self.append(f"\n{'=' * 68}\n  BATCH COMPLETE\n{'=' * 68}\n")
        except Exception as e:
            self.append(f"\n[ERROR] {e}\n")
        finally:
            self.msg_queue.put(("done", None))
            self.msg_queue.put(("status", "Ready."))

    def stop(self):
        if not self._running:
            return
        self._stop_flag = True
        self.append("\n[stop requested]\n")
        self.msg_queue.put(("status", "Stopping..."))


if __name__ == "__main__":
    try:
        Launcher().mainloop()
    except Exception as e:
        from tkinter import messagebox as mb
        mb.showerror("Launcher failed", str(e))