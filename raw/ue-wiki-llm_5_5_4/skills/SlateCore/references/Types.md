---
name: slatecore-types
description: EVisibility + ESlateVisibility + EHorizontalAlignment + EWidgetClipping + FSlateColor + FOptionalSize.
---

# SlateCore / Types

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.5.4
> 다루는 영역: Slate 공용 타입 — `TAttribute`/`TSlateAttribute` 어트리뷰트 시스템 + `SlateEnums`/`SlateStructs`/`SlateConstants` + `FPaintArgs` + `ISlateMetaData` + 메타데이터 종류 + `FWidgetActiveTimerDelegate`
> 관련 sub-skill: [`SWidget/`](../SWidget/SKILL.md), [`Layout/`](../Layout/SKILL.md), [`Input/`](../Input/SKILL.md), [`Drawing/`](../Drawing/SKILL.md)

---

## 1. 개요

Slate 의 모든 sub-skill 이 공유하는 작은 타입·유틸·어트리뷰트 시스템을 모은 영역. **`TAttribute`/`TSlateAttribute`** 는 위젯 인자/멤버의 표준 형식이고, **`FPaintArgs`** 는 페인트 컨텍스트, **메타데이터 시스템**은 위젯에 외부 정보를 부착하는 메커니즘.

---

## 2. 핵심 헤더와 클래스

### 2.1 어트리뷰트 시스템

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Types/SlateAttribute.h` | `TSlateAttribute<T, EInvalidateWidgetReason>`, `TSlateMemberAttribute<...>` | 위젯 멤버 어트리뷰트. 값 변경 시 자동 인밸리데이션. |
| `Public/Types/SlateAttributeDescriptor.h` | `FSlateAttributeDescriptor` | `SLATE_DECLARE_WIDGET` 가 등록하는 어트리뷰트 메타. |
| `Public/Types/SlateAttributeMetaData.h` | `FSlateAttributeMetaData` | 위젯별 어트리뷰트 인스턴스 매니저. |
| `Public/Types/Attributes/SlateAttributeBase.inl`, `SlateAttributeContained.inl`, `SlateAttributeDefinition.inl`, `SlateAttributeManaged.inl`, `SlateAttributeMember.inl` | (인라인 구현) | 어트리뷰트 종류별 구현. 직접 include 안 함. |

> `TAttribute<T>` 자체는 `Core` 모듈의 `Misc/Attribute.h` 에 있고, SlateCore는 그 위에 위젯 인밸리데이션 통합을 더한 `TSlateAttribute` 를 제공.

### 2.2 enum / 구조체 / 상수

| 헤더 | 심볼 | 용도 |
|------|------|------|
| `Public/Types/SlateEnums.h` | `enum class EUINavigation : uint8` (Up/Down/Left/Right/Next/Previous, L98), `EUINavigationAction : uint8` (Accept/Back, L123), `ENavigationSource : uint8` (L144), `ENavigationGenesis : uint8` (L157), `EHorizontalAlignment : int` (HAlign_Fill/Left/Center/Right, L173), `EVerticalAlignment : int` (VAlign_Fill/Top/Center/Bottom, L193), `EMenuPlacement : int` (L213), `EOrientation : int` (Horizontal/Vertical, L260), `EScrollDirection : int` (L274), `EActiveTimerReturnType : uint8` (Continue/Stop, L328) | Slate 전반의 enum. |
| `Public/Types/SlateStructs.h` | `struct FOptionalSize` (L12), `FSizeParam` (L95), `FStretch` (L144), `FStretchContent` (L161), `FAuto` (L182) | 사이즈 파라미터 — `SBoxPanel::Slot().FillWidth(...)` 같은 곳에 사용. |
| `Public/Types/SlateConstants.h` | `SlateConstants::*` | 매직 넘버 (드래그 임계값 등). |
| `Public/Types/SlateBox2.h`, `SlateVector2.h` | `FBox2f`/`FVector2f` 호환 래퍼 | 5.x `FVector2D` → `FVector2f` 마이그레이션 보조. |
| `Public/Types/PaintArgs.h` | `class FPaintArgs` | `OnPaint` 의 `Args` 파라미터. `GetCurrentTime()`/`GetDeltaTime()`/`GetWidgetStyle()`/`InheritedHittestability()`. |

### 2.3 메타데이터 시스템

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Types/ISlateMetaData.h` | `class ISlateMetaData` | 위젯에 부착하는 메타데이터 베이스 (`SLATE_METADATA_TYPE` 매크로). |
| `Public/Types/InvisibleToWidgetReflectorMetaData.h` | `FInvisibleToWidgetReflectorMetaData : ISlateMetaData` 🛠 | Slate Reflector(에디터 디버그)에서 숨김. |
| `Public/Types/NavigationMetaData.h` | `FNavigationMetaData : ISlateMetaData` | 위젯의 내비게이션 정책 (방향별 경계 등). |
| `Public/Types/ReflectionMetadata.h` | `FReflectionMetaData : ISlateMetaData` 🛠 | 클래스명·인스턴스명 디버그 정보. |
| `Public/Types/TrackedMetaData.h` | `FTrackedMetaData : ISlateMetaData` 🛠 | 자동화 테스트용 위젯 추적. |

