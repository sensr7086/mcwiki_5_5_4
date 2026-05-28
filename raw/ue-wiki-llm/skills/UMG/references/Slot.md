---
name: umg-slot
description: UPanelSlot + UCanvasPanelSlot + UHorizontalBoxSlot + UVerticalBoxSlot + UOverlaySlot + Anchors + Alignment.
---

# UMG · Slot sub-skill

> **모듈**: UMG (Tier 3 · Slate 카테고리)
> **위치**: `Engine/Source/Runtime/UMG/Public/Components/PanelSlot.h` + `*Slot.h`
> **다루는 범위**: `UPanelSlot` 베이스 + 각 패널의 자식별 프로퍼티 슬롯 (UVerticalBoxSlot / UCanvasPanelSlot / UOverlaySlot / 등 18개+).

---

## 1. 개요

UMG의 **자식별 배치 프로퍼티**는 부모 패널이 아니라 **슬롯**(`UPanelSlot` 자손)에 보관된다. `UPanelWidget::AddChild(UWidget*) → UPanelSlot*` 가 슬롯 인스턴스를 생성·반환하며, 각 패널은 자기 타입의 슬롯 (`UVerticalBoxSlot`, `UCanvasPanelSlot` 등) 을 사용. 슬롯의 `UPROPERTY` 는 디테일 패널에 노출되며, 변경 시 `SynchronizeProperties()` → 대응하는 Slate 측 슬롯 (`SVerticalBox::Slot()` 등) 에 반영.

> Slate 측 슬롯(`SBoxPanel::FSlot` 등)은 [`SlateCore/references/Layout.md §3.3`](../../SlateCore/references/Layout.md) 참조.

---

## 2. 핵심 헤더와 클래스

### 2.1 베이스 사슬

```
UVisual (Visual.h)
└── UPanelSlot (PanelSlot.h L12)
    ├── UVerticalBoxSlot          VerticalBoxSlot.h
    ├── UHorizontalBoxSlot        HorizontalBoxSlot.h
    ├── UStackBoxSlot             StackBoxSlot.h
    ├── UWrapBoxSlot              WrapBoxSlot.h
    ├── UCanvasPanelSlot          CanvasPanelSlot.h    ★ Anchor/Offset/ZOrder
    ├── UOverlaySlot              OverlaySlot.h
    ├── UGridSlot                 GridSlot.h
    ├── UUniformGridSlot          UniformGridSlot.h
    ├── UScrollBoxSlot            ScrollBoxSlot.h
    ├── UWidgetSwitcherSlot       WidgetSwitcherSlot.h
    ├── UScaleBoxSlot             ScaleBoxSlot.h
    ├── USizeBoxSlot              SizeBoxSlot.h
    ├── USafeZoneSlot             SafeZoneSlot.h
    ├── UButtonSlot               ButtonSlot.h         (UContentWidget)
    ├── UBorderSlot               BorderSlot.h         (UContentWidget)
    ├── UBackgroundBlurSlot       BackgroundBlurSlot.h
    └── UWindowTitleBarAreaSlot   WindowTitleBarAreaSlot.h
```

### 2.2 UPanelSlot 베이스 (`PanelSlot.h` L12)

```cpp
class UPanelSlot : public UVisual
{
    UPROPERTY(Instanced) UPanelWidget* Parent;
    UPROPERTY(Instanced) UWidget* Content;

    // 핵심 virtual
    virtual void ReleaseSlateResources(bool bReleaseChildren) override;
    virtual void SynchronizeProperties();
    virtual void PostEditChangeProperty(struct FPropertyChangedEvent& PropertyChangedEvent) override;
    virtual bool NudgeByDesigner(const FVector2D& NudgeDirection, const TOptional<int32>& GridSnapSize) { return false; }
    virtual bool DragDropPreviewByDesigner(const FVector2D& LocalCursorPosition, const TOptional<int32>& XGridSnapSize, const TOptional<int32>& YGridSnapSize) { return false; }
    virtual void SynchronizeFromTemplate(const UPanelSlot* const TemplateSlot) {};
};
```

---

## 3. 자주 쓰는 슬롯별 API

### 3.1 UVerticalBoxSlot / UHorizontalBoxSlot / UStackBoxSlot

| API | 메모 |
|-----|------|
| `void SetSize(FSlateChildSize)` | Auto / Fill (계수 포함) |
| `void SetPadding(FMargin)` | |
| `void SetHorizontalAlignment(EHorizontalAlignment)` | Left/Center/Right/Fill |
| `void SetVerticalAlignment(EVerticalAlignment)` | Top/Center/Bottom/Fill |

`FSlateChildSize`:
- `FSlateChildSize(ESlateSizeRule::Automatic)` → Auto
- `FSlateChildSize(ESlateSizeRule::Fill, 1.0f)` → Fill 비율 1
- `FSlateChildSize(ESlateSizeRule::Fill, 2.0f)` → Fill 비율 2 (다른 Fill 자식의 2배)

