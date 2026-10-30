export default function SignalList({ signals }) {
  if (!signals.length) return <p className="muted">발견된 위험 신호가 없어요.</p>
  return (
    <ul className="signals">
      {signals.map((s, i) => (
        <li key={`${s.rule_id}-${i}`}>
          <div className="signal-top">
            <strong>{s.type}</strong>
            <span className="weight">+{s.weight}</span>
          </div>
          <p>{s.explain}</p>
        </li>
      ))}
    </ul>
  )
}
