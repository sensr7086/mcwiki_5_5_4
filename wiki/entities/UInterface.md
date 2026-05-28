---
type: entity
title: "UInterface / IInterface"
aliases: [UInterface, IInterface, TScriptInterface]
kind: model
sources:
  - "[[sources/ue-coreuobject-interface]]"
tags: [ue, runtime, foundation, coreuobject]
last_updated: 2026-05-09
---

# UInterface / IInterface

## 요약

UE 의 인터페이스 메커니즘 — 2 클래스 페어. UMyInterface (UINTERFACE 메타) + IMyInterface (실제 인터페이스). UMyInterface 는 reflection 정보, IMyInterface 는 메서드. C++ 호출 시 `Execute_*` 매크로로 BP 안전.

## 관계

- 부모 (U-): UInterface (UClass 자손)
- 부모 (I-): UInterface (interface 자체)
- Wrapper: TScriptInterface<IMyInterface>

## 핵심 주장

- UINTERFACE(BlueprintType) 매크로 + IInterface 자손 + UFUNCTION(BlueprintCallable, BlueprintImplementableEvent) 메서드 — 2 클래스 페어 표준.
- C++ 호출: `IMyInterface::Execute_MyMethod(Obj, Args)` — Obj 가 BP 구현한 경우도 안전. `MyObj->MyMethod()` 직접 호출은 BP override 무시.
- TScriptInterface<IMyInterface>: UPROPERTY 멤버 표준 — UObject + Interface 양쪽 보유.
- Implements<T>(): Object 가 인터페이스 구현하는지 검사.
- BP 지원 분기: BlueprintType (BP 구현 가능) / Native-Only Cannot (C++ 만) / MinimalAPI (다른 모듈 cast 가능).

## 열린 질문

- [ ] BP Interface vs Native Interface 결정 트리
- [ ] Diamond inheritance 함정
