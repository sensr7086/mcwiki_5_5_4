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
