// 프론트 2 담당
import { Link } from 'react-router-dom'

export default function ExpiredNotice({ message = '결과가 만료되었어요 (10분 보관)', retry }) {
  return (
    <section className="notice" role="alert">
      <p className="notice__icon" aria-hidden="true">⏰</p>
      <p className="notice__text">{message}</p>
      {retry && <button type="button" className="btn btn--ghost" onClick={retry}>다시 불러오기</button>}
      <Link to="/" className="btn">시뮬레이터로 돌아가기</Link>
    </section>
  )
}
