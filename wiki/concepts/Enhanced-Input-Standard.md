---
type: concept
title: "Enhanced Input 표준 (5.x)"
aliases: [Enhanced Input, EI, 5.x Input Standard]
sources:
  - "[[sources/ue-input-skill]]"
related_concepts:
  - "[[concepts/IMC-Stack]]"
tags: [ue, input, plugin]
last_updated: 2026-05-09
---

# Enhanced Input 표준

## 1. 정의 (한 줄)

5.x 입력 표준 (`Engine/Plugins/EnhancedInput`). [[entities/UInputAction]] (자산) + [[entities/UInputMappingContext]] (Action ↔ Key) + [[entities/UEnhancedInputLocalPlayerSubsystem]] (LocalPlayer 별 IMC stack) + [[entities/UEnhancedInputComponent]] (BindAction). Legacy UInputComponent 의 후속.

## 2. 자세히

흐름:
```
UInputAction 자산 (예: IA_Jump, ValueType=Bool)
    │
UInputMappingContext (예: IMC_Default — IA_Jump ↔ SpaceBar)
    │
사용자 입력 → Subsystem (LocalPlayer 별)
    │
EnhancedInputComponent::BindAction(IA_Jump, Triggered, this, &OnJump)
    │
OnJump(FInputActionValue Value) callback
```

## 3. 변형 / 사례 / 응용

- ETriggerEvent 7 종 + UInputTrigger 8 종 + UInputModifier 9 종 의 조합 — 복잡한 입력 (Hold / Tap / Combo 등) 직관적 표현.
- IMC stack: Priority 기반 동적 전환 ([[concepts/IMC-Stack]]). 메뉴 모드 → 게임 모드 → 차량 모드.
- Couch Co-op: ULocalPlayer 마다 별개 Subsystem.
- Legacy 마이그레이션: BindAction(TEXT("Jump")) → UInputAction 자산 + EnhancedInputComponent BindAction.

## 4. 관련 entity

- [[entities/UInputAction]] · [[entities/UInputMappingContext]] · [[entities/UEnhancedInputLocalPlayerSubsystem]] · [[entities/UEnhancedInputComponent]] · [[entities/FKey]]

## 5. 열린 질문

- [ ] Multiplayer 의 입력 흐름 (Server-side input vs Client prediction)
- [ ] Enhanced Input 의 Modular 확장 (Common Input 5.x)
