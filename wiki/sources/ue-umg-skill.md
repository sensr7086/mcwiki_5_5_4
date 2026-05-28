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
