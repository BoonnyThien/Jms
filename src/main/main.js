const { app, BrowserWindow, ipcMain, screen, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

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
let isRecording = false;
let isPlaying = false;
const isDev = !app.isPackaged;

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}
function send(channel, ...args) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send(channel, ...args);
  }
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

// ─── IPC: Recording ──────────────────────────────────────
ipcMain.handle('start-recording', () => {
  isRecording = true;
  if (mainWindow) mainWindow.setIgnoreMouseEvents(false);
  return true;
});

ipcMain.handle('stop-recording', () => {
  isRecording = false;
  if (mainWindow) mainWindow.setIgnoreMouseEvents(true, { forward: true });
  return true;
});

ipcMain.handle('record-click', async (e, screenX, screenY) => {
  if (!isRecording) return null;

  const step = { step: 0, x: Math.round(screenX), y: Math.round(screenY), delay: 500 };

  // Forward click to OS: temporarily click-through, send click, restore
  if (mainWindow) mainWindow.setIgnoreMouseEvents(true);
  await delay(30);
  osClick(step.x, step.y);
  await delay(50);
  if (isRecording && mainWindow) mainWindow.setIgnoreMouseEvents(false);

  return step;
});

// ─── IPC: Execute Sequence ───────────────────────────────
// Vue sends the FULL customized step array; Main executes it exactly.
ipcMain.handle('execute-sequence', async (e, sequence) => {
  if (!Array.isArray(sequence) || sequence.length === 0 || isPlaying) return false;
  isPlaying = true;

  // Click-through during playback
  if (mainWindow) mainWindow.setIgnoreMouseEvents(true, { forward: true });

  for (let i = 0; i < sequence.length; i++) {
    if (!isPlaying) break;
    const s = sequence[i];

    send('playback-step', { current: i + 1, total: sequence.length });

    // Wait the exact delay specified by the user
    if (i > 0) {
      await delay(s.delay);
    }
    if (!isPlaying) break;

    osClick(s.x, s.y);
  }

  isPlaying = false;
  if (mainWindow) mainWindow.setIgnoreMouseEvents(true, { forward: true });
  send('playback-done');
  return true;
});

ipcMain.handle('stop-playback', () => {
  isPlaying = false;
  return true;
});

// ─── IPC: Save / Load Macro ──────────────────────────────
ipcMain.handle('save-macro', async (e, steps) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    title: 'Lưu Macro',
    defaultPath: 'macro.json',
    filters: [{ name: 'JSON Files', extensions: ['json'] }],
  });
  if (result.canceled || !result.filePath) return null;

  fs.writeFileSync(result.filePath, JSON.stringify(steps, null, 2), 'utf-8');
  return result.filePath;
});

ipcMain.handle('load-macro', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Tải Macro',
    filters: [{ name: 'JSON Files', extensions: ['json'] }],
    properties: ['openFile'],
  });
  if (result.canceled || result.filePaths.length === 0) return null;

  try {
    const data = fs.readFileSync(result.filePaths[0], 'utf-8');
    const parsed = JSON.parse(data);
    if (Array.isArray(parsed)) return parsed;
    return null;
  } catch {
    return null;
  }
});

// ─── App Lifecycle ───────────────────────────────────────
app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
