# hackathon-2026

## 링크

- [Notion - 해커톤 팀 페이지](https://app.notion.com/p/2b5bb2b710398350a88701550cf9c10a)

## AI와 함께 작업할 때

이 레포에는 AI가 따라야 할 규칙이 들어 있습니다. 작업 전에 확인하세요.

- 규칙 문서: [`AGENTS.md`](AGENTS.md) (AI 행동 규칙), [`GIT_CONVENTION.md`](GIT_CONVENTION.md) (Git 규칙)
- **Claude Code, Codex, Cursor, Gemini CLI, Copilot**: 레포 폴더에서 실행하면 위 문서를 자동으로 읽습니다.
- **ChatGPT 웹처럼 레포를 직접 못 읽는 AI**: 대화 처음에 `AGENTS.md`와 `GIT_CONVENTION.md` 내용을 통째로 붙여넣고 시작하세요.
- 커밋·push·PR·merge를 AI에게 시킬 때도 따로 규칙을 설명할 필요가 없습니다. "커밋해줘", "PR 만들어줘"라고만 하면 됩니다.


## 백엔드 모델과 실행

문자 2~4-gram 다항 나이브 베이즈가 판정하고, 기존 규칙이 참고 근거를 표시합니다.
점수는 사기 확률이 아닙니다. API 계약은 [docs/API.md](docs/API.md)를 참고하세요.

프로젝트 루트의 PowerShell에서 실행합니다.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --reload
```

API 테스트: http://127.0.0.1:8000/docs

### 모델 재학습 (정규화 또는 학습 자료를 변경할 때)

```powershell
.\.venv\Scripts\python.exe backend/message_model.py --train
```

- 입력: `data/lgaidataset.csv`의 라벨 1(일반), 2(스미싱). 정의가 없는 라벨 3은 제외합니다.
- 같은 정규화 문장과 숫자만 다른 문장은 한 그룹에 묶어 학습·검증·시험을 70/10/20으로 분리합니다. 비슷하지만 다른 모든 문장을 묶은 것은 아닙니다.
- `data/ham.txt`의 정상 SMS 26개는 중복·시험 그룹을 제외한 뒤 학습 가중치 5로 보충합니다. 보충 자료 자체의 성공률을 시험 성능으로 발표하지 않습니다.
- 출력: `backend/message_model.json.gz`. 이 파일을 소스와 함께 전달하면 서버 실행에는 CSV가 필요하지 않습니다.
- 서버는 모델을 한 번만 읽으므로 재학습 후 재시작하세요. 정규화가 바뀌면 모델도 다시 학습해야 합니다.
- 학습 명령은 분리한 시험 자료의 수치를 출력합니다. 같은 데이터셋 안의 개발 참고 수치이며 실제 모든 문자의 성능을 보장하지 않습니다.
