<template>
  <div class="overlay-root" @click="handleOverlayClick">
    <!-- Click ripples during recording -->
    <div
      v-for="ripple in ripples"
      :key="ripple.id"
      class="click-ripple"
      :style="{ left: ripple.x + 'px', top: ripple.y + 'px' }"
    />

    <!-- Recording banner -->
    <transition name="fade">
      <div v-if="isRecording" class="recording-hint">
        <span class="animate-pulse-rec text-rose-400 text-xs font-semibold tracking-wider">
          ● ĐANG GHI — Click vào bất kỳ đâu trên màn hình
        </span>
      </div>
    </transition>

    <!-- Macro Panel -->
    <MacroPanel
      ref="panelRef"
      :is-recording="isRecording"
      :is-playing="isPlaying"
      :playback-info="playbackInfo"
      @start-recording="onStartRecording"
      @stop-recording="onStopRecording"
      @execute="onExecute"
      @stop-playback="onStopPlayback"
      @save="onSave"
      @load="onLoad"
      @step-added="onStepAdded"
      @panel-enter="onPanelEnter"
      @panel-leave="onPanelLeave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import MacroPanel from './components/MacroPanel.vue';

const panelRef = ref<InstanceType<typeof MacroPanel> | null>(null);
const isRecording = ref(false);
const isPlaying = ref(false);
const playbackInfo = ref<{ current: number; total: number } | null>(null);
const ripples = ref<{ id: number; x: number; y: number }[]>([]);
let rippleId = 0;

onMounted(() => {
  window.electronAPI.onPlaybackStep((data) => {
    playbackInfo.value = data;
  });
  window.electronAPI.onPlaybackDone(() => {
    isPlaying.value = false;
    playbackInfo.value = null;
  });
});

// ─── Click capture during recording ─────────────────────
function handleOverlayClick(e: MouseEvent) {
  if (!isRecording.value) return;
  const panel = document.getElementById('macro-panel');
  if (panel && panel.contains(e.target as Node)) return;

  const sx = e.screenX;
  const sy = e.screenY;

  // Ripple
  const id = ++rippleId;
  ripples.value.push({ id, x: e.clientX, y: e.clientY });
  setTimeout(() => { ripples.value = ripples.value.filter(r => r.id !== id); }, 700);

  // Record in Main + forward OS click
  window.electronAPI.recordClick(sx, sy).then((step) => {
    if (step && panelRef.value) {
      panelRef.value.addStep(step.x, step.y);
    }
  });
}

// ─── Panel hover for click-through ──────────────────────
function onPanelEnter() {
  if (!isRecording.value && !isPlaying.value) {
    window.electronAPI.setClickThrough(false);
  }
}
function onPanelLeave() {
  if (!isRecording.value && !isPlaying.value) {
    window.electronAPI.setClickThrough(true);
  }
}

// ─── Recording ──────────────────────────────────────────
async function onStartRecording() {
  await window.electronAPI.startRecording();
  isRecording.value = true;
}
async function onStopRecording() {
  await window.electronAPI.stopRecording();
  isRecording.value = false;
}

// ─── Execution ──────────────────────────────────────────
async function onExecute(steps: Step[]) {
  if (steps.length === 0) return;
  isPlaying.value = true;
  playbackInfo.value = { current: 0, total: steps.length };
  await window.electronAPI.executeSequence(steps);
}
async function onStopPlayback() {
  await window.electronAPI.stopPlayback();
  isPlaying.value = false;
  playbackInfo.value = null;
}

// ─── Save / Load ────────────────────────────────────────
async function onSave(steps: Step[]) {
  await window.electronAPI.saveMacro(steps);
}
async function onLoad() {
  const loaded = await window.electronAPI.loadMacro();
  if (loaded && panelRef.value) {
    panelRef.value.loadSteps(loaded);
  }
}

function onStepAdded() { /* placeholder for future use */ }

// ─── Types ──────────────────────────────────────────────
interface Step { step: number; x: number; y: number; delay: number; }
</script>

<style scoped>
.overlay-root {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  background: transparent;
  z-index: 1;
}
.recording-hint {
  position: fixed;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15, 15, 25, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(244, 63, 94, 0.3);
  padding: 8px 20px;
  border-radius: 999px;
  z-index: 99998;
  pointer-events: none;
}
</style>
