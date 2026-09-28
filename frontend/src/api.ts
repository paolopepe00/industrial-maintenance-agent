export interface PendingApproval {
  tool: string
  args: Record<string, unknown>
  tool_call_id: string
  reasoning: string
}

export interface ChatResponse {
  answer: string
  sources: string[]
  tool_calls: string[]
  pending_approval: PendingApproval | null
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const sendMessage = (message: string, thread_id: string) =>
  post<ChatResponse>('/chat', { message, thread_id })

export const confirmAction = (thread_id: string, approve: boolean) =>
  post<ChatResponse>('/chat/confirm', { thread_id, approve })