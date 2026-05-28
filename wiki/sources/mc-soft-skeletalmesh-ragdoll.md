---
type: source
title: "MCSoftSkeletalMeshComponent — Ragdoll + PhysAnim + Hit Direction (KMCProject)"
slug: mc-soft-skeletalmesh-ragdoll
source_path: raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md
source_kind: design-note
source_date: 2026-05-10
ingested: 2026-05-10
related_entities:
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/USkeletalMesh]]"
  - "[[entities/UPrimitiveComponent]]"
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
tags: [ue, runtime, components, skeletalmesh, physics, ragdoll, physanim, hit-reaction, validation, project, kmcproject]
---

# MCSoftSkeletalMeshComponent — Ragdoll + PhysAnim + Hit Direction Design

> Source: [[raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md]]
> Kind: design-note · Date: 2026-05-10 · Ingested: 2026-05-10
> Project: KMCProject · Component: `UMCSoftSkeletalMeshComponent`

## 1. Summary

KMCProject 의 `UMCSoftSkeletalMeshComponent` (모든 자산 멤버 Soft 인 `USkeletalMeshComponent` 자손) 위에 **Ragdoll + UPhysicalAnimationComponent 통합 + 피격 방향 임펄스** 를 설계. 1차 §1~§7 = ragdoll 활성/비활성 시퀀스 + Soft PhysicsAsset 비동기 로드. 2차 §8~§9 = [[sources/ue-components-physicscomponents]] §7 의 PhysAnim 을 1급 시민으로 흡수해 *피격 시 본별 모터 + 방향성 임펄스* 한 함수 호출. 3차 적용 = 모든 silent return 사이트를 [[concepts/MC-Asset-Validation-Policy]] 의 LOG / ensure 매크로로 갈아끼움 (LOG 사이트 19개 + ensure 사이트 1개).

## 2. Key claims

