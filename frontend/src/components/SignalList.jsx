// 프론트 2 담당
export default function SignalList({ signals = [] }) {
  return (
    <section className="card">
      <h2 className="card__title">왜 위험한가요?</h2>
      {signals.length === 0 ? (
        <p className="card__empty">위험 신호가 발견되지 않았어요</p>
      ) : (
        <ul className="signals">
          {signals.map((s, i) => (
            <li key={`${s.rule_id}-${i}`} className="signals__item">
              <div className="signals__head">
                <strong>{s.type}</strong>
                <span className="signals__weight">{s.rule_id === 'model_pattern' ? '모델 판정' : '규칙 근거'}</span>
              </div>
              {s.detail && <code className="signals__detail">{s.detail}</code>}
              <p className="signals__explain">{s.explain}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
