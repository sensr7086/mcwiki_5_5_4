---
type: entity
title: "UPanelWidget / UPanelSlot"
aliases: [UPanelWidget, UPanelSlot, UCanvasPanel, UVerticalBox, UHorizontalBox, UGridPanel]
kind: model
sources:
  - "[[sources/ue-umg-skill]]"
tags: [ue, umg, ui]
last_updated: 2026-05-09
---

# UPanelWidget / UPanelSlot

## 요약

[[entities/UWidget]] 자손. **자식 N 개를 담을 수 있는 위젯**. Slot 기반 — 각 Panel 종류마다 전용 [[entities/UPanelSlot]] 자손 (UCanvasPanelSlot / UHorizontalBoxSlot / UGridSlot 등). 자식별 배치 메타 (Anchor / Padding / Margin / Size) 가 Slot 에.

## 관계

- 부모: [[entities/UWidget]]
- 자손: UCanvasPanel / UHorizontalBox / UVerticalBox / UGridPanel / UScrollBox / UWrapBox / UStackBox / UOverlay 등
- Slot: UPanelSlot 자손 (Panel 종류별)

## 핵심 주장

- AddChild(Widget) 또는 Editor 의 디자이너 트리 — 자식 추가.
- AddChild 반환값 = UPanelSlot 자손 — Cast 후 배치 메타 설정 (예: `Cast<UCanvasPanelSlot>(Slot)->SetAnchors(...)`).
- UCanvasPanel: Anchor 기반 자유 배치 (HUD 표준).
- UVerticalBox / UHorizontalBox: 한 방향 자동 배치. Fill / Auto.
- UGridPanel: 행/열 grid 배치.
- UScrollBox: Scrollable 컨테이너. UWrapBox: 자식이 줄 바꿈.
- ClearChildren / RemoveChild / GetChildAt — 자식 관리 API.

## 열린 질문

- [ ] HUD 의 표준 panel 조합 (CanvasPanel + ScaleBox + 등)
- [ ] CommonUI 의 Activatable 위젯 stack 패턴
