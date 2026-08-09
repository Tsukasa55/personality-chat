<script setup lang="ts">
import type { MessageOut } from '../api'

defineProps<{ message: MessageOut }>()

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="bubble-row" :class="message.role">
    <div class="bubble">
      <p class="content">{{ message.content }}</p>
      <span class="time">{{ formatTime(message.created_at) }}</span>
    </div>
  </div>
</template>

<style scoped>
.bubble-row {
  display: flex;
  margin: 6px 0;
}
.bubble-row.user { justify-content: flex-end; }
.bubble-row.assistant { justify-content: flex-start; }

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.user .bubble {
  background: linear-gradient(135deg, #7c6af7, #6d28d9);
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant .bubble {
  background: var(--surface2);
  color: var(--text);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}

.content { white-space: pre-wrap; }

.time {
  display: block;
  font-size: 11px;
  opacity: 0.6;
  margin-top: 4px;
  text-align: right;
}
</style>
