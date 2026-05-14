const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // ─── Click-through control ─────────────────────────
  setClickThrough: (ignore) => ipcRenderer.send('set-click-through', ignore),

  // ─── Macro CRUD ────────────────────────────────────
  getMacros: () => ipcRenderer.invoke('get-macros'),
  createMacro: (name) => ipcRenderer.invoke('create-macro', name),
  deleteMacro: (id) => ipcRenderer.invoke('delete-macro', id),
  renameMacro: (id, name) => ipcRenderer.invoke('rename-macro', id, name),
  resetMacro: (id) => ipcRenderer.invoke('reset-macro', id),

  // ─── Recording ─────────────────────────────────────
  startRecording: (macroId) => ipcRenderer.invoke('start-recording', macroId),
  stopRecording: () => ipcRenderer.invoke('stop-recording'),
  recordClick: (sx, sy) => ipcRenderer.invoke('record-click', sx, sy),

  // ─── Playback ──────────────────────────────────────
  startPlayback: (macroId) => ipcRenderer.invoke('start-playback', macroId),
  stopPlayback: () => ipcRenderer.invoke('stop-playback'),

  // ─── Events from Main → Renderer ──────────────────
  onStepRecorded: (cb) => ipcRenderer.on('step-recorded', (_, d) => cb(d)),
  onPlaybackStep: (cb) => ipcRenderer.on('playback-step', (_, d) => cb(d)),
  onPlaybackDone: (cb) => ipcRenderer.on('playback-done', (_, d) => cb(d)),
  onMacrosUpdated: (cb) => ipcRenderer.on('macros-updated', (_, d) => cb(d)),
});
