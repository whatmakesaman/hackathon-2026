// 프론트 2 담당: 결과 화면(/result/:id)
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import LevelHeader from '../components/LevelHeader'
import HighlightedText from '../components/HighlightedText'
import SignalList from '../components/SignalList'
import AdviceList from '../components/AdviceList'
import ClickedGuide from '../components/ClickedGuide'
import ExpiredNotice from '../components/ExpiredNotice'
import './Result.css'

export default function Result() {
  const { id } = useParams()
  const [state, setState] = useState({ status: 'loading' })

  const load = useCallback(() => {
    setState({ status: 'loading' })
    api(`/result/${id}`)
      .then((data) => setState({ status: 'ok', data }))
      .catch((e) => setState({ status: e.status === 404 ? 'expired' : 'error' }))
  }, [id])

  useEffect(() => { load() }, [load])

  if (state.status === 'loading') return <main className="result"><p className="result__loading">불러오는 중…</p></main>
  if (state.status === 'expired') return <main className="result"><ExpiredNotice /></main>
  if (state.status === 'error')
    return <main className="result"><ExpiredNotice message="잠시 후 다시 시도해주세요" retry={load} /></main>

  const r = state.data
  return (
    <main className="result">
      <LevelHeader level={r.level} category={r.category} score={r.score} />
      <HighlightedText text={r.text} signals={r.signals || []} />
      <SignalList signals={r.signals || []} />
      <AdviceList advice={r.advice || []} />
      {r.level !== 'safe' && <ClickedGuide items={r.if_clicked || []} />}
      <footer className="result__footer">
        <p>100% 판별은 아니에요. 의심되면 공식 채널로 확인하세요.</p>
        <Link to="/" className="btn">다시 해보기</Link>
      </footer>
    </main>
  )
}
