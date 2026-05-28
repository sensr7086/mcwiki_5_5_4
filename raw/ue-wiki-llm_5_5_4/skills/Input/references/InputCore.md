---
name: input-inputcore
description: FKey + EKeys 200+ - Mouse/Keyboard/Gamepad/Touch/VR/Gesture/Tilt + Face Button 플랫폼 추상화 (BottomFace/RightFace/LeftFace/TopFace).
---

# Input/InputCore — FKey + EKeys (200+ 키 정의) + Touch + Gamepad + Gesture + VR

> **위치**: `Engine/Source/Runtime/InputCore/Classes/InputCoreTypes.h` (789 lines) + `Public/GenericPlatform/GenericPlatformInput.h` + 플랫폼별 (`Windows/Mac/Linux/Android/iOS`)
> **모듈명**: `InputCore` (Tier 1 — Core 의존성)
> **요지**: **모든 키 정의의 베이스** — FKey 구조 + EKeys 200+ 정적 멤버. Enhanced Input / Legacy InputComponent / Slate 모두 FKey 사용. 플랫폼별 키 매핑 + Touch + Gesture + VR 통합.

---

## 🚨 공통 정책

| 정책 | InputCore 적용 |
|------|---------------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | (InputCore 자체는 데이터 정의 — 콜백 없음) |
| 🎯 어셋 | FKey = struct (자산 X) — UPROPERTY EditAnywhere 으로 BP 노출 가능 (단축키 설정 자산). |

---

## 1. FKey 구조 (InputCoreTypes.h:108~)

### 1.1 핵심 정의

```cpp
USTRUCT(BlueprintType)
struct INPUTCORE_API FKey
{
    GENERATED_USTRUCT_BODY()

    FKey() = default;
    FKey(const FName InName) : KeyName(InName) {}
    FKey(const TCHAR* InName) : KeyName(FName(InName)) {}

    bool IsValid() const;
    bool IsAnalog() const;                      // Mouse / Thumbstick / Trigger 등
    bool IsDigital() const;                     // Keyboard / Button
    bool IsAxis1D() const;                      // 1D Axis (Throttle / Trigger)
    bool IsAxis2D() const;                      // 2D Axis (Mouse / Thumbstick)
    bool IsAxis3D() const;                      // 3D (Tilt / Gyro)
    bool IsButtonAxis() const;                  // 가짜 Axis (KEY = +1 / -1)
    bool IsTouch() const;                       // Touch1~10
    bool IsMouseButton() const;
    bool IsModifierKey() const;                 // Shift / Ctrl / Alt
    bool IsGamepadKey() const;
    bool IsGesture() const;                     // Pinch / Swipe

    FName GetFName() const { return KeyName; }
    FText GetDisplayName(bool bLongDisplayName = true) const;

private:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Input")
    FName KeyName;

    mutable TSharedPtr<struct FKeyDetails> KeyDetails;   // 캐시
};
```

### 1.2 FKeyDetails (메타 정보)

```cpp
// InputCoreTypes.h:145
struct FKeyDetails
{
    FKey Key;
    TAttribute<FText> LongDisplayName;       // "Space Bar"
    TAttribute<FText> ShortDisplayName;      // "Space"
    uint32 KeyFlags;                          // Axis1D / Axis2D / Touch / Gesture / Modifier 등
    FName MenuCategory;                       // 단축키 메뉴 카테고리

    enum EKeyFlags
    {
        GamepadKey      = 0x00000001,
        Touch           = 0x00000002,
        MouseButton     = 0x00000004,
        ModifierKey     = 0x00000008,
        NotBlueprintBindableKey = 0x00000010,
        Axis1D          = 0x00000020,
        Axis2D          = 0x00000040,
        Axis3D          = 0x00000080,
        UpdateAxisWithoutSamples = 0x00000100,
        NotActionBindableKey     = 0x00000200,
        Deprecated      = 0x00000400,
        ButtonAxis      = 0x00000800,         // 키보드의 W = +1, S = -1 처럼 가짜 Axis
        Audio           = 0x00001000,
        Vision          = 0x00002000,
        Gesture         = 0x00004000,
    };
};
```

