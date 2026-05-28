---
name: components-physicscomponents
description: UPhysicsConstraintComponent + UPhysicsHandleComponent + UPhysicsThrusterComponent + URadialForceComponent + USpringArmComponent + 6대 정책.
---

# Components / PhysicsComponents — 물리 (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/PhysicsEngine/{PhysicsConstraintComponent,PhysicsHandleComponent,PhysicsSpringComponent,PhysicsThrusterComponent,PhysicalAnimationComponent,RadialForceComponent,ClusterUnionComponent,ClusterUnionReplicatedProxyComponent}.h`
> **베이스**: `UActorComponent` (Handle/PhysAnim) 또는 `USceneComponent` (Constraint/Spring/Thruster/RadialForce) 또는 `UPrimitiveComponent` (ClusterUnion)
> **요지**: **Chaos 5.x 통합 후 모든 물리는 `FBodyInstance` + `FPhysicsActorHandle` 경유**. 본 sub-skill 은 **물리 보조 컴포넌트 8종** — Constraint(조인트), Handle(잡기), Spring(스프링), Thruster(추력), Radial Force(폭발), Physical Animation(물리 애니), Cluster Union(파괴 클러스터).

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

## 1. 컴포넌트 8종 한 줄 요약

| # | 컴포넌트 | 베이스 | 역할 |
|---|---------|--------|------|
| 1 | `UPhysicsConstraintComponent` | `USceneComponent` | 두 RigidBody 간 조인트 (6DOF + Drive + Limit) |
| 2 | `UPhysicsHandleComponent` | `UActorComponent` | 물리 객체 잡기/드래그 (Spring 기반) |
| 3 | `UPhysicsSpringComponent` | `USceneComponent` | Raycast 스프링 (간이 차량 서스펜션) |
| 4 | `UPhysicsThrusterComponent` | `USceneComponent` | -X 축 일정 추력 (로켓·제트) |
| 5 | `URadialForceComponent` | `USceneComponent` | 반경 안 모든 RigidBody 에 Force/Impulse (폭발) |
| 6 | `UPhysicalAnimationComponent` | `UActorComponent` | SkeletalMesh 본별 물리 시뮬 + 애니 블렌드 (DriveTarget) |
| 7 | `UClusterUnionComponent` | `UPrimitiveComponent` | Chaos 파괴 시스템 — 여러 GeometryCollection 클러스터 |
| 8 | `UClusterUnionReplicatedProxyComponent` | `UActorComponent` | ClusterUnion 네트워크 복제 보조 |

> **ClassGroup = `Physics`** 통일. **Mobility 보통 `Movable`** 강제 (Static 객체는 물리 시뮬 못 함).

---

## 2. UPhysicsConstraintComponent — 조인트 (가장 자주 사용)

[`PhysicsConstraintComponent.h:23-200`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicsConstraintComponent.h):

### 2.1 핵심 필드

```cpp
// 두 RigidBody 지정
UPROPERTY(EditInstanceOnly, Category=Constraint)
TObjectPtr<AActor> ConstraintActor1;
UPROPERTY(EditAnywhere, Category=Constraint)
FConstrainComponentPropName ComponentName1;        // Actor1 안 컴포넌트 이름

UPROPERTY(EditInstanceOnly, Category=Constraint)
TObjectPtr<AActor> ConstraintActor2;
UPROPERTY(EditAnywhere, Category=Constraint)
FConstrainComponentPropName ComponentName2;

// 직접 코드 설정
TWeakObjectPtr<UPrimitiveComponent> OverrideComponent1;
TWeakObjectPtr<UPrimitiveComponent> OverrideComponent2;

// 모든 조인트 옵션
UPROPERTY(EditAnywhere, Category=ConstraintComponent, meta=(ShowOnlyInnerProperties))
FConstraintInstance ConstraintInstance;            // 6DOF + Drive + Limit + Break Force

// 깨짐 알림
UPROPERTY(BlueprintAssignable)
FConstraintBrokenSignature OnConstraintBroken;
UPROPERTY(BlueprintAssignable)
FPlasticDeformationEventSignature OnPlasticDeformation;
```

### 2.2 FConstraintInstance — 옵션 5종

| 그룹 | 필드 | 의미 |
|------|------|------|
| Linear Limit | `LinearLimit.XMotion`/`YMotion`/`ZMotion` | Free / Locked / Limited |
| Angular Limit | `AngularLimit.Swing1Motion`/`Swing2Motion`/`TwistMotion` | Free / Locked / Limited |
| Drive | `LinearDrive.XDrive` 등 | 위치/속도 드라이브 (스프링) |
| Disable Collision | `bDisableCollision` | 두 Body 간 콜리전 무시 |
| Break | `LinearBreakThreshold` / `AngularBreakThreshold` | 깨짐 임계 (0 = 안 깨짐) |

