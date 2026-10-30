// 개발용 미리보기(/phone): A의 2분할 화면이 들어오기 전까지 폰 화면만 따로 확인한다. 통합 후 지운다.
import { useState } from 'react'
import PhoneInbox from '../components/PhoneInbox'
import { makeMockMessage } from '../mocks/inbox'
import { api } from '../api'

export default function PhonePreview() {
  const [inbox, setInbox] = useState([])
  const [error, setError] = useState('')

  function addMock() {
    setInbox((list) => [...list, makeMockMessage(list.length)])
  }

  // 진짜 result_id로 배너→결과 화면 흐름을 보려고 서버 분석 결과를 그대로 담는다.
  async function addFromServer() {
    setError('')
    const mock = makeMockMessage(inbox.length)
    try {
      const result = await api('/simulate/incoming', {
        method: 'POST',
        body: JSON.stringify({ text: mock.text, sender: mock.sender }),
      })
      setInbox((list) => [...list, { ...mock, receivedAt: Date.now(), result }])
    } catch {
      setError('서버 연결에 실패했어요')
    }
  }

  return (
    <main className="page">
      <h1 className="title">폰 화면 미리보기</h1>
      <p className="muted">위험 → 주의 → 안전 → 보안 점검 문자 순서로 도착해요.</p>
      <div className="samples">
        <button type="button" className="chip" onClick={addMock}>목 문자 도착</button>
        <button type="button" className="chip" onClick={addFromServer}>서버 분석 문자 도착</button>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      <PhoneInbox inbox={inbox} />
    </main>
  )
}
