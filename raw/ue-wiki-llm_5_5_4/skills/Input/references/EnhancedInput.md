---
name: input-enhancedinput
description: 5.x Enhanced Input Plugin 메인 - UInputAction + UInputMappingContext + UInputAction Modifier/Trigger + UEnhancedInputLocalPlayerSubsystem + UEnhancedInputComponent + 4단 셋업.
---

# Input/EnhancedInput — 5.x 표준 Plugin 메인

> **위치**: `Engine/Plugins/EnhancedInput/Source/EnhancedInput/` (Plugin — 5.0+ 기본 활성)
> **모듈명**: `EnhancedInput` (Runtime + Editor)
> **베이스**: `UInputAction : public UDataAsset` / `UInputMappingContext : public UDataAsset` / `UEnhancedInputComponent : public UInputComponent`
> **요지**: **5.x 모든 신규 게임의 입력 표준** — InputAction 자산 + MappingContext Stack + Trigger / Modifier 분리.

---

## 🚨 공통 정책

| 정책 | EnhancedInput 적용 |
|------|-------------------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | InputAction 콜백 (특히 `ETriggerEvent::Triggered` — 매 프레임) 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무. |
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | UInputAction / UInputMappingContext = 작은 자산 (Hard Reference OK). PlayerController / Pawn UPROPERTY 표준. |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) | UEnhancedInputComponent = UInputComponent 자손 — 6대 정책 적용. |

---

## 1. 5종 핵심 (Plugin 의 모든 것)

| # | 클래스 | 역할 | 자세한 sub-skill |
|---|--------|------|-----------------|
| 1 | **UInputAction** | 입력 액션 자산 (`.uasset`) — Bool / Axis1D / Axis2D / Axis3D ValueType | [`Action`](../Action/SKILL.md) §1 |
| 2 | **UInputMappingContext (IMC)** | 키 매핑 자산 (`.uasset`) — Action ↔ Key + Trigger / Modifier per-mapping | [`Subsystem`](../Subsystem/SKILL.md) §3 |
| 3 | **UInputTrigger** | 트리거 조건 (Pressed / Released / Hold / Tap / Pulse / Chord / Down / Combo 8종) | [`Action`](../Action/SKILL.md) §3 |
| 4 | **UInputModifier** | 입력 변환 (DeadZone / Scale / Negate / Swizzle / Smooth / Response Curve 9종) | [`Action`](../Action/SKILL.md) §4 |
| 5 | **UEnhancedInputComponent** | BindAction(Action, ETriggerEvent, Function) — Pawn 측 콜백 등록 | [`Subsystem`](../Subsystem/SKILL.md) §5 |
| 6 | **UEnhancedInputLocalPlayerSubsystem** | LocalPlayer 별 IMC Stack — AddMappingContext / RemoveMappingContext | [`Subsystem`](../Subsystem/SKILL.md) §1 |

---

## 2. 표준 흐름 (입력 → 콜백)

```
[1] 하드웨어 입력 (Mouse / Keyboard / Gamepad / Touch)
  ↓
[2] SlateApplication 가 PlayerController 의 PlayerInput 으로 라우팅
  ↓
[3] UEnhancedPlayerInput::ProcessAxes / ProcessKeyDown
  ↓
[4] UEnhancedInputLocalPlayerSubsystem 의 IMC Stack 평가 (Priority 높은 것부터)
  ↓ 매핑된 Action 의 Modifier 적용 (DeadZone / Scale / Negate)
  ↓ Trigger 평가 (Pressed / Hold / Tap 등)
  ↓ ETriggerEvent 결정 (Triggered / Started / Completed 등)
[5] UEnhancedInputComponent::BindAction 콜백 호출 (FInputActionValue)
  ↓
[6] 게임 로직 (Pawn / Controller)
```

---

## 3. 표준 셋업 — 4단 (자산 → PC → Pawn → 게임 로직)

### 3.1 자산 작성 (Editor)

