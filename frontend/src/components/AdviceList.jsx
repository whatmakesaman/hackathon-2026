// 프론트 2 담당
export default function AdviceList({ advice = [] }) {
  if (advice.length === 0) return null
  return (
    <section className="todo" aria-labelledby="todo-title">
      <h2 id="todo-title" className="todo__title">이렇게 하세요</h2>
      <ol className="todo__list">
        {advice.map((a, i) => (
          <li key={i} className="todo__item">
            <span className="todo__num" aria-hidden="true">{i + 1}</span>
            <span>{a}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}
