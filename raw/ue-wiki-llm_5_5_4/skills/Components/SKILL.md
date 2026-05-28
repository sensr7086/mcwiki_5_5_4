---
name: components-main
description: Tier 1 Components 메인 — ActorComponent + SceneComponent + PrimitiveComponent (베이스 3) + MeshComponents + ShapeComponents + LightComponents + PhysicsComponents + MovementComponents + CameraComponent + AudioComponent + ParticleComponents + RenderingComponents + AtmosphereComponents + SystemComponents + SpecialComponents 15개 sub-skill. 6대 정책 의무 + 어셋 로드 정책 + 어셋 최적화 정책 cross-link.
---

# Components Module — 메인 SKILL.md

> **모듈**: `Engine/Source/Runtime/Engine/` 내 컴포넌트 묶음 (Tier 1)
> **카테고리**: `[Components]` — 게임 시스템의 근간
> **사이즈**: `Engine/Classes/Components/` 70 + `GameFramework/` 7 + `Camera/` 2 + `Particles/` 1 + `PhysicsEngine/` 6+ + `Animation/` 1 + `Atmosphere/` 1 + `Debug/` 1 + `Interfaces/` 1 = **약 90개 컴포넌트** (5.5.4)

---

## 🚨 모든 Components sub-skill 의무 정책 (본문 시작부 의무 블록)

> **모든 Components 작성 시 다음 횡단 정책 모두 적용 의무**. 자세한 코드·결정 트리·함정은 각 인덱스 참조.

| 정책 | 적용 |
|------|------|
| 🚨 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) | **6대 의무** — Mobility / NewObject·DuplicateObject / GC 방어 / GetOwner 캐싱 / PrimaryComponentTick / CDO. **모든 Components sub-skill 본문 시작부 동일 6대 정책 블록 의무 삽입**. |
| 🎯 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) | **어셋 로드 정책** — Mesh / Material / Texture / SoundCue / NiagaraSystem / Animation 어셋 멤버는 **Soft vs Hard 결정 + Constructor 안 어셋 로드 금지 + BeginPlay 동기 LoadObject 금지 + UAssetManager Primary Asset / Bundle + FStreamableManager 비동기 + Handle Pin/Release**. SpawnActor 히칭 4단 원인 이해 + Cooked Build 검증 의무. |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../references/12_AssetOptimizationPolicy.md) | **어셋 최적화 5대 영역** — (1) SkeletalMesh Bone LOD (USkeletalMeshLODSettings + BonesToRemove/Prioritize) + (2) StaticMesh LOD (ScreenSize 표준 + 5.x Nanite) + (3) Actor Merging (HISM / Mesh Merge / HLOD / WorldPartition) + (4) Audio Culling (Attenuation + Concurrency + Significance) + (5) Niagara Scalability (EffectType + 품질 레벨 매트릭스). **다수 NPC 환경 = §6 통합 매트릭스**. |
| 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) | Tick / TimerManager / 람다 / OnRep_\* / 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무. |
| 🚨 [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) | Tick / 콜백 안 `TActorIterator` / `TObjectIterator` 사용 금지 — 등록 패턴 우선. |

---

## 1. 개요

UE 의 **모든 게임 로직과 시각/물리/오디오/입력 동작**이 컴포넌트 위에서 실행. AActor 자체는 거의 비어있고, 실제 동작은 부착된 컴포넌트가 담당. 컴포넌트 베이스 사슬:

```
UObject
└── UActorComponent (로직 전용 — Tick / Replication / 라이프사이클)
    └── USceneComponent (트랜스폼 보유 — Attach / Mobility / Sockets)
        └── UPrimitiveComponent (콜리전 + 렌더 + 물리)
            ├── UMeshComponent → UStaticMeshComponent / USkeletalMeshComponent / ...
            ├── UShapeComponent → UBoxComponent / USphereComponent / UCapsuleComponent / UBrushComponent
            ├── UDecalComponent · UTextRenderComponent · UBillboardComponent · UMaterialBillboardComponent · UArrowComponent · ULineBatchComponent · UDrawSphereComponent · UDrawFrustumComponent
            ├── UReflectionCaptureComponent / USceneCaptureComponent / UPlanarReflectionComponent / URuntimeVirtualTextureComponent
            ├── UPostProcessComponent · UStereoLayerComponent
            └── ...
        ├── ULightComponentBase → ULocalLightComponent → UPointLight / USpotLight / URectLight / ...
        │                       ↘ UDirectionalLightComponent · USkyLightComponent · USkyAtmosphereComponent
        ├── UCameraComponent · UCameraShakeSourceComponent
        ├── USpringArmComponent · UAudioComponent · UForceFeedbackComponent · UParticleSystemComponent
        ├── USplineComponent · UTimelineComponent · UVectorFieldComponent
        └── ...
    ├── UMovementComponent → UNavMovementComponent → UPawnMovementComponent → UCharacterMovementComponent / UProjectileMovementComponent / URotatingMovementComponent / UInterpToMovementComponent
    ├── UInputComponent · UChildActorComponent · UApplicationLifecycleComponent · UPawnNoiseEmitterComponent · UPlatformEventsComponent · UWorldPartitionStreamingSourceComponent
    └── 물리: UPhysicsConstraintComponent · UPhysicsHandleComponent · UPhysicsSpringComponent · UPhysicalAnimationComponent · UClusterUnionComponent
```