```
[자산 1] IA_Move (UInputAction)
  - ValueType: Axis2D
  - Triggers: (없음 — Modifier 만)
  - Modifiers: DeadZone (0.2), Smooth

[자산 2] IA_Jump (UInputAction)
  - ValueType: Bool
  - Triggers: Pressed, Released
  - Modifiers: (없음)

[자산 3] IMC_Default (UInputMappingContext)
  - Mapping 1: IA_Move ↔ W/A/S/D (Modifier: Negate Y for S, Swizzle for A/D)
  - Mapping 2: IA_Move ↔ Gamepad_LeftThumbstick_2D (Modifier: DeadZone 0.2)
  - Mapping 3: IA_Jump ↔ SpaceBar
  - Mapping 4: IA_Jump ↔ Gamepad_FaceButton_Bottom
  - Mapping 5: IA_Look ↔ Mouse_2D (Modifier: Scale 0.5)
  - Mapping 6: IA_Look ↔ Gamepad_RightThumbstick_2D (Modifier: DeadZone, Scale 100)
```

### 3.2 PlayerController — IMC 등록

```cpp
// MyPlayerController.h
UCLASS()
class AMyPlayerController : public APlayerController
{
    GENERATED_BODY()
public:
    UPROPERTY(EditDefaultsOnly, Category="Input")
    TObjectPtr<UInputMappingContext> DefaultMappingContext;

    UPROPERTY(EditDefaultsOnly, Category="Input")
    TObjectPtr<UInputMappingContext> MenuMappingContext;

    virtual void OnPossess(APawn* InPawn) override;
};

// MyPlayerController.cpp
void AMyPlayerController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyPC::OnPossess);

    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
    {
        if (DefaultMappingContext)
        {
            Subsystem->AddMappingContext(DefaultMappingContext, /*Priority=*/ 0);
        }
    }
}
```

### 3.3 Pawn / Character — Action 바인딩

```cpp
// MyCharacter.h
UCLASS()
class AMyCharacter : public ACharacter
{
    GENERATED_BODY()
public:
    UPROPERTY(EditDefaultsOnly, Category="Input")
    TObjectPtr<UInputAction> MoveAction;

    UPROPERTY(EditDefaultsOnly, Category="Input")
    TObjectPtr<UInputAction> LookAction;

    UPROPERTY(EditDefaultsOnly, Category="Input")
    TObjectPtr<UInputAction> JumpAction;

    UPROPERTY(EditDefaultsOnly, Category="Input")
    TObjectPtr<UInputAction> InteractAction;

protected:
    virtual void SetupPlayerInputComponent(UInputComponent* InInputComponent) override;

    void OnMove(const FInputActionValue& Value);
    void OnLook(const FInputActionValue& Value);
    void OnInteract();
};

// MyCharacter.cpp
void AMyCharacter::SetupPlayerInputComponent(UInputComponent* InInputComponent)
{
    Super::SetupPlayerInputComponent(InInputComponent);

    if (auto* EIC = Cast<UEnhancedInputComponent>(InInputComponent))
    {
        // Triggered = 매 프레임 (Axis 입력)
        EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AMyCharacter::OnMove);
        EIC->BindAction(LookAction, ETriggerEvent::Triggered, this, &AMyCharacter::OnLook);

        // Started = 한 번 (눌림 시점)
        EIC->BindAction(JumpAction, ETriggerEvent::Started, this, &ACharacter::Jump);

        // Completed = 한 번 (떨어짐 시점)
        EIC->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);

        // 매개변수 없는 콜백
        EIC->BindAction(InteractAction, ETriggerEvent::Started, this, &AMyCharacter::OnInteract);
    }
}

void AMyCharacter::OnMove(const FInputActionValue& Value)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::OnMove);
    const FVector2D Axis = Value.Get<FVector2D>();

    if (Controller)
    {
        const FRotator YawRot(0, Controller->GetControlRotation().Yaw, 0);
        const FVector Forward = FRotationMatrix(YawRot).GetUnitAxis(EAxis::X);
        const FVector Right   = FRotationMatrix(YawRot).GetUnitAxis(EAxis::Y);

        AddMovementInput(Forward, Axis.Y);
        AddMovementInput(Right,   Axis.X);
    }
}

void AMyCharacter::OnLook(const FInputActionValue& Value)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::OnLook);
    const FVector2D Axis = Value.Get<FVector2D>();
    AddControllerYawInput(Axis.X);
    AddControllerPitchInput(-Axis.Y);
}

void AMyCharacter::OnInteract()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::OnInteract);
    // 매개변수 없는 콜백 — Started Trigger 표준
}
```

