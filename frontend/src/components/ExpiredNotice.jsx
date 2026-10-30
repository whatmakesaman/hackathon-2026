// 프론트 2 담당
import { Link } from 'react-router-dom'

export default function ExpiredNotice({ message = '시간이 지나 결과가 사라졌어요 (10분 보관)', retry }) {
  return (
    <section className="notice" role="alert">
      <span className="notice__icon" aria-hidden="true">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />
        </svg>
      </span>
      <p className="notice__text">{message}</p>
      <div className="notice__actions">
        {retry && <button type="button" className="btn btn--ghost" onClick={retry}>다시 불러오기</button>}
        <Link to="/" className="btn">시뮬레이터로 돌아가기</Link>
      </div>
    </section>
  )
}
