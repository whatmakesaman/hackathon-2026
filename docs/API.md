# API 명세서

스팸 문자 분석 웹 시제품의 백엔드(FastAPI) API입니다.
**이 문서가 프론트와 백엔드가 맞춰야 하는 기준입니다.** 바꿔야 한다면 먼저 이 문서를 고치고 팀 채널에 알립니다.

- 근거: 노션 `PoC 기능 명세서`, 프론트 `mocks/sample.js`, 백엔드 `notification.py`, `push_routes.py`, `scripts/demo.py`
- 가입·로그인·토큰 API는 **없습니다.** (노션 API 페이지의 `API 명세 (auth)`는 다른 프로젝트 템플릿이 남은 것이라 쓰지 않습니다)

## 1. 기본 정보

| 항목 | 내용 |
|---|---|
| 백엔드 주소 | `http://localhost:8000` (Swagger 테스트 화면: `/docs`) |
| 프론트 호출 주소 | `/api/...` → Vite 프록시가 `/api`를 **떼고** 백엔드로 전달 (`/api/samples` → `GET /samples`) |
| 형식 | 요청·응답 모두 JSON (UTF-8) |
| 인증 | 없음 |
| 저장 | DB·디스크에 저장하지 않음. 분석 결과는 서버 **메모리에만 10분** 보관 |
| CORS | `http://localhost:5173`, `http://localhost:3000`에서 `GET`, `POST` 허용 |

> **백엔드 라우트에는 `/api` 접두사를 붙이지 않습니다.** `/api`는 프론트 프록시가 붙이는 주소입니다.

## 2. 엔드포인트 한눈에 보기

| 메서드 | 경로 | 설명 | 단계 | 담당 |
|---|---|---|---|---|
| POST | `/analyze` | 문자를 분석해 결과를 바로 돌려줌 (저장·알림 없음) | 필수 | B |
| POST | `/simulate/incoming` | 문자 수신 시뮬레이션: 분석 → 저장 → 알림 판단 | 필수 | B |
| GET | `/result/{result_id}` | 저장된 분석 결과 조회 (10분 후 만료) | 필수 | B |
| GET | `/samples` | 시연용 샘플 문자 목록 | 필수 | B (내용은 C) |
| GET | `/push/vapid-public-key` | 웹 푸시 공개키 | 2단계 | D |
| POST | `/push/subscribe` | 웹 푸시 구독 등록 | 2단계 | D |

2단계 항목은 06:00까지 안 되면 포기하고, 앱 내 알림 배너로 시연합니다.

## 3. 공통 규칙

### 위험 등급 (`level`)

값은 **영어 소문자 3개만** 씁니다. 화면에 보이는 한글 이름("안전", "주의", "위험")은 프론트의 `levels.js`가 붙입니다.

| `level` | 화면 이름 | 점수 구간 | 알림 |
|---|---|---|---|
| `safe` | 안전 | 0 ~ 19 | 없음 |
| `caution` | 주의 | 20 ~ 59 | 조용히 |
| `danger` | 위험 | 60 이상 | 소리·진동 |

- 점수는 **0~100 정수의 위험 신호 점수**이며 사기 확률이 아닙니다. 모델이 경고한 문자는 `max(주의 기준, 규칙 점수)`로 표시합니다. 모델이 경고하지 않은 문자는 기존 모델의 안전 구간 점수를 유지합니다.
- 구간 경계값은 `rules.yaml`의 `levels`에서 정합니다. 현재값은 `caution: 20`, `danger: 60`입니다.

### 모델과 규칙의 역할

- 서버는 `backend/message_model.json.gz`를 시작할 때 한 번 읽습니다. CSV를 요청마다 읽거나 재학습하지 않습니다.
- 모델은 의심 문자 여부를 결정합니다. 모델이 경고하면 규칙 점수로 주의(20~59)·위험(60~100)을 구분합니다. 모델만 의심하고 규칙 근거가 없어도 최소 20점의 주의로 경고합니다. 모델이 안전으로 판정한 문자는 규칙만으로 경고하지 않습니다.
- `safe`는 유형 `정상`과 빈 `signals`, `advice`, `if_clicked`를 반환합니다.
- `caution`·`danger`에는 `rule_id: model_pattern`인 모델 안내 신호를 먼저 넣습니다. 원문 특정 위치를 원인으로 단정하지 않으므로 `start`, `end`는 `null`입니다.
- 나머지 신호는 등급을 구분하는 규칙 근거입니다. 안전 신호의 감점·0~100 제한·모델 경고의 최소 20점 때문에 표시된 양수 가중치 합계가 최종 점수와 다를 수 있습니다. 모델이 경고했지만 규칙으로 유형을 찾지 못하면 `category`는 `기타 의심`입니다.
- 데이터셋에는 주의·위험 정답이 없습니다. 이 구분은 규칙에 따른 서비스 정책이며, 실제 피해 정도나 등급별 정확도를 검증한 결과가 아닙니다. 모델 파일의 `training.test_metrics`는 학습 당시 모델 자체의 등급 집계이며, 현재 규칙 결합 등급 분포는 별도로 평가해야 합니다.
- 모델 파일이 없거나 정규화 코드와 맞지 않으면 시작 오류로 알립니다. README의 모델 재학습 명령으로 다시 생성합니다.

