---
name: components-systemcomponents
description: UInputComponent (Enhanced Input) + UChildActorComponent - Input 처리 + Actor 합성 + 6대 정책.
---

# Components / SystemComponents — Input + ChildActor (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/{InputComponent,ChildActorComponent}.h`
> **베이스**: `UActorComponent` → `UInputComponent` / `USceneComponent` → `UChildActorComponent`
> **요지**: **시스템 통합 컴포넌트** — Input 은 액션/축 바인딩, ChildActor 는 다른 Actor 를 컴포넌트처럼 부착. **Enhanced Input** 시스템이 5.x 기본이지만 베이스 `UInputComponent` 와 함께 동작.

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
| 🎯 **어셋 최적화** | 🚨 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) — **§9 ULODSyncComponent (본 sub-skill §9)** = **§1 SkeletalMesh Bone LOD 의 Modular Character 페어** (Body/Cape/Hair/Weapon LOD 동기화). 한 캐릭터에 여러 SkeletalMesh = ULODSyncComponent 의무 — Drive (Body) / Passive (Cape/Hair) / Disabled. CustomLODMapping 으로 LOD 비율 다른 Mesh 통합 (Body LOD 0~3 → Hair LOD 0~1). |

---

## 1. UInputComponent — 입력 바인딩 (Enhanced Input 깊이)

> **🎯 자세한 = [`Input` 카테고리](../../Input/SKILL.md)** — 5 sub-skill (EnhancedInput / Action / Subsystem / InputCore / Legacy) + 🚨 `Input/SKILL.md` 사용 규약 12종.
>
> 본 §은 **컴포넌트 측면 호스트** 만 다룸 — Enhanced Input 의 모든 깊이는 [`Input/EnhancedInput`](../../Input/references/EnhancedInput.md) + [`Input/Action`](../../Input/references/Action.md) + [`Input/Subsystem`](../../Input/references/Subsystem.md).

### 1.1 베이스 트리

```
UActorComponent
└── UInputComponent (Engine — Components/InputComponent.h)
    └── UEnhancedInputComponent (EnhancedInput Plugin — 5.x 표준)
```

### 1.2 5.x 표준 — UEnhancedInputComponent (5종 핵심)

> **5.x 신규 게임 = Enhanced Input 의무**. Legacy `BindAction(TEXT("Jump"), IE_Pressed, ...)` 는 마이그레이션 시만.

| # | 클래스 | 역할 | 자세한 |
|---|--------|------|------|
| 1 | **UInputAction** (자산) | Bool / Axis1D / Axis2D / Axis3D ValueType | [`Input/Action §1`](../../Input/references/Action.md) |
| 2 | **UInputMappingContext (IMC)** (자산) | Action ↔ Key 매핑 | [`Input/Subsystem §3`](../../Input/references/Subsystem.md) |
| 3 | **UInputTrigger** | Pressed/Released/Hold/Tap/Pulse/Chord/Down/Combo **8종** | [`Input/Action §3`](../../Input/references/Action.md) |
| 4 | **UInputModifier** | DeadZone/Scale/Negate/Swizzle/Smooth/ResponseCurve/FOVScaling **9종** | [`Input/Action §4`](../../Input/references/Action.md) |
| 5 | **UEnhancedInputLocalPlayerSubsystem** | LocalPlayer 별 IMC Stack 관리 | [`Input/Subsystem §1`](../../Input/references/Subsystem.md) |

### 1.3 표준 셋업 4단 (자산 → PC → Pawn → 게임 로직)

```cpp
// [1] DefaultInput.ini — Enhanced Input 활성 의무
// [/Script/Engine.InputSettings]
// DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput
// DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent

// [2] PlayerController — IMC 등록
void AMyPlayerController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyPC::OnPossess);

    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
    {
        Subsystem->AddMappingContext(DefaultMappingContext, /*Priority=*/ 0);
    }
}

// [3] Pawn — Action 바인딩
void AMyCharacter::SetupPlayerInputComponent(UInputComponent* InInputComponent)
{
    Super::SetupPlayerInputComponent(InInputComponent);

    if (auto* EIC = Cast<UEnhancedInputComponent>(InInputComponent))
    {
        // Axis 입력 = Triggered (매 프레임)
        EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AMyCharacter::OnMove);
        EIC->BindAction(LookAction, ETriggerEvent::Triggered, this, &AMyCharacter::OnLook);

        // 단발 입력 = Started + Completed
        EIC->BindAction(JumpAction, ETriggerEvent::Started,   this, &ACharacter::Jump);
        EIC->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);

        // 매개변수 없는 콜백 = Started 만
        EIC->BindAction(InteractAction, ETriggerEvent::Started, this, &AMyCharacter::OnInteract);
    }
}

// [4] 게임 로직
void AMyCharacter::OnMove(const FInputActionValue& Value)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::OnMove);
    const FVector2D Axis = Value.Get<FVector2D>();   // Axis2D ValueType
    AddMovementInput(GetActorForwardVector(), Axis.Y);
    AddMovementInput(GetActorRightVector(), Axis.X);
}
```

