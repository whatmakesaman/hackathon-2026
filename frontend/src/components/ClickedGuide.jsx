export default function ClickedGuide({ items }) {
  return (
    <details className="card guide">
      <summary>이미 눌렀거나 송금했다면</summary>
      <ol className="advice">
        {items.map((a, i) => <li key={i}>{a}</li>)}
      </ol>
      <p className="muted">
        신고·상담: 한국인터넷진흥원 <a href="tel:118">118</a> ·{' '}
        <a href="https://www.boho.or.kr" target="_blank" rel="noopener noreferrer">boho.or.kr</a>
      </p>
    </details>
  )
}
