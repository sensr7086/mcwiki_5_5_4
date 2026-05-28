---
type: concept
title: "Slate Paint Cycle"
aliases: [OnPaint, Paint Cycle, OnArrangeChildren]
sources:
  - "[[sources/ue-slatecore-skill]]"
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
tags: [ue, slate, ui]
last_updated: 2026-05-09
---

# Slate Paint Cycle

## 1. 정의 (한 줄)

[[entities/SWidget]] 의 매 프레임 paint 사이클 — Tick → ComputeDesiredSize → OnArrangeChildren → OnPaint (재귀, root → leaf). LayerId 기반 z-order.

## 2. 자세히

```
[[entities/FSlateApplication]]::Tick (매 프레임)
    │
    ├─▶ Tick (각 SWidget 의 OnTick)
    │
    ├─▶ ComputeDesiredSize (자식의 ideal size 계산, 재귀 leaf → root)
    │
    ├─▶ OnArrangeChildren (자식의 [[entities/FGeometry]] 결정, root → leaf)
    │
    └─▶ OnPaint (재귀, root → leaf)
        ├─▶ FSlateDrawElement::MakeBox / MakeText / 등 누적
        ├─▶ LayerId 증가 (depth)
        └─▶ 자식의 OnPaint 호출 (자식 LayerId += parent 의 max)
```

## 3. 변형 / 사례 / 응용

- LayerId: 큰 LayerId 가 위. OnPaint 안에서 `++LayerId` 로 그리기 명령마다 증가.
- Custom OnPaint override: SCompoundWidget 자손 또는 SLeafWidget 자손에서 override. NativeOnPaint vs OnPaint 함정 (NativeOnPaint 는 SCompoundWidget 의 자식 paint 호출 skip).
- 5.x: SLATE_USE_RETAINER_BOX_AS_PARENT 등 CVar — Retainer 를 부모 처럼 보이게 (digital twin).

## 4. 관련 entity

- [[entities/SWidget]] · [[entities/FSlateDrawElement]] · [[entities/FGeometry]]

## 5. 열린 질문

- [ ] NativeOnPaint vs OnPaint override 의 함정 카탈로그
- [ ] OnPaint 안 GPU 명령 (RDG) 통합
