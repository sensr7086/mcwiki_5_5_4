---
name: gameframework-pawncharacter
description: APawn (588 lines) + ACharacter (1,058 lines) - Jump/Crouch/Landing/RootMotion + Movement 모드 + 다수 NPC 환경 최적화 10종 (Tick 회피·URO·Significance·AnimationBudgetAllocator).
---

# GameFramework/PawnCharacter — APawn + ACharacter 합본 (게임 캐릭터 표준)

> **위치**: `Engine/Source/Runtime/Engine/Classes/GameFramework/Pawn.h` (588 lines) + `Character.h` (1,058 lines)
> **베이스**: `APawn : public AActor` / `ACharacter : public APawn`
> **요지**: APawn = **Controller 소유 가능한 Actor** (입력·Possess). ACharacter = **CapsuleComponent + Mesh + CharacterMovementComponent 페어** + Jump/Crouch/Launch/RootMotion 기본기 + 표준 캐릭터 복제.

---

## 🚨 공통 정책 (Components 6대 의무 + Pawn/Character 특화)

> 모든 Pawn/Character 작성 시 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) 의 6대 정책 + Pawn/Character 추가 규칙.

| # | 정책 | Pawn/Character 적용 |
|---|------|---------------------|
| 1 | **Mobility** | RootComponent (Pawn = 임의 / Character = CapsuleComponent) — **Movable 강제** (이동·점프 위해). Mesh = SkeletalMeshComponent (CapsuleComponent 자식, RelativeLocation = `FVector(0, 0, -CapsuleHalfHeight)` 표준 — 발 바닥 정렬). |
| 2 | **NewObject + DuplicateObject** | Spawn = `World->SpawnActor<ACharacter>(Class, Transform)` 만. **Possess 후 BeginPlay 보장 X** — `BeginPlay` vs `PossessedBy` 둘 중 늦은 시점에 캐싱. |
| 3 | **GC 방어** | `TWeakObjectPtr<AController>` 캐싱 + `GetController()` 매번 비싸지 않지만 캐싱 권장. **Pawn 의 Controller 는 PossessedBy/UnPossessed 에서만 변경** — Tick 안 매번 검사 금지. |
| 4 | **Cached References** | `BeginPlay` + `PossessedBy` 둘 다 fired 후에 → `CachedController` / `CachedMesh` / `CachedCMC` 캐싱 (TWeakObjectPtr). `GetCharacterMovement()` 는 `inline` 이라 비용 0 — 캐싱 불필요. |
| 5 | **PrimaryActorTick** | **🚨 ACharacter::Tick 은 기본 OFF 권장** — `UCharacterMovementComponent::TickComponent` 가 모든 이동·물리·입력 처리. ACharacter::Tick 활성 시 매 프레임 추가 비용. AI 는 Significance + TickInterval 조정. |
| 6 | **CDO + OnConstruction** | `CreateDefaultSubobject` 는 Constructor 안만 — Capsule / Mesh / CharacterMovement 모두 Constructor. **OnConstruction 안 멱등** — Mesh AnimClass 변경 등은 BeginPlay 에서. |
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — **SkeletalMesh / AnimBP / PhysicsAsset / Audio = Soft + UAssetManager Primary Asset 표준**. Modular Character (Body/Cape/Hair/Weapon) = `UPrimaryDataAsset` + Bundle 분리 (`Body` / `Equipment` / `Cosmetic`). 자주 Spawn 되는 Character (적/NPC) = Match Start `PreloadPrimaryAssets(bLoadRecursive=true)` 의무 — Subobject (Mesh+AnimBP+PhysicsAsset+Audio) 모두 메모리 상주. AI Pawn = Significance 통합 + Bundle 동적 변경 (가까울 때 `HighQuality` / 멀 때 `LowQuality`). 자세한 패턴 = [`Actor §12`](../Actor/SKILL.md). |
| 🎯 **어셋 최적화** | 🚨 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) — **§1 SkeletalMesh Bone LOD** (USkeletalMeshLODSettings + BonesToRemove 70/50/30/15% + BonesToPrioritize head/hand/weapon_socket/IK + LODHysteresis 0.05 + 5.x SkinCacheUsage) 직접 적용. 본 sub-skill **§6 최적화 10종** (Tick 회피·URO·EVisibilityBasedAnimTickOption·Significance·AnimationBudgetAllocator·Network·Mesh LOD·Capsule Channel·PostProcess AnimBP LOD·**AI vs Player 매트릭스** Significance 1.0/0.5/0.1) 이 §6 통합 매트릭스의 **9개 항목** (Bone / SkinCache / AnimTickOption / URO / PhysicsAsset / Niagara Spawn / Audio / NetUpdateFrequency / Capsule Overlap) 와 1:1 페어 — **다수 캐릭터 환경 = §6 표준 결정 트리** (캐릭터 < 10 → Significance 수동 / 10~50 → +URO+AnimTickOption / 50~200 → +AnimationBudgetAllocator / 200+ → +Pooling+Mass Entity). |

