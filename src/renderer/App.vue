<template>
  <div class="overlay-root" @click="handleOverlayClick">
    <!-- Click ripple effects during recording -->
    <div
      v-for="ripple in ripples"
      :key="ripple.id"
      class="click-ripple"
      :style="{ left: ripple.x + 'px', top: ripple.y + 'px' }"
    />

    <!-- Recording overlay hint -->
    <transition name="fade">
      <div v-if="isRecording" class="recording-hint">
        <span class="animate-pulse-rec text-rose-400 text-xs font-semibold tracking-wider">
          ● ĐANG GHI — Click vào bất kỳ đâu trên màn hình
        </span>
      </div>
    </transition>

    <!-- Floating Menu -->
    <FloatingMenu
      :is-recording="isRecording"
      :is-playing="isPlaying"
      :macros="macros"
      :selected-macro-id="selectedMacroId"
      :playback-info="playbackInfo"
      @start-recording="onStartRecording"
      @stop-recording="onStopRecording"
      @start-playback="onStartPlayback"
      @stop-playback="onStopPlayback"
      @create-macro="onCreateMacro"
      @delete-macro="onDeleteMacro"
      @rename-macro="onRenameMacro"
      @reset-macro="onResetMacro"
      @select-macro="onSelectMacro"
      @fab-enter="onFabEnter"
      @fab-leave="onFabLeave"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import FloatingMenu from './components/FloatingMenu.vue';

const isRecording = ref(false);
const isPlaying = ref(false);
const macros = ref([]);
const selectedMacroId = ref(null);
const ripples = ref([]);
const playbackInfo = ref(null);
let rippleId = 0;

onMounted(async () => {
  macros.value = await window.electronAPI.getMacros();
  if (macros.value.length > 0) selectedMacroId.value = macros.value[0].id;

  window.electronAPI.onMacrosUpdated((d) => { macros.value = d; });
  window.electronAPI.onStepRecorded(() => {});
  window.electronAPI.onPlaybackStep((d) => { playbackInfo.value = d; });
  window.electronAPI.onPlaybackDone(() => { isPlaying.value = false; playbackInfo.value = null; });
});

// ─── Click capture during recording ─────────────────────
function handleOverlayClick(e) {
  if (!isRecording.value) return;
  // Ignore clicks on the FAB
  const fab = document.getElementById('floating-menu');
  if (fab && fab.contains(e.target)) return;

  // Use screen coordinates for OS-level clicking
  const sx = e.screenX;
  const sy = e.screenY;

  // Show ripple at client position
  const id = ++rippleId;
  ripples.value.push({ id, x: e.clientX, y: e.clientY });
  setTimeout(() => { ripples.value = ripples.value.filter(r => r.id !== id); }, 700);

  window.electronAPI.recordClick(sx, sy);
}

// ─── FAB hover → toggle click-through ───────────────────
function onFabEnter() {
  if (!isRecording.value && !isPlaying.value) {
    window.electronAPI.setClickThrough(false);
  }
}
function onFabLeave() {
  if (!isRecording.value && !isPlaying.value) {
    window.electronAPI.setClickThrough(true);
  }
}

// ─── Actions ─────────────────────────────────────────────
async function onStartRecording() {
  if (!selectedMacroId.value) return;
  await window.electronAPI.startRecording(selectedMacroId.value);
  isRecording.value = true;
}
async function onStopRecording() {
  await window.electronAPI.stopRecording();
  isRecording.value = false;
}
async function onStartPlayback(macroId) {
  isPlaying.value = true;
  playbackInfo.value = { macroId, current: 0, total: 0 };
  await window.electronAPI.startPlayback(macroId);
}
async function onStopPlayback() {
  await window.electronAPI.stopPlayback();
  isPlaying.value = false;
  playbackInfo.value = null;
}
async function onCreateMacro() {
  const id = await window.electronAPI.createMacro(null);
  selectedMacroId.value = id;
}
async function onDeleteMacro(macroId) {
  await window.electronAPI.deleteMacro(macroId);
  if (selectedMacroId.value === macroId) {
    selectedMacroId.value = macros.value.length > 0 ? macros.value[0].id : null;
  }
}
async function onRenameMacro(macroId, name) { await window.electronAPI.renameMacro(macroId, name); }
async function onResetMacro(macroId) { await window.electronAPI.resetMacro(macroId); }
function onSelectMacro(macroId) { selectedMacroId.value = macroId; }
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
