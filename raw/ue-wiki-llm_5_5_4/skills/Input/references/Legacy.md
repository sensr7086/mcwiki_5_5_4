---
name: input-legacy
description: UInputComponent (legacy) + InputDevice + Force Feedback 4채널 + Haptic 5.x 4종 - Migration 5단계 (DefaultInput.ini → IMC).
---

# Input/Legacy — UInputComponent (Legacy) + InputDevice (RawInput) + Force Feedback + Haptic

> **위치**: Engine `Components/InputComponent.h` (Legacy InputComponent) + `InputDevice/` 모듈 (IInputDevice / IHapticDevice) + `GameFramework/ForceFeedback*.h` + `Haptics/HapticFeedbackEffect_*.h`
> **베이스**: `UInputComponent : public UActorComponent` / `IInputDevice` / `IHapticDevice`
> **요지**: **Legacy 입력 시스템 + 디바이스 통합 (Force Feedback / Haptic / RawInput)** — 5.x 에서도 호환 + Force Feedback / Haptic 은 Enhanced Input 과 별도 표준.

---

## 🚨 공통 정책

| 정책 | Legacy / InputDevice 적용 |
|------|--------------------------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | BindAction / BindAxis 콜백 첫 줄 스코프 의무. |
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | UForceFeedbackEffect / UHapticFeedbackEffect = 작은 자산 (Hard OK). |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) | UInputComponent = UActorComponent — 6대 정책 적용. |

---

## 1. UInputComponent (Legacy — InputComponent.h:110~)

> **5.x 에서도 호환** — 단순 프로토타입 / 마이그레이션 / 에디터 도구에서만 사용. **신규 게임 = Enhanced Input 의무**.

### 1.1 베이스 + FInputBinding

```cpp
// InputComponent.h:110
struct FInputBinding
{
    uint8 bConsumeInput:1;             // 처리 후 다음 InputComponent 로 안 넘김 (기본 true)
    uint8 bExecuteWhenPaused:1;        // Pause 중 실행 (기본 false)

    FInputBinding()
        : bConsumeInput(true)
        , bExecuteWhenPaused(false) {}
};

class UInputComponent : public UActorComponent
{
    int32 Priority = 0;                 // 입력 처리 순서 (높을수록 먼저)

    // 5종 Binding 배열
    TArray<FInputActionBinding> ActionBindings;
    TArray<FInputKeyBinding> KeyBindings;
    TArray<FInputTouchBinding> TouchBindings;
    TArray<FInputAxisBinding> AxisBindings;
    TArray<FInputAxisKeyBinding> AxisKeyBindings;
    TArray<FInputVectorAxisBinding> VectorAxisBindings;
    TArray<FInputGestureBinding> GestureBindings;
};
```

### 1.2 5종 Binding 시그니처

```cpp
// 1. Action (Pressed / Released — Project Settings INI 참조)
PlayerInputComponent->BindAction(
    /*ActionName=*/ TEXT("Jump"),
    /*KeyEvent=*/ IE_Pressed,
    this,
    &AMyPawn::OnJump
);

// 2. Axis (1D — float 매개변수)
PlayerInputComponent->BindAxis(
    /*AxisName=*/ TEXT("MoveForward"),
    this,
    &AMyPawn::MoveForward
);

void AMyPawn::MoveForward(float Value)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MoveForward);
    AddMovementInput(GetActorForwardVector(), Value);
}

// 3. AxisKey (FKey 직접 — INI 안 거치고)
PlayerInputComponent->BindAxisKey(
    /*Key=*/ EKeys::MouseX,
    this,
    &AMyPawn::Turn
);

// 4. Key (FInputChord — Modifier 키 조합)
PlayerInputComponent->BindKey(
    FInputChord(EKeys::F, /*bShift=*/ false, /*bCtrl=*/ true, false, false),
    IE_Pressed,
    this,
    &AMyPawn::OnCtrlF
);

// 5. Touch
PlayerInputComponent->BindTouch(
    IE_Pressed,
    this,
    &AMyPawn::OnTouchStart
);

void AMyPawn::OnTouchStart(ETouchIndex::Type FingerIndex, FVector Location)
{
    // Touch 위치 처리
}

// 6. Gesture
PlayerInputComponent->BindGesture(
    /*GestureKey=*/ EKeys::Gesture_Pinch,
    this,
    &AMyPawn::OnPinch
);
```

