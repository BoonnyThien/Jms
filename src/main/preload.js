const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // ─── Click-through ─────────────────────────────────
  setClickThrough: (ignore) => ipcRenderer.send('set-click-through', ignore),

  // ─── Recording ─────────────────────────────────────
  startRecording: () => ipcRenderer.invoke('start-recording'),
  stopRecording: () => ipcRenderer.invoke('stop-recording'),
  recordClick: (sx, sy) => ipcRenderer.invoke('record-click', sx, sy),

  // ─── Execution ─────────────────────────────────────
  executeSequence: (steps) => ipcRenderer.invoke('execute-sequence', steps),
  stopPlayback: () => ipcRenderer.invoke('stop-playback'),

  // ─── Save / Load ──────────────────────────────────
  saveMacro: (steps) => ipcRenderer.invoke('save-macro', steps),
  loadMacro: () => ipcRenderer.invoke('load-macro'),

  // ─── Events from Main ─────────────────────────────
  onStepRecorded: (cb) => ipcRenderer.on('step-recorded', (_, d) => cb(d)),
  onPlaybackStep: (cb) => ipcRenderer.on('playback-step', (_, d) => cb(d)),
  onPlaybackDone: (cb) => ipcRenderer.on('playback-done', () => cb()),
});
