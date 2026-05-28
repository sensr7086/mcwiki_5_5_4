---
name: input-action
description: UInputAction (ValueType 4종 - Bool/Axis1D/Axis2D/Axis3D) + ETriggerEvent 7종 (Triggered/Started/Ongoing/Canceled/Completed) + UInputTrigger 8종 + UInputModifier 9종.
---

# Input/Action — UInputAction + ETriggerEvent + UInputTrigger + UInputModifier

> **위치**: `Engine/Plugins/EnhancedInput/Source/EnhancedInput/Public/InputAction.h` + `InputTriggers.h` + `InputModifiers.h` (Plugin)
> **베이스**: `UInputAction : public UDataAsset` / `UInputTrigger : public UObject` / `UInputModifier : public UObject`
> **요지**: **Enhanced Input 의 자산 + 평가 시스템** — InputAction (자산) + Trigger (조건) + Modifier (변환). 매핑된 키 → Modifier 적용 → Trigger 평가 → ETriggerEvent.

---

## 🚨 공통 정책

| 정책 | Action 적용 |
|------|------------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | InputAction 콜백 첫 줄 스코프 의무. |
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | UInputAction = 작은 자산 — Hard Reference OK. UPROPERTY EditDefaultsOnly + BP 지정 표준. |

---

## 1. UInputAction 자산

### 1.1 ValueType (4종)

```cpp
enum class EInputActionValueType : uint8
{
    Boolean,    // 단순 눌림/안눌림 — Jump / Trigger
    Axis1D,     // 1축 float — Throttle / Trigger Pressure
    Axis2D,     // 2축 FVector2D — Move / Look (가장 흔함)
    Axis3D,     // 3축 FVector — VR / 3D Joystick (드물게)
};
```

### 1.2 핵심 필드 (자산 — Editor 에서 설정)

```cpp
class UInputAction : public UDataAsset
{
    UPROPERTY(EditAnywhere)
    EInputActionValueType ValueType;            // Bool / Axis1D / Axis2D / Axis3D

    UPROPERTY(EditAnywhere)
    bool bConsumeInput = true;                  // 처리 후 다음으로 전파 X

    UPROPERTY(EditAnywhere)
    bool bTriggerWhenPaused = false;            // Pause 중 활성

    UPROPERTY(EditAnywhere)
    bool bReserveAllMappings = false;           // 모든 매핑 점유

    // Action 자체에 Trigger / Modifier 추가 (모든 IMC 매핑에 적용)
    UPROPERTY(EditAnywhere, Instanced)
    TArray<TObjectPtr<UInputTrigger>> Triggers;

    UPROPERTY(EditAnywhere, Instanced)
    TArray<TObjectPtr<UInputModifier>> Modifiers;
};
```

### 1.3 FInputActionValue (콜백 매개변수)

```cpp
// 콜백 시그니처
void OnAction(const FInputActionValue& Value);

// ValueType 별 추출
bool BoolValue   = Value.Get<bool>();              // Boolean
float Axis1D     = Value.Get<float>();             // Axis1D
FVector2D Axis2D = Value.Get<FVector2D>();         // Axis2D
FVector Axis3D   = Value.Get<FVector>();           // Axis3D

// Magnitude (절대값)
float Magnitude = Value.GetMagnitude();
```

### 1.4 표준 자산 명명 규칙

```
IA_Move      (Axis2D)        — 캐릭터 이동
IA_Look      (Axis2D)        — 카메라 룩
IA_Jump      (Bool)          — 점프
IA_Crouch    (Bool)          — Crouch 토글
IA_Sprint    (Bool)          — 달리기
IA_Interact  (Bool)          — 상호작용 (E)
IA_Fire      (Bool)          — 발사
IA_Aim       (Bool)          — 조준 (Hold)
IA_Reload    (Bool)          — 재장전
IA_Inventory (Bool)          — 인벤토리 토글
```

---

## 2. ETriggerEvent 7종 (가장 중요)

