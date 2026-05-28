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
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 mostly-cosmetic**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **mostly-cosmetic**. 5.5↔5.7 raw diff 가 대부분 cosmetic (whitespace / formatting) + 소수 (≤2) 의미 변경 — 본문 본질 안정.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
