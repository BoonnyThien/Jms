<template>
  <div
    id="macro-panel"
    class="glass-card fixed rounded-2xl select-none z-[99999] transition-shadow duration-300 flex flex-col"
    :class="{
      'ring-2 ring-rose-500/50 shadow-[0_0_30px_rgba(244,63,94,0.15)]': isRecording,
      'ring-2 ring-amber-500/40 shadow-[0_0_30px_rgba(245,158,11,0.1)]': isPlaying,
    }"
    :style="{ left: pos.x + 'px', top: pos.y + 'px', width: '420px', maxHeight: '520px' }"
    @mousedown.stop
    @mouseenter="$emit('panel-enter')"
    @mouseleave="$emit('panel-leave')"
  >
    <!-- ═══════ HEADER (Drag Handle) ═══════ -->
    <div
      class="flex items-center justify-between px-4 py-2.5 cursor-grab active:cursor-grabbing border-b border-white/5 flex-shrink-0"
      @mousedown="startDrag"
    >
      <div class="flex items-center gap-2.5">
        <div class="w-2 h-2 rounded-full" :class="statusDotClass" />
        <span class="text-white/90 font-bold text-sm tracking-wide">Macro Panel</span>
        <span class="text-[10px] px-2 py-0.5 rounded-full font-mono" :class="statusBadgeClass">
          {{ statusText }}
        </span>
      </div>
      <button
        @click="isCollapsed = !isCollapsed"
        class="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10 text-white/40 hover:text-white/70 transition-colors text-xs"
      >{{ isCollapsed ? '▼' : '─' }}</button>
    </div>

    <transition name="slide">
      <div v-if="!isCollapsed" class="flex flex-col overflow-hidden flex-1">

        <!-- ═══════ CONTROLS BAR ═══════ -->
        <div class="flex items-center gap-1.5 px-3 py-2.5 border-b border-white/5 flex-shrink-0">
          <!-- Record -->
          <button
            @click="handleRecord"
            :disabled="isPlaying"
            class="ctrl-btn flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
            :class="isRecording
              ? 'bg-rose-500/25 text-rose-300 hover:bg-rose-500/35 animate-pulse-rec'
              : isPlaying
                ? 'bg-white/5 text-white/20 cursor-not-allowed'
                : 'bg-rose-500/10 text-rose-400/80 hover:bg-rose-500/20 hover:text-rose-300'"
          >
            <span>{{ isRecording ? '⏹' : '🔴' }}</span>
            <span>{{ isRecording ? 'Dừng k' : 'Ghi' }}</span>
          </button>

          <!-- Play -->
          <button
            @click="handlePlay"
            :disabled="steps.length === 0 || isRecording"
            class="ctrl-btn flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
            :class="isPlaying
              ? 'bg-amber-500/25 text-amber-300 hover:bg-amber-500/35'
              : steps.length === 0 || isRecording
                ? 'bg-white/5 text-white/20 cursor-not-allowed'
                : 'bg-emerald-500/10 text-emerald-400/80 hover:bg-emerald-500/20 hover:text-emerald-300'"
          >
            <span>{{ isPlaying ? '⏹' : '▶️' }}</span>
            <span>{{ isPlaying ? 'Dừng' : 'Phát' }}</span>
          </button>

          <div class="flex-1" />

          <!-- Save -->
          <button
            @click="$emit('save', steps)"
            :disabled="steps.length === 0"
            class="ctrl-btn px-2.5 py-1.5 rounded-lg text-xs transition-all"
            :class="steps.length === 0
              ? 'bg-white/5 text-white/15 cursor-not-allowed'
              : 'bg-white/5 text-white/50 hover:bg-sky-500/15 hover:text-sky-300'"
            title="Lưu macro"
          >💾</button>

          <!-- Load -->
          <button
            @click="$emit('load')"
            :disabled="isRecording || isPlaying"
            class="ctrl-btn px-2.5 py-1.5 rounded-lg text-xs transition-all"
            :class="isRecording || isPlaying
              ? 'bg-white/5 text-white/15 cursor-not-allowed'
              : 'bg-white/5 text-white/50 hover:bg-violet-500/15 hover:text-violet-300'"
            title="Tải macro"
          >📂</button>

          <!-- Clear All -->
          <button
            @click="clearAll"
            :disabled="steps.length === 0 || isRecording || isPlaying"
            class="ctrl-btn px-2.5 py-1.5 rounded-lg text-xs transition-all"
            :class="steps.length === 0 || isRecording || isPlaying
              ? 'bg-white/5 text-white/15 cursor-not-allowed'
              : 'bg-white/5 text-white/50 hover:bg-rose-500/15 hover:text-rose-300'"
            title="Xóa tất cả bước"
          >🗑️</button>
        </div>

        <!-- ═══════ TABLE HEADER ═══════ -->
        <div class="grid grid-cols-[40px_1fr_1fr_1fr_36px] gap-1 px-3 py-1.5 text-[10px] text-white/30 font-semibold uppercase tracking-widest border-b border-white/5 flex-shrink-0">
          <span class="text-center">#</span>
          <span class="text-center">X</span>
          <span class="text-center">Y</span>
          <span class="text-center">Delay (ms)</span>
          <span></span>
        </div>

        <!-- ═══════ STEP ROWS ═══════ -->
        <div class="step-list flex-1 overflow-y-auto min-h-0">
          <div v-if="steps.length === 0" class="flex flex-col items-center justify-center py-10 text-white/20">
            <span class="text-3xl mb-2">🎯</span>
            <span class="text-xs">Chưa có bước nào</span>
            <span class="text-[10px] mt-1 text-white/15">Nhấn 🔴 Ghi rồi click vào màn hình</span>
          </div>

          <transition-group name="list" tag="div">
            <div
              v-for="(step, index) in steps"
              :key="step.id"
              class="grid grid-cols-[40px_1fr_1fr_1fr_36px] gap-1 items-center px-3 py-1 border-b border-white/[0.03] group hover:bg-white/[0.03] transition-colors"
              :class="{
                'bg-emerald-500/5 border-l-2 border-l-emerald-400/40': isPlaying && playbackInfo && playbackInfo.current === index + 1
              }"
            >
              <!-- Step Number -->
              <span class="text-center text-[11px] text-white/30 font-mono">{{ index + 1 }}</span>

              <!-- X -->
              <input
                type="number"
                v-model.number="step.x"
                :disabled="isRecording || isPlaying"
                class="step-input"
              />

              <!-- Y -->
              <input
                type="number"
                v-model.number="step.y"
                :disabled="isRecording || isPlaying"
                class="step-input"
              />

              <!-- Delay -->
              <input
                type="number"
                v-model.number="step.delay"
                :disabled="isRecording || isPlaying"
                min="10"
                step="100"
                class="step-input"
              />

              <!-- Remove -->
              <button
                @click="removeStep(index)"
                :disabled="isRecording || isPlaying"
                class="w-6 h-6 flex items-center justify-center rounded text-white/15 hover:bg-rose-500/20 hover:text-rose-400 transition-all opacity-0 group-hover:opacity-100"
                :class="{ 'cursor-not-allowed': isRecording || isPlaying }"
                title="Xóa bước"
              >✕</button>
            </div>
          </transition-group>
        </div>

        <!-- ═══════ PLAYBACK PROGRESS ═══════ -->
        <transition name="fade">
          <div
            v-if="isPlaying && playbackInfo"
            class="px-3 py-2 border-t border-white/5 flex-shrink-0"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="text-amber-300 text-[10px] font-medium">Đang phát...</span>
              <span class="text-amber-300/60 text-[10px] font-mono">
                {{ playbackInfo.current }} / {{ playbackInfo.total }}
              </span>
            </div>
            <div class="w-full h-1 bg-white/5 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-amber-400 to-orange-400 rounded-full transition-all duration-200"
                :style="{ width: progressPercent + '%' }"
              />
            </div>
          </div>
        </transition>

        <!-- ═══════ FOOTER ═══════ -->
        <div class="px-3 py-2 border-t border-white/5 flex items-center justify-between flex-shrink-0">
          <span class="text-[10px] text-white/25 font-mono">
            {{ steps.length }} bước
          </span>
          <span class="text-[10px] text-white/15">
            Kéo header để di chuyển
          </span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Step {
  id: number;
  x: number;
  y: number;
  delay: number;
}

