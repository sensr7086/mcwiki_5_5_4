---
type: source
title: "UE Slate — EditorApplication sub-skill"
slug: ue-slate-editorapplication
source_path: raw/ue-wiki-llm/skills/Slate/references/EditorApplication.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, editor]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE Slate — EditorApplication sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/EditorApplication.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

🛠 SDockTab + SWindow + 에디터 전용 위젯 묶음 — Slate 의 Application 측면 (게임 SApplication 과 분리).

## 2. Key claims

- SWindow: Slate의 OS-level 윈도우. ClientSize / Title / Style. 게임 메인 vs 모달 dialog.
- SDockTab: Docking 시스템의 탭 (Docking sub-skill 페어).
- 에디터 전용 위젯들: SListPanel / SSplitter / SSeparator / SThrobber / 등 — 에디터 UI 의 표준 컴포넌트.
- FSlateApplication::Get().AddWindow / AddModalWindow — 새 윈도우 등록.
- Editor 빌드만 — `#if WITH_EDITOR` 가드.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 mostly-cosmetic**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **mostly-cosmetic**. 5.5↔5.7 raw diff 가 대부분 cosmetic (whitespace / formatting) + 소수 (≤2) 의미 변경 — 본문 본질 안정.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
