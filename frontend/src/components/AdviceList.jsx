// 프론트 2 담당
export default function AdviceList({ advice = [] }) {
  if (advice.length === 0) return null
  return (
    <section className="card">
      <h2 className="card__title">이렇게 하세요</h2>
      <ol className="advice">
        {advice.map((a, i) => <li key={i}>{a}</li>)}
      </ol>
    </section>
  )
}
