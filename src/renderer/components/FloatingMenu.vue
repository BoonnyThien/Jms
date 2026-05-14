<template>
  <div
    id="floating-menu"
    ref="menuRef"
    class="glass-card fixed rounded-2xl select-none z-[99999] transition-shadow duration-300"
    :class="{ 'ring-2 ring-rose-500/50 shadow-[0_0_30px_rgba(244,63,94,0.2)]': isRecording }"
    :style="{ left: pos.x + 'px', top: pos.y + 'px', width: '300px' }"
    @mousedown.stop
    @mouseenter="$emit('fab-enter')"
    @mouseleave="$emit('fab-leave')"
  >
    <!-- Header (Drag Handle) -->
    <div
      class="flex items-center justify-between px-4 py-2.5 cursor-grab active:cursor-grabbing border-b border-white/5"
      @mousedown="startDrag"
    >
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full" :class="statusDotClass" />
        <span class="text-white/90 font-semibold text-sm tracking-wide">Auto-Clicker</span>
      </div>
      <button
        @click="toggleCollapse"
        class="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10 text-white/50 hover:text-white/80 transition-colors text-xs"
      >
        {{ isCollapsed ? '▼' : '▲' }}
      </button>
    </div>

    <!-- Body -->
    <transition name="slide">
      <div v-if="!isCollapsed">

        <!-- Macro List -->
        <div class="macro-list max-h-48 overflow-y-auto px-2 py-2 space-y-1">
          <div
            v-for="macro in macros"
            :key="macro.id"
            class="flex items-center gap-2 px-2.5 py-2 rounded-lg transition-all duration-200 group"
            :class="macro.id === selectedMacroId
              ? 'bg-gradient-to-r from-indigo-500/20 to-purple-500/20 border border-indigo-400/20'
              : 'hover:bg-white/5 border border-transparent'"
            @click="$emit('select-macro', macro.id)"
          >
            <div
              class="w-2 h-2 rounded-full flex-shrink-0 transition-colors"
              :class="macro.id === selectedMacroId ? 'bg-indigo-400' : 'bg-white/20'"
            />

            <!-- Name (editable on double-click) -->
            <div class="flex-1 min-w-0">
              <input
                v-if="editingId === macro.id"
                v-model="editingName"
                @blur="finishRename(macro.id)"
                @keydown.enter="finishRename(macro.id)"
                @keydown.escape="cancelRename"
                @click.stop
                class="bg-white/10 text-white text-xs font-medium px-2 py-0.5 rounded w-full outline-none focus:ring-1 focus:ring-indigo-400/50"
              />
              <span
                v-else
                @dblclick.stop="startRename(macro)"
                class="text-white/80 text-xs font-medium truncate block cursor-text"
                title="Nhấp đúp để đổi tên"
              >{{ macro.name }}</span>
            </div>

            <span class="text-[10px] text-white/40 font-mono flex-shrink-0">{{ macro.stepCount }} bước</span>

            <!-- Play / Stop -->
            <button
              @click.stop="handlePlay(macro.id)"
              :disabled="macro.stepCount === 0 || isRecording"
              class="w-7 h-7 flex items-center justify-center rounded-lg transition-all flex-shrink-0"
              :class="isPlaying && playbackInfo?.macroId === macro.id
                ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
                : macro.stepCount === 0 || isRecording
                  ? 'text-white/15 cursor-not-allowed'
                  : 'text-emerald-400/70 hover:bg-emerald-500/20 hover:text-emerald-400'"
              :title="isPlaying && playbackInfo?.macroId === macro.id ? 'Dừng phát' : 'Phát macro'"
            >
              <span class="text-sm">{{ isPlaying && playbackInfo?.macroId === macro.id ? '⏹' : '▶' }}</span>
            </button>

            <!-- Delete -->
            <button
              @click.stop="$emit('delete-macro', macro.id)"
              :disabled="isRecording || isPlaying"
              class="w-7 h-7 flex items-center justify-center rounded-lg text-white/20 hover:bg-rose-500/20 hover:text-rose-400 transition-all opacity-0 group-hover:opacity-100 flex-shrink-0"
              title="Xóa macro"
            ><span class="text-xs">✕</span></button>
          </div>

          <div v-if="macros.length === 0" class="text-center py-6 text-white/30 text-xs">
            Chưa có macro nào.<br />Nhấn "＋ Thêm" để bắt đầu.
          </div>
        </div>

        <!-- Playback Progress -->
        <transition name="fade">
          <div
            v-if="isPlaying && playbackInfo"
            class="mx-3 mb-2 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2"
          >
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-amber-300 text-[10px] font-medium">Đang phát lại...</span>
              <span class="text-amber-300/70 text-[10px] font-mono">{{ playbackInfo.current }}/{{ playbackInfo.total }}</span>
            </div>
            <div class="w-full h-1 bg-white/5 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-amber-400 to-orange-400 rounded-full transition-all duration-300"
                :style="{ width: (playbackInfo.total > 0 ? (playbackInfo.current / playbackInfo.total) * 100 : 0) + '%' }"
              />
            </div>
          </div>
        </transition>

        <!-- Controls -->
        <div class="px-3 pb-3 pt-1 flex items-center gap-2">
          <button
            @click="$emit('create-macro')"
            :disabled="isRecording || isPlaying"
            class="flex items-center gap-1 px-3 py-2 rounded-xl text-xs font-medium transition-all"
            :class="isRecording || isPlaying
              ? 'bg-white/5 text-white/20 cursor-not-allowed'
              : 'bg-white/5 text-white/60 hover:bg-indigo-500/20 hover:text-indigo-300'"
            title="Thêm macro mới"
          >
            <span class="text-sm">＋</span><span>Thêm</span>
          </button>

          <div class="flex-1" />

          <button
            @click="handleRecord"
            :disabled="!selectedMacroId || isPlaying"
            class="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all"
            :class="isRecording
              ? 'bg-rose-500/25 text-rose-300 hover:bg-rose-500/35 animate-pulse-rec'
              : !selectedMacroId || isPlaying
                ? 'bg-white/5 text-white/20 cursor-not-allowed'
                : 'bg-rose-500/15 text-rose-400 hover:bg-rose-500/25'"
            :title="isRecording ? 'Dừng ghi' : 'Bắt đầu ghi'"
          >
            <span class="text-sm">{{ isRecording ? '⏹' : '🔴' }}</span>
            <span>{{ isRecording ? 'Dừng' : 'Ghi' }}</span>
          </button>

          <button
            @click="$emit('reset-macro', selectedMacroId)"
            :disabled="!selectedMacroId || isRecording || isPlaying || selectedSteps === 0"
            class="w-8 h-8 flex items-center justify-center rounded-xl transition-all"
            :class="!selectedMacroId || isRecording || isPlaying || selectedSteps === 0
              ? 'bg-white/5 text-white/15 cursor-not-allowed'
              : 'bg-white/5 text-white/50 hover:bg-orange-500/20 hover:text-orange-300'"
            title="Xóa bước đã ghi"
          ><span class="text-sm">🔄</span></button>
        </div>

        <!-- Status -->
        <div class="px-4 pb-2.5 flex items-center justify-between">
          <span class="text-[10px] font-medium" :class="statusTextClass">{{ statusText }}</span>
          <span v-if="selectedMacroId" class="text-[10px] text-white/25 font-mono">{{ selectedSteps }} bước đã ghi</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';

