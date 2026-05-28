---
type: source
title: "UE Slate — LayoutWidgets sub-skill"
slug: ue-slate-layoutwidgets
source_path: raw/ue-wiki-llm/skills/Slate/references/LayoutWidgets.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui]
---

# UE Slate — LayoutWidgets sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/LayoutWidgets.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

레이아웃 위젯 — SHorizontalBox + SVerticalBox + SOverlay + SScrollBox + SBox + SBorder + SExpandableArea.

## 2. Key claims

- SHorizontalBox / SVerticalBox: 한 방향 자동 배치. AddSlot()-> + FillWidth/Height + Padding.
- SOverlay: 자식들을 같은 위치 (Z 순서). HUD popup 표준.
- SScrollBox: 스크롤 가능 컨테이너. Orientation (Horizontal / Vertical) + ScrollWhenFocusChanges.
- SBox: padding / size override (WidthOverride / HeightOverride / MinDesiredWidth).
- SBorder: 배경 + 단일 content. BorderImage + BorderBackgroundColor.
- SExpandableArea: 접기/펼치기 영역. HeaderContent + BodyContent.
