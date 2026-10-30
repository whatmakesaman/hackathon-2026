import json
import logging
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

import store
from analyzer import load_rules
from message_model import analyze_with_model, load_model
from notification import build_notification
from push import send_to_all
from push_routes import router as push_router
from url_ai import apply_ai_verdict, check_urls

ROOT_DIR = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT_DIR / "rules.yaml"
SAMPLES_PATH = ROOT_DIR / "data" / "demo_samples.json"
LEVEL_KO = {"safe": "안전", "caution": "주의", "danger": "위험"}

logger = logging.getLogger(__name__)

# 규칙은 서버가 켜질 때 한 번만 읽는다. 잘못된 규칙은 건너뛰고 경고만 남긴다.
RULES, RULE_WARNINGS = load_rules(RULES_PATH)
MODEL = load_model()
for warning in RULE_WARNINGS:
    logger.warning("규칙 건너뜀: %s", warning)


class UTF8JSONResponse(JSONResponse):
    # charset이 없으면 브라우저 주소창에서 열 때 한글을 EUC-KR로 추측해 깨져 보인다.
    media_type = "application/json; charset=utf-8"


app = FastAPI(
    default_response_class=UTF8JSONResponse,
    title="스팸 문자 검사 API",
    description="학습 모델이 의심 여부를 판단하고, rules.yaml의 위험 신호 점수로 주의·위험을 나눕니다. 점수는 확률이 아닙니다.",
    docs_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(push_router)


@app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
def korean_docs() -> HTMLResponse:
    page = get_swagger_ui_html(openapi_url=app.openapi_url, title="스팸 문자 검사 · API 문서")
    # Swagger가 요청 실행 후 다시 그리는 화면에도 한글 문구를 적용한다.
    translation = """
<script>
document.documentElement.lang = "ko";
const labels = new Map(Object.entries({
    "Try it out": "직접 입력하기", "Execute": "검사 실행", "Cancel": "취소",
    "Clear": "결과 지우기", "Reset": "초기화", "Parameters": "요청 매개변수",
    "No parameters": "별도의 요청 매개변수가 없습니다.", "Request body": "검사할 문자",
    "required": "필수", "Responses": "응답", "Server response": "실제 서버 응답",
    "Response body": "실제 응답 내용", "Response headers": "응답 헤더",
    "Request URL": "요청 주소", "Code": "상태 코드", "Details": "상세 내용",
    "Description": "설명", "Links": "관련 링크", "No links": "관련 링크 없음",
    "Example Value": "응답 형식 예시", "Schema": "데이터 구조", "Schemas": "데이터 구조 목록",
    "Successful Response": "요청 처리 성공", "Validation Error": "입력값 검증 오류",
    "Media type": "데이터 형식", "Download": "다운로드", "Curl": "터미널 요청 명령어",
    "Controls Accept header.": "서버에서 받을 응답 형식을 지정합니다.",
    "Controls Content-Type header.": "서버로 보낼 데이터 형식을 지정합니다.",
    "Available values": "선택 가능한 값", "Example Description": "예시 설명",
    "Expand all": "모두 펼치기", "Collapse all": "모두 접기"
}));
function translateLabels() {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
        const node = walker.currentNode;
        if (node.parentElement.closest("script, style, pre, code, textarea")) continue;
        const original = node.nodeValue.trim();
        if (labels.has(original)) {
            node.nodeValue = node.nodeValue.replace(original, labels.get(original));
        }
    }
}
translateLabels();
new MutationObserver(translateLabels).observe(document.body, {
    childList: true, subtree: true, characterData: true
});
</script>
"""
    return HTMLResponse(page.body.decode("utf-8").replace("</body>", translation + "</body>"))


class CheckRequest(BaseModel):
    text: str = Field(
        min_length=1, max_length=2000, pattern=r"\S",
        title="검사할 문자", description="공백만 있는 입력은 제외하며, 1~2000자까지 입력할 수 있습니다.",
        examples=["무료 상품권 당첨! 지금 클릭"],
    )


class CheckResponse(BaseModel):
    score: int = Field(ge=0, le=100, title="스팸 점수", description="0~100 위험 신호 점수이며 사기 확률이 아닙니다.", examples=[50])
    level: Literal["안전", "주의", "위험"] = Field(title="위험 등급", examples=["주의"])
    reasons: list[str] = Field(title="의심 근거", description="모델 판정 안내와 규칙에서 발견한 참고 표현 목록", examples=[[]])


@app.post(
    "/api/check", response_model=CheckResponse, tags=["문자 검사"],
    summary="문자의 스팸 위험도 검사",
    description="직접 입력하기를 누르고 text에 문자를 입력한 뒤 검사 실행을 누르세요.",
    response_description="문자 검사 결과",
    responses={422: {"description": "입력 오류: text 누락, 빈 값, 공백만 있는 값 또는 2000자 초과"}},
)
def check(req: CheckRequest) -> CheckResponse:
    result = analyze_with_model(req.text, RULES, MODEL)
    reasons = list(dict.fromkeys(s["detail"] for s in result["signals"]))
    return CheckResponse(score=result["score"], level=LEVEL_KO[result["level"]], reasons=reasons)


class IncomingRequest(CheckRequest):
    sender: str = Field(default="", max_length=50, title="발신 번호", examples=["010-1234-5678"])


def analyze_full(text: str) -> dict:
    # 단어 점수 모델 결과에 AI 링크 판정을 덧붙인다. AI가 실패하면 모델 결과 그대로다.
    return apply_ai_verdict(analyze_with_model(text, RULES, MODEL), check_urls(text), RULES["levels"]["caution"])


@app.post("/analyze", tags=["문자 검사"], summary="문자 분석 (저장·알림 없음)")
def analyze_text(req: CheckRequest) -> dict:
    result = analyze_full(req.text)
    # 분석 전용 API라 원문을 되돌려 주지 않는다. (docs/API.md의 Result)
    return {key: value for key, value in result.items() if key != "text"}


@app.post("/simulate/incoming", tags=["시뮬레이터"], summary="문자 수신 시뮬레이션(분석→보관→알림 판단)")
def simulate_incoming(req: IncomingRequest, background: BackgroundTasks) -> dict:
    result = analyze_full(req.text)
    result_id = store.save(result)
    notification = build_notification(result, result_id)
    if notification:
        # 푸시 발송이 느리거나 실패해도 화면 응답은 바로 돌려준다.
        background.add_task(send_to_all, notification)
    return {
        "result_id": result_id,
        "level": result["level"],
        "category": result["category"],
        "notified": notification is not None,
        "notification": notification,
    }


@app.get(
    "/result/{result_id}", tags=["문자 검사"], summary="보관 중인 분석 결과 조회",
    responses={404: {"description": "결과가 없거나 10분이 지나 만료됨"}},
)
def get_result(result_id: str) -> dict:
    result = store.get(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없거나 만료되었어요")
    return {"result_id": result_id, **result}


@app.get("/samples", tags=["시뮬레이터"], summary="시연용 샘플 문자 목록")
def get_samples() -> list:
    if not SAMPLES_PATH.exists():
        return []
    with open(SAMPLES_PATH, encoding="utf-8") as f:
        return json.load(f)
