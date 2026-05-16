import json
import os
import sys

# Locate the root directory for the config file
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(BASE_DIR, "projects.json")
DEFAULT_COLOR = "#6366f1"

def new_id() -> str:
    import random
    import string
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))

def load_and_migrate_data() -> list[dict]:
    """Loads projects.json and gracefully migrates schema from v1.0.1 to v1.0.2"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return []
            
        migrated = []
        for p in data:
            new_p = {}
            # v1.0.2 Schema Upgrade
            new_p["job_id"] = p.get("job_id", p.get("id", new_id()))
            new_p["name"] = p.get("name", p.get("job_name", "Untitled"))
            new_p["fab_color"] = p.get("fab_color", DEFAULT_COLOR)
            new_p["fab_is_compact"] = p.get("fab_is_compact", False)
            
            # Position Migration
            pos = p.get("fab_pos")
            if not pos:
                if "fab_last_position" in p:
                    pos = p["fab_last_position"]
                elif "fab_x" in p and "fab_y" in p:
                    pos = {"x": p["fab_x"], "y": p["fab_y"]}
                else:
                    pos = {"x": 100, "y": 100}
            new_p["fab_pos"] = pos
            
            # Steps Migration
            new_steps = []
            for idx, s in enumerate(p.get("steps", [])):
                new_s = {}
                new_s["step_id"] = s.get("step_id", idx + 1)
                new_s["name"] = s.get("name", f"Step {idx + 1}")
                
                # Action mapping normalization
                old_action = s.get("action", s.get("action_type", "single_click"))
                if old_action not in ["single_click", "double_click", "right_click", "pause_macro"]:
                    old_action = "single_click"
                new_s["action"] = old_action
                
                new_s["x"] = s.get("x", 0)
                new_s["y"] = s.get("y", 0)
                new_s["delay_after"] = s.get("delay_after", s.get("delay", 500))
                new_s["press_duration"] = s.get("press_duration", 80)
                new_steps.append(new_s)
                
            new_p["steps"] = new_steps
            migrated.append(new_p)
            
        return migrated
    except Exception:
        return []

def save_data(projects: list[dict]):
    """Saves the current state of projects to the config file safely"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)
