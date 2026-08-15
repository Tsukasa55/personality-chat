<script setup lang="ts">
/**
 * 月夜の狼アバター（ループ動画版）
 *
 * 2.5Dレイヤー合成はやめ、ループ動画を再生する。
 * 感情表現は「状態別フィルター（色味）」のみ維持する。
 *
 * props は従来と同一（ChatView 側の変更は不要）:
 *   - state:   通常 / 喜び / 悲しみ / 考え中（[STATE:x] に対応）
 *   - talking: 予約（現状は未使用。将来、発話用の別ループへ切替可能なようクラスだけ付与）
 *
 * 動画ファイルの配置:
 *   frontend/public/avatar_loop.mp4  （下の SRC を変えれば任意パス/webm も可）
 *   ポスター（読み込み中・モーション低減時の静止画）: frontend/public/avatar.png
 */
import { ref, computed, onMounted } from 'vue'
import type { AvatarState } from '../api'

const props = withDefaults(
  defineProps<{
    state: AvatarState
    talking?: boolean
  }>(),
  { talking: false },
)

// 状態別に「フィルター（色味）」と枠グロー色のみ保持
const CFG: Record<AvatarState, { label: string; glow: string; filter: string }> = {
  normal:   { label: '通常',   glow: '#7c6af7', filter: 'none' },
  happy:    { label: '喜び',   glow: '#f59e0b', filter: 'brightness(1.07) saturate(1.12)' },
  sad:      { label: '悲しみ', glow: '#60a5fa', filter: 'brightness(0.84) saturate(0.5) contrast(1.03)' },
  thinking: { label: '考え中', glow: '#a78bfa', filter: 'brightness(0.95) sepia(0.10)' },
}
const cfg = computed(() => CFG[props.state] ?? CFG.normal)

// 動画・ポスターのパス（必要なら変更）
const SRC = '/avatar_loop.mp4'
const POSTER = '/avatar.png'

// モーション低減設定では自動再生せずポスター静止画を表示
const reduced = ref(false)
onMounted(() => {
  const m = window.matchMedia('(prefers-reduced-motion: reduce)')
  reduced.value = m.matches
  m.addEventListener?.('change', (e) => (reduced.value = e.matches))
})
</script>

<template>
  <div
    class="avatar"
    :class="{ talking: props.talking }"
    :style="{ borderColor: cfg.glow, boxShadow: `0 0 20px ${cfg.glow}66` }"
  >
    <!-- 通常: ループ動画（状態フィルターのみ適用） -->
    <video
      v-if="!reduced"
      class="avatar-media"
      :style="{ filter: cfg.filter }"
      :poster="POSTER"
      autoplay
      loop
      muted
      playsinline
      preload="auto"
    >
      <source :src="SRC" type="video/mp4" />
    </video>

    <!-- モーション低減時: 静止画にフィルターのみ -->
    <img
      v-else
      class="avatar-media"
      :src="POSTER"
      alt="月夜の狼"
      :style="{ filter: cfg.filter }"
    />
  </div>
</template>

<style scoped>
.avatar {
  /* 動画(540x800・縦長)の比率に合わせ、見切れないようにする */
  width: min(540px, 92vw);
  aspect-ratio: 540 / 800;
  max-height: 88vh;
  border-radius: 16px;
  overflow: hidden;
  border: 3px solid #7c6af7;
  box-shadow: 0 0 24px #7c6af766;
  /* 枠色・グローは state に応じてインラインで上書き。滑らかに補間 */
  transition: border-color 0.5s ease, box-shadow 0.5s ease;
  background: #0b1020;
  margin: 0 auto;
}

.avatar-media {
  width: 100%;
  height: 100%;
  object-fit: contain; /* 縦横比を保ち全体を表示（見切れ防止） */
  display: block;
  transition: filter 0.5s ease; /* 状態フィルターの切替をなめらかに */
}
</style>
