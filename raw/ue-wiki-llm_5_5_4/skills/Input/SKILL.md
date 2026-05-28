---
name: input-main
description: Tier 1 Input 메인 — EnhancedInput (5.x Plugin) + Action (UInputAction + Trigger 8종 + Modifier 9종) + Subsystem (UEnhancedInputLocalPlayerSubsystem + IMC Stack) + InputCore (FKey + EKeys 200+) + Legacy (UInputComponent + InputDevice + Force Feedback + Haptic) 5개 sub-skill. 5.x Enhanced Input 표준.
---

# Input — 입력 시스템 (Enhanced Input + InputCore + Legacy)

> **위치**: Plugin `Engine/Plugins/EnhancedInput/Source/EnhancedInput/` (5.x 표준) + Engine `InputCore/` (베이스) + Engine `Components/InputComponent.h` (legacy) + `InputDevice/` (Force Feedback / Haptic)
> **요지**: **모든 게임 입력의 진입점** — 5.x = **Enhanced Input Plugin 표준** (InputAction 자산 기반) + Legacy UInputComponent (호환) + InputCore (FKey 200+ 정의) + InputDevice (Force Feedback / Haptic / RawInput).
> **카테고리**: `[Input]` — 게임 입력 처리

---

## 🚨 공통 정책 (모든 Input sub-skill 의무)

| 정책 | Input 적용 |
|------|----------|
| 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) | **모든 InputAction 콜백 / Tick 입력 처리 첫 줄** `TRACE_CPUPROFILER_EVENT_SCOPE` 의무. 매 프레임 호출되는 ETriggerEvent::Triggered 가 가장 흔함. |
| 🎯 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) | UInputAction / UInputMappingContext = **작은 자산** (Hard Reference OK). PlayerController / Pawn 의 Constructor 안 BP 지정 표준. |
| 🚨 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) | UInputComponent 는 UActorComponent — 6대 정책 적용. UEnhancedInputComponent 는 UInputComponent 자손 (자동). |

---

## 1. sub-skill 인덱스 (5개 + 메인)

| # | sub-skill | 위치 | 한 줄 요약 |
|---|-----------|------|-----------|
| 1 | [`EnhancedInput`](./EnhancedInput/SKILL.md) | `skills/Input/references/EnhancedInput.md` | **5.x 표준 Plugin 메인** — 5종 핵심 (InputAction / IMC / Trigger / Modifier / EnhancedInputComponent / Subsystem) + 표준 패턴 + Pawn / PlayerController 통합 |
| 2 | [`Action`](./Action/SKILL.md) | `skills/Input/references/Action.md` | **UInputAction 자산** + ValueType 4종 (Bool/Axis1D/Axis2D/Axis3D) + **ETriggerEvent 5종** (Triggered/Started/Ongoing/Canceled/Completed + None) + **UInputTrigger 10종** (Down/Pressed/Released/Hold/HoldAndRelease/Tap/Pulse/ChordAction/ChordBlocker/Combo) + **UInputModifier 11종** (DeadZone/Scalar/ScaleByDeltaTime/Negate/Swizzle/Smooth/SmoothDelta/ResponseCurveExp/ResponseCurveUser/FOVScaling/ToWorldSpace) — UE 5.5 |
| 3 | [`Subsystem`](./Subsystem/SKILL.md) | `skills/Input/references/Subsystem.md` | **UEnhancedInputLocalPlayerSubsystem** (LocalPlayer 별) + **UEnhancedPlayerInput** + **MappingContext Stack** (Priority + AddMappingContext / RemoveMappingContext) + **UEnhancedInputComponent** BindAction 패턴 + Modular Input 5.x |
| 4 | [`InputCore`](./InputCore/SKILL.md) | `skills/Input/references/InputCore.md` | **InputCore 모듈** — FKey + EKeys 200+ 정의 (A/B/C/SpaceBar/MouseX/Gamepad_LeftThumbstick_X 등) + Touch (Touch1~10) + Gesture (Pinch/Swipe) + Gamepad (Xbox/Playstation/Generic) + 플랫폼별 키 |
| 5 | [`Legacy`](./Legacy/SKILL.md) | `skills/Input/references/Legacy.md` | **UInputComponent + InputDevice 모듈** — Legacy BindAction/BindAxis/BindTouch + Project Settings INI (DefaultInput.ini) + IInputDevice / IInputInterface (RawInput) + **Force Feedback** (UForceFeedbackEffect 자산 + IForceFeedbackInterface) + **Haptic** |

