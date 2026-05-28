---
name: input-subsystem
description: UEnhancedInputLocalPlayerSubsystem + IMC Stack (Priority 7단계) + UEnhancedPlayerInput + UEnhancedInputComponent + Modular 5.x.
---

# Input/Subsystem — UEnhancedInputLocalPlayerSubsystem + UEnhancedPlayerInput + UEnhancedInputComponent + IMC Stack

> **위치**: `Engine/Plugins/EnhancedInput/Source/EnhancedInput/Public/EnhancedInputSubsystems.h` + `EnhancedPlayerInput.h` + `EnhancedInputComponent.h` (Plugin)
> **베이스**: `UEnhancedInputLocalPlayerSubsystem : public UEnhancedInputSubsystemInterface, public ULocalPlayerSubsystem` / `UEnhancedPlayerInput : public UPlayerInput` / `UEnhancedInputComponent : public UInputComponent`
> **요지**: **Enhanced Input 의 런타임 시스템** — Subsystem 이 IMC Stack 관리 + PlayerInput 이 키 → Action 평가 + InputComponent 가 콜백 등록.

---

## 🚨 공통 정책

| 정책 | Subsystem 적용 |
|------|---------------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | EnhancedInputComponent BindAction 콜백 + AddMappingContext / RemoveMappingContext 호출 시점 첫 줄 스코프. |
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | UInputMappingContext = 작은 자산 — Hard Reference OK. PlayerController UPROPERTY 표준. |
| 🚨 [`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md) | Subsystem 으로 IMC 검색 — `TObjectIterator<UInputMappingContext>` 절대 금지. |

---

## 1. UEnhancedInputLocalPlayerSubsystem (가장 중요)

### 1.1 베이스 + 진입점

```cpp
// EnhancedInputSubsystems.h
class UEnhancedInputLocalPlayerSubsystem : public UEnhancedInputSubsystemInterface,
                                            public ULocalPlayerSubsystem
{
    // ULocalPlayerSubsystem — LocalPlayer 별 1개 (Couch Co-op 시 Player1/2 따로)
};

// 표준 진입점
UEnhancedInputLocalPlayerSubsystem* Subsystem =
    ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer());

// PlayerController 안
UEnhancedInputLocalPlayerSubsystem* Subsystem =
    ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer());
```

> **🔑 LocalPlayer 별 Subsystem** — Couch Co-op 시 Player1 = Keyboard / Player2 = Gamepad 분리 가능.

### 1.2 IMC Stack API (가장 흔함)

```cpp
// IMC 추가 — Priority 높을수록 먼저 평가
Subsystem->AddMappingContext(IMC, /*Priority=*/ 0, FModifyContextOptions());

// IMC 제거
Subsystem->RemoveMappingContext(IMC, FModifyContextOptions());

// 모든 IMC 제거
Subsystem->ClearAllMappings();

// IMC 가 활성 중인지 검사
bool bIsActive = Subsystem->HasMappingContext(IMC);

// 활성 IMC 목록 (Priority 정렬)
TArray<FEnhancedInputActionEventBinding> Bindings;
Subsystem->GetAllPlayerMappingsToKey(Key, Bindings);
```

### 1.3 FModifyContextOptions (5.x)

```cpp
struct FModifyContextOptions
{
    bool bIgnoreAllPressedKeysUntilRelease = true;   // 모든 눌린 키 release 까지 무시
    bool bForceImmediately = false;                   // 즉시 적용 (다음 Tick 안 기다림)
    bool bNotifyUserSettings = false;
};

// 사용
FModifyContextOptions Opts;
Opts.bForceImmediately = true;
Subsystem->AddMappingContext(IMC, 0, Opts);
```

### 1.4 Player Mappable Key (5.x — 사용자 설정)

```cpp
// 사용자가 키 매핑 변경 가능 (Settings 메뉴)
UEnhancedInputUserSettings* Settings = Subsystem->GetUserSettings();

// 키 매핑 변경
Settings->RegisterInputMappingContext(IMC);
Settings->ApplySettings();
Settings->SaveSettings();