### 2.3 표준 패턴 — 코드로 두 컴포넌트 연결

```cpp
// AHinge::AHinge
ConstraintComp = CreateDefaultSubobject<UPhysicsConstraintComponent>(TEXT("Constraint"));
RootComponent = ConstraintComp;

ConstraintComp->ConstraintInstance.SetLinearXLimit(LCM_Locked, 0.f);
ConstraintComp->ConstraintInstance.SetLinearYLimit(LCM_Locked, 0.f);
ConstraintComp->ConstraintInstance.SetLinearZLimit(LCM_Locked, 0.f);
ConstraintComp->ConstraintInstance.SetAngularSwing1Limit(ACM_Locked, 0.f);
ConstraintComp->ConstraintInstance.SetAngularSwing2Limit(ACM_Locked, 0.f);
ConstraintComp->ConstraintInstance.SetAngularTwistLimit(ACM_Limited, 90.f);   // ±90° 비틂만 허용

// 런타임에 두 컴포넌트 연결
ConstraintComp->SetConstrainedComponents(MeshA, NAME_None, MeshB, NAME_None);
```

### 2.4 깨짐 + 변형

```cpp
// 깨짐 임계 — 1000 N 넘으면 깨짐
ConstraintComp->ConstraintInstance.LinearBreakThreshold = 1000.f;

// 깨짐 콜백 (블루프린트 또는 C++)
ConstraintComp->OnConstraintBroken.AddDynamic(this, &AHinge::OnHingeBroken);
```

> **5.4+ Plasticity** — `bLinearPlasticity` / `bAngularPlasticity` 로 영구 변형 (휘어진 채 유지). `OnPlasticDeformation` 콜백.

### 2.5 ReInit 필요 시점

```cpp
// 컴포넌트 등록/언등록 시 자동 호출
// 수동: 두 RigidBody 의 PhysicsState 변경 시
ConstraintComp->ReInitConstraintAndApplyPhysicsState(ChangedComponent, EComponentPhysicsStateChange::Created);
```

---

## 3. UPhysicsHandleComponent — 잡기 (Drag-and-Drop)

[`PhysicsHandleComponent.h:16-150`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicsHandleComponent.h):

### 3.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `GrabbedComponent` | 현재 잡고 있는 컴포넌트 |
| `GrabbedBoneName` | 스켈레탈 메시면 본 이름 |
| `bSoftLinearConstraint` | 위치 부드러운 (Spring) |
| `bSoftAngularConstraint` | 회전 부드러운 |
| `LinearStiffness` / `LinearDamping` | 위치 스프링 강성/댐핑 |
| `AngularStiffness` / `AngularDamping` | 회전 스프링 강성/댐핑 |
| `bInterpolateTarget` | TargetTransform 보간 |
| `InterpolationSpeed` | 보간 속도 |

### 3.2 표준 사용

```cpp
// FPS 그랩 — Pawn 에 부착
PhysicsHandle = CreateDefaultSubobject<UPhysicsHandleComponent>(TEXT("PhysicsHandle"));

// 잡기
void AGrabPawn::TryGrab()
{
    FHitResult Hit;
    GetWorld()->LineTraceSingleByChannel(Hit, GetActorLocation(),
        GetActorLocation() + GetActorForwardVector() * 500.f, ECC_PhysicsBody);
    if (Hit.bBlockingHit && Hit.Component->IsSimulatingPhysics())
    {
        PhysicsHandle->GrabComponentAtLocationWithRotation(
            Hit.Component.Get(), Hit.BoneName, Hit.Location, GetActorRotation());
    }
}

// 매 Tick 타겟 위치 갱신
void AGrabPawn::Tick(float Dt)
{
    Super::Tick(Dt);
    if (PhysicsHandle->GrabbedComponent)
    {
        const FVector TargetLoc = GetActorLocation() + GetActorForwardVector() * 200.f;
        PhysicsHandle->SetTargetLocationAndRotation(TargetLoc, GetActorRotation());
    }
}

// 놓기
void AGrabPawn::Release()
{
    PhysicsHandle->ReleaseComponent();
}
```

> **bSoftLinearConstraint = true** 가 표준 — 부드러운 잡기. False = 즉시 따라옴 (단단한 잡기, 비현실적).

---

## 4. UPhysicsSpringComponent — Raycast 스프링 (차량 서스펜션)

