const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

// ─── Windows API for OS-level mouse clicks ───────────────
let osClick;
try {
  const koffi = require('koffi');
  const user32 = koffi.load('user32.dll');
  const SetCursorPos = user32.func('bool __stdcall SetCursorPos(int x, int y)');
  const mouse_event_fn = user32.func('void __stdcall mouse_event(uint32_t dwFlags, uint32_t dx, uint32_t dy, uint32_t dwData, uintptr_t dwExtraInfo)');
  const LEFTDOWN = 0x0002;
  const LEFTUP = 0x0004;

  osClick = (x, y) => {
    SetCursorPos(x, y);
    mouse_event_fn(LEFTDOWN, 0, 0, 0, 0);
    mouse_event_fn(LEFTUP, 0, 0, 0, 0);
  };
  console.log('[main] koffi loaded — OS-level clicks enabled');
} catch (err) {
  console.warn('[main] koffi failed, using PowerShell fallback:', err.message);
  const { exec } = require('child_process');
  osClick = (x, y) => {
    const ps = `
      Add-Type -TypeDefinition @"
      using System; using System.Runtime.InteropServices;
      public class WinMouse {
        [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
        [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, int e);
        public static void Click(int x, int y) { SetCursorPos(x,y); mouse_event(2,0,0,0,0); mouse_event(4,0,0,0,0); }
      }
"@
      [WinMouse]::Click(${x}, ${y})
    `;
    exec(`powershell -NoProfile -Command "${ps.replace(/"/g, '\\"').replace(/\n/g, ' ')}"`);
  };
}

// ─── State ───────────────────────────────────────────────
let mainWindow = null;
let macros = [{ id: 'macro-1', name: 'Macro 1', steps: [] }];
let activeMacroId = null;
let isRecording = false;
let lastClickTime = null;
let isPlaying = false;

const isDev = !app.isPackaged;

function genId() {
  return 'macro-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7);
}
function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}
function send(channel, ...args) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send(channel, ...args);
  }
}
function macroList() {
  return macros.map(m => ({ id: m.id, name: m.name, stepCount: m.steps.length }));
}

// ─── Window ──────────────────────────────────────────────
function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width,
    height,
    x: 0,
    y: 0,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    hasShadow: false,
    skipTaskbar: false,
    resizable: false,
    fullscreenable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Default: click-through (user can interact with apps below)
  mainWindow.setIgnoreMouseEvents(true, { forward: true });

  if (isDev) {
    mainWindow.webContents.loadURL('http://localhost:5173');
  } else {
    mainWindow.webContents.loadFile(path.join(__dirname, '../../dist/index.html'));
  }

  mainWindow.show();
  mainWindow.maximize();
}

// ─── IPC: Click-through toggle ───────────────────────────
ipcMain.on('set-click-through', (event, ignore) => {
  if (!mainWindow || mainWindow.isDestroyed()) return;
  if (ignore) {
    mainWindow.setIgnoreMouseEvents(true, { forward: true });
  } else {
    mainWindow.setIgnoreMouseEvents(false);
  }
});

// ─── IPC: Macro CRUD ─────────────────────────────────────
ipcMain.handle('get-macros', () => macroList());

ipcMain.handle('create-macro', (e, name) => {
  const m = { id: genId(), name: name || `Macro ${macros.length + 1}`, steps: [] };
  macros.push(m);
  send('macros-updated', macroList());
  return m.id;
});

ipcMain.handle('delete-macro', (e, id) => {
  macros = macros.filter(m => m.id !== id);
  if (activeMacroId === id) { activeMacroId = null; isRecording = false; }
  send('macros-updated', macroList());
});

ipcMain.handle('rename-macro', (e, id, name) => {
  const m = macros.find(m => m.id === id);
  if (m) m.name = name;
  send('macros-updated', macroList());
});

ipcMain.handle('reset-macro', (e, id) => {
  const m = macros.find(m => m.id === id);
  if (m) m.steps = [];
  send('macros-updated', macroList());
});

// ─── IPC: Recording ──────────────────────────────────────
ipcMain.handle('start-recording', (e, macroId) => {
  const m = macros.find(m => m.id === macroId);
  if (!m) return false;
  activeMacroId = macroId;
  isRecording = true;
  lastClickTime = Date.now();
  m.steps = [];
  // Make overlay capture clicks (NOT click-through)
  if (mainWindow) mainWindow.setIgnoreMouseEvents(false);
  send('macros-updated', macroList());
  return true;
});

ipcMain.handle('stop-recording', () => {
  isRecording = false;
  activeMacroId = null;
  lastClickTime = null;
  // Restore click-through
  if (mainWindow) mainWindow.setIgnoreMouseEvents(true, { forward: true });
  return true;
});

ipcMain.handle('record-click', async (e, screenX, screenY) => {
  if (!isRecording || !activeMacroId) return null;
  const m = macros.find(m => m.id === activeMacroId);
  if (!m) return null;

  const now = Date.now();
  const d = lastClickTime ? Math.max(now - lastClickTime, 100) : 1000;
  lastClickTime = now;

  const step = { step: m.steps.length + 1, x: Math.round(screenX), y: Math.round(screenY), delay: d };
  m.steps.push(step);

  // Forward click to OS: temporarily go click-through, send click, restore
  if (mainWindow) mainWindow.setIgnoreMouseEvents(true);
  await delay(30);
  osClick(step.x, step.y);
  await delay(50);
  if (isRecording && mainWindow) mainWindow.setIgnoreMouseEvents(false);

  send('step-recorded', { macroId: activeMacroId, stepCount: m.steps.length, step });
  send('macros-updated', macroList());
  return step;
});

// ─── IPC: Playback ───────────────────────────────────────
ipcMain.handle('start-playback', async (e, macroId) => {
  const m = macros.find(m => m.id === macroId);
  if (!m || m.steps.length === 0 || isPlaying) return false;
  isPlaying = true;

  // Click-through during playback
  if (mainWindow) mainWindow.setIgnoreMouseEvents(true, { forward: true });

  for (let i = 0; i < m.steps.length; i++) {
    if (!isPlaying) break;
    const s = m.steps[i];
    send('playback-step', { macroId, current: i + 1, total: m.steps.length });
    if (i > 0) await delay(s.delay);
    if (!isPlaying) break;
    osClick(s.x, s.y);
  }

  isPlaying = false;
  if (mainWindow) mainWindow.setIgnoreMouseEvents(true, { forward: true });
  send('playback-done', { macroId });
  return true;
});

ipcMain.handle('stop-playback', () => {
  isPlaying = false;
  return true;
});

// ─── App Lifecycle ───────────────────────────────────────
app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