### 2.4 델리게이트

| 헤더 | 심볼 | 용도 |
|------|------|------|
| `Public/Types/WidgetActiveTimerDelegate.h` | `DECLARE_DELEGATE_RetVal_TwoParams(EActiveTimerReturnType, FWidgetActiveTimerDelegate, double, float)` | `RegisterActiveTimer` 콜백 시그니처. |
| `Public/Types/WidgetMouseEventsDelegate.h` | 마우스 이벤트 델리게이트 | `OnMouseMove` 등의 외부 hook. |

---

## 3. 자주 쓰는 API

### 3.1 TAttribute / TSlateAttribute

```cpp
// === TAttribute<T> — 정적 값 또는 람다 ===
TAttribute<FText> Static = FText::FromString(TEXT("Hello"));   // 정적
TAttribute<FText> Dyn    = TAttribute<FText>::CreateLambda([this]() {
    return FText::AsNumber(GetHealth());
});

// 사용 시:
FText Cur = Dyn.Get();             // 람다면 호출, 정적이면 값 반환
bool bBound = Dyn.IsBound();        // 람다 / 정적 / 미설정 구분

// === TSlateAttribute<T, Reason> — 위젯 멤버 ===
class SMyWidget : public SCompoundWidget
{
    SLATE_DECLARE_WIDGET(SMyWidget, SCompoundWidget)
private:
    TSlateAttribute<FText, EInvalidateWidgetReason::Layout> Title;
    // 값 변경 시 자동으로 Layout 인밸리데이션 발행
};
```

자세한 인밸리데이션 흐름은 [`SWidget/§5`](../SWidget/SKILL.md), [`Drawing/§4`](../Drawing/SKILL.md).

### 3.2 사이즈 파라미터

```cpp
// SBoxPanel::Slot 에서:
+ SVerticalBox::Slot()
    .AutoHeight()                        // FAuto — 자식 desired size
+ SVerticalBox::Slot()
    .FillHeight(1.f)                     // FStretch — 1.f 비율
+ SVerticalBox::Slot()
    .HAlign(HAlign_Center)
    .VAlign(VAlign_Top)

// FOptionalSize — 옵션 너비/높이
SNew(SBox).WidthOverride(FOptionalSize(/*set=*/100.f));
SNew(SBox).WidthOverride(FOptionalSize());     // unset → 자식 기본값 사용
```

### 3.3 FPaintArgs

```cpp
virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geo, ...) const override
{
    double T  = Args.GetCurrentTime();
    float Dt  = Args.GetDeltaTime();
    const FWidgetStyle& Style = Args.GetWidgetStyle();
    bool bHitTest = Args.GetInheritedHittestability();
    // ...
}
```

### 3.4 메타데이터 부착

```cpp
class FMyMetaData : public ISlateMetaData
{
public:
    SLATE_METADATA_TYPE(FMyMetaData, ISlateMetaData)
    FString DebugName;
};

// 위젯에 부착
TSharedRef<SWidget> W = SNew(SButton);
W->AddMetadata(MakeShared<FMyMetaData>());

// 검색
TSharedPtr<FMyMetaData> Meta = W->GetMetaData<FMyMetaData>();
if (Meta) UE_LOG(LogTemp, Log, TEXT("%s"), *Meta->DebugName);
```

### 3.5 ActiveTimer 등록 (Animation 과 짝)

```cpp
RegisterActiveTimer(0.f, FWidgetActiveTimerDelegate::CreateSP(this, &SMy::Tick));

EActiveTimerReturnType SMy::Tick(double InCurrentTime, float InDeltaTime)
{
    DoWork();
    return WantsContinue ? EActiveTimerReturnType::Continue
                         : EActiveTimerReturnType::Stop;
}
```

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 ISlateMetaData (`ISlateMetaData.h`)

```cpp
class ISlateMetaData
{
public:
    virtual ~ISlateMetaData() = default;
    virtual bool IsOfType(const FName& Type) const;     // SLATE_METADATA_TYPE 매크로가 자동 구현
};
```

`SLATE_METADATA_TYPE(MyType, ParentType)` 매크로로 등록 — 실제로 override 할 일은 없다.

### 4.2 어트리뷰트 시스템 내부

`TSlateAttribute` 의 비교 predicate 를 커스터마이즈할 수 있지만 게임 코드에서 일반적으로 만지지 않음. 기본 `TSlateAttributeComparePredicate<>` 와 `TSlateAttributeFTextComparePredicate` (FText 특수) 가 자동 사용됨.

---

## 5. 예제

### 5.1 어트리뷰트 람다 vs 정적

