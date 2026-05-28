---
type: entity
title: "UWidget / UVisual"
aliases: [UWidget, UVisual, UMG Widget]
kind: model
sources:
  - "[[sources/ue-umg-skill]]"
tags: [ue, umg, ui]
last_updated: 2026-05-09
---

# UWidget

## 요약

[[entities/UObject]] 자손 (UVisual → UWidget). UMG 의 모든 위젯의 베이스. 50+ 자손. 내부적으로 TSharedRef<[[entities/SWidget]]> 를 만들어 Slate 사이클에 진입. 자손 분류: UPanelWidget (자식 N) / UContentWidget (자식 1) / ULeafWidget (자식 X) / UListViewBase.

## 관계

- 부모: UVisual → [[entities/UObject]]
- 자손: [[entities/UPanelWidget]] / UContentWidget / ULeafWidget / UListViewBase / [[entities/UUserWidget]] (특수)
- Wrapper of: [[entities/SWidget]] (TakeWidget 으로 연결)

## 핵심 주장

- TakeWidget(): 내부 TSharedRef<SWidget> 반환 — Slate 와 통합점.
- RebuildWidget(): SWidget 재생성 — Editor 측 Construction 또는 런타임 첫 표시 시.
- SynchronizeProperties(): UWidget 의 속성 → SWidget 으로 동기화.
- Visibility (ESlateVisibility 5종): Visible / Collapsed / Hidden / HitTestInvisible / SelfHitTestInvisible.
- 모든 UMG 위젯은 BP 노출 — 디테일 패널에서 편집.

## 열린 질문

- [ ] RebuildWidget vs SynchronizeProperties 호출 순서
- [ ] PreConstruct vs Construct vs RebuildWidget 의 정확한 라이프사이클
