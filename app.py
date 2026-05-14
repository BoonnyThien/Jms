"""
Coordinate Auto-Clicker — Native Python Desktop App
────────────────────────────────────────────────────
Tech: customtkinter · pyautogui · pynput · threading
Two UI modes: Main Dashboard (setup) ↔ Mini Widget (execute)
"""

import json
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pyautogui

from pynput import mouse as pynput_mouse

# ─── Globals ──────────────────────────────────────────────
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
pyautogui.PAUSE = 0.02

APP_TITLE = "Auto-Clicker"
DEFAULT_DELAY = 500  # ms
CONFIG_FILE = "config.json"

# ─── Colors ───────────────────────────────────────────────
C_BG = "#0d0d14"
C_BG2 = "#13131f"
C_SURFACE = "#1a1a2e"
C_BORDER = "#2a2a3e"
C_TEXT = "#e2e2f0"
C_TEXT_DIM = "#6b6b80"
C_ACCENT = "#6366f1"
C_REC = "#f43f5e"
C_PLAY = "#10b981"
C_WARN = "#f59e0b"
C_DEL = "#ef4444"


# ═══════════════════════════════════════════════════════════
#  STEP ROW WIDGET
# ═══════════════════════════════════════════════════════════
class StepRow(ctk.CTkFrame):
    """One row in the macro table: # | X | Y | Delay | [Delete]"""

    def __init__(self, master, index: int, x: int = 0, y: int = 0,
                 delay: int = DEFAULT_DELAY, on_delete=None):
        super().__init__(master, fg_color="transparent", height=36)
        self.on_delete = on_delete
        self.pack(fill="x", padx=4, pady=1)

        # Step Number
        self.lbl_num = ctk.CTkLabel(self, text=str(index), width=36,
                                     font=("Consolas", 12), text_color=C_TEXT_DIM)
        self.lbl_num.pack(side="left", padx=(4, 2))

        # X
        self.entry_x = ctk.CTkEntry(self, width=72, font=("Consolas", 12),
                                     placeholder_text="X", justify="center",
                                     fg_color=C_BG2, border_color=C_BORDER,
                                     text_color=C_TEXT)
        self.entry_x.pack(side="left", padx=2)
        self.entry_x.insert(0, str(x))

        # Y
        self.entry_y = ctk.CTkEntry(self, width=72, font=("Consolas", 12),
                                     placeholder_text="Y", justify="center",
                                     fg_color=C_BG2, border_color=C_BORDER,
                                     text_color=C_TEXT)
        self.entry_y.pack(side="left", padx=2)
        self.entry_y.insert(0, str(y))

        # Delay
        self.entry_delay = ctk.CTkEntry(self, width=80, font=("Consolas", 12),
                                         placeholder_text="ms", justify="center",
                                         fg_color=C_BG2, border_color=C_BORDER,
                                         text_color=C_TEXT)
        self.entry_delay.pack(side="left", padx=2)
        self.entry_delay.insert(0, str(delay))

        # Delete button
        self.btn_del = ctk.CTkButton(self, text="✕", width=30, height=28,
                                      font=("Segoe UI", 12),
                                      fg_color="transparent", text_color=C_TEXT_DIM,
                                      hover_color="#3a1525",
                                      command=self._on_delete)
        self.btn_del.pack(side="left", padx=(4, 4))

    def _on_delete(self):
        if self.on_delete:
            self.on_delete(self)

    def set_index(self, idx: int):
        self.lbl_num.configure(text=str(idx))

    def get_data(self) -> dict:
        try:
            x = int(self.entry_x.get())
        except ValueError:
            x = 0
        try:
            y = int(self.entry_y.get())
        except ValueError:
            y = 0
        try:
            delay = int(self.entry_delay.get())
        except ValueError:
            delay = DEFAULT_DELAY
        return {"x": x, "y": y, "delay": max(delay, 10)}

    def highlight(self, active: bool):
        """Highlight row during playback."""
        if active:
            self.configure(fg_color="#0f2a1f")
        else:
            self.configure(fg_color="transparent")


