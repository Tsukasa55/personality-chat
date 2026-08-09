<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useChatStore } from '../stores/chat'
import { api } from '../api'
import WolfAvatar from '../components/WolfAvatar.vue'
import MessageBubble from '../components/MessageBubble.vue'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()

const input = ref('')
const sending = ref(false)
const error = ref('')
const messagesEl = ref<HTMLElement | null>(null)

onMounted(async () => {
  if (!userStore.googleApiKey) { router.push('/'); return }
  try {
    const data = await api.getHistory(userStore.userId)
    chatStore.setMessages(data.messages)
    if (data.messages.length > 0) {
      const last = data.messages[data.messages.length - 1]
      if (last.role === 'assistant') {
        chatStore.setAvatarState(last.avatar_state)
      }
    }
    scrollBottom()
  } catch { /* ignore */ }
})

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return

  input.value = ''
  sending.value = true
  error.value = ''
  chatStore.setAvatarState('thinking')

  try {
    const res = await api.sendMessage(userStore.userId, text, userStore.googleApiKey)
    chatStore.setMessages(res.history)
    chatStore.setAvatarState(res.avatar_state)
    await nextTick()
    scrollBottom()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '送信エラー'
    chatStore.setAvatarState('sad')
  } finally {
    sending.value = false
  }
}

function scrollBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
}

async function clearHistory() {
  if (!confirm('会話履歴をすべて削除しますか？')) return
  await api.deleteHistory(userStore.userId)
  chatStore.setMessages([])
  chatStore.setAvatarState('normal')
}

const hasMessages = computed(() => chatStore.messages.length > 0)
</script>

<template>
  <div class="chat-layout">
    <!-- サイドパネル（アバター） -->
    <aside class="sidebar">
      <div class="app-title">月夜の狼</div>
      <WolfAvatar :state="chatStore.avatarState" />

      <div class="sidebar-actions">
        <button class="btn-ghost small" @click="router.push('/quiz')">📋 性格を設定し直す</button>
        <button class="btn-ghost small danger" @click="clearHistory" :disabled="!hasMessages">
          🗑 履歴を削除
        </button>
      </div>

      <div class="user-info">
        <span>匿名ユーザー</span>
        <span class="uid">{{ userStore.userId.slice(0, 8) }}...</span>
      </div>
    </aside>

    <!-- メインチャット -->
    <main class="chat-main">
      <div class="chat-header">
        <h2>月夜の狼チャット</h2>
        <span class="header-sub">設定した性格で狼が応答します</span>
      </div>

      <div class="messages" ref="messagesEl">
        <div v-if="!hasMessages" class="empty-state">
          <p>「こんにちは」と話しかけてみてください。</p>
        </div>
        <MessageBubble
          v-for="msg in chatStore.messages"
          :key="msg.id"
          :message="msg"
        />
        <div v-if="sending" class="typing-indicator">
          <span /><span /><span />
        </div>
      </div>

      <p v-if="error" class="error-bar">⚠ {{ error }}</p>

      <div class="input-row">
        <textarea
          v-model="input"
          placeholder="メッセージを入力..."
          rows="1"
          @keydown.enter.exact.prevent="send"
          @keydown.enter.shift.exact="input += '\n'"
        />
        <button class="btn-primary send-btn" @click="send" :disabled="sending || !input.trim()">
          {{ sending ? '…' : '送信' }}
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* サイドバー */
.sidebar {
  width: 260px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px;
  gap: 12px;
  overflow-y: auto;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent2);
  letter-spacing: 0.05em;
}

.sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  margin-top: 8px;
}

.small { font-size: 13px; padding: 8px 12px; width: 100%; }
.danger { color: #f87171 !important; border-color: #f8717144 !important; }
.danger:hover:not(:disabled) { background: #f8717111 !important; }

.user-info {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  color: var(--text-muted);
}
.uid { font-family: monospace; font-size: 10px; opacity: 0.6; }

/* メインチャット */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: baseline;
  gap: 12px;
}
h2 { font-size: 18px; color: var(--text); }
.header-sub { font-size: 13px; color: var(--text-muted); }

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.empty-state {
  margin: auto;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}

/* タイピング */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 12px 16px;
  align-self: flex-start;
}
.typing-indicator span {
  width: 8px; height: 8px;
  background: var(--accent);
  border-radius: 50%;
  animation: typing 1.2s ease-in-out infinite;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing {
  0%, 100% { transform: translateY(0); opacity: 0.4; }
  50% { transform: translateY(-6px); opacity: 1; }
}

.error-bar {
  background: #450a0a;
  color: #fca5a5;
  padding: 8px 24px;
  font-size: 13px;
}

.input-row {
  padding: 16px 24px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

textarea {
  flex: 1;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  max-height: 120px;
  overflow-y: auto;
}

.send-btn { padding: 10px 20px; font-size: 14px; white-space: nowrap; }

/* レスポンシブ */
@media (max-width: 640px) {
  .sidebar { width: 72px; padding: 12px 8px; }
  .sidebar .app-title, .sidebar-actions, .user-info span:first-child { display: none; }
  .chat-header .header-sub { display: none; }
}
</style>
