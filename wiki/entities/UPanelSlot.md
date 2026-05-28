---
type: entity
title: "UPanelSlot"
aliases: [UPanelSlot, UCanvasPanelSlot, UHorizontalBoxSlot, UGridSlot]
kind: model
sources:
  - "[[sources/ue-umg-skill]]"
tags: [ue, umg, ui]
last_updated: 2026-05-09
---

# UPanelSlot

## 요약

UVisual 자손. **자식 배치 메타 — Panel 종류별 전용 자손**. UCanvasPanelSlot (Anchor / Position / Size) / UHorizontalBoxSlot (Padding / Size / VerticalAlign) / UGridSlot (Row / Col / Span) 등. AddChild 반환값을 Cast 해 사용.

## 관계

- 부모: UVisual → [[entities/UObject]]
- 자손: 각 [[entities/UPanelWidget]] 종류별 (UCanvasPanelSlot / UVerticalBoxSlot / 등)

## 핵심 주장

- 각 Panel 마다 전용 Slot 자손 — Cast 필요. 잘못된 Slot 자손으로 cast 시 nullptr.
- UCanvasPanelSlot: SetAnchors(FAnchors) + SetPosition(FVector2D) + SetSize(FVector2D) + SetAlignment(FVector2D) + SetZOrder(int32). Editor 디자이너에서 주 사용.
- UHorizontalBoxSlot / UVerticalBoxSlot: SetSize(FSlateChildSize) (Fill ratio 또는 Auto) + SetPadding(FMargin) + SetVerticalAlignment / SetHorizontalAlignment.
- UGridSlot: SetRow / SetColumn / SetRowSpan / SetColumnSpan.
- 5.x: Slot 의 일부 (UCanvasPanelSlot 등) 가 native C++ structs 로 대체 검토 — 메모리/속도 ↑.

## 열린 질문

- [ ] FAnchors 의 미리 정의 매크로 (TopLeft / Center / FillScreen 등)
- [ ] UCanvasPanelSlot 의 Z-order 결정 트리
