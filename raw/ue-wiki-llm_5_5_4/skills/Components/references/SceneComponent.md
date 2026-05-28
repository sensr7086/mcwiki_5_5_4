---
name: components-scenecomponent
description: USceneComponent 트랜스폼 보유 - SetWorldLocation + SetRelativeLocation + AttachToComponent + GetForwardVector + 6대 정책.
---

# Components · SceneComponent sub-skill

> **모듈**: Engine (Tier 1)
> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/SceneComponent.h`
> **다루는 범위**: `USceneComponent` — 트랜스폼·계층·부착·이동·Mobility·Sockets — `UActorComponent` 자손 + 모든 비주얼/콜리전 컴포넌트의 베이스.

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

UE 3D 월드에서 **위치/회전/스케일을 보유하는 컴포넌트**의 베이스. 부모-자식 계층(Attach)을 형성하며, 부모 트랜스폼이 자식에게 전파됨.

**`UActorComponent` vs `USceneComponent`**:

| | `UActorComponent` | `USceneComponent` |
|--|------------------|-------------------|
| 트랜스폼 | ❌ | ✅ |
| Attach 가능 | ❌ | ✅ (다른 SceneComponent에) |
| Sockets | ❌ | ✅ |
| Mobility | ❌ | ✅ (Static/Stationary/Movable) |
| 사용처 | 스탯/인벤토리/로직 | 메시/콜리전/카메라/라이트 |

**부착 시스템**: 액터의 `RootComponent` 가 1개 USceneComponent — 모든 다른 SceneComponent는 직간접적으로 RootComponent 자손. 액터 위치 = RootComponent 위치.

---

## 2. 핵심 헤더

| 클래스 | 위치 | 의미 |
|--------|------|------|
| `USceneComponent` | `SceneComponent.h` (계승: UActorComponent) | 베이스 |
| `EAttachmentRule` | (Engine/SceneComponent.h) | KeepRelative / KeepWorld / SnapToTarget |
| `FAttachmentTransformRules` | | Attach 시 트랜스폼 처리 |
| `FDetachmentTransformRules` | | Detach 시 |
| `EComponentMobility` | | Static / Stationary / Movable |

---

## 3. Attach / Detach 시스템

### 3.1 Attachment Rules

```cpp
// 5개 멤버
struct FAttachmentTransformRules
{
    EAttachmentRule LocationRule;     // KeepRelative / KeepWorld / SnapToTarget
    EAttachmentRule RotationRule;
    EAttachmentRule ScaleRule;
    bool bWeldSimulatedBodies = false; // 물리 바디 융합

    // 빌트인
    static const FAttachmentTransformRules KeepRelativeTransform;     // 모두 KeepRelative
    static const FAttachmentTransformRules KeepWorldTransform;         // 모두 KeepWorld
    static const FAttachmentTransformRules SnapToTargetIncludingScale; // 부모와 동일 + 스케일
    static const FAttachmentTransformRules SnapToTargetNotIncludingScale; // 부모 + 자기 스케일
};
```

### 3.2 Attach API

| API | 의미 |
|-----|------|
| `bool AttachToComponent(USceneComponent* Parent, const FAttachmentTransformRules& Rules, FName SocketName=NAME_None)` | 부착 (Socket 옵션) |
| `bool AttachToActor(AActor* Parent, const FAttachmentTransformRules& Rules, FName SocketName=NAME_None)` | 액터의 Root 에 부착 |
| `void DetachFromComponent(const FDetachmentTransformRules& Rules)` | 분리 |
| `USceneComponent* GetAttachParent() const` | 부착 부모 |
| `FName GetAttachSocketName() const` | 부착 소켓 |
| `TArray<USceneComponent*> GetAttachChildren() const` | 직속 자식들 |
| `void GetChildrenComponents(bool bIncludeAllDescendants, TArray<USceneComponent*>&)` | 모든 자손 |
| `int32 GetNumChildrenComponents() const` | |

### 3.3 사용 패턴

```cpp
// Spawn된 액터에 무기 부착
AWeapon* Weapon = GetWorld()->SpawnActor<AWeapon>(...);
Weapon->AttachToActor(MyCharacter,
    FAttachmentTransformRules::SnapToTargetNotIncludingScale,
    FName("WeaponSocket"));    // 캐릭터 메시의 소켓

