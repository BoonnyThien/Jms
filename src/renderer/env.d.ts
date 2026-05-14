/// <reference types="vite/client" />

interface Step {
  step: number;
  x: number;
  y: number;
  delay: number;
}

interface ElectronAPI {
  setClickThrough: (ignore: boolean) => void;
  startRecording: () => Promise<boolean>;
  stopRecording: () => Promise<boolean>;
  recordClick: (sx: number, sy: number) => Promise<Step | null>;
  executeSequence: (steps: Step[]) => Promise<boolean>;
  stopPlayback: () => Promise<boolean>;
  saveMacro: (steps: Step[]) => Promise<string | null>;
  loadMacro: () => Promise<Step[] | null>;
  onStepRecorded: (cb: (step: Step) => void) => void;
  onPlaybackStep: (cb: (data: { current: number; total: number }) => void) => void;
  onPlaybackDone: (cb: () => void) => void;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

export {};
