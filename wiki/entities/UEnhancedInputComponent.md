---
type: entity
title: "UEnhancedInputComponent"
aliases: [UEnhancedInputComponent, BindAction]
kind: model
sources:
  - "[[sources/ue-input-skill]]"
tags: [ue, input, plugin, components]
last_updated: 2026-05-09
---

# UEnhancedInputComponent

## 요약

UInputComponent 자손 (Enhanced Input Plugin). [[entities/APlayerController]] / [[entities/APawn]] 의 InputComponent 의 5.x 표준 형. `BindAction(InputAction, ETriggerEvent, this, &MyClass::Handler)` 패턴.

## 관계

- 부모: UInputComponent → [[entities/UActorComponent]]
- 호스트: [[entities/APlayerController]] (Possess 시 SetupPlayerInputComponent 안에서 셋업), [[entities/APawn]]

## 핵심 주장

- BindAction 시그니처: `BindAction(IA_Jump, ETriggerEvent::Started, this, &AMyChar::OnJumpStarted)`. ETriggerEvent 7 종 중 선택.
- 콜백 시그니처: `void OnJumpStarted(const FInputActionValue& Value)`. Value.Get<bool>() / Get<FVector2D>() / Get<FVector>() — UInputAction 의 ValueType 에 맞게.
- Priority: 같은 Action 의 다중 BindAction 시 등록 순서로 처리. bConsumeInput 으로 차단.
- Possess 흐름: PC->Possess(Pawn) → Pawn->PossessedBy(PC) → Pawn->SetupPlayerInputComponent(InputComponent).
- 6 대 정책 ([[concepts/Component-Policies-6]]): UInputComponent 자손이라 자동 적용.

## 열린 질문

- [ ] BindActionValue (UEnhancedInputComponent 5.x) — value 직접 binding
- [ ] 같은 Action 의 다중 binding 우선순위 결정
