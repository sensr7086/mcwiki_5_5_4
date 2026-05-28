---
type: source
title: "UE Slate — TextInput sub-skill"
slug: ue-slate-textinput
source_path: raw/ue-wiki-llm/skills/Slate/references/TextInput.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
tags: [ue, slate, ui]
---

# UE Slate — TextInput sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/TextInput.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

텍스트 입력 위젯 — SEditableText + SEditableTextBox + SMultiLineEditableText + STextEntryPopup.

## 2. Key claims

- SEditableText: 단일 라인 입력. Text attribute + OnTextChanged + OnTextCommitted (Enter).
- SEditableTextBox: SEditableText + 배경 박스 (스타일 통합).
- SMultiLineEditableText: 다중 라인 + 스크롤. Rich text markup 지원.
- STextEntryPopup: 모달 입력 popup (이름 입력 등).
- 입력 시 매 frame invalidate — [[concepts/Slate-Invalidation]] 의 hot spot. SInvalidationPanel 안에 두지 않아야.
- Localization 통합: FText 표준 (LOCTEXT 매크로).
