---
type: entity
title: "ACharacter"
aliases: [ACharacter, Character]
kind: model
sources:
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, gameframework, character]
last_updated: 2026-05-09
---

# ACharacter

## 요약

[[entities/APawn]] 자손. **두 발 캐릭터의 표준** — UCapsuleComponent (RootComponent) + [[entities/USkeletalMeshComponent]] (Mesh) + [[entities/UCharacterMovementComponent]] (CMC) 의 페어 강제. 1,095 lines. Jump / Crouch / Launch / RootMotion 통합.

## 관계

- 부모: [[entities/APawn]] → [[entities/AActor]]
- 강제 컴포넌트: UCapsuleComponent + [[entities/USkeletalMeshComponent]] + [[entities/UCharacterMovementComponent]]
- 협력: [[entities/UAnimInstance]] (Mesh 의 AnimBP)

## 핵심 주장

- 3 종 컴포넌트가 Constructor 에서 CreateDefaultSubobject — Capsule (콜리전+RootComponent) + Mesh (시각, attach to Capsule) + CMC (이동 로직). [[raw/ue-wiki-llm/skills/GameFramework/SKILL]]
- Jump: Jump() → CMC 의 DoJump → MOVE_Falling 전환 → JumpZVelocity 적용. JumpMaxHoldTime 으로 변동.
- Crouch: Crouch() / UnCrouch(). bIsCrouched 가 Replicated. Crouch 시 Capsule HalfHeight 변경 + MaxWalkSpeedCrouched.
- Launch: LaunchCharacter(Velocity, OverrideXY, OverrideZ) — 임펄스 적용.
- [[concepts/RootMotion]]: AnimMontage 의 root motion 이 Character 이동 구동 (Server Authoritative). bUseControllerRotationYaw / bOrientRotationToMovement 로 회전 정책.
- Landing 이벤트: OnLanded(Hit). FallingMovementMode → Walking 전환 시 호출.

## 열린 질문

- [ ] CMC 와 ACharacter 의 책임 분담 — 어디까지 CMC, 어디부터 ACharacter
- [ ] RootMotion 의 Multiplayer 동기화 (Server Authoritative vs Client Prediction)
