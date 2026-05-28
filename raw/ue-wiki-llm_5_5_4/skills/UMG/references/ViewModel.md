---
name: umg-viewmodel
description: 🆕 5.x MVVM - UMVVMViewModelBase + UMVVMView + Field Notify + Binding 자동화.
---

# UMG · ViewModel sub-skill

> **모듈**: UMG (Tier 3 · Slate 카테고리) — FieldNotification 통합
> **위치**: `Engine/Source/Runtime/UMG/Public/FieldNotification/` + `Engine/Source/Runtime/UMG/Public/Binding/` + (런타임은 별도 `FieldNotification` 모듈)
> **다루는 범위**: `FieldNotify` 메타키 + `INotifyFieldValueChanged` 인터페이스 + UMG 자체 `Binding/*` 시스템 (legacy) + MVVM 패턴.

---

## 1. 개요

UMG에서 **데이터 변경 → 위젯 자동 갱신** 을 구현하는 두 시스템:

1. **FieldNotify (5.3+ 권장)** — `UPROPERTY(FieldNotify)` 마킹된 프로퍼티가 변경되면 옵서버에게 자동 통지. UE의 공식 MVVM 패턴 (`UMVVMViewModelBase`) 의 기반. 런타임 모듈명은 `FieldNotification` (별도 모듈).
2. **Legacy Binding (`Public/Binding/*`)** — 디자이너에서 임의 함수 결과를 위젯 프로퍼티에 폴링 바인딩. 매 프레임 평가 → **성능 함정** ([`06_InvalidationHotspots.md §2.7`](../../../references/06_InvalidationHotspots.md)). 신규 코드는 FieldNotify 권장.

본 sub-skill 은 **FieldNotify 사용·구현** 과 **Legacy Binding 회피** 가 주제.

---

## 2. 핵심 헤더와 클래스

### 2.1 FieldNotification 모듈

```
FieldNotification/                          (별도 모듈 — Build.cs에 추가 필요)
└── INotifyFieldValueChanged                인터페이스 — 옵서버 등록/통지
    + FFieldId / FFieldNotificationId
    + FFieldValueChangedDelegate
```

UMG 측 헤더 (deprecated forwarding):

| 헤더 | 메모 |
|------|------|
| `UMG/Public/FieldNotification/IFieldValueChanged.h` | **5.3에서 deprecated** — `INotifyFieldValueChanged.h` 사용 |
| `UMG/Public/FieldNotification/FieldId.h` | `FFieldId` |
| `UMG/Public/FieldNotification/FieldMulticastDelegate.h` | 멀티캐스트 델리게이트 |
| `UMG/Public/FieldNotification/FieldNotificationDeclaration.h` | `UE_FIELD_NOTIFICATION_*` 매크로 |
| `UMG/Public/FieldNotification/FieldNotificationHelpers.h` | 헬퍼 |
| `UMG/Public/FieldNotification/IClassDescriptor.h` | 클래스 디스크립터 |
| `UMG/Public/FieldNotification/WidgetEventField.h` | 위젯 이벤트 필드 |

### 2.2 Legacy UMG Binding (`Binding/`)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `Binding/PropertyBinding.h` | `UPropertyBinding` | 베이스 — 프로퍼티 폴링 |
| `Binding/BoolBinding.h` | `UBoolBinding` | bool 폴링 |
| `Binding/BrushBinding.h` | `UBrushBinding` | FSlateBrush 폴링 |
| `Binding/CheckedStateBinding.h` | `UCheckedStateBinding` | 체크 상태 |
| `Binding/ColorBinding.h` | `UColorBinding` | FSlateColor / FLinearColor |
| `Binding/FloatBinding.h` | `UFloatBinding` | float |
| `Binding/Int32Binding.h` | `UInt32Binding` | int32 |
| `Binding/MouseCursorBinding.h` | `UMouseCursorBinding` | 마우스 커서 |
| `Binding/TextBinding.h` | `UTextBinding` | FText |
| `Binding/VisibilityBinding.h` | `UVisibilityBinding` | ESlateVisibility |
| `Binding/WidgetBinding.h` | `UWidgetBinding` | UWidget* |
| `Binding/States/...` | (상태 바인딩) | 진보형 |
| `Binding/DynamicPropertyPath.h` | `FDynamicPropertyPath` | 경로 표현 |

> **Legacy Binding 사용 회피**. 매 프레임 폴링 → 인밸리데이션 다발 + 성능 저하. FieldNotify 또는 직접 setter 호출로 대체.

---

## 3. FieldNotify — 사용법

### 3.1 UPROPERTY 마킹

