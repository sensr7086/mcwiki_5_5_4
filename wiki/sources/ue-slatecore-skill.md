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
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
