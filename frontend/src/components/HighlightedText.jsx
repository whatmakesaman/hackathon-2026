// 서버 위치는 코드포인트 기준이므로 Array.from으로 나눠 이모지가 섞여도 어긋나지 않게 한다.
export function splitByRanges(text, ranges) {
  const chars = Array.from(text)
  const sorted = [...ranges].sort((a, b) => a.start - b.start)
  const merged = []
  for (const r of sorted) {
    const last = merged[merged.length - 1]
    if (last && r.start <= last.end) last.end = Math.max(last.end, r.end)
    else merged.push({ start: r.start, end: r.end })
  }
  const parts = []
  let cursor = 0
  for (const m of merged) {
    const start = Math.min(m.start, chars.length)
    const end = Math.min(m.end, chars.length)
    if (start > cursor) parts.push({ text: chars.slice(cursor, start).join(''), hit: false })
    if (end > start) parts.push({ text: chars.slice(start, end).join(''), hit: true })
    cursor = Math.max(cursor, end)
  }
  if (cursor < chars.length) parts.push({ text: chars.slice(cursor).join(''), hit: false })
  return parts
}

// 원문은 텍스트로만 렌더한다 (링크화, innerHTML 금지).
export default function HighlightedText({ text, signals }) {
  const parts = splitByRanges(text, signals)
  return (
    <p className="message">
      {parts.map((p, i) => (p.hit ? <mark key={i}>{p.text}</mark> : <span key={i}>{p.text}</span>))}
    </p>
  )
}