- **PhysicsAsset Soft 분리** — 평소 가벼운 trace-only / 사망 시 정밀 ragdoll PhysicsAsset swap, ragdoll 없는 캐릭터 메모리 절감, 다수 NPC hit/death 시점만 비동기 로드. [§2](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#2)
- **풀-바디 활성 6 단계** — Soft PhysicsAsset 비동기 로드 + Pin → AnimClass 캐싱 + nullptr 분리 → 콜리전 백업/Ragdoll 프로필 → Constraint Profile → SetSimulatePhysics(true) + WakeAllRigidBodies → bRagdollActive=1 + Broadcast. [§3.1](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#31)
- **부분 ragdoll = AnimClass 유지** — [[sources/ue-components-physicscomponents]] §7.2. SetAllBodiesBelowSimulatePhysics 만. `bRagdollActive` 의도적 비대칭 (풀-바디만 true). [§3.2](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#32)
- **PhysAnim 자동 생성 + 바인딩 (`EnsurePhysicalAnimationComponent`)** — BeginPlay 이후 `NewObject<UPhysicalAnimationComponent>(Owner)` + `SetSkeletalMeshComponent(this)` + `RegisterComponent`. Constructor 안 호출 = `UnsafeDuringActorConstruction` 위반 ([[sources/ue-components-physicscomponents]] §11 함정 #7) — 본 컴포넌트의 *유일한 ensure 사이트* (`HasBegunPlay()` 검사). [§8.1](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#81-자동-생성--바인딩)
- **`ApplyMotorProfileBelow` = ApplyPhysicalAnimationProfileBelow + SetSimulate 페어** — 함정 #8 ([[sources/ue-components-physicscomponents]] §11) 의 *Profile 적용 후 SetSimulate 안 호출하면 모터 효과 0* 을 사용자가 신경 쓰지 않게 두 호출을 묶음. [§8.2](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#82)
- **`FadeMotorStrength`** — [[sources/ue-components-physicscomponents]] §7.2 SetStrengthMultiplyer(0~1) wrapper. Hit reaction 종료 시 0 fade-out. [§8.4](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#84)
- **`ApplyHitImpulse(BoneName, Impulse, bVelChange)`** — [[sources/ue-components-primitivecomponent]] AddImpulse 위임. [[sources/ue-components-charactermovementdeep]] §11 의 *bVelChange=false (N·s, Mass 영향, 사실적) vs true (Velocity 즉시, Mass 무시, 게임적)* 매트릭스를 본 단위 ragdoll 컨텍스트로 차용. 본이 시뮬 중이어야 효과 — 함정 #11. [§9.1](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#91)
- **`ApplyRadialHitImpulse`** — [[sources/ue-components-primitivecomponent]] AddRadialImpulse 위임 (RIF_Linear / RIF_Constant). 폭발 / 광범위 충격. [§9.2](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#92)
- **`OnHitReceived` 5 단계 통합** — Mesh 로드 검증 → Enable Full/Partial Ragdoll → ApplyMotorProfileBelow + FadeMotorStrength → Dir 정규화 + `HitUpwardBias` Z 보강 → ApplyHitImpulse. 게임 코드 진입점. [§9.3](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#93)
- **`OnHitFromResult` 자동 추출** — `Hit.BoneName` 비면 `FindClosestBone(Hit.ImpactPoint, ..., bRequiresPhysicsAsset=true)`, 방향 = `-Hit.ImpactNormal` (없으면 trace 방향). UE 충돌 콜백 즉시 연결. [§9.4](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#94)
- **함정 매트릭스 15종** — 1~8 ragdoll, 9~10 PhysAnim, 11~12 Impulse, 13~14 HitDirection / HitResult, 15 평면 피격 회피. [§10](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#10)
- **결정 트리** — 충돌 콜백 → `OnHitFromResult`, 적 NPC 피격 → `OnHitReceived`, 폭발 → `EnableFullRagdoll + ApplyRadialHitImpulse`, 본별 모터만 → `ApplyMotorSettings/ProfileBelow`. [§11](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#11)
- **정책 매핑 완전** — [[concepts/Component-Policies-6]] 6대 + [[concepts/Asset-Loading-Policy]] §2 단계 5 + [[concepts/Profiling-Scope-Rule]] + **[[concepts/MC-Asset-Validation-Policy]]** (LOG 사이트 19 + ensure 사이트 1). 모든 silent return 제거. [§4 / §12](raw/articles/2026-05-10_mc-soft-skeletalmesh-ragdoll.md#12)
- **MCParts/MCStory 통합점** — `SubSkeletalMesh` 노드가 적 NPC 본체 호스트, MCStory Action 노드가 `OnHitReceived` / `EnableFullRagdoll` 트리거. KMCProject 두 그래프 시스템 사이의 hit-reaction 표준 다리.

## 3. Quotations

> "PhysicsAsset 변경 시 `SetSimulatePhysics(true)` 안 호출 → Ragdoll 안 활성." — [[sources/ue-assetclasses-mesh]] §7 함정 #6
>
> "PhysAnim 적용 후 `SetSimulatePhysics` 안 호출 → 모터 효과 안 남." → 함정 #8 — [[sources/ue-components-physicscomponents]] §11
>
> "`ApplyPhysicalAnimationProfileBelow` 생성자 안 호출 — `UnsafeDuringActorConstruction` — BeginPlay 이후" → 본 컴포넌트 **유일한 ensure 사이트** ([[concepts/MC-Asset-Validation-Policy]] §4) — [[sources/ue-components-physicscomponents]] §11 함정 #7
>
> "`AddImpulse(bVelChange=true)` 즉시 Velocity 변경 (Mass 무시) — 점프/폭발 즉시 반응" — [[sources/ue-components-charactermovementdeep]] §11
>
> "PhysicsAsset 의 Ragdoll 시점 — SetSimulatePhysics(true) 의 단계" — [[entities/USkeletalMeshComponent]] *열린 질문* §3 (본 노트 §3+§9 로 해소)

## 4. Open questions / next sources

- [ ] AnimMontage 기반 GetUp 시퀀스 — [[concepts/Inertialization]] / [[sources/ue-animation-rootmotion]] 결합
- [ ] 멀티플레이 — Ragdoll 시뮬 cosmetic-only vs Authority replicate 결정 ([[sources/ue-networking-skill]])
- [ ] PhysAnim Profile 별 데이터 시트 — "HitReaction" / "DeathHard" / "DeathSoft"
- [ ] `OnHitReceived` 멀티 본 동시 적용 (양쪽 어깨 + 가슴 동시 피격) — N hits 누적
- [ ] [[entities/USkeletalMeshComponent]] *EVisibilityBasedAnimTickOption 결정 트리* 열린 질문 해소
- [ ] `MCSoftStaticMeshComponent.cpp` `DEFINE_MC_COMPONENT_BASE` 누락 검증
- [ ] 다른 MC 컴포넌트로 [[concepts/MC-Asset-Validation-Policy]] 일괄 적용 ([[sources/mc-asset-validation-policy]] §9)
