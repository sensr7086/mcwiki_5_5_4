---
type: entity
title: "FSlateBrush"
aliases: [FSlateBrush, FSlateImageBrush, FSlateBoxBrush, FSlateBorderBrush]
kind: model
sources:
  - "[[sources/ue-slatecore-skill]]"
tags: [ue, slate, ui]
last_updated: 2026-05-09
---

# FSlateBrush

## 요약

Slate 의 텍스처 + 색상 + 마진 wrapper. FSlateImageBrush (단순 이미지) / FSlateBoxBrush (9-slice) / FSlateBorderBrush (테두리) / FSlateColorBrush (단색). [[entities/FSlateStyleSet]] 에서 등록되어 ID 로 lookup.

## 관계

- 자손 변형: ImageBrush / BoxBrush / BorderBrush / ColorBrush
- 사용처: [[entities/FSlateDrawElement]]::MakeBox 의 brush 인자

## 핵심 주장

- 9-slice (FSlateBoxBrush): 코너 / 가장자리 / 중심 9 영역 — 크기에 따라 코너는 보존 + 중심은 늘어남. UI 패널 표준.
- ImageSize: 픽셀 단위. DPI scaling 적용.
- TintColor: 추가 색상 multiplier.
- DrawAs: Image / Box / Border — DrawElement 의 호출 변경.
- 5.x 표준: SlateBrush 의 텍스처는 [[entities/UTexture]] (UTexture2D) 직접 또는 FSlateAtlas 단편.

## 열린 질문

- [ ] FSlateAtlas 의 동적 등록 패턴
- [ ] TintColor 의 ColorAndOpacity 와의 차이
