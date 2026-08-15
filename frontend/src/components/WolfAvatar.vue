<script setup lang="ts">
/**
 * 月夜の狼 2.5D アバター
 * public/wolf/*.webp のレイヤーを合成し、まばたき・視線追従・呼吸・耳・口パクを
 * requestAnimationFrame で駆動する。追加ライブラリなし。
 */
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import type { AvatarState } from '../api'

const props = withDefaults(defineProps<{
  state: AvatarState
  /** 応答を話している間 true にすると口が動く */
  talking?: boolean
}>(), { talking: false })

/* ---------------------------------------------------------------- 素材座標 */
const BASE_W = 1024
const VIEW_H = 1180            // バストアップとして見せる高さ（原画は1536）
const P = {
  moon:      { cx: 515, cy: 156, r: 84 },
  ear_l:     { x: 250, y: 92,  w: 162, h: 266, px: 325, py: 344 },
  ear_r:     { x: 596, y: 90,  w: 160, h: 268, px: 681, py: 344 },
  socket_l:  { x: 387, y: 420, w: 70,  h: 56 },
  socket_r:  { x: 565, y: 420, w: 70,  h: 56 },
  iris_l:    { x: 393, y: 426, w: 58,  h: 44 },
  iris_r:    { x: 571, y: 426, w: 58,  h: 44 },
  lid_l:     { x: 379, y: 412, w: 86,  h: 72 },
  lid_r:     { x: 557, y: 412, w: 86,  h: 72 },
  mouth_dark:{ x: 330, y: 610, w: 350, h: 34 },
  jaw:       { x: 330, y: 610, w: 350, h: 120 },
}

/* ------------------------------------------------------------ ステート定義 */
type Cfg = {
  label: string; glow: string; filter: string
  earL: number; earR: number   // 耳の回転(deg)
  lid: number                  // まぶたの下がり具合 0=開 1=閉
  browTilt: number             // 頭の傾き(deg)
  breath: number               // 呼吸周期(ms)
  tint: number                 // 感情色のかぶせ具合 0..1
  irisBias: [number, number]   // 視線の癖(px)
}
const CFG: Record<AvatarState, Cfg> = {
  normal:   { label: '通常',   glow: '#7c6af7', filter: 'none',
              earL: 0,   earR: 0,  lid: 0.00, browTilt: 0,    breath: 4200,
              irisBias: [0, 0],       tint: 0.00 },
  happy:    { label: '喜び',   glow: '#f59e0b', filter: 'brightness(1.07) saturate(1.12)',
              earL: 6,   earR: -6, lid: 0.00, browTilt: 0,    breath: 3200,
              irisBias: [0, -1.5],    tint: 0.10 },
  sad:      { label: '悲しみ', glow: '#60a5fa', filter: 'brightness(0.84) saturate(0.5) contrast(1.03)',
              earL: -11, earR: 11, lid: 0.42, browTilt: -2.2, breath: 5600,
              irisBias: [0, 2.5],     tint: 0.30 },
  thinking: { label: '考え中', glow: '#a78bfa', filter: 'brightness(0.95) sepia(0.10)',
              earL: -4,  earR: 2,  lid: 0.30, browTilt: 1.4,  breath: 4800,
              irisBias: [-3.5, -2.5], tint: 0.13 },
}
const cfg = computed(() => CFG[props.state] ?? CFG.normal)
/** 透明度つきの色は JS 側で組み立てる（古いブラウザ対策） */
const glowVars = computed(() => ({
  '--glow': cfg.value.glow,
  '--glow-45': cfg.value.glow + '73',
  '--glow-55': cfg.value.glow + '8c',
  '--glow-70': cfg.value.glow + 'b3',
}))

/* ------------------------------------------------------------ スケーリング */
const root = ref<HTMLElement | null>(null)
const scale = ref(0.25)
let ro: ResizeObserver | null = null

/* ------------------------------------------------------------ リグの状態値 */
const s = ref({
  blink: 0,        // 0..1 まばたき量
  gx: 0, gy: 0,    // 視線オフセット(px, 原画基準)
  bodyY: 0, bodyS: 1,
  headX: 0, headY: 0, headR: 0,
  earL: 0, earR: 0,
  jaw: 0,          // 0..1 口の開き
})

