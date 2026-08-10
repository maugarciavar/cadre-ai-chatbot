import type { ChatMessage, ChatResult } from '../types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function sendChatMessage(message: string, history: ChatMessage[]): Promise<ChatResult> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })

  if (!response.ok) {
    throw new Error(
      response.status === 422
        ? 'That message is too long. Please shorten it and try again.'
        : `Chat request failed (${response.status})`,
    )
  }

  return response.json()
}
