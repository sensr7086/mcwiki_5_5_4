---
type: entity
title: "UCharacterMovementComponent"
aliases: [UCharacterMovementComponent, CharacterMovementComponent, CMC]
kind: model
sources:
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, components, movement]
last_updated: 2026-05-09
---

# UCharacterMovementComponent

## 요약

[[entities/UActorComponent]] 자손 (UMovementComponent → UNavMovementComponent → UPawnMovementComponent → 본 클래스). [[entities/ACharacter]] 의 페어 — Walk / Falling / Swimming / Flying / Custom 5 종 모드 + 복제 (FSavedMove + Server Authoritative). RootMotion 통합 진입점.

## 관계

- 부모: UPawnMovementComponent → UNavMovementComponent → UMovementComponent → [[entities/UActorComponent]]
- 호스트: [[entities/ACharacter]] (CharacterMovement 멤버)
- 협력: [[entities/UAnimInstance]] (RootMotion provider)
- 협력 컴포넌트: UCapsuleComponent (Character 의 RootComponent) + [[entities/USkeletalMeshComponent]] (Mesh)

## 핵심 주장

- 5 종 모드 (`EMovementMode`): MOVE_None / MOVE_Walking / MOVE_NavWalking / MOVE_Falling / MOVE_Swimming / MOVE_Flying / MOVE_Custom. SetMovementMode 로 전환. [[sources/ue-gameframework-skill]]
- 복제 동작: Client Prediction + Server Reconciliation. ServerMove / ClientAdjustPosition / FSavedMove_Character 패턴. [[raw/ue-wiki-llm/skills/GameFramework/SKILL.md]]
- RootMotion 통합: bEnableRootMotionMontagesOnly / IAnimRootMotionProvider 5.x. AnimMontage 의 root motion 이 Character 이동을 구동. [[concepts/RootMotion]]
- Phys* 함수들 (PhysWalking / PhysFalling / 등) 가 모드별 Tick 처리. Custom 모드는 PhysCustom 으로 override.
- 자주 쓰는 프로퍼티: MaxWalkSpeed / JumpZVelocity / GravityScale / GroundFriction / MaxAcceleration.

## 열린 질문

- [ ] FSavedMove_Character 의 압축/언압축 패턴 — 커스텀 변수 추가 시
- [ ] PhysCustom 으로 grappling hook / wall run 구현 표준 패턴
