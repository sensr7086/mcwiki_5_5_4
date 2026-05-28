# AGENTS.md

본 파일은 [`CLAUDE.md`](./CLAUDE.md) 의 alias.

OpenAI Codex 와 일부 도구는 `AGENTS.md` 를 자동으로 읽는다. Claude Code 와 OpenCode 는 `CLAUDE.md` 를 우선 본다. 두 파일이 갈라지지 않도록 다음 중 하나를 선택:

- **(권장) symlink** — Linux/macOS:
  ```bash
  ln -sf CLAUDE.md AGENTS.md
  ```
- **(Windows) 하드링크 또는 동기화 스크립트**:
  ```cmd
  mklink /H AGENTS.md CLAUDE.md
  ```
  또는 git pre-commit hook 으로 `cp CLAUDE.md AGENTS.md` 자동.

본 파일이 *비어있고 위 안내문만 있다면* 사용자가 아직 link 를 만들지 않은 것. 즉시 수정 필요.

---

> **LLM 에게**: 이 파일을 읽었다면 즉시 `CLAUDE.md` 를 마저 읽고 그 스키마를 따른다.
