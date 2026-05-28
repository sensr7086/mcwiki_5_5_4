---
name: components-movementcomponents
description: UCharacterMovementComponent (5종 모드) + UFloatingPawnMovement + UProjectileMovementComponent + Replication + 6대 정책.
---

# Components / MovementComponents — 이동 베이스 (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/GameFramework/{MovementComponent,NavMovementComponent,PawnMovementComponent,CharacterMovementComponent,ProjectileMovementComponent,RotatingMovementComponent,SpringArmComponent}.h` + `Classes/Components/InterpToMovementComponent.h` + `Public/CharacterMovementComponentAsync.h`
> **베이스**: `UActorComponent` → `UMovementComponent` → `UNavMovementComponent` → `UPawnMovementComponent` → `UCharacterMovementComponent`
> **요지**: **`UMovementComponent` 는 `UpdatedComponent` (USceneComponent 또는 자손) 를 매 Tick 위치 업데이트** — Plane Constraint / Penetration Resolve / SlideAlongSurface / TwoWallAdjust 가 베이스. **`UCharacterMovementComponent`** 는 5종 MovementMode (Walking/Falling/Swimming/Flying/Custom + NavWalking) + 클라/서버 예측 + 보정 (Network Prediction) — 가장 큰 클래스. **Projectile/Rotating/InterpTo** 는 단순 자손. **`USpringArmComponent`** 는 `USceneComponent` 직속 (이동 베이스 아님 — 카메라 boom).

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

## 1. 상속 트리 (UCharacterMovement = 약 5,200줄)

```
UActorComponent
└── UMovementComponent  (abstract)        — UpdatedComponent 매 Tick 이동 + Plane Constraint
    └── UNavMovementComponent  (abstract) — Path Following 통합 (NavMovementProperties)
        └── UPawnMovementComponent (abstract) — Pawn 입력 누적 (AddInputVector / ConsumeInputVector)
            └── UCharacterMovementComponent — Walking/Falling/Swimming/Flying + 복제 + 예측 + 보정
                                              ├── PerformMovement (서버/오너)
                                              ├── SimulateMovement (시뮬레이션 프록시)
                                              ├── ServerMove* (RPC 패킷)
                                              └── ClientAdjustPosition* (보정 RPC)
    └── UProjectileMovementComponent      — 발사체 (Bounce/Homing/Sub-step)
    └── URotatingMovementComponent        — 회전 (RotationRate + Pivot)
    └── UInterpToMovementComponent        — 컨트롤 포인트 시퀀스 (OneShot/Loop/PingPong)

USceneComponent
└── USpringArmComponent                   — 카메라 boom (콜리전 회피 lag)
```

**MovementComponent.h L60-68** ([`MovementComponent.h:60-68`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/GameFramework/MovementComponent.h)) — 베이스 책임 4가지:
1. **Plane / Axis 제약** (`bConstrainToPlane` + `PlaneConstraintNormal`)
2. **Slide / Penetration 유틸** (`SlideAlongSurface` / `ComputeSlideVector` / `TwoWallAdjust` / `SafeMoveUpdatedComponent` / `ResolvePenetration`)
3. **자동 Tick 등록 + UpdatedComponent 자동 탐지** (`bAutoRegisterUpdatedComponent`)
4. **Owning Actor 의 Root 또는 명시 컴포넌트 이동** (`UpdatedComponent` / `UpdatedPrimitive`)

---

## 2. UMovementComponent 베이스 — 핵심 필드 + virtual

### 2.1 핵심 필드 (`MovementComponent.h:76-196`)