```cpp
UCLASS()
class UMyViewModel : public UObject, public INotifyFieldValueChanged
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadWrite, Setter, Getter, FieldNotify, Category="Data")
    int32 Score = 0;

    UPROPERTY(BlueprintReadWrite, Setter, Getter, FieldNotify, Category="Data")
    FText PlayerName;

    void SetScore(int32 NewScore);
    int32 GetScore() const { return Score; }

    void SetPlayerName(FText NewName);
    FText GetPlayerName() const { return PlayerName; }

    // INotifyFieldValueChanged 구현
    UE_FIELD_NOTIFICATION_DECLARE_FIELD(Score);
    UE_FIELD_NOTIFICATION_DECLARE_FIELD(PlayerName);
    UE_FIELD_NOTIFICATION_DECLARE_HAS_FIELD_BEGIN
        UE_FIELD_NOTIFICATION_DECLARE_HAS_FIELD(Score)
        UE_FIELD_NOTIFICATION_DECLARE_HAS_FIELD(PlayerName)
    UE_FIELD_NOTIFICATION_DECLARE_HAS_FIELD_END;
};
```

setter 안에서 통지:

```cpp
void UMyViewModel::SetScore(int32 NewScore)
{
    if (Score != NewScore)
    {
        Score = NewScore;
        UE_MVVM_BROADCAST_FIELD_VALUE_CHANGED(Score);
        // 또는 명시적: BroadcastFieldValueChanged(THIS_FIELD_NOTIFICATION_ID(Score));
    }
}
```

### 3.2 위젯에서 옵서버 등록

```cpp
void UMyHUDWidget::NativeConstruct()
{
    Super::NativeConstruct();              // ← FIRST: 입력 델리게이트·UpdateCanTick

    if (UMyViewModel* VM = GetViewModel())
    {
        // FieldNotify 변경 시 자동 콜백
        FFieldNotificationId ScoreId = THIS_FIELD_NOTIFICATION_ID_OF(VM, Score);
        VM->AddFieldValueChangedDelegate(ScoreId,
            INotifyFieldValueChanged::FFieldValueChangedDelegate::CreateUObject(this, &UMyHUDWidget::HandleScoreChanged));
    }
}

void UMyHUDWidget::NativeDestruct()
{
    if (UMyViewModel* VM = GetViewModel())
    {
        VM->RemoveAllFieldValueChangedDelegates(this);
    }
    Super::NativeDestruct();               // ← LAST
}

void UMyHUDWidget::HandleScoreChanged(UObject* Object, FFieldNotificationId FieldId)
{
    if (UMyViewModel* VM = Cast<UMyViewModel>(Object))
    {
        if (ScoreText) { ScoreText->SetText(FText::AsNumber(VM->GetScore())); }
    }
}
```

### 3.3 기본 제공된 FieldNotify 위젯 프로퍼티

UMG 표준 위젯 중 일부는 이미 `FieldNotify` 가 적용되어 있어 ViewModel 측 구현만으로 자동 갱신 가능:

| 위젯 | FieldNotify 프로퍼티 | 헤더 |
|------|---------------------|------|
| `UCheckBox` | `CheckedState` | CheckBox.h L38 |
| `UImage` | `Brush` | Image.h L38 |
| `UTextBlock` (BindableProperty 통해) | `Text` | TextBlock.h |
| `URichTextBlock` | `Text` | RichTextBlock.h |

자세히는 각 헤더의 `meta=(FieldNotify)` 확인.

---

## 4. UMVVM 플러그인 통합 (5.1+)

UE 5.1+ 의 공식 MVVM 시스템 (`ModelViewViewModel` 플러그인) 은 FieldNotify 위에 빌드. 통합 사용:

| 클래스 | 모듈 | 의미 |
|--------|------|------|
| `UMVVMViewModelBase` | `ModelViewViewModel` 플러그인 | INotifyFieldValueChanged 구현 베이스 |
| `UMVVMView` | 동상 | 뷰 측 바인딩 등록 |
| `UMVVMSubsystem` | 동상 | ViewModel 컬렉션 관리 |
| `UMVVMViewModelContextResolver` | 동상 | DI 패턴 — ViewModel 주입 |

> 본 위키는 ModelViewViewModel 플러그인 자체는 다루지 않음 (별도 플러그인). FieldNotify 만 다룸.

---

## 5. 가상 함수 (오버라이드 포인트)

### 5.1 INotifyFieldValueChanged 인터페이스

