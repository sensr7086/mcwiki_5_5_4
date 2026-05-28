---
type: source
title: "UE Slate — Commands sub-skill"
slug: ue-slate-commands
source_path: raw/ue-wiki-llm/skills/Slate/references/Commands.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/FUICommandList]]"
tags: [ue, slate, editor, ui]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE Slate — Commands sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/Commands.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

🛠 [[entities/FUICommandList]] + FUICommandInfo + UI_COMMAND 매크로 + InputBindingManager + 단축키.

## 2. Key claims

- TCommands<T> 등록 패턴: `class FMyCommands : public TCommands<FMyCommands>` + virtual `RegisterCommands()` override.
- UI_COMMAND 매크로: `UI_COMMAND(MyCmd, "Label", "Tooltip", EUserInterfaceActionType::Button, FInputChord(EKeys::F))`.
- FUICommandList::MapAction: Command → callback 매핑.
- FInputBindingManager: 사용자 단축키 customization (Settings → Hotkeys).
- 메뉴 / 툴바 / 단축키 통합 — 한 Command 가 메뉴 / 툴바 / 단축키 양쪽에서 발화.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 mostly-cosmetic**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **mostly-cosmetic**. 5.5↔5.7 raw diff 가 대부분 cosmetic (whitespace / formatting) + 소수 (≤2) 의미 변경 — 본문 본질 안정.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