### 1.3 EInputEvent 종류

```cpp
enum EInputEvent
{
    IE_Pressed,        // 눌림 시점
    IE_Released,       // 떨어짐 시점
    IE_Repeat,          // 반복 (OS 키 반복)
    IE_DoubleClick,
    IE_Axis,            // (Axis 전용 — BindAxis 가 자동 처리)
};
```

### 1.4 Project Settings — DefaultInput.ini (Legacy)

```ini
; DefaultInput.ini
[/Script/Engine.InputSettings]

; ActionMapping 정의
+ActionMappings=(ActionName="Jump",Key=SpaceBar,bShift=False,bCtrl=False,bAlt=False)
+ActionMappings=(ActionName="Jump",Key=Gamepad_FaceButton_Bottom)
+ActionMappings=(ActionName="Fire",Key=LeftMouseButton)

; AxisMapping 정의
+AxisMappings=(AxisName="MoveForward",Key=W,Scale=1.0)
+AxisMappings=(AxisName="MoveForward",Key=S,Scale=-1.0)
+AxisMappings=(AxisName="MoveRight",Key=D,Scale=1.0)
+AxisMappings=(AxisName="MoveRight",Key=A,Scale=-1.0)
+AxisMappings=(AxisName="Turn",Key=MouseX,Scale=1.0)
+AxisMappings=(AxisName="LookUp",Key=MouseY,Scale=-1.0)
+AxisMappings=(AxisName="Turn",Key=Gamepad_RightX,Scale=1.0)
+AxisMappings=(AxisName="LookUp",Key=Gamepad_RightY,Scale=-1.0)
```

### 1.5 Priority + Consumption (Stack 처리)

> **여러 InputComponent 스택** — Pawn / PlayerController / 다른 Component 모두 InputComponent 보유 가능.

```cpp
// PlayerController->PushInputComponent(MenuInputComponent);   // Stack 위 — 우선
// PlayerController->PopInputComponent(MenuInputComponent);

// Priority 직접 설정
MenuInputComponent->Priority = 100;                    // 높은 우선순위
PawnInputComponent->Priority = 0;                      // 낮음

// bConsumeInput
ActionBinding.bConsumeInput = true;                     // 처리 후 다음 InputComponent 안 호출
```

> **자세한 Input Stack 패턴 = [`GameFramework/Controller §3.3`](../../GameFramework/references/Controller.md)**.

---

## 2. UForceFeedback (게임패드 진동)

### 2.1 UForceFeedbackEffect 자산

```cpp
// GameFramework/ForceFeedbackEffect.h
class UForceFeedbackEffect : public UObject
{
    UPROPERTY(EditAnywhere)
    TArray<FForceFeedbackChannelDetails> ChannelDetails;
};

struct FForceFeedbackChannelDetails
{
    bool bAffectsLeftLarge;       // L 큰 모터 (저주파)
    bool bAffectsLeftSmall;       // L 작은 모터 (고주파)
    bool bAffectsRightLarge;
    bool bAffectsRightSmall;

    UPROPERTY()
    TObjectPtr<UCurveFloat> Curve;   // 시간 → 강도
};
```

### 2.2 PlayerController 측 재생

```cpp
// PlayerController API
PC->ClientPlayForceFeedback(MyForceFeedbackEffect, /*Looping=*/ false, /*Tag=*/ NAME_None);
PC->ClientStopForceFeedback(MyForceFeedbackEffect, /*Tag=*/ NAME_None);

// 직접 강도 설정
PC->PlayDynamicForceFeedback(
    /*Intensity=*/ 0.8f,
    /*Duration=*/ 0.5f,
    /*bAffectsLeftLarge=*/ true,
    /*bAffectsLeftSmall=*/ true,
    /*bAffectsRightLarge=*/ true,
    /*bAffectsRightSmall=*/ true,
    EDynamicForceFeedbackAction::Start
);
```

### 2.3 UForceFeedbackComponent (3D — 거리 기반)