| Event | 의미 | 호출 빈도 | 표준 사용 |
|-------|------|----------|----------|
| `None` | 비활성 (드물게 — 디버그) | — | (드물게) |
| `Started` | **활성 시작** | 1회 | Jump / Interact (눌림) |
| `Ongoing` | 부분 활성 (Hold 중) | 매 Tick | Hold 진행 표시 |
| `Triggered` | **활성 매 Tick** | **매 프레임** | Move / Look (Axis 연속) |
| `Canceled` | 취소 (Hold 중 떨어짐) | 1회 | 차징 취소 |
| `Completed` | **활성 종료** | 1회 | Jump 떨어짐 / Hold 완료 |

### 2.1 사용 매트릭스

| 입력 종류 | Bind ETriggerEvent | 콜백 |
|----------|-------------------|------|
| Move (Axis2D 연속) | `Triggered` | `OnMove(FInputActionValue)` |
| Look (Axis2D 연속) | `Triggered` | `OnLook(FInputActionValue)` |
| Jump (단발) | `Started` + `Completed` | `Jump()` + `StopJumping()` |
| Crouch (토글) | `Started` | `ToggleCrouch()` |
| Aim (Hold) | `Started` + `Completed` | `StartAim()` + `StopAim()` |
| Charge Attack (Hold N초) | `Triggered` (Hold Trigger 1.0s) + `Canceled` | `Fire()` + `CancelCharge()` |
| Combo (시퀀스) | `Triggered` (Combo Trigger) | `ExecuteCombo()` |

---

## 3. UInputTrigger 8종 (조건)

> **트리거가 활성 조건 결정** — Action 또는 IMC 매핑에 추가. 여러 Trigger AND 조합.

### 3.1 표준 8종

| Trigger | 의미 | 매개변수 |
|---------|------|---------|
| `UInputTriggerPressed` | **눌림 시점 1회** | (없음) |
| `UInputTriggerReleased` | **떨어짐 시점 1회** | (없음) |
| `UInputTriggerDown` | **눌리고 있음 매 Tick** | `ActuationThreshold` (0.5) |
| `UInputTriggerHold` | **N초 유지 후 트리거** | `HoldTimeThreshold` (1.0s) + `bIsOneShot` |
| `UInputTriggerHoldAndRelease` | **N초 유지 후 떨어지면 트리거** | `HoldTimeThreshold` |
| `UInputTriggerTap` | **N초 안 눌렀다 떨어짐** | `TapReleaseTimeThreshold` (0.3s) |
| `UInputTriggerPulse` | **N초마다 트리거** (자동 발사) | `Interval` (0.5s) + `TriggerLimit` |
| `UInputTriggerChord` | **다른 Action 과 함께 눌림** | `ChordAction` (참조) |
| `UInputTriggerCombo` (5.x) | **시퀀스 (예: 위→위→아래→발사)** | `Combo` 배열 |

### 3.2 표준 사용 패턴

```cpp
// Hold (1초 차징 후 발사)
IA_ChargedFire = UInputAction (Bool)
  - Triggers:
    - UInputTriggerHold (HoldTimeThreshold = 1.0s)
  - Modifiers: (없음)

// 콜백
EIC->BindAction(IA_ChargedFire, ETriggerEvent::Triggered, this, &AMyChar::ChargedFire);   // 1초 후
EIC->BindAction(IA_ChargedFire, ETriggerEvent::Canceled,  this, &AMyChar::CancelCharge);  // 1초 전 떨어짐
```

```cpp
// Combo (위 → 위 → 발사 — 가루다 콤보)
IA_GarudaCombo = UInputAction (Bool)
  - Triggers:
    - UInputTriggerCombo
      - Actions: [IA_Up, IA_Up, IA_Fire]   // 3개 시퀀스
      - TimeBetweenInputs: 0.5s
  - Modifiers: (없음)
```

```cpp
// Pulse (자동 발사 — 0.2초마다)
IA_AutoFire = UInputAction (Bool)
  - Triggers:
    - UInputTriggerPulse (Interval = 0.2s, TriggerLimit = 0)
```

```cpp
// Chord (Shift + W → 달리기)
IA_Sprint = UInputAction (Bool)
  - Triggers:
    - UInputTriggerChord (ChordAction = IA_ShiftKey)   // Shift 도 눌려있어야
```

### 3.3 Trigger 결합 (AND)