/* 目標値（実測値はこれに追従して補間される） */
const target = { gx: 0, gy: 0, headX: 0, headY: 0 }
const reduced = typeof matchMedia === 'function'
  && matchMedia('(prefers-reduced-motion: reduce)').matches

/* ------------------------------------------------------------ まばたき制御 */
let blinkPhase = -1      // -1 = 待機
let blinkAt = 0
let blinkQueue = 0
const BLINK_MS = 130
function scheduleBlink(now: number) {
  blinkAt = now + 2200 + Math.random() * 4200
  blinkQueue = Math.random() < 0.22 ? 1 : 0   // たまに二度まばたき
}

/* ---------------------------------------------------------------- 口パク */
let jawSeed = 0

/* ------------------------------------------------------------ メインループ */
let raf = 0
let t0 = 0
function loop(now: number) {
  raf = requestAnimationFrame(loop)
  if (!t0) { t0 = now; scheduleBlink(now) }
  const t = now - t0
  const c = cfg.value

  // 呼吸（下端支点でわずかに伸縮）
  const br = Math.sin((t / c.breath) * Math.PI * 2)
  s.value.bodyY = reduced ? 0 : br * 2.6
  s.value.bodyS = reduced ? 1 : 1 + br * 0.0035

  // 頭の揺れ（呼吸より少し遅れる）＋ ポインタ追従
  const sway = Math.sin((t / (c.breath * 1.45)) * Math.PI * 2)
  s.value.headX += (target.headX - s.value.headX) * 0.055
  s.value.headY += (target.headY - s.value.headY) * 0.055
  s.value.headR = c.browTilt + (reduced ? 0 : sway * 0.5) + s.value.headX * 0.13

  // 耳（左右で位相をずらした微揺れ）
  const eL = c.earL + (reduced ? 0 : Math.sin(t / 900) * 0.9)
  const eR = c.earR + (reduced ? 0 : Math.sin(t / 1050 + 1.7) * 0.9)
  s.value.earL += (eL - s.value.earL) * 0.08
  s.value.earR += (eR - s.value.earR) * 0.08

  // 視線
  s.value.gx += (target.gx + c.irisBias[0] - s.value.gx) * 0.09
  s.value.gy += (target.gy + c.irisBias[1] - s.value.gy) * 0.09

  // まばたき
  if (blinkPhase < 0 && now >= blinkAt) { blinkPhase = now }
  if (blinkPhase >= 0) {
    const p = (now - blinkPhase) / BLINK_MS
    if (p >= 1) {
      blinkPhase = -1
      if (blinkQueue > 0) { blinkQueue--; blinkAt = now + 90 } else scheduleBlink(now)
      s.value.blink = 0
    } else {
      s.value.blink = p < 0.42 ? p / 0.42 : 1 - (p - 0.42) / 0.58
    }
  }

  // 口パク
  if (props.talking && !reduced) {
    jawSeed += 0.055
    const v = (Math.sin(jawSeed * 2.7) * 0.5 + 0.5) * (Math.sin(jawSeed * 0.9) * 0.35 + 0.65)
    s.value.jaw += (Math.max(0, v) - s.value.jaw) * 0.35
  } else {
    s.value.jaw += (0 - s.value.jaw) * 0.16
  }
  return
}

/* ------------------------------------------------------------ ポインタ追従 */
function onPointer(e: PointerEvent) {
  const el = root.value
  if (!el) return
  const r = el.getBoundingClientRect()
  const nx = Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width - 0.5) * 2.2))
  const ny = Math.max(-1, Math.min(1, ((e.clientY - r.top) / r.height - 0.5) * 2.2))
  target.gx = nx * 5.5
  target.gy = ny * 4.0
  target.headX = nx * 7
  target.headY = ny * 4
}
function onLeaveWindow() { target.gx = 0; target.gy = 0; target.headX = 0; target.headY = 0 }

/* -------------------------------------------------------------- ライフサイクル */
function fit() {
  const el = root.value
  if (el) scale.value = el.clientWidth / BASE_W
}
onMounted(() => {
  fit()
  ro = new ResizeObserver(fit)
  if (root.value) ro.observe(root.value)
  window.addEventListener('pointermove', onPointer, { passive: true })
  document.addEventListener('pointerleave', onLeaveWindow)
  raf = requestAnimationFrame(loop)
})
onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  ro?.disconnect()
  window.removeEventListener('pointermove', onPointer)
  document.removeEventListener('pointerleave', onLeaveWindow)
})

