---
name: umg-uwidget
description: UWidget 베이스 - RebuildWidget + SynchronizeProperties + ReleaseSlateResources + Visibility + IsVisible + GetCachedWidget.
---

# UMG / UWidget

> 부모 모듈: [`UMG`](../SKILL.md) · UE 5.5.4
> 다루는 영역: 모든 UMG 위젯의 베이스 — `UVisual` / `UWidget : INotifyFieldValueChanged` + `RebuildWidget()` (UWidget → SWidget 변환) + `SynchronizeProperties()` + 인밸리데이션 / 갱신 흐름 (Setter 자동 트리거 / `EWidgetVolatility` / `ForceVolatile`) + Slot / 공통 setter (Visibility/IsEnabled/RenderTransform/Opacity/Clipping/PixelSnapping/Cursor/ToolTip/Focus/Navigation) + FieldNotification (MVVM)
> **🚨 인밸리데이션 갱신 흐름은 본 sub-skill 의 의무 섹션 (§5)** — [`SlateCore/SKILL.md §5.1`](../../SlateCore/SKILL.md) 표에서 명시됨.
> 관련 sub-skill: [`UUserWidget/`](../UUserWidget/SKILL.md), [`PanelWidgets/`](../PanelWidgets/SKILL.md), [`Slot/`](../Slot/SKILL.md), [`ViewModel/`](../ViewModel/SKILL.md), [`../../SlateCore/SWidget/`](../../SlateCore/references/SWidget.md), [`../../SlateCore/Drawing/`](../../SlateCore/references/Drawing.md)

---

## 1. 개요

`UWidget` 은 **모든 UMG 위젯의 베이스**다. UCLASS 라 디테일 패널·BP 노드에 노출되고, 내부적으로 `RebuildWidget()` 으로 `TSharedRef<SWidget>` 을 만들어 Slate 사이클에 들어간다.

```
UObject
  └─ UVisual                  (UMG 의 슬롯·위젯 공통 베이스)
       ├─ UWidget             (★ 모든 UMG 위젯의 베이스)
       │    ├─ UPanelWidget    (자식 N개 — PanelWidgets/SKILL.md)
       │    │    ├─ UContentWidget    (자식 1개)
       │    │    │    ├─ UInvalidationBox / URetainerBox / UButton / UBorder ...
       │    │    │    └─ UUserWidget  (★ BP 위젯의 베이스 — UUserWidget/SKILL.md)
       │    │    └─ UCanvasPanel / UGridPanel / UHorizontalBox ...
       │    ├─ ULeafWidget 류 (자식 없음)  — UTextBlock / UImage / USlider ...
       │    └─ UListViewBase 류           — UListView / UTreeView / UTileView
       └─ UPanelSlot          (자식 배치 메타 — Slot/SKILL.md)
```

**왜 두 단계 분리** — `UVisual` 은 슬롯과 위젯의 공통(예: `ReleaseSlateResources`/UObject 베이스 동작), `UWidget` 은 위젯만의 동작(SWidget 생성·인밸리데이션·BP 노출).

---

## 2. 핵심 헤더와 클래스

