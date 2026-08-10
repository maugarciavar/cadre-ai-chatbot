import { useRef, useState, useEffect } from 'react'
import { sendChatMessage } from '../lib/api'
import type { ChatMessage, DisplayMessage } from '../types'
import { MessageBubble } from './MessageBubble'
import { EscalationBanner } from './EscalationBanner'
import { MessageInput } from './MessageInput'

const STARTER_QUESTIONS = [
  'What does Cadre AI do?',
  'How do I book a strategy call?',
  "What's the AI Maturity Index?",
  'How do you handle LLM selection and data security?',
]

export function ChatWindow() {
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollAnchorRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  async function handleSend(text: string) {
    const history: ChatMessage[] = messages.map(({ role, content }) => ({ role, content }))

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setIsLoading(true)
    setError(null)

    try {
      const result = await sendChatMessage(text, history)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: result.reply, escalate: result.escalate },
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-window">
      <div className="message-list">
        {messages.length === 0 && (
          <div className="starter-questions">
            <p>Ask me anything about Cadre AI, or try one of these:</p>
            <div className="starter-question-chips">
              {STARTER_QUESTIONS.map((question) => (
                <button
                  key={question}
                  type="button"
                  className="starter-question-chip"
                  onClick={() => handleSend(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index}>
            <MessageBubble role={message.role} content={message.content} />
            {message.role === 'assistant' && message.escalate && <EscalationBanner />}
          </div>
        ))}

        {isLoading && (
          <div className="message-row message-row-assistant">
            <div className="message-bubble message-bubble-assistant message-bubble-loading">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}

        <div ref={scrollAnchorRef} />
      </div>

      {error && <div className="chat-error">{error}</div>}

      <MessageInput onSend={handleSend} disabled={isLoading} />
    </div>
  )
}