---

## 2. EKeys — 200+ 정적 키 인스턴스

> **`InputCoreTypes.h`** 안에 정의된 모든 표준 키. `EKeys::SpaceBar` 형식 사용.

### 2.1 Mouse (5종 + Axis 6종)

```cpp
// InputCoreTypes.h:293~
static INPUTCORE_API const FKey MouseX;            // 1D Axis
static INPUTCORE_API const FKey MouseY;            // 1D Axis
static INPUTCORE_API const FKey Mouse2D;           // 2D Axis (5.x)
static INPUTCORE_API const FKey MouseScrollUp;
static INPUTCORE_API const FKey MouseScrollDown;
static INPUTCORE_API const FKey MouseWheelAxis;    // 1D Axis

static INPUTCORE_API const FKey LeftMouseButton;
static INPUTCORE_API const FKey RightMouseButton;
static INPUTCORE_API const FKey MiddleMouseButton;
static INPUTCORE_API const FKey ThumbMouseButton;
static INPUTCORE_API const FKey ThumbMouseButton2;
```

### 2.2 Keyboard — Special (15+종)

```cpp
// InputCoreTypes.h:306~
static INPUTCORE_API const FKey BackSpace;
static INPUTCORE_API const FKey Tab;
static INPUTCORE_API const FKey Enter;
static INPUTCORE_API const FKey Pause;
static INPUTCORE_API const FKey CapsLock;
static INPUTCORE_API const FKey Escape;
static INPUTCORE_API const FKey SpaceBar;
static INPUTCORE_API const FKey PageUp;
static INPUTCORE_API const FKey PageDown;
static INPUTCORE_API const FKey End;
static INPUTCORE_API const FKey Home;

// 방향키
static INPUTCORE_API const FKey Left;
static INPUTCORE_API const FKey Up;
static INPUTCORE_API const FKey Right;
static INPUTCORE_API const FKey Down;

// 편집
static INPUTCORE_API const FKey Insert;
static INPUTCORE_API const FKey Delete;
```

### 2.3 Keyboard — Letters / Numbers / Numpad / Function

```cpp
// 숫자 (0~9)
static INPUTCORE_API const FKey Zero;
static INPUTCORE_API const FKey One; ... Nine;

// 알파벳 (A~Z)
static INPUTCORE_API const FKey A;  ... Z;

// Numpad (NumPadZero ~ NumPadNine + NumPad 연산)
static INPUTCORE_API const FKey NumPadZero; ... NumPadNine;
static INPUTCORE_API const FKey Multiply / Add / Subtract / Decimal / Divide;

// Function (F1~F12)
static INPUTCORE_API const FKey F1; ... F12;

// Lock / Modifier
static INPUTCORE_API const FKey NumLock / ScrollLock;
static INPUTCORE_API const FKey LeftShift / RightShift;
static INPUTCORE_API const FKey LeftControl / RightControl;
static INPUTCORE_API const FKey LeftAlt / RightAlt;
static INPUTCORE_API const FKey LeftCommand / RightCommand;   // Mac
```

### 2.4 Gamepad (Xbox / PlayStation 표준 — 30+종)