```cpp
// Components/ForceFeedbackComponent.h — Audio 처럼 3D 위치 기반
auto* FFC = NewObject<UForceFeedbackComponent>(Owner);
FFC->ForceFeedbackEffect = MyEffect;
FFC->bAutoDestroy = true;
FFC->SetWorldLocation(ImpactLocation);
FFC->Activate();

// Attenuation — 거리 기반 강도
UForceFeedbackAttenuation* Attenuation = ...;
FFC->AttenuationSettings = Attenuation;
```

---

## 3. Haptic Feedback (5.x — VR / 게임패드)

> **`Haptics/HapticFeedbackEffect_*`** = 5.x VR / 게임패드 Haptic. ForceFeedback 보다 정밀.

### 3.1 자산 종류 4종

```cpp
// HapticFeedbackEffect_Base.h — 베이스
class UHapticFeedbackEffect_Base : public UObject {};

// HapticFeedbackEffect_Buffer.h — 사전 녹음 데이터
class UHapticFeedbackEffect_Buffer : public UHapticFeedbackEffect_Base
{
    TArray<uint8> Amplitudes;
    int32 SampleRate;
};

// HapticFeedbackEffect_Curve.h — Curve 기반
class UHapticFeedbackEffect_Curve : public UHapticFeedbackEffect_Base
{
    FRichCurve HapticDetails_Amplitude;
    FRichCurve HapticDetails_Frequency;
};

// HapticFeedbackEffect_SoundWave.h — 사운드 파일 기반
class UHapticFeedbackEffect_SoundWave : public UHapticFeedbackEffect_Base
{
    TObjectPtr<USoundWave> SoundWave;
};
```

### 3.2 PlayerController 측 재생 (VR Hand)

```cpp
PC->SetHapticsByValue(
    /*Frequency=*/ 0.5f,
    /*Amplitude=*/ 0.8f,
    /*Hand=*/ EControllerHand::Right
);

PC->PlayHapticEffect(
    HapticEffect,
    EControllerHand::Right,
    /*Scale=*/ 1.0f,
    /*bLoop=*/ false
);

PC->StopHapticEffect(EControllerHand::Right);
```

---

## 4. IInputDevice (커스텀 입력 디바이스 — 5.x 플러그인)

### 4.1 IInputDevice 인터페이스 (InputDevice.h:?)

```cpp
// InputDevice/Public/IInputDevice.h
class IInputDevice
{
public:
    virtual void Tick(float DeltaTime) = 0;           // 매 프레임 입력 풀링
    virtual void SendControllerEvents() = 0;           // SlateApplication 으로 이벤트 전송
    virtual void SetMessageHandler(const TSharedRef<FGenericApplicationMessageHandler>& InMessageHandler) = 0;

    virtual bool Exec(UWorld* InWorld, const TCHAR* Cmd, FOutputDevice& Ar) = 0;

    // Force Feedback
    virtual void SetChannelValue(int32 ControllerId, FForceFeedbackChannelType ChannelType, float Value) = 0;
    virtual void SetChannelValues(int32 ControllerId, const FForceFeedbackValues& Values) = 0;
};

// IInputDeviceModule.h — Plugin 진입점
class IInputDeviceModule : public IModuleInterface
{
public:
    virtual TSharedPtr<class IInputDevice> CreateInputDevice(const TSharedRef<FGenericApplicationMessageHandler>& InMessageHandler) = 0;
};
```

### 4.2 IHapticDevice (Haptic 기능)

```cpp
// InputDevice/Public/IHapticDevice.h
class IHapticDevice
{
public:
    virtual void SetHapticFeedbackValues(int32 ControllerId, int32 Hand, const FHapticFeedbackValues& Values) = 0;
    virtual void GetHapticFrequencyRange(float& MinFrequency, float& MaxFrequency) const = 0;
    virtual float GetHapticAmplitudeScale() const = 0;
};
```

### 4.3 표준 Plugin 종류

> **InputDevice Plugin 예시** — 5.x 표준 / 커뮤니티:
> - **WindowsRawInput** — Raw Input API (다중 마우스 / 키보드)
> - **XInputDevice** — Xbox 컨트롤러
> - **WinDualShock / SCEDualShock** — PS DualShock
> - **OpenXR** — VR 디바이스
> - **OnlineSubsystem** — Steam Input / EOS Input

