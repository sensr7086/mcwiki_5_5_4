---
type: source
title: "UE SlateCore — Types sub-skill"
slug: ue-slatecore-types
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Types.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui]
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
