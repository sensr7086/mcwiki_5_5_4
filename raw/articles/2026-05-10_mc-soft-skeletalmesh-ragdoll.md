---
title: "MCSoftSkeletalMeshComponent — Ragdoll Design Note"
project: KMCProject
component: UMCSoftSkeletalMeshComponent
ue_version: 5.7.4
date: 2026-05-10
author: KMCProject (Min-Cheol)
related_vault:
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/USkeletalMesh]]"
  - "[[sources/ue-assetclasses-mesh]]"
  - "[[sources/ue-components-physicscomponents]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, runtime, components, skeletalmesh, physics, ragdoll, soft-pointer, async-load]
---

# MCSoftSkeletalMeshComponent — Ragdoll Design Note

> 프로젝트 컴포넌트 `UMCSoftSkeletalMeshComponent` 의 ragdoll 기능 설계서.
> Mesh / AnimClass / Materials 가 모두 `TSoftObjectPtr` 인 비동기 로드 컴포넌트에 PhysicsAsset 도 Soft 로 묶고 풀-바디 / 부분 ragdoll 을 노출.

## 1. 컨텍스트 (왜 만드는가)

KMCProject 의 [[sources/ue-components-meshcomponents]] 호스트 — `USkeletalMeshComponent` 직속 자손인 `UMCSoftSkeletalMeshComponent` 는 **모든 자산 멤버를 `TSoftObjectPtr` 로 보유**해 [[concepts/Soft-Reference-vs-Hard]] 표준을 따른다. SpawnActor 첫 프레임에 Subobject Hard Reference 동기 로드로 발생하는 4단 히칭 ([[concepts/Asset-Loading-Policy]] §3) 을 회피하는 것이 본 컴포넌트의 존재 이유.

[[entities/USkeletalMeshComponent]] 의 *열린 질문 §3* 가 직접 명시: *"PhysicsAsset 의 Ragdoll 시점 — SetSimulatePhysics(true) 의 단계."* 즉 **vault 안에서도 ragdoll 활성 시퀀스가 풀린 적이 없는 영역**. 이 노트는 그 시퀀스를 프로젝트 컨벤션으로 정착시킨다.

대표 사용처 — **MCParts 그래프의 SubSkeletalMesh 노드**가 런타임에 적 NPC 의 본체 메시로 스폰될 때 / **MCStory 의 Action 노드가 캐릭터를 KO 처리** 할 때.

## 2. 설계 결정 — Hard 가 아닌 Soft 로 가는 이유

| 항목 | 결정 | 근거 |
| ---- | ---- | ---- |
| Mesh | `TSoftObjectPtr<USkeletalMesh>` | [[concepts/Asset-Loading-Policy]] §1 — SkeletalMesh 10~100MB+ 는 Soft 표준 |
| AnimClass | `TSoftClassPtr<UAnimInstance>` | 같은 정책 — Class CDO 부담 분리 |
| Override Materials | `TArray<TSoftObjectPtr<UMaterialInterface>>` | 같은 묶음 핸들로 묶어 첫 렌더 PSO 미컴파일 회피 |
| **PhysicsAsset** | **`TSoftObjectPtr<UPhysicsAsset>` (옵션)** | 본문 §3 |

PhysicsAsset 은 [[entities/USkeletalMesh]] 의 *서브오브젝트가 아닌 페어 자산*. SkeletalMesh 자체가 `TObjectPtr<UPhysicsAsset>` 으로 hard 참조하므로 Mesh 가 로드되면 **자동으로 PhysicsAsset 도 따라옴**. 그럼에도 Soft 로 따로 쓸 이유:

