---
type: source
title: "UE SlateCore — Layout sub-skill"
slug: ue-slatecore-layout
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Layout.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/FGeometry]]"
tags: [ue, slate, ui]
---

# UE SlateCore — Layout sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/Layout.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

Slate Layout 시스템 — FArrangedChildren + [[entities/FGeometry]] + EHorizontalAlignment + EVerticalAlignment + SizeBox / Padding / Box.

## 2. Key claims

- FGeometry: Position + Size + DPI scale. Local-to-Absolute 변환.
- FArrangedChildren: 자식의 Geometry 배열. OnArrangeChildren 의 출력.
- EHorizontalAlignment: HAlign_Left / HAlign_Center / HAlign_Right / HAlign_Fill.
- EVerticalAlignment: VAlign_Top / VAlign_Center / VAlign_Bottom / VAlign_Fill.
- FMargin: Padding (Left / Top / Right / Bottom).
- FSlateLayoutTransform / FSlateRenderTransform: 변환 (Scale / Translation / Rotation).
- 5.x FVector2f / FVector2d 권장 — FVector2D 는 deprecation 경고.