---

## 1. 의존 트리 + 컴포넌트 페어

```
AActor                              (GameFramework/Actor)
└── APawn                           (GameFramework/PawnCharacter §3)
    │
    │  📌 핵심: Controller 소유 + InputComponent 자동 생성 + AddMovementInput
    │
    └── ACharacter                  (GameFramework/PawnCharacter §4)
         │
         │  📌 핵심: CapsuleComponent + Mesh + CharacterMovementComponent 페어
         │  📌 추가: Jump / Crouch / Launch / RootMotion / SmoothCorrection
         │
         ├─ CapsuleComponent (RootComponent)        ── Movable 콜리전
         ├─ Mesh: USkeletalMeshComponent             ── Capsule 자식 (발 바닥 정렬)
         └─ CharacterMovement: UCharacterMovementComponent  ── 별도 (UpdatedComponent = Capsule)
```

> **5.x Modular Character**: Mesh 외 추가 SkeletalMeshComponent (Cape / Hair / Weapon) 는 Mesh 자식으로 부착. LOD 동기화 = `ULODSyncComponent` ([`SystemComponents §9`](../../Components/references/SystemComponents.md)).

---

## 2. APawn 라이프사이클 (Actor 11단계 + Pawn 추가)

```
[1-7] Actor 라이프사이클 (Constructor → BeginPlay)  ── GameFramework/Actor §1
[8] PossessedBy(NewController)       ── 서버에서 Controller 할당 시 (Possess 호출)
[9] OnRep_Controller()                ── 클라이언트 Controller 변경 복제 시
[10] Restart()                         ── Pawn 재시작 (Respawn 후 첫 Possess + 매번 PossessedBy 후)
[11] SetupPlayerInputComponent(IC)    ── Possess 후 PlayerController 측 호출 — 입력 바인딩
[12] Tick(DeltaSeconds)                ── 매 프레임 (활성 시)
[13] UnPossessed()                     ── Controller 해제 시
[14] EndPlay → Destroyed → BeginDestroy ── Actor 종료
```

> **Possess 흐름** (Controller → Pawn):
> ```
> Server: AController::Possess(InPawn)
>   ↓ Pawn->PossessedBy(this)            ── Controller 캐싱 / OnRep_Controller 트리거
>   ↓ Pawn->Restart()                     ── 입력 셋업 + AnimBP 재설정 등
>   ↓ Pawn->SetupPlayerInputComponent(IC) ── 키 바인딩
> ```

---

## 3. APawn 핵심 (588 lines)

### 3.1 Controller 소유 흐름

