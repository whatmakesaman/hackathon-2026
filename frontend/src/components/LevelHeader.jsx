// 프론트 2 담당
import { LEVELS } from '../levels'

export default function LevelHeader({ level, category, score }) {
  const lv = LEVELS[level] || LEVELS.caution
  return (
    <header className="level-header" style={{ background: lv.bg, color: lv.color }}>
      <span className="level-header__icon" aria-hidden="true">{lv.icon}</span>
      <div className="level-header__body">
        <h1 className="level-header__title">
          {lv.label}
          {category && <span className="level-header__category"> · {category}</span>}
        </h1>
      </div>
      <span className="level-header__score">{score}점</span>
    </header>
  )
}
