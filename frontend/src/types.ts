export type Role = 'user' | 'assistant'

export interface ChatMessage {
  role: Role
  content: string
}

export interface DisplayMessage extends ChatMessage {
  escalate?: boolean
}

export interface ChatResult {
  reply: string
  escalate: boolean
}
