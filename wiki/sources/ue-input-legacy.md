---
type: source
title: "UE Input — Legacy sub-skill"
slug: ue-input-legacy
source_path: raw/ue-wiki-llm/skills/Input/references/Legacy.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/FKey]]"
tags: [ue, input, migration]
---

# UE Input — Legacy sub-skill

> Source: [[raw/ue-wiki-llm/skills/Input/references/Legacy.md]]
> Parent: [[sources/ue-input-skill]]

## 1. Summary

UInputComponent (legacy) + InputDevice + Force Feedback 4 채널 + Haptic 5.x 4 종 — Migration 5 단계 (DefaultInput.ini → IMC).

## 2. Key claims

- Legacy UInputComponent: BindAction(TEXT("Jump"), IE_Pressed, ...) — 4.x 표준. 5.x 에서는 Enhanced Input 권장.
- DefaultInput.ini: Legacy ActionMappings + AxisMappings — Project Settings 의 Input 패널.
- IInputDevice / IInputInterface: Custom RawInput device — 특수 컨트롤러 (HOTAS / Wheel / steering).
- Force Feedback: UForceFeedbackEffect 자산 + 4 채널 (Left Large / Left Small / Right Large / Right Small) + IForceFeedbackInterface.
- Haptic 5.x 4 종: HapticFeedbackEffect_Buffer / Curve / SoundWave / Native — VR 컨트롤러 진동 (OpenXR).
- Migration 5 단계 (Legacy → Enhanced):
  1. Project Settings 의 Action/Axis Mappings 식별.
  2. UInputAction 자산 생성 (각 ActionMapping → IA).
  3. UInputMappingContext 자산 생성 (DefaultInput.ini 의 매핑 반영).
  4. SetupPlayerInputComponent 의 BindAction(TEXT(...)) → BindAction(IA, ETriggerEvent::Triggered, ...).
  5. Subsystem->AddMappingContext(IMC, 0).

## 3. Open questions

- [ ] Force Feedback 4 채널 의 Gamepad 별 매핑 차이