1. **다른 PhysicsAsset 으로 덮어쓰기** — 같은 메시에 평소엔 가벼운 Trace-only PhysicsAsset, 사망 시 정밀 ragdoll PhysicsAsset 을 swap. [[sources/ue-assetclasses-mesh]] §5 `SetPhysicsAsset` 패턴.
2. **로딩 분리** — 평소엔 ragdoll 비활성 캐릭터 (UI 프리뷰, 멀리서 보이는 NPC) 는 ragdoll PhysicsAsset 이 필요 없음. Hit / Death 시점에만 비동기 로드 → 메모리 절감.
3. **다수 NPC 환경** — 100명 적이 있어도 실제로 ragdoll 이 되는 건 한 순간에 소수. 미리 hard 로드하면 [[concepts/Asset-Optimization-Policy]] 메모리 영역 부담.

## 3. Ragdoll 활성 시퀀스 (vault 통합)

[[sources/ue-assetclasses-mesh]] §4.2 + [[sources/ue-components-physicscomponents]] §7 + [[entities/USkeletalMeshComponent]] §3 의 사이를 메운다.

### 3.1 풀-바디 Ragdoll (Death / KO)

```cpp
void UMCSoftSkeletalMeshComponent::EnableFullRagdoll()
{
    // 0) 이미 활성 → 무시
    if (bRagdollActive) return;

    // 1) Soft PhysicsAsset 비동기 로드 (선택) — 핸들 Pin 의무
    //    [[concepts/Asset-Loading-Policy]] §2 단계 5
    RequestRagdollActivation(/*bFull=*/true, NAME_None, true);
}

// 콜백 (메인 스레드)
void UMCSoftSkeletalMeshComponent::HandleRagdollPhysicsAssetLoaded(bool bFull, FName, bool)
{
    // 1) Mesh 의 기본 PhysicsAsset 덮어쓰기 (옵션)
    if (UPhysicsAsset* Override = SoftRagdollPhysicsAsset.Get())
        SetPhysicsAsset(Override, /*bForceReInit=*/false);

    // 2) AnimClass 캐싱 + 분리 — AnimGraph 가 본을 다시 가져오지 못 하게
    CachedAnimClassBeforeRagdoll = GetAnimClass();
    SetAnimInstanceClass(nullptr);

    // 3) 콜리전 프로필 백업 + Ragdoll 프로필
    CachedCollisionProfileBeforeRagdoll = GetCollisionProfileName();
    SetCollisionProfileName(RagdollCollisionProfile);   // 보통 "Ragdoll"

    // 4) Constraint Profile (PhysicsAsset 안 정의) — Default / Ragdoll / HitReaction
    SetConstraintProfileForAll(RagdollConstraintProfile, /*bDefault=*/false);

    // 5) 시뮬 활성 — [[sources/ue-assetclasses-mesh]] §7 함정 #6 의무 페어
    SetSimulatePhysics(true);
    SetAllBodiesSimulatePhysics(true);
    WakeAllRigidBodies();

    bRagdollActive = 1;
    OnRagdollStateChanged.Broadcast(this, true);
}
```

### 3.2 부분 Ragdoll (Hit Reaction)

```cpp
void UMCSoftSkeletalMeshComponent::EnablePartialRagdoll(FName BoneName, bool bIncludeSelf)
{
    const FName Pivot = BoneName.IsNone() ? DefaultRagdollPivotBone : BoneName;
    RequestRagdollActivation(/*bFull=*/false, Pivot, bIncludeSelf);
}

// 콜백 — 부분 분기
{
    // AnimInstance *유지* — 본 위는 애니, 아래는 물리 ([[sources/ue-components-physicscomponents]] §7.2)
    SetConstraintProfileForAll(RagdollConstraintProfile, false);
    SetAllBodiesBelowSimulatePhysics(BoneIfPartial, /*bNewSimulate=*/true, bIncludeSelfIfPartial);
    OnRagdollStateChanged.Broadcast(this, true);
}
```

부분 ragdoll 은 `bRagdollActive` 플래그를 켜지 않는다. `IsRagdollActive()` 의 의미를 *풀-바디* 로 한정 — 의도적 비대칭. UI / 게임플레이 로직이 두 상태를 구분해야 할 때 명료해진다. 정밀한 본별 모터 효과가 필요하면 [[sources/ue-components-physicscomponents]] §7 의 `UPhysicalAnimationComponent` 를 별도 컴포넌트로 추가 — 이 클래스는 그 책임을 떠안지 않는다.

