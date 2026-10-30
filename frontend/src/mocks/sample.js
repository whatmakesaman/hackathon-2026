// 백엔드 준비 전 임시 데이터. VITE_USE_MOCK=true 일 때만 쓰이며, 제출 전에 끄거나 제거한다.

export const samples = [
  { label: '택배 사칭 (위험)', sender: '010-1234-5678', text: '[Web발신] 택배 주소 확인 http://bit.ly/xxx 😀 지금 확인하세요' },
  { label: '무료 당첨 (위험)', sender: '1588-0000', text: '[Web발신] 축하합니다! 100% 무료 상품권 당첨. http://win-prize.xyz 에서 수령하세요' },
  { label: '배송 안내 (주의)', sender: '1577-1111', text: '[Web발신] 고객님의 상품이 배송 예정입니다. 자세한 내용은 앱에서 확인하세요 www.example.com' },
  { label: '친구 약속 (안전)', sender: '010-9999-8888', text: '내일 저녁 7시에 강남역에서 보자. 늦지 마!' },
]

const ADVICE = {
  danger: ['링크를 누르지 마세요', '공식 앱에서 직접 조회하세요'],
  caution: ['발신처를 확인하세요', '링크 대신 공식 앱을 이용하세요'],
  safe: [],
}
const IF_CLICKED = ['앱을 설치했다면 삭제하세요', '비밀번호를 변경하세요', '118에 상담하세요']

function find(text, needle) {
  const cps = Array.from(text)
  const idx = text.indexOf(needle)
  if (idx < 0) return null
  const start = Array.from(text.slice(0, idx)).length
  return { start, end: start + Array.from(needle).length }
}

function signal(text, needle, rule_id, type, weight, explain) {
  const pos = find(text, needle)
  return pos ? [{ rule_id, type, detail: needle, weight, explain, ...pos }] : []
}

function analyze(text) {
  const signals = [
    ...signal(text, 'http://bit.ly/xxx', 'short_url', '단축URL', 50, '실제 주소를 숨길 수 있어요'),
    ...signal(text, 'http://win-prize.xyz', 'odd_domain', '의심 도메인', 40, '공식 기관이 쓰지 않는 주소예요'),
    ...signal(text, '무료', 'free', '무료 유도', 15, '공짜 혜택으로 클릭을 유도해요'),
    ...signal(text, '당첨', 'prize', '당첨 유도', 20, '당첨 사칭은 대표적인 스미싱 수법이에요'),
    ...signal(text, 'www.example.com', 'plain_url', '링크 포함', 20, '출처를 알 수 없는 링크예요'),
  ]
  const score = Math.min(100, signals.reduce((s, x) => s + x.weight, 0) + (signals.length ? 20 : 0))
  const level = score >= 60 ? 'danger' : score >= 30 ? 'caution' : 'safe'
  const category = level === 'safe' ? '정상' : text.includes('택배') || text.includes('배송') ? '택배·기관 사칭' : '기타 의심'
  return { score, level, category, signals, advice: ADVICE[level], if_clicked: IF_CLICKED }
}

const store = new Map()
const TTL = 600

export async function mockApi(path, options) {
  await new Promise((r) => setTimeout(r, 400))
  if (path === '/simulate/incoming') {
    const { text } = JSON.parse(options.body)
    const result = analyze(text)
    const id = Math.random().toString(16).slice(2, 10)
    store.set(id, { text, at: Date.now(), ...result })
    const notified = result.level !== 'safe'
    return {
      result_id: id,
      level: result.level,
      category: result.category,
      notified,
      notification: notified
        ? {
            title: result.level === 'danger' ? '⚠️ 스팸 의심 문자' : '확인이 필요한 문자',
            body: `${result.category} · ${result.signals.map((s) => s.type).join(', ')}. 링크를 누르지 마세요`,
            url: `/result/${id}`,
          }
        : null,
    }
  }
  const m = path.match(/^\/result\/(.+)$/)
  if (m) {
    const r = store.get(m[1])
    const left = r ? TTL - Math.floor((Date.now() - r.at) / 1000) : 0
    if (!r || left <= 0) throw Object.assign(new Error('not found'), { status: 404 })
    // 저장 시각(at)은 내부용이라 응답에 넣지 않는다. (docs/API.md)
    const { at, ...rest } = r
    return { result_id: m[1], ...rest, expires_in: left }
  }
  throw Object.assign(new Error('not found'), { status: 404 })
}
