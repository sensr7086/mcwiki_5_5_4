---
type: source
title: "UE Slate — Menu sub-skill"
slug: ue-slate-menu
source_path: raw/ue-wiki-llm/skills/Slate/references/Menu.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UToolMenus]]"
tags: [ue, slate, editor, ui]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE Slate — Menu sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/Menu.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

🛠 메뉴 구성 (Legacy + 5.x) — FMenuBuilder + FExtensibilityManager + FExtender. 5.x = [[entities/UToolMenus]] 표준 (FMenuBuilder 의 후속).

## 2. Key claims

- FMenuBuilder (Legacy): 메뉴 트리 구성. AddMenuEntry / AddSubMenu / AddMenuSeparator. 5.x 에서도 일부 사용 (호환).
- FExtensibilityManager: 다른 모듈이 메뉴 확장 가능하게.
- FExtender: 특정 메뉴에 항목 추가/대체.
- 5.x [[entities/UToolMenus]] 권장: 더 강력 + Editor Utility Widget 통합 + 동적 등록.
- FUICommandList 와 페어 — `MenuBuilder.AddMenuEntry(MyCommands.MyCommand)`.
- 표준 메뉴 path: MainFrame.MainMenu.* / LevelEditor.MainMenu.*.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
