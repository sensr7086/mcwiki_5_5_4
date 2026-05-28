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
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