```cpp
class INotifyFieldValueChanged : public UInterface
{
public:
    virtual FDelegateHandle AddFieldValueChangedDelegate(FFieldNotificationId InFieldId, FFieldValueChangedDelegate InNewDelegate) = 0;
    virtual bool RemoveFieldValueChangedDelegate(FFieldNotificationId InFieldId, FDelegateHandle InHandle) = 0;
    virtual int32 RemoveAllFieldValueChangedDelegates(const void* InUserObject) = 0;
    virtual int32 RemoveAllFieldValueChangedDelegates(FFieldNotificationId InFieldId, const void* InUserObject) = 0;
    
protected:
    virtual void BroadcastFieldValueChanged(FFieldNotificationId InFieldId) = 0;
    virtual const UE::FieldNotification::IClassDescriptor& GetFieldNotificationDescriptor() const = 0;
};
```

`UE_FIELD_NOTIFICATION_IMPLEMENTATION_*` 매크로가 위 virtual 들을 자동 생성. 사용자가 직접 구현하는 경우는 거의 없다.

---

## 6. Legacy Binding 회피 패턴

### 6.1 디자이너 Bind 함수 → 매 프레임 폴링

**디자이너의 위젯 프로퍼티 옆 "Bind ▼" 메뉴 → BP 함수 선택** 하면 `UFloatBinding` / `UTextBinding` 등이 생성되어 **매 프레임 BP 함수를 호출**해서 위젯 프로퍼티 갱신. 이는:

- BP 함수가 매 프레임 실행 → 부담
- 결과값이 안 바뀌어도 setter 호출 → Slate setter가 "동일값 비교" 안 하면 **자동 Invalidate** → DrawCall 증가
- 디버그 어려움 — Tick 로그에 안 잡힘

### 6.2 회피 — FieldNotify 또는 명시적 setter

```cpp
// ❌ Legacy Binding (디자이너에서 PlayerScoreText.Text 옆 Bind ▼ → GetPlayerScoreText)
UFUNCTION(BlueprintPure) FText GetPlayerScoreText() const
{
    return FText::AsNumber(PlayerScore);
}

// ✅ 변경 시점에만 명시적 setter 호출
void UMyHUDWidget::SetPlayerScore(int32 NewScore)
{
    if (PlayerScore != NewScore)
    {
        PlayerScore = NewScore;
        if (PlayerScoreText)
        {
            PlayerScoreText->SetText(FText::AsNumber(NewScore));
        }
    }
}

// ✅✅ 더 좋음 — ViewModel 측 FieldNotify
void UMyViewModel::SetScore(int32 NewScore)
{
    if (Score != NewScore)
    {
        Score = NewScore;
        UE_MVVM_BROADCAST_FIELD_VALUE_CHANGED(Score);
        // → 모든 옵서버 위젯이 자동 갱신
    }
}
```

자세한 hotspot은 [`06_InvalidationHotspots.md §2.7`](../../../references/06_InvalidationHotspots.md).

---

## 7. 예제

### 7.1 ViewModel + 다중 위젯 동기화

```cpp
UCLASS(BlueprintType, Blueprintable)
class UPlayerStatsViewModel : public UObject, public INotifyFieldValueChanged
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadWrite, Getter, Setter, FieldNotify) float HealthPercent = 1.f;
    UPROPERTY(BlueprintReadWrite, Getter, Setter, FieldNotify) float ManaPercent = 1.f;
    UPROPERTY(BlueprintReadWrite, Getter, Setter, FieldNotify) FText PlayerName;
    UPROPERTY(BlueprintReadWrite, Getter, Setter, FieldNotify) int32 Level = 1;

    void SetHealthPercent(float V) { if (HealthPercent != V) { HealthPercent = V; UE_MVVM_BROADCAST_FIELD_VALUE_CHANGED(HealthPercent); } }
    void SetManaPercent(float V)   { if (ManaPercent != V)   { ManaPercent = V;   UE_MVVM_BROADCAST_FIELD_VALUE_CHANGED(ManaPercent); } }
    void SetPlayerName(FText V)    { if (!PlayerName.EqualTo(V)) { PlayerName = V; UE_MVVM_BROADCAST_FIELD_VALUE_CHANGED(PlayerName); } }
    void SetLevel(int32 V)         { if (Level != V)         { Level = V;         UE_MVVM_BROADCAST_FIELD_VALUE_CHANGED(Level); } }

    // INotifyFieldValueChanged 구현 매크로 (생략)
};

// 호스트 위젯 — 여러 자식 위젯을 단일 ViewModel에 동기화
UCLASS()
class UMyPlayerHUD : public UUserWidget
{
    GENERATED_BODY()
protected:
    UPROPERTY(meta=(BindWidget)) UProgressBar* HealthBar = nullptr;
    UPROPERTY(meta=(BindWidget)) UProgressBar* ManaBar = nullptr;
    UPROPERTY(meta=(BindWidget)) UTextBlock* NameText = nullptr;
    UPROPERTY(meta=(BindWidget)) UTextBlock* LevelText = nullptr;

    UPROPERTY() TObjectPtr<UPlayerStatsViewModel> ViewModel = nullptr;

    virtual void NativeConstruct() override
    {
        Super::NativeConstruct();      // ← FIRST
        if (!ViewModel) { ViewModel = NewObject<UPlayerStatsViewModel>(this); }
        BindToViewModel();
    }

    virtual void NativeDestruct() override
    {
        if (ViewModel) { ViewModel->RemoveAllFieldValueChangedDelegates(this); }
        Super::NativeDestruct();       // ← LAST
    }

    void BindToViewModel()
    {
        ViewModel->AddFieldValueChangedDelegate(
            THIS_FIELD_NOTIFICATION_ID_OF(ViewModel.Get(), HealthPercent),
            INotifyFieldValueChanged::FFieldValueChangedDelegate::CreateUObject(this, &UMyPlayerHUD::HandleHealthChanged));
        // ... ManaPercent, PlayerName, Level 동일 패턴
        // 초기 상태 1회 강제 동기화
        HandleHealthChanged(ViewModel, THIS_FIELD_NOTIFICATION_ID_OF(ViewModel.Get(), HealthPercent));
    }

    void HandleHealthChanged(UObject* Obj, FFieldNotificationId Id)
    {
        if (UPlayerStatsViewModel* VM = Cast<UPlayerStatsViewModel>(Obj))
        {
            HealthBar->SetPercent(VM->HealthPercent);
        }
    }
};
```

