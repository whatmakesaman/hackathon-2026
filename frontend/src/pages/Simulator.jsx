import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { samples as mockSamples } from '../mocks/sample'
import NotificationBanner from '../components/NotificationBanner'

export default function Simulator() {
  const navigate = useNavigate()
  // 서버 샘플(GET /samples)을 못 받아도 시연할 수 있게 목 샘플로 먼저 채워 둔다.
  const [samples, setSamples] = useState(mockSamples)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [banner, setBanner] = useState(null)
  const [safeNotice, setSafeNotice] = useState(false)
  const closeBanner = useCallback(() => setBanner(null), [])

  useEffect(() => {
    api('/samples')
      .then((list) => { if (Array.isArray(list) && list.length) setSamples(list) })
      .catch(() => {})
  }, [])

  async function receive() {
    setLoading(true)
    setError('')
    setBanner(null)
    setSafeNotice(false)
    try {
      const res = await api('/simulate/incoming', {
        method: 'POST',
        body: JSON.stringify({ text, sender: '010-1234-5678' }),
      })
      if (res.notified && res.notification) setBanner(res)
      else setSafeNotice(true)
    } catch {
      setError('분석에 실패했어요. 잠시 후 다시 시도해 주세요.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="page">
      {banner && (
        <NotificationBanner
          level={banner.level}
          notification={banner.notification}
          onOpen={(url) => navigate(url)}
          onClose={closeBanner}
        />
      )}
      <h1 className="title">문자 수신 시뮬레이터</h1>
      <p className="muted">샘플을 고르거나 직접 입력한 뒤 문자를 받아 보세요.</p>

      <div className="samples">
        {samples.map((s) => (
          <button key={s.id || s.label} type="button" className="chip" onClick={() => setText(s.text)}>
            {s.label}
          </button>
        ))}
      </div>

      <label htmlFor="msg" className="sr-only">문자 내용</label>
      <textarea
        id="msg"
        value={text}
        maxLength={2000}
        rows={6}
        placeholder="문자 내용을 입력하세요"
        onChange={(e) => setText(e.target.value)}
      />
      <div className="count">{text.length}/2000</div>

      <button type="button" className="primary" disabled={loading || !text.trim()} onClick={receive}>
        {loading ? '분석 중…' : '문자 받기'}
      </button>

      {error && <p className="error" role="alert">{error}</p>}
      {safeNotice && <p className="safe-notice">✅ 위험 신호가 발견되지 않았어요</p>}
    </main>
  )
}
