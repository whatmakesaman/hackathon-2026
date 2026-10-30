import { LEVELS } from '../levels'

export default function LevelHeader({ level, category, score }) {
  const lv = LEVELS[level]
  return (
    <header className={`level-header ${lv.cls}`}>
      <div className="level-icon" aria-hidden="true">{lv.icon}</div>
      <div>
        <h1>{lv.label}{level === 'safe' ? '' : ' · 스팸 의심'}</h1>
        <p>{category}</p>
      </div>
      <small className="score">점수 {score}</small>
    </header>
  )
}