### 3.3 비활성 (DisableRagdoll)

```cpp
void UMCSoftSkeletalMeshComponent::DisableRagdoll()
{
    // 진행 중 ragdoll 비동기 로드 취소 — 도착 후 Enable 재호출 회피
    if (RagdollLoadHandle.IsValid()) { RagdollLoadHandle->CancelHandle(); RagdollLoadHandle.Reset(); }

    SetAllBodiesSimulatePhysics(false);
    SetSimulatePhysics(false);
    SetConstraintProfileForAll(NAME_None, /*bDefault=*/true);

    if (!CachedCollisionProfileBeforeRagdoll.IsNone())
        SetCollisionProfileName(CachedCollisionProfileBeforeRagdoll);

    if (bRestoreAnimClassOnDisable && CachedAnimClassBeforeRagdoll)
        SetAnimInstanceClass(CachedAnimClassBeforeRagdoll);

    bRagdollActive = 0;
    OnRagdollStateChanged.Broadcast(this, false);
}
```

## 4. 정책 매핑 (vault concepts)

| 정책 | 본 컴포넌트의 적용 |
| ---- | ----------------- |
| [[concepts/Component-Policies-6]] §1 Mobility | 생성자 `SetMobility(Movable)` |
| [[concepts/Component-Policies-6]] §2 NewObject | `CreateDefaultSubobject` 안 씀 (런타임 add) — 런타임 add 시 `NewObject<T>(Outer=Actor)` 권장 |
| [[concepts/Component-Policies-6]] §3 GC | 모든 UObject 멤버 `UPROPERTY()` + `TObjectPtr` (CachedAnimClassBeforeRagdoll 도 `Transient + UPROPERTY`) |
| [[concepts/Component-Policies-6]] §4 GetOwner 캐싱 | BeginPlay 1회 `CachedOwner = GetOwner()` |
| [[concepts/Component-Policies-6]] §5 Tick | 빈 메시 상태 `bCanEverTick=false` + `SetComponentTickEnabled(false)` 시작 → 로드 완료 후 활성 |
| [[concepts/Component-Policies-6]] §6 CDO | `GetMutableDefault` 사용 안 함 |
| [[concepts/Asset-Loading-Policy]] §2 단계 1 | Mesh / AnimClass / Materials / PhysicsAsset 모두 Soft |
| [[concepts/Asset-Loading-Policy]] §2 단계 2 | Constructor 안 자산 로드 절대 없음 |
| [[concepts/Asset-Loading-Policy]] §2 단계 5 | `FStreamableManager::RequestAsyncLoad` + `LoadHandle` / `RagdollLoadHandle` Pin + EndPlay Cancel |
| [[concepts/Profiling-Scope-Rule]] | 모든 BeginPlay / EndPlay / 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |

## 5. 함정 매트릭스 (vault 함정 표 추출)

[[sources/ue-assetclasses-mesh]] §7 + [[sources/ue-components-physicscomponents]] §11 의 함정을 본 컴포넌트 컨텍스트로 좁힘.

