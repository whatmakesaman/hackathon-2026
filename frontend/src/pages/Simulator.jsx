import { useEffect, useState } from 'react'
import { api } from '../api'
import { samples as mockSamples } from '../mocks/sample'
import PhoneInbox from '../components/PhoneInbox'
import './Simulator.css'

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
    <main className="sim sim--split">
      <form onSubmit={send} className="sim__panel">
        <header className="sim__head">
          <h1 className="sim__title">문자 발신 패널</h1>
          <p className="sim__sub">샘플을 고르거나 직접 입력한 뒤 문자를 보내세요. 오른쪽 폰에 문자가 도착해요.</p>
        </header>

        <div className="sim__samples" role="group" aria-label="샘플 문자">
          {samples.map((s) => (
            <button
              key={s.id || s.label}
              type="button"
              className="sim__chip"
              aria-pressed={text === s.text}
              disabled={loading}
              onClick={() => {
                setText(Array.from(s.text).slice(0, 2000).join(''))
                setSender(Array.from(s.sender || '').slice(0, 50).join(''))
                setSent(false)
                setError('')
              }}
            >
              {s.label}
            </button>
          ))}
        </div>

        <section className="sim__card">
          <label htmlFor="sender" className="sim__label">발신번호 (선택, 최대 50자)</label>
          <input
            id="sender"
            type="text"
            className="sim__field"
            value={sender}
            disabled={loading}
            placeholder="010-1234-5678"
            onChange={(event) => {
              setSender(Array.from(event.target.value).slice(0, 50).join(''))
              setSent(false)
            }}
          />
          <label htmlFor="msg" className="sim__label">문자 내용</label>
          <textarea
            id="msg"
            className="sim__input"
            value={text}
            disabled={loading}
            aria-describedby="message-count"
            rows={6}
            placeholder="샘플을 고르거나 문자 내용을 입력하세요"
            onChange={(event) => {
              setText(Array.from(event.target.value).slice(0, 2000).join(''))
              setSent(false)
            }}
          />
          <div id="message-count" className="sim__count">{textLength}/2000</div>
        </section>

        <button type="submit" className="sim__receive" disabled={loading || !text.trim()}>
          {loading ? '전송 중…' : '문자 보내기'}
        </button>

        {error && <p className="sim__error" role="alert">{error}</p>}
        {sent && <p className="sim__safe" role="status">발송됨 · 오른쪽 폰 화면을 확인하세요</p>}
      </form>

      <aside className="sim__phone" aria-label="수신 화면">
        <PhoneInbox inbox={inbox} />
      </aside>
    </main>
  )
}