[`PhysicsSpringComponent.h:19-90`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicsSpringComponent.h):

### 4.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `SpringStiffness` | 강성 |
| `SpringDamping` | 댐핑 (떨림 흡수) |
| `SpringLengthAtRest` | 휴식 길이 |
| `SpringRadius` | Raycast 구체 반경 |
| `SpringChannel` | Raycast Trace Channel |
| `bIgnoreSelf` | Owner Actor 의 다른 컴포넌트 무시 |
| `SpringCompression` | 현재 압축 (transient — 읽기 전용) |

### 4.2 동작

> **+X 축 방향**으로 Raycast — Hit 거리에 따라 스프링 힘 계산.
> 차량 4륜 서스펜션은 4개 SpringComponent 부착 (각 휠 위치).

> **5.x 에서는 ChaosVehicles 또는 PhysicsControl 플러그인** 우선. PhysicsSpringComponent 는 빠른 프로토타이핑 / 간이 차량 / 비행체 호버용.

---

## 5. UPhysicsThrusterComponent — 추력 (로켓 / 제트)

[`PhysicsThrusterComponent.h:16-30`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicsThrusterComponent.h):

```cpp
UCLASS(hidecategories=(Object, Mobility, LOD), ClassGroup=Physics, MinimalAPI)
class UPhysicsThrusterComponent : public USceneComponent
{
    UPROPERTY(BlueprintReadWrite, interp, Category=Physics)
    float ThrustStrength;     // -X 방향 N (Newton)

    virtual void TickComponent(float DeltaTime, enum ELevelTick TickType,
                               FActorComponentTickFunction *ThisTickFunction) override;
};
```

> **-X 방향**으로 ThrustStrength 만큼 힘 적용 (X 축이 분사 방향 — 즉 추력은 -X). Owner Actor 의 RootComponent (또는 Attach 부모) 의 `bSimulatingPhysics = true` 필요.

```cpp
// 로켓
Thruster = CreateDefaultSubobject<UPhysicsThrusterComponent>(TEXT("Thruster"));
Thruster->SetupAttachment(GetMesh());
Thruster->SetRelativeLocation(FVector(50, 0, 0));    // Mesh 뒤쪽
Thruster->SetRelativeRotation(FRotator(0, 180, 0));  // X 축 = 분사 방향
Thruster->ThrustStrength = 5000.f;                    // N
Thruster->SetActive(false);                           // Activate 시작 시
```

---

## 6. URadialForceComponent — 폭발 / 충격파

[`RadialForceComponent.h:16-100`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/PhysicsEngine/RadialForceComponent.h):

### 6.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `Radius` | 영향 반경 |
| `Falloff` | `RIF_Constant` / `RIF_Linear` |
| `ImpulseStrength` | 단발 임펄스 강도 (FireImpulse) |
| `bImpulseVelChange` | 질량 무시 (속도 변화 직접) |
| `ForceStrength` | 매 Tick 적용 힘 (Active 시) |
| `bIgnoreOwningActor` | Owner 의 컴포넌트 무시 |
| `DestructibleDamage` | DestructibleMesh 데미지 |
| `ObjectTypesToAffect` | 영향 줄 ObjectType (`EObjectTypeQuery`) |

### 6.2 두 가지 모드

**(1) 단발 임펄스 — 폭발**:
```cpp
// 폭탄 폭발 시
RadialForce->FireImpulse();   // ImpulseStrength + Radius + Falloff 한 번에 적용
```

**(2) 지속 힘 — Tick 매 프레임 (`SetActive(true)` 동안)**:
```cpp
// 지속 충격파
RadialForce->SetActive(true);    // ForceStrength * Tick 적용 시작
// ...
RadialForce->SetActive(false);
```

> **bIgnoreOwningActor = true** 권장 (Owner 가 자기 자신에 영향 안 받게).

---

## 7. UPhysicalAnimationComponent — Ragdoll + Animation 블렌드

[`PhysicalAnimationComponent.h:17-150`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicalAnimationComponent.h):

### 7.1 FPhysicalAnimationData — 본별 모터 설정

```cpp
USTRUCT(BlueprintType)
struct FPhysicalAnimationData
{
    FName BodyName;
    uint8 bIsLocalSimulation : 1;        // World vs Local 시뮬
    float OrientationStrength;            // 회전 보정 강도
    float AngularVelocityStrength;        // 각속도 보정
    float PositionStrength;               // 위치 보정 (Non-local 시뮬 시)
    float VelocityStrength;
    float MaxLinearForce;
    float MaxAngularForce;
};
```