// 분리
Weapon->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
```

---

## 4. Transform — Relative / World / Local

### 4.1 좌표계 3종

| 좌표계 | 의미 |
|--------|------|
| **Relative** | 부모 기준 (부모 트랜스폼 적용 전) |
| **World** | 월드 절대 (모든 부모 트랜스폼 누적) |
| **Local** | 자기 좌표계 (Forward/Right/Up 기준) |

### 4.2 Setter API (SceneComponent.h L383+)

#### Relative (부모 기준)

| API | 의미 |
|-----|------|
| `void SetRelativeLocation(FVector NewLocation, bool bSweep=false, FHitResult* OutSweepHitResult=nullptr, ETeleportType=None)` | |
| `void SetRelativeRotation(FRotator NewRotation, bool bSweep=false, ...)` | |
| `void SetRelativeScale3D(FVector NewScale3D)` | |
| `void SetRelativeTransform(const FTransform& NewTransform, bool bSweep=false, ...)` | |
| `void AddRelativeLocation(FVector DeltaLocation, bool bSweep=false, ...)` | 누적 |
| `void AddRelativeRotation(FRotator DeltaRotation, bool bSweep=false, ...)` | |

#### World (월드 절대)

| API | 의미 |
|-----|------|
| `void SetWorldLocation(FVector NewLocation, bool bSweep=false, ...)` | |
| `void SetWorldRotation(FRotator NewRotation, bool bSweep=false, ...)` | |
| `void SetWorldScale3D(FVector NewScale)` | |
| `void SetWorldTransform(const FTransform& NewTransform, bool bSweep=false, ...)` | |
| `void AddWorldOffset(FVector DeltaLocation, bool bSweep=false, ...)` | 월드 오프셋 누적 |
| `void AddWorldRotation(FRotator DeltaRotation, bool bSweep=false, ...)` | |

#### Local (로컬 축 기준)

| API | 의미 |
|-----|------|
| `void AddLocalOffset(FVector DeltaLocation, bool bSweep=false, ...)` | 자기 Forward/Right/Up 기준 |
| `void AddLocalRotation(FRotator DeltaRotation, bool bSweep=false, ...)` | |
| `void AddLocalTransform(const FTransform& DeltaTransform, bool bSweep=false, ...)` | |

### 4.3 Getter API

| API | 의미 |
|-----|------|
| `FVector GetRelativeLocation() const` / `Rotation` / `Scale3D` | 부모 기준 |
| `FVector GetComponentLocation() const` / `Rotation` / `Scale` | 월드 |
| `FTransform GetComponentTransform() const` | 월드 변환 |
| `FTransform GetRelativeTransform() const` | 부모 기준 변환 |
| `FVector GetForwardVector() const` / `RightVector` / `UpVector` | 월드 축 |

### 4.4 bSweep / Teleport (이동 정책)

`bSweep=true` — 이동 경로를 콜리전 검사. 막히면 이동 안 함 + `FHitResult` 반환:

```cpp
FHitResult Hit;
SetWorldLocation(NewPos, /*bSweep=*/true, &Hit, ETeleportType::None);
if (Hit.bBlockingHit)
{
    UE_LOG(LogTemp, Log, TEXT("Blocked by %s"), *Hit.GetActor()->GetName());
}
```

`ETeleportType`:
- `None` — 일반 이동 (물리 영향)
- `TeleportPhysics` — 텔레포트 (물리 끊김)
- `ResetPhysics` — 물리 리셋

---

## 5. Mobility (정적 / 정지 / 가동)

`EComponentMobility` (UPROPERTY):

| 모빌리티 | 의미 | 용도 |
|----------|------|------|
| `Static` | 절대 이동 X — 라이트 베이크 가능 | 건물·바닥·정적 props |
| `Stationary` | 게임 중 위치 고정, 라이트 동적 변화 | 라이트 (베이크된 그림자 + 동적 광) |
| `Movable` | 자유 이동 — 라이트 베이크 불가 | 캐릭터·움직이는 props |

```cpp
SetMobility(EComponentMobility::Movable);    // 게임 중 이동 가능하게
```

> **주의**: `Static` / `Stationary` 컴포넌트는 게임 중 `SetWorldLocation` 호출 시 경고 + 동작 안 함. 이동 필요하면 `Movable` 의무.

---

## 6. Sockets (특정 부착점)

### 6.1 Socket 시스템

`USceneComponent` 베이스는 사용자 정의 소켓 — `USkeletalMeshComponent` / `UStaticMeshComponent` 등 자손은 메시 본/소켓 통합.

### 6.2 API

| API | 의미 |
|-----|------|
| `virtual bool DoesSocketExist(FName SocketName) const` | 소켓 존재 |
| `virtual FTransform GetSocketTransform(FName SocketName, ERelativeTransformSpace TransformSpace=RTS_World) const` | 소켓 변환 |
| `virtual FVector GetSocketLocation(FName SocketName) const` | 위치 |
| `virtual FQuat GetSocketQuaternion(FName SocketName) const` | 회전 |
| `virtual FRotator GetSocketRotation(FName SocketName) const` | |
| `virtual TArray<FName> GetAllSocketNames() const` | 모든 소켓 |

### 6.3 사용

```cpp
// 캐릭터 메시의 "Hand_R" 소켓에 무기 부착
USkeletalMeshComponent* Mesh = MyCharacter->GetMesh();
if (Mesh->DoesSocketExist(FName("Hand_R")))
{
    Weapon->AttachToComponent(Mesh,
        FAttachmentTransformRules::SnapToTargetIncludingScale,
        FName("Hand_R"));
}
```

---

## 7. UpdatedChildren (자식 동기)

`USceneComponent` 가 이동/회전 시 자식 트랜스폼을 자동 갱신. 사용자 정의 콜백:

```cpp
virtual void UpdateChildTransforms(EUpdateTransformFlags=Default, ETeleportType=None)
{
    // 자식 트랜스폼 동기화
}

