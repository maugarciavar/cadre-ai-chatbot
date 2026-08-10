import type { Role } from '../types'

interface MessageBubbleProps {
  role: Role
  content: string
}

export function MessageBubble({ role, content }: MessageBubbleProps) {
  return (
    <div className={`message-row message-row-${role}`}>
      <div className={`message-bubble message-bubble-${role}`}>{content}</div>
    </div>
  )
}