### 3.2 UCanvasPanelSlot — 가장 복잡

| API | 메모 |
|-----|------|
| `void SetAnchors(FAnchors)` | Min/Max (각 0~1 또는 동일값으로 점 anchor) |
| `void SetOffsets(FMargin)` | Left/Top/Right/Bottom — Anchor 기준 오프셋 |
| `void SetAlignment(FVector2D)` | 위젯 자체의 정렬 기준점 (0~1) |
| `void SetSize(FVector2D)` | (AutoSize=false 일 때) |
| `void SetAutoSize(bool)` | true → DesiredSize 사용 |
| `void SetZOrder(int32)` | 같은 레이어 내 정렬 |
| `void SetMinimum(FVector2D)` / `SetMaximum(FVector2D)` | Anchor 직접 설정 (편의) |
| `void SetPosition(FVector2D)` | Offset Left/Top 동시 |

**Anchor 패턴**:
- `FAnchors(0, 0)` → 좌상단 점 anchor (Position+Size 사용)
- `FAnchors(1, 1)` → 우하단 점 anchor
- `FAnchors(0.5)` → 중앙 점
- `FAnchors(0, 0, 1, 1)` → 부모 전체 (Stretch)

### 3.3 UOverlaySlot

| API | 메모 |
|-----|------|
| `void SetPadding(FMargin)` | |
| `void SetHorizontalAlignment(EHorizontalAlignment)` | |
| `void SetVerticalAlignment(EVerticalAlignment)` | |

Z-order는 자식 추가 순서. 변경하려면 `RemoveChildAt` + `AddChild`.

### 3.4 UGridSlot / UUniformGridSlot

`UGridSlot`:

| API | 메모 |
|-----|------|
| `void SetRow(int32)` / `GetRow() const` | |
| `void SetColumn(int32)` / `GetColumn() const` | |
| `void SetRowSpan(int32)` / `SetColumnSpan(int32)` | 셀 병합 |
| `void SetLayer(int32)` | Z-order |
| `void SetNudge(FVector2D)` | 픽셀 단위 미세 조정 |
| `void SetPadding(FMargin)` / `SetHorizontalAlignment` / `SetVerticalAlignment` | |

`UUniformGridSlot`:

| API | 메모 |
|-----|------|
| `void SetRow(int32)` / `SetColumn(int32)` | |
| `void SetHorizontalAlignment` / `SetVerticalAlignment` | |

### 3.5 UScrollBoxSlot

| API | 메모 |
|-----|------|
| `void SetPadding(FMargin)` | |
| `void SetHorizontalAlignment` / `SetVerticalAlignment` | |

### 3.6 UWrapBoxSlot

| API | 메모 |
|-----|------|
| `void SetPadding(FMargin)` | |
| `void SetFillEmptySpace(bool)` | true → 줄의 남는 공간 채움 |
| `void SetFillSpanWhenLessThan(float)` | |
| `void SetHorizontalAlignment` / `SetVerticalAlignment` | |

### 3.7 UButtonSlot / UBorderSlot — UContentWidget 슬롯

| API | 메모 |
|-----|------|
| `void SetPadding(FMargin)` | |
| `void SetHorizontalAlignment` / `SetVerticalAlignment` | |

### 3.8 UScaleBoxSlot / USizeBoxSlot / USafeZoneSlot

`UScaleBoxSlot` / `USizeBoxSlot`:

| API | 메모 |
|-----|------|
| `void SetPadding(FMargin)` | |
| `void SetHorizontalAlignment` / `SetVerticalAlignment` | |

`USafeZoneSlot`:

| API | 메모 |
|-----|------|
| `void SetIsTitleSafe(bool)` | true → TitleSafe / false → ActionSafe |

### 3.9 UWidgetSwitcherSlot

| API | 메모 |
|-----|------|
| `void SetPadding(FMargin)` | |
| `void SetHorizontalAlignment` / `SetVerticalAlignment` | |

> 디자이너에서 `UWidgetSwitcher::SetActiveWidgetIndex(int32)` 또는 `SetActiveWidget(UWidget*)` 로 자식 전환.

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 UPanelSlot 베이스 virtual

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `virtual void SynchronizeProperties()` | (override 시 자체 처리) | UPROPERTY → Slate 측 슬롯 동기화 |
| `virtual void ReleaseSlateResources(bool) override` | **FIRST** | Slate 슬롯 해제 |
| `virtual void PostEditChangeProperty(FPropertyChangedEvent&) override` 🛠 | **FIRST** | 디자이너 변경 |
| `virtual bool NudgeByDesigner(FVector2D, TOptional<int32>)` 🛠 | (선택) | 화살표 키 미세 이동 |
| `virtual bool DragDropPreviewByDesigner(FVector2D, TOptional<int32>, TOptional<int32>)` 🛠 | (선택) | 드래그 미리보기 |
| `virtual void SynchronizeFromTemplate(const UPanelSlot* const)` | (선택) | 템플릿 슬롯 → 인스턴스 복사 |