// 사용자 정의 SceneComponent에서 자식 변경 옵서버
virtual void OnUpdateTransform(EUpdateTransformFlags, ETeleportType=None)
{
    Super::OnUpdateTransform(...);     // ← FIRST
    // 트랜스폼 변경 후 처리
}
```

`OnChildAttached(USceneComponent*)` / `OnChildDetached(USceneComponent*)` — 자식 추가/제거 콜백.

---

## 8. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `OnRegister()` (UActorComponent 베이스) | **FIRST** | 등록 — 트랜스폼 초기화 |
| `OnUnregister()` | **LAST** | |
| `OnUpdateTransform(EUpdateTransformFlags, ETeleportType)` | **FIRST** | 트랜스폼 변경 후 |
| `OnChildAttached(USceneComponent*)` | **FIRST** | 자식 추가 |
| `OnChildDetached(USceneComponent*)` | **FIRST** | 자식 제거 |
| `OnAttachmentChanged()` | **FIRST** | 부착 부모 변경 |
| `IsWorldGeometry() const` | (override 시 자체) | World 지오메트리? |
| `GetComponentVelocity() const` | (override 시 자체) | 속도 (물리 통합) |

---

## 9. 함정

| 함정 | 회피 |
|------|------|
| `Static`/`Stationary` 컴포넌트 게임 중 이동 시도 | `SetMobility(Movable)` 의무 |
| `bSweep=true` 결과 무시 | `FHitResult` 검사 + 막힘 처리 |
| 부착 후 `KeepRelative` 인데 위치 안 맞음 | `SnapToTargetIncludingScale` 또는 `KeepWorld` 사용 |
| 부착 시 SocketName 누락 | 부모 트랜스폼 기준 — 소켓 사용 시 명시 |
| `SetWorldLocation` 매 프레임 호출 + 물리 시뮬 활성 | `ETeleportType::TeleportPhysics` 사용 |
| 액터 RootComponent 가 nullptr | 생성자에서 `RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"))` |
| 이동 후 자식 위치 갱신 안 됨 | UE는 자동 갱신 — 경고: `bAbsoluteLocation`/`bAbsoluteRotation` 가 true 면 부모 무시 |
| `OnUpdateTransform` Super 누락 | 자식 트랜스폼 미갱신 |
| Mobility 와 라이트 베이크 충돌 | Static 컴포넌트만 베이크 가능 |

---

## 10. 에디터 전용 🛠

| 항목 | 가드 | 의미 |
|------|------|------|
| 디테일 패널 변환 변경 | `WITH_EDITOR` (PostEditChangeProperty) | |
| 디자이너 트리 편집 | `WITH_EDITORONLY_DATA` | |
| `bVisualizeComponent` 🛠 | (UPROPERTY) | 디자이너에서 시각화 |

---

## 11. 관련 sub-skill

- [`Components/ActorComponent`](../ActorComponent/SKILL.md) — 베이스
- [`Components/PrimitiveComponent`](../PrimitiveComponent/SKILL.md) — 자손 (콜리전·렌더 추가)
- [`Components/MeshComponents`](../MeshComponents/SKILL.md) — 자손 (메시 + 소켓 시스템)
- [`Components/MovementComponents`](../MovementComponents/SKILL.md) — UpdatedComponent 패턴 (이동 처리)
- [`CoreUObject/Network`](../../CoreUObject/references/Network.md) — 트랜스폼 복제
- 교차: [`04_OverrideIndex.md`](../../../references/04_OverrideIndex.md) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (OnUpdateTransform 콜백 스코프)