### 3.4 동적 IMC 스택 (메뉴 / 차량 / 1인칭/3인칭 전환)

```cpp
// 메뉴 열기 — 게임 IMC 비활성 + 메뉴 IMC 활성
void AMyController::OpenMenu()
{
    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
    {
        Subsystem->RemoveMappingContext(DefaultMappingContext);
        Subsystem->AddMappingContext(MenuMappingContext, /*Priority=*/ 100);
    }

    // Input Mode 도 함께 변경
    FInputModeUIOnly Mode;
    Mode.SetWidgetToFocus(MenuWidget->TakeWidget());
    SetInputMode(Mode);
    bShowMouseCursor = true;
}

// 차량 탑승
void AMyCharacter::EnterVehicle()
{
    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
    {
        Subsystem->RemoveMappingContext(DefaultMappingContext);
        Subsystem->AddMappingContext(VehicleMappingContext, /*Priority=*/ 0);
    }
}

// 1인칭 ↔ 3인칭 전환 — IMC 분리
void AMyCharacter::ToggleFirstPerson()
{
    bIsFirstPerson = !bIsFirstPerson;
    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
    {
        if (bIsFirstPerson)
        {
            Subsystem->RemoveMappingContext(ThirdPersonMappingContext);
            Subsystem->AddMappingContext(FirstPersonMappingContext, /*Priority=*/ 10);
        }
        else
        {
            Subsystem->RemoveMappingContext(FirstPersonMappingContext);
            Subsystem->AddMappingContext(ThirdPersonMappingContext, /*Priority=*/ 10);
        }
    }
}
```

---

## 4. IMC Priority 관리 매트릭스

> **여러 IMC 동시 활성** — 동일 Action 중복 매핑 시 Priority 높은 것 우선.

| IMC | Priority | 사용 |
|-----|---------|------|
| MenuMappingContext | 100 | 메뉴 열림 (모든 게임 입력 차단) |
| DialogMappingContext | 50 | 대화창 (Skip / Choice) |
| FirstPersonMappingContext | 10 | 1인칭 모드 |
| DefaultMappingContext | 0 | 일반 게임 (가장 낮음) |

```cpp
// 메뉴 안에서도 일부 게임 입력 (Pause Toggle) 살리기
// → DefaultMappingContext 유지 + MenuMappingContext 추가 (Priority 100)
// → MenuMappingContext 가 Action 매핑 안 가지고 있는 키만 DefaultMappingContext 가 처리
```

---

## 5. ETriggerEvent 7종 (가장 중요)

| Event | 의미 | 사용 케이스 |
|-------|------|----------|
| `Triggered` | **트리거 활성 매 Tick** | Move (Axis 매 프레임 입력) |
| `Started` | **활성 시작 (한 번)** | Jump 시작 / Interact |
| `Ongoing` | 트리거가 부분 활성 (예: Hold 중) | Hold 진행 표시 |
| `Canceled` | **트리거 취소** (Hold 중 떨어짐) | Hold 중 취소 처리 |
| `Completed` | **활성 종료** (한 번) | Jump 떨어짐 / Hold 완료 |
| `None` | 비활성 | (드물게 — 명시적 디버그) |

### 표준 사용 패턴

| 입력 종류 | Trigger | Event |
|----------|---------|-------|
| 이동 / 룩 (Axis 연속) | (없음) | `Triggered` (매 프레임) |
| 점프 (눌림) | (없음) | `Started` (시작) + `Completed` (종료) |
| 차징 (Hold 후 발사) | `Hold (1.0s)` | `Triggered` (1초 후) + `Canceled` (1초 전 떨어짐) |
| 더블 탭 | `Tap (0.3s)` | `Triggered` |
| Combo (시퀀스) | `Combo` | `Triggered` |