```cpp
// 여러 Trigger = AND 조건
IA_ChargedShot = UInputAction (Bool)
  - Triggers:
    - UInputTriggerHold (1.0s)
    - UInputTriggerChord (ChordAction = IA_AimDownSights)
  - => 1초 유지 + 조준 중일 때만 트리거
```

---

## 4. UInputModifier 9종 (변환)

> **입력 값 변환** — 매핑된 키의 raw 값 → 게임 로직이 사용할 값. 여러 Modifier = 순차 적용.

### 4.1 표준 9종

| Modifier | 의미 | 매개변수 |
|----------|------|---------|
| `UInputModifierDeadZone` | **데드존 적용** | `LowerThreshold` (0.2) + `UpperThreshold` (1.0) + Type (Radial / Axial) |
| `UInputModifierScale` | **3축 배율** | `Scalar` (FVector) |
| `UInputModifierScalar` | 단일 float 배율 | `Scalar` (float) |
| `UInputModifierNegate` | **부호 반전** | `bX` / `bY` / `bZ` (어떤 축?) |
| `UInputModifierSwizzleAxis` | **축 순서 바꾸기** | `Order` (XY → YX 등) |
| `UInputModifierSmooth` | **부드럽게 (Lag)** | `SmoothingType` |
| `UInputModifierResponseCurveExponential` | **지수 곡선** | `CurveExponent` (FVector) |
| `UInputModifierResponseCurveUser` | **사용자 곡선** | `ResponseCurve` (FRichCurve) |
| `UInputModifierFOVScaling` | **카메라 FOV 따라 회전 속도** | `FOVScale` |

### 4.2 표준 사용 패턴

```cpp
// Move (W/A/S/D → Axis2D)
// W / S 는 Y 축 / A / D 는 X 축
// IMC 매핑:
// - W → IA_Move (Modifier: Swizzle YX) — 키 자체는 1D, Swizzle 로 Axis2D Y 축에 매핑
// - S → IA_Move (Modifier: Negate Y, Swizzle YX)
// - A → IA_Move (Modifier: Negate X)
// - D → IA_Move (Modifier: 없음)

// 또는 더 간단 — Gamepad LeftThumbstick 2D 직접
// - Gamepad_LeftThumbstick_2D → IA_Move (Modifier: DeadZone 0.2)
```

```cpp
// Look (Mouse 2D)
// IMC 매핑:
// - Mouse_2D → IA_Look (Modifier: Scale 0.5 — 감도 조절)
// - Gamepad_RightThumbstick_2D → IA_Look (Modifier: DeadZone 0.2 + Scale 100 + Negate Y for invert)
```

```cpp
// Aim Sensitivity (FOV 줌인 시 자동 감도 감소)
IA_Look = UInputAction (Axis2D)
  - Modifiers (Action 측):
    - UInputModifierFOVScaling (FOVScale = 1.0)
  // → 카메라 FOV 60° = 1.0 / 30° (조준) = 0.5 자동 감도 감소
```

### 4.3 Modifier 순서

```cpp
// Modifier 는 순차 적용 (배열 순서)
IA_Move (Axis2D)
  Modifiers:
    [0] DeadZone (0.2)              // 1단계: 데드존 → 작은 입력 무시
    [1] Scale (1.5, 1.5, 0)          // 2단계: 1.5 배 증가
    [2] ResponseCurveExponential (2)  // 3단계: 지수 곡선 (가속)
    [3] Smooth                        // 4단계: 부드럽게
```

---

## 5. Modifier 위치 (Action vs IMC 매핑 vs Trigger 안)

> **Modifier 추가 위치 3곳**:

| 위치 | 적용 범위 | 사용 케이스 |
|------|---------|----------|
| **Action 자체** (`UInputAction::Modifiers`) | 모든 IMC 매핑에 적용 | 글로벌 — Look 의 FOV Scaling |
| **IMC 매핑 (per-mapping)** | 해당 키 매핑만 | Device 별 — 키보드 / 게임패드 다른 DeadZone |
| **Trigger 안 (per-trigger)** | 해당 Trigger 만 | 드물게 |

### 표준 분리