```cpp
// Pawn.h:199 — Controller 는 ReplicatedUsing
UPROPERTY(replicatedUsing=OnRep_Controller)
TObjectPtr<AController> Controller;

// Pawn.h:359 — PossessedBy (Server only)
ENGINE_API virtual void PossessedBy(AController* NewController);
{
    // 베이스 동작:
    // 1. Controller = NewController
    // 2. SetOwner(NewController)
    // 3. NotifyControllerChanged()
    // 4. ReceiveControllerChanged (BP)
}

// Pawn.h:267 — OnRep_Controller (Client)
ENGINE_API virtual void OnRep_Controller();

// Pawn.h:366 — UnPossessed (Server)
ENGINE_API virtual void UnPossessed();
```

```cpp
// MyPawn.cpp — Controller 캐싱 표준
void AMyPawn::PossessedBy(AController* NewController)
{
    Super::PossessedBy(NewController);   // ⚠️ 처음 — 베이스가 Controller / Owner 설정
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyPawn::PossessedBy);

    // 이 시점 — Controller 가 정해짐. 캐싱 + 초기 셋업
    CachedController = NewController;
    if (auto* PC = Cast<APlayerController>(NewController))
    {
        // PlayerController 페어 셋업
    }
    else if (auto* AIC = Cast<AAIController>(NewController))
    {
        // AI 페어 셋업
    }
}

void AMyPawn::OnRep_Controller()
{
    Super::OnRep_Controller();
    // Client — Controller 가 복제됨. 캐싱
    CachedController = Controller;
}

void AMyPawn::UnPossessed()
{
    // 정리 작업 먼저
    CachedController.Reset();
    Super::UnPossessed();                // ⚠️ 마지막
}
```

### 3.2 InputComponent 자동 생성 (Possess 후)

> **PlayerController 가 Possess 시 자동으로 Pawn 의 InputComponent 생성 + SetupPlayerInputComponent 호출**.

```cpp
// Pawn.h:465 — 베이스가 자동 호출 (UInputComponent 생성)
ENGINE_API virtual UInputComponent* CreatePlayerInputComponent();

// Pawn.h:471 — 자식이 override 하여 키 바인딩
virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) {}
```

```cpp
// MyCharacter.cpp — Enhanced Input 표준 (5.x)
void AMyCharacter::SetupPlayerInputComponent(UInputComponent* InInputComponent)
{
    Super::SetupPlayerInputComponent(InInputComponent);

    if (auto* EIC = Cast<UEnhancedInputComponent>(InInputComponent))
    {
        EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AMyCharacter::OnMove);
        EIC->BindAction(LookAction, ETriggerEvent::Triggered, this, &AMyCharacter::OnLook);
        EIC->BindAction(JumpAction, ETriggerEvent::Started, this, &ACharacter::Jump);
        EIC->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);
        EIC->BindAction(CrouchAction, ETriggerEvent::Started, this, &AMyCharacter::ToggleCrouch);
    }
}
```

> **자세한 Enhanced Input 패턴은 [`Components/SystemComponents §1`](../../Components/references/SystemComponents.md)**.

### 3.3 이동 입력 — AddMovementInput

```cpp
// Pawn.h:484 — 입력 누적 (CharacterMovementComponent 가 ConsumeMovementInputVector 로 소비)
ENGINE_API virtual void AddMovementInput(FVector WorldDirection, float ScaleValue = 1.0f, bool bForce = false);

// Pawn.h:494/515 — 입력 조회 / 소비
ENGINE_API FVector GetPendingMovementInputVector() const;
ENGINE_API virtual FVector ConsumeMovementInputVector();
```

```cpp
void AMyCharacter::OnMove(const FInputActionValue& Value)
{
    const FVector2D Input = Value.Get<FVector2D>();
    if (auto* PC = Cast<APlayerController>(Controller))
    {
        const FRotator YawRot(0, PC->GetControlRotation().Yaw, 0);
        const FVector Forward = FRotationMatrix(YawRot).GetUnitAxis(EAxis::X);
        const FVector Right   = FRotationMatrix(YawRot).GetUnitAxis(EAxis::Y);
        AddMovementInput(Forward, Input.Y);   // 누적 — CharacterMovement 가 다음 Tick 에 소비
        AddMovementInput(Right,   Input.X);
    }
}
```