| 필드 | 타입 | 의미 |
|------|------|------|
| `UpdatedComponent` | `TObjectPtr<USceneComponent>` | 이동 대상 — null 이면 자동 탐지 (Owner Root) |
| `UpdatedPrimitive` | `TObjectPtr<UPrimitiveComponent>` | UpdatedComponent 의 Primitive 캐스트 (콜리전·물리용) |
| `Velocity` | `FVector` | 현재 속도 |
| `MoveComponentFlags` | `EMoveComponentFlags` | `MoveComponent` 호출 플래그 |
| `bUpdateOnlyIfRendered` | `uint8:1` | UpdatedComponent 가 최근 렌더 안 됐으면 Tick 스킵 |
| `bAutoUpdateTickRegistration` | `uint8:1` | UpdatedComponent 변경 시 Tick 자동 on/off |
| `bTickBeforeOwner` | `uint8:1` | 등록 시 Owner 보다 먼저 Tick 의존성 추가 |
| `bAutoRegisterUpdatedComponent` | `uint8:1` | 시작 시 Owner Root 자동 할당 |
| `bConstrainToPlane` | `uint8:1` | 평면 제약 활성화 |
| `PlaneConstraintNormal` / `PlaneConstraintOrigin` | `FVector` | 평면 정의 |
| `bComponentShouldUpdatePhysicsVolume` | `uint8:1` | UpdatedComponent 의 PhysicsVolume 자동 업데이트 |

### 2.2 베이스 virtual (`MovementComponent.h:199-410`)

| virtual | 역할 | Super 호출 |
|---------|------|-----------|
| `TickComponent` | 매 프레임 (자식이 실제 이동 구현) | **반드시 Super FIRST** |
| `InitializeComponent` | UpdatedComponent 자동 탐지 | Super FIRST |
| `OnRegister` | Plane Constraint 정규화 + Tick 의존성 | Super FIRST |
| `Deactivate` | 정지 + UnregisterTickFunctions | Super FIRST/LAST 무관 |
| `Serialize` | 베이스 상태 직렬화 | Super FIRST |
| `PostLoad` | Plane Normal 재정규화 | Super FIRST |
| `PostEditChangeProperty` 🛠 | Plane 설정 변경 즉시 반영 | Super FIRST |
| `GetMaxSpeed` | (자식 override) 현재 모드 최대 속도 | — |
| `GetGravityZ` | PhysicsVolume 의 Gravity 또는 World | — |
| `StopMovementImmediately` | Velocity = 0 | — |
| `ShouldSkipUpdate` | `bUpdateOnlyIfRendered` + Mobility 검사 | — |
| `MoveUpdatedComponentImpl` | 실제 Move (Plane Constraint 반영) | — |
| `SafeMoveUpdatedComponent` | 침투 발생 시 ResolvePenetration 후 재시도 | — |
| `ResolvePenetrationImpl` | 침투 해소 (MTD + InflationDistance) | — |
| `ComputeSlideVector` | Slide 방향 계산 | — |
| `SlideAlongSurface` | Slide 이동 + TwoWallAdjust | — |
| `TwoWallAdjust` | 두 벽 사이 끼임 처리 | — |
| `HandleImpact` | Blocking 충격 콜백 (자식 override) | — |

### 2.3 `MoveUpdatedComponent` vs `SafeMoveUpdatedComponent`

```cpp
// 단순 이동 — 침투 발생 시 그대로 멈춤
bool bMoved = MoveUpdatedComponent(Delta, NewRotation, /*bSweep=*/true, &Hit);

// 침투 시 ResolvePenetration 후 재시도 — 캐릭터/프로젝타일 표준
FHitResult Hit;
bool bSucceeded = SafeMoveUpdatedComponent(Delta, NewRotation, /*bSweep=*/true, Hit);
if (Hit.Time < 1.f && Hit.bBlockingHit)
{
    SlideAlongSurface(Delta, 1.f - Hit.Time, Hit.Normal, Hit, /*bHandleImpact=*/true);
}
```

> **`SafeMoveUpdatedComponent` 가 표준** — `MoveUpdatedComponent` 직접 호출은 Plane Constraint 만 필요한 단순 케이스로 한정.

---

## 3. UNavMovementComponent — 네비게이션 통합

`NavMovementComponent.h:26` — `UNavMovementComponent : public UMovementComponent, public INavMovementInterface`.