```
IA_Look (Action)
  Modifiers (Action 측):
    - FOVScaling                   // 모든 Device 공통

IMC_Default (Mapping Context)
  - Mapping: IA_Look ↔ Mouse_2D
    Modifiers (per-mapping):
      - Scale 0.5                   // 마우스 만 감도 조절
  - Mapping: IA_Look ↔ Gamepad_RightThumbstick_2D
    Modifiers (per-mapping):
      - DeadZone 0.2                // 게임패드 만 데드존
      - Scale 100                   // 게임패드 만 더 빠르게
```

---

## 6. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | InputAction ValueType = Bool 인데 `Value.Get<float>()` | ValueType 일치 — Bool = `Get<bool>()`, Axis2D = `Get<FVector2D>()` |
| 2 | Move Action 에 `Started` Trigger 사용 | Move = Axis 연속 — Trigger 없음 + `ETriggerEvent::Triggered` |
| 3 | Jump Action 에 Hold Trigger + `Triggered` | Jump = `Started` (시작) + `Completed` (떨어짐) — Hold 안 씀 |
| 4 | DeadZone 0.0 (게임패드) | 0.15~0.25 표준 — 게임패드 노이즈 회피 |
| 5 | Mouse 입력 에 Smooth 추가 | 마우스 = Raw 빠른 응답. Smooth = 게임패드 만 |
| 6 | FOVScaling 모든 Action 적용 | Look 만 — Move 에 적용 시 이동 속도 변동 |
| 7 | Combo Trigger 의 TimeBetweenInputs 너무 짧음 | 0.3~0.5s 표준 — 너무 짧으면 거의 동시 입력만 인식 |
| 8 | Pulse Trigger 의 Interval 0.0 | 매 Tick 트리거 — `Triggered` 와 동일. Interval > 0 |
| 9 | 🚨 OnAction 콜백 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 10 | `bConsumeInput = false` 인데 다중 IMC 동시 활성 | Action 중복 호출 — Consume 결정 명확히 |

---

## 7. 체크리스트

- [ ] UInputAction ValueType 정확히 (Bool / Axis1D / Axis2D / Axis3D)
- [ ] 표준 자산 명명 (IA_Move / IA_Look / IA_Jump 등)
- [ ] ETriggerEvent 사용 정확히 (Move=Triggered / Jump=Started+Completed)
- [ ] Trigger AND 조합 명확 (Hold + Chord 등)
- [ ] Modifier 위치 분리 (Action 글로벌 / IMC per-mapping / Trigger per-trigger)
- [ ] DeadZone 0.15~0.25 (게임패드)
- [ ] Mouse Sensitivity = Scale per-mapping
- [ ] Look = FOVScaling (Action 측)
- [ ] 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] bTriggerWhenPaused = true (Pause Toggle / 메뉴 Action)

---

## 8. 관련 sub-skill

- [`Input/EnhancedInput`](../EnhancedInput/SKILL.md) — 메인 (5종 핵심)
- [`Input/Subsystem`](../Subsystem/SKILL.md) — IMC Stack + Subsystem
- [`Input/InputCore`](../InputCore/SKILL.md) — FKey / EKeys
- 교차: 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (콜백 스코프)

---

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UInputAction** ValueType 4종 (Bool/Axis1D/Axis2D/Axis3D) + bConsumeInput / bTriggerWhenPaused / bReserveAllMappings + Triggers / Modifiers (Action 측). **FInputActionValue** Get<T> 매개변수 + Magnitude. **표준 자산 명명** (IA_Move/Look/Jump/Crouch/Sprint/Interact/Fire/Aim/Reload). **ETriggerEvent 7종** (None/Started/Ongoing/Triggered/Canceled/Completed) + 사용 매트릭스. **UInputTrigger 8종** (Pressed/Released/Down/Hold/HoldAndRelease/Tap/Pulse/Chord/Combo) + 표준 사용 패턴 + AND 결합. **UInputModifier 9종** (DeadZone/Scale/Scalar/Negate/Swizzle/Smooth/ResponseCurveExp/ResponseCurveUser/FOVScaling) + 순차 적용. **Modifier 위치 3곳** (Action / IMC 매핑 / Trigger 안). 함정 10종 + 10단 체크리스트. |
