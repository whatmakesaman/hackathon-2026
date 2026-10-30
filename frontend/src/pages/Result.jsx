import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import LevelHeader from '../components/LevelHeader'
import HighlightedText from '../components/HighlightedText'
import SignalList from '../components/SignalList'
import AdviceList from '../components/AdviceList'
import ClickedGuide from '../components/ClickedGuide'

export default function Result() {
  const { id } = useParams()
  const [state, setState] = useState({ status: 'loading' })

  useEffect(() => {
    let alive = true
    setState({ status: 'loading' })
    api(`/result/${id}`)
      .then((data) => alive && setState({ status: 'ok', data }))
      .catch((e) => alive && setState({ status: e.status === 404 ? 'expired' : 'error' }))
    return () => { alive = false }
  }, [id])

  if (state.status === 'loading') {
    return <main className="page"><p className="muted">분석 결과를 불러오는 중…</p></main>
  }

  if (state.status !== 'ok') {
    const expired = state.status === 'expired'
    return (
      <main className="page center">
        <h1 className="title">{expired ? '결과가 만료되었어요' : '결과를 불러오지 못했어요'}</h1>
        <p className="muted">
          {expired ? '분석 결과는 10분 동안만 보관돼요.' : '잠시 후 다시 시도해 주세요.'}
        </p>
        <Link to="/" className="primary link-btn">시뮬레이터로 돌아가기</Link>
      </main>
    )
  }

  const { data } = state
  return (
    <main className="page">
      <LevelHeader level={data.level} category={data.category} score={data.score} />
      <section className="card">
        <h2>받은 문자</h2>
        <HighlightedText text={data.text} signals={data.signals} />
      </section>
      <section className="card">
        <h2>위험 신호</h2>
        <SignalList signals={data.signals} />
      </section>
      <AdviceList advice={data.advice} />
      {data.level !== 'safe' && <ClickedGuide items={data.if_clicked} />}
      <p className="disclaimer">100% 판별은 아니에요. 의심되면 공식 채널로 확인하세요.</p>
      <Link to="/" className="primary link-btn">다시 해보기</Link>
    </main>
  )
}