```cpp
// InputCoreTypes.h:450~
// Trigger Axis (1D)
static INPUTCORE_API const FKey Gamepad_LeftTriggerAxis;     // 0~1
static INPUTCORE_API const FKey Gamepad_RightTriggerAxis;

// Thumbstick Axis
static INPUTCORE_API const FKey Gamepad_LeftX;               // 1D
static INPUTCORE_API const FKey Gamepad_LeftY;
static INPUTCORE_API const FKey Gamepad_LeftThumbstick;       // 2D Axis (5.x 권장)
static INPUTCORE_API const FKey Gamepad_RightX;
static INPUTCORE_API const FKey Gamepad_RightY;
static INPUTCORE_API const FKey Gamepad_RightThumbstick;      // 2D Axis (5.x 권장)

// Face Buttons (Xbox: A/B/X/Y / PS: ✕/○/□/△)
static INPUTCORE_API const FKey Gamepad_FaceButton_Bottom;    // Xbox A / PS ✕
static INPUTCORE_API const FKey Gamepad_FaceButton_Right;     // Xbox B / PS ○
static INPUTCORE_API const FKey Gamepad_FaceButton_Left;      // Xbox X / PS □
static INPUTCORE_API const FKey Gamepad_FaceButton_Top;       // Xbox Y / PS △

// Shoulder + Trigger
static INPUTCORE_API const FKey Gamepad_LeftShoulder;          // LB / L1
static INPUTCORE_API const FKey Gamepad_RightShoulder;         // RB / R1
static INPUTCORE_API const FKey Gamepad_LeftTrigger;           // Digital LT / L2
static INPUTCORE_API const FKey Gamepad_RightTrigger;          // Digital RT / R2

// Special
static INPUTCORE_API const FKey Gamepad_Special_Left;          // Back / Share
static INPUTCORE_API const FKey Gamepad_Special_Right;         // Start / Options
static INPUTCORE_API const FKey Gamepad_LeftThumbstick_Click;  // L3
static INPUTCORE_API const FKey Gamepad_RightThumbstick_Click; // R3

// D-Pad
static INPUTCORE_API const FKey Gamepad_DPad_Up;
static INPUTCORE_API const FKey Gamepad_DPad_Down;
static INPUTCORE_API const FKey Gamepad_DPad_Left;
static INPUTCORE_API const FKey Gamepad_DPad_Right;
```

> **Face Button 추상화 — 플랫폼별 자동 매핑**:
> - Xbox: FaceButton_Bottom = A
> - PS: FaceButton_Bottom = ✕
> - Switch (Pro): FaceButton_Bottom = B (위치 다름!)
>
> 항상 **추상 이름** 사용 (Bottom / Right / Left / Top) — `Gamepad_A` 같은 직접 사용 금지.

### 2.5 Touch (Touch1~10 — 멀티터치)

```cpp
// InputCoreTypes.h:255~
enum class EKeys
{
    Touch1 = 1,
    Touch2,
    ...
    Touch10,    // 최대 10 손가락
};

static INPUTCORE_API const FKey Touch1;
static INPUTCORE_API const FKey Touch2;
... Touch10;
```

```cpp
// 사용 — 모바일
EIC->BindAction(IA_Touch, ETriggerEvent::Started, this, &AMyChar::OnTouchStart);

void AMyChar::OnTouchStart(const FInputActionValue& Value)
{
    // FInputActionValue 안 Touch 위치 (FVector2D)
    FVector2D TouchLoc = Value.Get<FVector2D>();
}
```

### 2.6 Tilt / Gyro (모바일 / VR)

```cpp
// InputCoreTypes.h:485~
static INPUTCORE_API const FKey Tilt;             // 가속도계 (모바일 Tilt)
static INPUTCORE_API const FKey Gyro;             // 자이로 (모바일 / VR)
static INPUTCORE_API const FKey Acceleration;     // 가속도 벡터
static INPUTCORE_API const FKey RotationRate;     // 회전 속도
```

### 2.7 Gesture (모바일 — Pinch / Swipe / Rotate / Flick)

```cpp
// InputCoreTypes.h:491~
static INPUTCORE_API const FKey Gesture_Pinch;     // 두 손가락 핀치 (Zoom)
static INPUTCORE_API const FKey Gesture_Flick;     // 빠른 스와이프
static INPUTCORE_API const FKey Gesture_Rotate;
static INPUTCORE_API const FKey Gesture_Swipe;
```

### 2.8 VR — Steam / Vive / Oculus / Daydream

