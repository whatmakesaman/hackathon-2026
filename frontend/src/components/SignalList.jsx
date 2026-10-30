// 프론트 2 담당
// 항목을 누르면 원문(HighlightedText)에서 같은 번호의 구간이 강조된다.
export default function SignalList({ signals = [], active = null, onPick }) {
  if (signals.length === 0) return <p className="reasons__empty">위험 신호가 발견되지 않았어요</p>

  return (
    <ul className="reasons">
      {signals.map((s, i) => {
        const on = i === active
        return (
          <li key={`${s.rule_id}-${i}`}>
            <button
              type="button"
              className={on ? 'reason is-active' : 'reason'}
              aria-pressed={on}
              onClick={() => onPick?.(i)}
            >
              <span className="reason__num" aria-hidden="true">{i + 1}</span>
              <span className="reason__body">
                <span className="reason__type">{s.type}</span>
                {s.explain && <span className="reason__explain">{s.explain}</span>}
                {s.detail && <code className="reason__detail">{s.detail}</code>}
              </span>
              <span className="reason__weight" aria-label={`${s.weight}점`}>+{s.weight}</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
