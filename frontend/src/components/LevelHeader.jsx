// 프론트 2 담당
import { toneOf, toneVars } from '../tones'

// 점수 구간(docs/API.md): 안전 0~29 / 주의 30~59 / 위험 60~ → 10칸 기준 3·3·4칸
const ZONES = [
  { level: 'safe', label: '안전', span: 3 },
  { level: 'caution', label: '주의', span: 3 },
  { level: 'danger', label: '위험', span: 4 },
]

function headline(level, category) {
  if (level === 'safe') return '위험 신호가 없어요'
  const named = category && category !== '기타 의심' && category !== '정상'
  if (level === 'danger') return named ? `${category} 문자로 보여요` : '위험한 문자로 보여요'
  return named ? `${category}일 수 있어요` : '확인이 필요한 문자예요'
}

export default function LevelHeader({ level, category, score = 0, lead }) {
  const tone = toneOf(level)
  const filled = Math.min(10, Math.ceil(score / 10))
  const showCategory = category && category !== '정상'

  return (
    <section className="verdict" style={toneVars(level)} aria-label="판정 결과">
      <div className="verdict__top">
        <div className="verdict__head">
          <span className="verdict__chip">
            <span className="verdict__dot" aria-hidden="true" />
            {tone.label}
            {showCategory && ` · ${category}`}
          </span>
          <h1 className="verdict__title">{headline(level, category)}</h1>
        </div>
        <p className="verdict__score" aria-label={`의심 점수 100점 중 ${score}점`}>
          <strong>{score}</strong>
          <span>/100</span>
        </p>
      </div>

      <div className="meter" role="img" aria-label={`위험도 ${tone.label} 구간`}>
        <div className="meter__cells">
          {Array.from({ length: 10 }, (_, i) => (
            <span key={i} className={i < filled ? 'meter__cell is-filled' : 'meter__cell'} />
          ))}
        </div>
        <div className="meter__zones" aria-hidden="true">
          {ZONES.map((z) => (
            <span
              key={z.level}
              className={z.level === level ? 'meter__zone is-current' : 'meter__zone'}
              style={{ gridColumn: `span ${z.span}` }}
            >
              {z.label}
            </span>
          ))}
        </div>
      </div>

      {lead && <p className="verdict__lead">{lead}</p>}
    </section>
  )
}
