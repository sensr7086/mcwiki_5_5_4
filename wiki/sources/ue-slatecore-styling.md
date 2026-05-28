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
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