### 7.2 표준 패턴 — Hit Reaction (피격 시 일부 본만 물리)

```cpp
// 1. SkeletalMesh 와 연결
PhysAnim = CreateDefaultSubobject<UPhysicalAnimationComponent>(TEXT("PhysAnim"));

void AMyChar::BeginPlay()
{
    Super::BeginPlay();
    PhysAnim->SetSkeletalMeshComponent(GetMesh());
}

// 2. 본별 또는 프로필별 적용
void AMyChar::OnHit(FName BoneName)
{
    // 해당 본 + 자손 본 일정 강도로 물리 시뮬
    FPhysicalAnimationData Data;
    Data.bIsLocalSimulation = true;
    Data.OrientationStrength = 1000.f;
    Data.AngularVelocityStrength = 100.f;
    Data.MaxAngularForce = 5000.f;
    PhysAnim->ApplyPhysicalAnimationSettingsBelow(BoneName, Data, /*bIncludeSelf=*/true);

    // 또는 PhysicsAsset 의 Physical Animation Profile 적용
    PhysAnim->ApplyPhysicalAnimationProfileBelow(BoneName, TEXT("HitProfile"),
        /*bIncludeSelf=*/true, /*bClearNotFound=*/false);

    // SkeletalMesh 의 본 시뮬 활성
    GetMesh()->SetAllBodiesBelowSimulatePhysics(BoneName, true, /*bIncludeSelf=*/true);
}

// 3. 강도 블렌드 (hit reaction 종료)
void AMyChar::FadeHitReaction()
{
    PhysAnim->SetStrengthMultiplyer(0.f);   // 0~1 — 물리 시뮬 강도 페이드
}
```

> **`Experimental` 마크** — UE 5.x 에서 안정. `UnsafeDuringActorConstruction` 메타 — 생성자 안 호출 금지 (BeginPlay 또는 이후).

---

## 8. UClusterUnionComponent — Chaos 파괴 통합 (5.x)

[`ClusterUnionComponent.h:36-200`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/PhysicsEngine/ClusterUnionComponent.h):

> 5.x Chaos Destruction — 여러 `UGeometryCollectionComponent` 를 하나의 `ClusterUnion` 으로 묶음. 자동차 차체 + 부품 등.
> **`ULevelSetElem`**, **`USkinnedTriangleMeshElem`** 와 함께 5.x Chaos 자체 신규 시스템.

### 8.1 동작

```cpp
ClusterUnion = CreateDefaultSubobject<UClusterUnionComponent>(TEXT("ClusterUnion"));
RootComponent = ClusterUnion;

void AMyVehicle::SetupCluster()
{
    ClusterUnion->AddComponentToCluster(BodyMesh.Get(), {});
    ClusterUnion->AddComponentToCluster(WheelMesh1.Get(), {});
    // ... 각 부품 등록
}

void AMyVehicle::OnPartBroken(UPrimitiveComponent* Part)
{
    ClusterUnion->RemoveComponentFromCluster(Part);
    // Part 가 독립 RigidBody 로 분리됨
}
```

> **`UClusterUnionReplicatedProxyComponent`** — 멀티플레이어에서 ClusterUnion 의 자식 본 데이터를 복제하는 보조. 자동 생성됨.

---

## 9. 물리 비용 — Constraint / Handle 매트릭스

| 컴포넌트 | 비용 (대략) | 비고 |
|---------|------------|------|
| Constraint | **고정** (Solver 한 반복마다 6DOF 검사) | 100개 = 100배 — Limit/Drive 활성 시 추가 |
| Handle (잡고 있을 때만) | 작음 (Spring 1개) | Soft Constraint 일 때 |
| Spring (Raycast 매 Tick) | 작음 | Raycast 비용 — Channel 좁힘 |
| Thruster (매 Tick AddForce) | 매우 작음 | RigidBody 1개 |
| RadialForce (FireImpulse) | 매우 작음 (1회) | Active 시 매 Tick |
| RadialForce (Active) | 중간 — 매 프레임 Overlap 검사 | bIgnoreOwningActor 필수 |
| PhysicalAnimation | **비쌈** (본별 모터) | Body 수 × Solver Iterations |
| ClusterUnion | 부품 수에 비례 | 100 부품 OK, 1000 부품 위험 |

---

## 10. 표준 셋업 결정 트리

