import { useCallback, useState } from 'react'

// 상위 화면에서 한 번 호출하고 발신 패널과 폰 화면에 같은 수신함을 전달한다.
export default function useInbox() {
  const [inbox, setInbox] = useState([])
  const addMessage = useCallback((message) => {
    setInbox((messages) => [...messages, message])
  }, [])

  return { inbox, addMessage }
}
