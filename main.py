import os
import sys
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # Windows 8.1+
except Exception:
    ctypes.windll.user32.SetProcessDPIAware() # Older Windows

# Guarantee PyInstaller path resolution
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

from ui.dashboard import Dashboard

if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()
