from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Spam Check API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class CheckRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000, pattern=r"\S")


class CheckResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    level: Literal["안전", "주의", "위험"]
    reasons: list[str]


@app.post("/api/check", response_model=CheckResponse)
def check(req: CheckRequest) -> CheckResponse:
    # shortcut: 임시 결과이며, B·C 모듈 완성 후 학습 및 분석 함수를 연결한다.
    return CheckResponse(score=50, level="주의", reasons=[])