### 3.4 카메라 입력 (Yaw / Pitch / Roll)

```cpp
// Pawn.h:524/533 — Controller 의 ControlRotation 변경
ENGINE_API virtual void AddControllerYawInput(float Val);
ENGINE_API virtual void AddControllerPitchInput(float Val);
ENGINE_API virtual void AddControllerRollInput(float Val);
```

> **bUseControllerRotationYaw/Pitch/Roll** 활성 시 — Pawn 회전 = Controller 회전. **Character 표준** = `bUseControllerRotationYaw=false` + `CharacterMovement->bOrientRotationToMovement=true` (이동 방향으로 회전).

### 3.5 AutoPossess (BP 자동 소유)

```cpp
// Pawn.h:105 — 자동 PlayerController 할당 (Player0/1/2/3)
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=Pawn)
TEnumAsByte<EAutoReceiveInput::Type> AutoPossessPlayer;   // Disabled / Player0~7

// Pawn.h:113 — 자동 AIController 할당
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=Pawn)
EAutoPossessAI AutoPossessAI;   // Disabled / PlacedInWorld / Spawned / PlacedInWorldOrSpawned
```

> **함정**: AutoPossessAI = `Spawned` 인데 Spawn 후 즉시 SetActorEnableCollision(false) 등 — Possess 안 됨 (NavMesh 검사 실패 등). 표준 = `PlacedInWorldOrSpawned`.

### 3.6 EyeHeight / GetPawnViewLocation

```cpp
// Pawn.h:98 — 시점 높이 (BaseEyeHeight 기본값)
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category=Camera)
float BaseEyeHeight;

// Pawn.h:436 — Camera 위치 (1인칭 카메라 표준)
ENGINE_API virtual FVector GetPawnViewLocation() const;
{
    // 베이스: GetActorLocation() + FVector(0, 0, BaseEyeHeight)
}
```

---

## 4. ACharacter 깊이 (1,058 lines — 가장 중요)

### 4.1 컴포넌트 페어 (Constructor 셋업)

```cpp
// Character.h:259/263 — 페어 멤버
TObjectPtr<UCharacterMovementComponent> CharacterMovement;
TObjectPtr<UCapsuleComponent> CapsuleComponent;
TObjectPtr<USkeletalMeshComponent> Mesh;   // (Mesh 는 protected)

// Character.h:404/410 — 표준 이름
static FName CharacterMovementComponentName;   // "CharMoveComp"
static FName CapsuleComponentName;             // "CollisionCylinder"

// 표준 Constructor
ACharacter::ACharacter()
{
    CapsuleComponent = CreateDefaultSubobject<UCapsuleComponent>(CapsuleComponentName);
    CapsuleComponent->InitCapsuleSize(34.f, 88.f);   // Radius / HalfHeight
    CapsuleComponent->SetCollisionProfileName(UCollisionProfile::Pawn_ProfileName);
    RootComponent = CapsuleComponent;

    Mesh = CreateOptionalDefaultSubobject<USkeletalMeshComponent>(MeshComponentName);
    if (Mesh)
    {
        Mesh->SetupAttachment(CapsuleComponent);
        Mesh->SetRelativeLocation(FVector(0, 0, -88.f));   // 발 바닥 정렬
        Mesh->SetRelativeRotation(FRotator(0, -90.f, 0));   // X 전방 회전
    }

    CharacterMovement = CreateDefaultSubobject<UCharacterMovementComponent>(CharacterMovementComponentName);
    CharacterMovement->UpdatedComponent = CapsuleComponent;   // 이동 대상 = Capsule
}
```

### 4.2 Jump 시스템 (5.5+ DeltaTime 처리)