# ═══════════════════════════════════════════════════════════
#  MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════
class MainDashboard(ctk.CTk):
    """The large setup/config window."""

    def __init__(self):
        super().__init__()
        self.title(f"⚡ {APP_TITLE} — Bảng Điều Khiển")
        self.geometry("520x620")
        self.minsize(460, 500)
        self.configure(fg_color=C_BG)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.step_rows: list[StepRow] = []
        self.is_recording = False
        self.is_playing = False
        self._listener = None
        self._play_thread = None
        self._stop_flag = threading.Event()
        self.mini_widget = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── Build UI ─────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color=C_SURFACE, corner_radius=0, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text=f"⚡ {APP_TITLE}",
                     font=("Segoe UI", 16, "bold"), text_color=C_TEXT
                     ).pack(side="left", padx=16)

        self.lbl_status = ctk.CTkLabel(header, text="Sẵn sàng",
                                        font=("Segoe UI", 11),
                                        text_color=C_TEXT_DIM)
        self.lbl_status.pack(side="right", padx=16)

        # ── Controls ──
        ctrl_frame = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        ctrl_frame.pack(fill="x", padx=12, pady=(10, 4))

        self.btn_record = ctk.CTkButton(
            ctrl_frame, text="🎯 Ghi Tọa Độ", width=120, height=34,
            font=("Segoe UI", 12, "bold"),
            fg_color=C_REC, hover_color="#e11d48",
            command=self._toggle_record)
        self.btn_record.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            ctrl_frame, text="＋ Thêm Bước", width=100, height=34,
            font=("Segoe UI", 12),
            fg_color=C_SURFACE, hover_color=C_BORDER, text_color=C_TEXT,
            command=lambda: self._add_step(0, 0, DEFAULT_DELAY)
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            ctrl_frame, text="🗑 Xóa Tất Cả", width=100, height=34,
            font=("Segoe UI", 12),
            fg_color=C_SURFACE, hover_color="#3a1525", text_color=C_DEL,
            command=self._clear_all
        ).pack(side="left")

        # ── Save / Load / Mini ──
        ctrl_frame2 = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        ctrl_frame2.pack(fill="x", padx=12, pady=(4, 8))

        ctk.CTkButton(
            ctrl_frame2, text="💾 Lưu", width=80, height=34,
            font=("Segoe UI", 12),
            fg_color=C_SURFACE, hover_color=C_BORDER, text_color=C_TEXT,
            command=self._save_config
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            ctrl_frame2, text="📂 Tải", width=80, height=34,
            font=("Segoe UI", 12),
            fg_color=C_SURFACE, hover_color=C_BORDER, text_color=C_TEXT,
            command=self._load_config
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            ctrl_frame2, text="🚀 Mini Widget", width=120, height=34,
            font=("Segoe UI", 12, "bold"),
            fg_color=C_ACCENT, hover_color="#4f46e5", text_color="#fff",
            command=self._show_mini_widget
        ).pack(side="right")

        # ── Table Header ──
        tbl_header = ctk.CTkFrame(self, fg_color=C_SURFACE, corner_radius=6, height=32)
        tbl_header.pack(fill="x", padx=12, pady=(4, 0))
        tbl_header.pack_propagate(False)

        cols = [("#", 36), ("X", 72), ("Y", 72), ("Delay (ms)", 80), ("", 30)]
        for text, w in cols:
            ctk.CTkLabel(tbl_header, text=text, width=w,
                         font=("Segoe UI", 10, "bold"),
                         text_color=C_TEXT_DIM
                         ).pack(side="left", padx=2 if text else 4)

        # ── Step List (Scrollable) ──
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=C_BG2, corner_radius=6,
            scrollbar_button_color=C_BORDER,
            scrollbar_button_hover_color=C_ACCENT)
        self.scroll_frame.pack(fill="both", expand=True, padx=12, pady=(2, 8))

        # ── Footer ──
        footer = ctk.CTkFrame(self, fg_color=C_SURFACE, corner_radius=0, height=32)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.lbl_count = ctk.CTkLabel(footer, text="0 bước",
                                       font=("Consolas", 11),
                                       text_color=C_TEXT_DIM)
        self.lbl_count.pack(side="left", padx=16)

        ctk.CTkLabel(footer, text="pyautogui • pynput",
                     font=("Consolas", 10), text_color="#3a3a4e"
                     ).pack(side="right", padx=16)

    # ─── Step Management ──────────────────────────────────
    def _add_step(self, x: int, y: int, delay: int):
        idx = len(self.step_rows) + 1
        row = StepRow(self.scroll_frame, index=idx, x=x, y=y, delay=delay,
                      on_delete=self._remove_step)
        self.step_rows.append(row)
        self._update_count()

    def _remove_step(self, row: StepRow):
        if row in self.step_rows:
            self.step_rows.remove(row)
            row.destroy()
            self._reindex()
            self._update_count()

    def _clear_all(self):
        for row in self.step_rows:
            row.destroy()
        self.step_rows.clear()
        self._update_count()

    def _reindex(self):
        for i, row in enumerate(self.step_rows):
            row.set_index(i + 1)

    def _update_count(self):
        self.lbl_count.configure(text=f"{len(self.step_rows)} bước")

    def _get_all_steps(self) -> list[dict]:
        return [row.get_data() for row in self.step_rows]

    # ─── Recording (pynput) ───────────────────────────────
    def _toggle_record(self):
        if self.is_recording:
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        self.is_recording = True
        self.btn_record.configure(text="⏹ Dừng Ghi", fg_color="#9f1239")
        self.lbl_status.configure(text="🔴 Đang ghi — Click vào bất kỳ đâu...",
                                   text_color=C_REC)

        # Minimize so user can click on target app
        self.iconify()

        def on_click(x, y, button, pressed):
            if pressed and button == pynput_mouse.Button.left:
                # Schedule UI update on the main thread
                self.after(0, lambda: self._add_step(int(x), int(y), DEFAULT_DELAY))
                # Stop after one click; user clicks Record again for more
                self.after(100, self._stop_record)
                self.after(150, self.deiconify)
                return False  # Stop listener

        self._listener = pynput_mouse.Listener(on_click=on_click)
        self._listener.start()

    def _stop_record(self):
        self.is_recording = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        self.btn_record.configure(text="🎯 Ghi Tọa Độ", fg_color=C_REC)
        self.lbl_status.configure(text="Sẵn sàng", text_color=C_TEXT_DIM)

    # ─── Save / Load ─────────────────────────────────────
    def _save_config(self):
        steps = self._get_all_steps()
        if not steps:
            messagebox.showwarning("Cảnh báo", "Chưa có bước nào để lưu.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Lưu Macro",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="config.json")
        if not filepath:
            return

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(steps, f, indent=2, ensure_ascii=False)

        self.lbl_status.configure(text=f"💾 Đã lưu: {os.path.basename(filepath)}",
                                   text_color=C_PLAY)

    def _load_config(self):
        filepath = filedialog.askopenfilename(
            title="Tải Macro",
            filetypes=[("JSON files", "*.json")])
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file:\n{e}")
            return

        if not isinstance(data, list):
            messagebox.showerror("Lỗi", "File JSON không đúng định dạng.")
            return

        self._clear_all()
        for step in data:
            self._add_step(
                step.get("x", 0),
                step.get("y", 0),
                step.get("delay", DEFAULT_DELAY))

        self.lbl_status.configure(
            text=f"📂 Đã tải {len(data)} bước từ {os.path.basename(filepath)}",
            text_color=C_ACCENT)

    # ─── Mini Widget ──────────────────────────────────────
    def _show_mini_widget(self):
        steps = self._get_all_steps()
        self.withdraw()  # Hide dashboard
        if self.mini_widget and self.mini_widget.winfo_exists():
            self.mini_widget.destroy()
        self.mini_widget = MiniWidget(self, steps)

    def show_dashboard(self):
        """Called by MiniWidget to return to dashboard."""
        if self.mini_widget and self.mini_widget.winfo_exists():
            self.mini_widget.destroy()
            self.mini_widget = None
        self.deiconify()

    def _on_close(self):
        if self._listener:
            self._listener.stop()
        self.destroy()