const props = defineProps({
  isRecording: Boolean,
  isPlaying: Boolean,
  macros: Array,
  selectedMacroId: String,
  playbackInfo: Object,
});

const emit = defineEmits([
  'start-recording', 'stop-recording',
  'start-playback', 'stop-playback',
  'create-macro', 'delete-macro', 'rename-macro', 'reset-macro',
  'select-macro', 'fab-enter', 'fab-leave',
]);

// ─── Drag ────────────────────────────────────────────────
const menuRef = ref(null);
const pos = ref({ x: 20, y: 80 });
let dragging = false;
let offset = { x: 0, y: 0 };

function startDrag(e) {
  dragging = true;
  offset = { x: e.clientX - pos.value.x, y: e.clientY - pos.value.y };
  document.addEventListener('mousemove', onDrag);
  document.addEventListener('mouseup', stopDrag);
}
function onDrag(e) {
  if (!dragging) return;
  pos.value = { x: e.clientX - offset.x, y: e.clientY - offset.y };
}
function stopDrag() {
  dragging = false;
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', stopDrag);
}

// ─── Collapse ────────────────────────────────────────────
const isCollapsed = ref(false);
function toggleCollapse() { isCollapsed.value = !isCollapsed.value; }

// ─── Rename ──────────────────────────────────────────────
const editingId = ref(null);
const editingName = ref('');

function startRename(macro) {
  editingId.value = macro.id;
  editingName.value = macro.name;
  nextTick(() => {
    const el = document.querySelector('#floating-menu input');
    if (el) el.focus();
  });
}
function finishRename(id) {
  if (editingName.value.trim()) emit('rename-macro', id, editingName.value.trim());
  editingId.value = null;
}
function cancelRename() { editingId.value = null; }

// ─── Actions ─────────────────────────────────────────────
function handleRecord() {
  emit(props.isRecording ? 'stop-recording' : 'start-recording');
}
function handlePlay(id) {
  if (props.isPlaying && props.playbackInfo?.macroId === id) emit('stop-playback');
  else emit('start-playback', id);
}

// ─── Computed ────────────────────────────────────────────
const selectedSteps = computed(() => {
  const m = props.macros.find(m => m.id === props.selectedMacroId);
  return m ? m.stepCount : 0;
});
const statusText = computed(() => {
  if (props.isRecording) return '● Đang ghi...';
  if (props.isPlaying) return '▶ Đang phát lại...';
  return '⏸ Chờ lệnh';
});
const statusTextClass = computed(() => {
  if (props.isRecording) return 'text-rose-400';
  if (props.isPlaying) return 'text-amber-400';
  return 'text-white/30';
});
const statusDotClass = computed(() => {
  if (props.isRecording) return 'bg-rose-500 animate-pulse-rec';
  if (props.isPlaying) return 'bg-amber-400 animate-pulse';
  return 'bg-emerald-500';
});
</script>
