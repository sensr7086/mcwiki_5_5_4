---
type: source
title: "UE Slate — MiscWidgets sub-skill"
slug: ue-slate-miscwidgets
source_path: raw/ue-wiki-llm/skills/Slate/references/MiscWidgets.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
tags: [ue, slate, ui]
---

# UE Slate — MiscWidgets sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/MiscWidgets.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

보조 위젯 — SThrobber + SCircularThrobber + SProgressBar + SSeparator + SSpacer.

## 2. Key claims

- SThrobber / SCircularThrobber: 로딩 인디케이터 (도트 / 원형). 매 frame 회전 = invalidate hot spot.
- SProgressBar: 진행률 (0~1).
- SSeparator: 구분선 (수평 / 수직). Orientation.
- SSpacer: 빈 공간 (Size 만 결정). Layout 의 padding 대안.
- 모두 [[concepts/Slate-Invalidation]] 영향 — Throbber 는 SInvalidationPanel 안에 두지 않아야.
