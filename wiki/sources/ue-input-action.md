---
type: source
title: "UE Input — Action sub-skill"
slug: ue-input-action
source_path: raw/ue-wiki-llm/skills/Input/references/Action.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UInputAction]]"
tags: [ue, input, plugin]
---

# UE Input — Action sub-skill

> Source: [[raw/ue-wiki-llm/skills/Input/references/Action.md]]
> Parent: [[sources/ue-input-skill]]

## 1. Summary

[[entities/UInputAction]] + ValueType 4 종 (Bool / Axis1D / Axis2D / Axis3D) + ETriggerEvent 7 종 + UInputTrigger 8 종 + UInputModifier 9 종.

## 2. Key claims

- ValueType 4 종: Bool / Axis1D (float) / Axis2D (FVector2D) / Axis3D (FVector). BindAction 콜백 시그니처 자동 결정.
- ETriggerEvent 7 종:
  - **Triggered** (활성 동안 매 frame), **Started** (시작), **Ongoing** (활성 중간), **Canceled** (Hold 중 미충족), **Completed** (정상 종료), **None**.
- UInputTrigger 8 종:
  - **Pressed** (한 번): 누른 frame.
  - **Released** (한 번): 뗀 frame.
  - **Hold**: N 초 유지.
  - **Tap**: N 초 안에 떼기.
  - **Pulse**: N 초마다 발화 (auto-fire).
  - **Chord** (다른 Action 활성 + 본 Action): 조합 키.
  - **Down**: 누르고 있는 동안 매 frame.
  - **Combo**: 시퀀스 입력 (격투 게임).
- UInputModifier 9 종: DeadZone / Scale / Negate / Swizzle / Smooth / ResponseCurve / FOVScaling / etc — value 변환.

## 3. Open questions

- [ ] Custom Trigger / Modifier 작성 패턴
