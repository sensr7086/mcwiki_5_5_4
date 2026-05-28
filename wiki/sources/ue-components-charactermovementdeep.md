---
type: source
title: "UE Components — CharacterMovement Deep"
slug: ue-components-charactermovementdeep
source_path: raw/ue-wiki-llm/skills/Components/references/MovementComponents/CharacterMovementDeep.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/UCharacterMovementComponent]]"
tags: [ue, components, movement, deep]
---

# UE Components — CharacterMovement Deep

> Source: [[raw/ue-wiki-llm/skills/Components/MovementComponents/references/CharacterMovementDeep.md]]
> Parent: [[sources/ue-components-movementcomponents]]

## 1. Summary

[[entities/UCharacterMovementComponent]] 깊이 자료 — Floor 검출 (FFindFloorResult + ComputeFloorDist) + Step Up + Movement Base + Jump 6 필드 / Crouch / RootMotion / NavWalking / RVO / Force 9 개 시스템.

## 2. Key claims

- Floor 검출: FFindFloorResult / ComputeFloorDist — 지면 감지의 정확한 알고리즘.
- Step Up: StepUpInternal / DoJump — 계단 / 장애물 자동 올라가기.
- Movement Base: BasedMovement — 움직이는 platform (배 / 차량) 위 standing.
- Jump 6 필드: JumpZVelocity / JumpMaxHoldTime / JumpMaxCount / JumpHoldForce / 등.
- Crouch: bWantsToCrouch + Capsule HalfHeight 변경 + MaxWalkSpeedCrouched.
- RootMotion 통합: bEnableRootMotionMontagesOnly + IAnimRootMotionProvider.
- NavWalking: Navmesh 위 simulation (AI 표준).
- RVO: Reciprocal Velocity Obstacles (군중 회피) — bUseRVOAvoidance.
- Force 9 종: AddForce / AddImpulse / LaunchCharacter / etc.