# ═══════════════════════════════════════════════════════════
#  MINI FLOATING WIDGET
# ═══════════════════════════════════════════════════════════
class MiniWidget(ctk.CTkToplevel):
    """Tiny always-on-top execution trigger."""

    def __init__(self, dashboard: MainDashboard, steps: list[dict]):
        super().__init__()
        self.dashboard = dashboard
        self.steps = steps
        self._stop_flag = threading.Event()
        self._play_thread = None
        self.is_playing = False

        # ── Window config ──
        self.title("")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=C_BG)
        self.geometry("220x52")

        # Position: top-right corner
        screen_w = self.winfo_screenwidth()
        self.geometry(f"+{screen_w - 240}+20")

        # ── Dragging ──
        self._drag_x = 0
        self._drag_y = 0

        # ── Build UI ──
        self._build_ui()

    def _build_ui(self):
        # Main frame with border
        frame = ctk.CTkFrame(self, fg_color=C_SURFACE, corner_radius=10,
                             border_width=1, border_color=C_BORDER)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Drag handle
        drag_bar = ctk.CTkLabel(frame, text="⠿", width=20,
                                 font=("Segoe UI", 14), text_color=C_TEXT_DIM,
                                 cursor="fleur")
        drag_bar.pack(side="left", padx=(6, 2))
        drag_bar.bind("<Button-1>", self._start_drag)
        drag_bar.bind("<B1-Motion>", self._do_drag)

        # Play button
        self.btn_play = ctk.CTkButton(
            frame, text="▶ Phát", width=70, height=32,
            font=("Segoe UI", 12, "bold"),
            fg_color=C_PLAY, hover_color="#059669",
            command=self._toggle_play)
        self.btn_play.pack(side="left", padx=4)

        # Step counter
        self.lbl_info = ctk.CTkLabel(
            frame, text=f"{len(self.steps)} bước",
            font=("Consolas", 10), text_color=C_TEXT_DIM, width=50)
        self.lbl_info.pack(side="left", padx=2)

        # Setup button
        ctk.CTkButton(
            frame, text="⚙", width=32, height=32,
            font=("Segoe UI", 14),
            fg_color="transparent", hover_color=C_BORDER, text_color=C_TEXT_DIM,
            command=self._back_to_dashboard
        ).pack(side="right", padx=(0, 6))

    # ─── Dragging ─────────────────────────────────────────
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    # ─── Playback ─────────────────────────────────────────
    def _toggle_play(self):
        if self.is_playing:
            self._stop_play()
        else:
            self._start_play()

    def _start_play(self):
        if not self.steps:
            return
        self.is_playing = True
        self._stop_flag.clear()
        self.btn_play.configure(text="⏹ Dừng", fg_color=C_WARN, hover_color="#d97706")
        self.lbl_info.configure(text="Đang phát...", text_color=C_WARN)

        self._play_thread = threading.Thread(target=self._execute, daemon=True)
        self._play_thread.start()

    def _stop_play(self):
        self._stop_flag.set()
        self.is_playing = False
        self.btn_play.configure(text="▶ Phát", fg_color=C_PLAY, hover_color="#059669")
        self.lbl_info.configure(text=f"{len(self.steps)} bước", text_color=C_TEXT_DIM)

    def _execute(self):
        """Runs in a background thread — uses pyautogui for OS-level clicks."""
        total = len(self.steps)
        for i, step in enumerate(self.steps):
            if self._stop_flag.is_set():
                break

            # Update counter on main thread
            self.after(0, lambda c=i+1, t=total:
                       self.lbl_info.configure(text=f"{c}/{t}", text_color=C_WARN))

            # Click at absolute screen coordinates
            pyautogui.click(x=step["x"], y=step["y"])

            # Custom exact delay
            delay_sec = step.get("delay", DEFAULT_DELAY) / 1000.0
            if self._stop_flag.wait(timeout=delay_sec):
                break  # Stopped during delay

        # Done — update UI on main thread
        self.after(0, self._stop_play)

    def _back_to_dashboard(self):
        if self.is_playing:
            self._stop_play()
        self.dashboard.show_dashboard()


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = MainDashboard()
    app.mainloop()
