---
name: slatecore-main
description: Tier 3 SlateCore 모듈 메인 — SWidget + Layout + Drawing + Styling + Input + Application + Animation + Text + Types + Trace 🛠 10개 sub-skill 인덱스. SWidget 베이스 + 인밸리데이션 + 패인트 사이클.
---

# SlateCore — 모듈 진입점

> Tier 3 · L4 (UI 인프라) · UE 5.7.4 기준
> 위치: `Engine/Source/Runtime/SlateCore/`
> 의존: **Public** Core, CoreUObject, DeveloperSettings, InputCore, Json, TraceLog (+ ApplicationCore — `bCompileAgainstApplicationCore`)
> 출처: `SlateCore.Build.cs` 직접 확인
>
> **상위 인덱스**: [`../../references/03_WikiHarness.md`](../../references/03_WikiHarness.md) 의 시나리오 표 (`§3.12 새 SWidget·UMG 위젯 작성`).

---

## 1. 개요

`SlateCore`는 UE의 **저수준 선언형 UI 코어**다. 위젯 베이스(`SWidget`), 레이아웃 계산(`FGeometry`/`FArrangedChildren`), 페인팅(`FSlateDrawElement`/`FSlateBrush`), 입력 라우팅(`FReply`/`FInputEvent`), 스타일 시스템(`FSlateStyleSet`), 폰트 셰이핑(HarfBuzz/FreeType 통합), Slate 어트리뷰트(`TSlateAttribute`/`TAttribute`)를 제공한다. 표준 위젯 라이브러리(`SButton`/`STextBlock`/`SListView` 등)는 상위의 `Slate` 모듈에 있고, BP 노출 위젯은 그 위 `UMG`에 있다.

```
SlateCore (이 모듈)
  └─ Slate (표준 위젯 + FSlateApplication)
        └─ UMG (UWidget BP 노출 + UWidgetTree)
```

핵심 빌드 정의:

- `WITH_FREETYPE` — FreeType 폰트 렌더링 (서버 빌드 0).
- `WITH_HARFBUZZ` — 텍스트 셰이핑 (서버 빌드 0).
- `UE_REPORT_SLATE_VECTOR_DEPRECATION=1` — 옛 `FVector2D` 좌표 사용 시 경고.

---

## 2. 의존·빌드 (`SlateCore.Build.cs` 요약)

```text
PublicDependencyModuleNames  : Core, CoreUObject, DeveloperSettings, InputCore, Json, TraceLog
                              (+ ApplicationCore — bCompileAgainstApplicationCore)
ThirdParty (Public)          : FreeType2, HarfBuzz, Nanosvg, ICU, XInput(Win64)
PrivateDefinitions           : UE_REPORT_SLATE_VECTOR_DEPRECATION=1
```

서버 타깃에서는 폰트/셰이핑 third-party가 빠진다 (`Target.Type == TargetType.Server`).

---

## 3. 자주 쓰는 API (1줄 요약 — 상세는 각 sub-skill)

```cpp
// 위젯 생성 (선언형 — Widgets/DeclarativeSyntaxSupport.h)
TSharedRef<SWidget> W = SNew(SBorder)
    .BorderImage(FAppStyle::GetBrush("Border"))
    [
        SNew(STextBlock).Text(LOCTEXT("Hello", "Hello"))
    ];

TSharedPtr<SButton> ButtonPtr;
auto Box = SNew(SVerticalBox)
    + SVerticalBox::Slot().AutoHeight()
    [
        SAssignNew(ButtonPtr, SButton)        // 핸들 보존
        .OnClicked_Lambda([](){ return FReply::Handled(); })
    ];

// FReply 패턴 (Input/SKILL.md 참조)
FReply Reply = FReply::Handled();
Reply = FReply::Unhandled();

// TAttribute / TSlateAttribute
TAttribute<FText> Lazy = TAttribute<FText>::CreateLambda([](){ return SomeText(); });
```

상세 시그니처·오버로드·사용 패턴은 다음 sub-skill에서 다룬다.

---

## 4. 사용 예제 (SCompoundWidget 골격)

```cpp
// SMyPanel.h
class SMyPanel : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SMyPanel)
        : _Title()
        {}
        SLATE_ATTRIBUTE(FText, Title)
        SLATE_EVENT(FOnClicked, OnButtonClicked)
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs);

private:
    TAttribute<FText> Title;
};

// SMyPanel.cpp
void SMyPanel::Construct(const FArguments& InArgs)
{
    Title = InArgs._Title;

    ChildSlot
    [
        SNew(SVerticalBox)
        + SVerticalBox::Slot().AutoHeight()
        [
            SNew(STextBlock).Text(Title)
        ]
        + SVerticalBox::Slot().AutoHeight()
        [
            SNew(SButton).OnClicked(InArgs._OnButtonClicked)
            [ SNew(STextBlock).Text(LOCTEXT("Click", "Click me")) ]
        ]
    ];
}
```