// 5.x — Player Mappable Key 표준 (deprecated)
// FPlayerMappableKeyOptions / IsMappingPlayerMappable
```

---

## 2. IMC Stack 우선순위 매트릭스 (실전)

### 2.1 표준 우선순위 분류

| Priority | IMC | 활성 시점 | 사용 |
|---------|-----|---------|------|
| **200** | `IMC_System` | 항상 | 시스템 단축키 (Alt+F4 / Console) |
| **150** | `IMC_Modal` | 모달 윈도우 (Pause / Settings) | 모달 입력만 |
| **100** | `IMC_Menu` | 메뉴 열림 | UI 네비게이션 |
| **50** | `IMC_Dialog` | 대화창 | Skip / Choice |
| **20** | `IMC_Vehicle` | 차량 탑승 | 운전 입력 |
| **10** | `IMC_FirstPerson` / `IMC_ThirdPerson` | 카메라 모드 | 시점별 입력 |
| **0** | `IMC_Default` | 기본 게임 | Move / Look / Jump |

### 2.2 동시 활성 패턴

```cpp
// 메뉴 + 게임 동시 활성 — 공통 입력 살리기
// 1. IMC_Default (Priority 0) — Move / Look / Jump / Interact
// 2. IMC_Menu    (Priority 100) — UI Navigation / Cancel / Confirm

// 메뉴 열림 시 — IMC_Default 유지 + IMC_Menu 추가
// → IMC_Menu 가 매핑 안 한 키만 IMC_Default 로 전파 (bConsumeInput 따라)

void OpenInventoryMenu()
{
    auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer());
    Subsystem->AddMappingContext(IMC_Inventory, /*Priority=*/ 100);
    // IMC_Default 는 그대로 — Move 등 게임 입력 유지
}

void CloseInventoryMenu()
{
    Subsystem->RemoveMappingContext(IMC_Inventory);
}
```

### 2.3 Modal — 게임 완전 차단

```cpp
void OpenPauseMenu()
{
    auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer());

    // 1. 모든 IMC 제거 (IMC_Default 등)
    Subsystem->RemoveMappingContext(IMC_Default);

    // 2. Pause 메뉴 IMC 만 활성
    Subsystem->AddMappingContext(IMC_Pause, /*Priority=*/ 150);

    // 3. Pause Action 은 bTriggerWhenPaused = true
    UGameplayStatics::SetGamePaused(this, true);
}
```

---

## 3. UInputMappingContext (자산)

### 3.1 핵심 구조

```cpp
class UInputMappingContext : public UDataAsset
{
    // Action ↔ Key 매핑 배열
    UPROPERTY(EditAnywhere, Category="Mappings")
    TArray<FEnhancedActionKeyMapping> Mappings;
};

struct FEnhancedActionKeyMapping
{
    UPROPERTY(EditAnywhere)
    TObjectPtr<const UInputAction> Action;       // 어떤 Action?

    UPROPERTY(EditAnywhere)
    FKey Key;                                     // 어떤 Key? (FKey — InputCore)

    // per-mapping Trigger / Modifier (Action 측 외 추가)
    UPROPERTY(EditAnywhere, Instanced)
    TArray<TObjectPtr<UInputTrigger>> Triggers;

    UPROPERTY(EditAnywhere, Instanced)
    TArray<TObjectPtr<UInputModifier>> Modifiers;

    UPROPERTY(EditAnywhere)
    bool bIsPlayerMappable;                       // 5.x — 사용자 키 매핑 가능
};
```

### 3.2 Editor 작성 패턴

```
IMC_Default (자산 — 디자이너 작성)
├── Mapping 1: IA_Move ↔ W
│     - Triggers: (없음)
│     - Modifiers: Swizzle (XY), Negate (X — W 가 -Y 매핑이라)
├── Mapping 2: IA_Move ↔ S
│     - Modifiers: Swizzle (XY), Negate (Y)
├── Mapping 3: IA_Move ↔ A
│     - Modifiers: Negate (X)
├── Mapping 4: IA_Move ↔ D
│     - Modifiers: (없음)
├── Mapping 5: IA_Move ↔ Gamepad_LeftThumbstick_2D
│     - Modifiers: DeadZone (0.2)
├── Mapping 6: IA_Look ↔ Mouse_2D
│     - Modifiers: Scale (0.5, 0.5, 0)
└── Mapping 7: IA_Jump ↔ SpaceBar / Gamepad_FaceButton_Bottom
```

> **Modifier 위치 — IMC per-mapping**: Device 별 (Mouse / Gamepad / Keyboard) 다른 감도 / DeadZone.

---

## 4. UEnhancedPlayerInput

### 4.1 베이스 + DefaultEngine.ini 등록

```cpp
// EnhancedPlayerInput.h
class UEnhancedPlayerInput : public UPlayerInput
{
    // 매 프레임 ProcessInputStack 안 호출 — IMC Stack 평가
    virtual void EvaluateInputDelegates(...) override;

