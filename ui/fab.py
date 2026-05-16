import time
import math
import tkinter as tk
import customtkinter as ctk
from core.engine import MacroState

BG = "#0c0c14"
BRD = "#2a2a3e"
TXT = "#e2e2f0"
ACC = "#6366f1"
GRN = "#10b981"; GRN2 = "#059669"
RED = "#f43f5e"; RED2 = "#e11d48"
AMB = "#f59e0b"; AMB2 = "#d97706"

class ProjectFAB(ctk.CTkToplevel):
    def __init__(self, master, project: dict, macro_engine, on_save=None, on_return=None, other_fabs=None):
        super().__init__(master)
        self.project = project
        self.macro_engine = macro_engine
        self.on_save = on_save
        self.on_return = on_return
        
        self._dx = self._dy = 0
        self._click_start_time = 0
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=BG)
        
        # Stacking Fix: Check for exact/near overlap and offset
        pos = self.project.get("fab_pos", {"x": 100, "y": 100})
        if other_fabs:
            for _ in range(10):
                collided = False
                for f in other_fabs:
                    fx = f.project.get("fab_pos", {}).get("x", 100)
                    fy = f.project.get("fab_pos", {}).get("y", 100)
                    dist = math.sqrt((pos["x"] - fx)**2 + (pos["y"] - fy)**2)
                    if dist < 20:
                        pos["x"] += 50
                        pos["y"] += 50
                        collided = True
                if not collided:
                    break
                    
        self.project["fab_pos"] = pos
        self.geometry(f"+{pos['x']}+{pos['y']}")
        
        self.tooltip = None
        
        # Connect engine callback
        self.macro_engine.ui_callback = self._on_state_change
        
        self._build()

    def _build(self):
        color = self.project.get("fab_color", ACC)
        is_compact = self.project.get("fab_is_compact", False)
        
        self.container = ctk.CTkFrame(self, fg_color=color, corner_radius=20 if is_compact else 10,
                                      border_width=1, border_color=BRD)
        self.container.pack(fill="both", expand=True, padx=1, pady=1)

        if is_compact:
            self.geometry(f"40x40+{self.project['fab_pos']['x']}+{self.project['fab_pos']['y']}")
            name = self.project.get("name", "?")
            initials = "".join([w[0] for w in name.split()[:2]]).upper() or name[:2].upper()
            
            self.lbl_name = ctk.CTkLabel(self.container, text=initials, font=("Segoe UI", 11, "bold"), text_color="#ffffff")
            self.lbl_name.pack(expand=True)
            
            self.lbl_name.bind("<Enter>", self._show_tooltip)
            self.lbl_name.bind("<Leave>", self._hide_tooltip)
            self.lbl_name.bind("<Button-1>", self._on_compact_click)
            self.lbl_name.bind("<B1-Motion>", self._drag_move)
            self.lbl_name.bind("<ButtonRelease-1>", self._drag_end)
            self.lbl_name.bind("<Button-3>", lambda e: self._show_menu())
            
        else:
            self.geometry(f"190x46+{self.project['fab_pos']['x']}+{self.project['fab_pos']['y']}")
            
            drag = ctk.CTkLabel(self.container, text="⠿", width=18, font=("Segoe UI", 13),
                                text_color="#ffffff", cursor="fleur")
            drag.pack(side="left", padx=(5, 2))
            drag.bind("<Button-1>", self._drag_start)
            drag.bind("<B1-Motion>", self._drag_move)
            drag.bind("<ButtonRelease-1>", self._drag_end)

            name = self.project.get("name", "?")[:12]
            self.lbl_name = ctk.CTkLabel(self.container, text=name, font=("Segoe UI", 10, "bold"),
                                          text_color="#ffffff", width=56)
            self.lbl_name.pack(side="left", padx=2)

            self.btn_play = ctk.CTkButton(self.container, text="▶", width=36, height=30,
                                           font=("Segoe UI", 13, "bold"),
                                           fg_color=GRN, hover_color=GRN2,
                                           command=self._toggle_play)
            self.btn_play.pack(side="left", padx=2)

            menu_btn = ctk.CTkButton(self.container, text="≡", width=28, height=28,
                                      font=("Segoe UI", 13), fg_color="transparent",
                                      hover_color=BRD, text_color="#ffffff",
                                      command=self._show_menu)
            menu_btn.pack(side="right", padx=(0, 4))
            
            self.container.bind("<Button-3>", lambda e: self._show_menu())
            self.lbl_name.bind("<Button-3>", lambda e: self._show_menu())
            
        self._on_state_change(self.macro_engine.state)

    def _show_tooltip(self, event):
        if self.tooltip: return
        x, y, _, _ = self.bbox("insert")
        x += self.winfo_rootx() + 45
        y += self.winfo_rooty() + 20
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.project.get("name", "Macro"), background="#ffffe0", relief="solid", borderwidth=1, font=("Segoe UI", 9))
        label.pack()

    def _hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def _on_compact_click(self, e):
        self._drag_start(e)
        self._click_start_time = time.time()
        
    def _drag_start(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag_move(self, e):
        x = self.winfo_x() + e.x - self._dx
        y = self.winfo_y() + e.y - self._dy
        self.geometry(f"+{x}+{y}")

    def _drag_end(self, e):
        self.project["fab_pos"] = {"x": self.winfo_x(), "y": self.winfo_y()}
        if self.on_save:
            self.on_save()
            
        if self.project.get("fab_is_compact", False):
            if time.time() - self._click_start_time < 0.2:
                self._toggle_play()

    def _show_menu(self):
        menu = tk.Menu(self, tearoff=0, bg="#1e1e2e", fg=TXT,
                       activebackground=ACC, activeforeground="#fff",
                       font=("Segoe UI", 10))
        menu.add_command(label="⚙  Mở Dashboard", command=self._return_dashboard)
        menu.add_separator()
        menu.add_command(label="✕  Đóng FAB", command=self.close_fab)
        try:
            menu.tk_popup(self.winfo_x() + 40, self.winfo_y() + 40)
        finally:
            menu.grab_release()

    def _on_state_change(self, new_state):
        is_compact = self.project.get("fab_is_compact", False)
        if new_state == MacroState.RUNNING:
            if is_compact:
                self.container.configure(border_width=3, border_color=RED)
            else:
                self.btn_play.configure(text="⏹", fg_color=RED, hover_color=RED2)
        elif new_state == MacroState.PAUSED:
            if is_compact:
                self.container.configure(border_width=3, border_color=AMB)
            else:
                self.btn_play.configure(text="▶", fg_color=AMB, hover_color=AMB2)
        else: # IDLE
            if is_compact:
                self.container.configure(border_width=1, border_color=BRD)
            else:
                self.btn_play.configure(text="▶", fg_color=GRN, hover_color=GRN2)

    def _toggle_play(self):
        if self.macro_engine.state == MacroState.RUNNING:
            self.macro_engine.stop()
        elif self.macro_engine.state == MacroState.PAUSED:
            self.macro_engine.resume()
        elif self.macro_engine.state == MacroState.IDLE:
            self.macro_engine.set_steps(self.project.get("steps", []))
            self.macro_engine.play()

    def _return_dashboard(self):
        if self.on_return: self.on_return()

    def close_fab(self):
        if self.macro_engine.state != MacroState.IDLE:
            self.macro_engine.stop()
        self.destroy()
