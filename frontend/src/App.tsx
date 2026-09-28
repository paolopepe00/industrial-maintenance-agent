import { useRef, useState } from 'react'
import { sendMessage, confirmAction, type ChatResponse, type PendingApproval } from './api'
import './App.css'

interface Message {
  role: 'user' | 'agent'
  text: string
  tools?: string[]
  sources?: string[]
  pending?: PendingApproval | null
  resolved?: 'approved' | 'declined'
}

const TOOL_LABELS: Record<string, string> = {
  get_machine_status: 'Checked machine status',
  get_sensor_data: 'Retrieved sensor data',
  get_maintenance_history: 'Retrieved maintenance history',
  get_open_work_orders: 'Checked open work orders',
  create_work_order: 'Created work order',
}

const toolNames = (calls: string[]) => [...new Set(calls.map((c) => c.split('(')[0]))]
const newThreadId = () => globalThis.crypto?.randomUUID?.() ?? `t-${Date.now()}`

function App() {
  const threadId = useRef(newThreadId())
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const pushAgent = (r: ChatResponse) =>
    setMessages((m) => [
      ...m,
      {
        role: 'agent',
        text: r.pending_approval ? r.pending_approval.reasoning : r.answer,
        tools: toolNames(r.tool_calls),
        sources: r.sources,
        pending: r.pending_approval,
      },
    ])

  const pushError = (e: unknown) =>
    setMessages((m) => [...m, { role: 'agent', text: `Errore: ${(e as Error).message}` }])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text }])
    setLoading(true)
    try {
      pushAgent(await sendMessage(text, threadId.current))
    } catch (e) {
      pushError(e)
    } finally {
      setLoading(false)
    }
  }

  const decide = async (index: number, approve: boolean) => {
    setMessages((m) =>
      m.map((msg, i) => (i === index ? { ...msg, resolved: approve ? 'approved' : 'declined' } : msg)),
    )
    setLoading(true)
    try {
      pushAgent(await confirmAction(threadId.current, approve))
    } catch (e) {
      pushError(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <h1>Industrial Maintenance Assistant</h1>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            {msg.tools && msg.tools.length > 0 && (
              <ul className="tools">
                {msg.tools.map((t) => (
                  <li key={t}>✓ {TOOL_LABELS[t] ?? t}</li>
                ))}
              </ul>
            )}
            {msg.text}
            {msg.pending && (
              <div className="approval">
                <strong>Azione in attesa di conferma:</strong> {msg.pending.tool}
                <pre>{JSON.stringify(msg.pending.args, null, 2)}</pre>
                {msg.resolved ? (
                  <em>{msg.resolved === 'approved' ? 'Approvata' : 'Rifiutata'}</em>
                ) : (
                  <>
                    <button disabled={loading} onClick={() => decide(i, true)}>Approva</button>
                    <button disabled={loading} onClick={() => decide(i, false)}>Rifiuta</button>
                  </>
                )}
              </div>
            )}
            {msg.sources && msg.sources.length > 0 && (
              <div className="sources">
                Fonti: {msg.sources.map((s) => s.split('/').pop()).join(', ')}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="msg agent">…</div>}
      </div>
      <div className="composer">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Descrivi il problema, es. P-102 has abnormal vibrations"
          disabled={loading}
        />
        <button onClick={send} disabled={loading}>Invia</button>
      </div>
    </>
  )
}

export default App