| 필드 / 메소드 | 위치 | 의미 |
|------------|------|------|
| `bPressedJump` | `Character.h:557` | Jump 버튼 눌린 상태 |
| `JumpKeyHoldTime` | `Character.h:604` | Jump 버튼 유지 시간 (현재) |
| `JumpForceTimeRemaining` | `Character.h:608` | 점프 힘 잔여 시간 |
| `JumpMaxHoldTime` | `Character.h:621` | 점프 버튼 최대 유지 시간 — 0 이면 즉시 끝 |
| `JumpMaxCount` | `Character.h:630` | 점프 횟수 (1 = 단일 / 2 = 더블 점프) |
| `JumpCurrentCount` | `Character.h:639` | 현재 점프 횟수 |
| `Jump()` | `Character.h:711` | 점프 트리거 (bPressedJump = true) |
| `StopJumping()` | (Character.h) | 점프 종료 (버튼 뗌) |
| `CanJump()` | (Character.h) | 점프 가능 여부 (override 가능) |
| `NotifyJumpApex()` | `Character.h:806` | 점프 정점 통과 시 콜백 |
| `IsJumpProvidingForce()` | (Character.h) | 점프 힘 적용 중인지 |

```cpp
// 더블 점프 — 단순 override
class AMyCharacter : public ACharacter
{
    AMyCharacter()
    {
        JumpMaxCount = 2;
        JumpMaxHoldTime = 0.3f;   // 0.3s 유지로 점프 높이 가변
    }

    virtual bool CanJumpInternal_Implementation() const override
    {
        // 일반 + 더블 점프 허용 (1회 점프 후 공중에서도)
        const bool bCanJumpFromGround = Super::CanJumpInternal_Implementation();
        return bCanJumpFromGround || JumpCurrentCount < JumpMaxCount;
    }

    virtual void NotifyJumpApex() override
    {
        Super::NotifyJumpApex();
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::NotifyJumpApex);
        // 점프 정점 — VFX / SFX 등
    }
};
```

> **Enhanced Input 표준 바인딩**:
> ```cpp
> EIC->BindAction(JumpAction, ETriggerEvent::Started, this, &ACharacter::Jump);
> EIC->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);
> ```

### 4.3 Crouch 시스템 (복제 안전)

| 필드 / 메소드 | 위치 | 의미 |
|------------|------|------|
| `bIsCrouched` | `Character.h:545` | **복제 (OnRep_IsCrouched)** |
| `CrouchedEyeHeight` | `Character.h:535` | Crouch 시 시점 높이 |
| `Crouch(bClientSimulation)` | (Character.h) | Crouch 요청 (CMC 측 처리) |
| `UnCrouch(bClientSimulation)` | (Character.h) | UnCrouch 요청 |
| `CanCrouch()` | (Character.h) | 가능 여부 (override) |
| `OnStartCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust)` | (Character.h) | 시작 콜백 (모든 사이드) |
| `OnEndCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust)` | (Character.h) | 종료 콜백 |
| `OnRep_IsCrouched()` | `Character.h:553` | 복제 콜백 (Simulated Proxy) |

```cpp
// CharacterMovement 측 설정 (Constructor)
CharacterMovement->bCanWalkOffLedgesWhenCrouching = true;
CharacterMovement->CrouchedHalfHeight = 50.f;
CharacterMovement->bCrouchMaintainsBaseLocation = true;   // 머리 고정 / 발 위치 변동

// Character 측 콜백 — Mesh / 카메라 보정
void AMyCharacter::OnStartCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
    Super::OnStartCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
    // Mesh 보정 — bCrouchMaintainsBaseLocation 인 경우 Mesh 위치 조정
    if (Mesh && bCrouchMaintainsBaseLocation)
    {
        Mesh->SetRelativeLocation(FVector(0, 0, -88.f + HalfHeightAdjust));
    }
}

void AMyCharacter::OnEndCrouch(float HalfHeightAdjust, float ScaledHalfHeightAdjust)
{
    Super::OnEndCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust);
    if (Mesh && bCrouchMaintainsBaseLocation)
    {
        Mesh->SetRelativeLocation(FVector(0, 0, -88.f));
    }
}
```

