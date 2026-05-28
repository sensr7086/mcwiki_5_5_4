---
type: source
title: "UE SlateCore — Types sub-skill"
slug: ue-slatecore-types
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Types.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE SlateCore — Types sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/Types.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

EVisibility + ESlateVisibility + EHorizontalAlignment + EWidgetClipping + FSlateColor + FOptionalSize.

## 2. Key claims

- EVisibility (SlateCore native) 5 종: Visible / Collapsed / Hidden / HitTestInvisible / SelfHitTestInvisible.
- ESlateVisibility (UMG 5 종) — 위와 동일. UWidget 의 BP 노출.
- EHorizontalAlignment / EVerticalAlignment — Layout 정렬.
- EWidgetClipping: 자식이 부모 영역 밖 표시 정책 (Inherit / OnDemand / ClipToBounds 등).
- FSlateColor: 테마 컬러 wrapper (FLinearColor + 일반화).
- FOptionalSize: WidthOverride / HeightOverride 의 optional. SBox 등에 사용.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