### 2.1 베이스 사슬

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Components/Visual.h` | `UCLASS(DefaultToInstanced, MinimalAPI) UVisual : public UObject` (L12) | UMG 슬롯/위젯 공통 베이스. `ReleaseSlateResources(bool)` virtual 1개 + `BeginDestroy`/`NeedsLoadForServer` override. |
| `Public/Components/Widget.h` | `class UWidget : public UVisual, public INotifyFieldValueChanged` (L215, UE 5.5) | **모든 UMG 위젯의 베이스**. FieldNotification 인터페이스로 MVVM 통합. 80+ public 메서드 + 다수 virtual. |
| `Public/Components/SlateWrapperTypes.h` | `enum class ESlateVisibility : uint8` (L21), `ESlateAccessibleBehavior : uint8` (L37), `EWidgetClipping`, `EWidgetPixelSnapping` 등 | UMG ↔ Slate enum 매핑. |

### 2.2 UWidget 핵심 멤버

| 멤버 | 위치 | 의미 |
|------|------|------|
| `UPROPERTY TObjectPtr<UPanelSlot> Slot` | Widget.h L263 (5.5) | 부모 패널의 자식 배치 메타 (CanvasPanelSlot/HorizontalBoxSlot 등). UPROPERTY로 직접 디테일 노출. |
| `UPROPERTY FText ToolTipText` (L276, 5.5) | Widget.h | 툴팁 — Setter `SetToolTipText` (L550, 5.5) + `FieldNotify` (FieldNotification 자동). |
| `UPROPERTY TObjectPtr<UWidget> ToolTipWidget` | Widget.h | 커스텀 툴팁 위젯. |
| `UPROPERTY FWidgetTransform RenderTransform` (L297, 5.5) | Widget.h | 렌더 변환 — Setter `SetRenderTransform` (L498, 5.5). |
| `UPROPERTY FVector2D RenderTransformPivot` (L305) | Widget.h | 변환 피벗. |
| `UPROPERTY ESlateVisibility Visibility` (L434, 5.5) | Widget.h | 가시성 — Setter `SetVisibility` + `FieldNotify`. |
| `UPROPERTY bool bIsEnabled` (L326) | Widget.h | 활성 — Setter `SetIsEnabled` + `FieldNotify`. |
| `UPROPERTY float RenderOpacity` (L446, 5.5) | Widget.h | 불투명도 — Setter `SetRenderOpacity` (L596, 5.5). |
| `uint8 bIsVolatile:1` | Widget.h L387 (5.5) | 휘발성 (캐시 비활성). `ForceVolatile` 으로 토글. |
| 델리게이트 11종 (`FGetBool`/`FGetFloat`/`FGetInt32`/`FGetText`/`FGetSlateColor`/`FGetLinearColor`/`FGetSlateBrush`/`FGetSlateVisibility`/`FGetMouseCursor`/`FGetCheckBoxState`/`FGetWidget`) | Widget.h L237~ | BP 동적 바인딩 베이스. ViewModel/SKILL.md 에서 자세히. |
| `FOnReply` / `FOnPointerEvent` / `FGenerateWidgetForString`/`Object` | Widget.h L266~ | 이벤트·생성 델리게이트. |

### 2.3 FieldNotification (MVVM 통합)

| 매크로 | 위치 | 역할 |
|--------|------|------|
| `UE_FIELD_NOTIFICATION_DECLARE_CLASS_DESCRIPTOR_BASE_BEGIN/END` | Widget.h L223~L233 | UWidget 자체의 필드 노티피케이션 디스크립터. |
| `UE_FIELD_NOTIFICATION_DECLARE_FIELD(ToolTipText, UMG_API)` 등 | Widget.h L224~226 | `ToolTipText` / `Visibility` / `bIsEnabled` 3개 필드 노티 등록 — **값 변경 시 자동 Broadcast**. |
| `UPROPERTY(... FieldNotify ...)` 메타 | Widget.h L326·L439 | UPROPERTY 에 `FieldNotify` 메타 → 코드 생성 시 노티 등록. |

`INotifyFieldValueChanged` 본체는 별도 `FieldNotification` 모듈 (`Public/INotifyFieldValueChanged.h`). 자세한 사용은 [`ViewModel/`](../ViewModel/SKILL.md).

---

## 3. 자주 쓰는 API

> ⚠ **UE 5.5 line 번호 주의**: 아래 코드 주석의 `// L###` setter line 번호는 UE 5.7.4 기준으로 기록된 값 — UE 5.5.4 에서는 함수 정의 위치가 평균 ~5~30 라인 위로 이동했음 (UWidget L215, Slot L263, ToolTipText L276 등 §2.2 참조). 정확 위치는 `grep -n "함수명" Source/Runtime/UMG/Public/Components/Widget.h` 로 즉시 검증.

### 3.1 가시성 / 활성 / 변환

