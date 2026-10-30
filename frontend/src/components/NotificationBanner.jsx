import { useEffect } from 'react'
import { LEVELS } from '../levels'

export default function NotificationBanner({ level, notification, onOpen, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 6000)
    return () => clearTimeout(t)
  }, [notification, onClose])

  const lv = LEVELS[level]
  return (
    <button type="button" className={`banner ${lv.cls}`} onClick={() => onOpen(notification.url)} role="alert">
      <span className="banner-icon" aria-hidden="true">{lv.icon}</span>
      <span className="banner-text">
        <strong>{notification.title}</strong>
        <span>{notification.body}</span>
      </span>
    </button>
  )
}
