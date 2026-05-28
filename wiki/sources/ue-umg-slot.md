---
type: source
title: "UE UMG — Slot sub-skill"
slug: ue-umg-slot
source_path: raw/ue-wiki-llm/skills/UMG/references/Slot.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UPanelSlot]]"
tags: [ue, umg, ui]
---

# UE UMG — Slot sub-skill

> Source: [[raw/ue-wiki-llm/skills/UMG/references/Slot.md]]
> Parent: [[sources/ue-umg-skill]]

## 1. Summary

[[entities/UPanelSlot]] 자손 — UCanvasPanelSlot + UHorizontalBoxSlot + UVerticalBoxSlot + UOverlaySlot + Anchors + Alignment.

## 2. Key claims

- UCanvasPanelSlot: SetAnchors(FAnchors) + SetPosition(FVector2D) + SetSize(FVector2D) + SetAlignment(FVector2D) + SetZOrder(int32).
- FAnchors 미리 정의 매크로: TopLeft / Center / FillScreen 등.
- UHorizontalBoxSlot / UVerticalBoxSlot: SetSize(FSlateChildSize Fill ratio 또는 Auto) + SetPadding(FMargin) + SetVerticalAlignment / SetHorizontalAlignment.
- UOverlaySlot: SetHorizontalAlignment / SetVerticalAlignment + SetPadding.
- UGridSlot: SetRow / SetColumn / SetRowSpan / SetColumnSpan.
- AddChild 반환값을 Cast 해 사용 — 잘못된 자손 cast 시 nullptr.
