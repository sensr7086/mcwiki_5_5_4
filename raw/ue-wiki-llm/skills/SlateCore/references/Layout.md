---
name: slatecore-layout
description: Slate Layout 시스템 - FArrangedChildren + FGeometry + EHorizontalAlignment + EVerticalAlignment + SizeBox / Padding / Box.
---

# SlateCore / Layout

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.7.4
> 다루는 영역: 레이아웃 베이스 — `FGeometry`/`FArrangedChildren`/`FArrangedWidget`/`FChildren`/`EVisibility`/`FMargin`/`FSlateRect` + 슬롯 시스템 (`FSlotBase`/`TPanelChildren`)
> 관련 sub-skill: [`SWidget/`](../SWidget/SKILL.md), [`Drawing/`](../Drawing/SKILL.md), [`Types/`](../Types/SKILL.md)

---

## 1. 개요

Slate 레이아웃 파이프라인은 두 단계:

```
1. CacheDesiredSize   — bottom-up: 자식의 ComputeDesiredSize 들이 부모로 올라옴
2. OnArrangeChildren  — top-down: 부모가 FGeometry로 자식 위치/크기 결정 → FArrangedChildren에 push
```

각 위젯은 `OnPaint` 시 `FGeometry`(절대 위치 + 크기 + 스케일)와 `FSlateRect`(잘라내기) 를 받고, `FSlateDrawElement`를 누적한다.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Layout/Geometry.h` | `USTRUCT FGeometry` (L39) | 절대 위치 + 로컬 크기 + 스케일 + 옵션 렌더 변환. **불변 멤버** (HACK 주석 — 호환을 위해 const 유지). |
| `Public/Layout/PaintGeometry.h` | `FPaintGeometry` | `FGeometry::ToPaintGeometry()` 결과. 페인트 단계에서 사용. |
| `Public/Layout/SlateRect.h` | `FSlateRect` | 좌상-우하 사각형. 컬링·잘라내기. |
| `Public/Layout/SlateRotatedRect.h` | `FSlateRotatedRect` | 회전된 사각형 (RenderTransform 후). |
| `Public/Layout/ArrangedChildren.h` | `class FArrangedChildren` (L14) | `OnArrangeChildren` 결과 누적. `EVisibility` 필터 가능. |
| `Public/Layout/ArrangedWidget.h` | `FArrangedWidget` | 자식 위젯 + 그 자식의 `FGeometry` 쌍. |
| `Public/Layout/ChildrenBase.h` | `class FChildren` (L26) | 자식 컬렉션 추상. |
| `Public/Layout/Children.h` | `FCombinedChildren` (L18), `FNoChildren` (L148), `TWeakChild<S>` (L211), `TSingleWidgetChildrenWithSlot<Slot>` (L301), `TPanelChildren<Slot>` (L460), `TSlotlessChildren<S>` (L835), `TOneDynamicChild<S>` (L1027) | 패턴별 자식 컨테이너. **TPanelChildren이 가장 흔함**. |
| `Public/Layout/Visibility.h` | `struct EVisibility` (Visible/Collapsed/Hidden/HitTestInvisible/SelfHitTestInvisible/All) | 가시성 + 히트테스트 정책. **5가지 + 합성**. |
| `Public/Layout/Margin.h` | `struct FMargin` (L16) | 좌·상·우·하 패딩 (USTRUCT). |
| `Public/Layout/Clipping.h` | `EWidgetClipping` 등 | 자식 클리핑 정책. |
| `Public/Layout/FlowDirection.h` | `EFlowDirection` (LeftToRight/RightToLeft) | RTL 지원. |
| `Public/Layout/WidgetPath.h` | `FWidgetPath`, `FArrangedWidget` 사슬 | 입력/포커스 라우팅에 사용. |
| `Public/Layout/LayoutGeometry.h`, `LayoutUtils.h` | 레이아웃 보조 함수 | `ArrangeChildAlongAxis` 등. |
| `Public/Layout/WidgetSlotWithAttributeSupport.h` | `TWidgetSlotWithAttributeSupport<SlotType>` | TSlateAttribute 지원 슬롯 베이스. |
| `Public/SlotBase.h` | `class FSlotBase` (L13), `template TSlotBase<DerivedSlot>` (L121) | 모든 슬롯 베이스. CRTP. |
| `Public/Layout/BasicLayoutWidgetSlot.h` | `template TBasicLayoutWidgetSlot<...>` (L596), `class FBasicLayoutWidgetSlot` (L645) | 표준 슬롯 (Padding/HAlign/VAlign 보유). |
| `Public/Containers/ObservableArray.h` | `TObservableArray<T>` | 변경 알림 가능한 배열 (리스트뷰 등에서 사용). |

### 2.1 EVisibility 5종

| 값 | 그림 | 레이아웃 공간 | 히트테스트 |
|----|------|---------------|-----------|
| `Visible` | ✅ | ✅ | ✅ |
| `HitTestInvisible` | ✅ | ✅ | ❌ (자식까지 차단) |
| `SelfHitTestInvisible` | ✅ | ✅ | ❌ (자식은 통과) |
| `Hidden` | ❌ | ✅ (공간 차지) | ❌ |
| `Collapsed` | ❌ | ❌ (공간 0) | ❌ |
| `All` | (마스크용 — 필터 시) | | |

`Visibility` 변경은 `EInvalidateWidgetReason::Visibility` (Layout 함의)를 트리거.

---

## 3. 자주 쓰는 API

```cpp
// === FGeometry (위젯에 들어오는 매 프레임 정보) ===
virtual int32 OnPaint(const FPaintArgs&, const FGeometry& Geo, ...) const
{
    FVector2D Size = Geo.GetLocalSize();         // 로컬 크기
    FVector2D Abs  = Geo.GetAbsolutePosition();  // 절대 위치
    float Scale    = Geo.GetAccumulatedLayoutTransform().GetScale();

    FPaintGeometry PG = Geo.ToPaintGeometry();
    FPaintGeometry Inset = Geo.ToPaintGeometry(FMargin(8.f), FSlateLayoutTransform()); // 인셋

    // 자식 배치용 child geometry
    FGeometry Child = Geo.MakeChild(/*ChildSize=*/FVector2D(64,32),
                                    FSlateLayoutTransform(/*Translation=*/FVector2D(8,8)));
}