### 3.1 핵심 필드 (5.5 부터 `FNavMovementProperties` 통합)

```cpp
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = NavMovement)
FNavAgentProperties NavAgentProps;        // Agent 반경/높이/Step/Slope

UPROPERTY()
FMovementProperties MovementState;        // 런타임 상태

UPROPERTY(EditAnywhere, Category = NavMovement)
FNavMovementProperties NavMovementProperties;  // Path Following 동작 (5.5 통합)
```

### 3.2 deprecated 5.5

[`NavMovementComponent.h:32-53`]:
- `FixedPathBrakingDistance` → `NavMovementProperties.FixedPathBrakingDistance`
- `bUpdateNavAgentWithOwnersCollision` → `NavMovementProperties.bUpdateNavAgentWithOwnersCollision`
- `bUseAccelerationForPaths` → `NavMovementProperties.bUseAccelerationForPaths`
- `bUseFixedBrakingDistanceForPaths` → `NavMovementProperties.bUseFixedBrakingDistanceForPaths`
- `bStopMovementAbortPaths` → `NavMovementProperties.bStopMovementAbortPaths`

> **5.5+** 신규 코드는 `NavMovementProperties.*` 직접 사용.

### 3.3 표준 override

| virtual | 역할 |
|---------|------|
| `RequestDirectMove` | 즉시 이동 명령 (NavMesh 무시) |
| `RequestPathMove` | 경로 따라 이동 |
| `CanStartPathFollowing` / `CanStopPathFollowing` | PathFollowing 시작/종료 가능? |
| `GetMaxSpeedForNavMovement` | Path 따라갈 때 최대 속도 |
| `GetPathFollowingBrakingDistance` | 정지 거리 |
| `StopActiveMovement` | 현재 이동 중단 |
| `SetPathFollowingAgent` | PathFollowingComponent 연결 |

---

## 4. UPawnMovementComponent — Pawn 입력

`PawnMovementComponent.h:42` — Pawn 만 등록 가능 (`SetUpdatedComponent` 에서 Pawn 검사).

### 4.1 입력 누적 패턴

```cpp
// (1) 외부 — APawn::AddMovementInput() 가 이걸 호출
PawnMovement->AddInputVector(WorldDir);

// (2) Tick 안에서 — PerformMovement 시작에서 ConsumeInputVector
const FVector Input = ConsumeInputVector();
if (!Input.IsZero() && !IsMoveInputIgnored())
{
    Acceleration = ComputeAccel(Input);
}

// (3) 보고 — 마지막 입력 (애니메이션 등 외부 시스템)
const FVector Last = GetLastInputVector();
const FVector Pending = GetPendingInputVector();
```

> `ConsumeInputVector` 는 **소비** 동시에 `LastInputVector` 저장. **두 번 부르면 0 반환** — Tick 안 한 번만.

---

## 5. UCharacterMovementComponent — 5종 모드 + 복제 핵심

> **가장 큰 클래스 (~5,200줄)** — §5.1~§5.4 핵심 + §5.5~§5.15 깊이는 [`references/CharacterMovementDeep.md`](./references/CharacterMovementDeep.md) 분리.

### 5.1 EMovementMode (`EngineTypes.h:1006-1034`)

```cpp
UENUM(BlueprintType)
enum EMovementMode : int
{
    MOVE_None,        // 이동 비활성
    MOVE_Walking,     // 표면 보행 (마찰 + Step Up)
    MOVE_NavWalking,  // NavMesh 단순 보행 (스윕 옵션)
    MOVE_Falling,     // 중력 낙하 (점프/낙하)
    MOVE_Swimming,    // PhysicsVolume Water 안 (부력)
    MOVE_Flying,      // 중력 무시
    MOVE_Custom,      // 사용자 정의 (CustomMovementMode 으로 sub-mode)
    MOVE_MAX
};
```