```
질문: 무엇을 하고 싶은가?
├── 두 객체 연결 (문/체인/Joint)
│   └── UPhysicsConstraintComponent (가장 자주)
│       ├── 문 → Twist 만 Limited
│       ├── 체인 → 전부 Limited (Linear + Angular)
│       └── 단단한 연결 → Linear/Angular 모두 Locked
├── 물건 잡고 옮기기 (FPS)
│   └── UPhysicsHandleComponent
├── 폭발 / 충격파
│   └── URadialForceComponent (FireImpulse)
├── 지속 추력 (로켓/제트/호버)
│   └── UPhysicsThrusterComponent
├── 차량 서스펜션 (간이)
│   └── UPhysicsSpringComponent (4개)
├── 캐릭터 부분 Ragdoll (피격)
│   └── UPhysicalAnimationComponent
└── 파괴 가능 차량/구조물
    └── UClusterUnionComponent (+ GeometryCollection)
```

---

## 11. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | Constraint 의 두 RigidBody Mobility 가 Static | Movable (또는 Stationary) 강제 |
| 2 | Constraint 의 Linear/Angular 모두 Free → 0 강성 | Locked 또는 Limited 명시 |
| 3 | Hand `GrabComponent` 가 `IsSimulatingPhysics() = false` 컴포넌트 | 잡기 전 검사 — Static/Kinematic 잡기 못 함 |
| 4 | Thruster 의 `ThrustStrength` 단위가 cm/s² (가속도) 인 줄 알기 | **N (Newton)** — Body 질량 따라 가속 다름 |
| 5 | RadialForce 매 Tick `FireImpulse` | `SetActive(true)` 사용 (지속 힘) — FireImpulse 는 1회 |
| 6 | RadialForce `bIgnoreOwningActor = false` (자기 자신 영향) | true 표준 |
| 7 | `ApplyPhysicalAnimationProfileBelow` 생성자 안 호출 | `UnsafeDuringActorConstruction` — BeginPlay 이후 |
| 8 | PhysAnim 적용 후 `SetSimulatePhysics` 안 호출 → 모터 효과 안 남 | `SetAllBodiesBelowSimulatePhysics(BoneName, true)` 명시 |
| 9 | ClusterUnion + 부품 매 Tick 추가/제거 | 물리 Solver Restart 비용 — 가능한 BeginPlay 1회 |
| 10 | Constraint 의 `OnConstraintBroken` 콜백 안에서 Constraint Destroy | Frame 끝에 destroy (`SetLifeSpan(0.001f)`) |
| 11 | 🚨 PhysAnim Tick / RadialForce Tick 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |
| 12 | 🚨 RadialForce 가 `TActorIterator` 로 영향 객체 검색 (X) | Overlap 사용 (자동) ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |

---

## 12. 체크리스트 (Physics 컴포넌트 작성)

- [ ] 어떤 컴포넌트 (Constraint/Handle/Spring/Thruster/RadialForce/PhysAnim/ClusterUnion)?
- [ ] 두 RigidBody (Constraint) 가 Movable 인가?
- [ ] Constraint Linear/Angular 6 모션 명시 (Free/Locked/Limited)
- [ ] Constraint Break Threshold 명시 (0 = 안 깨짐)
- [ ] Handle: bSoft*Constraint = true 표준 (부드러운 잡기)
- [ ] Thruster: RootComponent 가 SimulatingPhysics = true
- [ ] RadialForce: bIgnoreOwningActor = true 표준
- [ ] RadialForce: FireImpulse (1회) vs SetActive (지속) 선택
- [ ] PhysAnim: BeginPlay 이후 ApplyPhysicalAnimationSettings (생성자 금지)
- [ ] PhysAnim: SetAllBodiesBelowSimulatePhysics 명시 호출
- [ ] PhysAnim: StrengthMultiplyer 페이드 (0~1)
- [ ] ClusterUnion: 부품 추가/제거는 BeginPlay 또는 이벤트 시점
- [ ] Tick / 콜백 / FireImpulse 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] 🚨 매 Tick TActorIterator 로 영향 객체 검색 안 함

---

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. 8개 PhysicsComponents — UPhysicsConstraintComponent (FConstraintInstance 6 모션 + Drive + Break + Plasticity) + UPhysicsHandleComponent (Soft Constraint 잡기) + UPhysicsSpringComponent (Raycast 스프링) + UPhysicsThrusterComponent (-X 추력) + URadialForceComponent (FireImpulse vs SetActive) + UPhysicalAnimationComponent (FPhysicalAnimationData + Profile + StrengthMultiplyer + UnsafeDuringActorConstruction 주의) + UClusterUnionComponent (5.x Chaos Destruction) + UClusterUnionReplicatedProxyComponent. 비용 매트릭스 + 결정 트리 + 함정 12종 + 체크리스트. |