// === OnArrangeChildren (Panel) ===
virtual void OnArrangeChildren(const FGeometry& Geo, FArrangedChildren& Out) const
{
    for (int32 i = 0; i < Children.Num(); ++i)
    {
        const FSlot& S = Children[i];
        if (S.GetWidget()->GetVisibility() == EVisibility::Collapsed) continue;

        FVector2D ChildPos(/* 계산 */);
        FVector2D ChildSize(/* 계산 */);
        Out.AddWidget(FArrangedWidget(
            S.GetWidget(),
            Geo.MakeChild(ChildSize, FSlateLayoutTransform(ChildPos))
        ));
    }
}

// === ComputeDesiredSize (모든 위젯) ===
virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const
{
    return FVector2D(/* 콘텐츠 기반 자연 크기 */);
}

// === Children 접근 ===
virtual FChildren* GetChildren() override { return &Children; }    // TPanelChildren<FSlot>

// === FMargin ===
FMargin Pad(8.f);                                  // 모두 8
FMargin Pad2(4.f, 8.f);                           // 좌우 4, 상하 8
FMargin Pad4(L=2, T=4, R=6, B=8);                 // 4방향 개별

// === FSlateRect ===
FSlateRect Cull = FSlateRect(0, 0, 1920, 1080);
bool bIntersect = Cull.IntersectionWith(Other);
```

### 3.1 슬롯 패턴

```cpp
// 자식 패널 정의 — 표준 슬롯 사용
class SMyPanel : public SPanel
{
public:
    class FSlot : public TBasicLayoutWidgetSlot<FSlot>
    {
    public:
        FSlot() : TBasicLayoutWidgetSlot<FSlot>(HAlign_Fill, VAlign_Fill) {}
        // Padding/HAlign/VAlign 은 TBasicLayoutWidgetSlot 가 제공
        SLATE_SLOT_BEGIN_ARGS(FSlot, TBasicLayoutWidgetSlot<FSlot>)
        SLATE_SLOT_END_ARGS()
    };

    SLATE_BEGIN_ARGS(SMyPanel) {}
        SLATE_SLOT_ARGUMENT(FSlot, Slots)
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs) { Children.AddSlots(MoveTemp(const_cast<TArray<typename FSlot::FSlotArguments>&>(InArgs._Slots))); }

    virtual FChildren* GetChildren() override { return &Children; }

    virtual void OnArrangeChildren(const FGeometry& Geo, FArrangedChildren& Out) const override
    {
        // FSlot::Padding(), HAlign, VAlign 활용해 배치
    }

    virtual FVector2D ComputeDesiredSize(float) const override { /* ... */ }

