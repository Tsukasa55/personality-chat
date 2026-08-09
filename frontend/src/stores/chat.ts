import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AvatarState, MessageOut } from '../api'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<MessageOut[]>([])
  const avatarState = ref<AvatarState>('normal')
  const loading = ref(false)
  const error = ref<string | null>(null)

  function setMessages(msgs: MessageOut[]) {
    messages.value = msgs
  }

  function setAvatarState(state: AvatarState) {
    avatarState.value = state
  }

  return { messages, avatarState, loading, error, setMessages, setAvatarState }
})
