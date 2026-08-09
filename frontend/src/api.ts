const BASE = import.meta.env.VITE_API_URL ?? '/api'

export interface PersonalityWeights {
  openness: number
  conscientiousness: number
  extraversion: number
  agreeableness: number
  neuroticism: number
}

export type AvatarState = 'normal' | 'happy' | 'sad' | 'thinking'

export interface MessageOut {
  id: number
  role: 'user' | 'assistant'
  content: string
  avatar_state: AvatarState
  created_at: string
}

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'API error')
  }
  return res.json()
}

export const api = {
  register: (userId: string) =>
    req<{ user_id: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    }),

  getQuestions: () =>
    req<{ questions: { id: number; text: string; trait: string }[] }>('/personality/questions'),

  submitQuiz: (userId: string, answers: { question_id: number; score: number }[]) =>
    req<PersonalityWeights>('/personality/submit', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, answers }),
    }),

  getProfile: (userId: string) =>
    req<PersonalityWeights>(`/personality/${userId}`),

  sendMessage: (userId: string, message: string, googleApiKey: string) =>
    req<{ reply: string; avatar_state: AvatarState; history: MessageOut[] }>('/chat/send', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, message, google_api_key: googleApiKey }),
    }),

  getHistory: (userId: string) =>
    req<{ messages: MessageOut[] }>(`/chat/history/${userId}`),

  deleteHistory: (userId: string) =>
    req<{ deleted: number }>(`/chat/history/${userId}`, { method: 'DELETE' }),
}
