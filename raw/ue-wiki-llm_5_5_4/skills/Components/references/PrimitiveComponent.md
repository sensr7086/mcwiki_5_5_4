---
name: components-primitivecomponent
description: UPrimitiveComponent 렌더 + 콜리전 - SetVisibility + SetCollisionEnabled + Overlap 이벤트 + Custom Depth + 6대 정책.
---

# Components · PrimitiveComponent sub-skill

> **모듈**: Engine (Tier 1)
> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/PrimitiveComponent.h`
> **다루는 범위**: `UPrimitiveComponent` — **콜리전 + 렌더 + 물리** 통합 베이스. 모든 메시/콜라이더/시각 헬퍼의 부모.

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

---

## 1. 개요

`USceneComponent` 자손 + **렌더 표시 / 콜리전 / 물리** 추가. 메시·콜라이더·라이트(LocalLight 외)·데칼·캡처 등 **3D에서 보이거나 콜라이딩 하는 모든 컴포넌트의 베이스**.

핵심 책임:
- **렌더 (RenderProxy)** — `FPrimitiveSceneProxy` 게임 스레드 → 렌더 스레드 통신
- **콜리전** — Channel / Profile / Response / Query / Physics
- **이벤트** — Overlap (Begin/End), Hit
- **Visibility** — Hidden / 게임 빌드 / 에디터
- **HLOD** — Hierarchical Level of Detail
- **Material** — Dynamic Material Instance 관리

---

## 2. 핵심 헤더

| 클래스/시스템 | 위치 | 의미 |
|-------------|------|------|
| `UPrimitiveComponent` | `PrimitiveComponent.h` | 베이스 |
| `FBodyInstance` | `Engine/PhysicsEngine/BodyInstance.h` | 물리 바디 |
| `UBodySetup` | `Engine/PhysicsEngine/BodySetup.h` | 물리 설정 데이터 |
| `FCollisionResponseContainer` | `Engine/CollisionProfile.h` | 채널별 응답 |
| `FBodyInstance::CollisionProfileName` | (CollisionProfile.h) | 프로파일 이름 |
| `FHitResult` / `FOverlapResult` | `Engine/EngineTypes.h` | 이벤트 결과 |
| `FPrimitiveSceneProxy` | `Renderer/PrimitiveSceneProxy.h` | 렌더 스레드 프록시 |

---

## 3. 콜리전 시스템

### 3.1 콜리전 3축

콜리전은 **3가지 정보**의 조합:

1. **Object Type** — 이 컴포넌트가 무엇인지 (`ECollisionChannel`)
   - `ECC_WorldStatic` / `ECC_WorldDynamic` / `ECC_Pawn` / `ECC_Visibility` / `ECC_Camera` / `ECC_PhysicsBody` / `ECC_Vehicle` / `ECC_Destructible` + `ECC_GameTraceChannel1~18` (사용자 정의)

2. **Collision Response** — 다른 채널에 대한 응답 (`ECollisionResponse`)
   - `ECR_Ignore` / `ECR_Overlap` / `ECR_Block`

3. **Collision Enabled** — 활성/비활성 (`ECollisionEnabled`)
   - `NoCollision` / `QueryOnly` / `PhysicsOnly` / `QueryAndPhysics` / `ProbeOnly` / `QueryAndProbe`

### 3.2 Collision Profile (편의 시스템)

자주 쓰는 조합을 **프로파일**로 묶음 (`Project Settings > Collision`):

| 프로파일 | 의미 |
|----------|------|
| `NoCollision` | 콜리전 없음 |
| `BlockAll` | 모두 Block |
| `OverlapAll` | 모두 Overlap |
| `BlockAllDynamic` | 동적 객체만 Block |
| `OverlapAllDynamic` | 동적만 Overlap |
| `IgnoreOnlyPawn` | Pawn만 Ignore |
| `Pawn` / `Spectator` / `CharacterMesh` / `PhysicsActor` / `Destructible` / `Vehicle` / `UI` | 표준 |
| `Trigger` | 트리거 (Query Only + Overlap) |
| `Custom...` | 사용자 정의 |

### 3.3 콜리전 API

#### 채널 / 프로파일

| API | 의미 |
|-----|------|
| `void SetCollisionEnabled(ECollisionEnabled::Type)` | 활성화 토글 |
| `ECollisionEnabled::Type GetCollisionEnabled() const` | |
| `void SetCollisionObjectType(ECollisionChannel)` | 자기 채널 |
| `void SetCollisionResponseToChannel(ECollisionChannel, ECollisionResponse)` | 응답 |
| `void SetCollisionResponseToAllChannels(ECollisionResponse)` | 일괄 |
| `void SetCollisionProfileName(FName, bool bUpdateOverlaps=true)` | 프로파일 |
| `FName GetCollisionProfileName() const` | |

#### Generate Events

```cpp
SetGenerateOverlapEvents(true);     // OnComponentBeginOverlap / OnComponentEndOverlap 활성
SetNotifyRigidBodyCollision(true);  // OnComponentHit 활성
```

### 3.4 Overlap / Hit 이벤트

#### 델리게이트 (UPROPERTY BlueprintAssignable)

```cpp
UPROPERTY(BlueprintAssignable, Category="Collision")
FComponentBeginOverlapSignature OnComponentBeginOverlap;
// (UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)