---

## 8. 운영 가이드 / 함정

| 함정 | 회피 |
|------|------|
| 디자이너 "Bind ▼" 메뉴 사용 | 매 프레임 폴링 → 명시적 setter 또는 FieldNotify |
| FieldNotify 마킹만 하고 setter에서 broadcast 누락 | `UE_MVVM_BROADCAST_FIELD_VALUE_CHANGED(...)` 호출 의무 |
| setter 안에서 동일값 비교 누락 | `if (Old != New)` 검사 → 무한 루프·불필요 통지 방지 |
| `NativeDestruct` 에서 옵서버 해제 안 함 | `RemoveAllFieldValueChangedDelegates(this)` 호출 |
| `IFieldValueChanged.h` (deprecated 5.3) 사용 | `INotifyFieldValueChanged.h` 사용 + `FieldNotification` 모듈 추가 |
| ViewModel을 호스트 위젯이 강 참조 못 함 | `UPROPERTY()` 로 GC 보호 |
| 다중 옵서버에서 같은 setter 호출 | broadcast 의 receiver가 자기 자신을 다시 set → 무한 루프 방지 |
| `meta=(FieldNotify)` 가 표준 위젯에 없음 | UMG 표준 위젯 중 일부만 마킹됨 — 직접 setter로 대체 |

---

## 9. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 가드 |
|------|------|
| Legacy Binding 디자이너 메뉴 🛠 | `WITH_EDITOR` (디자이너에서 Bind ▼ 추가) |
| `meta=(FieldNotify)` 메타 처리 🛠 | `WITH_EDITOR` (UnrealHeaderTool 시점) |
| `UMVVM*` 플러그인 디자이너 통합 🛠 | 별도 플러그인 |

자세한 에디터 전용 통합은 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md).

---

## 10. 관련 sub-skill

- [`UMG/UWidget`](../UWidget/SKILL.md) — UWidget 베이스
- [`UMG/UUserWidget`](../UUserWidget/SKILL.md) — Native\* + Super 호출 규약 (NativeConstruct 에서 옵서버 등록 / NativeDestruct 에서 해제)
- [`UMG/StandardWidgets`](../StandardWidgets/SKILL.md) — UCheckBox/UImage 의 `meta=(FieldNotify)` 프로퍼티
- [`UMG/Slot`](../Slot/SKILL.md) — 슬롯 setter 자동 인밸리데이션
- [`CoreUObject/Reflection`](../../CoreUObject/references/Reflection.md) — UPROPERTY 메타키 처리
- [`CoreUObject/Network`](../../CoreUObject/references/Network.md) — RepNotify 와 비교 (네트워크 변경 통지의 다른 형태)
- [`06_InvalidationHotspots.md §2.7`](../../../references/06_InvalidationHotspots.md) — Legacy Binding 매 프레임 폴링 회피
- [`04_OverrideIndex.md §6.5`](../../../references/04_OverrideIndex.md) — Native\* Super 호출 규약
