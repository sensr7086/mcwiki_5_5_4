---
name: slatecore-swidget
description: SWidget 베이스 - SLATE_BEGIN_ARGS + Construct + OnPaint + ComputeDesiredSize + ArrangeChildren + SLATE_NEW + SAssignNew + SCompoundWidget vs SLeafWidget.
---

# SlateCore / SWidget

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.5.4
> 다루는 영역: 위젯 베이스 사슬 (`SWidget`/`SCompoundWidget`/`SLeafWidget`/`SPanel`) + 선언 매크로(`SLATE_BEGIN_ARGS`/`SLATE_DECLARE_WIDGET`) + Construct 라이프사이클 + 입력/페인트 virtual + **TSlateAttribute 자동 인밸리데이션**
> 관련 sub-skill: [`Layout/`](../Layout/SKILL.md), [`Drawing/`](../Drawing/SKILL.md), [`Input/`](../Input/SKILL.md), [`Types/`](../Types/SKILL.md)

---

## 1. 개요

`SWidget`은 모든 Slate 위젯의 베이스다. 다음 4단계 사슬:

```
FSlateControlledConstruction
  └─ SWidget                       (Widgets/SWidget.h:153)
       ├─ SCompoundWidget          (SCompoundWidget.h:21)  ← 자식 1개 + ChildSlot
       ├─ SLeafWidget              (SLeafWidget.h:21)      ← 자식 없음 (STextBlock/SImage 부류)
       └─ SPanel                   (SPanel.h:22)           ← 자식 N개 + Slot 시스템
            └─ (구체 패널) SVerticalBox/SHorizontalBox/SOverlay 등
```

위젯은 **선언형**으로 만든다 — `SNew`/`SAssignNew` 매크로가 `Construct(const FArguments&)` 를 호출하며, 인자는 `SLATE_BEGIN_ARGS` 블록으로 정의된 구조체로 넘어온다. raw `new SWidget()` 금지.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Widgets/SWidget.h` | `class SWidget : FSlateControlledConstruction, TSharedFromThis<SWidget>` (L153) | 모든 Slate 위젯의 루트. `SLATE_DECLARE_WIDGET_API`. |
| `Public/Widgets/SCompoundWidget.h` | `class SCompoundWidget : SWidget` (L21) | 단일 자식 컨테이너. `ChildSlot` 패턴. UI 합성용 베이스. |
| `Public/Widgets/SLeafWidget.h` | `class SLeafWidget : SWidget` (L21) | 자식 없는 잎 위젯. `OnPaint`/`ComputeDesiredSize` 직접 구현. |
| `Public/Widgets/SPanel.h` | `class SPanel : SWidget` (L22) | 다중 자식 컨테이너. `OnArrangeChildren` 구현 필수. `FChildren* GetChildren()` 노출. |
| `Public/Widgets/DeclarativeSyntaxSupport.h` | `SLATE_BEGIN_ARGS` (L62), `SLATE_END_ARGS` (L115), `SLATE_ATTRIBUTE` (L193), `SLATE_ARGUMENT` (L209), `SLATE_NAMED_SLOT` (L438), `SLATE_DEFAULT_SLOT` (L445), `SLATE_EVENT` (L459) | 선언 매크로. |
| `Public/Widgets/SlateControlledConstruction.h` | `SLATE_DECLARE_WIDGET` (L19), `SLATE_IMPLEMENT_WIDGET` (L44) | 어트리뷰트 등록 매크로 — TSlateAttribute 시스템 진입점. |

### 2.1 선언 매크로 한 눈에

```cpp
SLATE_BEGIN_ARGS(SMyWidget)                      // 인자 구조체 시작
    : _Title()                                    // 기본값
    , _bEnabled(true)
    {}
    SLATE_ATTRIBUTE(FText, Title)                 // TAttribute<FText> _Title
    SLATE_ARGUMENT(bool, bEnabled)                // bool _bEnabled
    SLATE_EVENT(FOnClicked, OnClicked)            // FOnClicked _OnClicked
    SLATE_NAMED_SLOT(FArguments, HeaderContent)   // 외부에서 슬롯 주입
    SLATE_DEFAULT_SLOT(FArguments, Content)       // [ ] 안에 들어가는 기본 슬롯
SLATE_END_ARGS()
```

`Construct(const FArguments& InArgs)` 안에서 `InArgs._Title`, `InArgs._OnClicked.IsBound() ? ... : ...` 형태로 접근.

---

## 3. 라이프사이클 / Construct 흐름

```
SNew(SMyWidget).Title(...)                        ← FArguments 빌더 호출
   ↓ TSlateDecl 가 SMyWidget 생성
   ↓ Construct(InArgs) 호출
   ↓ ChildSlot[ ... ] / 자식 슬롯 채우기
   ↓ TSlateAttribute 멤버에 InArgs._Title.Assign(*this, ...)
   ↓ 위젯 트리에 부착되면 자동 페인트 사이클 진입