/* ステートが変わった直後に一度まばたきさせる（表情の切替が自然になる） */
watch(() => props.state, () => { blinkAt = performance.now() + 60 })

/* ------------------------------------------------------------------ 表示用 */
const lidAmount = computed(() => Math.min(1, cfg.value.lid + s.value.blink * (1 - cfg.value.lid)))
function box(k: keyof typeof P) {
  const p = P[k] as { x: number; y: number; w: number; h: number }
  return { left: p.x + 'px', top: p.y + 'px', width: p.w + 'px', height: p.h + 'px' }
}
</script>

<template>
  <div class="avatar-wrapper" :class="`state-${state}`">
    <div class="viewport" ref="root" :style="glowVars">
      <!-- 背景プレート（リグが動いても縁が出ないよう少し拡大してぼかす） -->
      <div class="stage backdrop" :style="{ transform: `scale(${scale})` }">
        <img src="/wolf/body.webp" class="layer plate" alt="" />
      </div>

      <!-- 月のグロー -->
      <div
        class="moon-glow"
        :style="{
          left: (P.moon.cx / BASE_W * 100) + '%',
          top: (P.moon.cy / VIEW_H * 100) + '%',
          width: (P.moon.r * 2.9 / BASE_W * 100) + '%',
        }"
      />

      <!-- リグ本体 -->
      <div
        class="stage rig"
        :style="{
          transform: `scale(${scale}) translate(${s.headX}px, ${s.bodyY + s.headY}px)
                      rotate(${s.headR}deg) scale(${s.bodyS})`,
          filter: cfg.filter,
        }"
      >
        <img src="/wolf/body.webp" class="layer" :style="{ width: BASE_W + 'px' }" alt="月夜の狼" />

        <img src="/wolf/ear_l.webp" class="layer" alt=""
             :style="{ ...box('ear_l'),
                       transformOrigin: `${P.ear_l.px - P.ear_l.x}px ${P.ear_l.py - P.ear_l.y}px`,
                       transform: `rotate(${s.earL}deg)` }" />
        <img src="/wolf/ear_r.webp" class="layer" alt=""
             :style="{ ...box('ear_r'),
                       transformOrigin: `${P.ear_r.px - P.ear_r.x}px ${P.ear_r.py - P.ear_r.y}px`,
                       transform: `rotate(${s.earR}deg)` }" />

        <!-- 目：眼窩 → 虹彩 → まぶた -->
        <img src="/wolf/socket_l.webp" class="layer" alt="" :style="box('socket_l')" />
        <img src="/wolf/socket_r.webp" class="layer" alt="" :style="box('socket_r')" />
        <img src="/wolf/iris_l.webp" class="layer iris" alt=""
             :style="{ ...box('iris_l'), transform: `translate(${s.gx}px, ${s.gy}px)` }" />
        <img src="/wolf/iris_r.webp" class="layer iris" alt=""
             :style="{ ...box('iris_r'), transform: `translate(${s.gx}px, ${s.gy}px)` }" />
        <img src="/wolf/lid_l.webp" class="layer lid" alt=""
             :style="{ ...box('lid_l'), transform: `scaleY(${lidAmount})` }" />
        <img src="/wolf/lid_r.webp" class="layer lid" alt=""
             :style="{ ...box('lid_r'), transform: `scaleY(${lidAmount})` }" />

        <!-- 口：口内の暗部 → 下顎 -->
        <img src="/wolf/mouth_dark.webp" class="layer" alt=""
             :style="{ ...box('mouth_dark'), opacity: Math.min(1, s.jaw * 1.6) }" />
        <img src="/wolf/jaw.webp" class="layer" alt=""
             :style="{ ...box('jaw'), transform: `translateY(${s.jaw * 9}px)` }" />
      </div>

      <!-- 感情の色かぶせ（輝度は保ったまま色相だけ寄せる） -->
      <div class="tint" :style="{ background: cfg.glow, opacity: cfg.tint }" />

      <!-- 感情エフェクト -->
      <svg v-if="state === 'happy'" class="fx" viewBox="0 0 100 115">
        <text x="9" y="20" font-size="7" opacity="0.85">✨</text>
        <text x="82" y="15" font-size="6" opacity="0.75">⭐</text>
        <text x="6" y="52" font-size="5" opacity="0.6">💫</text>
      </svg>
      <svg v-if="state === 'sad'" class="fx" viewBox="0 0 100 115">
        <ellipse class="tear" cx="41.5" cy="47" rx="1.3" ry="2.4" fill="#bfdbfe" opacity="0.8" />
        <ellipse class="tear t2" cx="58.5" cy="47" rx="1.1" ry="2.1" fill="#bfdbfe" opacity="0.65" />
      </svg>
      <svg v-if="state === 'thinking'" class="fx thinking" viewBox="0 0 100 115">
        <circle cx="84" cy="16" r="9" fill="#1e293b" stroke="#7c6af7" stroke-width="1" opacity="0.88" />
        <text x="80.5" y="19.5" font-size="9" fill="#a78bfa">？</text>
        <circle cx="75" cy="27" r="3" fill="#7c6af7" opacity="0.55" />
        <circle cx="69" cy="34" r="2" fill="#7c6af7" opacity="0.35" />
      </svg>

      <div class="vignette" />
    </div>

    <div class="state-label">
      <span class="state-dot" :style="{ background: cfg.glow }" />
      {{ cfg.label }}
      <span v-if="talking" class="talk-dot">●</span>
    </div>
  </div>