- `SLATE_BEGIN_ARGS`/`SLATE_END_ARGS` — 선언적 인자 구조체. `_FieldName` 형태로 멤버 노출.
- `SLATE_ATTRIBUTE(Type, Name)` — `TAttribute<Type>` 인자.
- `SLATE_EVENT(DelegateType, Name)` — 이벤트 핸들러 인자.
- `SLATE_ARGUMENT(Type, Name)` — 단순 값 인자.

---

## 5. Sub-skill 인덱스

SlateCore의 클래스·virtual·예제는 다음 10개 sub-skill로 분산되어 있다. 각 sub-skill은 *개요 → 핵심 헤더/클래스 → 자주 쓰는 API → virtual → 예제 → 에디터 전용 → 관련 sub-skill* 일관 7섹션 구조.

| # | Sub-skill | 다루는 영역 | 주요 헤더/심볼 |
|---|-----------|-------------|----------------|
| 1 | [`SWidget/`](./SWidget/SKILL.md) | 위젯 베이스 사슬·SLATE_DECLARE_WIDGET·SLATE_BEGIN_ARGS·Construct·라이프사이클 | `Widgets/SWidget.h`, `SCompoundWidget.h`, `SLeafWidget.h`, `SPanel.h`, `DeclarativeSyntaxSupport.h` |
| 2 | [`Layout/`](./Layout/SKILL.md) | FGeometry·FArrangedChildren·FMargin·FChildren·EVisibility·SlotBase | `Layout/*`, `SlotBase.h`, `Containers/*` |
| 3 | [`Drawing/`](./Drawing/SKILL.md) | FSlateDrawElement·FPaintArgs·FSlateBrush·FSlateRenderTransform·텍스처·Invalidation | `Rendering/*`, `Brushes/*`, `Textures/*`, `FastUpdate/*` |
| 4 | [`Styling/`](./Styling/SKILL.md) | FSlateStyleSet·FSlateColor·FSlateBrush·FSlateWidgetStyle·USlateWidgetStyleAsset 🛠 일부 | `Styling/*` |
| 5 | [`Input/`](./Input/SKILL.md) | FReply·FInputEvent·FPointerEvent·FKeyEvent·FFocusEvent·FNavigationConfig | `Input/*` |
| 6 | [`Application/`](./Application/SKILL.md) | ISlateApplicationBase·FSlateApplicationBase·FSlateUser·SWindow 베이스 | `Application/*` |
| 7 | [`Animation/`](./Animation/SKILL.md) | Slate 자체 트위닝 — FCurveSequence·FCurveHandle·SlateClipping (호버/페이드 등 단순 커브) | `Animation/*` |
| 8 | [`Text/`](./Text/SKILL.md) | FSlateFontInfo·IRun·ITextLayoutMarshaller·FontCache·HarfBuzz/FreeType 통합 | `Fonts/*` |
| 9 | [`Types/`](./Types/SKILL.md) | TAttribute·TSlateAttribute·TSlateDelegates·SlateEnums·SlateStructs·ISlateMetaData·WidgetActiveTimer | `Types/*` |
| 10 | [`Trace/`](./Trace/SKILL.md) | FSlateTrace·SlateDebugging·Insights 통합 (Slate Insights Profiler) 🛠 | `Trace/*`, `Debugging/*` |

> **UMG의 `UWidgetAnimation`(MovieScene 기반 시퀀서 통합)은 본 위키에서 제외** — 향후 `LevelSequence`/`MovieScene` 모듈 위키에서 통합적으로 다룬다. 본 sub-skill의 [`Animation/`](./Animation/SKILL.md) 은 SlateCore의 단순 커브 시스템(`FCurveSequence`/`FCurveHandle` — 위젯 호버·페이드·슬라이드 등)만 다루며, MovieScene과 무관하다.
> Sound 폴더는 `FSlateSound` 만 있어 작아 별도 sub-skill로 두지 않고 [`Drawing/`](./Drawing/SKILL.md) 또는 [`Styling/`](./Styling/SKILL.md) 안에서 다룬다.

### 5.1 ⚡ 공통 강조 — 인밸리데이션 / 갱신 흐름

Slate · UMG 성능의 핵심은 **인밸리데이션 시스템**이다. 다음 sub-skill 들은 인밸리데이션 흐름을 **각자의 관점에서 별도 섹션으로 의무 기술**한다 (sub-skill 작성 시 누락 금지):

