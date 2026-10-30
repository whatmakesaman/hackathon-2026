// 결과 화면·알림 배너가 함께 쓰는 등급별 색. (levels.js의 이모지 아이콘 대신 SVG를 쓰는 새 디자인용)
export const TONES = {
  safe: { label: '안전', text: '#2b8a3e', fill: '#40c057', soft: '#ebfbee' },
  caution: { label: '주의', text: '#a63f08', fill: '#f76707', soft: '#fff1e6' },
  danger: { label: '위험', text: '#c92a2a', fill: '#e03131', soft: '#fff5f5' },
}

export function toneOf(level) {
  return TONES[level] || TONES.caution
}

// 컴포넌트 style에 넣어 CSS 변수로 색을 넘긴다.
export function toneVars(level) {
  const t = toneOf(level)
  return { '--tone-text': t.text, '--tone-fill': t.fill, '--tone-soft': t.soft }
}
