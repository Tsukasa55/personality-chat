<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { api } from '../api'
import type { PersonalityWeights } from '../api'

const router = useRouter()
const store = useUserStore()

const questions = ref<{ id: number; text: string; trait: string }[]>([])
const answers = ref<Record<number, number>>({})
const loading = ref(false)
const submitting = ref(false)
const result = ref<PersonalityWeights | null>(null)
const error = ref('')

const current = ref(0)
const total = computed(() => questions.value.length)
const progress = computed(() => total.value ? ((current.value) / total.value) * 100 : 0)

const LABELS = ['まったく違う', 'やや違う', 'どちらとも言えない', 'やや当てはまる', 'とても当てはまる']

onMounted(async () => {
  loading.value = true
  try {
    const data = await api.getQuestions()
    questions.value = data.questions
  } catch {
    error.value = '質問の読み込みに失敗しました'
  } finally {
    loading.value = false
  }
})

function select(score: number) {
  const q = questions.value[current.value]
  if (!q) return
  answers.value[q.id] = score
  if (current.value < total.value - 1) {
    current.value++
  }
}

const allAnswered = computed(() =>
  questions.value.every(q => answers.value[q.id] !== undefined)
)

async function submit() {
  submitting.value = true
  error.value = ''
  try {
    const answerList = questions.value.map(q => ({
      question_id: q.id,
      score: answers.value[q.id],
    }))
    result.value = await api.submitQuiz(store.userId, answerList)
    store.markProfileDone()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '送信に失敗しました'
  } finally {
    submitting.value = false
  }
}

const traitLabels: Record<string, string> = {
  openness: '開放性',
  conscientiousness: '誠実性',
  extraversion: '外向性',
  agreeableness: '協調性',
  neuroticism: '神経症傾向',
}
</script>

<template>
  <div class="quiz-page">
    <div class="quiz-card" v-if="!result">
      <div class="quiz-header">
        <h2>狼の性格を設定</h2>
        <span class="progress-label">{{ current + 1 }} / {{ total }}</span>
      </div>

      <p class="quiz-intro">
        どんな月夜の狼と話したいですか？各項目に、そう思う度合いで答えてください。
      </p>

      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }" />
      </div>

      <div v-if="loading" class="center-text">読み込み中...</div>
      <div v-else-if="questions[current]" class="question-section">
        <div class="trait-badge">{{ questions[current].trait }}</div>
        <p class="question-text">{{ questions[current].text }}</p>

        <div class="options">
          <button
            v-for="(label, i) in LABELS"
            :key="i"
            class="option-btn"
            :class="{ selected: answers[questions[current].id] === i + 1 }"
            @click="select(i + 1)"
          >
            <span class="score">{{ i + 1 }}</span>
            <span class="label">{{ label }}</span>
          </button>
        </div>
      </div>

      <div class="quiz-nav">
        <button class="btn-ghost" @click="current = Math.max(0, current - 1)" :disabled="current === 0">
          ← 戻る
        </button>
        <button
          v-if="allAnswered"
          class="btn-primary"
          @click="submit"
          :disabled="submitting"
        >
          {{ submitting ? '送信中...' : 'この性格で決定' }}
        </button>
        <button
          v-else
          class="btn-ghost"
          @click="current = Math.min(total - 1, current + 1)"
          :disabled="current === total - 1"
        >
          次へ →
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- 結果画面 -->
    <div class="result-card" v-else>
      <h2>設定した性格</h2>
      <p class="quiz-intro">この設定で月夜の狼が応答します。</p>
      <div class="trait-bars">
        <div v-for="(val, key) in result" :key="key" class="trait-row">
          <span class="trait-name">{{ traitLabels[key] }}</span>
          <div class="bar-bg">
            <div class="bar-fill" :style="{ width: (val * 100).toFixed(0) + '%' }" />
          </div>
          <span class="trait-val">{{ (val * 100).toFixed(0) }}%</span>
        </div>
      </div>
      <button class="btn-primary" @click="router.push('/chat')">チャットを開始 →</button>
    </div>
  </div>
</template>

<style scoped>
.quiz-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at 50% 10%, #1a1a3e 0%, #0f0f1a 70%);
  padding: 20px;
}

.quiz-card, .result-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 40px 36px;
  max-width: 560px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  box-shadow: var(--shadow);
}

.quiz-header { display: flex; justify-content: space-between; align-items: center; }
h2 { font-size: 20px; font-weight: 700; color: var(--accent2); }
.progress-label { font-size: 13px; color: var(--text-muted); }
.quiz-intro { font-size: 13px; color: var(--text-muted); line-height: 1.6; margin-top: -12px; }

.progress-bar {
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  border-radius: 3px;
  transition: width 0.3s ease;
}

.trait-badge {
  display: inline-block;
  background: var(--accent)22;
  color: var(--accent2);
  border: 1px solid var(--accent)44;
  border-radius: 20px;
  padding: 2px 12px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}

.question-text {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.5;
  min-height: 60px;
}

.options { display: flex; flex-direction: column; gap: 8px; }

.option-btn {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  text-align: left;
  transition: all 0.15s;
}

.option-btn:hover { border-color: var(--accent); background: var(--accent)11; }
.option-btn.selected {
  border-color: var(--accent);
  background: var(--accent)22;
  color: var(--accent2);
}

.score {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--border);
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.option-btn.selected .score { background: var(--accent); color: white; }
.label { font-size: 14px; }

.quiz-nav { display: flex; justify-content: space-between; align-items: center; }
.error { color: #f87171; font-size: 13px; }
.center-text { text-align: center; color: var(--text-muted); }

/* 結果 */
.trait-bars { display: flex; flex-direction: column; gap: 16px; }
.trait-row { display: flex; align-items: center; gap: 12px; }
.trait-name { width: 90px; font-size: 13px; color: var(--text-muted); flex-shrink: 0; }
.bar-bg { flex: 1; height: 10px; background: var(--border); border-radius: 5px; overflow: hidden; }
.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  border-radius: 5px;
  transition: width 0.8s ease;
}
.trait-val { width: 36px; font-size: 13px; font-weight: 600; color: var(--accent2); text-align: right; }
</style>