```cpp
// 가시성 (자동 인밸리데이션 — Visibility = Layout 트리거)
MyWidget->SetVisibility(ESlateVisibility::Visible);
//          Hidden / HitTestInvisible / SelfHitTestInvisible / Collapsed

// 활성 (FieldNotify 자동 Broadcast)
MyWidget->SetIsEnabled(false);

// 렌더 변환 — RenderTransform 트리거 (Layout 변경 없음)
FWidgetTransform Tr;
Tr.Translation = FVector2D(10.f, 0.f);
Tr.Scale       = FVector2D(1.5f, 1.5f);
Tr.Angle       = 15.f;
MyWidget->SetRenderTransform(Tr);                   // L504
MyWidget->SetRenderScale(FVector2D(2.f));           // L508
MyWidget->SetRenderShear(FVector2D(0.f, 0.2f));     // L512
MyWidget->SetRenderTransformAngle(45.f);            // L516
MyWidget->SetRenderTranslation(FVector2D(0,10));    // L524
MyWidget->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));  // L531
MyWidget->SetRenderOpacity(0.5f);                   // L602  → Paint 트리거

// 클리핑·픽셀 스냅
MyWidget->SetClipping(EWidgetClipping::ClipToBounds);    // L610
MyWidget->SetPixelSnapping(EWidgetPixelSnapping::Inherit); // L616

// 휘발성 (매 프레임 페인트 — 신중)
MyWidget->ForceVolatile(true);                       // L620

// 사용자 좌우 흐름
MyWidget->SetFlowDirectionPreference(EFlowDirectionPreference::LeftToRight);  // L537
```

### 3.2 입력 / 포커스 / 캡처

```cpp
// 포커스
MyWidget->SetKeyboardFocus();                        // L652
MyWidget->SetFocus();                                // L672
MyWidget->SetUserFocus(PlayerController);            // L676
bool bHas = MyWidget->HasKeyboardFocus();            // L632
bool bAny = MyWidget->HasAnyUserFocus();             // L660
bool bHasDescendants = MyWidget->HasFocusedDescendants();  // L664

// 마우스 캡처 검사
bool bCap = MyWidget->HasMouseCapture();             // L639
bool bCapByUser = MyWidget->HasMouseCaptureByUser(0, -1);  // L648

// 커서
MyWidget->SetCursor(EMouseCursor::Hand);             // L570
MyWidget->ResetCursor();                             // L574

// 툴팁
MyWidget->SetToolTipText(LOCTEXT("Tip", "Hello"));  // L556 (FieldNotify 자동)
MyWidget->SetToolTip(MyCustomToolTipWidget);         // L563
FText T = MyWidget->GetToolTipText();                // L552
```

### 3.3 내비게이션

```cpp
// 모든 방향 한 번에
MyWidget->SetAllNavigationRules(EUINavigationRule::Explicit, FName("NextWidget"));  // L709

// 방향별
MyWidget->SetNavigationRule(EUINavigation::Right, EUINavigationRule::Stop, NAME_None);  // L719
MyWidget->SetNavigationRuleBase(EUINavigation::Up, EUINavigationRule::Wrap);            // L727
MyWidget->SetNavigationRuleExplicit(EUINavigation::Down, OtherWidget);                  // L735
MyWidget->SetNavigationRuleCustom(EUINavigation::Left, MyDelegate);                     // L743
MyWidget->SetNavigationRuleCustomBoundary(EUINavigation::Right, MyDelegate);            // L751
```

### 3.4 라이프사이클 검사

```cpp
bool bConstructed = MyWidget->IsConstructed();       // L856 — RebuildWidget() 후 true
bool bInViewport  = MyWidget->IsInViewport();        // L549
bool bRendered    = MyWidget->IsRendered();          // L578
bool bVisible     = MyWidget->IsVisible();           // L582
```

### 3.5 FieldNotification (MVVM)

```cpp
// FieldNotify 가 붙은 UPROPERTY 의 변경 알림 구독
MyWidget->K2_AddFieldValueChangedDelegate(            // L798 — BP 노출
    UWidget::FFieldNotificationClassDescriptor::Visibility,
    OnVisibilityChanged
);
MyWidget->K2_RemoveFieldValueChangedDelegate(...);    // L801
MyWidget->K2_BroadcastFieldValueChanged(...);         // L805 — 수동 broadcast (자체 Field 추가 시)

// C++ 측 인터페이스 (INotifyFieldValueChanged)
UE::FieldNotification::FFieldId Id =
    UWidget::FFieldNotificationClassDescriptor::Visibility;
MyWidget->AddFieldValueChangedDelegate(Id, ...);
```

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 핵심 4 virtual (가장 자주 override)

