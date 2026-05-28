---
type: entity
title: "UUserWidget"
aliases: [UUserWidget, BP Widget, Widget Blueprint]
kind: model
sources:
  - "[[sources/ue-umg-skill]]"
tags: [ue, umg, ui]
last_updated: 2026-05-09
---

# UUserWidget

## 요약

UContentWidget 자손. **BP 위젯의 베이스** — 디자이너가 디자이너 패널에서 트리 짜고 BP 노드로 동작 작성. CreateWidget<UMyUserWidget>(Owner, WidgetClass) 으로 생성. PreConstruct / Construct / Tick / Destruct 라이프사이클.

## 관계

- 부모: UContentWidget → [[entities/UPanelWidget]] → [[entities/UWidget]]
- 자손: 사용자 정의 UMyHUDWidget, UMyMenuWidget 등
- 협력: WidgetTree (UWidgetTree, 자식 위젯 컨테이너), [[entities/UPanelSlot]]

## 핵심 주장

- Native callback: NativePreConstruct / NativeConstruct / NativeTick / NativeDestruct + BP 페어 (PreConstruct / Construct / Tick / Destruct).
- Super 호출 규약: NativeConstruct/NativePreConstruct → Super FIRST, NativeDestruct → Super LAST. 위반 시 invalidation 깨짐. → [[concepts/UMG-Super-Call-Convention]]
- WidgetClass = TSubclassOf<UUserWidget> (Hard) 또는 TSoftClassPtr<UUserWidget> (Soft, 권장). [[concepts/Asset-Loading-Policy]]
- CreateWidget 첫 호출 = BP 컴파일 + SWidget 트리 생성 (큰 비용). 메뉴/HUD = Map 시작 시 사전 PreLoad.
- BindWidget specifier: `UPROPERTY(meta=(BindWidget))` — BP 디자이너의 명시적 위젯 ↔ C++ 멤버 바인딩.
- BindWidgetAnim: AnimationBlueprint 와 동일 패턴.

## 열린 질문

- [ ] CommonUI Plugin 5.x 와의 통합 (Activatable Widget)
- [ ] WidgetPool 패턴 (UMG 위젯 재사용)