---

## 2. 의존·빌드 (Engine.Build.cs 요약)

`Engine` 모듈은 UE의 거의 모든 게임 시스템 — 의존 모듈 100+. 컴포넌트 사용 시 게임 모듈에서 다음 의존:

```csharp
PublicDependencyModuleNames.AddRange(new string[] {
    "Core", "CoreUObject", "Engine"     // ← 컴포넌트 사용 시 핵심
});
```

추가 (시나리오별):
- 물리 통합 시: `PhysicsCore`
- 애니 통합 시: `AnimationCore`, `AnimGraphRuntime`
- 네트워킹: `NetCore`
- GAS: `GameplayAbilities`, `GameplayTags`, `GameplayTasks` (별도 플러그인)

---

## 3. Sub-skill 인덱스 (15개 분할)

각 sub-skill 은 *개요 → 핵심 헤더/클래스 → 자주 쓰는 API → virtual → 예제 → 함정 → 관련 sub-skill* 일관 구조.

### 3.1 베이스 사슬 3개 (가장 자주)

| # | Sub-skill | 다루는 영역 | 주요 헤더/심볼 |
|---|-----------|-------------|----------------|
| 1 | [`ActorComponent/`](./ActorComponent/SKILL.md) | **모든 컴포넌트의 베이스** — `UActorComponent` + 라이프사이클 (Register/InitializeComponent/BeginPlay/Tick/EndPlay/UninitializeComponent) + ETickingGroup + Replication + Activate/Deactivate | `Components/ActorComponent.h` |
| 2 | [`SceneComponent/`](./SceneComponent/SKILL.md) | **트랜스폼 + 계층** — `USceneComponent` + Attach/Detach + Transform (Relative/World/Local) + Mobility (Static/Stationary/Movable) + Sockets + UpdatedChildren | `Components/SceneComponent.h` |
| 3 | [`PrimitiveComponent/`](./PrimitiveComponent/SKILL.md) | **콜리전 + 렌더 + 물리** — `UPrimitiveComponent` + Collision (Channel/Profile/Response) + Overlap/Hit 이벤트 + Visibility + RenderProxy + HLOD + Material 동적 변경 | `Components/PrimitiveComponent.h` + `Components/MeshComponent.h` |

### 3.2 시각 / 메시 (5개)

| # | Sub-skill | 다루는 영역 |
|---|-----------|-------------|
| 4 | [`MeshComponents/`](./MeshComponents/SKILL.md) | StaticMesh/SkeletalMesh/SkinnedMesh/InstancedStaticMesh/HierarchicalISM/SplineMesh/PoseableMesh/InstancedSkinnedMesh + Model |
| 5 | [`LightComponents/`](./LightComponents/SKILL.md) | LightComponentBase/LocalLight/Directional/Point/Spot/Rect/SkyLight/SkyAtmosphere/LightmassPortal/WindDirectionalSource (11개) |
| 6 | [`RenderingComponents/`](./RenderingComponents/SKILL.md) | Decal·TextRender·Billboard·MaterialBillboard·Arrow·DrawSphere·DrawFrustum·LineBatch (시각 헬퍼) + SceneCapture·PlanarReflection·ReflectionCapture·RuntimeVirtualTexture (캡처) + PostProcess·StereoLayer |
| 7 | [`AtmosphereComponents/`](./AtmosphereComponents/SKILL.md) | Atmosphere·SkyAtmosphere·ExponentialHeightFog·LocalFogVolume·HeterogeneousVolume·VolumetricCloud (대기/안개/볼륨) |
| 8 | [`ParticleComponents/`](./ParticleComponents/SKILL.md) | UParticleSystemComponent (Cascade — legacy) + UNiagaraComponent (별도 모듈, cross-reference) + VectorField |

### 3.3 콜리전 / 물리 (2개)

| # | Sub-skill | 다루는 영역 |
|---|-----------|-------------|
| 9 | [`ShapeComponents/`](./ShapeComponents/SKILL.md) | UShapeComponent (베이스) + UBoxComponent / USphereComponent / UCapsuleComponent / UBrushComponent (콜리전 / 트리거) |
| 10 | [`PhysicsComponents/`](./PhysicsComponents/SKILL.md) | UPhysicsConstraintComponent · UPhysicsHandleComponent · UPhysicsSpringComponent · UPhysicalAnimationComponent · UClusterUnionComponent (PhysicsEngine 폴더) |

### 3.4 게임플레이 / 시스템 (3개)