UPROPERTY(BlueprintAssignable, Category="Collision")
FComponentEndOverlapSignature OnComponentEndOverlap;
// (UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)

UPROPERTY(BlueprintAssignable, Category="Collision")
FComponentHitSignature OnComponentHit;
// (UPrimitiveComponent* HitComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit)
```

#### 사용 패턴

```cpp
void AMyTrigger::BeginPlay()
{
    Super::BeginPlay();
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyTrigger_BeginPlay);

    if (TriggerVolume)
    {
        TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &AMyTrigger::HandleOverlapBegin);
        TriggerVolume->OnComponentEndOverlap.AddDynamic(this, &AMyTrigger::HandleOverlapEnd);
    }
}

UFUNCTION()
void AMyTrigger::HandleOverlapBegin(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyTrigger_HandleOverlapBegin);    // ← 의무
    if (APlayerCharacter* Player = Cast<APlayerCharacter>(OtherActor))
    {
        // ...
    }
}
```

> **🚨 OnRep_\* / 바인딩된 UFUNCTION 모두 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) 스코프 의무**.

### 3.5 트레이스 (능동 검사)

```cpp
// World 레벨 트레이스 (UWorld 사용)
FHitResult Hit;
FCollisionQueryParams Params;
Params.AddIgnoredActor(this);
GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params);