[`CharacterMovementComponent.h:228-237`]:
```cpp
UPROPERTY(BlueprintReadOnly)
TEnumAsByte<enum EMovementMode> MovementMode;

UPROPERTY(BlueprintReadOnly)
uint8 CustomMovementMode;        // MOVE_Custom 일 때 sub-mode (0-7 권장 — RepBits 압축)
```

> **MovementMode 변경**: `SetMovementMode(MOVE_Walking)` — 자동으로 5종 `Phys*` 함수로 라우팅.

### 5.2 5종 Phys* 함수 (`CharacterMovementComponent.h:1956-1968`)

| 함수 | 역할 | 호출 빈도 |
|------|------|-----------|
| `PhysWalking(deltaTime, Iterations)` | 보행 (Step Up + Floor 추적) | MOVE_Walking |
| `PhysFalling(deltaTime, Iterations)` | 낙하 (AirControl + Air Movement) | MOVE_Falling |
| `PhysFlying(deltaTime, Iterations)` | 비행 (Fluid Friction) | MOVE_Flying |
| `PhysSwimming(deltaTime, Iterations)` | 수영 (Buoyancy + Surface Test) | MOVE_Swimming |
| `PhysCustom(deltaTime, Iterations)` | 사용자 모드 (override 필수) | MOVE_Custom |

**커스텀 모드 추가 패턴**:

```cpp
// Custom MovementMode 정의
enum ECustomMovementMode { CMOVE_Glide, CMOVE_Climb, CMOVE_Dash };

UCLASS()
class UMyCharacterMovement : public UCharacterMovementComponent
{
    virtual void PhysCustom(float DeltaTime, int32 Iterations) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyCharMove_PhysCustom);
        Super::PhysCustom(DeltaTime, Iterations);

        switch (CustomMovementMode)
        {
        case CMOVE_Glide:  PhysGlide(DeltaTime, Iterations); break;
        case CMOVE_Climb:  PhysClimb(DeltaTime, Iterations); break;
        case CMOVE_Dash:   PhysDash(DeltaTime, Iterations);  break;
        }
    }
};
```

### 5.3 PerformMovement / SimulateMovement / SimulatedTick

[`CharacterMovementComponent.h:2252-2258`]:

```cpp
// 서버 또는 오너 (Authoritative + AutonomousProxy)
ENGINE_API virtual void PerformMovement(float DeltaTime);

// 시뮬레이션 프록시 — Tick 진입점
ENGINE_API virtual void SimulatedTick(float DeltaSeconds);

// SimulatedTick 안에서 호출 (실제 시뮬)
ENGINE_API virtual void SimulateMovement(float DeltaTime);
```

**3중 분기**:

| Role | Tick → 호출 함수 |
|------|------------------|
| `ROLE_Authority` (서버) | `TickComponent` → `PerformMovement` |
| `ROLE_AutonomousProxy` (조작 클라) | `TickComponent` → `PerformMovement` + `ReplicateMoveToServer` |
| `ROLE_SimulatedProxy` (관전 클라) | `TickComponent` → `SimulatedTick` → `SimulateMovement` |

### 5.4 UpdateCharacterStateBeforeMovement / AfterMovement

[`CharacterMovementComponent.h:1602-1605`] — 자식이 가장 자주 override 하는 hook:

```cpp
// PerformMovement 안 — 실제 위치 변화 직전
virtual void UpdateCharacterStateBeforeMovement(float DeltaSeconds) override
{
    Super::UpdateCharacterStateBeforeMovement(DeltaSeconds);

    if (bWantsToSprint && MovementMode == MOVE_Walking)
    {
        MaxWalkSpeed = SprintSpeed;
    }
}

// PerformMovement 안 — 위치 변화 직후 (회전 일부 후)
virtual void UpdateCharacterStateAfterMovement(float DeltaSeconds) override
{
    Super::UpdateCharacterStateAfterMovement(DeltaSeconds);
    // Surface 종속 효과 (발자국/먼지 등)
}
```

