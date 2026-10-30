from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="스팸 문자 검사 API",
    description="문자를 입력하고 검사 결과를 확인하세요. 현재는 임시 결과(50점·주의)를 반환합니다.",
    docs_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


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
    score: int = Field(ge=0, le=100, title="스팸 점수", description="0~100점", examples=[50])
    level: Literal["안전", "주의", "위험"] = Field(title="위험 등급", examples=["주의"])
    reasons: list[str] = Field(title="의심 근거", description="점수를 올린 의심 단어 목록", examples=[[]])


@app.post(
    "/api/check", response_model=CheckResponse, tags=["문자 검사"],
    summary="문자의 스팸 위험도 검사",
    description="직접 입력하기를 누르고 text에 문자를 입력한 뒤 검사 실행을 누르세요. 현재 결과는 임시 값입니다.",
    response_description="문자 검사 결과",
    responses={422: {"description": "입력 오류: text 누락, 빈 값, 공백만 있는 값 또는 2000자 초과"}},
)
def check(req: CheckRequest) -> CheckResponse:
    # shortcut: 임시 결과이며, B·C 모듈 완성 후 학습 및 분석 함수를 연결한다.
    return CheckResponse(score=50, level="주의", reasons=[])
