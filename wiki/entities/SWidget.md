---
type: entity
title: "SWidget"
aliases: [SWidget, TSharedRef<SWidget>]
kind: model
sources:
  - "[[sources/ue-slatecore-skill]]"
  - "[[sources/ue-slate-skill]]"
tags: [ue, slate, ui, foundation]
last_updated: 2026-05-09
---

# SWidget

## 요약

SlateCore 의 모든 위젯 베이스. C++ 의 abstract class. TSharedRef / TSharedPtr 으로만 보유 — UPROPERTY 안 됨 (UObject 가 아님). [[entities/UWidget]] (UMG) 가 SWidget 을 wrapping. 핵심 가상: Construct (slate macro 스타일) / OnPaint / ComputeDesiredSize / OnArrangeChildren / 입력 callback.

## 관계

- 자손 ~50+: SButton / STextBlock / SImage / SListView / SDockTab / SBorder / SHorizontalBox / SVerticalBox / ...
- Wrapper: [[entities/UWidget]] (UMG, UObject 자손)
- Owner: [[entities/FSlateApplication]] / [[entities/UPanelWidget]]

## 핵심 주장

- TSharedRef/TSharedPtr 강제 — `MakeShared<SButton>()` 또는 `SNew(SButton)` 매크로.
- Slate Construct 매크로: `SLATE_BEGIN_ARGS(SMyWidget) ... SLATE_END_ARGS` + `void Construct(const FArguments& InArgs)`.
- OnPaint(Args, Geometry, Culling, OutDrawElements, LayerId, Style, ColorTint) → FSlateDrawElement::MakeBox/Text/Line 등으로 그리기.
- ComputeDesiredSize: 자식의 ideal size 계산. OnArrangeChildren: 자식 Geometry 결정.
- [[concepts/Slate-Invalidation]]: Volatile (매 프레임 invalidate) vs Cached (변경 시만). SInvalidationPanel / SRetainerPanel 로 비싼 위젯 캐싱.

## 열린 질문

- [ ] OnPaint 의 NativeOnPaint vs OnPaint override 함정
- [ ] SLATE_ATTRIBUTE / TAttribute / TSlateAttribute 차이
