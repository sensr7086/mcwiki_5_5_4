---
type: entity
title: "FSlateStyleSet / FAppStyle"
aliases: [FSlateStyleSet, FAppStyle, FCoreStyle, FSlateStyleRegistry]
kind: model
sources:
  - "[[sources/ue-slatecore-skill]]"
tags: [ue, slate, ui]
last_updated: 2026-05-09
---

# FSlateStyleSet / FAppStyle

## 요약

Slate 의 스타일 시스템 — 이름 ↔ 위젯 모양 (브러시 / 폰트 / 색) 매핑. FSlateStyleSet (베이스) + FAppStyle (Editor 의 표준) + FCoreStyle (런타임 코어) + FSlateStyleRegistry (등록).

## 관계

- 사용처: 모든 [[entities/SWidget]] / FButtonStyle / FTextBlockStyle / FCheckBoxStyle 등의 베이스
- Editor 표준: FAppStyle::Get() (`Style/Roboto.ttf` 등)
- Game 표준: FCoreStyle::Get()

## 핵심 주장

- 등록 패턴: 모듈의 StartupModule() 안에서 `FSlateStyleSet StyleSet("MyStyle")` 생성 + `Set("MyBrush", new FSlateImageBrush(...))` + `FSlateStyleRegistry::RegisterSlateStyle(StyleSet)`.
- 사용 패턴: `FAppStyle::GetBrush("Icons.Edit")` 또는 `FAppStyle::GetWidgetStyle<FButtonStyle>("Button")`.
- 5.x 변화: FEditorStyle (UE 4.x) 가 FAppStyle 으로 통합 — Editor 의 단일 AppStyle.
- 게임 UI 의 표준: 자체 SlateStyleSet 등록 — UMG 의 디테일 패널에서 선택 가능.

## 열린 질문

- [ ] FAppStyle 과 FCoreStyle 의 결정 트리 (Editor vs Game)
- [ ] 5.x StyleSet 의 동적 reload 패턴 (스타일 변경 hot reload)