---

## 2. 의존 트리 + 흐름

```
[하드웨어 입력] (Mouse / Keyboard / Gamepad / Touch / VR)
  ↓
SlateApplication (윈도우 시스템 — SlateCore/Input)
  ↓
APlayerController::PlayerInput (UEnhancedPlayerInput 또는 UPlayerInput)
  ↓
[Enhanced Input 활성 시]
UEnhancedInputLocalPlayerSubsystem
  ↓ MappingContext Stack (Priority 별 정렬)
  ↓ Action ↔ Key 매핑 평가
UInputAction → UInputTrigger 평가 → UInputModifier 적용
  ↓ ETriggerEvent (Triggered / Started / etc)
UEnhancedInputComponent::BindAction 콜백
  ↓ FInputActionValue (Bool / Axis1D / Axis2D / Axis3D)
[게임 로직]

[Legacy 활성 시 — 5.x 호환]
UInputComponent::BindAction (Pressed/Released)
  ↓ Project Settings DefaultInput.ini
[게임 로직]
```

---

## 3. Enhanced Input vs Legacy 결정 매트릭스

| 항목 | **Enhanced Input** (5.x 표준) | **Legacy UInputComponent** |
|------|------------------------------|----------------------------|
| 정의 위치 | UInputAction + UInputMappingContext **자산** (`.uasset`) | DefaultInput.ini Project Settings |
| ValueType | Bool / Axis1D / Axis2D / Axis3D | float (1D), bool (Pressed/Released) |
| Trigger | 8종 (Pressed/Released/Hold/Tap/Pulse/Chord/Down/Combo) | 3종 (IE_Pressed / IE_Released / IE_Repeat) |
| Modifier | 9종 (DeadZone/Smooth/Scale/Negate/Swizzle/ResponseCurve 등) | 없음 |
| Mapping Context | **동적 추가/제거 + Priority Stack** | 정적 (INI) |
| LocalPlayer | LocalPlayerSubsystem 으로 매핑 | PlayerController 단일 |
| Device 별 매핑 | IMC 별 분리 (Keyboard / Gamepad / Touch IMC 따로) | 단일 매핑 |
| 권장 | **신규 코드 표준** | 단순 프로토타입 / 마이그레이션 시만 |

> **5.x 신규 게임 = Enhanced Input 의무**. Legacy 는 호환 + 마이그레이션만.

---

## 4. Enhanced Input 표준 셋업 (전체 흐름)

### 4.1 자산 작성 (Editor)

```
1. UInputAction 자산 생성 (예: IA_Move, IA_Jump, IA_Look)
   - ValueType = Axis2D (Move/Look) / Bool (Jump)
   - Trigger / Modifier 추가

2. UInputMappingContext 자산 생성 (예: IMC_Default, IMC_Vehicle)
   - Action ↔ Key 매핑 추가
   - 각 매핑에 Trigger / Modifier 추가
```

### 4.2 PlayerController 측 — IMC 등록

```cpp
// MyPlayerController.cpp
void AMyPlayerController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyPC::OnPossess);

    // LocalPlayerSubsystem 으로 IMC 스택 추가
    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
    {
        Subsystem->AddMappingContext(DefaultMappingContext, /*Priority=*/ 0);
    }
}
```

### 4.3 Pawn 측 — Action 바인딩