const props = defineProps<{
  isRecording: boolean;
  isPlaying: boolean;
  playbackInfo: { current: number; total: number } | null;
}>();

const emit = defineEmits<{
  'start-recording': [];
  'stop-recording': [];
  'execute': [steps: { step: number; x: number; y: number; delay: number }[]];
  'stop-playback': [];
  'save': [steps: { step: number; x: number; y: number; delay: number }[]];
  'load': [];
  'step-added': [];
  'panel-enter': [];
  'panel-leave': [];
}>();

// ─── State ───────────────────────────────────────────────
const steps = ref<Step[]>([]);
const isCollapsed = ref(false);
let nextId = 1;

// ─── Drag ────────────────────────────────────────────────
const pos = ref({ x: 16, y: 60 });
let dragging = false;
let offset = { x: 0, y: 0 };

function startDrag(e: MouseEvent) {
  dragging = true;
  offset = { x: e.clientX - pos.value.x, y: e.clientY - pos.value.y };
  document.addEventListener('mousemove', onDrag);
  document.addEventListener('mouseup', stopDrag);
}
function onDrag(e: MouseEvent) {
  if (!dragging) return;
  pos.value = { x: e.clientX - offset.x, y: e.clientY - offset.y };
}
function stopDrag() {
  dragging = false;
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', stopDrag);
}