### AI 링크 분석 (`/analyze`, `/simulate/incoming`)

- 문자에 링크가 있고 `ANTHROPIC_API_KEY`(환경 변수 또는 루트 `.env`)가 있으면 Claude가 링크를 `malicious` / `suspicious` / `safe`로 판정합니다.
- AI는 링크에 **접속하지 않고** 주소 모양과 문자 맥락만 봅니다.
- `malicious`·`suspicious`면 `rule_id: ai_url` 신호를 `signals` 맨 앞에 넣습니다. `start`, `end`는 첫 번째 링크 위치입니다.
- 기본적으로 `score`는 바꾸지 않습니다. 모델이 `safe`인데 AI가 `malicious`면 모델 단독 탐지와 같이 최소 주의 점수(20점)의 `caution`으로 올립니다(유형 `기타 의심`).
- 키가 없거나 호출이 실패하면(8초 제한) AI 판정 없이 기존 결과를 그대로 돌려줍니다.

### 입력 제한

| 필드 | 규칙 |
|---|---|
| `text` | 필수, 1~2000자, 공백만 있는 값은 거부 |
| `sender` | 선택, 문자열(최대 50자). 표시용이며 분석에는 쓰지 않음 |

### 위치 값 (`start`, `end`)

- 원문(`text`) 기준 **글자 단위** 위치입니다. 이모지 하나는 **1글자**로 셉니다. (Python `str` 인덱스, JS `Array.from(text)` 기준. JS `string.length` 기준이 아닙니다)
- `end`는 **포함하지 않는** 끝 위치입니다. `text[start:end]`가 잡힌 부분과 같습니다.
- 문자 정규화(전각·공백 제거 등) 후 매칭했더라도 위치는 **원문 기준**으로 돌려줍니다.

### 개인정보

- 문자 원문은 **로그에 남기지 않습니다.**
- 푸시 알림 본문에는 원문을 넣지 않습니다. (유형 + 한 줄 요약만)

### 에러 응답

FastAPI 기본 형식을 씁니다.

| 상태 | 언제 | 응답 |
|---|---|---|
| 404 | `result_id`가 없거나 10분이 지나 만료됨 | `{"detail": "결과를 찾을 수 없거나 만료되었어요"}` |
| 422 | 입력 검증 실패 (`text` 누락·빈 값·공백뿐·2000자 초과) | FastAPI 기본 검증 오류 형식 |
| 500 | 서버 오류 | `{"detail": "..."}` (원문은 포함하지 않음) |

프론트는 **상태 코드로만** 구분합니다. (404 → "결과가 만료되었어요", 그 외 → "불러오지 못했어요")

## 4. 공통 객체

### Signal (감지한 위험 신호)

| 필드 | 타입 | 설명 |
|---|---|---|
| `rule_id` | string | `rules.yaml`의 규칙 `id` (예: `short_url`), 모델 안내 `model_pattern`, AI 링크 판정 `ai_url` |
| `type` | string | 화면에 보이는 짧은 이름 (예: `단축URL`) |
| `detail` | string | 규칙에서 발견한 원문 표현 또는 모델 판정 안내 문구 |
| `weight` | integer | 규칙의 가중치. 모델 통계 점수와 합산하지 않으며, 모델 안내 신호는 0 |
| `explain` | string | "왜 위험한지" 쉬운 말 한 줄 |
| `start` | integer \| null | 원문 기준 시작 위치. 위치가 없는 신호는 `null` |
| `end` | integer \| null | 원문 기준 끝 위치(미포함). 위치가 없는 신호는 `null` |

### Notification (알림 문구)

| 필드 | 타입 | 설명 |
|---|---|---|
| `title` | string | 알림 제목 |
| `body` | string | 알림 본문. **원문 미포함** |
| `url` | string | 누르면 이동할 **프론트 화면 주소** (`/result/{result_id}`) |

등급별 문구:

| `level` | `title` | `body` |
|---|---|---|
| `danger` | `⚠️ 스팸 의심 문자` | `{category} · {첫 번째 신호의 type}. 링크를 누르지 마세요` |
| `caution` | `확인이 필요한 문자` | `의심스러운 표현이 있어요. 눌러서 확인하기` |
| `safe` | 알림 없음 (`notification`은 `null`) | |

### Result (분석 결과)