| 위치 | 다룰 항목 |
|------|-----------|
| **이 모듈** [`Drawing/`](./Drawing/SKILL.md) | `EInvalidateWidgetReason` (Layout/Paint/Volatility/ChildOrder/RenderTransform/Visibility/AttributeRegistration/Prepass), `SInvalidationPanel`, `FSlateInvalidationRoot`, `FastUpdate/` 폴더 클래스, `SWidget::Invalidate()` / `SetVolatile()`, **`OnPaint` LayerId 단조 증가 / DrawCall 배치 (`FSlateElementBatcher`) / 아틀라스 활용** |
| **이 모듈** [`SWidget/`](./SWidget/SKILL.md) | `TSlateAttribute<T, EInvalidateWidgetReason>` 가 어트리뷰트 변경 시 자동으로 발행하는 인밸리데이션, `SLATE_DECLARE_WIDGET` + `PrivateRegisterAttributes` |
| [`UMG/UWidget/`](../UMG/references/UWidget.md) | `UWidget::SynchronizeProperties()` 호출 시점, `EWidgetVolatility`, `UWidget::Invalidate(EInvalidateWidgetReason)`, BP 노출 setter들이 자동 트리거하는 reason |
| [`UMG/UUserWidget/`](../UMG/references/UUserWidget.md) | `NativePreConstruct`/`NativeOnInitialized`/`NativeConstruct`/`NativeTick`/`NativeDestruct` 시퀀스에서 인밸리데이션 발생 시점, `UInvalidationBox` 사용 패턴, `UUserWidget::TickFrequency` (NeverTick 권장 조건), **`NativeOnPaint`/`NativePaint` override 시 LayerId 중복·DrawCall 폭증·자동 휘발성 함정 (Canvas ZOrder ≠ LayerId)** |

핵심 원칙 (각 sub-skill에서 반복 명시):

1. **TSlateAttribute** 사용으로 자동 인밸리데이션을 받는다 — raw 멤버 변수에 setter로 매번 `Invalidate()` 호출하는 구식 패턴 지양.
2. **UInvalidationBox** 안에 정적 영역을 넣어 매 프레임 재페인트를 막는다.
3. **`SetVolatile(true)`** 는 캐시를 끄므로 신중히 — 진짜 매 프레임 변하는 경우에만.
4. **`Tick`은 비싸다** — UUserWidget의 `TickFrequency`를 `NeverTick`/`OnlyWhenVisible`로, Slate는 `RegisterActiveTimer` 권장.
5. **`SynchronizeProperties`** 는 디자이너 변경/생성 시에만 호출되므로 런타임 setter는 별도로 인밸리데이션을 직접 지정해야 함.
6. **`OnPaint` override 시**: 자식의 반환 LayerId 받아 위로 단조 증가 / 같은 텍스처·폰트끼리 묶어 그리기 / 텍스처 아틀라스 활용 / `NativeOnPaint` 는 자동 휘발성으로 캐시 비활성 → 가능하면 표준 위젯 조합 (자세히 [`Drawing/§5`](./Drawing/SKILL.md)).

---

## 6. 관련 모듈

- **상위 (의존됨)**: `Slate` (표준 위젯), `SlateRHIRenderer`, `SlateNullRenderer`, `UMG`, 거의 모든 에디터 모듈.
- **하위 (의존)**: `Core`, `CoreUObject`, `DeveloperSettings`, `InputCore`, `Json`, `TraceLog` (+ `ApplicationCore` 옵션).
- **연계**:
  - [`Slate/`](../Slate/SKILL.md) — 표준 위젯 + `FSlateApplication` 통합
  - [`UMG/`](../UMG/SKILL.md) — `UWidget`/`UUserWidget` BP 노출 레이어
  - [`InputCore/`](../InputCore/SKILL.md) — `FKey`/`EKeys` 입력 식별자
  - [`ApplicationCore/`](../ApplicationCore/SKILL.md) — OS 윈도우/이벤트
  - [`CoreUObject/UObject/`](../CoreUObject/references/UObject.md) — `USlateWidgetStyleAsset` 등 UCLASS 통합 (Styling sub-skill 참조)

---

## 7. 작성·인용 규칙

전체 위키 공통 규칙을 따른다 — `skills/CoreUObject/SKILL.md §7.1` 의 에디터 전용 표기 규칙(🛠 마커 + `WITH_EDITOR`/`WITH_EDITORONLY_DATA` 가드 명시) + 라인 번호 직접 grep 검증.

추가로 SlateCore 특수 규약:

- `SNew`/`SAssignNew` 매크로 사용 — `new SWidget()` 직접 호출 금지.
- 람다에서 위젯 캡처는 `TWeakPtr<SWidget>` 사용 — 강 참조 보유 시 메모리 누수.
- `FVector2D` → `FVector2f` 마이그레이션 (5.x) — 옛 좌표 사용 시 `UE_REPORT_SLATE_VECTOR_DEPRECATION` 경고.
- 라인 번호는 5.7.4 트리에서 직접 grep — 마이너 패치에 따라 ±수십 라인.
