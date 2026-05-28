---
type: source
title: "UE SlateCore — Styling sub-skill"
slug: ue-slatecore-styling
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Styling.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/FSlateStyleSet]]"
  - "[[entities/FSlateBrush]]"
tags: [ue, slate, ui]
---

# UE SlateCore — Styling sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/Styling.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

[[entities/FSlateStyleSet]] + [[entities/FSlateBrush]] + FSlateColor + FSlateFontInfo + FSlateWidgetStyle — Style 등록/해제.

## 2. Key claims

- FSlateStyleSet (StyleName): 등록 패턴 — `FSlateStyleSet StyleSet("MyStyle")` + `Set("MyBrush", new FSlateImageBrush(...))` + `FSlateStyleRegistry::RegisterSlateStyle(StyleSet)`.
- FSlateBrush: 텍스처 wrapper. ImageBrush / BoxBrush (9-slice) / BorderBrush / ColorBrush.
- FSlateColor: 테마 컬러 — Foreground / Background / 사용자 정의.
- FSlateFontInfo: 폰트 메타 (Path / Size / Hinting).
- FSlateWidgetStyle: 위젯 종류별 style (FButtonStyle / FTextBlockStyle / FCheckBoxStyle 등).
- 사용 패턴: `FAppStyle::GetBrush("Icons.Edit")` / `FAppStyle::GetWidgetStyle<FButtonStyle>("Button")`.