</template>

<style scoped>
.avatar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.viewport {
  position: relative;
  width: 100%;
  max-width: 260px;
  aspect-ratio: 1024 / 1180;   /* バストアップ */
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--glow-55);
  box-shadow: 0 0 22px -4px var(--glow-45),
              inset 0 0 30px -10px #000;
  background: #14121a;
  transition: border-color 0.6s ease, box-shadow 0.6s ease;
  contain: paint;
}

.stage {
  position: absolute;
  top: 0;
  left: 0;
  width: 1024px;
  height: 1536px;
  transform-origin: top left;
  will-change: transform;
}

/* リグの縁が覗かないよう、背後に少し拡大＋ぼかした同じ絵を敷く */
.backdrop { filter: blur(6px) brightness(0.8); }
.backdrop .plate {
  width: 1024px;
  transform: scale(1.09);
  transform-origin: 50% 30%;
}

.rig { transition: filter 0.6s ease; }

.layer {
  position: absolute;
  display: block;
  image-rendering: auto;
  pointer-events: none;
  user-select: none;
}

.lid { transform-origin: top center; }
.iris { filter: drop-shadow(0 0 3px var(--glow-70)); }

.moon-glow {
  position: absolute;
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: radial-gradient(circle,
    var(--glow-45) 0%,
    transparent 68%);
  mix-blend-mode: screen;
  pointer-events: none;
  animation: moon-breathe 6s ease-in-out infinite;
  transition: background 0.8s ease;
}
@keyframes moon-breathe {
  0%, 100% { opacity: 0.55; }
  50%      { opacity: 0.95; }
}

.fx {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.thinking { animation: float 2.4s ease-in-out infinite; }
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-3px); }
}
.tear { animation: drip 3.4s ease-in infinite; }
.tear.t2 { animation-delay: 1.5s; }
@keyframes drip {
  0%   { transform: translateY(0);   opacity: 0; }
  18%  { opacity: 0.85; }
  75%  { transform: translateY(9px); opacity: 0.45; }
  100% { transform: translateY(13px); opacity: 0; }
}

.tint {
  position: absolute;
  inset: 0;
  mix-blend-mode: color;
  pointer-events: none;
  transition: background 0.7s ease, opacity 0.7s ease;
}

.vignette {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(ellipse at 50% 38%, transparent 45%, #0b0a10cc 100%);
}

.state-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted, #94a3b8);
  font-weight: 500;
}
.state-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  animation: blink-dot 2s ease-in-out infinite;
}
.talk-dot { font-size: 8px; color: var(--glow); animation: blink-dot 0.6s linear infinite; }
@keyframes blink-dot {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.35; }
}

@media (prefers-reduced-motion: reduce) {
  .moon-glow, .thinking, .tear, .state-dot { animation: none; }
}
</style>
