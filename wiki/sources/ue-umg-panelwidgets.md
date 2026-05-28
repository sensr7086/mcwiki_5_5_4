---
type: source
title: "UE UMG — PanelWidgets sub-skill"
slug: ue-umg-panelwidgets
source_path: raw/ue-wiki-llm/skills/UMG/references/PanelWidgets.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UPanelWidget]]"
tags: [ue, umg, ui]
---

# UE UMG — PanelWidgets sub-skill

> Source: [[raw/ue-wiki-llm/skills/UMG/references/PanelWidgets.md]]
> Parent: [[sources/ue-umg-skill]]

## 1. Summary

[[entities/UPanelWidget]] 자손 — UCanvasPanel + UHorizontalBox + UVerticalBox + UOverlay + UScrollBox + UWrapBox + UGridPanel.

## 2. Key claims

- UCanvasPanel: Anchor 기반 자유 배치 (HUD 표준). UCanvasPanelSlot 의 SetAnchors / SetPosition / SetSize.
- UHorizontalBox / UVerticalBox: 한 방향 자동. AddChildToHorizontalBox / SizeRule (Auto / Fill).
- UOverlay: 같은 위치 (Z 순서). HUD popup.
- UScrollBox: Scrollable 컨테이너. Orientation 설정.
- UWrapBox: 자식이 줄 바꿈.
- UGridPanel: 행/열 grid 배치.
- Editor 의 디자이너 패널에서 자식 추가 — 자동으로 적절한 UPanelSlot 자손 생성.