### 4.4 Landing 시스템

```cpp
// Character.h:37 — 델리게이트 (BP 노출)
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLandedSignature, const FHitResult&, Hit);

// Character.h:820 — Landed (CharacterMovement 가 Falling → Walking 전환 시)
ENGINE_API virtual void Landed(const FHitResult& Hit);

// Character.h:842 — OnLanded BP 콜백
ENGINE_API void OnLanded(const FHitResult& Hit);

// Character.h:831 — 델리게이트
FLandedSignature LandedDelegate;
```

```cpp
void AMyCharacter::Landed(const FHitResult& Hit)
{
    Super::Landed(Hit);
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::Landed);

    // 낙하 데미지 + 더블 점프 카운트 리셋
    JumpCurrentCount = 0;
    if (LastFallVelocity.Z < -1500.f)
    {
        ApplyFallDamage();
    }
}
```

### 4.5 OnMovementModeChanged (모드 전환 콜백)

```cpp
// CharacterMovement 가 SetMovementMode 시 자동 호출
virtual void OnMovementModeChanged(EMovementMode PrevMovementMode, uint8 PrevCustomMode = 0) override
{
    Super::OnMovementModeChanged(PrevMovementMode, PrevCustomMode);
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::OnMovementModeChanged);

    // Falling → Walking = Landing 처리됨 (위 Landed 가 먼저 호출)
    if (CharacterMovement->MovementMode == MOVE_Swimming)
    {
        // 수영 모드 — Mesh AnimBP 변경 등
    }
}
```

> **5종 모드** 전환 깊이는 [`Components/MovementComponents §5.10`](../../Components/references/MovementComponents.md).

### 4.6 LaunchCharacter (외부 Velocity 적용)

```cpp
// Character.h:791
ENGINE_API virtual void LaunchCharacter(FVector LaunchVelocity, bool bXYOverride, bool bZOverride);

// 폭발 / 점프 패드 / 그래플
GetMesh()->SetSimulatePhysics(false);
LaunchCharacter(FVector(0, 0, 1500.f), /*bXYOverride=*/false, /*bZOverride=*/true);
```

> **bXYOverride / bZOverride**:
> - false = 기존 Velocity 에 더하기
> - true = 기존 Velocity 무시하고 덮어쓰기

### 4.7 RootMotion 시스템

| 영역 | 메커니즘 |
|------|---------|
| **Animation Root Motion** | AnimBP / AnimMontage 의 RootBone 모션 → CharacterMovement 가 자동 적용 |
| **Programmatic Root Motion Source** | `FRootMotionSource_*` (JumpForce / RadialForce / MoveToForce 등) — Code 에서 추가 |
| **Replication** | `RepRootMotion` (FRepRootMotionMontage) + `OnRep_RepRootMotion` |
| **Simulated Proxy 보정** | `bClientResimulateRootMotion` (Character.h:569) |

> **자세한 RootMotion 패턴은 [`MovementComponents §5.12`](../../Components/references/MovementComponents.md)**.

### 4.8 Movement Base 시스템 (이동 표면)

```cpp
// Character.h:431/435 — 현재 / 복제된 베이스 (엘리베이터 / 이동 플랫폼)
struct FBasedMovementInfo BasedMovement;
struct FBasedMovementInfo ReplicatedBasedMovement;   // 복제용

// Character.h:445 — 복제 콜백
ENGINE_API virtual void OnRep_ReplicatedBasedMovement();
```

> **자세한 Movement Base 패턴은 [`MovementComponents §5.7`](../../Components/references/MovementComponents.md)**.

