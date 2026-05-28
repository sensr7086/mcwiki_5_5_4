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
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