```

`Construct` 가 끝나면 위젯은 페인트/입력 사이클에 들어간다. 명시적인 `BeginPlay/EndPlay`는 없으며, 파괴는 `TSharedPtr<SWidget>` 의 마지막 참조가 사라질 때 일어난다.

`OnArrangeChildren`/`ComputeDesiredSize`/`OnPaint` 가 매 프레임 또는 인밸리데이션 후 호출된다.

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 레이아웃·페인트 (가장 자주 override)

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual int32 OnPaint(...) const = 0` | SWidget.h L1615 | 그리기. `OutDrawElements` 에 `FSlateDrawElement::Make*` 추가. 다음 LayerId 반환. |
| `virtual void OnArrangeChildren(const FGeometry&, FArrangedChildren&) const = 0` | SWidget.h L1624 | 자식 배치 — Panel/CompoundWidget. |
| `virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const = 0` | SWidget.h L722 | 위젯이 원하는 크기 — 부모 레이아웃 결정 입력. |
| `virtual FChildren* GetChildren() = 0` | SWidget.h L839 | 자식 리스트. Panel은 슬롯 컨테이너 반환. |
| `virtual FChildren* GetAllChildren()` | SWidget.h L847 | 시각적 자식 + 비-시각적 자식 (디버그용). |
| `virtual bool CustomPrepass(float LayoutScaleMultiplier)` | SWidget.h L701 | 커스텀 prepass 단계 — true 반환 시 기본 prepass 건너뜀. |

### 4.2 입력 (사용자 인터랙션)

`SWidget.h` 안에 `OnMouseButtonDown/Up/DoubleClick`, `OnMouseMove`, `OnMouseEnter/Leave`, `OnMouseWheel`, `OnDragDetected`, `OnKeyDown/Up`, `OnKeyChar`, `OnFocusReceived/Lost`, `OnFocusChanging`, `OnTouchStarted/Moved/Ended`, `OnNavigation`, `OnTooltipRequested` 등이 있다. **모두 `FReply` 또는 void 반환** — 자세한 패턴은 [`Input/`](../Input/SKILL.md).

### 4.3 인밸리데이션·휘발성

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual bool ComputeVolatility() const` | SWidget.h L1581 | 매 프레임 재페인트 필요한지 — true 반환 시 캐시 비활성. |
| `virtual bool Advanced_IsInvalidationRoot() const` | SWidget.h L1507 | 자신이 인밸리데이션 루트인지 (`SInvalidationPanel`만 true). |
| `virtual const FSlateInvalidationRoot* Advanced_AsInvalidationRoot() const` | SWidget.h L1508 | 위 캐스트. |
| `virtual bool Advanced_IsWindow() const` | SWidget.h L1506 | `SWindow` 자식만 true. |

### 4.4 검증·접근성

`virtual bool IsInteractable() const` (L937), `virtual bool ValidatePathToChild(SWidget*)` (L680), `virtual FChildren* Debug_GetChildrenForReflector()` (L854).

---

## 5. ⚡ TSlateAttribute 자동 인밸리데이션 (의무 섹션)

`TSlateAttribute<T, EInvalidateWidgetReason>` 는 **값 변경 시 자동으로 해당 invalidation reason을 위젯에 발행**한다 — 매번 `Invalidate()` 를 직접 부르는 구식 패턴을 대체한다.

```cpp
class SMyWidget : public SCompoundWidget
{
    SLATE_DECLARE_WIDGET(SMyWidget, SCompoundWidget)   // 어트리뷰트 등록 매크로

public:
    SLATE_BEGIN_ARGS(SMyWidget) : _Title() {}
        SLATE_ATTRIBUTE(FText, Title)
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs);