private:
    TPanelChildren<FSlot> Children;
};
```

표준 패널들 (`SVerticalBox`/`SHorizontalBox`/`SUniformGridPanel` 등)은 [`Slate/LayoutWidgets/`](../../Slate/references/LayoutWidgets.md) 에서 다룬다.

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 SWidget 의 레이아웃 virtual

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual void OnArrangeChildren(const FGeometry&, FArrangedChildren&) const = 0` | SWidget.h L1659 | 자식 배치 (`Panel`/`CompoundWidget`). |
| `virtual FVector2D ComputeDesiredSize(float) const = 0` | SWidget.h L731 | 자연 크기 — 부모가 사용. |
| `virtual FChildren* GetChildren() = 0` | SWidget.h L856 | 자식 컬렉션. |
| `virtual bool CustomPrepass(float)` | SWidget.h L710 | 커스텀 prepass. |

### 4.2 FChildren 핵심 인터페이스 (`Public/Layout/ChildrenBase.h`)

```cpp
class FChildren {
public:
    virtual int32 Num() const = 0;
    virtual TSharedRef<SWidget> GetChildAt(int32 Index) = 0;
    virtual TSharedRef<const SWidget> GetChildAt(int32 Index) const = 0;
    // FSlot 접근 (Panel일 때):
    virtual FSlotBase& GetSlotAt(int32 Index) = 0;
    // ...
};
```

---

## 5. 예제

### 5.1 균등 배치 패널

```cpp
class SUniformPanel : public SPanel
{
public:
    using FSlot = FBasicLayoutWidgetSlot;

    SLATE_BEGIN_ARGS(SUniformPanel) {}
        SLATE_SLOT_ARGUMENT(FSlot, Slots)
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs)
    {
        Children.Reserve(InArgs._Slots.Num());
        for (auto& S : const_cast<TArray<FSlot::FSlotArguments>&>(InArgs._Slots))
            Children.AddSlot(MoveTemp(S));
    }

    virtual FChildren* GetChildren() override { return &Children; }

    virtual void OnArrangeChildren(const FGeometry& Geo, FArrangedChildren& Out) const override
    {
        const int32 N = Children.Num();
        if (N == 0) return;
        const FVector2D Total = Geo.GetLocalSize();
        const float W = Total.X / N;

        for (int32 i = 0; i < N; ++i)
        {
            const FSlot& S = Children[i];
            if (S.GetWidget()->GetVisibility() == EVisibility::Collapsed) continue;

            const FMargin M = S.GetPadding();
            const FVector2D ChildPos(W * i + M.Left, M.Top);
            const FVector2D ChildSize(W - M.Left - M.Right, Total.Y - M.Top - M.Bottom);
            Out.AddWidget(FArrangedWidget(
                S.GetWidget(),
                Geo.MakeChild(ChildSize, FSlateLayoutTransform(ChildPos))
            ));
        }
    }

    virtual FVector2D ComputeDesiredSize(float Scale) const override
    {
        FVector2D Sum(0.f);
        for (int32 i = 0; i < Children.Num(); ++i)
        {
            const FVector2D C = Children[i].GetWidget()->GetDesiredSize();
            Sum.X += C.X;
            Sum.Y = FMath::Max(Sum.Y, C.Y);
        }
        return Sum;
    }

private:
    TPanelChildren<FSlot> Children;
};
```

### 5.2 가시성 토글

```cpp
TWeakPtr<SWidget> WeakInventory = InventoryWidget;
auto Toggle = [WeakInventory]()
{
    if (TSharedPtr<SWidget> W = WeakInventory.Pin())
    {
        W->SetVisibility(W->GetVisibility() == EVisibility::Visible
                         ? EVisibility::Collapsed
                         : EVisibility::Visible);
        // 자동으로 EInvalidateWidgetReason::Visibility 발행 → 부모 Layout 재계산
    }
};
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `Hittest2_FromArray(...)` 🛠 | ArrangedChildren.h | (디버그·테스트 도우미) | 헤더 자체에 `@todo hittest2.0` 표시. 일반 코드에서 사용 안 함. |
| `WidgetPath.inl` 의 일부 디버그 경로 🛠 | (인라인) | 트레이스/디자이너 확인용 | 거의 내부 사용. |

런타임에서 안전한 API는 `FGeometry`/`FArrangedChildren`/`FChildren`/`EVisibility`/`FMargin` 전부.

---

## 7. 관련 sub-skill

- [`SWidget/`](../SWidget/SKILL.md) — `OnArrangeChildren`/`ComputeDesiredSize` virtual 본체
- [`Drawing/`](../Drawing/SKILL.md) — `FGeometry::ToPaintGeometry()` 가 `FSlateDrawElement` 의 좌표
- [`Types/`](../Types/SKILL.md) — `TAttribute<EVisibility>` 등 어트리뷰트 가시성
- [`Input/`](../Input/SKILL.md) — `FWidgetPath` 가 입력 라우팅에 사용
