// 프론트 2 담당
export default function ClickedGuide({ items = [] }) {
  return (
    <details className="card clicked">
      <summary className="clicked__summary">이미 눌렀거나 송금했다면</summary>
      {items.length > 0 && (
        <ul className="clicked__list">
          {items.map((t, i) => <li key={i}>{t}</li>)}
        </ul>
      )}
      <p className="clicked__report">
        신고·상담: 한국인터넷진흥원 <strong>118</strong> (전화), 경찰청 <strong>112</strong>
      </p>
    </details>
  )
}
