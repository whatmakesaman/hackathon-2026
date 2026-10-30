import { useEffect, useState } from 'react'
import { api } from '../api'
import { samples as mockSamples } from '../mocks/sample'
import PhoneInbox from '../components/PhoneInbox'

export default function Simulator({ inbox, addMessage }) {
  // 서버 샘플(GET /samples)을 못 받아도 시연할 수 있게 목 샘플로 먼저 채워 둔다.
  const [samples, setSamples] = useState(mockSamples)
  const [text, setText] = useState('')
  const [sender, setSender] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [sent, setSent] = useState(false)
  const textLength = Array.from(text).length

  useEffect(() => {
    api('/samples')
      .then((list) => { if (Array.isArray(list) && list.length) setSamples(list) })
      .catch(() => {})
  }, [])

  async function send(event) {
    event.preventDefault()
    if (loading || !text.trim() || textLength > 2000) return
    setLoading(true)
    setError('')
    setSent(false)
    try {
      const res = await api('/simulate/incoming', {
        method: 'POST',
        body: JSON.stringify({ text, ...(sender ? { sender } : {}) }),
        signal: AbortSignal.timeout(15000),
      })
      addMessage({
        id: crypto.randomUUID(),
        sender,
        text,
        receivedAt: Date.now(),
        result: res,
      })
      setSent(true)
    } catch {
      setError('전송 실패. 서버 연결을 확인한 뒤 다시 시도해 주세요.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{ maxWidth: 1100, margin: '0 auto', padding: 16, display: 'flex', flexWrap: 'wrap', gap: 24 }}>
      <form onSubmit={send} className="page card" style={{ flex: '1 1 320px', minWidth: 0, maxWidth: '100%', margin: 0 }}>
      <h1 className="title">문자 발신 패널</h1>
      <p className="muted">샘플을 고르거나 직접 입력한 뒤 문자를 보내세요.</p>

      <div className="samples">
        {samples.map((s) => (
          <button key={s.id || s.label} type="button" className="chip" disabled={loading} onClick={() => {
            setText(Array.from(s.text).slice(0, 2000).join(''))
            setSender(Array.from(s.sender || '').slice(0, 50).join(''))
            setSent(false)
            setError('')
          }}>
            {s.label}
          </button>
        ))}
      </div>

      <label htmlFor="sender">발신번호 (선택, 최대 50자)</label>
      <input
        id="sender"
        type="text"
        value={sender}
        disabled={loading}
        placeholder="010-1234-5678"
        style={{ width: '100%', padding: 12, border: '1px solid var(--line)', borderRadius: 12, font: 'inherit' }}
        onChange={(event) => {
          setSender(Array.from(event.target.value).slice(0, 50).join(''))
          setSent(false)
        }}
      />
      <label htmlFor="msg">문자 내용</label>
      <textarea
        id="msg"
        value={text}
        disabled={loading}
        aria-describedby="message-count"
        rows={6}
        placeholder="문자 내용을 입력하세요"
        onChange={(event) => {
          setText(Array.from(event.target.value).slice(0, 2000).join(''))
          setSent(false)
        }}
      />
      <div id="message-count" className="count">{textLength}/2000</div>

      <button type="submit" className="primary" disabled={loading || !text.trim()}>
        {loading ? '전송 중…' : '문자 보내기'}
      </button>

      {error && <p className="error" role="alert">{error}</p>}
      {sent && <p className="safe-notice" role="status">발송됨</p>}
      </form>
      <aside aria-label="수신 화면" style={{ flex: '1 1 320px', minWidth: 0 }}>
        <PhoneInbox inbox={inbox} />
      </aside>
    </main>
  )
}
