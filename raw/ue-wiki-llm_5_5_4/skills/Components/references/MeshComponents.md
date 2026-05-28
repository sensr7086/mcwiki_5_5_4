---
name: components-meshcomponents
description: UStaticMeshComponent + USkeletalMeshComponent + UInstancedStaticMeshComponent + UHierarchicalISMC - SkeletalMesh Tick 최적화 5종 (URO/EVisibilityBasedAnimTickOption) + 6대 정책.
---

# Components · MeshComponents sub-skill

> **모듈**: Engine (Tier 1)
> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/`
> **다루는 범위**: 9개 메시 컴포넌트 — `UMeshComponent` (베이스) → `UStaticMeshComponent` / `USkinnedMeshComponent` → `USkeletalMeshComponent` / `UInstancedSkinnedMeshComponent` / `UPoseableMeshComponent` + `UInstancedStaticMeshComponent` / `UHierarchicalInstancedStaticMeshComponent` / `USplineMeshComponent` + `UModelComponent`.

---

## 🚨 공통 정책 (Components 6대 의무)

> 모든 컴포넌트는 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) 의 5대 정책 적용.

| # | 정책 | 핵심 규칙 |
|---|------|-----------|
| 1 | **Mobility** | 생성자에서 `Static`/`Stationary`/`Movable` 명시. 런타임 `SetMobility` 금지 ([§1](../../../references/10_ComponentPolicies.md#1-mobility-정책-ecomponentmobilitystatic-stationary-movable)) |
| 2 | **NewObject + DuplicateObject** | Constructor=`CreateDefaultSubobject` / 런타임=`NewObject<T>(this)` / Deep copy=`DuplicateObject<T>(Source, Outer)` ([§2](../../../references/10_ComponentPolicies.md#2-newobject--duplicateobject-정책)) |
| 3 | **GC 방어** | UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>`. 비-UCLASS = `TStrongObjectPtr<T>` ([§3](../../../references/10_ComponentPolicies.md#3-gc-방어-전략)) |
| 4 | **GetOwner 캐싱** | `BeginPlay` 에서 `TWeakObjectPtr<AOwner>` 1회 캐싱. Tick/콜백 안 매번 Cast 금지 ([§4](../../../references/10_ComponentPolicies.md#4-getowner-캐싱-정책)) |
| 5 | **PrimaryComponentTick** | 기본 `bCanEverTick = false`. 필요 시 `TickInterval` 우선 (0.1~1s). 매 프레임 = 마지막 수단 ([§5](../../../references/10_ComponentPolicies.md#5-primarycomponenttick-정책)) |
| 6 | **CDO** | `GetMutableDefault` 로 CDO 변경 금지. `PostInitProperties` 안 `HasAnyFlags(RF_ClassDefaultObject)` 검사. `CreateDefaultSubobject` 는 Constructor 안만 ([§6](../../../references/10_ComponentPolicies.md#6-cdo-class-default-object-정책)) |
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — **StaticMesh / SkeletalMesh / Material / PhysicsAsset 모두 Soft + UAssetManager 표준** (큰 자산). Mesh 변경 = `SetStaticMesh` / `SetSkeletalMesh` 직전 `RequestAsyncLoad` 사전 호출. ISM/HISM = 메시 자체 Hard (1회 Spawn) + 인스턴스 데이터만 동적. **TextureStreaming + bForceMiplevelsToBeResident** 사전 — 첫 GPU 업로드 히칭 회피. AnimBP = SkeletalMesh 의존 — Bundle 묶음 PreLoad. |
| 🎯 **어셋 최적화** | 🚨 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) — **§1 SkeletalMesh Bone LOD** (USkeletalMeshLODSettings + BonesToRemove 70/50/30/15% + BonesToPrioritize head/hand/weapon_socket + LODHysteresis 0.05 + 5.x SkinCacheUsage LOD 별) + **§2 StaticMesh LOD** (ScreenSize 표준 1.0/0.5/0.25/0.1/0.05 + 5.x Nanite 결정 매트릭스 + AutoComputeLODScreenSize + MinLOD 플랫폼별) + **§3 Actor Merging** (HISM 동일 메시 100+ / Mesh Merge 작은 영역 / HLOD 큰 영역 / 5.x WorldPartition HLOD 오픈 월드). **§7 SkeletalMesh Tick 최적화** (이 sub-skill 본문 §7 — URO + EVisibilityBasedAnimTickOption 5종 + AnimationBudgetAllocator) 가 §1 Bone LOD 와 통합 — **다수 NPC 환경 = §6 통합 매트릭스 (LOD 5단계 9개 항목)**. |

---

## 1. 개요

UE 의 **3D 메시 표시** 컴포넌트 묶음. `UPrimitiveComponent` 자손 + `UMeshComponent` (Material 슬롯 통합 베이스) → 정적/스킨/인스턴스 분류.

**상속 트리**:

```
UPrimitiveComponent (콜리전 + 렌더 베이스)
├── UMeshComponent                 — Material 슬롯 시스템 베이스
│   ├── UStaticMeshComponent       — 단일 메시
│   │   ├── UInstancedStaticMeshComponent (ISM) — N개 인스턴스
│   │   │   └── UHierarchicalInstancedStaticMeshComponent (HISM) — Foliage/대량
│   │   └── USplineMeshComponent   — 스플라인 따라 휜 메시
│   └── USkinnedMeshComponent      — 스켈레탈 베이스 (애니 X)
│       ├── USkeletalMeshComponent — 애니메이션 통합 (가장 큰 컴포넌트 — 2857줄)
│       ├── UInstancedSkinnedMeshComponent — 5.x 신규 GPU 인스턴스 스킨
│       └── UPoseableMeshComponent — 코드 직접 본 조작
└── UModelComponent                — BSP/Brush 모델 (구식)
```

---

## 2. 핵심 헤더

| 클래스 | 위치 | 라인 수 | 핵심 특징 |
|--------|------|--------|----------|
| `UMeshComponent` | `MeshComponent.h` | (작음) | Material 슬롯 |
| `UStaticMeshComponent` | `StaticMeshComponent.h` | 1000 | UStaticMesh 참조 |
| `USkinnedMeshComponent` | `SkinnedMeshComponent.h` | (~2000) | 스켈레탈 베이스 |
| `USkeletalMeshComponent` | `SkeletalMeshComponent.h` | **2857** | 애니메이션 통합 — 가장 무거움 |
| `UInstancedStaticMeshComponent` | `InstancedStaticMeshComponent.h` | (대) | ISM — 인스턴스 데이터 |
| `UHierarchicalInstancedStaticMeshComponent` | `HierarchicalInstancedStaticMeshComponent.h` | (대) | HISM — 컬링/LOD |
| `USplineMeshComponent` | `SplineMeshComponent.h` | (중) | 스플라인 따라 휨 |
| `UPoseableMeshComponent` | `PoseableMeshComponent.h` | (소) | 본 직접 조작 |
| `UInstancedSkinnedMeshComponent` | `InstancedSkinnedMeshComponent.h` | (5.x) | GPU 스킨 인스턴스 |
| `UModelComponent` | `ModelComponent.h` | (구식) | BSP |

---

## 3. UStaticMeshComponent

### 3.1 자주 쓰는 API

| API | 의미 |
|-----|------|
| `void SetStaticMesh(UStaticMesh* NewMesh)` | 메시 교체 |
| `UStaticMesh* GetStaticMesh() const` | |
| `void SetMaterial(int32 ElementIndex, UMaterialInterface*)` | (UPrimitiveComponent §5.2) |
| `void SetForcedLodModel(int32 NewForcedLodModel)` | LOD 강제 (1-based) |
| `void SetLODDataCount(uint32 MinSize, uint32 MaxSize)` | |
| `bool SetLightmapResolution(int32 NewResolution, bool bOverride)` | 라이트맵 해상도 |

### 3.2 함정

- `UStaticMesh` 가 nullptr 인 채로 등록 — 바운드 0 → 컬링 됨
- LOD 자동 — 거리 기반. `SetForcedLodModel(N)` 으로 강제 가능
- 메시 변경 후 콜리전 갱신 필요 — `BodyInstance` 가 자동 처리하지만 시뮬 중이면 `RecreatePhysicsState()` 호출

---

## 4. UInstancedStaticMeshComponent (ISM)

### 4.1 사용 — 동일 메시 N개

```cpp
UInstancedStaticMeshComponent* ISM = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("ISM"));
ISM->SetStaticMesh(MyMesh);
ISM->SetMaterial(0, MyMaterial);

// 인스턴스 추가 (FTransform 배열)
TArray<FTransform> Transforms;
for (int32 i = 0; i < 1000; i++)
{
    Transforms.Add(FTransform(FRotator::ZeroRotator, FVector(i * 200, 0, 0)));
}
ISM->AddInstances(Transforms, /*bShouldReturnIndices=*/false);
```

### 4.2 자주 쓰는 API

| API | 의미 |
|-----|------|
| `int32 AddInstance(const FTransform& InstanceTransform, bool bWorldSpace=false)` | 1개 추가 |
| `TArray<int32> AddInstances(const TArray<FTransform>&, bool bShouldReturnIndices=false, bool bWorldSpace=false)` | 다중 |
| `bool RemoveInstance(int32 InstanceIndex)` | |
| `bool RemoveInstances(const TArray<int32>& InstancesToRemove)` | 다중 (역순 자동) |
| `void ClearInstances()` | |
| `int32 GetInstanceCount() const` | |
| `bool GetInstanceTransform(int32 InstanceIndex, FTransform& OutInstanceTransform, bool bWorldSpace=false) const` | |
| `bool UpdateInstanceTransform(int32 InstanceIndex, const FTransform&, bool bWorldSpace=false, bool bMarkRenderStateDirty=false, bool bTeleport=false)` | |
| `void SetCustomData(int32 InstanceIndex, TArrayView<const float> CustomData)` | 인스턴스별 머티리얼 파라미터 |
| `int32 NumCustomDataFloats` | (UPROPERTY) — 인스턴스당 float 개수 |

### 4.3 ISM Custom Data — 인스턴스별 Material 파라미터

```cpp
// 머티리얼 그래프에서 GetPerInstanceCustomData(0~N) 노드 사용
ISM->NumCustomDataFloats = 4;       // 4개 float per instance
ISM->SetCustomData(InstanceIdx, { Health, Damage, Speed, Color });
```

매 인스턴스 별로 다른 색·HP·진행도 등 표현 가능 — MID 없이.

---

## 5. UHierarchicalInstancedStaticMeshComponent (HISM)

ISM 확장 — **공간 분할 트리** + **자동 컬링** + **자동 LOD 분배**. Foliage 시스템과 풀들이 사용.

| 추가 API | 의미 |
|----------|------|
| `void BuildTreeIfOutdated(bool bAsync, bool bForce)` | 공간 분할 트리 빌드 |
| `void Flatten(bool bForce=false)` | 평탄화 |
| `int32 InstanceCountToRender` | 현재 렌더링 인스턴스 수 |

> **선택 가이드**:
> - 인스턴스 < 100, 정적 위치 → **ISM** 충분
> - 인스턴스 > 1000, 컬링 중요 → **HISM**
> - 잎/풀/돌멩이 → HISM (Foliage 시스템 자동 사용)

---

## 6. USplineMeshComponent

스플라인 곡선을 따라 메시 변형. 도로/케이블/파이프 등.

```cpp
USplineMeshComponent* Mesh = CreateDefaultSubobject<USplineMeshComponent>(TEXT("Mesh"));
Mesh->SetStaticMesh(RoadSegment);
Mesh->SetStartAndEnd(Point0, Tangent0, Point1, Tangent1, /*bUpdateMesh=*/true);
```

| API | 의미 |
|-----|------|
| `void SetStartAndEnd(FVector StartPos, FVector StartTangent, FVector EndPos, FVector EndTangent, bool bUpdateMesh)` | 시작/끝 위치 + 탄젠트 |
| `void SetForwardAxis(ESplineMeshAxis::Type)` | 메시 어느 축이 spline 진행 방향 |
| `void SetSplineUpDir(const FVector& InSplineUpDir, bool bUpdateMesh)` | Up 벡터 |
| `void SetStartScale(FVector2D StartScale, bool bUpdateMesh)` / `SetEndScale(...)` | 시작/끝 스케일 |
| `void SetStartRoll(float StartRoll, bool bUpdateMesh)` / `SetEndRoll(...)` | 롤 |

---

## 7. USkeletalMeshComponent — Tick 최적화 (가장 중요)

### 7.1 USkinnedMeshComponent 베이스

| 멤버 | 의미 |
|------|------|
| `EVisibilityBasedAnimTickOption VisibilityBasedAnimTickOption` (L694) | **가시성 기반 Tick 정책 (5종)** |
| `bool bEnableUpdateRateOptimizations:1` (L820) | URO 활성 |
| `bool bDisplayDebugUpdateRateOptimizations:1` (L826) | 디버그 표시 |
| `bool bComponentUseFixedSkelBounds:1` (L767) | 고정 바운드 (성능 + 컬링 정확도 ↓) |
| `bool bRenderStatic:1` (L832) | 정적 렌더 (애니 X) |
| `FAnimUpdateRateParameters* AnimUpdateRateParams` (L2026) | URO 파라미터 |
| `bool ShouldUseUpdateRateOptimizations() const` (L2032) | 사용 여부 |

### 7.2 🚨 EVisibilityBasedAnimTickOption — 5종 (SkinnedMeshComponent.h L84)

```cpp
enum class EVisibilityBasedAnimTickOption : uint8
{
    AlwaysTickPoseAndRefreshBones,                     // 0. 가장 비쌈
    AlwaysTickPose,                                    // 1.
    OnlyTickMontagesAndRefreshBonesWhenPlayingMontages,// 2.
    OnlyTickMontagesWhenNotRendered,                   // 3.
    OnlyTickPoseWhenRendered,                          // 4. 가장 가벼움
};
```

| 옵션 | 보이는 동안 | 안 보이는 동안 | 비용 | 사용처 |
|------|------------|---------------|------|--------|
| `AlwaysTickPoseAndRefreshBones` | Tick + RefreshBones | **Tick + RefreshBones** | 매우 높음 | 본을 코드/콜리전이 항상 사용 — 거의 사용 X |
| `AlwaysTickPose` | Tick + RefreshBones | **Tick만 (RefreshBones X)** | 높음 | 본 위치 코드에서 필요 (소켓·콜라이더) |
| `OnlyTickMontagesAndRefreshBonesWhenPlayingMontages` | Tick + RefreshBones | **몽타주 재생 중에만 Tick + RefreshBones** | 중간 | 몽타주 가끔 — 렌더 안 될 때도 |
| `OnlyTickMontagesWhenNotRendered` | Tick + RefreshBones | **몽타주만 Tick** (모든 그래프 X) | 낮음 | 5.x 권장 — 표준 NPC |
| `OnlyTickPoseWhenRendered` | Tick + RefreshBones | **아무것도 안 함** | 가장 낮음 | 안 보일 때 정지 OK — 배경 NPC |

### 7.3 사용 패턴

```cpp
USkeletalMeshComponent* Mesh = GetMesh();
Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
// 안 보일 때 완전 정지
```

### 7.4 URO (UpdateRate Optimizations) — 자세히

거리 기반으로 Tick 빈도 자동 조절:

```cpp
Mesh->bEnableUpdateRateOptimizations = true;
// AnimUpdateRateParams 가 자동으로 거리 → UpdateRate 매핑
// 가까이: 매 프레임 (1)
// 중간: 2-3 프레임마다 (2~3)
// 멀리: 4-5 프레임마다 (4~5)
```

#### 7.4.1 FAnimUpdateRateParameters 구조 (`Engine/Classes/Engine/EngineTypes.h` L2388)

| 멤버 | 타입 | 의미 |
|------|------|------|
| `OptimizeMode` | `EOptimizeMode` | **TrailMode** (지난 프레임 보간) / **LookAheadMode** (미리 계산) |
| `ShiftBucket` | `EUpdateRateShiftBucket` | 인스턴스 분산용 버킷 (4종) — 동일 메시 N개의 평가가 같은 프레임에 몰리지 않도록 |
| `bInterpolateSkippedFrames:1` | uint8 | 스킵 프레임 보간 |
| `bShouldUseLodMap:1` | uint8 | LOD/Frameskip 맵 사용 (vs DistanceFactor) |
| `bShouldUseMinLod:1` | uint8 | MinLODModel 사용 (vs PredictedLOD) |
| `bSkipUpdate:1` | uint8 | (이번 프레임) 업데이트 스킵 |
| `bSkipEvaluation:1` | uint8 | (이번 프레임) 평가 스킵 |
| `UpdateRate` | int32 | **N프레임마다 1번 Tick** (1=매 프레임) |
| `EvaluationRate` | int32 | **N프레임마다 1번 풀 평가** (UpdateRate 의 배수) |
| `BaseNonRenderedUpdateRate` | int32 | 안 보일 때 기본 UpdateRate |
| `MaxEvalRateForInterpolation` | int32 | 보간 가능한 최대 EvalRate (이상이면 보간 X) |
| `BaseVisibleDistanceFactorThesholds` | TArray\<float\> | 보일 때 DistanceFactor → 스킵 매핑 |
| `LODToFrameSkipMap` | TMap\<int32, int32\> | LOD → 스킵 프레임 |

#### 7.4.2 EOptimizeMode 차이

| 모드 | 동작 | 사용처 |
|------|------|--------|
| `TrailMode` (기본) | 지난 평가 결과를 다음 N프레임 동안 보간 | 단순 / 시각만 |
| `LookAheadMode` | 미리 다음 평가 시점 예측 → 보간 | RootMotion·Procedural Anim |

#### 7.4.3 UpdateRate vs EvaluationRate

```
프레임:    1   2   3   4   5   6   7   8   9   10
Update:    ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓     UpdateRate=1
Update:    ✓   .   ✓   .   ✓   .   ✓   .   ✓   .     UpdateRate=2 (격프레임)
Update:    ✓   .   .   ✓   .   .   ✓   .   .   ✓     UpdateRate=3
Eval:      ✓   .   .   .   .   ✓   .   .   .   .     EvalRate=5 (UpdateRate=2 의 2.5배)
                                                       → 풀 평가는 5프레임마다, 그 외는 보간
```

**Update** = 본 변환 산출 (TickPose / RefreshBoneTransforms) — **가벼움**.
**Evaluation** = AnimGraph 풀 평가 (StateMachine·BlendSpace·BlueprintGraph) — **무거움**.

비싼 AnimGraph 가 있는 NPC는 EvaluationRate를 UpdateRate의 2~3배로 늘려 **AnimGraph 평가 비용 1/N**.

#### 7.4.4 ShiftBucket — 인스턴스 분산

같은 종류 NPC 100명을 모두 매 5번째 프레임에 동시 평가하면 5프레임마다 스파이크 발생. UE는 자동으로 4개 ShiftBucket(0~3)에 분산:

```
프레임:    1   2   3   4   5   6   7   8
Bucket0:   ✓   .   .   .   .   ✓   .   .   (5프레임마다 frame 1, 6, 11...)
Bucket1:   .   ✓   .   .   .   .   ✓   .   (5프레임마다 frame 2, 7, 12...)
Bucket2:   .   .   ✓   .   .   .   .   ✓   (5프레임마다 frame 3, 8, 13...)
Bucket3:   .   .   .   ✓   .   .   .   .   (5프레임마다 frame 4, 9, 14...)
```

→ 각 프레임당 1/4만 평가 — **스파이크 4분산**. 자동 — 사용자가 직접 ShiftBucket 설정 거의 안 함.

#### 7.4.5 URO 관련 API

| API | 의미 |
|-----|------|
| `bool ShouldUseUpdateRateOptimizations() const` | 사용 여부 |
| `virtual void AnimUpdateRateTick(...)` | URO 파라미터 갱신 (자동) |
| `void OnAnimUpdateRateChanged()` | 변경 콜백 (override 가능) |
| `static FAnimUpdateRateParameters* GetOrCreateAnimUpdateRateParameters(USkinnedMeshComponent*)` | 파라미터 가져오기 |

### 7.5 추가 LOD/AnimGraph 비용 항목

#### A. PostProcess Animation Blueprint

USkeletalMesh 의 PostProcessAnimBlueprint — 메시 레벨 후처리 (IK·Physics·Cloth). **항상 풀 평가** — URO 영향 X. 무거운 PostProcess AnimBP는:

- LOD 별로 비활성화 (LODSettings 에서)
- 가까이만 PostProcess 활성 (조건부)

#### B. LOD 별 본 수 / AnimGraph 비활성화

`SkeletalMesh > LODSettings > LODSetting per LOD`:
- `BoneSizeRatioThreshold` — LOD별 작은 본 제거
- `bDisableSubLODBoneRemoval`
- `bAllowMeshDeformer` — GPU 디포머 (5.x)
- `bAllowCPUAccess` — CPU 본 접근 필요 시만

**AnimGraph LOD Threshold**: AnimGraph 노드별 `LOD Threshold` 설정 — 특정 LOD 이상에서 노드 비활성. PostProcess BP·복잡한 IK 노드에 적용.

#### C. bRecentlyRendered (Visibility 캐시)

`UPrimitiveComponent::bRecentlyRendered` (5초 buffer) — `WasRecentlyRendered(Tolerance)` 가 검사. URO 의 `BaseNonRenderedUpdateRate` 도 이걸 기반.

### 7.6 AnimationBudgetAllocator (Plugin — 자동 Budget 분배)

`Engine/Plugins/Runtime/AnimationBudgetAllocator/` 플러그인 — **글로벌 시간 예산 (예: 1ms / 프레임)** 안에서 자동으로 인스턴스별 UpdateRate 조정. `USkeletalMeshComponentBudgeted` 자손을 사용 + Budget Allocator 매니저가 매 프레임 평가.

#### 7.6.1 핵심 클래스

| 클래스/인터페이스 | 위치 | 의미 |
|------------------|------|------|
| `IAnimationBudgetAllocator` | `Public/IAnimationBudgetAllocator.h` L14 | 매니저 인터페이스 |
| `IAnimationBudgetAllocatorModule` | `Public/IAnimationBudgetAllocatorModule.h` | `IAnimationBudgetAllocator& GetAllocator(UWorld*)` |
| `USkeletalMeshComponentBudgeted` | `Publ