// 컴포넌트 단위 (직접 검사)
TArray<FHitResult> Hits;
MyComponent->ComponentSweepMulti(Hits, Start, End, FQuat::Identity, Params);
```

### 3.6 Move Ignore

| API | 라인 | 의미 |
|-----|------|------|
| `void IgnoreActorWhenMoving(AActor* Actor, bool bShouldIgnore)` | L1012 | 액터 무시 |
| `TArray<AActor*> CopyArrayOfMoveIgnoreActors()` | L1018 | 복사 |
| `void ClearMoveIgnoreActors()` | L1029 | 초기화 |
| `void IgnoreComponentWhenMoving(UPrimitiveComponent* Component, bool)` | L1047 | 컴포넌트 무시 |
| `void ClearMoveIgnoreComponents()` | L1064 | 초기화 (인라인) |
| `virtual bool ShouldComponentIgnoreHitResult(FHitResult const& TestHit, EMoveComponentFlags MoveFlags)` | L1073 | override 가능 |

---

## 4. 물리 시스템

### 4.1 BodyInstance + BodySetup

`UPrimitiveComponent::BodyInstance` 가 물리 바디 1개. `UBodySetup` (UPROPERTY 또는 메시에 포함) 이 콜리전 형태·물리 머티리얼 정의.

### 4.2 물리 API

| API | 의미 |
|-----|------|
| `void SetSimulatePhysics(bool bSimulate)` | 물리 시뮬 토글 |
| `bool IsSimulatingPhysics() const` | |
| `void SetEnableGravity(bool)` | 중력 |
| `void SetMassOverrideInKg(FName BoneName=NAME_None, float MassInKg=1.f, bool bOverrideMass=true)` | 질량 |
| `float GetMass() const` | |
| `void SetLinearDamping(float)` / `SetAngularDamping(float)` | 감쇠 |
| `void SetPhysicsLinearVelocity(FVector NewVel, bool bAddToCurrent=false, FName BoneName=NAME_None)` | 선속도 |
| `void SetPhysicsAngularVelocityInDegrees(FVector, bool=false, FName=NAME_None)` | 각속도 |
| `void AddForce(FVector Force, FName BoneName=NAME_None, bool bAccelChange=false)` | 힘 |
| `void AddImpulse(FVector Impulse, FName BoneName=NAME_None, bool bVelChange=false)` | 충격량 |
| `void AddTorqueInRadians(FVector, FName=NAME_None, bool bAccelChange=false)` | 토크 |
| `void AddRadialForce(FVector Origin, float Radius, float Strength, ERadialImpulseFalloff Falloff, bool bAccelChange=false)` | 반경 힘 |
| `void AddRadialImpulse(FVector Origin, float Radius, float Strength, ERadialImpulseFalloff, bool bVelChange=false)` | 반경 충격 |

### 4.3 콘스트레인트 / 락

| API | 의미 |
|-----|------|
| `void SetPhysicsLinearVelocity(...)` | (이동 시 물리 동기) |
| `void SetConstraintMode(EDOFMode::Type)` | 자유도 (None/SixDOF/YZPlane/XZPlane/XYPlane/CustomPlane/Default) |
| `void SetPhysicsLinearLock(bool LockX, LockY, LockZ)` | 직선 락 |
| `void SetPhysicsAngularLock(bool LockX, LockY, LockZ)` | 각 락 |

자세한 물리 콘스트레인트는 [`Components/PhysicsComponents`](../PhysicsComponents/SKILL.md) (`UPhysicsConstraintComponent`).

---

## 5. Visibility / 렌더

### 5.1 Visibility API

| API | 의미 |
|-----|------|
| `void SetVisibility(bool bNewVisibility, bool bPropagateToChildren=false)` | 가시성 |
| `void SetHiddenInGame(bool bNewHidden, bool bPropagateToChildren=false)` | 게임 빌드 숨김 |
| `bool IsVisible() const` | 효과적 가시성 |
| `bool WasRecentlyRendered(float Tolerance=0.2f) const` | 최근 렌더? (L935) |

### 5.2 Material 동적 변경

| API | 라인 | 의미 |
|-----|------|------|
| `UMaterialInterface* GetMaterial(int32 ElementIndex) const` | L1432 | 가져오기 |
| `void SetMaterial(int32 ElementIndex, UMaterialInterface*)` | L1466 | 설정 |
| `int32 GetNumMaterials() const` | L2186 | 슬롯 수 |
| `UMaterialInstanceDynamic* CreateAndSetMaterialInstanceDynamic(int32 ElementIndex)` | L1481 | MID 생성 + 설정 (Deprecated — `CreateDynamicMaterialInstance` 사용) |
| `UMaterialInstanceDynamic* CreateDynamicMaterialInstance(int32 ElementIndex, UMaterialInterface*=nullptr, FName OptionalName=NAME_None)` | L1495 | MID 생성만 (권장) |
| `void SetMaterialByName(FName MaterialSlotName, UMaterialInterface*)` | L1474 | 슬롯명으로 |

> ⚠ 5.5.4 기준: `GetCreateMaterialInstanceDynamic` / `TArray<UMaterialInterface*> GetMaterials() const` 는 `UPrimitiveComponent` 헤더에 존재하지 않음 (이후 버전 추가).

### 5.3 RenderProxy (게임 → 렌더 스레드)

```cpp
virtual FPrimitiveSceneProxy* CreateSceneProxy()
{
    return new FMyCustomSceneProxy(this);
}
```

게임 스레드 데이터가 렌더 스레드로 안전하게 전달되도록 `FPrimitiveSceneProxy` 자손 작성. **§11 자세한 패턴 참조**.

---

## 6. HLOD (Hierarchical Level of Detail)

| API | 라인 | 의미 |
|-----|------|------|
| `bool IsExcludedFromHLODLevel(EHLODLevelExclusion HLODLevel) const` | L716 | 특정 레벨 제외? |
| `void SetExcludedFromHLODLevel(EHLODLevelExclusion HLODLevel, bool bExcluded)` | L720 | 설정 |

---

## 7. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `OnRegister()` | **FIRST** | 등록 — 콜리전·렌더 셋업 |
| `OnUnregister()` | **LAST** | |
| `OnComponentCreated()` | **FIRST** | 생성 직후 |
| `BeginPlay()` | **FIRST** | 게임 시작 |
| `EndPlay(EEndPlayReason)` | **LAST** | |
| `Tick(...)` | **FIRST + 스코프** | 매 프레임 |
| `CreateSceneProxy()` | (override 시 자체) | 렌더 프록시 — 사용자 정의 메시 |
| `UpdateBounds()` | **FIRST** | AABB 업데이트 |
| `OnComponentCollisionSettingsChanged()` | **FIRST** | 콜리전 설정 변경 |
| `OnAttachmentChanged()` | **FIRST** | (USceneComponent 베이스) 부착 변경 |
| `ShouldComponentIgnoreHitResult(FHitResult, EMoveComponentFlags)` | (override 시 자체) | Move ignore 정책 |

---

## 8. 함정

| 함정 | 회피 |
|------|------|
| `OnComponentBeginOverlap` 안 호출됨 — `SetGenerateOverlapEvents(true)` 누락 | 의무 |
| `OnComponentHit` 안 호출됨 — `bSimulatePhysics=false` + `bNotifyRigidBodyCollision=false` | 둘 중 하나 필요 |
| 콜리전 응답 — Block 대 Overlap 의 차이 모르고 사용 | Block: 막힘 + Hit / Overlap: 통과 + 알림 |
| Profile 변경 후 Channel 변경 — 무효 | Profile은 일관성 — 둘 중 하나만 |
| `bSimulatePhysics=true` 인데 콜리전 `QueryOnly` | `QueryAndPhysics` 또는 `PhysicsOnly` 의무 |
| `SetWorldLocation` 시 물리 끊김 | `ETeleportType::TeleportPhysics` 사용 |
| MID 매 프레임 `CreateDynamicMaterialInstance` 호출 | 1회 캐싱 + Setter 사용 |
| 대량 인스턴스 — Material 슬롯 N개 모두 MID로 변경 | InstancedStaticMesh + InstanceCustomData 사용 |
| Trace 결과 `Hit.GetActor()` nullptr 가능 | 검사 의무 |
| `WasRecentlyRendered` 결과 — 가시성 토글 직후 false | Tolerance 조정 또는 직접 `IsVisible` |
| 🚨 Overlap/Hit 콜백 람다·UFunction 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) 의무 — 빈도 폭증 가능 |
| `ComponentSweepMulti` 매 프레임 호출 | 캐싱 + 거리 기반 throttle |

---

## 9. 에디터 전용 🛠

| 항목 | 가드 | 의미 |
|------|------|------|
| `bVisualizeComponent` 🛠 | (UPROPERTY) | 디자이너 시각화 |
| `bUseAsOccluder` 디테일 패널 | `WITH_EDITORONLY_DATA` | |
| `PostEditChangeProperty` 🛠 | `WITH_EDITOR` | 디테일 변경 즉시 반영 |

---

## 10. 관련 sub-skill

- [`Components/SceneComponent`](../SceneComponent/SKILL.md) — 베이스 (트랜스폼)
- [`Components/MeshComponents`](../MeshComponents/SKILL.md) — 자손 (StaticMesh / SkeletalMesh)
- [`Components/ShapeComponents`](../ShapeComponents/SKILL.md) — 자손 (Box/Sphere/Capsule)
- [`Components/PhysicsComponents`](../PhysicsComponents/SKILL.md) — Physics Constraint / Handle / Spring
- [`Components/MovementComponents`](../MovementComponents/SKILL.md) — UpdatedComponent (UPrimitiveComponent 와 연계)
- [`CoreUObject/Network`](../../CoreUObject/references/Network.md) — 위치/회전 복제
- 향후: `Renderer` / `RHI` (Render 카테고리, Tier 2) — `FPrimitiveSceneProxy` 자세한 작성
- 교차: [`04_OverrideIndex.md`](../../../references/04_OverrideIndex.md) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (Overlap/Hit/Tick 콜백 스코프)

---

## 11. FPrimitiveScene