---

## 5.5 ~ 5.15 깊이 자료 — [`references/CharacterMovementDeep.md`](./references/CharacterMovementDeep.md) ✂️

> **Article 3 Level 3 progressive disclosure 적용** — 메인 SKILL.md 슬림화 (36KB → ~15KB) + 깊이 자료 별도 파일 (~21KB). 80% 케이스 메인만 로드, 깊이 필요 시 reference 추가 로드.

| § | 시스템 | reference 위치 |
|---|--------|----------------|
| 5.5 | **Floor 검출** (FFindFloorResult / FindFloor / ComputeFloorDist / Walkable / Perch) | [`§1`](./references/CharacterMovementDeep.md#1-floor-검출-시스템-ffindfloorresult--findfloor--computefloordist) |
| 5.6 | **Step Up + Ledge** (CanStepUp / StepUp / CheckLedgeDirection / ShouldCatchAir) | [`§2`](./references/CharacterMovementDeep.md#2-step-up--ledge-시스템) |
| 5.7 | **Movement Base** (엘리베이터·이동 플랫폼 — OldBaseQuat/Location + MaybeUpdateBasedMovement + UseRelativePosition) | [`§3`](./references/CharacterMovementDeep.md#3-movement-base-시스템-이동-표면--엘리베이터이동-플랫폼) |
| 5.8 | **Jump 시스템** (JumpZVelocity / AirControl / DoJump 5.5+ DeltaTime / NotifyJumpApex / ProcessLanded / GetMaxJumpHeight) | [`§4`](./references/CharacterMovementDeep.md#4-jump-시스템) |
| 5.9 | **Crouch 시스템** (bCanCrouch / CrouchedHalfHeight / Crouch/UnCrouch / CanCrouchInCurrentState 자식 override) | [`§5`](./references/CharacterMovementDeep.md#5-crouch-시스템) |
| 5.10 | **SetMovementMode + OnMovementModeChanged** (DefaultLandMode / GroundMode / virtual override 패턴) | [`§6`](./references/CharacterMovementDeep.md#6-setmovementmode--onmovementmodechanged) |
| 5.11 | **Velocity / Acceleration** (CalcVelocity / ApplyVelocityBraking / GetMaxAcceleration / ComputeAnalogInputModifier) | [`§7`](./references/CharacterMovementDeep.md#7-velocity--acceleration-계산) |
| 5.12 | **RootMotion 깊이** (Animation RM vs Programmatic RootMotionSource — Dash 표준 패턴 + Server/Client 동일 시뮬) | [`§8`](./references/CharacterMovementDeep.md#8-rootmotion-깊이) |
| 5.13 | **NavMesh Walking** (MOVE_NavWalking — bSweepWhileNavWalking / bProjectNavMeshWalking — 다수 AI 표준) | [`§9`](./references/CharacterMovementDeep.md#9-navmesh-walking-move_navwalking) |
| 5.14 | **RVO + Avoidance** (bUseRVOAvoidance / AvoidanceConsiderationRadius / AvoidanceWeight / NavAvoidanceMask + UAvoidanceManager) | [`§10`](./references/CharacterMovementDeep.md#10-rvo--avoidance) |
| 5.15 | **Force / Impulse** (AddImpulse / AddForce / AddRadialImpulse / bVelChange 차이) | [`§11`](./references/CharacterMovementDeep.md#11-force--impulse-외부-힘) |

> 본 reference 는 [`Article 3 progressive disclosure`](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) 표준 — 메인 routing 시 description 매칭 후, 깊이 필요 시만 추가 로드.

---

## 6. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-06 | **Level 3 분리 완료** — §5.5~§5.15 깊이 자료를 [`references/CharacterMovementDeep.md`](./references/CharacterMovementDeep.md) 로 이동. 메인 SKILL.md 36KB → ~15KB / reference ~21KB. Anthropic Skills Article 3 progressive disclosure 첫 적용 사례. |
