// 프론트 2 담당
// 서버 위치값은 코드포인트 기준이라 Array.from으로 잘라 이모지가 섞여도 맞춘다.
// 신호마다 번호를 붙이기 위해, 잡힌 구간이 어느 신호(index)인지 함께 돌려준다.
// 구간이 겹치면 먼저 시작한 신호가 차지하고, 뒤 신호는 겹치지 않는 부분만 남긴다.
export function splitBySignals(text, signals) {
  const chars = Array.from(text)
  const ranges = signals
    .map((s, index) => ({ index, start: s.start, end: s.end }))
    .filter((r) => Number.isInteger(r.start) && Number.isInteger(r.end))
    .map((r) => ({ ...r, start: Math.max(0, r.start), end: Math.min(chars.length, r.end) }))
    .filter((r) => r.end > r.start)
    .sort((a, b) => a.start - b.start)

  const parts = []
  let cursor = 0
  for (const r of ranges) {
    const start = Math.max(r.start, cursor)
    if (r.end <= start) continue
    if (start > cursor) parts.push({ text: chars.slice(cursor, start).join(''), index: null })
    parts.push({ text: chars.slice(start, r.end).join(''), index: r.index })
    cursor = r.end
  }
  if (cursor < chars.length) parts.push({ text: chars.slice(cursor).join(''), index: null })
  return parts
}

// 원문은 텍스트로만 렌더한다(링크 클릭 불가, innerHTML 사용 안 함).
export default function HighlightedText({ text = '', signals = [], active = null }) {
  const parts = splitBySignals(text, signals)
  return (
    <p className="bubble" aria-label="받은 문자 원문">
      {parts.map((p, i) =>
        p.index === null ? (
          <span key={i}>{p.text}</span>
        ) : (
          <span key={i}>
            <mark className={p.index === active ? 'hl is-active' : 'hl'}>{p.text}</mark>
            <span className={p.index === active ? 'hl__num is-active' : 'hl__num'} aria-hidden="true">
              {p.index + 1}
            </span>
          </span>
        )
      )}
    </p>
  )
}
