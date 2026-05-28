---
type: source
title: "UE 5.7.4 Slate Module — Main SKILL"
slug: ue-slate-skill
source_path: raw/ue-wiki-llm/skills/Slate/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/SWidget]]"
  - "[[entities/FSlateApplication]]"
  - "[[entities/FTabManager]]"
  - "[[entities/FUICommandList]]"
related_concepts:
  - "[[concepts/Slate-Editor-Runtime-Separation]]"
tags: [ue, slate, ui]
---

# UE 5.7.4 Slate Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Slate/SKILL.md]]

## 1. Summary

게임 UI + 인하우스 에디터 도구 통합 모듈 (12 sub-skill).

## 2. Sub-skills (12 — Phase 4F 완료)

### 게임 + 에디터 공통
- [[sources/ue-slate-application]] — SButton/SImage/SBox/SBorder/STextBlock/SOverlay
- [[sources/ue-slate-commonwidgets]] — SButton/SCheckBox/SComboBox/SProgressBar/SSpinBox 일반
- [[sources/ue-slate-layoutwidgets]] — SHorizontalBox/SVerticalBox/SOverlay/SScrollBox 레이아웃
- [[sources/ue-slate-liststrees]] — SListView/STreeView/STableRow 가상화
- [[sources/ue-slate-textinput]] — SEditableText / 텍스트 입력
- [[sources/ue-slate-miscwidgets]] — SThrobber / SSeparator / SSpacer
- [[sources/ue-slate-animation]] — FCurveSequence + ActiveTimer

### 인하우스 툴 🛠
- [[sources/ue-slate-docking]] — FTabManager + SDockTab + Layout
- [[sources/ue-slate-menu]] — FMenuBuilder + FExtender + 5.x ToolMenus
- [[sources/ue-slate-commands]] — FUICommandList + UI_COMMAND 매크로
- [[sources/ue-slate-editorapplication]] — SDockTab + SWindow 에디터
- [[sources/ue-slate-grapheditor]] — SGraphEditor + UEdGraph 노드 그래프

## 3. Open questions

- [ ] 5.x Slate vs UMG 결정 트리 (game UI)

## Cross-link

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-ref-05-editoronlyindex]] (inbound=3, suggest_missing_cross_link high confidence)
