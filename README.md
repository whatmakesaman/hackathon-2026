# hackathon-2026

## 링크

- [Notion - 해커톤 팀 페이지](https://app.notion.com/p/2b5bb2b710398350a88701550cf9c10a)

## 팀원 작업 시작하기 (필독)

**각자 `dev`에서 내 브랜치를 새로 만들어 작업하고, `dev`로 PR을 올립니다.** `main`, `dev`에는 직접 올리지 않습니다.

```bash
git clone https://github.com/whatmakesaman/hackathon-2026.git   # 처음 한 번만
cd hackathon-2026
git fetch origin
git switch -c feature/내기능 origin/dev      # 1. dev에서 내 브랜치 만들기

# ... 작업 ...

git add 바꾼파일.py                          # 2. 파일을 지정해서 추가
git commit -m "feat: 한 줄 설명"             # 3. 타입: 설명
git push origin feature/내기능               # 4. 내 브랜치 이름을 적어서 push
gh pr create --base dev                      # 5. dev로 PR 만들기
```

- 이전에 만든 브랜치로 이어서 작업한다면 먼저 `git fetch origin && git merge origin/dev`로 최신 규칙을 받으세요.
- 자세한 규칙은 [`GIT_CONVENTION.md`](GIT_CONVENTION.md)에 있습니다.

## AI와 함께 작업할 때

이 레포에는 AI가 따라야 할 규칙이 들어 있습니다. 작업 전에 확인하세요.

- 규칙 문서: [`AGENTS.md`](AGENTS.md) (AI 행동 규칙), [`GIT_CONVENTION.md`](GIT_CONVENTION.md) (Git 규칙)
- **Claude Code, Codex, Cursor, Gemini CLI, Copilot**: 레포 폴더에서 실행하면 위 문서를 자동으로 읽습니다.
- **ChatGPT 웹처럼 레포를 직접 못 읽는 AI**: 대화 처음에 `AGENTS.md`와 `GIT_CONVENTION.md` 내용을 통째로 붙여넣고 시작하세요.
- 커밋·push·PR·merge를 AI에게 시킬 때도 따로 규칙을 설명할 필요가 없습니다. "커밋해줘", "PR 만들어줘"라고만 하면 됩니다.