```cpp
// Steam Controller
static INPUTCORE_API const FKey Steam_Touch_0; ... Steam_Touch_3;
static INPUTCORE_API const FKey Steam_Back_Left / Back_Right;

// HTC Vive (`InputCoreTypes.h:516~`)
static INPUTCORE_API const FKey Vive_Left_Grip_Click;
static INPUTCORE_API const FKey Vive_Left_Menu_Click;
static INPUTCORE_API const FKey Vive_Left_Trigger_Click;
... Vive_Right_*

// Oculus Touch
static INPUTCORE_API const FKey OculusTouch_Left_Grip_Click;
... OculusTouch_Right_*

// Daydream / Mixed Reality
static INPUTCORE_API const FKey Daydream_*;
static INPUTCORE_API const FKey MixedReality_*;
```

> **VR Input 5.x 표준 — OpenXR + Enhanced Input 통합**. 플랫폼 별 VR Input Mapping Context 분리.

### 2.9 EControllerHand (VR)

```cpp
// InputCoreTypes.h:16
enum class EControllerHand : uint8
{
    Left,
    Right,
    AnyHand,
    Pad,
    ExternalCamera,
    Gun,
    HMD,
    Special_1, Special_2, Special_3, Special_4, Special_5, Special_6, Special_7, Special_8, Special_9, Special_10, Special_11,
};
```

---

## 3. 키 검색 / 캐싱

### 3.1 EKeys::GetSupportedKeys

```cpp
// 모든 등록 키 조회
TArray<FKey> AllKeys;
EKeys::GetSupportedKeys(AllKeys);
// 200+ 키 — Mouse / Keyboard / Gamepad / Touch / VR / Gesture
```

### 3.2 EKeys::GetKeyDetails

```cpp
// 키 상세 정보
TSharedPtr<FKeyDetails> Details = EKeys::GetKeyDetails(EKeys::SpaceBar);
FText DisplayName = Details->GetDisplayName();    // "Space Bar"

// FKey::GetDisplayName 으로도
FText Display = EKeys::SpaceBar.GetDisplayName();
```

### 3.3 키 카테고리별 필터

```cpp
// 게임패드 키만
TArray<FKey> GamepadKeys;
for (const FKey& Key : AllKeys)
{
    if (Key.IsGamepadKey())
    {
        GamepadKeys.Add(Key);
    }
}

// Axis 키만
for (const FKey& Key : AllKeys)
{
    if (Key.IsAxis2D())
    {
        // Mouse2D / Gamepad_LeftThumbstick / Gamepad_RightThumbstick
    }
}
```

---

## 4. 플랫폼별 키 매핑

### 4.1 GenericPlatformInput

```cpp
// InputCore/Public/GenericPlatform/GenericPlatformInput.h
class FGenericPlatformInput
{
    static FKey GetGamepadAcceptKey();     // Xbox A / PS ✕ / Switch B
    static FKey GetGamepadCancelKey();
    static FKey GetGamepadHomeKey();
};

// 플랫폼별 자식 — Windows / Mac / Linux / Android / iOS
```

### 4.2 표준 사용 — Accept / Cancel 추상화

```cpp
// 메뉴 OK / Cancel — 플랫폼별 자동
FKey AcceptKey = FPlatformInput::GetGamepadAcceptKey();
FKey CancelKey = FPlatformInput::GetGamepadCancelKey();
```

---

## 5. AnyKey (모든 키 트리거)

```cpp
// InputCoreTypes.h:291
static INPUTCORE_API const FKey AnyKey;

// 사용 — 모든 키 입력 시 트리거 (Press Any Key 화면)
EIC->BindAction(IA_AnyKey, ETriggerEvent::Started, this, &AMyChar::OnAnyKey);

// IMC 매핑
// IA_AnyKey ↔ AnyKey
```

---

## 6. ButtonAxis (키보드 가짜 Axis)

> **W/A/S/D 같은 키보드 키를 Axis 처럼** — `+1` / `-1` 매핑.

```cpp
// IMC 매핑 (IA_MoveForward Axis1D)
// W ↔ IA_MoveForward (Modifier: 없음)              // +1
// S ↔ IA_MoveForward (Modifier: Negate (X))         // -1
// → IA_MoveForward 가 -1 ~ +1 Axis1D 값 가짐

// 또는 Axis2D
// W ↔ IA_Move (Modifier: Swizzle XY → YX)            // (0, +1)
// S ↔ IA_Move (Modifier: Swizzle YX, Negate Y)      // (0, -1)
// A ↔ IA_Move (Modifier: Negate X)                    // (-1, 0)
// D ↔ IA_Move (Modifier: 없음)                         // (+1, 0)
```

