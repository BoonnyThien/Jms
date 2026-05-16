# JMS Automation Suite - AI State

## Current Version
- Branch: Py
- Tag: v1.0.2 (In Progress)

## Architecture Overview
The application is being modularized from a monolithic `main.py` into a structured, maintainable architecture:

- `core/`
  - `config.py`: Handles JSON data loading, saving, and schema migrations.
  - `engine.py`: Contains the PyAutoGUI click logic, threaded execution, and macro state machine (IDLE, RUNNING, PAUSED).
- `ui/`
  - `fab.py`: Manages the Floating Action Buttons (FAB), stacking, UI updates, and drag-and-drop.
  - `dashboard.py`: Manages the main GUI dashboard (customtkinter), macro table editing, and setup.
- `main.py`: The entry point that initializes the app and stitches components together.

## Current Progress
- [x] Task 1: Create Memory & Restructure (`AI_STATE.md` created, folder structure proposed).
- [x] Task 2: Advanced JSON Schema (`core/config.py`).
- [x] Task 3: The Anti-Bot Engine & Intervention (`core/engine.py`).
- [x] Task 4: UI Upgrades (`ui/fab.py` & `ui/dashboard.py`).

## Next Steps
- Modularization for `v1.0.2` is successfully complete. Awaiting final review.
