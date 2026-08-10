import { useEffect, useState } from 'react'
import { getHealth } from './lib/api'
import './App.css'

type ConnectionState =
  | { phase: 'loading' }
  | { phase: 'ok'; status: string }
  | { phase: 'error'; message: string }

function App() {
  const [connection, setConnection] = useState<ConnectionState>({ phase: 'loading' })

  useEffect(() => {
    getHealth()
      .then((health) => setConnection({ phase: 'ok', status: health.status }))
      .catch((error: unknown) =>
        setConnection({
          phase: 'error',
          message: error instanceof Error ? error.message : 'Unknown error',
        }),
      )
  }, [])

  return (
    <main className="phase0">
      <h1>Cadre AI Chatbot</h1>
      <p className="subtitle">Phase 0 — deployment skeleton</p>
      {connection.phase === 'loading' && <p>Checking backend connection…</p>}
      {connection.phase === 'ok' && <p className="ok">backend status: {connection.status}</p>}
      {connection.phase === 'error' && (
        <p className="error">Backend unreachable: {connection.message}</p>
      )}
    </main>
  )
}

export default App
