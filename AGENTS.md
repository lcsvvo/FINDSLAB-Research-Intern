# Codex 협업 규칙

이 저장소에서 작업할 때는 아래 규칙을 반드시 따른다. 상세 배경은 `README.md`의 "협업 가이드" 섹션 참고. (`CLAUDE.md`와 동일한 규칙)

1. **작업 시작 전** 로컬 `main`에 `git pull`부터 한다.
2. **브랜치는 항상 새로 생성**한다. 네이밍: `<type>/<짧은-설명>` (예: `feature/rate-beta-hac`, `fix/rolling-window`, `docs/readme-update`). **`codex/~` 같은 자동 브랜치명을 임의로 만들지 않는다.**
3. 작업 완료 후 의미 단위로 `commit` → `push`.
4. **PR을 생성**하고 무엇을 했는지 / 왜 했는지 / 확인이 필요한 사항만 간단히 작성한다.
5. **PR을 임의로 merge하지 않는다.** 안내 또는 확인 후 merge한다.
6. 새 작업 전 항상 최신 `main`을 `pull`한다.
7. `data/`, `docs/private/`는 절대 커밋하지 않는다.