> **자세한 = [`Action/SKILL.md §3 Trigger`](../Action/SKILL.md)**.

---

## 6. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 5.x 신규 코드를 Legacy `BindAction("Jump", IE_Pressed, ...)` 작성 | Enhanced Input 의무 — UInputAction 자산 + IMC |
| 2 | `SetupPlayerInputComponent` 안 IMC 등록 | LocalPlayerSubsystem (PlayerController OnPossess) |
| 3 | `SubsystemCast<UEnhancedInputComponent>` 결과 nullptr 가드 안 함 | `if (auto* EIC = Cast<...>(InInputComponent))` 의무 |
| 4 | `BindAction` 의 ETriggerEvent = `None` | 활성 안 됨 — `Triggered` / `Started` / `Completed` |
| 5 | Move Action 에 `Started` 만 바인딩 | Axis 입력 = `Triggered` (매 프레임) |
| 6 | Jump Action 에 `Triggered` 바인딩 | 매 프레임 호출됨 — `Started` (한 번) |
| 7 | IMC Priority 충돌 (메뉴 + 게임 모두 같은 Priority) | 메뉴 = 100 / 게임 = 0 분리 |
| 8 | Project Settings DefaultInput.ini 와 IMC 동시 사용 | 충돌 가능 — 일관성 유지 (Enhanced Input 만) |
| 9 | 🚨 InputAction 콜백 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |
| 10 | `bExecuteWhenPaused` 안 켜고 Pause Toggle Action | 메뉴 / Pause Toggle = `bExecuteWhenPaused = true` 의무 |

---

## 7. 체크리스트

- [ ] DefaultGame.ini 또는 .uproject 에서 `EnhancedInput` Plugin 활성
- [ ] Build.cs `PublicDependencyModuleNames.AddRange({"EnhancedInput"})`
- [ ] DefaultInput.ini 에서 `DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput`
- [ ] DefaultInput.ini 에서 `DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent`
- [ ] PlayerController 또는 Pawn 의 UPROPERTY = TObjectPtr<UInputAction> + UInputMappingContext
- [ ] OnPossess 또는 BeginPlay 에서 `Subsystem->AddMappingContext(IMC, Priority)`
- [ ] SetupPlayerInputComponent 에서 `Cast<UEnhancedInputComponent>` + BindAction
- [ ] Axis 입력 = `ETriggerEvent::Triggered` / 단발 입력 = `Started` + `Completed`
- [ ] InputAction 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] 메뉴 / 차량 / 모드 전환 = IMC Stack 동적 추가/제거
- [ ] Pause Toggle = `bExecuteWhenPaused = true`

---

## 8. 관련 sub-skill

- [`Input/SKILL.md`](../SKILL.md) — 메인 (Input 카테고리)
- [`Input/Action`](../Action/SKILL.md) — UInputAction + Trigger 8종 + Modifier 9종 깊이
- [`Input/Subsystem`](../Subsystem/SKILL.md) — UEnhancedInputLocalPlayerSubsystem + UEnhancedPlayerInput + Stack
- [`Input/InputCore`](../InputCore/SKILL.md) — FKey / EKeys / Touch / Gesture
- [`Input/Legacy`](../Legacy/SKILL.md) — UInputComponent (호환) + InputDevice (Force Feedback)
- [`Components/SystemComponents §1`](../../Components/references/SystemComponents.md) — UInputComponent 호스트
- [`GameFramework/Controller §3.2-§3.3`](../../GameFramework/references/Controller.md) — Input Mode + Stack
- [`GameFramework/PawnCharacter §3.2`](../../GameFramework/references/PawnCharacter.md) — SetupPlayerInputComponent

---

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. EnhancedInput Plugin 5종 핵심 (UInputAction / IMC / Trigger 8종 / Modifier 9종 / EnhancedInputComponent / Subsystem) + 표준 흐름 6단계 + **표준 셋업 4단** (자산 작성 / PC IMC 등록 / Pawn Action 바인딩 / 동적 IMC 스택) + IMC Priority 매트릭스 + **ETriggerEvent 7종** 표 + 표준 사용 매트릭스 + 함정 10종 + 11단 체크리스트. |