| 시그니처 | 위치 | 호출 시점 / 용도 |
|----------|------|------------------|
| `virtual void SynchronizeProperties()` | Widget.h L930 | **디테일 패널 변경/생성 직후** UPROPERTY → Slate 위젯에 반영. **런타임 setter 는 별도** — 자세히 §5.1. |
| `virtual TSharedRef<SWidget> RebuildWidget()` | Widget.h L1140 (protected) | UWidget 자손이 자기 SWidget 만드는 핵심. **새 UWidget 자손 작성 시 필수 override**. |
| `virtual void OnWidgetRebuilt()` | Widget.h | RebuildWidget 직후 — 이벤트 바인딩 등 후처리. |
| `virtual void ReleaseSlateResources(bool bReleaseChildren)` | Visual.h | SWidget 해제 시. 캐시된 위젯 핸들 정리. |

### 4.2 입력 / 콜백 (자주 override 안 함 — UUserWidget Native* 사용 권장)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void SetIsEnabled(bool)` | Widget.h L545 | 활성 변경 — override 시 추가 동작. |
| `virtual void SetVisibility(ESlateVisibility)` | Widget.h L590 | 가시성 변경. |

### 4.3 에디터 전용 🛠

| 시그니처 | 위치 | 가드 |
|----------|------|------|
| `inline bool IsDesignTime() const` 🛠 | Widget.h | `WITH_EDITOR` |
| `virtual TSharedRef<SWidget> RebuildDesignWidget(TSharedRef<SWidget>)` 🛠 | Widget.h | `WITH_EDITOR` — 디자이너 표시용 위젯 (게임 빌드와 다른 시각). |
| `TSharedRef<SWidget> CreateDesignerOutline(TSharedRef<SWidget>) const` 🛠 | Widget.h | `WITH_EDITOR` |
| `FText GetDisplayNameBase() const` 🛠 | Widget.h | `WITH_EDITOR` |
| `void SetDisplayLabel(const FString&)` 🛠 | Widget.h L973 | `WITH_EDITOR` |
| `void SetCategoryName(const FString&)` 🛠 | Widget.h L979 | `WITH_EDITOR` |

### 4.4 🚨 Super 호출 순서 — UWidget 측

UWidget 베이스에서는 **Native\* 라이프사이클이 없다** (그건 UUserWidget 전용). 그래도 override되는 4종의 Super 호출 순서는 정해져 있다.

| 가상 함수 | Super 호출 위치 | 베이스가 처리하는 구획 | 위반 시 증상 |
|-----------|----------------|----------------------|--------------|
| `RebuildWidget()` | **호출 안 함** (return SNew(...)) | UWidget 베이스는 SNullWidget 반환 — **반드시 자기 SWidget 생성해서 return** | Super 결과를 return하면 빈 위젯 생성 |
| `SynchronizeProperties()` | **첫 줄** (Super FIRST) | Visibility/Enabled/RenderTransform/RenderOpacity 등 공통 프로퍼티 → SWidget에 반영 | 가시성/활성/Transform 변경이 디자이너에서 즉시 반영 안 됨 |
| `OnWidgetRebuilt()` | **첫 줄** (Super FIRST) | (UWidget은 비어있음, UUserWidget이 BindWidget 매핑·NativeOnInitialized 등 처리) | UUserWidget 파생에서 BindWidget 비어있는 채로 사용자 코드 실행 |
| `ReleaseSlateResources(bReleaseChildren)` | **첫 줄** (Super FIRST) | 캐시된 Slate 핸들 정리(SafeWidget 약 참조 등) | 재빌드 시 옛 SWidget 핸들이 남아 GC 못 됨 |

> **새 UWidget 자손 작성 시**: §4.5 템플릿의 패턴(SynchronizeProperties / ReleaseSlateResources에서 Super FIRST) 그대로 따라야 부모(UWidget·UVisual)가 보장하는 공통 프로퍼티가 손실되지 않는다.

### 4.5 RebuildWidget 작성 패턴 (사용자 정의 UWidget)

