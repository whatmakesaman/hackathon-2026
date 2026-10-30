export default function AdviceList({ advice }) {
  if (!advice.length) return null
  return (
    <section className="card">
      <h2>이렇게 하세요</h2>
      <ol className="advice">
        {advice.map((a, i) => <li key={i}>{a}</li>)}
      </ol>
    </section>
  )
}