// ─── Step Management (exposed to parent) ─────────────────
function addStep(x: number, y: number, delay: number = 500) {
  steps.value.push({ id: nextId++, x, y, delay });
  emit('step-added');
}

function loadSteps(loaded: { step: number; x: number; y: number; delay: number }[]) {
  steps.value = loaded.map((s, i) => ({
    id: nextId++,
    x: s.x,
    y: s.y,
    delay: s.delay ?? 500,
  }));
}

function removeStep(index: number) {
  steps.value.splice(index, 1);
}

function clearAll() {
  steps.value = [];
}

// Expose methods to parent (App.vue)
defineExpose({ addStep, loadSteps });

// ─── Actions ─────────────────────────────────────────────
function handleRecord() {
  if (props.isRecording) {
    emit('stop-recording');
  } else {
    emit('start-recording');
  }
}

function handlePlay() {
  if (props.isPlaying) {
    emit('stop-playback');
  } else {
    const exportSteps = steps.value.map((s, i) => ({
      step: i + 1,
      x: s.x,
      y: s.y,
      delay: s.delay,
    }));
    emit('execute', exportSteps);
  }
}

// ─── Computed ────────────────────────────────────────────
const progressPercent = computed(() => {
  if (!props.playbackInfo || props.playbackInfo.total === 0) return 0;
  return (props.playbackInfo.current / props.playbackInfo.total) * 100;
});

const statusText = computed(() => {
  if (props.isRecording) return 'Đang ghi';
  if (props.isPlaying) return 'Đang phát';
  return 'Sẵn sàng';
});

const statusDotClass = computed(() => {
  if (props.isRecording) return 'bg-rose-500 animate-pulse-rec';
  if (props.isPlaying) return 'bg-amber-400 animate-pulse';
  return 'bg-emerald-500';
});

const statusBadgeClass = computed(() => {
  if (props.isRecording) return 'bg-rose-500/15 text-rose-400';
  if (props.isPlaying) return 'bg-amber-500/15 text-amber-400';
  return 'bg-white/5 text-white/30';
});
</script>