### 1.4 ETriggerEvent 7종 (가장 중요)

| Event | 호출 빈도 | 표준 사용 |
|-------|----------|----------|
| `Started` | 1회 (시작) | Jump / Interact (눌림) |
| `Triggered` | **매 프레임** | Move / Look (Axis 연속) |
| `Ongoing` | 매 Tick (Hold 중) | 차징 진행 표시 |
| `Canceled` | 1회 (Hold 취소) | 차징 취소 |
| `Completed` | 1회 (종료) | Jump 떨어짐 / Hold 완료 |

> **Move = `Triggered` / Jump = `Started` + `Completed` / Charge = `Triggered`(Hold) + `Canceled`** 표준.

### 1.5 IMC Priority 매트릭스 (동적 입력 모드)

| Priority | IMC | 활성 시점 |
|---------|-----|---------|
| **200** | `IMC_System` | 시스템 단축키 |
| **150** | `IMC_Modal` | 모달 윈도우 (Pause / Settings) |
| **100** | `IMC_Menu` | 메뉴 열림 |
| **50** | `IMC_Dialog` | 대화창 |
| **20** | `IMC_Vehicle` | 차량 탑승 |
| **10** | `IMC_FirstPerson` / `IMC_ThirdPerson` | 카메라 모드 |
| **0** | `IMC_Default` | 기본 게임 (Move/Look/Jump) |

### 1.6 콜백 시그니처 3종

```cpp
// 패턴 1: 매개변수 없음 (Started / Completed)
void AMyChar::OnJump();
EIC->BindAction(IA_Jump, ETriggerEvent::Started, this, &AMyChar::OnJump);

// 패턴 2: FInputActionValue (Axis 입력)
void AMyChar::OnMove(const FInputActionValue& Value);
EIC->BindAction(IA_Move, ETriggerEvent::Triggered, this, &AMyChar::OnMove);

// 패턴 3: FInputActionInstance (Hold 진행 / 시간 정보)
void AMyChar::OnCharge(const FInputActionInstance& Instance);
EIC->BindAction(IA_Charge, ETriggerEvent::Triggered, this, &AMyChar::OnCharge);
// Instance.ElapsedProcessedTime — Hold 진행 시간
```

### 1.7 Pause 입력 (메뉴 / 일시정지 토글)

```cpp
// Pause 중에도 실행 — IA_Pause 자산의 bTriggerWhenPaused = true 설정
// (UInputAction 자산 측에서 설정 — 코드 X)
```

### 1.8 동적 IMC 스택 (메뉴 / 차량 / 모드 전환)

```cpp
void AMyController::OpenMenu()
{
    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
    {
        Subsystem->RemoveMappingContext(DefaultMappingContext);
        Subsystem->AddMappingContext(MenuMappingContext, /*Priority=*/ 100);
    }

    FInputModeUIOnly Mode;
    Mode.SetWidgetToFocus(MenuWidget->TakeWidget());
    SetInputMode(Mode);
    bShowMouseCursor = true;
}
```

### 1.9 Legacy UInputComponent (호환만)

> **5.x 마이그레이션 시 / 단순 프로토타입만**. 신규 게임 사용 X.

```cpp
// Legacy — DefaultInput.ini 의 ActionMapping / AxisMapping 참조
PlayerInputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &ACharacter::Jump);
PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &AMyChar::MoveForward);

// 자세한 = Input/references/Legacy.md
```

### 1.10 Build.cs 의존성

```csharp
PublicDependencyModuleNames.AddRange(new string[] {
    "InputCore",                  // FKey / EKeys (베이스)
    "EnhancedInput",              // 5.x 표준 Plugin
});
```

```ini
; .uproject — Plugin 활성
{
    "Plugins": [
        { "Name": "EnhancedInput", "Enabled": true }
    ]
}
```

### 1.11 cross-link

- 🎯 [`Input/SKILL.md`](../../Input/SKILL.md) — Input 카테고리 메인
- 🎯 [`Input/EnhancedInput`](../../Input/references/EnhancedInput.md) — 5종 핵심 깊이
- 🎯 [`Input/Action`](../../Input/Act