---
type: source
title: "UE SlateCore — Drawing sub-skill"
slug: ue-slatecore-drawing
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Drawing.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/FSlateDrawElement]]"
  - "[[entities/FSlateBrush]]"
related_concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
tags: [ue, slate, ui, rendering]
---

# UE SlateCore — Drawing sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/Drawing.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

OnPaint + [[entities/FSlateDrawElement]]::MakeBox/Lines/Text + FPaintArgs + LayerId + [[entities/FSlateBrush]] + Material 통합.

## 2. Key claims

- OnPaint(Args, Geometry, CullingRect, OutDrawElements, LayerId, Style, ColorTint).
- FSlateDrawElement::MakeBox / MakeText / MakeLines / MakeSpline / MakeViewport 등 정적 헬퍼.
- LayerId: depth — 큰 LayerId 가 위. 매 호출 ++ 증가.
- FPaintArgs: paint 컨텍스트 (Volatility / WindowOffset 등).
- Material 통합: FSlateMaterialBrush — Material Domain=UI 의 Slate 사용.
- [[concepts/Slate-Paint-Cycle]] 의 OnPaint 단계.

## Cross-link

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-ref-deep-invalidationhotspots]] (inbound=3, suggest_missing_cross_link high confidence)