### 4.4 커스텀 Plugin 작성 (요지)

```cpp
// MyDevicePlugin.cpp
class FMyDeviceModule : public IInputDeviceModule
{
    virtual TSharedPtr<IInputDevice> CreateInputDevice(...) override
    {
        return MakeShared<FMyInputDevice>(InMessageHandler);
    }
};

class FMyInputDevice : public IInputDevice
{
    virtual void Tick(float DeltaTime) override
    {
        // Raw Input 풀링
    }

    virtual void SendControllerEvents() override
    {
        // SlateApplication 에 키 이벤트 전송
        MessageHandler->OnControllerButtonPressed(EKeys::SpaceBar.GetFName(), /*UserId=*/ 0, /*ControllerId=*/ 0);
    }
};
```

---

## 5. Touch / Gesture (모바일)

### 5.1 Touch 핵심 메소드

```cpp
// PlayerController 안 Touch 정보 조회
bool bPressed;
float LocationX, LocationY;
PC->GetInputTouchState(ETouchIndex::Touch1, LocationX, LocationY, bPressed);
PC->IsInputKeyDown(EKeys::Touch1);
PC->WasInputKeyJustPressed(EKeys::Touch1);

// Trace under touch
FHitResult Hit;
PC->GetHitResultUnderFinger(ETouchIndex::Touch1, ECC_Visibility, false, Hit);
```

### 5.2 ETouchIndex (10 손가락 지원)

```cpp
enum class ETouchIndex : uint8
{
    Touch1 = 0,
    Touch2,
    ...
    Touch10,
    CursorPointerIndex,    // 마우스 위치 (Touch 시뮬)
    MAX_TOUCHES = 11,
};
```

### 5.3 Gesture (Pinch / Swipe / Rotate / Flick)

```cpp
// IMC 매핑 (Gesture)
// Gesture_Pinch ↔ IA_Zoom (Axis1D)
// Gesture_Swipe ↔ IA_Swipe (Axis2D)

// 또는 Legacy
PlayerInputComponent->BindGesture(EKeys::Gesture_Pinch, this, &AMyPawn::OnPinch);

void AMyPawn::OnPinch(float Value)
{
    // Value = 핀치 비율 (1.0 = 시작 / >1 = 확대 / <1 = 축소)
    Camera->FieldOfView = FMath::Clamp(Camera->FieldOfView / Value, 30.f, 120.f);
}
```

---

## 6. Migration — Legacy → Enhanced Input

### 6.1 마이그레이션 결정 트리

```
Project = 5.0+ 신규?
├── Yes → 처음부터 Enhanced Input
└── No (4.x 마이그레이션)
    ├── Production 임박? → Legacy 유지 + 부분적 Enhanced (특정 시스템만)
    └── 시간 충분 → 전체 마이그레이션
        1. DefaultPlayerInputClass / DefaultInputComponentClass 변경
        2. ActionMapping → IA_* 자산 + IMC 자산
        3. BindAction / BindAxis → BindAction(IA_, ETriggerEvent::*, ...)
        4. SetupPlayerInputComponent 안 Cast<UEnhancedInputComponent> 가드
```

### 6.2 마이그레이션 단계별

```cpp
// Step 1: DefaultInput.ini 변경
// Before: 자동 = UPlayerInput / UInputComponent
// After:
[/Script/Engine.InputSettings]
DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput
DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent

// Step 2: ActionMapping → IA_* 자산
// Before: +ActionMappings=(ActionName="Jump",Key=SpaceBar)
// After: IA_Jump (자산) + IMC_Default 매핑 (IA_Jump ↔ SpaceBar)

// Step 3: BindAction
// Before:
PlayerInputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &ACharacter::Jump);

// After:
if (auto* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent))
{
    EIC->BindAction(JumpAction, ETriggerEvent::Started, this, &ACharacter::Jump);
    EIC->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);
}

// Step 4: BindAxis (float) → BindAction(Axis2D)
// Before:
PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &AMyPawn::MoveForward);
// After: IA_Move (Axis2D) + OnMove(FInputActionValue&)

// Step 5: 마이그레이션 후 INI 비우기 + Enhanced Input Plugin 활성
```

