---
type: entity
title: "FKey / EKeys"
aliases: [FKey, EKeys, InputCore]
kind: model
sources:
  - "[[sources/ue-input-skill]]"
tags: [ue, input]
last_updated: 2026-05-09
---

# FKey / EKeys

## 요약

InputCore 모듈의 핵심 — UE 의 모든 입력 key 를 추상화한 struct. EKeys 정적 namespace 에 200+ key 정의. 플랫폼 추상화 (Xbox / PlayStation / Generic gamepad 통합).

## 관계

- 자체 모듈: InputCore (Engine 모듈)
- 사용처: [[entities/UInputMappingContext]] (Action ↔ Key 매핑), Legacy InputComponent::BindAction

## 핵심 주장

- 분류: Mouse (X / Y / LeftMouseButton) / Keyboard (A~Z / 0~9 / SpaceBar / Escape / ...) / Gamepad (Xbox: Gamepad_LeftThumbstick_X / Gamepad_FaceButton_Bottom) / Touch (Touch1~10) / VR / Gesture (Pinch / Swipe).
- Face Button 추상화: Gamepad_FaceButton_Bottom (= Xbox A / PlayStation Cross) — 플랫폼 차이 흡수.
- EKeys::IsValid / IsModifierKey / IsAxisKey 헬퍼.
- Legacy InputComponent BindAction 의 키 인자: `BindAction(TEXT("Jump"), IE_Pressed, ...)` — Project Settings → Input 의 Action Mappings 와 페어.
- 5.x Enhanced Input 에서는 IMC 안 에서 FKey 사용 — DefaultInput.ini 매핑 우회.

## 열린 질문

- [ ] Gamepad 의 platform-specific 매핑 (Switch Pro Controller 등)
- [ ] VR Controller 의 FKey 표준 (OpenXR)