```cpp
UCLASS()
class MYGAME_API UMyHealthBar : public UWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Percent = 1.f;

    UFUNCTION(BlueprintCallable)
    void SetPercent(float NewPercent);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void SynchronizeProperties() override;
    virtual void ReleaseSlateResources(bool bReleaseChildren) override;

private:
    TSharedPtr<SProgressBar> MyProgressBar;
};

TSharedRef<SWidget> UMyHealthBar::RebuildWidget()
{
    MyProgressBar = SNew(SProgressBar)
        .Percent(Percent);
    return MyProgressBar.ToSharedRef();
}

void UMyHealthBar::SynchronizeProperties()
{
    Super::SynchronizeProperties();    // 부모 동기화 먼저 (Visibility/Enabled 등)
    if (MyProgressBar.IsValid())
    {
        MyProgressBar->SetPercent(Percent);
    }
}

void UMyHealthBar::SetPercent(float NewPercent)   // ★ 런타임 setter
{
    Percent = FMath::Clamp(NewPercent, 0.f, 1.f);
    if (MyProgressBar.IsValid())
    {
        MyProgressBar->SetPercent(Percent);
        // ↑ Slate 측 setter 가 자동 Invalidate(EInvalidateWidgetReason::Paint) 호출
    }
}

void UMyHealthBar::ReleaseSlateResources(bool bReleaseChildren)
{
    Super::ReleaseSlateResources(bReleaseChildren);
    MyProgressBar.Reset();             // 약 참조로도 충분하지만 명시적 해제 권장
}
```

---

## 5. 🚨 인밸리데이션 / 갱신 흐름 (의무 섹션)

`UWidget` 의 갱신 시점은 **3가지 경로**가 있고, 각각 다른 트리거를 가진다. 혼동하면 디자이너 변경이 안 보이거나, 런타임 setter 가 무시되거나, 매 프레임 불필요한 페인트가 발생한다.

### 5.1 SynchronizeProperties — 디자이너/생성 시점

```
① 디자이너에서 UPROPERTY 변경
   → PostEditChangeProperty (CoreUObject/Editor)
   → SynchronizeProperties() 호출
② BP 위젯 생성 (CreateWidget<T>)
   → Construct → SynchronizeProperties()
③ 사용자가 RerunConstructionScript 같은 컨텍스트
   → SynchronizeProperties()
```

**한계** — `SynchronizeProperties` 는 위 3가지 시점에만 호출. **런타임에서 `MyWidget->Percent = 0.5f` 직접 대입은 SWidget 으로 전달 안 됨**. 반드시 setter (`SetPercent` 같은 사용자 정의 또는 `SetVisibility` 같은 표준) 를 거쳐야 인밸리데이션 발생.

### 5.2 표준 setter 의 자동 인밸리데이션 trigger

UWidget 의 각 표준 setter 는 내부적으로 적절한 `EInvalidateWidgetReason` 을 발행한다:

| setter | 자동 trigger reason | 비고 |
|--------|---------------------|------|
| `SetVisibility(ESlateVisibility)` | `Visibility` (Layout 함의) | + `FieldNotify` Broadcast |
| `SetIsEnabled(bool)` | `Paint` | + `FieldNotify` Broadcast |
| `SetToolTipText(FText)` | (인밸리데이션 없음) | + `FieldNotify` Broadcast |
| `SetRenderTransform(FWidgetTransform)` | `RenderTransform` | (Layout 변경 없음) |
| `SetRenderScale/Shear/Angle/Translation/Pivot` | `RenderTransform` | 동상 |
| `SetRenderOpacity(float)` | `Paint` | |
| `SetClipping(EWidgetClipping)` | `Layout` | |
| `SetPixelSnapping(EWidgetPixelSnapping)` | `Paint` | |
| `SetCursor(EMouseCursor::Type)` | (인밸리데이션 없음) | 다음 호버 시 적용 |
| `ForceVolatile(bool)` | `Volatility` | 캐시 비활성/재활성 |
| 사용자 정의 setter (예: `SetPercent`) | (자동 없음) | **수동으로 SWidget setter 호출 또는 Invalidate(...)** |

