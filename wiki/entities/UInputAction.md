---
type: entity
title: "UInputAction (Enhanced Input)"
aliases: [UInputAction, InputAction, IA]
kind: model
sources:
  - "[[sources/ue-input-skill]]"
tags: [ue, input, plugin]
last_updated: 2026-05-09
---

# UInputAction

## 요약

5.x Enhanced Input Plugin 의 핵심 자산. **추상화된 입력 동작** (Jump / Move / Aim 등) — 실제 Key 와 분리. ValueType 4 종 (Bool / Axis1D / Axis2D / Axis3D). [[entities/UInputMappingContext]] 가 Action ↔ Key 매핑.

## 관계

- 부모: [[entities/UObject]]
- 페어 자산: [[entities/UInputMappingContext]] (Key 매핑)
- 협력: UInputTrigger (8종) + UInputModifier (9종)
- 런타임: [[entities/UEnhancedInputComponent]]::BindAction

## 핵심 주장

- ValueType (EInputActionValueType) 4 종: Boolean / Axis1D (float) / Axis2D (FVector2D) / Axis3D (FVector). BindAction 콜백 시그니처가 ValueType 에 맞춰 자동.
- ETriggerEvent 7 종: Triggered (매 frame, 활성 동안) / Started / Ongoing / Canceled / Completed / None.
- UInputTrigger 8 종: Pressed / Released / Hold / Tap / Pulse / Chord / Down / Combo. Action 자산에 등록.
- UInputModifier 9 종: DeadZone / Scale / Negate / Swizzle / Smooth / ResponseCurve / FOVScaling / etc.
- 자산 정책: 작은 자산 — Hard Reference OK. PlayerController / Pawn Constructor 안 BP 지정 표준. [[concepts/Asset-Loading-Policy]]
- Profiling 의무: BindAction 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`. Triggered 가 매 프레임. [[concepts/Profiling-Scope-Rule]]

## 열린 질문

- [ ] UInputTrigger 8 종 결정 트리
- [ ] Custom Modifier 작성 패턴
