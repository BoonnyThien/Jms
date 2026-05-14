"""
Multi-Project Automation Hub
─────────────────────────────
customtkinter · pyautogui · pynput · threading
Multiple projects, each with its own FAB and click sequence.
Auto-saves to projects.json.
"""

import json, os, threading, time, tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import pyautogui
from pynput import mouse as pmouse

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects.json")
DEFAULT_DELAY = 500

# ─── Colors ───────────────────────────────────────────────
BG      = "#0c0c14"
BG2     = "#12121e"
SURF    = "#1a1a2e"
SURF2   = "#22223a"
BRD     = "#2a2a3e"
TXT     = "#e2e2f0"
DIM     = "#6b6b80"
ACC     = "#6366f1"
ACC2    = "#4f46e5"
GREEN   = "#10b981"
GREEN2  = "#059669"
RED     = "#f43f5e"
RED2    = "#e11d48"
AMBER   = "#f59e0b"
AMBER2  = "#d97706"

# ─── Data helpers ─────────────────────────────────────────
def load_data() -> list[dict]:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_data(projects: list[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)

def new_id():
    import random, string
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


# ═══════════════════════════════════════════════════════════
#  FAB — Floating Action Button (one per project)
# ═══════════════════════════════════════════════════════════
class ProjectFAB(ctk.CTkToplevel):
    def __init__(self, master, project: dict, on_pos_changed=None):
        super().__init__(master)
        self.project = project
        self.on_pos_changed = on_pos_changed
        self._stop = threading.Event()
        self._playing = False
        self._dx = self._dy = 0

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=BG)

        fx = project.get("fab_x", 100)
        fy = project.get("fab_y", 100)
        self.geometry(f"180x44+{fx}+{fy}")

        self._build()
        self.protocol("WM_DELETE_WINDOW", self.close_fab)

    def _build(self):
        f = ctk.CTkFrame(self, fg_color=SURF, corner_radius=10,
                         border_width=1, border_color=BRD)
        f.pack(fill="both", expand=True, padx=1, pady=1)

        # Drag handle
        drag = ctk.CTkLabel(f, text="⠿", width=18, font=("Segoe UI", 13),
                            text_color=DIM, cursor="fleur")
        drag.pack(side="left", padx=(5, 2))
        drag.bind("<Button-1>", self._drag_start)
        drag.bind("<B1-Motion>", self._drag_move)

        # Name label
        name = self.project.get("name", "?")[:10]
        ctk.CTkLabel(f, text=name, font=("Segoe UI", 10, "bold"),
                     text_color=TXT, width=60).pack(side="left", padx=2)

        # Play button
        self.btn = ctk.CTkButton(f, text="▶", width=36, height=30,
                                  font=("Segoe UI", 13, "bold"),
                                  fg_color=GREEN, hover_color=GREEN2,
                                  command=self._toggle)
        self.btn.pack(side="left", padx=2)

        # Close
        ctk.CTkButton(f, text="✕", width=26, height=26,
                       font=("Segoe UI", 11), fg_color="transparent",
                       hover_color="#3a1525", text_color=DIM,
                       command=self.close_fab).pack(side="right", padx=(0, 4))

    def _drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag_move(self, e):
        x = self.winfo_x() + e.x - self._dx
        y = self.winfo_y() + e.y - self._dy
        self.geometry(f"+{x}+{y}")
        self.project["fab_x"] = x
        self.project["fab_y"] = y
        if self.on_pos_changed:
            self.on_pos_changed()

    def _toggle(self):
        if self._playing:
            self._stop.set()
        else:
            self._play()

    def _play(self):
        steps = self.project.get("steps", [])
        if not steps:
            return
        self._playing = True
        self._stop.clear()
        self.btn.configure(text="⏹", fg_color=AMBER, hover_color=AMBER2)
        threading.Thread(target=self._exec, daemon=True).start()

    def _exec(self):
        for s in self.project.get("steps", []):
            if self._stop.is_set():
                break
            pyautogui.click(x=s["x"], y=s["y"])
            if self._stop.wait(timeout=s.get("delay", DEFAULT_DELAY) / 1000.0):
                break
        self.after(0, self._done)

    def _done(self):
        self._playing = False
        self.btn.configure(text="▶", fg_color=GREEN, hover_color=GREEN2)

    def close_fab(self):
        if self._playing:
            self._stop.set()
        self.destroy()