### 4.9 ServerMove RPC (CharacterMovement Networking)

> **모든 ServerMove* RPC 는 ACharacter 에 선언되지만 실제 처리는 UCharacterMovementComponent 에 위임**. `Character.h:334-381` 의 ServerMoveDualHybridRootMotion / ClientAdjustRootMotionPosition 등.

```cpp
// 5.0 부터 Packed 으로 통합 (ServerMovePacked / ClientMoveResponsePacked)
// 자세한 구조 = MovementComponents §6.5
```

### 4.10 Network Smoothing (Simulated Proxy)

> **Character::Tick 안에서 NetworkSmoothing 자동 적용** — `MeshTranslationOffset` 보정. 활성 토글:

```cpp
CharacterMovement->NetworkSmoothingMode = ENetworkSmoothingMode::Linear;   // 기본
CharacterMovement->NetworkSmoothingMode = ENetworkSmoothingMode::Exponential;
CharacterMovement->NetworkSmoothingMode = ENetworkSmoothingMode::Replay;   // 리플레이
CharacterMovement->NetworkSmoothingMode = ENetworkSmoothingMode::Disabled;  // OFF (디버그)
```

> 자세한 Smoothing = [`MovementComponents §6.7`](../../Components/references/MovementComponents.md).

---

## 5. Pawn vs Character 분기 결정

| 시나리오 | 베이스 |
|---------|-------|
| 캐릭터 (사람·동물·로봇) — 걷기/점프/Crouch/낙하 | **ACharacter** |
| 차량 — Wheel / Suspension / Throttle | **APawn** + ChaosVehicleMovementComponent |
| 비행체 — 6DoF / Free Roam | **APawn** + 커스텀 Movement |
| 정찰 카메라 (RTS) — 입력만 | **APawn** + Spectator |
| 고정 포탑 — 회전 + 발사 | **APawn** + RotatingMovementComponent |
| 워킹 메카 (Mech) — 다리 IK + 점프 | **ACharacter** + 커스텀 CMC |
| 평면 2.5D 게임 (사이드 뷰) | **ACharacter** (CMC 가 모든 처리) |

> **선택 기준**: Capsule 기반 콜리전 + 점프 + Crouch + 걷기 = `ACharacter`. 그 외 = `APawn`.

---

## 6. 🎯 최적화 방안 — [`references/CharacterOptimization.md`](./references/CharacterOptimization.md) ✂️

> **Article 3 Level 3 progressive disclosure 적용** — 메인 SKILL.md 슬림화 (34KB → ~17KB) + 깊이 자료 별도 파일 (~13KB).
>
> **Character 중심 매 프레임 다수 캐릭터 환경 최적화 10종** — 각각의 코드 패턴·매트릭스·결정 트리는 reference 참조.

