---
type: source
title: "UE 5.7.4 UMG Module — Main SKILL"
slug: ue-umg-skill
source_path: raw/ue-wiki-llm/skills/UMG/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UWidget]]"
  - "[[entities/UUserWidget]]"
  - "[[entities/UPanelWidget]]"
  - "[[entities/UPanelSlot]]"
  - "[[entities/SWidget]]"
related_concepts:
  - "[[concepts/UMG-Super-Call-Convention]]"
  - "[[concepts/Slate-Invalidation]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, umg, ui]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE 5.7.4 UMG Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/UMG/SKILL.md]]

## 1. Summary

Slate 위에 UObject + BP 노출 레이어 (7 sub-skill).

## 2. Sub-skills (7 — Phase 4F 완료)

- [[sources/ue-umg-uwidget]] — UWidget 베이스 (RebuildWidget/SynchronizeProperties/ReleaseSlateResources)
- [[sources/ue-umg-uuserwidget]] — UUserWidget (PreConstruct/Construct/Tick/Destruct)
- [[sources/ue-umg-standardwidgets]] — UButton/UImage/UCheckBox/UTextBlock/UProgressBar
- [[sources/ue-umg-panelwidgets]] — UCanvasPanel/UHorizontalBox/UVerticalBox 등
- [[sources/ue-umg-listwidgets]] — UListView/UTileView/UTreeView/UDynamicEntryBox
- [[sources/ue-umg-slot]] — UPanelSlot 자손 (UCanvasPanelSlot/UHorizontalBoxSlot 등)
- [[sources/ue-umg-viewmodel]] 🆕 — 5.x MVVM Plugin (UMVVMViewModelBase + Field Notify)

## 3. Open questions

- [ ] CommonUI Plugin 5.x 와의 통합 (Activatable Widget)
- [ ] WidgetPool 패턴 (UMG 위젯 재사용)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
