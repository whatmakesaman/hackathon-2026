// A의 수신함 코드가 올라오기 전까지 쓰는 목 문자. 모양은 docs/TASK_B_phone.md "공용 약속"과 같다.
// result_id가 가짜라서 배너를 누르면 결과 화면이 만료(404) 안내를 보여준다.

const TEMPLATES = [
  {
    sender: '010-1234-5678',
    text: '[Web발신] 택배 주소 확인 http://bit.ly/xxx 😀 지금 확인하세요',
    result: {
      result_id: 'mock-danger',
      level: 'danger',
      category: '택배·기관 사칭',
      notified: true,
      notification: { title: '⚠️ 스팸 의심 문자', body: '택배·기관 사칭 · 단축URL. 링크를 누르지 마세요', url: '/result/mock-danger' },
    },
  },
  {
    sender: '1577-1111',
    text: '[Web발신] 고객님의 상품이 배송 예정입니다. 자세한 내용은 앱에서 확인하세요 www.example.com',
    result: {
      result_id: 'mock-caution',
      level: 'caution',
      category: '기타 의심',
      notified: true,
      notification: { title: '확인이 필요한 문자', body: '의심스러운 표현이 있어요. 눌러서 확인하기', url: '/result/mock-caution' },
    },
  },
  {
    sender: '1588-2100',
    text: '[인증번호] 482913 를 입력해 주세요. 타인에게 절대 알려주지 마세요.',
    result: { result_id: 'mock-safe', level: 'safe', category: '정상', notified: false, notification: null },
  },
  {
    // 보안 점검(B6)용: 글자로만 보여야 한다.
    sender: '<img src=x onerror=alert(1)>',
    text: '<script>alert(1)</script> <img src=x onerror=alert(1)>',
    result: {
      result_id: 'mock-xss',
      level: 'danger',
      category: '기타 의심',
      notified: true,
      notification: { title: '⚠️ 스팸 의심 문자', body: '<b>굵게</b> 보이면 안 돼요', url: '/result/mock-xss' },
    },
  },
]

export function makeMockMessage(i) {
  const t = TEMPLATES[i % TEMPLATES.length]
  return { id: `mock-${i}-${Date.now()}`, sender: t.sender, text: t.text, receivedAt: Date.now(), result: { ...t.result } }
}
