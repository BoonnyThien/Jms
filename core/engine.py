import threading
import time
import pyautogui
import pygetwindow as gw
from pynput import keyboard as pkeyboard

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02

# Global Emergency Panic Interruption
emergency_stop_event = threading.Event()

def on_press(key):
    try:
        if key == pkeyboard.Key.esc or key == pkeyboard.Key.f9:
            emergency_stop_event.set()
    except Exception:
        pass

keyboard_listener = pkeyboard.Listener(on_press=on_press)
keyboard_listener.start()

class MacroState:
    IDLE = 0
    RUNNING = 1
    PAUSED = 2

class MacroEngine:
    def __init__(self, ui_callback=None):
        """
        ui_callback: Function called when state changes to update the UI.
        Signature: ui_callback(new_state: MacroState)
        """
        self.state = MacroState.IDLE
        self.current_step_index = 0
        self.steps = []
        self.ui_callback = ui_callback

    def set_steps(self, steps: list[dict]):
        self.steps = steps

    def _set_state(self, new_state):
        self.state = new_state
        if self.ui_callback:
            self.ui_callback(self.state)

    def play(self):
        if not self.steps:
            return
        self._set_state(MacroState.RUNNING)
        self.current_step_index = 0
        emergency_stop_event.clear()
        threading.Thread(target=self._exec, daemon=True).start()

    def pause(self):
        if self.state == MacroState.RUNNING:
            self._set_state(MacroState.PAUSED)

    def resume(self):
        if self.state == MacroState.PAUSED:
            self._set_state(MacroState.RUNNING)

    def stop(self):
        emergency_stop_event.set()
        self._set_state(MacroState.IDLE)

    def _exec(self):
        while self.current_step_index < len(self.steps):
            if emergency_stop_event.is_set():
                break
                
            if self.state == MacroState.PAUSED:
                time.sleep(0.1)
                continue
                
            s = self.steps[self.current_step_index]
            action = s.get("action", "single_click")
            x, y = s.get("x", 0), s.get("y", 0)
            press_duration = s.get("press_duration", 80) / 1000.0
            delay_after = s.get("delay_after", 500) / 1000.0
            
            # The pause_macro intervention mechanism
            if action == "pause_macro":
                self._set_state(MacroState.PAUSED)
                self.current_step_index += 1
                continue
                
            # Coordinate adjustment for strict browser boundary bypass
            target_x, target_y = x, y
            try:
                windows = gw.getWindowsWithTitle("JMS VN")
                if windows:
                    win = windows[0]
                    target_x = win.left + x
                    target_y = win.top + y
            except Exception:
                pass
                
            # Anti-bot: First move mouse naturally
            pyautogui.moveTo(target_x, target_y, duration=0.1)
            
            # Anti-bot: Strict press_duration application between mouseDown and mouseUp
            if action == "single_click":
                pyautogui.mouseDown(button='left')
                time.sleep(press_duration)
                pyautogui.mouseUp(button='left')
            elif action == "right_click":
                pyautogui.mouseDown(button='right')
                time.sleep(press_duration)
                pyautogui.mouseUp(button='right')
            elif action == "double_click":
                pyautogui.mouseDown(button='left')
                time.sleep(press_duration)
                pyautogui.mouseUp(button='left')
                time.sleep(0.05)
                pyautogui.mouseDown(button='left')
                time.sleep(press_duration)
                pyautogui.mouseUp(button='left')
                
            # Delay phase checking emergency trigger
            t = 0
            while t < delay_after:
                if emergency_stop_event.is_set(): break
                time.sleep(0.05)
                t += 0.05
                
            self.current_step_index += 1
            
        # Complete Execution
        self._set_state(MacroState.IDLE)
