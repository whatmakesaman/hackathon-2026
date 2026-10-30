// 프론트 2 담당
// "이미 눌렀다면" 안내를 펼쳐서 한 단계씩 체크하게 한다. 체크 상태는 화면에만 있고 서버로 보내지 않는다.
import { useId, useState } from 'react'

export default function ClickedGuide({ items = [] }) {
  const [open, setOpen] = useState(false)
  const [done, setDone] = useState(() => new Set())
  const panelId = useId()

  function toggle(i) {
    setDone((prev) => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }

  const allDone = items.length > 0 && done.size === items.length

  return (
    <section className={open ? 'clicked is-open' : 'clicked'}>
      <button
        type="button"
        className="clicked__toggle"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="clicked__icon" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 9v4" /><path d="M12 17h.01" />
            <path d="M10.3 3.9L2.4 17.5A2 2 0 0 0 4.1 20.5h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
          </svg>
        </span>
        <span className="clicked__label">
          <strong>이미 링크를 눌렀거나 송금했어요</strong>
          <span>지금 할 일을 순서대로 알려드려요</span>
        </span>
        <svg className="clicked__chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div id={panelId} className="clicked__panel">
          {items.length > 0 && (
            <>
              <ol className="steps">
                {items.map((t, i) => {
                  const on = done.has(i)
                  return (
                    <li key={i}>
                      <button type="button" className={on ? 'step is-done' : 'step'} aria-pressed={on} onClick={() => toggle(i)}>
                        <span className="step__box" aria-hidden="true">
                          {on ? (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12l5 5L20 7" /></svg>
                          ) : (
                            i + 1
                          )}
                        </span>
                        <span className="step__text">{t}</span>
                      </button>
                    </li>
                  )
                })}
              </ol>
              <p className="clicked__progress" aria-live="polite">
                {allDone ? '모두 마쳤어요. 이상한 결제나 문자가 오면 다시 확인해 주세요.' : `${items.length}단계 중 ${done.size}단계 완료`}
              </p>
            </>
          )}
          <div className="clicked__calls">
            <a className="call call--ghost" href="tel:112">112 경찰 신고</a>
            <a className="call" href="tel:118">118 상담 연결</a>
          </div>
        </div>
      )}
    </section>
  )
}
