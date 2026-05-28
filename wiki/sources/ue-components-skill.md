---
type: source
title: "UE 5.7.4 Components Module — Main SKILL"
slug: ue-components-skill
source_path: raw/ue-wiki-llm/skills/Components/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UActorComponent]]"
  - "[[entities/USceneComponent]]"
  - "[[entities/UPrimitiveComponent]]"
  - "[[entities/UStaticMeshComponent]]"
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/UCharacterMovementComponent]]"
  - "[[entities/UNiagaraComponent]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Mobility]]"
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, runtime, components]
---

# UE 5.7.4 Components Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Components/SKILL.md]]

## 1. Summary

UE 의 모든 게임 로직 + 시각/물리/오디오/입력 동작이 컴포넌트 위에서 실행. AActor 자체는 거의 비어있고 부착된 컴포넌트가 동작 담당. ~90 개 컴포넌트. 15 sub-skill 분할.

## 2. Key claims

- 베이스 사슬: UObject → [[entities/UActorComponent]] → [[entities/USceneComponent]] → [[entities/UPrimitiveComponent]] → 전문 자손.
- 6 대 의무 정책 → [[concepts/Component-Policies-6]] · [[raw/ue-wiki-llm/references/10_ComponentPolicies.md]]
- 자산 멤버 정책 → [[concepts/Asset-Loading-Policy]] · [[raw/ue-wiki-llm/references/11_AssetLoadingPolicy.md]]
- 5 대 최적화 → [[concepts/Asset-Optimization-Policy]] · [[raw/ue-wiki-llm/references/12_AssetOptimizationPolicy.md]]
- 횡단 의무: [[concepts/Profiling-Scope-Rule]] · TActorIterator 금지 ([[concepts/Global-Iterator-Avoidance]]).

## 3. Sub-skills (15 — Phase 4B 완료)

### 베이스 3
- [[sources/ue-components-actorcomponent]] — UActorComponent 로직 전용 + 라이프사이클 + Replication
- [[sources/ue-components-scenecomponent]] — USceneComponent 트랜스폼 + Mobility + Sockets
- [[sources/ue-components-primitivecomponent]] — UPrimitiveComponent 콜리전 + 렌더 + 물리

### 시각 / 메시
- [[sources/ue-components-meshcomponents]] — StaticMesh / SkeletalMesh / HISM (5중 최적화)
- [[sources/ue-components-shapecomponents]] — Box / Sphere / Capsule (트리거 / Pawn capsule)
- [[sources/ue-components-lightcomponents]] — Point/Spot/Rect/Directional/Sky + Mobility 매트릭스
- [[sources/ue-components-renderingcomponents]] — Decal / TextRender / SceneCapture / PostProcess / RVT
- [[sources/ue-components-atmospherecomponents]] — SkyAtmosphere / HeightFog / VolumetricCloud / Wind

### 동작 / 물리
- [[sources/ue-components-movementcomponents]] — CMC + FloatingPawn + Projectile + Rotating
- [[sources/ue-components-physicscomponents]] — Constraint / Handle / Thruster / RadialForce / SpringArm

### 미디어
- [[sources/ue-components-audiocomponent]] — UAudioComponent + Attenuation + Concurrency + MetaSounds
- [[sources/ue-components-particlecomponents]] — Niagara + Cascade + VectorField (AutoRelease 풀)

### 시스템 / 카메라 / 특수
- [[sources/ue-components-cameracomponent]] — UCameraComponent + UCineCameraComponent (5.x)
- [[sources/ue-components-systemcomponents]] — InputComponent + ChildActor + WorldPartitionStreamingSource
- [[sources/ue-components-specialcomponents]] — Spline / SplineMesh / Timeline / StereoLayer

## 4. Open questions

- [ ] `UCharacterMovementComponent` 의 5 종 모드 + 복제 동작 디테일
- [ ] `UPostProcessComponent` 와 Material Domain=PostProcess 의 cross-link
- [ ] 5.x Element System (UPlacementSubsystem) 가 Component-Lifecycle 에 미치는 영향

## 5. Cross-link

### Cycle 5p reverse-link 보강 (med confidence missing)

- **횡단 정책 (references)**:
  - [[sources/ue-ref-10-componentpolicies]] — Components 6 대 의무 정책 (Mobility / NewObject·DuplicateObject / GC 방어 / GetOwner 캐싱 / PrimaryComponentTick / CDO) 정밀판. §2 의 6 대 의무 인용 소스.
  - [[sources/ue-ref-12-assetoptimizationpolicy]] — Bone LOD / StaticMesh LOD / HISM·HLOD·WorldPartition / Audio Culling / Niagara Quality Scaling 5 대 영역. §2 의 5 대 최적화 + §3 시각·메시·미디어 sub-skill 적용 대상.
  - [[sources/ue-ref-09-globaliteratorpolicy]] — TActorIterator/TObjectIterator/TObjectRange 회피 + 등록 패턴 + AssetRegistry 우선. §2 의 횡단 의무 (TActorIterator 금지) 인용 소스.

- **자산 페어**:
  - [[sources/ue-assetclasses-mesh]] — StaticMesh + SkeletalMesh + Skeleton + PhysicsAsset 자산 정의. §3 시각/메시 sub-skill (meshcomponents) 의 호스트↔자산 페어.
