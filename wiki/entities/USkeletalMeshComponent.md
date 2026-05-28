---
type: entity
title: "USkeletalMeshComponent"
aliases: [USkeletalMeshComponent, SkeletalMeshComponent]
kind: model
sources:
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-assetclasses-skill]]"
  - "[[sources/ue-animation-skill]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
tags: [ue, runtime, components, mesh, animation]
last_updated: 2026-05-10
---

# USkeletalMeshComponent

## 요약

[[entities/UPrimitiveComponent]] 자손. **스켈레탈 메시의 호스트** — [[entities/USkeletalMesh]] + USkeleton 자산 + [[entities/UAnimInstance]] (AnimBlueprint 또는 native). 본 카테고리의 가장 비용 큰 컴포넌트 (매 프레임 Pose 평가). [[concepts/Asset-Optimization-Policy]] 5 중 최적화의 주 대상.

## 관계

- 부모: [[entities/UPrimitiveComponent]]
- 페어 자산: [[entities/USkeletalMesh]] + USkeleton + UPhysicsAsset + [[entities/UAnimSequence]] (DefaultAnim) + [[entities/UAnimMontage]] + UAnimBlueprint
- 호스트: [[entities/ACharacter]] 의 Mesh 멤버
- 변형: USkeletalMeshComponentBudgeted (AnimationBudgetAllocator Plugin)
- 프로젝트 변형: KMCProject 의 `UMCSoftSkeletalMeshComponent` — 모든 자산 멤버 Soft + Ragdoll API ([[sources/mc-soft-skeletalmesh-ragdoll]])

## 핵심 주장

- AnimBlueprint 또는 [[entities/UAnimInstance]] native — `AnimClass` 또는 `AnimInstanceClass` 로 결정. [[entities/UAnimInstance]]
- §7 EVisibilityBasedAnimTickOption (5종): AlwaysTickPoseAndRefreshBones / AlwaysTickPose / OnlyTickMontagesWhenNotRendered / OnlyTickPoseWhenRendered / OnlyTickMontagesAndRefreshBonesWhenPlayingMontages. → [[concepts/EVisibilityBasedAnimTickOption]]
- §6 [[concepts/URO]] (UpdateRateOptimization): 거리/Significance 기반 Animation Tick 주기 분할 (매 프레임 → 2/4/8 프레임 마다). [[concepts/URO]]
- [[concepts/Bone-LOD]]: USkeletalMeshLODSettings 의 BonesToRemove / Prioritize — LOD 별 본 수 감소. [[concepts/Asset-Optimization-Policy]]
- AnimationBudgetAllocator Plugin: USkeletalMeshComponentBudgeted 자동 등록 → 프레임 budget 안에서 우선순위 큰 캐릭터부터 Tick. [[raw/ue-wiki-llm/references/12_AssetOptimizationPolicy.md]]
- 다수 NPC (50+) 환경 = URO + Visibility + Significance + AnimSharing + Budget 5 중 누적.
- **PhysicsAsset → Ragdoll 시퀀스 6 단계** — Soft PhysicsAsset 비동기 로드 → AnimClass 캐싱 + 분리 → 콜리전/Constraint Profile → SetSimulatePhysics(true) + WakeAllRigidBodies. 부분 ragdoll 은 AnimClass *유지* + SetAllBodiesBelowSimulatePhysics. 자세한 함정 8종 + 결정 트리는 [[sources/mc-soft-skeletalmesh-ragdoll]].

## 열린 질문

- [ ] EVisibilityBasedAnimTickOption 5 종의 결정 트리 (어느 옵션을 언제)
- [x] ~~PhysicsAsset 의 Ragdoll 시점 — SetSimulatePhysics(true) 의 단계~~ — [[sources/mc-soft-skeletalmesh-ragdoll]] §3 으로 해소 (2026-05-10)
