---
type: entity
title: "FGeometry / FArrangedChildren"
aliases: [FGeometry, FArrangedChildren, FArrangedWidget]
kind: model
sources:
  - "[[sources/ue-slatecore-skill]]"
tags: [ue, slate, ui]
last_updated: 2026-05-09
---

# FGeometry / FArrangedChildren

## 요약

Slate 위젯의 layout 결과. FGeometry (위젯의 size + transform + DPI scale) + FArrangedChildren (자식의 Geometry 배열). [[entities/SWidget]]::OnArrangeChildren 의 출력. OnPaint / 입력 hit test 의 입력.

## 관계

- 사용자: [[entities/SWidget]]::OnPaint, OnArrangeChildren, ComputeDesiredSize
- 협력: FSlateLayoutTransform / FSlateRenderTransform (5.x)

## 핵심 주장

- AbsoluteSize: pixel 단위 size. LocalSize: Slate 단위 (DPI scaling 전).
- Local-to-Absolute / Absolute-to-Local 변환 — 입력 hit test 의 핵심.
- 5.x 권장: FVector2f / FVector2d (대신 FVector2D 는 deprecated 경고).
- DPI scaling: OS 의 사용자 설정 (125%/150% 등) 자동 반영.
- FArrangedChildren::AddWidget(EVisibility::Visible, FArrangedWidget(Child, Geometry)).

## 열린 질문

- [ ] FSlateLayoutTransform vs FSlateRenderTransform 차이
- [ ] 5.x FVector2f 마이그레이션의 함정
