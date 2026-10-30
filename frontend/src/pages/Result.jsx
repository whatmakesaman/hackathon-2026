// 프론트 2 담당: 결과 화면(/result/:id)
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { toneVars } from '../tones'
import LevelHeader from '../components/LevelHeader'
import HighlightedText from '../components/HighlightedText'
import SignalList from '../components/SignalList'
import AdviceList from '../components/AdviceList'
import ClickedGuide from '../components/ClickedGuide'
import ExpiredNotice from '../components/ExpiredNotice'
import './Result.css'

const LEAD = {
  danger: '문자 속 링크는 누르지 말고, 아래 안내를 따라 주세요.',
  caution: '보낸 곳이 확실해질 때까지 링크와 전화번호는 쓰지 마세요.',
  safe: '그래도 모르는 링크나 송금 요청은 한 번 더 확인하세요.',
}

// 처음엔 원문에서 위치를 찾을 수 있는 첫 신호를 강조해 둔다.
function firstLocated(signals) {
  const i = signals.findIndex((s) => Number.isInteger(s.start) && Number.isInteger(s.end))
  if (i >= 0) return i
  return signals.length ? 0 : null
}

function TopBar() {
  return (
    <header className="result__bar">
      <Link to="/" className="result__back" aria-label="시뮬레이터로 돌아가기">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M15 18l-6-6 6-6" />
        </svg>
      </Link>
      <span className="result__bar-title">문자 분석</span>
    </header>
  )
}

export default function Result() {
  const { id } = useParams()
  const [state, setState] = useState({ status: 'loading' })
  const [active, setActive] = useState(null)

  const load = useCallback(() => {
    setState({ status: 'loading' })
    api(`/result/${id}`)
      .then((data) => {
        setActive(firstLocated(data.signals || []))
        setState({ status: 'ok', data })
      })
      .catch((e) => setState({ status: e.status === 404 ? 'expired' : 'error' }))
  }, [id])

  useEffect(() => { load() }, [load])

  if (state.status !== 'ok') {
    return (
      <main className="result">
        <TopBar />
        {state.status === 'loading' && <p className="result__loading">불러오는 중…</p>}
        {state.status === 'expired' && <ExpiredNotice />}
        {state.status === 'error' && <ExpiredNotice message="잠시 후 다시 시도해주세요" retry={load} />}
      </main>
    )
  }

  const r = state.data
  const signals = r.signals || []
  const minutesLeft = Number.isFinite(r.expires_in) ? Math.max(1, Math.ceil(r.expires_in / 60)) : null

  return (
    <main className="result" style={toneVars(r.level)}>
      <TopBar />

      <LevelHeader level={r.level} category={r.category} score={r.score} lead={LEAD[r.level]} />

      <section className="panel" aria-labelledby="why-title">
        <div className="panel__head panel__head--row">
          <h2 id="why-title" className="panel__title">{signals.length ? '왜 의심되나요' : '분석한 문자'}</h2>
          {signals.length > 0 && <p className="panel__sub">항목을 누르면 문자에서 찾아줘요</p>}
        </div>
        <div className="message">
          <p className="message__meta">
            받은 문자{minutesLeft && ` · ${minutesLeft}분 뒤 결과가 사라져요`}
          </p>
          <HighlightedText text={r.text} signals={signals} active={active} />
        </div>
        <SignalList signals={signals} active={active} onPick={setActive} />
      </section>

      <AdviceList advice={r.advice || []} />

      {r.level !== 'safe' && <ClickedGuide items={r.if_clicked || []} />}

      <p className="result__disclaimer">100% 판별은 아니에요. 의심되면 공식 채널로 확인하세요.</p>

      <footer className="result__footer">
        <Link to="/" className="btn btn--block">다른 문자 받아보기</Link>
      </footer>
    </main>
  )
}
