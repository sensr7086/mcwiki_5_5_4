---
type: source
title: "UE UMG — UWidget sub-skill"
slug: ue-umg-uwidget
source_path: raw/ue-wiki-llm/skills/UMG/references/UWidget.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UWidget]]"
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
tags: [ue, umg, ui]
---

# UE UMG — UWidget sub-skill

> Source: [[raw/ue-wiki-llm/skills/UMG/references/UWidget.md]]
> Parent: [[sources/ue-umg-skill]]

## 1. Summary

[[entities/UWidget]] 베이스 — RebuildWidget + SynchronizeProperties + ReleaseSlateResources + Visibility + IsVisible + GetCachedWidget.

## 2. Key claims

- RebuildWidget(): SWidget 트리 재생성. Editor 측 Construction 또는 런타임 첫 표시 시.
- SynchronizeProperties(): UWidget 속성 → SWidget 동기화. UPROPERTY 변경 후 호출.
- ReleaseSlateResources(bool): SWidget 참조 해제 — Destruct 시 호출.
- Visibility (ESlateVisibility 5 종): Visible / Collapsed / Hidden / HitTestInvisible / SelfHitTestInvisible.
- IsVisible(): Visible 또는 HitTestInvisible 만 true.
- GetCachedWidget(): 내부 TSharedPtr<SWidget> 접근. RebuildWidget 후만 valid.
- TakeWidget(): SWidget 반환 (필요 시 RebuildWidget 호출).