    // Action 평가 결과
    TMap<TObjectPtr<const UInputAction>, FInputActionInstance> ActionInstanceData;
};
```

```ini
; DefaultInput.ini — Enhanced Input 활성 (가장 중요)
[/Script/Engine.InputSettings]
DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput
DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent
```

> **위 두 줄 없으면 Enhanced Input 동작 안 함** — 5.x 신규 프로젝트는 자동 설정. 마이그레이션 시 의무.

### 4.2 FInputActionInstance

```cpp
// 현재 Action 의 평가 상태
struct FInputActionInstance
{
    FInputActionValue Value;                     // 현재 값
    ETriggerEvent TriggerEvent;                   // 현재 Event
    TArray<TObjectPtr<UInputTrigger>> Triggers;
    TArray<TObjectPtr<UInputModifier>> Modifiers;

    // 시간 정보
    float TriggeredTime = 0.f;                    // 트리거된 시간
    float LastTriggeredWorldTime = 0.f;
    float ElapsedProcessedTime = 0.f;             // 활성 시간 (Hold 진행)
};
```

### 4.3 런타임 Action 상태 조회

```cpp
// PlayerController 또는 Pawn 에서
auto* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer());
FInputActionValue Value = Subsystem->GetActionValue(IA_Move);   // 현재 Move 값

// Hold 진행 시간 (charging UI)
FInputActionInstance Instance = Subsystem->GetActionInstanceData(IA_ChargedFire);
float HoldTime = Instance.ElapsedProcessedTime;   // 0~1.0s
```

---

## 5. UEnhancedInputComponent (Pawn / PlayerController 측)

### 5.1 BindAction 4종 시그니처

```cpp
class UEnhancedInputComponent : public UInputComponent
{
    // 1. UFunction (UObject)
    template<class UserClass, typename FuncType>
    FInputBindingHandle& BindAction(const UInputAction* Action, ETriggerEvent EventType,
                                     UserClass* Object, FuncType Func);

    // 2. 매개변수 없음
    // EIC->BindAction(IA_Jump, ETriggerEvent::Started, this, &ACharacter::Jump);

    // 3. FInputActionValue 매개변수
    // EIC->BindAction(IA_Move, ETriggerEvent::Triggered, this, &AMyChar::OnMove);
    // void OnMove(const FInputActionValue& Value);

    // 4. FInputActionInstance 매개변수 (Hold 진행 시간 등)
    // EIC->BindAction(IA_ChargedFire, ETriggerEvent::Triggered, this, &AMyChar::OnCharge);
    // void OnCharge(const FInputActionInstance& Instance);
};
```

### 5.2 매개변수 패턴 표준

```cpp
// 패턴 1 — 매개변수 없음 (Started / Completed)
void AMyCharacter::OnJump()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::OnJump);
    Jump();
}

// 패턴 2 — FInputActionValue (Axis 입력)
void AMyCharacter::OnMove(const FInputActionValue& Value)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::OnMove);
    const FVector2D Axis = Value.Get<FVector2D>();
    AddMovementInput(GetActorForwardVector(), Axis.Y);
    AddMovementInput(GetActorRightVector(), Axis.X);
}

// 패턴 3 — FInputActionInstance (Hold 진행 / 시간 정보)
void AMyCharacter::OnChargingFire(const FInputActionInstance& Instance)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCharacter::OnChargingFire);
    float ChargeRatio = FMath::Clamp(Instance.ElapsedProcessedTime / 1.0f, 0.f, 1.f);
    UpdateChargeUI(ChargeRatio);
}
```

### 5.3 BindActionValue (raw 키 값 — Modifier 적용 전)

```cpp
// 5.x — raw 키 값 직접 바인딩 (드물게)
EIC->BindActionValue(IA_Move);   // Modifier 적용 전 raw 값
```

---

## 6. Modular Input (5.x — 컴포넌트 분리)

### 6.1 PlayerControllerComponent / PawnComponent 패턴

> **5.x — Lyra 같은 모듈러 게임** — Input 처리를 Component 로 분리하여 재사용.

```cpp
// MyInputComponent.h — Pawn 의 Input 처리 분리
UCLASS()
class UMyInputHandlerComponent : public UPawnComponent
{
    GENERATED_BODY()
public:
    void SetupInput(UEnhancedInputComponent* EIC, AMyCharacter* Owner);
};

void UMyInputHandlerComponent::SetupInput(UEnhancedInputComponent* EIC, AMyCharacter* Owner)
{
    EIC->BindAction(MoveAction, ETriggerEvent::Triggered, Owner, &AMyCharacter::OnMove);
    // ... 모든 바인딩
}