---

## 7. 함정 & 안티패턴 (8종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | `Gamepad_A` / `Gamepad_X` 직접 사용 | 추상 — `Gamepad_FaceButton_Bottom/Right/Left/Top` |
| 2 | Mouse2D 안 쓰고 MouseX + MouseY 별도 | Mouse2D (5.x) 권장 — 한 매핑으로 처리 |
| 3 | Gamepad_LeftThumbstick (2D) 안 쓰고 LeftX + LeftY | LeftThumbstick (2D) 권장 |
| 4 | DeadZone 없이 Gamepad Axis | DeadZone 0.15~0.25 의무 |
| 5 | VR 키 플랫폼 분리 안 함 | OpenXR + 플랫폼별 IMC (Vive_* / OculusTouch_* / Daydream_*) |
| 6 | 모바일 Tilt / Gyro 비활성 검사 안 함 | Project Settings 에서 활성 + 디바이스 검사 |
| 7 | Touch1 의 Pressed 만 처리 (Drag 안 함) | Touch1 Triggered 추가 — Drag 시 매 프레임 |
| 8 | Accept Key 플랫폼별 분기 안 함 | `FPlatformInput::GetGamepadAcceptKey()` 사용 |

---

## 8. 체크리스트

- [ ] 게임패드 = 추상 이름 (FaceButton_Bottom 등) 사용
- [ ] Mouse / Gamepad Axis = 2D 변형 (Mouse2D / LeftThumbstick) 사용
- [ ] Gamepad Axis = DeadZone Modifier 의무
- [ ] VR = 플랫폼 별 IMC 분리 (Vive / Oculus / Daydream)
- [ ] 모바일 Tilt / Gyro / Touch / Gesture 활성 검사
- [ ] Accept / Cancel = `FPlatformInput::GetGamepadAcceptKey()` 추상화
- [ ] 사용자 키 매핑 = `EKeys::GetSupportedKeys` 로 모든 키 목록

---

## 9. 관련 sub-skill

- [`Input/SKILL.md`](../SKILL.md) — 메인
- [`Input/EnhancedInput`](../EnhancedInput/SKILL.md) — IMC 의 Key 필드 = FKey
- [`Input/Action`](../Action/SKILL.md) — UInputAction (Modifier 가 FKey 값 변환)
- [`Input/Subsystem`](../Subsystem/SKILL.md) — UEnhancedInputLocalPlayerSubsystem
- [`Input/Legacy`](../Legacy/SKILL.md) — UInputComponent BindKey (Legacy 직접 키 바인딩)
- [`SlateCore/Input`](../../SlateCore/references/Input.md) — Slate 측 키 처리 (FReply / OnKeyDown)

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **InputCoreTypes.h 789 lines** 분석. **FKey 구조** (KeyName + KeyDetails 캐시 + IsAnalog/Digital/Axis1D/2D/3D/ButtonAxis/Touch/MouseButton/ModifierKey/GamepadKey/Gesture). **FKeyDetails** EKeyFlags 13종 + LongDisplayName / ShortDisplayName / MenuCategory. **EKeys 200+ 정적 멤버** (Mouse 11종 + Keyboard Special 17종 + Letters/Numbers/Numpad/Function 약 80종 + Gamepad 30+종 + Touch1~10 + Tilt/Gyro/Acceleration/RotationRate + Gesture 4종 + VR Vive/Oculus/Daydream/MixedReality + EControllerHand 11종). **Face Button 플랫폼별 추상화** (Bottom/Right/Left/Top — Xbox A/B/X/Y vs PS ✕/○/□/△). **AnyKey** + **ButtonAxis (키보드 가짜 Axis)** + **GenericPlatformInput** GetGamepadAcceptKey/CancelKey/HomeKey. 함정 8종 + 7단 체크리스트. |