**핵심**: 사용자 정의 setter 작성 시 — Slate 측 setter 를 호출하거나, 없으면 직접 `Invalidate(reason)` 호출.

### 5.3 EWidgetVolatility / ForceVolatile

```cpp
MyWidget->ForceVolatile(true);           // L620 — 매 프레임 페인트 (SInvalidationPanel 캐시 비활성)
MyWidget->ForceVolatile(false);          // 휘발성 해제
```

**언제 사용** — 진짜 매 프레임 변하는 위젯 (전체 화면 GIF·실시간 그래프). `UInvalidationBox` 안에 휘발성 위젯이 있으면 캐시가 매 프레임 무효 → 오히려 손해.

`uint8 bIsVolatile:1` (Widget.h L388) 가 멤버 비트.

### 5.4 InvalidateLayoutAndVolatility — 레이아웃 캐싱 위젯에 신호

```cpp
MyWidget->InvalidateLayoutAndVolatility();   // L691
// → SInvalidationPanel/UInvalidationBox 가 이 위젯 영역의 캐시를 무효화
```

자식 위젯의 desired size 가 변했을 때 부모의 레이아웃 캐시를 무효화. UPanelWidget 의 슬롯 변경 시 자동.

### 5.5 ForceLayoutPrepass — 즉시 레이아웃 재계산

```cpp
MyWidget->ForceLayoutPrepass();           // L684
// → 이번 프레임 안에 ComputeDesiredSize 강제 호출
```

비싸다 — 사이즈를 즉시 알아야 하는 특수한 경우만 (애니메이션 시작 시 정확한 시작점 등).

### 5.6 5가지 핵심 원칙 (다시)

1. **`SynchronizeProperties`** 는 디자이너 변경/생성 시에만 호출 — **런타임 setter 는 별도로 인밸리데이션 트리거**.
2. **표준 setter 사용** — UWidget 의 표준 setter 는 자동으로 `EInvalidateWidgetReason` 발행. 직접 멤버 대입 금지.
3. **사용자 정의 setter** — Slate 측 setter 를 호출하거나, 없으면 `MyProgressBar->SetXxx(...)` 같이 위임. 정 안 되면 `Invalidate(reason)` 직접.
4. **`ForceVolatile(true)` 신중** — 진짜 매 프레임 변하는 경우만. `UInvalidationBox` 와 충돌 시 캐시 손해.
5. **`UCanvasPanelSlot::ZOrder`** ≠ Slate `LayerId` — 부모 패널의 자식 정렬용. `OnPaint` 안의 LayerId 와 혼동 금지.

자세한 인밸리데이션 reason 8종과 LayerId/DrawCall 가이드는 [`SlateCore/Drawing/`](../../SlateCore/references/Drawing.md) §4·§5.

---

## 6. 🚨 Focus / Navigation 시스템 (게임패드·키보드 내비)

UMG에서 **위젯 간 포커스 이동** (Tab/Shift+Tab/방향키/D-pad/스틱) 을 제어하는 시스템. 콘솔/모바일 컨트롤러 환경에서 필수. 모든 UWidget 자손이 자동으로 보유.

### 6.1 핵심 클래스 / 데이터

| 헤더 | 클래스/enum | 의미 |
|------|------------|------|
| `Components/Widget.h` L465 | `UWidget::Navigation` (UPROPERTY) | 위젯별 네비게이션 데이터 |
| `Blueprint/WidgetNavigation.h` L52 | `UWidgetNavigation : UObject` | 6방향 + RoutingPolicy + NavigationMethod 묶음 |
| `Blueprint/WidgetNavigation.h` L23 | `FWidgetNavigationData` (USTRUCT) | 1방향 — Rule + WidgetToFocus / Widget / CustomDelegate |
| `SlateCore/Public/Input/NavigationReply.h` L14 | `EUINavigationRule` (uint8) | **Escape / Explicit / Wrap / Stop / Custom / CustomBoundary / Invalid** |
| `SlateCore/Public/Types/SlateEnums.h` L98 | `EUINavigation` (uint8) | **Left / Right / Up / Down / Next / Previous** |
| `SlateCore/Public/Types/SlateEnums.h` L123 | `EUINavigationAction` | Accept / Back |
| `Blueprint/WidgetNavigation.h` (L80) | `EWidgetNavigationRoutingPolicy` | AcceptFocus / Routed / Stop |

