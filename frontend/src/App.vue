<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'
import { api } from './api'

const userStore = useUserStore()

onMounted(async () => {
  userStore.init()
  try {
    await api.register(userStore.userId)
  } catch {
    // 既存ユーザーは無視
  }
})
</script>

<template>
  <RouterView />
</template>
