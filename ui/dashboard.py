import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from pynput import mouse as pmouse

from core.config import load_and_migrate_data, save_data, new_id
from core.engine import MacroEngine
from ui.fab import ProjectFAB

BG = "#0c0c14"; BG2 = "#12121e"; SURF = "#1a1a2e"; SURF2 = "#22223a"
BRD = "#2a2a3e"; TXT = "#e2e2f0"; DIM = "#6b6b80"
ACC = "#6366f1"; ACC2 = "#4f46e5"
GRN = "#10b981"; GRN2 = "#059669"
RED = "#f43f5e"; RED2 = "#e11d48"

class SetupOverlay(ctk.CTkToplevel):
    def __init__(self, master, project, on_save):
        super().__init__(master)
        self.project = project
        self.on_save = on_save
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.6)
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(self.winfo_screenwidth()//2, 50, text="KÉO THẢ ĐIỂM ĐỂ CHỈNH TỌA ĐỘ. BẤM ESC ĐỂ LƯU & THOÁT.", fill="white", font=("Segoe UI", 20, "bold"))
        self.nodes = []
        for idx, step in enumerate(self.project.get("steps", [])):
            if step.get("action") == "pause_macro": continue
            x, y = step.get("x", 0), step.get("y", 0)
            r = 15
            item = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="#ff4d4d", outline="#ff1a1a", width=3, stipple="gray50")
            text = self.canvas.create_text(x, y, text=str(idx+1), fill="white", font=("Segoe UI", 12, "bold"))
            self.nodes.append({"item": item, "text": text, "index": idx})
        self.bind("<Escape>", self._close)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self._drag_data = {"item": None, "x": 0, "y": 0, "index": -1}

    def _on_press(self, event):
        item = self.canvas.find_withtag("current")
        if item:
            item_id = item[0]
            for node in self.nodes:
                if node["item"] == item_id or node["text"] == item_id:
                    self._drag_data.update({"item": node, "x": event.x, "y": event.y, "index": node["index"]})
                    break

    def _on_drag(self, event):
        if self._drag_data["item"]:
            dx, dy = event.x - self._drag_data["x"], event.y - self._drag_data["y"]
            self.canvas.move(self._drag_data["item"]["item"], dx, dy)
            self.canvas.move(self._drag_data["item"]["text"], dx, dy)
            self._drag_data.update({"x": event.x, "y": event.y})

    def _on_release(self, event):
        if self._drag_data["item"]:
            idx = self._drag_data["index"]
            coords = self.canvas.coords(self._drag_data["item"]["item"])
            self.project["steps"][idx]["x"] = int((coords[0] + coords[2]) / 2)
            self.project["steps"][idx]["y"] = int((coords[1] + coords[3]) / 2)
            if self.on_save: self.on_save()
            self._drag_data["item"] = None

    def _close(self, event=None):
        if self.on_save: self.on_save()
        self.destroy()