### 6.2 EUINavigationRule 6종 의미

| Rule | 의미 |
|------|------|
| `Escape` | 기본 — 현재 컨테이너 밖으로 자동 검색 (Slate 기본 동작) |
| `Explicit` | 특정 위젯으로 명시 이동 |
| `Wrap` | 컨테이너 안에서 wrap-around (반대편으로) |
| `Stop` | 이 방향 이동 차단 |
| `Custom` | 사용자 정의 델리게이트 호출 |
| `CustomBoundary` | 컨테이너 boundary 도달 시에만 사용자 정의 |
| `Invalid` | 미정의 |

### 6.3 자주 쓰는 API (Widget.h)

| API | 라인 | 의미 |
|-----|------|------|
| `void SetAllNavigationRules(EUINavigationRule Rule, FName WidgetToFocus)` | L709 | 6방향 일괄 설정 |
| `void SetNavigationRuleBase(EUINavigation Direction, EUINavigationRule Rule)` | L727 | Escape/Wrap/Stop 같이 베이스 규칙만 |
| `void SetNavigationRuleExplicit(EUINavigation Direction, UWidget* InWidget)` | L735 | Explicit — 대상 위젯 직접 |
| `void SetNavigationRuleCustom(EUINavigation Direction, FCustomWidgetNavigationDelegate)` | L743 | Custom — 콜백 |
| `void SetNavigationRuleCustomBoundary(EUINavigation Direction, FCustomWidgetNavigationDelegate)` | L751 | CustomBoundary |
| `void SetNavigationMethod(const TInstancedStruct<FNavigationMethod>&)` | L757 | 5.x 새 NavigationMethod (TInstancedStruct) |
| `void BuildNavigation()` | L937 | 명시적 네비 트리 빌드 |
| `void SetNavigationRule(EUINavigation, EUINavigationRule, FName)` 🚨 | L719 | **DEPRECATED 4.23** — 위 4종으로 대체 |

> **⚠️ Deprecated 주의**: `SetNavigationRule` (단일 함수) 은 4.23 부터 deprecated. 신규 코드는 `SetNavigationRuleBase`/`Explicit`/`Custom`/`CustomBoundary` 4종 분리 사용.

### 6.4 사용 패턴

#### A. 기본 — 디자이너에서 Navigation 설정

UMG 디자이너의 위젯 디테일 패널 → "Navigation" 카테고리 → 6방향 (Up/Down/Left/Right/Next/Previous) 마다 Rule + 대상 위젯 설정. 가장 일반적 케이스. C++ 작업 불필요.

#### B. 런타임 명시 (특정 위젯으로 점프)

```cpp
void UMyMenuWidget::SetupCustomNav()
{
    if (StartButton && OptionsButton && QuitButton)
    {
        StartButton->SetNavigationRuleExplicit(EUINavigation::Down, OptionsButton);
        OptionsButton->SetNavigationRuleExplicit(EUINavigation::Up, StartButton);
        OptionsButton->SetNavigationRuleExplicit(EUINavigation::Down, QuitButton);
        QuitButton->SetNavigationRuleExplicit(EUINavigation::Up, OptionsButton);
        // wrap-around
        StartButton->SetNavigationRuleBase(EUINavigation::Up, EUINavigationRule::Wrap);
        QuitButton->SetNavigationRuleBase(EUINavigation::Down, EUINavigationRule::Wrap);
    }
}
```

#### C. Custom 델리게이트 (조건부 이동)

```cpp
// 헤더에서 UFUNCTION 선언
UFUNCTION()
UWidget* HandleCustomNav(EUINavigation Direction);

// Construct/NativeConstruct 안에서 바인드
FCustomWidgetNavigationDelegate Delegate;
Delegate.BindDynamic(this, &UMyMenuWidget::HandleCustomNav);
StartButton->SetNavigationRuleCustom(EUINavigation::Down, Delegate);

UWidget* UMyMenuWidget::HandleCustomNav(EUINavigation Direction)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(U