| # | Sub-skill | 다루는 영역 |
|---|-----------|-------------|
| 11 | [`MovementComponents/`](./MovementComponents/SKILL.md) | **이동 베이스** — UMovementComponent → UNavMovementComponent → UPawnMovementComponent → **UCharacterMovementComponent** (가장 큼·복제 핵심) / UProjectileMovementComponent / URotatingMovementComponent / UInterpToMovementComponent + USpringArmComponent (Camera) |
| 12 | [`CameraComponent/`](./CameraComponent/SKILL.md) | UCameraComponent · UCameraShakeSourceComponent (Camera 카테고리) + 카메라 매트릭스 / FOV / View Target 통합 |
| 13 | [`SystemComponents/`](./SystemComponents/SKILL.md) | UInputComponent · UChildActorComponent · UApplicationLifecycleComponent · UPawnNoiseEmitterComponent · UPlatformEventsComponent · UWorldPartitionStreamingSourceComponent · UBoundsCopyComponent · ULODSyncComponent |

### 3.5 오디오 / 특수 (2개)

| # | Sub-skill | 다루는 영역 |
|---|-----------|-------------|
| 14 | [`AudioComponent/`](./AudioComponent/SKILL.md) | UAudioComponent · UForceFeedbackComponent (햅틱) + AudioMixer cross-reference (별도 모듈) |
| 15 | [`SpecialComponents/`](./SpecialComponents/SKILL.md) | USplineComponent · UTimelineComponent · UStereoLayerComponent · UDebugDrawComponent · UPreviewAssetAttachComponent + ComponentInterfaces (인터페이스) |

---

## 4. 🚨 작성 / 사용 규칙

### 4.0 6대 공통 정책 ([`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md))

> **모든 Components sub-skill 의 본문 시작부에 동일 블록이 의무 삽입** — 이번 절은 그 6대 정책의 메인 인덱스 요약.

| # | 정책 | 핵심 규칙 |
|---|------|-----------|
| 1 | **Mobility** | 생성자에서 `Static`/`Stationary`/`Movable` 명시. 런타임 `SetMobility` 금지 (re-register + Lightmap 무효) |
| 2 | **NewObject + DuplicateObject** | Constructor=`CreateDefaultSubobject` / 런타임=`NewObject<T>(this)` / Deep copy=`DuplicateObject<T>(Source, Outer)` — Outer 유효성 검사 |
| 3 | **GC 방어** | UCLASS 안 UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>`. 비-UCLASS = `TStrongObjectPtr<T>` 또는 `FGCObject::AddReferencedObjects` |
| 4 | **GetOwner 캐싱** | `BeginPlay` 에서 `TWeakObjectPtr<AOwner>` 1회 캐싱. Tick / 콜백 안 매번 `Cast<>` 안 함 |
| 5 | **PrimaryComponentTick** | 기본 `bCanEverTick = false`. 필요 시 `TickInterval` (0.05~1s) 우선. 매 프레임 = 마지막 수단 + 첫 줄 프로파일링 스코프 |
| 6 | **CDO** | `GetMutableDefault<T>()->Set*()` 으로 CDO 변경 금지. `PostInitProperties` 안 `HasAnyFlags(RF_ClassDefaultObject)` 검사. `CreateDefaultSubobject` 는 Constructor 안만 |

자세한 코드 패턴·결정 트리·함정·체크리스트는 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) 참조.

### 4.1 베이스 선택

| 시나리오 | 베이스 |
|----------|--------|
| 트랜스폼 불필요 (스탯·인벤토리·게임 로직) | `UActorComponent` |
| 트랜스폼 필요 (위치·회전 — 부착) | `USceneComponent` |
| 콜리전·렌더 필요 (메시·라이트·콜라이더) | `UPrimitiveComponent` (또는 직속 자손) |
| 메시 표시 | `UMeshComponent` 자손 |
| 콜라이더만 (트리거·검출) | `UShapeComponent` 자손 |

### 4.2 라이프사이클 의무 ([`04_OverrideIndex.md §6.1`](../../references/04_OverrideIndex.md))

- `BeginPlay()` → **Super FIRST**
- `Tick(DeltaTime)` → **Super FIRST + 프로파일링 스코프 의무** ([`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md))
- `EndPlay(EEndPlayReason)` → **Super LAST**
- `OnRegister()` / `OnUnregister()` → Super FIRST (등록/해제)
- `InitializeComponent()` / `UninitializeComponent()` → Super FIRST/LAST

### 4.3 멀티플레이 / Replication

- `SetIsReplicatedByDefault(true)` 생성자에서 명시
- `UPROPERTY(Replicated)` 또는 `ReplicatedUsing=OnRep_*`
- `GetLifetimeReplicatedProps` override + `DOREPLIFETIME*` 매크로
- 권한 검사: `GetOwner()->HasAuthority()` 또는 `GetOwnerRole() == ROLE_Authority`
- RPC 는 Owning Actor 통해가 안전

### 4.4 