| # | 함정 | 본 컴포넌트의 회피 |
| - | ---- | ----------------- |
| 1 | PhysicsAsset 변경 후 `SetSimulatePhysics(true)` 안 호출 → ragdoll 안 활성 ([[sources/ue-assetclasses-mesh]] §7 #6) | `HandleRagdollPhysicsAssetLoaded` 가 SetPhysicsAsset → SetSimulatePhysics 페어 보장 |
| 2 | AnimGraph 가 본을 매 프레임 덮어써 ragdoll 안 보임 | 풀-바디 시 `SetAnimInstanceClass(nullptr)` 분리, 부분 시 의도적 유지 |
| 3 | 로드 콜백 도착 전 컴포넌트 GC ([[concepts/Asset-Loading-Policy]] §2 단계 5) | 모든 람다 캡처 = `TWeakObjectPtr<this>` + `IsValid` 검사 |
| 4 | DisableRagdoll 후 본이 캡슐 안에 박혀 들어감 | `SnapMeshToOwnerCapsule()` 별도 헬퍼 — Character 일 때 Capsule 기준, 아니면 Root 기준 |
| 5 | 다른 Skeleton 의 SkeletalMesh 로 swap 시 AnimInstance 깨짐 ([[sources/ue-assetclasses-mesh]] §7 #3) | `ApplyLoadedAssets` 에서 SetSkeletalMeshAsset → SetAnimInstanceClass 순서 강제 |
| 6 | Constraint Profile 동적 미사용 → 모든 ragdoll 이 동일 표현 | `RagdollConstraintProfile` UPROPERTY 노출 + `SetRagdollConstraintProfile` BP API |
| 7 | 빈 메시 상태에서 Tick → `RefreshBoneTransforms` 의 잘못된 ref-pose 갱신 | 생성자에서 Tick OFF, Mesh 로드 완료 시 활성 |
| 8 | Ragdoll PhysicsAsset 비동기 로드 중 `DisableRagdoll` 호출 → 도착 후 다시 활성 | `RagdollLoadHandle->CancelHandle()` 의무 |

## 6. 결정 트리 (사용 시점)

```
SkeletalMesh + 비동기 로드 + ragdoll 필요?
├── 일반 캐릭터 + 사망 시 ragdoll
│   └── UMCSoftSkeletalMeshComponent + EnableFullRagdoll()
├── 적 NPC + 피격 hit reaction
│   └── EnablePartialRagdoll(FName("spine_03"), true)
├── 본별 정밀 모터 (관성 잡기)
│   └── + UPhysicalAnimationComponent (vault: [[sources/ue-components-physicscomponents]] §7)
├── 차량 + 파괴
│   └── (다른 컴포넌트) UClusterUnionComponent — vault §8
└── 장식용 / UI 프리뷰 (ragdoll 절대 없음)
    └── SoftRagdollPhysicsAsset 비워두기 → 추가 메모리 0
```

## 7. 체크리스트

- [ ] Mesh / AnimClass / Materials / PhysicsAsset 모두 Soft 인가
- [ ] Constructor 에서 Tick OFF + Mobility=Movable + 콜리전 NoCollision 시작
- [ ] BeginPlay = Super FIRST + `CachedOwner` 1회
- [ ] EndPlay = `LoadHandle` + `RagdollLoadHandle` 둘 다 Cancel + Super LAST
- [ ] 모든 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] 비동기 로드 람다 = `TWeakObjectPtr<this>` + `IsValid` 검사
- [ ] 풀-바디 ragdoll = AnimClass 캐싱 → SetAnimInstanceClass(nullptr) → SetCollisionProfile → SetConstraintProfile → SetSimulatePhysics + WakeAllRigidBodies 순서
- [ ] DisableRagdoll = Cancel handle → SetSimulatePhysics(false) → 콜리전 / AnimClass 복원
- [ ] Cooked Build (Development) `stat unit` 으로 첫 EnableFullRagdoll 시 히칭 검증

## 8. PhysicalAnimation 통합 (본별 모터 효과)

본 절은 [[sources/ue-components-physicscomponents]] §7 의 `UPhysicalAnimationComponent` 를 본 컴포넌트의 1급 시민으로 흡수해 *피격 시 본별 모터 효과 + 자연스러운 hit reaction* 를 한 함수 호출로 끝낸다.

### 8.1 자동 생성 + 바인딩

```cpp
// BeginPlay 안 — bAutoCreatePhysicalAnimation = true 면 자동
EnsurePhysicalAnimationComponent();

// 내부 동작:
//   1) NewObject<UPhysicalAnimationComponent>(Outer = Owner)   ← [[concepts/Component-Policies-6]] §2
//   2) SetSkeletalMeshComponent(this)                            ← [[sources/ue-components-physicscomponents]] §7.2
//   3) RegisterComponent + Owner->AddInstanceComponent(...)
```

- `bAutoCreatePhysicalAnimation = false` 로 두면 `EnsurePhysicalAnimationComponent()` 첫 호출 시 lazy 생성 — UI 프리뷰 / 원거리 NPC 의 메모리 절감.
- **함정 #7** ([[sources/ue-components-physicscomponents]] §11) — Constructor 안 `ApplyPhysicalAnimationProfile*` 호출은 `UnsafeDuringActorConstruction` 위반. 본 컴포넌트는 BeginPlay 이후에만 Apply 가 호출되도록 EnsurePhysicalAnimationComponent 조차 BeginPlay 시점 이후로 미룸.

### 8.2 본별 Profile 적용 (`ApplyMotorProfileBelow`)

```cpp
// PhysicsAsset 안 미리 정의된 Profile (예: "HitReaction") 을 BoneName + 자손 본에 적용
ApplyMotorProfileBelow(BoneName, ProfileName, /*bIncludeSelf=*/true);

// 내부:
//   1) EnsurePhysicalAnimationComponent
//   2) PhysAnim->ApplyPhysicalAnimationProfileBelow(...)
//   3) SetAllBodiesBelowSimulatePhysics(BoneName, true, bIncludeSelf)   // 함정 #8 페어 의무
```

함정 #8 ([[sources/ue-components-physicscomponents]] §11) — *Profile 적용 후 `SetSimulatePhysics` 안 호출하면 모터 효과 0*. `ApplyMotorProfileBelow` 가 두 호출을 묶어주므로 사용자는 신경 쓸 필요 없음.

### 8.3 본별 직접 설정 (`ApplyMotorSettingsBelow`)

Profile 없이 코드에서 즉시 [[sources/ue-components-physicscomponents]] §7.1 의 `FPhysicalAnimationData` 를 채워 적용:

```cpp
FPhysicalAnimationData Data;
Data.bIsLocalSimulation = true;
Data.OrientationStrength = 1000.f;
Data.AngularVelocityStrength = 100.f;
Data.MaxAngularForce = 5000.f;

ApplyMotorSettingsBelow(TEXT("spine_03"), Data);
```

### 8.4 강도 페이드 (`FadeMotorStrength`)

```cpp
// Hit reaction 종료 시 0 으로 페이드 (애니로 자연스럽게 복귀)
GetWorld()->GetTimerManager().SetTimer(FadeTimer, [this]()
{
    static float Strength = 1.f;
    Strength -= 0.1f;
    FadeMotorStrength(Strength);
    if (Strength <= 0.f) DisableRagdoll();
}, 0.05f, true);
```

vault: [[sources/ue-components-physicscomponents]] §7.2 — `SetStrengthMultiplyer(0~1)`.

## 9. 피격 방향 처리 (Hit Direction Impulse)

본 절은 [[sources/ue-components-primitivecomponent]] §AddImpulse / §AddRadialImpulse 를 본 단위 ragdoll 시뮬과 결합한다.

### 9.1 본 단위 임펄스 (`ApplyHitImpulse`)

```cpp
// 본이 이미 시뮬 중이어야 효과 있음 ([[sources/ue-assetclasses-mesh]] §7 함정 #6)
ApplyHitImpulse(BoneName, HitDirection * Strength, /*bVelChange=*/false);

// bVelChange = false → N·s 임펄스 (Mass 영향 — 무거운 본 덜 밀림 — 사실적)
// bVelChange = true  → 즉시 Velocity 변경 (Mass 무시 — 즉각 반응 — 게임적)
```

vault [[sources/ue-components-charactermovementdeep]] §11 의 *bVelChange 차이* 매트릭스를 본 단위 ragdoll 컨텍스트로 차용.

### 9.2 반경 임펄스 (`ApplyRadialHitImpulse`)

```cpp
// 폭발 / 광범위 충격 — 모든 시뮬 본에 거리 falloff 적용
ApplyRadialHitImpulse(ExplosionOrigin, /*Radius=*/500.f, /*Strength=*/3000.f, RIF_Linear);
```

`ERadialImpulseFalloff` — `RIF_Constant` 또는 `RIF_Linear` ([[sources/ue-components-physicscomponents]] §6).

### 9.3 통합 (`OnHitReceived`)

게임 코드에서 가장 자주 호출할 진입점. *부분 ragdoll + Motor Profile + 방향 임펄스* 한 호출:

```cpp
// 피격 — 적이 가슴 (spine_03) 에 정면 피격
const FVector HitDir = (HitTarget - Attacker->GetActorLocation()).GetSafeNormal();
EnemyMesh->OnHitReceived(
    /*BoneName=*/         TEXT("spine_03"),
    /*HitDirection=*/     HitDir,
    /*ImpulseStrength=*/  -1.f,           // -1 = DefaultHitImpulseStrength UPROPERTY
    /*ProfileOverride=*/  NAME_None,      // = HitProfileName UPROPERTY ("HitReaction")
    /*bUseFullRagdoll=*/  false           // 부분 ragdoll
);

// 사망 — 강한 일격
EnemyMesh->OnHitReceived(TEXT("pelvis"), HitDir * 2.f, 2000.f, NAME_None, /*bUseFullRagdoll=*/true);
```

**내부 절차** (vault 4 출처 통합 시퀀스):
1. **Mesh 로드 검증** — `GetSkeletalMeshAsset() == nullptr` 면 reject ([[concepts/Asset-Loading-Policy]] 의 비동기 로드 완료 보장).
2. **Ragdoll 활성** — `bUseFullRagdoll ? EnableFullRagdoll : EnablePartialRagdoll(EffectiveBone)`.
3. **Motor Profile** — `ApplyMotorProfileBelow(EffectiveBone, EffectiveProfile, true)` + `FadeMotorStrength(DefaultHitMotorStrength)`.
4. **방향 정규화 + Upward Bias** — `Dir.Normalize() + Dir.Z += HitUpwardBias` (피격이 너무 평면적이지 않게).
5. **임펄스 적용** — `ApplyHitImpulse(EffectiveBone, Dir * Strength, false)`.

**Upward Bias 의 역할** — `0.25` 기본값. 정면 피격 (HitDir = -Forward) 만으로 임펄스를 주면 본이 옆으로만 밀리고 위로 살짝 떠오르는 자연스러움이 빠진다. Z 성분을 인위적으로 보강해 피격 본이 살짝 떠오르도록.

### 9.4 FHitResult 자동 추출 (`OnHitFromResult`)

UE 의 충돌 콜백 (`OnComponentHit` / `LineTraceSingleByChannel`) 에서 받은 `FHitResult` 를 그대로 넘기면 본 / 방향 / 위치를 자동 추출:

```cpp
void AEnemy::OnTakeDamage(const FHitResult& Hit, float Damage)
{
    if (Damage > 50.f)
    {
        MeshComp->OnHitFromResult(Hit, /*Strength=*/Damage * 30.f, NAME_None, /*bFull=*/false);
    }
}

// 내부 추출:
//   HitBone = Hit.BoneName  (없으면 FindClosestBone(Hit.ImpactPoint, ..., bRequiresPhysicsAsset=true))
//   HitDir  = -Hit.ImpactNormal  (없으면 (TraceEnd - TraceStart).Normalized)
```

vault: 본 자동 선택은 `USkinnedMeshComponent::FindClosestBone(Location, BoneLocation, IgnoreScale, bRequiresPhysicsAsset=true)` 표준 — `bRequiresPhysicsAsset=true` 가 PhysicsAsset 안 정의된 본만 후보로 한정해 ragdoll 가능한 본만 선택.

## 10. 함정 매트릭스 — 갱신

[[sources/ue-assetclasses-mesh]] §7 + [[sources/ue-components-physicscomponents]] §11 의 함정을 본 컴포넌트 + PhysAnim + Hit Direction 컨텍스트로 확장.

| # | 함정 | 본 컴포넌트의 회피 |
| - | ---- | ----------------- |
| 1 | PhysicsAsset 변경 후 `SetSimulatePhysics(true)` 안 호출 ([[sources/ue-assetclasses-mesh]] §7 #6) | `HandleRagdollPhysicsAssetLoaded` 의 5단 시퀀스 |
| 2 | AnimGraph 가 본을 매 프레임 덮어써 ragdoll 안 보임 | 풀-바디 시 `SetAnimInstanceClass(nullptr)`, 부분 시 의도적 유지 |
| 3 | 로드 콜백 도착 전 컴포넌트 GC | `TWeakObjectPtr<this>` + `IsValid` |
| 4 | DisableRagdoll 후 본이 캡슐 안 박힘 | `SnapMeshToOwnerCapsule()` |
| 5 | 다른 Skeleton SkeletalMesh swap 시 AnimInstance 깨짐 | SetSkeletalMeshAsset → SetAnimInstanceClass 순서 강제 |
| 6 | Constraint Profile 동적 미사용 | `RagdollConstraintProfile` UPROPERTY + `SetRagdollConstraintProfile` |
| 7 | 빈 메시 상태 Tick → ref-pose 갱신 오류 | 생성자 Tick OFF, 로드 완료 시 활성 |
| 8 | 진행 중 ragdoll 비동기 로드 중 Disable | `RagdollLoadHandle->CancelHandle` |
| 9 | **PhysAnim Constructor 안 ApplyProfile** ([[sources/ue-components-physicscomponents]] §11 #7) | `EnsurePhysicalAnimationComponent` 가 BeginPlay 시점 이후에만 호출됨 |
| 10 | **PhysAnim Profile 적용 후 SetSimulate 안 호출** ([[sources/ue-components-physicscomponents]] §11 #8) | `ApplyMotorProfileBelow` 안 SetAllBodiesBelowSimulatePhysics 페어 자동 |
| 11 | **AddImpulse 가 시뮬 안 된 본에 적용** ([[sources/ue-assetclasses-mesh]] §7 #6) | OnHitReceived 가 EnablePartial/FullRagdoll 을 선행 |
| 12 | **bVelChange 잘못 선택** ([[sources/ue-components-charactermovementdeep]] §11) | `ApplyHitImpulse(bVelChange=false)` 표준 — N·s 사실적, true 는 과도 게임감 |
| 13 | **HitDirection 이 0 벡터** | `OnHitReceived` 가 Owner 의 -Forward 로 fallback |
| 14 | **HitResult 의 BoneName 비어 있음** | `OnHitFromResult` 가 `FindClosestBone(..., bRequiresPhysicsAsset=true)` 자동 선택 |
| 15 | **평면적 피격 (Z 성분 0)** | `HitUpwardBias` UPROPERTY 기본 0.25 — Z 보강 |

## 11. 결정 트리 — 갱신

```
SkeletalMesh + 비동기 로드 + ragdoll 필요?
├── 일반 캐릭터 + 사망 시 ragdoll
│   └── EnableFullRagdoll() (또는 OnHitReceived(..., bUseFullRagdoll=true))
├── 적 NPC + 피격 hit reaction (방향성 + 본별 모터)
│   └── OnHitReceived(BoneName, HitDir, Strength)   ← 통합 진입점
├── 충돌 콜백 / Trace Hit
│   └── OnHitFromResult(Hit, Damage*30)              ← BoneName + Dir 자동 추출
├── 폭발 (광범위 임펄스)
│   └── EnableFullRagdoll() + ApplyRadialHitImpulse(Origin, Radius, Strength)
├── 본별 모터 만 (Ragdoll 없이 idle 흔들림 등)
│   └── ApplyMotorSettingsBelow / ApplyMotorProfileBelow + 직접 SetSimulate 제어
└── 차량 + 파괴
    └── (다른 컴포넌트) UClusterUnionComponent
```

## 12. 체크리스트 — 갱신

- [ ] Mesh / AnimClass / Materials / PhysicsAsset 모두 Soft 인가
- [ ] Constructor 에서 Tick OFF + Mobility=Movable + 콜리전 NoCollision 시작
- [ ] BeginPlay = Super FIRST + `CachedOwner` 1회 + (옵션) `EnsurePhysicalAnimationComponent`
- [ ] EndPlay = `LoadHandle` + `RagdollLoadHandle` 둘 다 Cancel + Super LAST
- [ ] 모든 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] 비동기 로드 람다 = `TWeakObjectPtr<this>` + `IsValid` 검사
- [ ] PhysAnim 은 BeginPlay 이후만 Apply (`UnsafeDuringActorConstruction` 회피)
- [ ] Profile 적용 후 `SetAllBodiesBelowSimulatePhysics` 페어 (함정 #10) — `ApplyMotorProfileBelow` 가 자동
- [ ] Hit 임펄스는 시뮬 활성된 본에만 (함정 #11) — `OnHitReceived` 가 ragdoll 선행
- [ ] HitDirection 정규화 + Upward Bias 적용
- [ ] DisableRagdoll = Cancel handle → SetSimulate(false) → 콜리전 / AnimClass 복원
- [ ] Cooked Build (Development) `stat unit` 첫 OnHitReceived 시 히칭 검증

## 13. 미해결 / 다음 작업

- [ ] AnimMontage 기반 GetUp 시퀀스 — `URO` / `Inertialization` ([[concepts/Inertialization]]) 와 결합
- [ ] 멀티플레이 — Ragdoll 시뮬 결과를 Authority 가 본 위치를 replicate 할지 cosmetic-only 처리할지 [[sources/ue-networking-skill]] 검토
- [ ] PhysAnim Profile 별 데이터 시트 — "HitReaction" / "DeathHard" / "DeathSoft" 등 표준 Profile 셋업 가이드
- [ ] `OnHitReceived` 의 멀티 본 동시 적용 (예: 양쪽 어깨 + 가슴 동시 피격) — N hits 누적 처리
- [ ] [[entities/USkeletalMeshComponent]] 의 *EVisibilityBasedAnimTickOption 결정 트리* 열린 질문 해소 (URO 문서와 묶어 별도 노트)
- [ ] `MCSoftStaticMeshComponent.cpp` 의 `DEFINE_MC_COMPONENT_BASE` 누락 검증

## 14. 변경 이력

| 날짜 | 변경 |
| ---- | ---- |
| 2026-05-10 | 최초 작성. EnableFullRagdoll / EnablePartialRagdoll / DisableRagdoll / SetRagdollConstraintProfile / SnapMeshToOwnerCapsule + Soft PhysicsAsset 비동기 로드 + 정책 매핑 + 함정 8종 + 결정 트리 + 체크리스트. |
| 2026-05-10 | **PhysAnim 통합 §8** + **Hit Direction Impulse §9** 추가 — `EnsurePhysicalAnimationComponent` / `ApplyMotorProfileBelow` / `ApplyMotorSettingsBelow` / `FadeMotorStrength` / `ApplyHitImpulse` / `ApplyRadialHitImpulse` / `OnHitReceived` / `OnHitFromResult` (8 신규 API). 함정 #9~#15 추가, 결정 트리 / 체크리스트 갱신. UPROPERTY 추가: `bAutoCreatePhysicalAnimation` / `HitProfileName` / `DefaultHitMotorStrength` / `DefaultHitImpulseStrength` / `HitUpwardBias` / `PhysicalAnim`. |