### 4.2 사용자 정의 슬롯 작성 패턴

```cpp
UCLASS()
class UMyCustomBoxSlot : public UPanelSlot
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Layout")
    FMargin Padding;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Layout")
    float Weight = 1.0f;

    UFUNCTION(BlueprintCallable) void SetPadding(FMargin InPadding);
    UFUNCTION(BlueprintCallable) void SetWeight(float InWeight);

    virtual void SynchronizeProperties() override
    {
        if (Slot)                        // SMyBoxPanel::FSlot* (ID는 사용자 정의 SPanel 측 슬롯)
        {
            Slot->SetPadding(Padding);
            Slot->SetWeight(Weight);
        }
    }

    virtual void ReleaseSlateResources(bool bReleaseChildren) override
    {
        Super::ReleaseSlateResources(bReleaseChildren);    // ← FIRST
        Slot = nullptr;
    }

    SMyBoxPanel::FSlot* Slot = nullptr;     // 비-UObject 핸들 (SWeakWidget 패턴)
};

void UMyCustomBoxSlot::SetPadding(FMargin InPadding)
{
    Padding = InPadding;
    if (Slot) { Slot->SetPadding(InPadding); }    // ← Slate setter 가 자동 Invalidate(Layout)
}
```

대응 패널 측:

```cpp
TSharedRef<SWidget> UMyCustomBoxPanel::RebuildWidget()
{
    MyPanel = SNew(SMyBoxPanel);
    for (int32 i = 0; i < GetChildrenCount(); i++)
    {
        if (UMyCustomBoxSlot* TypedSlot = Cast<UMyCustomBoxSlot>(Slots[i]))
        {
            TypedSlot->Slot = &MyPanel->AddSlot()
                .Padding(TypedSlot->Padding)
                .Weight(TypedSlot->Weight)
                [TypedSlot->Content->TakeWidget()];
        }
    }
    return MyPanel.ToSharedRef();
}

UClass* UMyCustomBoxPanel::GetSlotClass() const
{
    return UMyCustomBoxSlot::StaticClass();    // ← 이 패널이 사용할 슬롯 타입
}
```

> **Super 호출 규약**: [`04_OverrideIndex.md §6.4`](../../../references/04_OverrideIndex.md). `SynchronizeProperties` 는 슬롯 베이스에서는 비어있어도 부모 `UVisual`/`UObject` 의 동기화가 추후 추가될 수 있으니 사용자 정의 시 `Super` 호출 권장.

---

## 5. 🚨 인밸리데이션 / 갱신 흐름 (의무 섹션)

### 5.1 슬롯 setter 자동 인밸리데이션

표준 슬롯의 `SetPadding`/`SetSize`/`SetHorizontalAlignment`/`SetVerticalAlignment` 등은 내부 SXxx::FSlot setter 호출 → **자동 `Invalidate(EInvalidateWidgetReason::Layout)`**. 매 프레임 호출하면 매 프레임 레이아웃 재계산.

### 5.2 디자이너 vs 런타임 동기화 차이

| 시점 | 슬롯 동기화 |
|------|------------|
| 디자이너 패널 변경 | `PostEditChangeProperty` → `SynchronizeProperties` → 즉시 SXxx::FSlot 갱신 |
| `CreateWidget<T>` 후 `AddChild` | `AddChild` 가 슬롯 인스턴스 + `RebuildWidget`/`SynchronizeProperties` 호출 |
| 런타임 `SetXxx` 호출 | 슬롯 setter 가 SXxx::FSlot 직접 갱신 + 자동 Invalidate |
| 슬롯 UPROPERTY 직접 수정 (`Slot->Padding = ...`) | **갱신 안 됨** — 반드시 `SetPadding(...)` 호출 |

### 5.3 Anchor 매 프레임 변경 함정

```cpp
// ❌ 매 프레임 Anchor 갱신
void NativeTick(...)
{
    Super::NativeTick(...);
    UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(MyMinimap->Slot);
    Slot->SetAnchors(FAnchors(GetCursorRelativeAnchor()));
    // → 매 프레임 Layout Invalidate → 부모 InvalidationBox 캐시 무효
}

// ✅ TSlateAttribute 활용 (자동 인밸리데이션)
// CanvasPanel 자체에 UPROPERTY(EditAnywhere) FAnchors DynamicAnchors;
// 디자이너에서 binding으로 동적 anchor 설정
```

자세한 hotspot은 [`06_InvalidationHotspots.md §2.5 / §3`](../../../references/06_InvalidationHotspots.md).

