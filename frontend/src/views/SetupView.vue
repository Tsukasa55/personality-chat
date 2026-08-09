<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import WolfAvatar from '../components/WolfAvatar.vue'

const router = useRouter()
const store = useUserStore()
const apiKey = ref(store.googleApiKey)
const error = ref('')

function proceed() {
  const key = apiKey.value.trim()
  if (!key) { error.value = 'Google AI APIキーを入力してください'; return }
  store.setApiKey(key)
  if (store.hasProfile) {
    router.push('/chat')
  } else {
    router.push('/quiz')
  }
}
</script>

<template>
  <div class="setup-page">
    <div class="setup-card">
      <WolfAvatar state="normal" />

      <h1>月夜の狼チャット</h1>
      <p class="subtitle">狼アバターの性格を決めて話せる会話AIアシスタント</p>

      <div class="form-group">
        <label>Google AI APIキー</label>
        <input
          v-model="apiKey"
          type="password"
          placeholder="AIza..."
          @keyup.enter="proceed"
        />
        <a href="https://aistudio.google.com/app/apikey" target="_blank" class="help-link">
          APIキーを取得する →
        </a>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <button class="btn-primary" @click="proceed" :disabled="!apiKey.trim()">
        {{ store.hasProfile ? 'チャットを開始' : '狼の性格を設定する' }}
      </button>

      <p class="note">
        会話履歴はブラウザのUUIDに紐付けて暗号化保存されます。<br />
        外部に送信されるのはGemini API宛のメッセージのみです。
      </p>
    </div>
  </div>
</template>

<style scoped>
.setup-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at 50% 20%, #1a1a3e 0%, #0f0f1a 70%);
  padding: 20px;
}

.setup-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 40px 36px;
  max-width: 420px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  box-shadow: var(--shadow);
}

h1 { font-size: 22px; font-weight: 700; color: var(--accent2); }
.subtitle { font-size: 13px; color: var(--text-muted); text-align: center; }

.form-group {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label { font-size: 13px; color: var(--text-muted); font-weight: 600; }
input { width: 100%; font-size: 14px; }

.help-link {
  font-size: 12px;
  color: var(--accent2);
  text-decoration: none;
  text-align: right;
}
.help-link:hover { text-decoration: underline; }

.error { color: #f87171; font-size: 13px; }

.btn-primary { width: 100%; }

.note {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  line-height: 1.6;
}
</style>