class StepEditor(ctk.CTkToplevel):
    def __init__(self, master, project: dict, on_save=None):
        super().__init__(master)
        self.project = project
        self.on_save = on_save
        self._listener = None
        self.rows = []
        self.title(f"📝 {project.get('name', 'Untitled')}")
        self.geometry("850x550")
        self.configure(fg_color=BG)
        self.attributes("-topmost", True)
        self._build()
        self._load_steps()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=SURF, corner_radius=0, height=42)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"📝 {self.project.get('name', '')}", font=("Segoe UI", 14, "bold"), text_color=TXT).pack(side="left", padx=12)

        p_set = ctk.CTkFrame(self, fg_color=BG2, corner_radius=4)
        p_set.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(p_set, text="FAB Color (HEX):", font=("Segoe UI", 11)).pack(side="left", padx=(10, 4))
        self.color_var = ctk.StringVar(value=self.project.get("fab_color", ACC))
        ctk.CTkEntry(p_set, width=80, height=24, textvariable=self.color_var).pack(side="left", padx=4)
        self.compact_var = ctk.BooleanVar(value=self.project.get("fab_is_compact", False))
        ctk.CTkCheckBox(p_set, text="Compact Mode (Mini Dot)", variable=self.compact_var, height=24).pack(side="left", padx=10)

        ctrl = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        ctrl.pack(fill="x", padx=10, pady=(4, 4))
        self.btn_rec = ctk.CTkButton(ctrl, text="🎯 Ghi Điểm", width=80, height=32, font=("Segoe UI", 11, "bold"), fg_color=RED, hover_color=RED2, command=self._toggle_rec)
        self.btn_rec.pack(side="left", padx=(0, 4))
        ctk.CTkButton(ctrl, text="🛠 Setup Tọa Độ", width=100, height=32, font=("Segoe UI", 11, "bold"), fg_color=ACC, hover_color=ACC2, command=self._open_setup).pack(side="left", padx=(0, 4))
        ctk.CTkButton(ctrl, text="＋ Thêm", width=70, height=32, font=("Segoe UI", 11), fg_color=SURF, hover_color=BRD, command=lambda: self._add_row({"name": "New Step", "action": "single_click", "x": 0, "y": 0, "delay_after": 500, "press_duration": 80})).pack(side="left", padx=(0, 4))
        ctk.CTkButton(ctrl, text="🗑 Xóa hết", width=80, height=32, font=("Segoe UI", 11), fg_color=SURF, text_color=RED, command=self._clear).pack(side="left")
        ctk.CTkButton(ctrl, text="💾 Lưu", width=70, height=32, font=("Segoe UI", 11, "bold"), fg_color=GRN, hover_color=GRN2, command=self._save).pack(side="right")

        th = ctk.CTkFrame(self, fg_color=SURF2, corner_radius=4, height=26)
        th.pack(fill="x", padx=10, pady=(4, 0)); th.pack_propagate(False)
        for t, w in [("#", 30), ("Step Name", 120), ("Action Type", 110), ("X", 60), ("Y", 60), ("Delay(ms)", 80), ("Hold(ms)", 80), ("", 60)]:
            ctk.CTkLabel(th, text=t, width=w, font=("Segoe UI", 9, "bold"), text_color=DIM).pack(side="left", padx=2)

        self.sframe = ctk.CTkScrollableFrame(self, fg_color=BG2, corner_radius=4)
        self.sframe.pack(fill="both", expand=True, padx=10, pady=(2, 6))
        self.lbl_st = ctk.CTkLabel(self, text="", font=("Segoe UI", 10), text_color=DIM)
        self.lbl_st.pack(pady=(0, 6))

    def _open_setup(self):
        if not self.rows: return messagebox.showinfo("Lỗi", "Chưa có điểm.")
        self._save_silently()
        SetupOverlay(self, self.project, lambda: (self.on_save and self.on_save(), self._clear(), self._load_steps()))

    def _load_steps(self):
        for s in self.project.get("steps", []): self._add_row(s)

    def _add_row(self, s_dict):
        idx = len(self.rows) + 1
        f = ctk.CTkFrame(self.sframe, fg_color="transparent", height=34)
        f.pack(fill="x", pady=1)

        lbl = ctk.CTkLabel(f, text=str(idx), width=30, font=("Consolas", 11), text_color=DIM)
        lbl.pack(side="left", padx=2)
        
        ename = ctk.CTkEntry(f, width=120, font=("Segoe UI", 11), fg_color=BG, border_color=BRD, text_color=TXT)
        ename.pack(side="left", padx=2); ename.insert(0, s_dict.get("name", f"Step {idx}"))
        
        act = ctk.StringVar(value=s_dict.get("action", "single_click"))
        ctk.CTkOptionMenu(f, values=["single_click", "double_click", "right_click", "pause_macro"], variable=act, width=110, height=24).pack(side="left", padx=2)
        
        ex = ctk.CTkEntry(f, width=60, font=("Consolas", 11), justify="center", fg_color=BG, border_color=BRD, text_color=TXT); ex.pack(side="left", padx=2); ex.insert(0, str(s_dict.get("x", 0)))
        ey = ctk.CTkEntry(f, width=60, font=("Consolas", 11), justify="center", fg_color=BG, border_color=BRD, text_color=TXT); ey.pack(side="left", padx=2); ey.insert(0, str(s_dict.get("y", 0)))
        ed = ctk.CTkEntry(f, width=80, font=("Consolas", 11), justify="center", fg_color=BG, border_color=BRD, text_color=TXT); ed.pack(side="left", padx=2); ed.insert(0, str(s_dict.get("delay_after", 500)))
        eh = ctk.CTkEntry(f, width=80, font=("Consolas", 11), justify="center", fg_color=BG, border_color=BRD, text_color=TXT); eh.pack(side="left", padx=2); eh.insert(0, str(s_dict.get("press_duration", 80)))

        rd = {"frame": f, "lbl": lbl, "ename": ename, "act": act, "ex": ex, "ey": ey, "ed": ed, "eh": eh}
        ctk.CTkButton(f, text="✕", width=26, height=26, font=("Segoe UI", 10), fg_color="transparent", text_color=DIM, hover_color="#3a1525", command=lambda r=rd: self._del(r)).pack(side="left", padx=1)
        ctk.CTkButton(f, text="▲", width=24, height=26, font=("Segoe UI", 9), fg_color="transparent", text_color=DIM, hover_color=BRD, command=lambda r=rd: self._mv(r, -1)).pack(side="left", padx=1)
        ctk.CTkButton(f, text="▼", width=24, height=26, font=("Segoe UI", 9), fg_color="transparent", text_color=DIM, hover_color=BRD, command=lambda r=rd: self._mv(r, 1)).pack(side="left", padx=1)
        
        self.rows.append(rd); self._reindex()

    def _del(self, r): self.rows.remove(r); r["frame"].destroy(); self._reindex()
    def _clear(self):
        for r in self.rows: r["frame"].destroy()
        self.rows.clear()
    def _mv(self, r, d):
        i = self.rows.index(r)
        if 0 <= i + d < len(self.rows):
            self.rows[i], self.rows[i+d] = self.rows[i+d], self.rows[i]
            for row in self.rows: row["frame"].pack_forget()
            for row in self.rows: row["frame"].pack(fill="x", pady=1)
            self._reindex()

    def _reindex(self):
        for i, r in enumerate(self.rows): r["lbl"].configure(text=str(i + 1))

    def _save_silently(self):
        self.project["fab_color"] = self.color_var.get()
        self.project["fab_is_compact"] = self.compact_var.get()
        out = []
        for i, r in enumerate(self.rows):
            try: x = int(r["ex"].get())
            except: x = 0
            try: y = int(r["ey"].get())
            except: y = 0
            try: d = max(int(r["ed"].get()), 0)
            except: d = 500
            try: h = max(int(r["eh"].get()), 10)
            except: h = 80
            out.append({"step_id": i+1, "name": r["ename"].get().strip() or f"Step {i+1}", "action": r["act"].get(), "x": x, "y": y, "delay_after": d, "press_duration": h})
        self.project["steps"] = out

    def _save(self):
        self._save_silently()
        if self.on_save: self.on_save()
        self.lbl_st.configure(text=f"💾 Đã lưu", text_color=GRN)

    def _toggle_rec(self):
        if self._listener: self._stop_rec()
        else: self._start_rec()

    def _start_rec(self):
        self.btn_rec.configure(text="⏹ Dừng", fg_color="#9f1239")
        self.iconify()
        def on_click(x, y, btn, pressed):
            if pressed and btn == pmouse.Button.left:
                self.after(0, lambda: self._add_row({"name": f"Step {len(self.rows)+1}", "action": "single_click", "x": int(x), "y": int(y), "delay_after": 500, "press_duration": 80}))
                self.after(100, self._stop_rec)
                self.after(150, self.deiconify)
                return False
        self._listener = pmouse.Listener(on_click=on_click)
        self._listener.start()

    def _stop_rec(self):
        if self._listener: self._listener.stop(); self._listener = None
        self.btn_rec.configure(text="🎯 Ghi Điểm", fg_color=RED)

    def _close(self):
        self._stop_rec(); self.destroy()


class Dashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⚡ JMS Automation Suite v1.0.2")
        self.geometry("700x600")
        self.minsize(500, 450)
        self.configure(fg_color=BG)
        ctk.set_appearance_mode("dark")
        self.projects = load_and_migrate_data()
        self.fabs = {}
        self.engines = {}
        self._build()
        self._render()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=SURF, corner_radius=0, height=50)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="⚡ JMS Automation Suite v1.0.2", font=("Segoe UI", 17, "bold"), text_color=TXT).pack(side="left", padx=16)
        self.lbl_count = ctk.CTkLabel(hdr, text="", font=("Consolas", 11), text_color=DIM)
        self.lbl_count.pack(side="right", padx=16)

        bar = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        bar.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkButton(bar, text="＋ Tạo Project Mới", width=160, height=36, font=("Segoe UI", 13, "bold"), fg_color=ACC, hover_color=ACC2, command=self._add).pack(side="left")

        self.sframe = ctk.CTkScrollableFrame(self, fg_color=BG2, corner_radius=8, scrollbar_button_color=BRD)
        self.sframe.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    def _render(self):
        for w in self.sframe.winfo_children(): w.destroy()
        if not self.projects:
            ctk.CTkLabel(self.sframe, text="Chưa có project.\nNhấn ＋ để tạo.", font=("Segoe UI", 12), text_color=DIM).pack(pady=40)
            self._update_count(); return
        for p in self.projects: self._card(p)
        self._update_count()

    def _card(self, p):
        card = ctk.CTkFrame(self.sframe, fg_color=SURF, corner_radius=10, border_width=1, border_color=BRD, height=64)
        card.pack(fill="x", padx=4, pady=3); card.pack_propagate(False)
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(12, 4))
        ne = ctk.CTkEntry(left, width=200, height=28, font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=0, text_color=TXT)
        ne.pack(anchor="w", pady=(8, 0)); ne.insert(0, p.get("name", "Untitled"))
        ne.bind("<FocusOut>", lambda e, pr=p, ent=ne: self._rename(pr, ent))
        ne.bind("<Return>", lambda e, pr=p, ent=ne: self._rename(pr, ent))
        ctk.CTkLabel(left, text=f"{len(p.get('steps', []))} bước", font=("Consolas", 9), text_color=DIM).pack(anchor="w")

        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=(4, 8))
        active = p["job_id"] in self.fabs and self.fabs[p["job_id"]].winfo_exists()
        
        ctk.CTkButton(right, text="📝", width=34, height=32, font=("Segoe UI", 13), fg_color=SURF2, hover_color=BRD, text_color=TXT, command=lambda: StepEditor(self, p, lambda: (self._save(), self._render()))).pack(side="left", padx=2)
        ctk.CTkButton(right, text="🟢" if active else "🚀", width=34, height=32, font=("Segoe UI", 13), fg_color=GRN if active else SURF2, hover_color=GRN2 if active else BRD, command=lambda: self._toggle_fab(p)).pack(side="left", padx=2)
        ctk.CTkButton(right, text="🗑", width=34, height=32, font=("Segoe UI", 13), fg_color=SURF2, text_color=RED, hover_color="#3a1525", command=lambda: self._del(p)).pack(side="left", padx=2)

    def _update_count(self):
        active = sum(1 for f in self.fabs.values() if f.winfo_exists())
        self.lbl_count.configure(text=f"{len(self.projects)} projects · {active} FABs")

    def _add(self):
        self.projects.append({"job_id": new_id(), "name": f"Project {len(self.projects)+1}", "fab_color": ACC, "fab_is_compact": False, "fab_pos": {"x": 100, "y": 100}, "steps": []})
        self._save(); self._render()

    def _rename(self, pr, ent):
        n = ent.get().strip()
        if n: pr["name"] = n; self._save(); self._render()

    def _del(self, pr):
        pid = pr["job_id"]
        if messagebox.askyesno("Xác nhận", f"Xóa '{pr.get('name')}'?"):
            if pid in self.fabs and self.fabs[pid].winfo_exists(): self.fabs[pid].close_fab()
            self.projects = [p for p in self.projects if p["job_id"] != pid]
            self._save(); self._render()

    def _toggle_fab(self, pr):
        pid = pr["job_id"]
        if pid in self.fabs and self.fabs[pid].winfo_exists():
            self.fabs[pid].close_fab(); del self.fabs[pid]; del self.engines[pid]
        else:
            if not pr.get("steps"): return messagebox.showinfo("Thông báo", "Thêm bước trước.")
            self.engines[pid] = MacroEngine()
            active_fabs = [f for p_id, f in self.fabs.items() if p_id != pid and f.winfo_exists()]
            self.fabs[pid] = ProjectFAB(self, pr, self.engines[pid], self._save, lambda: (self.deiconify(), self._render()), active_fabs)
        self._render()

    def _save(self): save_data(self.projects)
    def _on_close(self):
        for f in list(self.fabs.values()):
            if f.winfo_exists(): f.close_fab()
        self._save(); self.destroy()