---

## 6. 예제

### 6.1 UCanvasPanelSlot 동적 Anchor 변경 (ScreenToWorld)

```cpp
void UMyHUDWidget::PinIconTo3DLocation(UWidget* PinIcon, FVector WorldLocation)
{
    if (UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(PinIcon->Slot))
    {
        FVector2D ScreenPos;
        if (UGameplayStatics::ProjectWorldToScreen(GetOwningPlayer(), WorldLocation, ScreenPos))
        {
            Slot->SetAnchors(FAnchors(0, 0));         // 좌상단 점 anchor
            Slot->SetAlignment(FVector2D(0.5, 0.5));  // 위젯 중심 기준
            Slot->SetPosition(ScreenPos);
        }
    }
}
```

### 6.2 UVerticalBoxSlot — Fill 비율 설정

```cpp
UVerticalBoxSlot* TopSlot = ItemBox->AddChildToVerticalBox(HeaderWidget);
TopSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
TopSlot->SetPadding(FMargin(0, 0, 0, 8));

UVerticalBoxSlot* MiddleSlot = ItemBox->AddChildToVerticalBox(BodyWidget);
MiddleSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill, 1.0f));   // 남는 공간 모두

UVerticalBoxSlot* BottomSlot = ItemBox->AddChildToVerticalBox(FooterWidget);
BottomSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
```

### 6.3 UGridSlot — 셀 병합

```cpp
UGridSlot* TitleSlot = GridPanel->AddChildToGrid(TitleText, /*Row=*/0, /*Column=*/0);
TitleSlot->SetColumnSpan(3);     // 3개 컬럼 병합
TitleSlot->SetHorizontalAlignment(HAlign_Center);

UGridSlot* IconSlot = GridPanel->AddChildToGrid(IconImage, 1, 0);
UGridSlot* NameSlot = GridPanel->AddChildToGrid(NameText, 1, 1);
UGridSlot* CountSlot = GridPanel->AddChildToGrid(CountText, 1, 2);
```

---

## 7. 운영 가이드 / 함정

| 함정 | 회피 |
|------|------|
| 슬롯 UPROPERTY 직접 수정 (`Slot->Padding = ...`) | 반드시 `SetPadding(...)` 호출 (자동 Invalidate) |
| Anchor 매 프레임 변경 | TSlateAttribute (Slate 측 자동 인밸리데이션) |
| `SetSize(FSlateChildSize::Fill)` 의 비율 의미 혼동 | 모든 Fill 자식의 비율 합 → 비율로 분배 |
| `UCanvasPanelSlot::SetAutoSize(true)` 후 Size 무시 | AutoSize 상태에서는 DesiredSize 가 크기 결정 |
| `UScrollBoxSlot::SetVerticalAlignment` 무시 | ScrollBox는 자식 정렬을 지원하지 않을 수 있음 — 자식 위젯 측에서 정렬 |
| 부모 패널 타입과 다른 슬롯 캐스팅 | `Cast<UCanvasPanelSlot>` 등 `if` 검사 |
| `AddChild` 반환값 무시 | 반환된 `UPanelSlot*` 을 즉시 캐스팅 + 설정 |
| 디자이너에서 슬롯 변경 안 보임 | `PostEditChangeProperty` override 시 Super FIRST 호출 |

---

## 8. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 가드 |
|------|------|
| `UPanelSlot::PostEditChangeProperty` 🛠 | `WITH_EDITOR` |
| `UPanelSlot::NudgeByDesigner` 🛠 | `WITH_EDITOR` (디자이너 화살표 미세 이동) |
| `UPanelSlot::DragDropPreviewByDesigner` 🛠 | `WITH_EDITOR` |
| `UPanelSlot::SynchronizeFromTemplate` 🛠 | (디자이너 템플릿 복사) |

자세한 에디터 전용 통합은 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md).

---

## 9. 관련 sub-skill

- [`UMG/UWidget`](../UWidget/SKILL.md) — UWidget·UVisual 베이스
- [`UMG/PanelWidgets`](../PanelWidgets/SKILL.md) — 각 패널의 자식 추가 헬퍼 (`AddChildToVerticalBox` 등)
- [`UMG/StandardWidgets`](../StandardWidgets/SKILL.md) — 자식으로 들어가는 표준 위젯
- [`SlateCore/Layout`](../../SlateCore/references/Layout.md) — SBoxPanel::FSlot / SCanvas::FSlot 등 Slate 측 슬롯
- [`04_OverrideIndex.md §6.4`](../../../references/04_OverrideIndex.md) — UPanelSlot Super 호출 규약
- [`06_InvalidationHotspots.md §2.5`](../../../references/06_InvalidationHotspots.md) — 슬롯 setter 매 프레임 호출 hotspot