// AMyCharacter::SetupPlayerInputComponent 안
auto* InputHandler = FindComponentByClass<UMyInputHandlerComponent>();
InputHandler->SetupInput(Cast<UEnhancedInputComponent>(InInputComponent), this);
```

### 6.2 Lyra 패턴 — UAbilityInputBindingComponent

> **GAS 와 통합 — Ability 별 Input 바인딩** — 무기 / 스킬 마다 다른 입력 자동 등록.

```cpp
// Ability 가 Activate 시 자동으로 Input 바인딩
// Ability 가 EndAbility 시 자동 Unbind
// 자세한 = Lyra Sample 참조
```

---

## 7. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | DefaultInput.ini 의 `DefaultPlayerInputClass` 미설정 | EnhancedPlayerInput / EnhancedInputComponent 의무 |
| 2 | `BindAction` 매개변수 시그니처 불일치 | (none) / FInputActionValue / FInputActionInstance 3종 정확히 |
| 3 | `Subsystem->AddMappingContext` 호출 안 함 | OnPossess / BeginPlay 에서 의무 |
| 4 | Subsystem 이 nullptr (Server / Dedicated) | LocalPlayer 안 있는 곳에서 호출 — 가드 의무 |
| 5 | 메뉴 IMC 추가 + Default IMC 제거 안 함 | bConsumeInput 따라 결정 — 명시적 Remove 권장 |
| 6 | Couch Co-op 시 Player1 / Player2 IMC 충돌 | LocalPlayer 별 Subsystem — 자동 분리 |
| 7 | 5.x 사용자 키 매핑 (Settings 메뉴) 안 구현 | UEnhancedInputUserSettings + bIsPlayerMappable |
| 8 | `GetActionValue` Server 에서 호출 | LocalPlayer 만 (Client) — 가드 |
| 9 | 🚨 BindAction 콜백 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 10 | 🚨 `TObjectIterator<UInputMappingContext>` | UAssetManager + AssetRegistry ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |

---

## 8. 체크리스트

- [ ] DefaultInput.ini `DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput`
- [ ] DefaultInput.ini `DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent`
- [ ] PlayerController OnPossess 또는 BeginPlay 에서 `AddMappingContext`
- [ ] Subsystem nullptr 가드 (Dedicated Server)
- [ ] BindAction 매개변수 시그니처 정확 (none / FInputActionValue / FInputActionInstance)
- [ ] IMC Priority 매트릭스 (System 200 / Modal 150 / Menu 100 / Game 0)
- [ ] 메뉴 / 차량 / 모드 전환 = 동적 AddMappingContext / RemoveMappingContext
- [ ] 5.x 사용자 키 매핑 = UEnhancedInputUserSettings 사용
- [ ] 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`

---

## 9. 관련 sub-skill

- [`Input/SKILL.md`](../SKILL.md) — 메인 (Input 카테고리)
- [`Input/EnhancedInput`](../EnhancedInput/SKILL.md) — 메인 (5종 핵심)
- [`Input/Action`](../Action/SKILL.md) — UInputAction + Trigger + Modifier
- [`Input/InputCore`](../InputCore/SKILL.md) — FKey (FEnhancedActionKeyMapping 의 Key 필드)
- [`GameFramework/Controller §3.2`](../../GameFramework/references/Controller.md) — Input Mode (UIOnly / GameAndUI / GameOnly)
- 교차: 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) · 🚨 [`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UEnhancedInputLocalPlayerSubsystem** (LocalPlayer 별 — Couch Co-op 분리) + IMC Stack API (AddMappingContext / RemoveMappingContext / ClearAllMappings / HasMappingContext / GetActionValue / GetActionInstanceData) + FModifyContextOptions (5.x — bIgnoreAllPressedKeysUntilRelease / bForceImmediately). **IMC Priority 매트릭스 7단계** (System 200 / Modal 150 / Menu 100 / Dialog 50 / Vehicle 20 / FirstPerson 10 / Default 0) + 동시 활성 패턴 + Modal 완전 차단 패턴. **UInputMappingContext** (FEnhancedActionKeyMapping per-mapping Trigger/Modifier + bIsPlayerMappable 5.x). **UEnhancedPlayerInput** + DefaultInput.ini 등록 (DefaultPlayerInputClass / DefaultInputComponentClass) + FInputActionInstance (TriggeredTime / ElapsedProcessedTime) + 런타임 Action 상태 조회. **UEnhancedInputComponent** BindAction 3종 시그니처 (none / FInputActionValue / FInputActionInstance) + BindActionValue raw. **Modular Input 5.x** (PawnComponent 분리 + Lyra UAbilityInputBindingComponent). **5.x Player Mappable Key** (UEnhancedInputUserSettings + ApplySettings). 함정 10종 + 9단 체크리스트. |
