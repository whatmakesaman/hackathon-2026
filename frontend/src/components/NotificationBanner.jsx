import { useEffect } from 'react'
import { toneOf, toneVars } from '../tones'
import './NotificationBanner.css'

// 서버 제목에 붙은 이모지(⚠️ 등)는 아이콘과 겹치므로 화면에서만 떼어낸다.
function cleanTitle(title = '') {
  return title.replace(/^[^\p{L}\p{N}]+/u, '').trim()
}

export default function NotificationBanner({ level, notification, onOpen, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 6000)
    return () => clearTimeout(t)
  }, [notification, onClose])

  const tone = toneOf(level)
  return (
    <button
      type="button"
      className="noti"
      style={toneVars(level)}
      onClick={() => onOpen(notification.url)}
      role="alert"
    >
      <span className="noti__icon" aria-hidden="true">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6l8-3z" /><path d="M12 8v5" /><path d="M12 16h.01" />
        </svg>
      </span>
      <span className="noti__body">
        <span className="noti__top">
          <strong className="noti__title">{cleanTitle(notification.title)}</strong>
          <span className="noti__level">{tone.label}</span>
          <span className="noti__time">지금</span>
        </span>
        <span className="noti__text">{notification.body}</span>
      </span>
    </button>
  )
}
