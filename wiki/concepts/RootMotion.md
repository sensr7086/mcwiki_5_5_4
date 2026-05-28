---
type: concept
title: "Root Motion"
aliases: [RootMotion, Root Motion, FRootMotionSource, IAnimRootMotionProvider]
sources:
  - "[[sources/ue-animation-skill]]"
related_concepts:
  - "[[concepts/Inertialization]]"
tags: [ue, runtime, animation, movement]
last_updated: 2026-05-09
---

# Root Motion

## 1. 정의 (한 줄)

AnimSequence / AnimMontage 의 root bone 변환이 [[entities/ACharacter]] 의 *이동* 을 구동하는 패턴 — Animator 가 디자인한 모션의 정확한 거리/타이밍을 그대로 게임에 반영.

## 2. 자세히

흐름:
```
AnimSequence (bEnableRootMotion=true)
    │
    ├─▶ Update_AnyThread → root bone delta 추출
    │
    ▼
[[entities/UAnimInstance]] / FRootMotionSource
    │
    ▼
IAnimRootMotionProvider (5.x)
    │
    ▼
[[entities/UCharacterMovementComponent]] (CMC)
    │
    ├─▶ ApplyRootMotionToVelocity / Position
    └─▶ Server Authoritative + Client Prediction
```

- **AnimMontage 의 RootMotion**: Character 의 `bEnableRootMotionMontagesOnly` 또는 IAnimRootMotionProvider.
- **FRootMotionSource 7 종**: ConstantForce / RadialForce / MoveToActorForce / MoveToForce / JumpForce / Custom / etc. CMC 의 ApplyRootMotionSource.
- **Multiplayer**: Server Authoritative — RootMotion 으로 인한 위치 변경도 동일하게 동기.

## 3. 변형 / 사례 / 응용

- **사용처**: 격투 게임의 어택 모션 (정확한 push / pull), 처형 모션 (캐릭터 정확한 위치 이동), 점프 인 어택, 기어 (climbing).
- **함정**: bEnableRootMotion 활성 모션이 BlendSpace 에 들어가면 root motion 이 합성되어 의도와 다른 이동.
- **5.x IAnimRootMotionProvider**: 더 일반화된 인터페이스 — Mesh-space / Component-space 변환 지원.

## 4. 관련 entity

- [[entities/UAnimSequence]] · [[entities/UAnimMontage]]
- [[entities/UAnimInstance]] · [[entities/UCharacterMovementComponent]] · [[entities/ACharacter]]

## 5. 열린 질문

- [ ] BlendSpace + RootMotion 의 흔한 함정 카탈로그
- [ ] Listen Server vs Dedicated 의 RootMotion replication 차이