| 필드 | 타입 | 설명 |
|---|---|---|
| `level` | string | `safe` / `caution` / `danger` |
| `score` | integer | 0~100 위험 신호 점수 (확률 아님) |
| `category` | string | 의심 유형. 아래 목록 중 하나 |
| `signals` | Signal[] | 감지한 신호. 없으면 `[]` |
| `advice` | string[] | "이렇게 하세요" 안내. `safe`면 `[]` |
| `if_clicked` | string[] | "이미 눌렀거나 송금했다면" 안내. `safe`면 `[]` |
| `ai_url` | object (선택) | AI 링크 판정 `{"verdict", "reason", "url"}`. 판정하지 않았으면 필드 없음 |

`category` 값:

| 값 | 설명 |
|---|---|
| `지인 사칭` | 가족·지인을 사칭해 송금·상품권을 요구 |
| `택배·기관 사칭` | 택배, 공공기관 사칭 |
| `금융·코인 사칭` | 은행, 카드, 코인 거래소 사칭 |
| `지원금·대출` | 지원금, 저금리 대출 유도 |
| `원격앱 설치 유도` | 앱 설치, 원격 제어 유도 |
| `기타 의심` | 위 유형에 맞지 않지만 `caution` 이상일 때 |
| `정상` | `safe`일 때 |

신고처(118 / 112 / 1332)는 `advice`, `if_clicked`에 넣기 전에 공식 사이트에서 다시 확인합니다.

## 5. 엔드포인트 상세

### POST `/analyze`

문자를 분석해 결과만 돌려줍니다. **저장하지 않고 알림도 보내지 않습니다.** 프론트 필수 호출은 아니며, 규칙 테스트·정확도 측정(`eval.py`)·Swagger 확인에 씁니다.

요청
```json
{ "text": "[Web발신] 택배 주소 확인 http://bit.ly/xxx 지금 확인하세요" }
```

응답 `200` — Result
```json
{
  "level": "danger",
  "score": 85,
  "category": "택배·기관 사칭",
  "signals": [
    {
      "rule_id": "short_url",
      "type": "단축URL",
      "detail": "http://bit.ly/xxx",
      "weight": 50,
      "explain": "실제 주소를 숨길 수 있어요",
      "start": 17,
      "end": 34
    }
  ],
  "advice": ["링크를 누르지 마세요", "공식 앱에서 직접 조회하세요"],
  "if_clicked": ["앱을 설치했다면 삭제하세요", "비밀번호를 변경하세요", "118에 상담하세요"]
}
```

### POST `/simulate/incoming`

문자가 폰에 도착한 상황을 흉내 냅니다. **분석 → 임시 저장 → 알림 판단**을 한 번에 합니다. 프론트 "문자 받기" 버튼이 호출합니다.

요청
```json
{ "text": "[Web발신] 택배 주소 확인 http://bit.ly/xxx 지금 확인하세요", "sender": "010-1234-5678" }
```

응답 `200`
```json
{
  "result_id": "a1b2c3d4",
  "level": "danger",
  "category": "택배·기관 사칭",
  "notified": true,
  "notification": {
    "title": "⚠️ 스팸 의심 문자",
    "body": "택배·기관 사칭 · 단축URL. 링크를 누르지 마세요",
    "url": "/result/a1b2c3d4"
  }
}
```

`safe`이면 알림을 만들지 않습니다.
```json
{ "result_id": "e5f6a7b8", "level": "safe", "category": "정상", "notified": false, "notification": null }
```

| 필드 | 설명 |
|---|---|
| `result_id` | 결과 조회용 값. 추측하기 어려운 무작위 문자열 |
| `notified` | 알림을 보냈으면 `true`. `safe`면 `false` |
| `notification` | `notified`가 `true`일 때만 객체, 아니면 `null` |

- `notified`가 `true`이고 푸시 구독이 있으면 서버가 **백그라운드에서 웹 푸시도 보냅니다.** (2단계, 실패해도 이 응답에는 영향 없음)
- 프론트는 `notified && notification`이면 앱 내 알림 배너를 띄우고, 아니면 "위험 신호가 발견되지 않았어요"를 보여줍니다.

### GET `/result/{result_id}`

저장된 분석 결과를 돌려줍니다. 알림 배너나 푸시 알림을 눌렀을 때 결과 화면(`/result/:id`)이 호출합니다.

응답 `200` — Result + 아래 필드
```json
{
  "result_id": "a1b2c3d4",
  "text": "[Web발신] 택배 주소 확인 http://bit.ly/xxx 지금 확인하세요",
  "expires_in": 540,
  "level": "danger",
  "score": 85,
  "category": "택배·기관 사칭",
  "signals": [ ... ],
  "advice": [ ... ],
  "if_clicked": [ ... ]
}
```

