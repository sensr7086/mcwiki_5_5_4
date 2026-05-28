---
type: source
title: "UE Input — EnhancedInput sub-skill"
slug: ue-input-enhancedinput
source_path: raw/ue-wiki-llm/skills/Input/references/EnhancedInput.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UInputAction]]"
  - "[[entities/UInputMappingContext]]"
  - "[[entities/UEnhancedInputLocalPlayerSubsystem]]"
  - "[[entities/UEnhancedInputComponent]]"
related_concepts:
  - "[[concepts/Enhanced-Input-Standard]]"
tags: [ue, input, plugin]
---

# UE Input — EnhancedInput sub-skill

> Source: [[raw/ue-wiki-llm/skills/Input/references/EnhancedInput.md]]
> Parent: [[sources/ue-input-skill]]

## 1. Summary

5.x Enhanced Input Plugin 메인 — [[entities/UInputAction]] + [[entities/UInputMappingContext]] + Modifier/Trigger + [[entities/UEnhancedInputLocalPlayerSubsystem]] + [[entities/UEnhancedInputComponent]] + 4 단 셋업.

## 2. Key claims

- 4 단 셋업:
  1. UInputAction 자산 작성 (Editor): IA_Move (Axis2D), IA_Jump (Bool), IA_Look (Axis2D).
  2. UInputMappingContext 자산 작성: IMC_DefaultGame — Move ↔ WASD + LeftStick, Jump ↔ SpaceBar + GamepadFaceButtonBottom.
  3. APawn / APlayerController BP 또는 C++ 에 IMC + IA 지정.
  4. SetupPlayerInputComponent 안에서 BindAction(IA, ETriggerEvent::Triggered, this, &OnMove).
- BeginPlay 또는 Possess 시 Subsystem 에 AddMappingContext(IMC, Priority).
- 5 종 핵심: InputAction / InputMappingContext / Trigger / Modifier / EnhancedInputComponent / Subsystem.
- Pawn / PlayerController 통합: Pawn 의 SetupPlayerInputComponent 표준 위치.

## 3. Open questions

- [ ] Pawn vs PC 어디서 BindAction 결정 트리
