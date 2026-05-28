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
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