| 필드 | 설명 |
|---|---|
| `text` | 받은 문자 원문. 결과 화면의 하이라이트에 씀 |
| `expires_in` | 만료까지 남은 **초** (최대 600) |

- 저장 후 **600초가 지나면 404**를 돌려줍니다. 만료된 결과는 지웁니다.
- 여러 요청이 동시에 저장소를 건드려도 안전하도록 **Lock**을 씁니다.
- 내부용 값(저장 시각 등)은 응답에 넣지 않습니다.

### GET `/samples`

시연용 샘플 문자 목록입니다. 시뮬레이터의 샘플 버튼과 `scripts/demo.py`가 씁니다.

응답 `200`
```json
[
  {
    "id": "s01",
    "label": "택배 사칭 (위험)",
    "sender": "010-1234-5678",
    "text": "[Web발신] 택배 주소 확인 http://bit.ly/xxx 지금 확인하세요"
  }
]
```

- 20~30개 (위험 15 / 주의 5 / 안전 5), 데이터는 `data/demo_samples.json`에서 읽습니다.
- 실제 스미싱 URL은 `bit.ly/xxxx` 같은 형태로 바꿔서 넣습니다.

### GET `/push/vapid-public-key` (2단계)

브라우저가 푸시를 구독할 때 쓰는 공개키입니다.

응답 `200`
```json
{ "key": "BEl62iUYgUivxIkv69yViEuiBIa-Ib9..." }
```

환경 변수 `VAPID_PUBLIC_KEY`에서 읽습니다. 비공개키(`VAPID_PRIVATE_KEY`)는 절대 응답이나 커밋에 넣지 않습니다.

### POST `/push/subscribe` (2단계)

브라우저의 `PushSubscription`을 등록합니다.

요청
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "keys": { "p256dh": "...", "auth": "..." },
  "expirationTime": null
}
```

응답 `200`
```json
{ "ok": true }
```

- 구독 정보도 메모리에만 두고, 푸시 서버가 만료(410)로 응답한 구독은 지웁니다.
- HTTPS가 필요해서 시연은 터널링(cloudflared) 주소에서 하고, Android 폰을 권장합니다.

## 6. 맞춰야 하는 부분 (브랜치마다 다른 것)

현재 원격 브랜치들이 서로 다른 계약을 쓰고 있어서, **합치기 전에 아래를 이 문서 기준으로 맞춰야 합니다.**

| # | 어긋나는 곳 | 현재 | 이 문서의 기준 |
|---|---|---|---|
| 1 | `level` 값 | `dageon-lee`의 `main.py`와 `analyzer.py`는 `"안전" / "주의" / "위험"` | `safe` / `caution` / `danger` (프론트와 `notification.py`가 이미 이 값을 씀) |
| 2 | 엔드포인트 | `dageon-lee`는 `POST /api/check` 하나 | `POST /analyze` 등 위 표. `/api` 접두사는 백엔드에 붙이지 않음 (프록시가 떼기 때문에 `/api/check`는 프론트에서 닿지 않음) |
| 3 | 점수 구간 | `analyzer.py`와 `rules.yaml` 초안은 40 / 70 | 30 / 60 (노션 기능 명세서). `rules.yaml`의 `levels` 값을 고침 |
| 4 | 신호 형식 | `analyzer.py`는 `reasons: ["무료", ...]` (단어 목록) | `signals` 객체 목록 (`rule_id`, `weight`, `explain`, `start`, `end` 포함). 결과 화면 하이라이트에 위치가 필요함 |
| 5 | 판정 방식 | `analyzer.py`는 샘플로 단어 가중치를 학습함 | 노션 기능 명세서는 `rules.yaml` 규칙 기반. 어느 쪽으로 갈지 팀이 정해야 함 |
| 6 | CORS | `main.py`는 `POST`만 허용 | `GET`, `POST` 허용 (직접 호출 시 `GET /samples`, `GET /result`가 막힘) |
| 7 | 목 데이터 | 프론트 `mocks/sample.js`가 `result`에 저장 시각(`at`)을 노출하고, `caution` 제목이 `주의가 필요한 문자` | `at` 제거, `caution` 제목은 `확인이 필요한 문자` (`notification.py` 기준) |

## 7. 이 문서에서 정한 것 (노션에 없던 부분)

노션 기능 명세서에 없어서 프론트 목 데이터와 백엔드 스텁을 보고 정했습니다. 다르게 하고 싶다면 팀 채널에서 바꾸고 이 문서를 고칩니다.

- `POST /analyze`는 **저장하지 않는 분석 전용**입니다.
- `category`의 `기타 의심` 값 (5가지 유형에 안 맞는 경우)
- `GET /result`의 `result_id`, `text`, `expires_in` 필드
- `GET /samples`의 `id` 필드 (`demo.py`가 사용)
- 에러 메시지 문구
