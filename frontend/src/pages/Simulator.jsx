import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { samples as mockSamples } from '../mocks/sample'
import NotificationBanner from '../components/NotificationBanner'
import './Simulator.css'

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
    <main className="sim">
      {banner && (
        <NotificationBanner
          level={banner.level}
          notification={banner.notification}
          onOpen={(url) => navigate(url)}
          onClose={closeBanner}
        />
      )}
      <header className="sim__head">
        <h1 className="sim__title">문자 수신 시뮬레이터</h1>
        <p className="sim__sub">문자를 받으면 알림이 뜨고, 알림을 누르면 결과 화면이 열려요.</p>
      </header>

      <div className="sim__samples" role="group" aria-label="샘플 문자">
        {samples.map((s) => (
          <button
            key={s.id || s.label}
            type="button"
            className="sim__chip"
            aria-pressed={text === s.text}
            onClick={() => setText(s.text)}
          >
            {s.label}
          </button>
        ))}
      </div>

      <section className="sim__card">
        <label htmlFor="msg" className="sim__label">받을 문자</label>
        <textarea
          id="msg"
          className="sim__input"
          value={text}
          maxLength={2000}
          rows={6}
          placeholder="샘플을 고르거나 문자 내용을 입력하세요"
          onChange={(e) => setText(e.target.value)}
        />
        <div className="sim__count">{text.length}/2000</div>
      </section>

      <button type="button" className="sim__receive" disabled={loading || !text.trim()} onClick={receive}>
        {loading ? '분석 중…' : '문자 받기'}
      </button>

      {error && <p className="sim__error" role="alert">{error}</p>}
      {safeNotice && <p className="sim__safe" role="status">위험 신호가 발견되지 않아 알림을 보내지 않았어요</p>}
      {banner && <p className="sim__hint">위에 뜬 알림을 눌러 결과를 확인해 보세요</p>}
    </main>
  )
}
