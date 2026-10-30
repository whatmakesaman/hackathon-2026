// 프론트 2 담당
// 서버 위치값은 코드포인트 기준이라 Array.from으로 잘라 이모지가 섞여도 맞춘다.
export function splitByRanges(text, ranges) {
  const chars = Array.from(text)
  const sorted = ranges
    .map((r) => ({ start: Math.max(0, r.start), end: Math.min(chars.length, r.end) }))
    .filter((r) => r.end > r.start)
    .sort((a, b) => a.start - b.start)
  const merged = []
  for (const r of sorted) {
    const last = merged[merged.length - 1]
    if (last && r.start <= last.end) last.end = Math.max(last.end, r.end)
    else merged.push({ ...r })
  }
  const parts = []
  let cursor = 0
  for (const m of merged) {
    if (m.start > cursor) parts.push({ text: chars.slice(cursor, m.start).join(''), hit: false })
    parts.push({ text: chars.slice(m.start, m.end).join(''), hit: true })
    cursor = m.end
  }
  if (cursor < chars.length) parts.push({ text: chars.slice(cursor).join(''), hit: false })
  return parts
}

// 원문은 텍스트로만 렌더한다(링크 클릭 불가, innerHTML 사용 안 함).
export default function HighlightedText({ text = '', signals = [] }) {
  const parts = splitByRanges(text, signals)
  return (
    <section className="card" aria-label="문자 원문">
      <p className="highlighted">
        {parts.map((p, i) =>
          p.hit ? <mark key={i} className="highlighted__hit">{p.text}</mark> : <span key={i}>{p.text}</span>
        )}
      </p>
    </section>
  )
}