private:
    // Layout 인밸리데이션을 자동으로 트리거 (값이 바뀌면 ComputeDesiredSize 재계산)
    TSlateAttribute<FText, EInvalidateWidgetReason::Layout> Title;

    // Paint만 (사이즈 변화 없음 — 캐시 색상 변경 등)
    TSlateAttribute<FLinearColor, EInvalidateWidgetReason::Paint> Tint;
};
```

`SLATE_DECLARE_WIDGET` + `SLATE_IMPLEMENT_WIDGET` 페어가 필요한 이유: 멤버 어트리뷰트의 reason 정보를 정적으로 등록해 런타임 비용을 줄이기 위함.

### 5.1 `EInvalidateWidgetReason` 8종 + 합성 (`InvalidateWidgetReason.h:13`)

| 비트 | 값 | 언제 |
|------|----|------|
| `None` | 0 | 무효 |
| `Layout` | `1<<0` | 원하는 크기 변경 — **비싸다**. |
| `Paint` | `1<<1` | 그림만 바뀜 (사이즈 동일). |
| `Volatility` | `1<<2` | 휘발성 자체가 바뀜. |
| `ChildOrder` | `1<<3` | 자식 추가/제거 (Prepass + Layout 함의). |
| `RenderTransform` | `1<<4` | 렌더 변환만 바뀜. |
| `Visibility` | `1<<5` | 가시성 변경 (Layout 함의). |
| `AttributeRegistration` | `1<<6` | 어트리뷰트 바인딩/언바인딩 (`SlateAttributeMetaData` 내부 사용). |
| `Prepass` | `1<<7` | 자식 트리 desired size 재계산 (Layout 함의). |
| `PaintAndVolatility` | Paint\|Volatility | 보통 사용. |
| `LayoutAndVolatility` | Layout\|Volatility | 보통 사용. |

`ENUM_CLASS_FLAGS` 가 적용되어 비트 OR 가능. 직접 발행: `Invalidate(EInvalidateWidgetReason::Layout)`.

### 5.2 자주 만나는 함정

1. **raw 멤버 + 매번 `Invalidate()`** — 구식. `TSlateAttribute` 로 마이그레이션.
2. **`SetVolatile(true)` 남용** — 캐시 무력화. 정말 매 프레임 변하는 경우만 (전체 화면 GIF·실시간 그래프 등).
3. **`SInvalidationPanel` 안에 자주 변하는 위젯** — 캐시가 매 프레임 무효화돼 오히려 손해. 자세한 흐름은 [`Drawing/`](../Drawing/SKILL.md).
4. **인밸리데이션 누락** — 새 멤버 변수에 setter만 만들고 `Invalidate()` 안 부르면 변경이 화면에 반영 안 됨.

---

## 6. 예제

### 6.1 SCompoundWidget (가장 흔함)

```cpp
class SMyHeader : public SCompoundWidget
{
    SLATE_DECLARE_WIDGET(SMyHeader, SCompoundWidget)

public:
    SLATE_BEGIN_ARGS(SMyHeader) : _Title(), _OnClicked() {}
        SLATE_ATTRIBUTE(FText, Title)
        SLATE_EVENT(FOnClicked, OnClicked)
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs)
    {
        Title.Assign(*this, InArgs._Title);
        ChildSlot
        [
            SNew(SButton)
            .OnClicked(InArgs._OnClicked)
            [ SNew(STextBlock).Text(TAttribute<FText>::Create([this]{ return Title.Get(); })) ]
        ];
    }

private:
    TSlateAttribute<FText, EInvalidateWidgetReason::Layout> Title;
};

// .cpp 어딘가에 한 번:
SLATE_IMPLEMENT_WIDGET(SMyHeader)
```

### 6.2 SLeafWidget (잎 — 자체 그리기)

```cpp
class SColorBox : public SLeafWidget
{
public:
    SLATE_BEGIN_ARGS(SColorBox) : _Color(FLinearColor::White) {}
        SLATE_ATTRIBUTE(FLinearColor, Color)
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs)
    {
        Color = InArgs._Color;
        SetCanTick(false);                      // Tick 불필요
    }

protected:
    virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geo,
                          const FSlateRect& Cull, FSlateWindowElementList& Out,
                          int32 LayerId, const FWidgetStyle& Style, bool bEnabled) const override
    {
        FSlateDrawElement::MakeBox(Out, LayerId, Geo.ToPaintGeometry(),
                                   FCoreStyle::Get().GetBrush("WhiteBrush"),
                                   ESlateDrawEffect::None, Color.Get());
        return LayerId + 1;
    }

    virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(32, 32); }

private:
    TAttribute<FLinearColor> Color;
};
```

### 6.3 SPanel (다중 자식)

`SHorizontalBox`/`SVerticalBox` 등 표준 패널은 [`Slate/LayoutWidgets/`](../../Slate/references/LayoutWidgets.md) 에서 다룬다. 직접 SPanel을 만드는 경우는 드물다 — 대부분 표준 패널을 조합한다.

---

## 7. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `Debug_GetChildrenForReflector()` 🛠 | SWidget.h L854 | 디버그 빌드 | Slate Reflector 위젯이 사용. |
| `IsInteractable()` 의 일부 경로 🛠 | SWidget.h L937 | 접근성 (Accessibility) 가드 | `Public/Widgets/Accessibility/` 안에 별도 헤더. |
| Slate Insights 트레이스 통합 🛠 | (`Trace/`) | `UE_TRACE_ENABLED` | [`Trace/`](../Trace/SKILL.md) 참조. |

---

## 8. 관련 sub-skill

- [`Layout/`](../Layout/SKILL.md) — `FGeometry`/`FArrangedChildren`/`FChildren` 자세히
- [`Drawing/`](../Drawing/SKILL.md) — `OnPaint` 가 호출하는 `FSlateDrawElement` + 인밸리데이션 캐시 흐름
- [`Input/`](../Input/SKILL.md) — `FReply` 와 모든 `On*Event` 패턴
- [`Types/`](../Types/SKILL.md) — `TAttribute` / `TSlateAttribute` 시스템 본체
- [`Application/`](../Application/SKILL.md) — `FSlateApplicationBase::Tick` 이 위젯 사이클을 돌리는 흐름
