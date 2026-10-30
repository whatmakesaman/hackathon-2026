// 프론트 2 담당
// 문자 속 주소를 열지 않고 글자만 나눠서 보여준다. 판정(점수)에는 쓰지 않는 화면용 설명이다.

const URL_RE = /(?:https?:\/\/)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?::\d+)?(?:\/[^\s]*)?/gi
const SHORTENERS = ['bit.ly', 'han.gl', 'me2.kr', 'url.kr', 't.ly', 'tinyurl.com', 'goo.gl', 'vo.la', 'buly.kr', 'is.gd']

export function findUrls(text, limit = 2) {
  const found = []
  for (const m of text.matchAll(URL_RE)) {
    const url = m[0].replace(/[.,!?)\]}'"]+$/, '')
    if (!found.includes(url)) found.push(url)
    if (found.length >= limit) break
  }
  return found
}

export function splitUrl(url) {
  const protocol = (url.match(/^https?:\/\//i) || [''])[0]
  const rest = url.slice(protocol.length)
  const slash = rest.indexOf('/')
  const host = slash < 0 ? rest : rest.slice(0, slash)
  const path = slash < 0 ? '' : rest.slice(slash)
  return { protocol, host, path }
}

function describe({ protocol, host, path }) {
  const rows = []
  if (/^http:/i.test(protocol)) rows.push({ part: protocol, note: '암호화되지 않은 연결이에요' })
  else if (protocol) rows.push({ part: protocol, note: '암호화 연결이지만, 안전한 사이트라는 뜻은 아니에요' })
  else rows.push({ part: '(생략)', note: '주소 앞부분이 빠져 있어요' })

  const bare = host.toLowerCase().replace(/^www\./, '').replace(/:\d+$/, '')
  rows.push(
    SHORTENERS.includes(bare)
      ? { part: host, note: '단축 주소라 실제로 어디로 가는지 숨겨져 있어요', strong: true }
      : { part: host, note: '실제로 접속되는 주소예요. 공식 주소와 한 글자씩 비교해 보세요', strong: true }
  )

  if (path && path !== '/') rows.push({ part: path, note: '세부 경로예요. 받는 사람마다 다르게 만들어 누가 눌렀는지 구분하기도 해요' })
  return rows
}

export default function LinkAnatomy({ text = '' }) {
  const urls = findUrls(text)
  if (urls.length === 0) return null

  return (
    <section className="panel" aria-labelledby="anatomy-title">
      <div className="panel__head">
        <h2 id="anatomy-title" className="panel__title">링크 해부</h2>
        <p className="panel__sub">열지 않고 주소만 읽어서 나눴어요</p>
      </div>
      {urls.map((url) => {
        const parts = splitUrl(url)
        return (
          <div key={url} className="anatomy">
            <p className="anatomy__url">
              <span className="anatomy__protocol">{parts.protocol}</span>
              <span className="anatomy__host">{parts.host}</span>
              <span className="anatomy__path">{parts.path}</span>
            </p>
            <dl className="anatomy__rows">
              {describe(parts).map((row) => (
                <div key={row.part} className="anatomy__row">
                  <dt className={row.strong ? 'anatomy__part is-strong' : 'anatomy__part'}>{row.part}</dt>
                  <dd className="anatomy__note">{row.note}</dd>
                </div>
              ))}
            </dl>
          </div>
        )
      })}
    </section>
  )
}
