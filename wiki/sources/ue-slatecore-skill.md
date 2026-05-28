---
type: source
title: "UE 5.7.4 SlateCore Module — Main SKILL"
slug: ue-slatecore-skill
source_path: raw/ue-wiki-llm/skills/SlateCore/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/SWidget]]"
  - "[[entities/FGeometry]]"
  - "[[entities/FSlateDrawElement]]"
  - "[[entities/FSlateBrush]]"
  - "[[entities/FSlateStyleSet]]"
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
  - "[[concepts/Slate-Paint-Cycle]]"
tags: [ue, slate, ui]
---

# UE 5.7.4 SlateCore Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/SlateCore/SKILL.md]]

## 1. Summary

UE 의 저수준 선언형 UI 코어 (10 sub-skill).

## 2. Sub-skills (10 — Phase 4F 완료)

- [[sources/ue-slatecore-swidget]] — SWidget 베이스 (SLATE_BEGIN_ARGS/Construct/OnPaint)
- [[sources/ue-slatecore-layout]] — FArrangedChildren + FGeometry + Alignment
- [[sources/ue-slatecore-drawing]] — OnPaint + FSlateDrawElement
- [[sources/ue-slatecore-styling]] — FSlateStyleSet + FSlateBrush + FSlateColor
- [[sources/ue-slatecore-input]] — OnMouseButtonDown/Up + OnKeyDown + FReply + FocusManager
- [[sources/ue-slatecore-application]] — FSlateApplication 글로벌
- [[sources/ue-slatecore-animation]] — FCurveSequence + FCurveHandle + ActiveTimer
- [[sources/ue-slatecore-text]] — FText + LOCTEXT + Localization + HarfBuzz
- [[sources/ue-slatecore-types]] — EVisibility + Alignment + WidgetClipping
- [[sources/ue-slatecore-trace]] 🛠 — Slate Trace + WidgetReflector + Insights

## 3. Open questions

- [ ] FVector2f/FVector2d 5.x 마이그레이션 함정