| § | 최적화 영역 | 핵심 | reference |
|---|------------|------|-----------|
| 6.1 | **Tick 회피** | `PrimaryActorTick.bCanEverTick = false` (CMC 가 처리) | [`§1`](./references/CharacterOptimization.md#1-tick-회피-가장-큰-최적화) |
| 6.2 | **Animation Tick 최적화** | URO + EVisibilityBasedAnimTickOption (5종) + bRecentlyRendered | [`§2`](./references/CharacterOptimization.md#2-animation-tick-최적화-가장-큰-비용) |
| 6.3 | **Significance 통합** | USignificanceManager 등록 + 거리 기반 SetTickInterval | [`§3`](./references/CharacterOptimization.md#3-significance-통합-다수-npc-환경-표준) |
| 6.4 | **AnimationBudgetAllocator 5.x** | USkeletalMeshComponentBudgeted + TargetMs 5ms | [`§4`](./references/CharacterOptimization.md#4-animationbudgetallocator-5x-plugin--significance-의-자동화) |
| 6.5 | **Network 최적화** | NetUpdateFrequency / NetCullDistance / NetworkSmoothingMode | [`§5`](./references/CharacterOptimization.md#5-network-최적화) |
| 6.6 | **Mesh LOD (Modular)** | ULODSyncComponent (Body Drive + Cape/Hair Passive) | [`§6`](./references/CharacterOptimization.md#6-mesh-lod-modular-character) |
| 6.7 | **Capsule Collision Channel** | Pawn 프로파일 vs CharacterMesh (Block only — Overlap 0) | [`§7`](./references/CharacterOptimization.md#7-capsule-collision-channel-오버랩-비용) |
| 6.8 | **PostProcess AnimBP** | SetPostProcessAnimBPLODThreshold (LOD 2 이하만) | [`§8`](./references/CharacterOptimization.md#8-postprocess-animbp--분리-lod) |
| 6.9 | **AI vs Player 매트릭스** | 9개 항목 4단계 (Player / AI Sig 1 / 0.5 / 0.1) | [`§9`](./references/CharacterOptimization.md#9-ai-vs-player-분리-표준-매트릭스) |
| 6.10 | **표준 결정 트리** | 캐릭터 수 별 (10 / 50 / 200) 단계적 적용 | [`§10`](./references/CharacterOptimization.md#10-표준-최적화-결정-트리) |

> reference 는 [`Article 3 progressive disclosure`](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) 표준 — 메인 routing 후 깊이 필요 시 추가 로드.

<!-- LEVEL3_SPLIT_MARKER — §6 content moved to references/CharacterOptimization.md (2026-05-06) -->

[원본 §6 ~ §6.10 본문 (Tick 회피 / Animation Tick / Significance / AnimationBudget / Network / Mesh LOD / Capsule Channel / PostProcess / AI vs Player 매트릭스 / 결정 트리) 은 모두 [`references/CharacterOptimization.md`](./references/CharacterOptimization.md) 로 이동됨]

---

## 7. 함정 & 안티패턴 (15종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | `ACharacter::Tick` 활성 + 매 프레임 로직 | CMC 가 처리 — Tick 비활성 + 필요 시 TickInterval |
| 2 | `Constructor` 안 `GetMesh()->SetAnimClass(...)` 동적 | Constructor 안 BP 클래스 모름 — `BeginPlay` 또는 BP 의 DefaultClass |
| 3 | `BeginPlay` 에서 `GetController()` 사용 — Possess 전 nullptr 가능 | `PossessedBy` 콜백에서 캐싱 — BeginPlay vs Possess 두 시점 모두 처리 |
| 4 | Server 가 `bIsCrouched = true` 직접 설정 | ⚠️ `Crouch()` / `UnCrouch()` 호출 — CMC 가 Capsule HalfHeight + bIsCrouched 모두 갱신 |
| 5 | Crouch 후 `OnStartCrouch` 안 Mesh 위치 보정 안 함 | bCrouchMaintainsBaseLocation 일 때 Mesh RelativeLocation 보정 의무 |
| 6 | `JumpMaxCount = 2` 인데 `CanJumpInternal` override 안 함 | 베이스는 JumpCurrentCount == 0 만 허용 — override 필요 |
| 7 | Multicast RPC 로 모든 클라에 Jump 명령 전파 | 표준 = `bPressedJump = true` + ServerMove 자동 복제 — Multicast 불필요 |
| 8 | RootMotion 안 `bClientResimulateRootMotion` 안 처리 | Simulated Proxy 가 RM 발산 — 5.x 자동 처리되지만 자식 override 시 주의 |
| 9 | Possess 전 `SetupPlayerInputComponent` 호출 | PlayerController 가 Possess 시 자동 호출 — 직접 호출 금지 |
| 10 | AI Pawn `AutoPossessAI = Spawned` 인데 NavMesh 없음 | NavMesh 검사 실패 — Possess 안 됨. Recast Volume 추가 또는 `Spawned` 만 |
| 11 | 🚨 `BeginPlay` / `