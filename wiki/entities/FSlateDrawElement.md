---
type: entity
title: "FSlateDrawElement / FSlateBrush"
aliases: [FSlateDrawElement, FSlateBrush, MakeBox, MakeText]
kind: model
sources:
  - "[[sources/ue-slatecore-skill]]"
tags: [ue, slate, ui, rendering]
last_updated: 2026-05-09
---

# FSlateDrawElement / FSlateBrush

## 요약

Slate 의 그리기 명령 — [[entities/SWidget]]::OnPaint 안에서 누적. MakeBox / MakeText / MakeLines / MakeSpline / MakeViewport / MakeCubicBezierSpline 등의 정적 헬퍼. FSlateBrush 는 텍스처 / 색상 / 마진 의 wrapping.

## 관계

- 사용자: [[entities/SWidget]]::OnPaint
- 협력: FSlateBrush (텍스처/색), [[entities/FSlateStyleSet]] (스타일 룩업)

## 핵심 주장

- OnPaint(Args, Geometry, ..., OutDrawElements, LayerId, ...) 안에서 `FSlateDrawElement::MakeBox(OutDrawElements, ++LayerId, Geometry.ToPaintGeometry(), &Brush, Tint)` 형태로 호출.
- LayerId: depth — 큰 LayerId 가 위. 매 호출마다 ++ 증가.
- FSlateBrush = `*FAppStyle::GetBrush("MyBrush")` 또는 `FSlateImageBrush(Texture, Size)`.
- MakeText: 폰트 (FSlateFontInfo) + 텍스트 + Geometry + Style.
- 5.x deprecation: 옛 FVector2D 좌표는 `UE_REPORT_SLATE_VECTOR_DEPRECATION=1` 으로 경고.

## 열린 질문

- [ ] LayerId 의 GPU 측 sort 동작
- [ ] FSlateImageBrush vs FSlateBoxBrush 결정 트리
