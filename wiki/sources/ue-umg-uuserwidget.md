---
type: source
title: "UE UMG — UUserWidget sub-skill"
slug: ue-umg-uuserwidget
source_path: raw/ue-wiki-llm/skills/UMG/references/UUserWidget.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UUserWidget]]"
related_concepts:
  - "[[concepts/UMG-Super-Call-Convention]]"
tags: [ue, umg, ui]
---

# UE UMG — UUserWidget sub-skill

> Source: [[raw/ue-wiki-llm/skills/UMG/references/UUserWidget.md]]
> Parent: [[sources/ue-umg-skill]]

## 1. Summary

[[entities/UUserWidget]] 디테일 — PreConstruct (디자이너) + Construct + Destruct + NativeConstruct + NativeDestruct + Tick + InvalidateLayoutAndVolatility.

## 2. Key claims

- 라이프사이클: NativePreConstruct (Editor preview / 디자이너) → NativeConstruct (런타임) → NativeTick → NativeDestruct.
- BP 페어: PreConstruct / Construct / Tick / Destruct event.
- [[concepts/UMG-Super-Call-Convention]] 의무: NativeConstruct → Super FIRST, NativeDestruct → Super LAST.
- 깊이 자료: [[sources/ue-umg-invalidationdeep]] — Native* 가상 함수 30+ + 5 핵심 원칙.
- InvalidateLayoutAndVolatility: 명시적 invalidate — Slate 가 layout 재계산.
- BindWidget specifier: `UPROPERTY(meta=(BindWidget))` — BP 디자이너 위젯 ↔ C++ 멤버 명시 바인딩.
- 