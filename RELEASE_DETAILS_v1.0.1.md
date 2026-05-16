# Release Notes: JMS Automation Suite v1.0.1

## Key Enhancements & Features

### 1. Architectural Refactoring & Stability
- **Anti-Drift DPI Lock**: Implemented Windows OS-level DPI locking using `ctypes`. This completely resolves the coordinate drift issues caused by screen sleep/timeout cycles scaling changes.
- **Advanced Safe-Click Engine**: Resolved the "4-hour fake-click bug" where web applications would drop instantaneous machine clicks. A human-like hold delay (~60ms threshold) and explicit mouse actions (`mouseDown`/`mouseUp`) are now utilized instead of standard 0ms duration clicks.
- **Emergency Panic Button**: Implemented a global keyboard listener (via `pynput`). Pressing **F9** or **ESC** will instantly terminate the running macro thread and release control of the mouse, preventing computer lockouts during long execution blocks.
- **Chrome Window Anchoring (Relative Coordinates)**: Added `pygetwindow` dependency. The system will dynamically find the "JMS VN" Chrome window and use it as an anchor (0, 0). Even if the user drags or moves the Chrome window, the macro accuracy will dynamically adjust and remain 100% precise.

### 2. Multi-FAB Setup & Enhanced UI
- **Data Schema Redesign**: Fully adopted the JSON structure with distinct `job_id`, `job_name`, `fab_label`, `fab_last_position`, and `action_type`.
- **Drag-and-Drop Floating Action Buttons (FAB)**: Jobs can now spawn floating frameless buttons. These buttons support free-dragging, saving their coordinate states locally to `projects.json` upon release.
- **Action Switching**: Users can easily toggle between `single_click` and `double_click` directly inside the macro setup table.
- **Visual "Snap & Drag Point" Layer**: Re-calibrating clicks no longer requires re-recording! Clicking "Cài đặt vị trí" pops open a transparent fullscreen canvas where the user can visually click-and-drag the neon-red step markers across the screen to adjust the click targets intuitively.

## Production Bundling Instructions

To build a standalone executable that requires **zero dependencies** for corporate machines:

1. Setup environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```
2. Build the Executable:
   ```bash
   pyinstaller --noconfirm --onefile --windowed --name "JMS_Automation_Suite_v1.0.1" main.py
   ```
3. Deliver the resulting `dist/JMS_Automation_Suite_v1.0.1.exe` to end-users. They can run it straight out of the box with zero installations!

## Git Synchronization Blueprint
```bash
git checkout Py
git add .
git commit -m "Feat: Upgrade to Multi-FAB engine v1.0.1 with Window-Anchoring, Visual Canvas Overlays, and DPI fix"
git push origin Py
```
