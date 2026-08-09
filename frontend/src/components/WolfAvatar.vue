<script setup lang="ts">
import type { AvatarState } from '../api'

defineProps<{ state: AvatarState }>()

const stateConfig = {
  normal:   { filter: 'none',                        label: '通常',     glow: '#7c6af7' },
  happy:    { filter: 'brightness(1.15) saturate(1.3)', label: '喜び',  glow: '#f59e0b' },
  sad:      { filter: 'brightness(0.7) hue-rotate(200deg)', label: '悲しみ', glow: '#60a5fa' },
  thinking: { filter: 'brightness(0.9) sepia(0.3)',  label: '考え中',  glow: '#a78bfa' },
}
</script>

<template>
  <div class="avatar-wrapper" :class="`state-${state}`">
    <!-- 月の背景 -->
    <div class="moon" :style="{ boxShadow: `0 0 40px 10px ${stateConfig[state].glow}55` }" />

    <!-- 狼アバター画像 -->
    <div class="avatar-frame">
      <img
        src="/avatar.png"
        alt="月夜の狼"
        class="avatar-img"
        :style="{ filter: stateConfig[state].filter }"
      />
      <!-- 表情オーバーレイ SVG -->
      <div class="expression-overlay">
        <!-- happy: 星のエフェクト -->
        <svg v-if="state === 'happy'" class="effect-svg" viewBox="0 0 120 120">
          <text x="10" y="30" font-size="18" opacity="0.9">✨</text>
          <text x="85" y="25" font-size="14" opacity="0.8">⭐</text>
          <text x="5" y="80" font-size="12" opacity="0.7">💫</text>
        </svg>
        <!-- sad: 雫 -->
        <svg v-if="state === 'sad'" class="effect-svg" viewBox="0 0 120 120">
          <circle cx="45" cy="60" r="4" fill="#93c5fd" opacity="0.8" />
          <ellipse cx="45" cy="68" rx="3" ry="6" fill="#93c5fd" opacity="0.6" />
          <circle cx="75" cy="65" r="3" fill="#93c5fd" opacity="0.7" />
          <ellipse cx="75" cy="72" rx="2.5" ry="5" fill="#93c5fd" opacity="0.5" />
        </svg>
        <!-- thinking: 思考バブル -->
        <svg v-if="state === 'thinking'" class="effect-svg thinking-bubble" viewBox="0 0 120 120">
          <circle cx="100" cy="20" r="12" fill="#1e293b" stroke="#7c6af7" stroke-width="1.5" opacity="0.9"/>
          <text x="94" y="25" font-size="12" fill="#a78bfa">？</text>
          <circle cx="92" cy="35" r="4" fill="#7c6af7" opacity="0.6"/>
          <circle cx="85" cy="45" r="3" fill="#7c6af7" opacity="0.4"/>
        </svg>
      </div>
    </div>

    <!-- 状態ラベル -->
    <div class="state-label">
      <span class="state-dot" :style="{ background: stateConfig[state].glow }" />
      {{ stateConfig[state].label }}
    </div>
  </div>
</template>

<style scoped>
.avatar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 16px;
  position: relative;
  transition: all 0.5s ease;
}

.moon {
  position: absolute;
  top: 20px;
  width: 90px;
  height: 90px;
  background: radial-gradient(circle, #f8fafc 60%, #e2e8f0 100%);
  border-radius: 50%;
  opacity: 0.15;
  transition: box-shadow 0.5s ease;
}

.avatar-frame {
  position: relative;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid v-bind('stateConfig[state].glow');
  box-shadow: 0 0 20px v-bind('stateConfig[state].glow + "66"');
  transition: all 0.5s ease;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: filter 0.5s ease;
}

.expression-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.effect-svg {
  width: 100%;
  height: 100%;
  position: absolute;
  inset: 0;
}

.thinking-bubble {
  animation: float 2s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.state-happy .avatar-frame {
  animation: pulse-happy 1.5s ease-in-out infinite;
}

@keyframes pulse-happy {
  0%, 100% { box-shadow: 0 0 20px #f59e0b66; }
  50% { box-shadow: 0 0 35px #f59e0baa; }
}

.state-sad .avatar-img {
  animation: sway 3s ease-in-out infinite;
}

@keyframes sway {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-1deg); }
  75% { transform: rotate(1deg); }
}

.state-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

.state-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