---

## 7. 함정 & 안티패턴 (8종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 5.x 신규 코드를 BindAction(TEXT("Jump"), ...) Legacy 작성 | Enhanced Input 의무 — IA_Jump 자산 |
| 2 | DefaultPlayerInputClass 안 변경 + Enhanced Input 사용 시도 | DefaultInput.ini 변경 의무 |
| 3 | UInputComponent + UEnhancedInputComponent 동시 사용 (혼합) | DefaultInputComponentClass 단일 결정 — 일관성 유지 |
| 4 | ForceFeedback 매 프레임 호출 | 한 번 + Looping 또는 Duration |
| 5 | Haptic VR 아닌 환경에서 호출 | `IsValid(GEngine->XRSystem)` 가드 |
| 6 | Touch1 만 사용 (멀티터치 안 함) | Touch1~10 — 게임에 따라 멀티 |
| 7 | Gesture 활성 안 하고 BindGesture | Project Settings > Engine > Input > bUseGestures 의무 |
| 8 | 🚨 BindAction 콜백 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |

---

## 8. 체크리스트

- [ ] 5.x 신규 = Enhanced Input 의무 (Legacy 안 사용)
- [ ] 마이그레이션 = DefaultInput.ini → IA_* 자산 → BindAction 순서
- [ ] ForceFeedback = UForceFeedbackEffect 자산 + ClientPlayForceFeedback
- [ ] Haptic VR = SetHapticsByValue + EControllerHand 분리
- [ ] Touch = ETouchIndex 1~10 + GetInputTouchState
- [ ] Gesture = Project Settings 활성 + BindGesture
- [ ] 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] InputDevice Plugin = IInputDevice + IHapticDevice 인터페이스 구현

---

## 9. 관련 sub-skill

- [`Input/SKILL.md`](../SKILL.md) — 메인
- [`Input/EnhancedInput`](../EnhancedInput/SKILL.md) — 5.x 표준 (Legacy 대체)
- [`Input/Action`](../Action/SKILL.md) + [`Input/Subsystem`](../Subsystem/SKILL.md)
- [`Input/InputCore`](../InputCore/SKILL.md) — FKey / EKeys (Legacy 도 사용)
- [`Components/SystemComponents §1`](../../Components/references/SystemComponents.md) — UInputComponent 호스트
- [`GameFramework/Controller §3.2-§3.3`](../../GameFramework/references/Controller.md) — Input Mode + Stack
- [`Components/AudioComponent`](../../Components/references/AudioComponent.md) — UForceFeedbackComponent (Audio 와 같은 패턴)

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UInputComponent (Legacy)** — InputComponent.h 5종 Binding (FInputActionBinding / FInputAxisBinding / FInputTouchBinding / FInputKeyBinding / FInputAxisKeyBinding / FInputVectorAxisBinding / FInputGestureBinding) + EInputEvent 5종 + DefaultInput.ini ActionMappings / AxisMappings + Priority + bConsumeInput + bExecuteWhenPaused. **UForceFeedback** — UForceFeedbackEffect 자산 (4채널 Left/Right Large/Small + Curve) + UForceFeedbackComponent (3D Audio 패턴 + Attenuation) + ClientPlayForceFeedback / PlayDynamicForceFeedback. **Haptic 5.x 4종** (Base/Buffer/Curve/SoundWave) + SetHapticsByValue + PlayHapticEffect + EControllerHand. **InputDevice 모듈** — IInputDevice (Tick / SendControllerEvents / Force Feedback) + IHapticDevice + IInputDeviceModule + 표준 Plugin 종류 (WindowsRawInput / XInputDevice / OpenXR / OnlineSubsystem) + 커스텀 Plugin 작성 패턴. **Touch / Gesture** — ETouchIndex 1~10 + GetInputTouchState + GetHitResultUnderFinger + Gesture (Pinch/Swipe/Rotate/Flick). **Migration Legacy → Enhanced Input 5단계**. 함정 8종 + 8단 체크리스트. |
