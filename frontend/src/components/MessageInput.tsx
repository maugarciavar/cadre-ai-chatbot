import { useState, type KeyboardEvent } from 'react'

interface MessageInputProps {
  onSend: (message: string) => void
  disabled: boolean
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [value, setValue] = useState('')

  const canSend = !disabled && value.trim().length > 0

  const handleSend = () => {
    if (!canSend) return
    onSend(value.trim())
    setValue('')
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="message-input">
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about Cadre AI…"
        disabled={disabled}
        rows={1}
        aria-label="Message"
      />
      <button type="button" onClick={handleSend} disabled={!canSend}>
        Send
      </button>
    </div>
  )
}
