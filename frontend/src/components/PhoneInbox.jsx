// 수신 폰 화면: inbox(docs/TASK_B_phone.md "공용 약속" 모양)를 말풍선으로 그리고, 알림 대상이면 1초 뒤 경고 배너를 띄운다.
// 분석은 다시 요청하지 않는다. 문자에 담겨 온 result만 쓴다.
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import NotificationBanner from './NotificationBanner'
import { LEVELS } from '../levels'
import './PhoneInbox.css'

const BANNER_DELAY_MS = 1000
const SENDER_MAX = 50

function formatTime(ms) {
  return new Date(ms).toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit' })
}

function shortSender(sender) {
  return Array.from(sender || '알 수 없음').slice(0, SENDER_MAX).join('')
}

function shouldAlert(m) {
  const r = m.result
  return Boolean(r && r.notified && r.notification && r.level !== 'safe' && LEVELS[r.level])
}

// danger만 소리·진동을 낸다(docs/API.md 위험 등급 표). 브라우저가 막아도 화면 배너는 그대로 뜬다.
function ringDanger() {
  try { navigator.vibrate?.([200, 100, 200]) } catch { /* 진동 미지원 */ }
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext
    if (!Ctx) return
    const ctx = new Ctx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'square'
    osc.frequency.value = 880
    gain.gain.setValueAtTime(0.08, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.4)
    osc.connect(gain).connect(ctx.destination)
    osc.onended = () => ctx.close()
    osc.start()
    osc.stop(ctx.currentTime + 0.4)
  } catch { /* 자동 재생이 막힌 경우 */ }
}

function useClock() {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 30000)
    return () => clearInterval(t)
  }, [])
  return now
}

export default function PhoneInbox({ inbox = [] }) {
  const navigate = useNavigate()
  const now = useClock()
  const [banner, setBanner] = useState(null)
  const seen = useRef(null)
  const timers = useRef([])
  const listRef = useRef(null)
  const closeBanner = useCallback(() => setBanner(null), [])

  useEffect(() => () => timers.current.forEach(clearTimeout), [])

  useEffect(() => {
    // 처음 그릴 때 이미 있던 문자는 알림 없이 보여준다. (결과 화면에서 돌아왔을 때 배너가 다시 뜨지 않게)
    if (seen.current === null) {
      seen.current = new Set(inbox.map((m) => m.id))
      return
    }
    const fresh = inbox.filter((m) => !seen.current.has(m.id))
    fresh.forEach((m) => seen.current.add(m.id))
    fresh.filter(shouldAlert).forEach((m) => {
      timers.current.push(setTimeout(() => {
        setBanner(m)
        if (m.result.level === 'danger') ringDanger()
      }, BANNER_DELAY_MS))
    })
  }, [inbox])

  useEffect(() => {
    const el = listRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [inbox.length])

  return (
    <section className="phone" aria-label="수신 폰 화면">
      <div className="phone__screen">
        <div className="phone__status" aria-hidden="true">
          <span>{formatTime(now)}</span>
          <span className="phone__status-icons">LTE ▮▮▮ 🔋</span>
        </div>
        <header className="phone__header">메시지</header>

        {banner && (
          <div key={banner.id} className={`phone__banner phone__banner--${banner.result.level}`}>
            <NotificationBanner
              level={banner.result.level}
              notification={banner.result.notification}
              onOpen={() => navigate(`/result/${encodeURIComponent(banner.result.result_id)}`)}
              onClose={closeBanner}
            />
          </div>
        )}

        {/* 문자 본문과 발신번호는 공격자가 넣은 값이라 텍스트로만 그린다. (innerHTML 사용 안 함) */}
        <ol className="phone__list" ref={listRef} aria-live="polite">
          {inbox.length === 0 && <li className="phone__empty">받은 문자가 없어요</li>}
          {inbox.map((m) => (
            <li key={m.id} className="bubble">
              <div className="bubble__meta">
                <span className="bubble__sender">{shortSender(m.sender)}</span>
                <time dateTime={new Date(m.receivedAt).toISOString()}>{formatTime(m.receivedAt)}</time>
              </div>
              <p className="bubble__text">{m.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