```cpp
// MyCharacter.cpp
void AMyCharacter::SetupPlayerInputComponent(UInputComponent* InInputComponent)
{
    Super::SetupPlayerInputComponent(InInputComponent);

    if (auto* EIC = Cast<UEnhancedInputComponent>(InInputComponent))
    {
        EIC->BindAction(MoveAction,  ETriggerEvent::Triggered, this, &AMyCharacter::OnMove);
        EIC->BindAction(LookAction,  ETriggerEvent::Triggered, this, &AMyCharacter::OnLook);
        EIC->BindAction(JumpAction,  ETriggerEvent::Started,   this, &ACharacter::Jump);
        EIC->BindAction(JumpAction,  ETriggerEvent::Completed, this, &ACharacter::StopJumping);
    }
}

void AMyCharacter::OnMove(const FInputActionValue& Value)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::OnMove);
    const FVector2D Axis = Value.Get<FVector2D>();
    AddMovementInput(GetActorForwardVector(), Axis.Y);
    AddMovementInput(GetActorRightVector(), Axis.X);
}
```

### 4.4 동적 IMC 스택 (메뉴 / 차량)

```cpp
// 메뉴 열 때 — 게임 입력 비활성 + 메뉴 입력 활성
void AMyController::OpenMenu()
{
    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
    {
        Subsystem->RemoveMappingContext(DefaultMappingContext);
        Subsystem->AddMappingContext(MenuMappingContext, /*Priority=*/ 100);   // 우선순위 높음
    }
}

// 차량 탑승 — 차량 입력 활성
void AMyCharacter::EnterVehicle()
{
    if (auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
    {
        Subsystem->RemoveMappingContext(DefaultMappingContext);
        Subsystem->AddMappingContext(VehicleMappingContext, /*Priority=*/ 0);
    }
}
```

---

## 5. Build.cs 의존성

```csharp
// MyGame.Build.cs
PublicDependencyModuleNames.AddRange(new string[] {
    "Core", "CoreUObject", "Engine",
    "InputCore",                  // FKey / EKeys (베이스)
    "EnhancedInput",              // 5.x 표준 Plugin
});

// 선택 — 모바일 / VR
PublicDependencyModuleNames.AddRange(new string[] {
    "InputDevice",                // RawInput / Force Feedback
    "HeadMountedDisplay",         // VR Input
});
```

```ini
; 프로젝트 / .uproject — Plugin 활성
{
    "Plugins": [
        { "Name": "EnhancedInput", "Enabled": true }
    ]
}
```

---

## 6. cross-cutting 인덱스

- 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — 모든 InputAction 콜백 첫 줄 스코프
- [`Components/SystemComponents §1`](../Components/references/SystemComponents.md) — UInputComponent 호스트 컴포넌트 (페어 sub-skill)
- [`GameFramework/Controller §3.2-§3.3`](../GameFramework/references/Controller.md) — Input Mode 3종 (UIOnly / GameAndUI / GameOnly) + Input Stack
- [`GameFramework/PawnCharacter §3.2-§3.3`](../GameFramework/references/PawnCharacter.md) — SetupPlayerInputComponent + AddMovementInput
- [`SlateCore/Input`](../SlateCore/references/Input.md) — Slate 입력 (FReply / OnMouseButton — UI 측면)

---

## 7. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | **`[Input]` 카테고리 신설** — 메인 SKILL.md + 5 sub-skill 분할 (EnhancedInput / Action / Subsystem / InputCore / Legacy). 베이스 흐름 + Enhanced vs Legacy 매트릭스 + 표준 셋업 4단 (자산 작성 / PC 측 IMC 등록 / Pawn 측 Action 바인딩 / 동적 IMC 스택) + Build.cs 의존성. EnhancedInput Plugin 분석 (마운트 외 — 5.x 표준 API 기반). InputCore + InputDevice 모듈 (Engine 트리 마운트). |
