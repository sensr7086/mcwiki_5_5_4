---
type: source
title: "UE GameFramework — PawnCharacter sub-skill"
slug: ue-gameframework-pawncharacter
source_path: raw/ue-wiki-llm/skills/GameFramework/references/PawnCharacter.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/APawn]]"
  - "[[entities/ACharacter]]"
  - "[[entities/UCharacterMovementComponent]]"
related_concepts:
  - "[[concepts/RootMotion]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/URO]]"
tags: [ue, runtime, gameframework, character]
---

# UE GameFramework — PawnCharacter sub-skill

> Source: [[raw/ue-wiki-llm/skills/GameFramework/references/PawnCharacter.md]]
> Parent: [[sources/ue-gameframework-skill]]

## 1. Summary

[[entities/APawn]] (598) + [[entities/ACharacter]] (1,095) 합본. Jump / Crouch / Landing / [[concepts/RootMotion]] + 5 종 Movement 모드. **§6 다수 NPC 환경 최적화 10 종**.

## 2. Deep references

- [[sources/ue-gameframework-characteroptimization]] — 최적화 10 종 + AI vs Player 9 매트릭스 + 결정 트리

## 3. Key claims

- APawn: Controller 가 Possess 가능. SetupPlayerInputComponent (Possess 시 자동).
- ACharacter: Capsule + SkeletalMesh + [[entities/UCharacterMovementComponent]] 강제 페어. Jump / Crouch / Launch / OnLanded.
- bIsCrouched 복제 — Capsule HalfHeight + MaxWalkSpeedCrouched.
- 최적화 10 종: PrimaryActorTick 비활성 / Component Tick 분산 / [[concepts/URO]] / EVisibilityBasedAnimTickOption / Bone LOD / Significance / AnimationBudgetAllocator / AnimSharing / Network / AI vs Player.
- AI vs Player 분기: AAIController = ServerAuthoritative + 비-cosmetic, APlayerController = Local + cosmetic 풀.
- Multiplayer: Server Authoritative + Client Prediction (FSavedMove_Character).

## 4. Open questions

- [ ] PhysCustom override 패턴 (grappling / wall run)