```cpp
// ✅ 자주 변하지 않는 값 → 정적
TAttribute<FText> Title = LOCTEXT("Hello", "Hello");

// ✅ 다른 멤버에 의존하는 값 → 람다
TAttribute<FText> HpText = TAttribute<FText>::CreateLambda([this]() {
    return FText::AsNumber(CachedHp);
});

// ❌ 람다 안에서 매번 무거운 계산 → 캐시 필요
TAttribute<FText> Bad = TAttribute<FText>::CreateLambda([this]() {
    return FText::FromString(ComputeExpensiveLabel());   // 매 프레임 호출됨
});

// ✅ 캐시 변수 + Tick/Timer 에서 갱신, 어트리뷰트는 단순 조회
TAttribute<FText> Good = TAttribute<FText>::CreateLambda([this]() {
    return CachedExpensiveLabel;
});
```

### 5.2 정렬·정합 enum 활용

```cpp
SNew(SHorizontalBox)
+ SHorizontalBox::Slot()
    .HAlign(HAlign_Left)
    .VAlign(VAlign_Center)
    .AutoWidth()
    [ SNew(SImage) ]
+ SHorizontalBox::Slot()
    .HAlign(HAlign_Fill)        // 남은 영역 채움
    .VAlign(VAlign_Center)
    .FillWidth(1.f)
    [ SNew(STextBlock) ];
```

### 5.3 메타데이터로 위젯 식별 (자동화 테스트)

```cpp
// 자동화 테스트가 위젯을 찾을 수 있게 식별자 부착
class FAutomationIdMetaData : public ISlateMetaData
{
public:
    SLATE_METADATA_TYPE(FAutomationIdMetaData, ISlateMetaData)
    FName Id;
    explicit FAutomationIdMetaData(FName InId) : Id(InId) {}
};

ChildSlot
[
    SNew(SButton).OnClicked_Lambda([](){ return FReply::Handled(); })
        ->AddMetadata(MakeShared<FAutomationIdMetaData>(TEXT("HUD.StartButton")))
];
```

---

## 6. 운영 가이드 / 함정

1. **`TAttribute` vs `TSlateAttribute`** — 인자(`SLATE_ATTRIBUTE`)는 `TAttribute<T>`, 위젯 멤버에 보유하는 형식은 `TSlateAttribute<T, Reason>`. 둘은 호환 (인자 → 멤버 `Assign`).
2. **람다 캡처 강 참조** — `[this]` 가 아니라 `[Weak = AsWeak()]` 후 `Pin()` 으로 안전하게. 강 참조 시 메모리 누수.
3. **`FVector2D` → `FVector2f`** — 5.x 마이그레이션. `SlateBox2.h`/`SlateVector2.h` 의 호환 래퍼 사용.
4. **`HAlign_Fill`/`VAlign_Fill`** 만 사용하면 자식 desired size 무시 — 의도한 정렬이 안 보일 때 first 의심.
5. **메타데이터 검색 비용** — 위젯에 메타데이터가 많아지면 `GetMetaData<T>` 가 선형 검색. 매 프레임 호출 회피.
6. **`EActiveTimerReturnType::Stop`** 반환 시 자동 해제 — 콜백 안에서 `UnRegisterActiveTimer` 추가 호출 불필요.
7. **`FOptionalSize` 의 unset** — `IsSet() == false` 면 자식 desired size 사용. 0 과 다름.

---

## 7. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `FInvisibleToWidgetReflectorMetaData` 🛠 | InvisibleToWidgetReflectorMetaData.h | `WITH_SLATE_DEBUGGING` 위주 | Slate Reflector 트리에서 숨김. |
| `FReflectionMetaData` 🛠 | ReflectionMetadata.h | `WITH_SLATE_DEBUGGING` | 클래스/인스턴스 디버그명. |
| `FTrackedMetaData` 🛠 | TrackedMetaData.h | `WITH_SLATE_DEBUGGING` | 자동화 테스트 추적. |
| `SLATE_METADATA_TYPE` 매크로 자체는 모든 빌드 | (매크로) | — | 메타데이터 본체는 런타임 안전. |

---

## 8. 관련 sub-skill

- [`SWidget/`](../SWidget/SKILL.md) — `TSlateAttribute` 의 자동 인밸리데이션, `RegisterActiveTimer`
- [`Layout/`](../Layout/SKILL.md) — `EHorizontalAlignment`/`EVerticalAlignment`/`FOptionalSize`/`FStretch` 가 슬롯에서 사용
- [`Input/`](../Input/SKILL.md) — `EUINavigation`/`EUINavigationAction` 이 내비 라우팅
- [`Drawing/`](../Drawing/SKILL.md) — `FPaintArgs` 가 OnPaint 컨텍스트
- [`Animation/`](../Animation/SKILL.md) — `FWidgetActiveTimerDelegate`/`EActiveTimerReturnType`
- [`Trace/`](../Trace/SKILL.md) — Slate Reflector 와 메타데이터 활용
