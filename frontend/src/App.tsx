import { ChatWindow } from './components/ChatWindow'
import './App.css'

function App() {
  return (
    <main className="app">
      <header className="app-header">
        <h1>Cadre AI</h1>
        <p className="app-subtitle">Ask about our services, industries, or how to get started.</p>
      </header>
      <ChatWindow />
    </main>
  )
}

export default App