# ═══════════════════════════════════════════════════════════
#  STEP EDITOR — edits one project's steps
# ═══════════════════════════════════════════════════════════
class StepEditor(ctk.CTkToplevel):
    def __init__(self, master, project: dict, on_save=None):
        super().__init__(master)
        self.project = project
        self.on_save = on_save
        self._listener = None
        self.rows: list[dict] = []  # {frame, ex, ey, ed}

        self.title(f"📝 Chỉnh sửa: {project.get('name', '?')}")
        self.geometry("480x500")
        self.configure(fg_color=BG)
        self.attributes("-topmost", True)

        self._build()
        self._load_steps()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=SURF, corner_radius=0, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"📝 {self.project.get('name', '')}",
                     font=("Segoe UI", 14, "bold"), text_color=TXT
                     ).pack(side="left", padx=12)

        # Controls
        ctrl = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        ctrl.pack(fill="x", padx=10, pady=(8, 4))

        self.btn_rec = ctk.CTkButton(ctrl, text="🎯 Ghi", width=80, height=32,
                                      font=("Segoe UI", 11, "bold"),
                                      fg_color=RED, hover_color=RED2,
                                      command=self._toggle_rec)
        self.btn_rec.pack(side="left", padx=(0, 4))

        ctk.CTkButton(ctrl, text="＋ Thêm", width=70, height=32,
                       font=("Segoe UI", 11), fg_color=SURF, hover_color=BRD,
                       text_color=TXT, command=lambda: self._add_row(0, 0, DEFAULT_DELAY)
                       ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(ctrl, text="🗑 Xóa hết", width=80, height=32,
                       font=("Segoe UI", 11), fg_color=SURF, hover_color="#3a1525",
                       text_color=RED, command=self._clear
                       ).pack(side="left")

        ctk.CTkButton(ctrl, text="💾 Lưu", width=70, height=32,
                       font=("Segoe UI", 11, "bold"), fg_color=ACC, hover_color=ACC2,
                       command=self._save
                       ).pack(side="right")

        # Table header
        th = ctk.CTkFrame(self, fg_color=SURF2, corner_radius=4, height=28)
        th.pack(fill="x", padx=10, pady=(4, 0))
        th.pack_propagate(False)
        for txt, w in [("#", 34), ("X", 80), ("Y", 80), ("Delay ms", 90), ("", 28)]:
            ctk.CTkLabel(th, text=txt, width=w, font=("Segoe UI", 9, "bold"),
                         text_color=DIM).pack(side="left", padx=2)

        # Scrollable list
        self.sframe = ctk.CTkScrollableFrame(self, fg_color=BG2, corner_radius=4,
                                              scrollbar_button_color=BRD)
        self.sframe.pack(fill="both", expand=True, padx=10, pady=(2, 8))

        # Status
        self.lbl_st = ctk.CTkLabel(self, text="", font=("Segoe UI", 10), text_color=DIM)
        self.lbl_st.pack(pady=(0, 6))

    def _load_steps(self):
        for s in self.project.get("steps", []):
            self._add_row(s["x"], s["y"], s.get("delay", DEFAULT_DELAY))

    def _add_row(self, x, y, delay):
        idx = len(self.rows) + 1
        f = ctk.CTkFrame(self.sframe, fg_color="transparent", height=34)
        f.pack(fill="x", pady=1)

        lbl = ctk.CTkLabel(f, text=str(idx), width=34, font=("Consolas", 11), text_color=DIM)
        lbl.pack(side="left", padx=2)

        ex = ctk.CTkEntry(f, width=80, font=("Consolas", 11), justify="center",
                           fg_color=BG, border_color=BRD, text_color=TXT)
        ex.pack(side="left", padx=2); ex.insert(0, str(x))

        ey = ctk.CTkEntry(f, width=80, font=("Consolas", 11), justify="center",
                           fg_color=BG, border_color=BRD, text_color=TXT)
        ey.pack(side="left", padx=2); ey.insert(0, str(y))

        ed = ctk.CTkEntry(f, width=90, font=("Consolas", 11), justify="center",
                           fg_color=BG, border_color=BRD, text_color=TXT)
        ed.pack(side="left", padx=2); ed.insert(0, str(delay))

        row_data = {"frame": f, "lbl": lbl, "ex": ex, "ey": ey, "ed": ed}

        ctk.CTkButton(f, text="✕", width=28, height=26, font=("Segoe UI", 10),
                       fg_color="transparent", hover_color="#3a1525", text_color=DIM,
                       command=lambda r=row_data: self._del_row(r)
                       ).pack(side="left", padx=2)

        # Move up button
        ctk.CTkButton(f, text="▲", width=24, height=26, font=("Segoe UI", 9),
                       fg_color="transparent", hover_color=BRD, text_color=DIM,
                       command=lambda r=row_data: self._move_up(r)
                       ).pack(side="left", padx=1)

        self.rows.append(row_data)
        self._reindex()

    def _del_row(self, row):
        if row in self.rows:
            self.rows.remove(row)
            row["frame"].destroy()
            self._reindex()

    def _clear(self):
        for r in self.rows:
            r["frame"].destroy()
        self.rows.clear()

    def _move_up(self, row):
        idx = self.rows.index(row)
        if idx <= 0:
            return
        self.rows[idx], self.rows[idx - 1] = self.rows[idx - 1], self.rows[idx]
        # Re-pack in new order
        for r in self.rows:
            r["frame"].pack_forget()
        for r in self.rows:
            r["frame"].pack(fill="x", pady=1)
        self._reindex()

    def _reindex(self):
        for i, r in enumerate(self.rows):
            r["lbl"].configure(text=str(i + 1))

    def _get_steps(self):
        result = []
        for r in self.rows:
            try: x = int(r["ex"].get())
            except: x = 0
            try: y = int(r["ey"].get())
            except: y = 0
            try: d = max(int(r["ed"].get()), 10)
            except: d = DEFAULT_DELAY
            result.append({"x": x, "y": y, "delay": d})
        return result

    def _save(self):
        self.project["steps"] = self._get_steps()
        if self.on_save:
            self.on_save()
        self.lbl_st.configure(text=f"💾 Đã lưu {len(self.rows)} bước", text_color=GREEN)

    # ─── Record ──────────────────────────────────────────
    def _toggle_rec(self):
        if self._listener:
            self._stop_rec()
        else:
            self._start_rec()

    def _start_rec(self):
        self.btn_rec.configure(text="⏹ Dừng", fg_color="#9f1239")
        self.lbl_st.configure(text="🔴 Click vào bất kỳ đâu...", text_color=RED)
        self.iconify()

        def on_click(x, y, btn, pressed):
            if pressed and btn == pmouse.Button.left:
                self.after(0, lambda: self._add_row(int(x), int(y), DEFAULT_DELAY))
                self.after(100, self._stop_rec)
                self.after(150, self.deiconify)
                return False

        self._listener = pmouse.Listener(on_click=on_click)
        self._listener.start()

    def _stop_rec(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
        self.btn_rec.configure(text="🎯 Ghi", fg_color=RED)
        self.lbl_st.configure(text="Sẵn sàng", text_color=DIM)

    def _close(self):
        self._stop_rec()
        self.destroy()


# ═══════════════════════════════════════════════════════════
#  MAIN DASHBOARD — Project Manager
# ═══════════════════════════════════════════════════════════
class Dashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"⚡ Auto-Clicker Hub")
        self.geometry("560x520")
        self.minsize(480, 400)
        self.configure(fg_color=BG)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.projects: list[dict] = load_data()
        self.fabs: dict[str, ProjectFAB] = {}
        self.project_cards: list = []

        self._build()
        self._render_list()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=SURF, corner_radius=0, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="⚡ Auto-Clicker Hub",
                     font=("Segoe UI", 17, "bold"), text_color=TXT
                     ).pack(side="left", padx=16)
        ctk.CTkLabel(hdr, text="Multi-Project", font=("Segoe UI", 10),
                     text_color=DIM).pack(side="left", padx=4)

        self.lbl_count = ctk.CTkLabel(hdr, text="", font=("Consolas", 11),
                                       text_color=DIM)
        self.lbl_count.pack(side="right", padx=16)

        # Add project button
        bar = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        bar.pack(fill="x", padx=14, pady=(10, 6))

        ctk.CTkButton(bar, text="＋ Tạo Project Mới", width=160, height=36,
                       font=("Segoe UI", 13, "bold"),
                       fg_color=ACC, hover_color=ACC2,
                       command=self._add_project).pack(side="left")

        ctk.CTkButton(bar, text="📂 Import JSON", width=120, height=36,
                       font=("Segoe UI", 12), fg_color=SURF, hover_color=BRD,
                       text_color=TXT, command=self._import_json).pack(side="right")

        # Project list (scrollable)
        self.sframe = ctk.CTkScrollableFrame(self, fg_color=BG2, corner_radius=8,
                                              scrollbar_button_color=BRD)
        self.sframe.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    # ─── Render project cards ─────────────────────────────
    def _render_list(self):
        for w in self.sframe.winfo_children():
            w.destroy()
        self.project_cards.clear()

        if not self.projects:
            ctk.CTkLabel(self.sframe, text="Chưa có project nào.\nNhấn ＋ để tạo mới.",
                         font=("Segoe UI", 12), text_color=DIM
                         ).pack(pady=40)
            self._update_count()
            return

        for p in self.projects:
            self._make_card(p)
        self._update_count()

    def _make_card(self, p: dict):
        card = ctk.CTkFrame(self.sframe, fg_color=SURF, corner_radius=10,
                            border_width=1, border_color=BRD, height=64)
        card.pack(fill="x", padx=4, pady=3)
        card.pack_propagate(False)

        # Left: name + step count
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(12, 4))

        # Editable name
        name_entry = ctk.CTkEntry(left, width=160, height=28, font=("Segoe UI", 12, "bold"),
                                   fg_color="transparent", border_width=0, text_color=TXT)
        name_entry.pack(anchor="w", pady=(8, 0))
        name_entry.insert(0, p.get("name", "Untitled"))
        name_entry.bind("<FocusOut>", lambda e, proj=p, ent=name_entry: self._rename(proj, ent))
        name_entry.bind("<Return>", lambda e, proj=p, ent=name_entry: self._rename(proj, ent))

        steps_n = len(p.get("steps", []))
        ctk.CTkLabel(left, text=f"{steps_n} bước · ID: {p['id'][:6]}",
                     font=("Consolas", 9), text_color=DIM).pack(anchor="w")

        # Right: action buttons
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=(4, 8))

        pid = p["id"]
        fab_active = pid in self.fabs and self.fabs[pid].winfo_exists()

        ctk.CTkButton(right, text="📝", width=34, height=32, font=("Segoe UI", 13),
                       fg_color=SURF2, hover_color=BRD, text_color=TXT,
                       command=lambda proj=p: self._edit(proj)
                       ).pack(side="left", padx=2)

        fab_text = "🟢" if fab_active else "🚀"
        fab_btn = ctk.CTkButton(right, text=fab_text, width=34, height=32,
                                 font=("Segoe UI", 13),
                                 fg_color=GREEN if fab_active else SURF2,
                                 hover_color=GREEN2 if fab_active else BRD,
                                 command=lambda proj=p: self._toggle_fab(proj))
        fab_btn.pack(side="left", padx=2)

        ctk.CTkButton(right, text="🗑", width=34, height=32, font=("Segoe UI", 13),
                       fg_color=SURF2, hover_color="#3a1525", text_color=RED,
                       command=lambda proj=p: self._delete(proj)
                       ).pack(side="left", padx=2)

        self.project_cards.append(card)

    def _update_count(self):
        n = len(self.projects)
        active = sum(1 for pid, fab in self.fabs.items() if fab.winfo_exists())
        self.lbl_count.configure(text=f"{n} projects · {active} FABs")

    # ─── Actions ──────────────────────────────────────────
    def _add_project(self):
        p = {"id": new_id(), "name": f"Project {len(self.projects) + 1}",
             "steps": [], "fab_x": 100, "fab_y": 100}
        self.projects.append(p)
        self._persist()
        self._render_list()

    def _rename(self, proj, entry):
        new_name = entry.get().strip()
        if new_name:
            proj["name"] = new_name
            self._persist()

    def _edit(self, proj):
        StepEditor(self, proj, on_save=lambda: (self._persist(), self._render_list()))

    def _delete(self, proj):
        if not messagebox.askyesno("Xác nhận", f"Xóa '{proj['name']}'?"):
            return
        pid = proj["id"]
        if pid in self.fabs and self.fabs[pid].winfo_exists():
            self.fabs[pid].close_fab()
            del self.fabs[pid]
        self.projects = [p for p in self.projects if p["id"] != pid]
        self._persist()
        self._render_list()

    def _toggle_fab(self, proj):
        pid = proj["id"]
        if pid in self.fabs and self.fabs[pid].winfo_exists():
            self.fabs[pid].close_fab()
            del self.fabs[pid]
        else:
            if not proj.get("steps"):
                messagebox.showinfo("Thông báo", "Project chưa có bước nào.\nHãy thêm bước trước.")
                return
            fab = ProjectFAB(self, proj, on_pos_changed=self._persist)
            self.fabs[pid] = fab
        self._render_list()

    def _import_json(self):
        from tkinter import filedialog
        fp = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))
            return

        # Support both formats: list of steps or list of projects
        if isinstance(data, list) and data and "x" in data[0]:
            p = {"id": new_id(), "name": os.path.basename(fp).replace(".json", ""),
                 "steps": data, "fab_x": 100, "fab_y": 100}
            self.projects.append(p)
        elif isinstance(data, list) and data and "id" in data[0]:
            self.projects.extend(data)
        self._persist()
        self._render_list()

    # ─── Persistence ──────────────────────────────────────
    def _persist(self):
        save_data(self.projects)

    def _on_close(self):
        for fab in self.fabs.values():
            if fab.winfo_exists():
                fab.close_fab()
        self._persist()
        self.destroy()


# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()
