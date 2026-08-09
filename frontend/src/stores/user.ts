import { defineStore } from 'pinia'
import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'

export const useUserStore = defineStore('user', () => {
  const userId = ref<string>('')
  const googleApiKey = ref<string>('')
  const hasProfile = ref(false)

  function init() {
    let id = localStorage.getItem('pchat_user_id')
    if (!id) {
      id = uuidv4()
      localStorage.setItem('pchat_user_id', id)
    }
    userId.value = id

    const key = localStorage.getItem('pchat_api_key')
    if (key) googleApiKey.value = key

    const profile = localStorage.getItem('pchat_has_profile')
    hasProfile.value = profile === 'true'
  }

  function setApiKey(key: string) {
    googleApiKey.value = key
    localStorage.setItem('pchat_api_key', key)
  }

  function markProfileDone() {
    hasProfile.value = true
    localStorage.setItem('pchat_has_profile', 'true')
  }

  return { userId, googleApiKey, hasProfile, init, setApiKey, markProfileDone }
})
