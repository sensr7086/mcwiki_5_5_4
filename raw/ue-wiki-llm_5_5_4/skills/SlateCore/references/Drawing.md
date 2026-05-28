---
name: slatecore-drawing
description: OnPaint + FSlateDrawElement::MakeBox/Lines/Text + FPaintArgs + LayerId + FSlateBrush + Material 통합.
---

# SlateCore / Drawing

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.5.4
> 다루는 영역: 그리기 — `FSlateDrawElement`/`FSlateWindowElementList`/`FPaintArgs`/`FSlateBrush` + 텍스처·SVG·렌더링 핸들 + **인밸리데이션 캐시 시스템 (`FSlateInvalidationRoot`/`FastUpdate`)**
> 관련 sub-skill: [`SWidget/`](../SWidget/SKILL.md), [`Layout/`](../Layout/SKILL.md), [`Styling/`](../Styling/SKILL.md)

---

## 1. 개요

Slate 그리기는 **즉시 모드 + 캐시 모드 혼합**:

```
[즉시 모드]  OnPaint(Geo, ...) 안에서 FSlateDrawElement::Make* 로 OutDrawElements 에 누적
            → FSlateRenderer 가 매 프레임 GPU에 제출 (SlateRHIRenderer)

[캐시 모드]  SInvalidationPanel(=FSlateInvalidationRoot) 가 자식 위젯 그래프의 결과 draw element를 캐싱
            → 인밸리데이션이 일어난 부분만 재페인트 (FastPath)
            → 큰 변경 시 전체 재페인트 (SlowPath)
```

위젯 작성자가 만지는 것은 거의 즉시 모드(`OnPaint` 안 `FSlateDrawElement::Make*`)다. 캐시 시스템은 자동으로 동작하며, 성능 튜닝 시 의식적으로 활용한다.

---

## 2. 핵심 헤더와 클래스

### 2.1 즉시 모드 그리기 (`Public/Rendering/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Rendering/DrawElements.h` | `class FSlateWindowElementList : FNoncopyable` (L225) | `OnPaint` 의 `OutDrawElements`. 한 윈도우의 draw element 누적. |
| `Rendering/DrawElementTypes.h` | `class FSlateDrawElement` (L50) | 단일 그리기 명령 (Box/Border/Text/Line/Spline/Gradient/Custom 등). 정적 `Make*` 헬퍼. |
| `Rendering/DrawElementCoreTypes.h` | `ESlateDrawEffect` (DrawDisabledEffect/PreMultipliedAlpha 등) | 그리기 효과 비트마스크. |
| `Rendering/DrawElementPayloads.h` | 페이로드 타입들 | `MakeText`/`MakeBox` 등이 내부적으로 보유. |
| `Rendering/RenderingCommon.h` | `FSlateVertex`, `ESlateBatchDrawFlag` | 정점·배치 플래그. |
| `Rendering/SlateLayoutTransform.h` | `FSlateLayoutTransform` | 위치 + 스케일. `FGeometry::MakeChild` 인자. |
| `Rendering/SlateRenderTransform.h` | `FSlateRenderTransform` | 회전·스큐 등 렌더 전용 변환 (레이아웃과 분리). |
| `Rendering/SlateResourceHandle.h` | `FSlateResourceHandle` | 텍스처/머티리얼 핸들 캐시. |
| `Rendering/SlateRenderer.h` | `class FSlateRenderer` | 렌더러 인터페이스 (실제 구현은 `SlateRHIRenderer`/`SlateNullRenderer`). |
| `Rendering/SlateDrawBuffer.h` | `FSlateDrawBuffer` | 한 프레임의 윈도우별 element list 묶음. |
| `Rendering/ElementBatcher.h` | `FSlateElementBatcher` | DrawElement → 정점 배치로 변환 (내부). |
| `Rendering/RenderingPolicy.h` | `FSlateRenderingPolicy` | 백엔드별 렌더 정책. |
| `Rendering/SlateSVGRasterizer.h`, `SlateVectorGraphicsCache.h` | SVG 래스터화·캐시 | `Nanosvg` 통합. |
| `Rendering/ShaderResourceManager.h` | 셰이더 리소스 관리 | 내부. |

### 2.2 브러시 (`Public/Brushes/`) — `FSlateBrush` 의 빠른 헬퍼들

| 헤더 | 심볼 | 패턴 |
|------|------|------|
| `Brushes/SlateBoxBrush.h` | `FSlateBoxBrush` | 9-slice 박스 (테두리·중앙 분리). 버튼 배경 등. |
| `Brushes/SlateBorderBrush.h` | `FSlateBorderBrush` | 테두리만. |
| `Brushes/SlateImageBrush.h` | `FSlateImageBrush` | 단일 이미지 스케일. |
| `Brushes/SlateColorBrush.h` | `FSlateColorBrush` | 단색 채움. |
| `Brushes/SlateRoundedBoxBrush.h` | `FSlateRoundedBoxBrush` | 둥근 모서리 박스 (5.x). |
| `Brushes/SlateDynamicImageBrush.h` | `FSlateDynamicImageBrush` | 런타임 동적 이미지 (UTexture 등). |
| `Brushes/SlateNoResource.h` | `FSlateNoResource` | 빈 브러시 (placeholder). |

기본 `FSlateBrush` 자체는 [`Styling/`](../Styling/SKILL.md) 에서 다룬다.

### 2.3 텍스처 (`Public/Textures/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Textures/SlateShaderResource.h` | `FSlateShaderResource` | RHI 텍스처 추상. |
| `Textures/SlateTextureData.h` | `FSlateTextureData` | CPU 측 픽셀 데이터. |
| `Textures/SlateUpdatableTexture.h` | `ISlateUpdatableTexture` | 매 프레임 갱신 가능 텍스처. |
| `Textures/TextureAtlas.h` | `FSlateTextureAtlas` | 작은 이미지 묶음 — 폰트 글리프·아이콘 등. |
| `Textures/SlateIcon.h` | `FSlateIcon` | 스타일셋 + 브러시명 식별자. |

### 2.4 ⚡ 인밸리데이션 캐시 (`Public/FastUpdate/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `FastUpdate/SlateInvalidationRoot.h` | `class FSlateInvalidationRoot : FGCObject, FNoncopyable` (L76), `FSlateInvalidationContext` (L28), `FSlateInvalidationResult` (L60), `enum class ESlateInvalidationPaintType` (None/Slow/Fast, L53) | 캐시 루트. `SInvalidationPanel`(→ `Slate` 모듈)이 이걸 감쌈. |
| `FastUpdate/SlateInvalidationRootHandle.h` | `FSlateInvalidationRootHandle` | 루트 식별자. |
| `FastUpdate/SlateInvalidationWidgetIndex.h` | `FSlateInvalidationWidgetIndex` | 빠른 위젯 인덱스. |
| `FastUpdate/SlateInvalidationWidgetSortOrder.h` | `FSlateInvalidationWidgetSortOrder` | 페인트 순서 정렬. |
| `FastUpdate/WidgetProxy.h` | `FWidgetProxy`, `FWidgetProxyHandle` | 위젯의 fast-path 표현. |
| `FastUpdate/WidgetUpdateFlags.h` | `enum class EWidgetUpdateFlags : uint8` (NeedsTick=1<<2, NeedsActiveTimerUpdate=1<<3, NeedsRepaint=1<<4, NeedsVolatilePaint=1<<6, NeedsVolatilePrepass=1<<7, AnyUpdate=0xff) | 위젯 갱신 플래그. |

---

## 3. 자주 쓰는 API

```cpp
virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geo,
                      const FSlateRect& Cull, FSlateWindowElementList& Out,
                      int32 LayerId, const FWidgetStyle& Style, bool bEnabled) const override
{
    // 박스
    FSlateDrawElement::MakeBox(
        Out, LayerId,
        Geo.ToPaintGeometry(),
        FCoreStyle::Get().GetBrush("Border"),       // 또는 자체 FSlateBrush
        ESlateDrawEffect::None,
        FLinearColor::White
    );

    // 텍스트
    FSlateDrawElement::MakeText(
        Out, LayerId + 1,
        Geo.ToPaintGeometry(FMargin(8.f), FSlateLayoutTransform()),
        FText::FromString(TEXT("Hello")),
        FCoreStyle::Get().GetFontStyle("NormalFont"),
        ESlateDrawEffect::None,
        FLinearColor::White
    );

    // 선
    TArray<FVector2D> Pts = { {0,0}, {100,100} };
    FSlateDrawElement::MakeLines(Out, LayerId + 2, Geo.ToPaintGeometry(), Pts,
                                 ESlateDrawEffect::None, FLinearColor::Red, true, 2.f);

    return LayerId + 3;     // 다음 레이어
}
```

`LayerId` 가 클수록 위에 그려진다. 반환값은 부모가 다음 형제에 사용할 시작 레이어.

### 3.1 페인트 보조

```cpp
// 자식 페인트 (CompoundWidget·Panel)
int32 NewLayer = SCompoundWidget::OnPaint(Args, Geo, Cull, Out, LayerId, Style, bEnabled);

// FPaintArgs (페인트 컨텍스트)
const FWidgetStyle& WidgetStyle = Args.GetWidgetStyle();
double CurrentTime = Args.GetCurrentTime();
float DeltaTime    = Args.GetDeltaTime();
```

---

## 4. ⚡ 인밸리데이션 / 갱신 흐름 (의무 섹션)

### 4.1 캐시 모드의 두 경로

| 경로 | 언제 | 비용 |
|------|------|------|
| **FastPath** | 일부 위젯만 변경됐고 fast-path 가능 | 낮음 — 변경된 위젯만 재페인트 |
| **SlowPath** | 자식 추가/제거, 레이아웃 변경, 또는 fast-path 불가능 | 높음 — 전체 그래프 prepass + paint |

`FSlateInvalidationRoot::NeedsSlowPath()` 가 true 면 다음 페인트는 SlowPath. `FSlateInvalidationRoot::PaintInvalidationRoot(...)` 의 결과 `FSlateInvalidationResult::bRepaintedWidgets` 로 실제 재페인트 여부 확인.

### 4.2 인밸리데이션 발행 경로

1. **TSlateAttribute 변경** → 등록된 reason 자동 발행 (`SlateAttributeMetaData`).
2. **명시적 호출** — `SWidget::Invalidate(EInvalidateWidgetReason)`.
3. **시각 속성 setter** — `SetVisibility`/`SetEnabled`/`SetRenderTransform` 등이 적절한 reason을 자동 발행.
4. **자식 추가/제거** — `ChildOrder` 발행.
5. **`SetVolatile(true)`** — 매 프레임 `NeedsVolatilePaint` (`EWidgetUpdateFlags`) 자동 처리.

### 4.3 ⚡ 핵심 운영 가이드

- **`SInvalidationPanel`** 안에 정적 영역(메뉴 바, 인벤토리 슬롯 그리드 등)을 넣으면 매 프레임 페인트 비용 절감. 단, 안의 위젯이 자주 변하면 SlowPath가 자주 일어나 오히려 손해.
- **`SetVolatile(true)`** = 캐시 비활성. 진짜 매 프레임 변하는 위젯에만 (전체 화면 GIF/실시간 그래프). `ComputeVolatility` virtual override로 자동 결정 가능.
- **드래그 중 페인트** — `EPropertyChangeType::Interactive` 같은 단계가 있다면 SlowPath 빈도를 낮추도록 변경을 batch.
- **`Advanced_ResetInvalidation(bClearResourcesImmediately=false)`** — 디버그용. 일반 코드에서 호출 금지.
- **디버그**: `Slate.InvalidationDebugging.IsEnabled` cvar / `Slate.DebugWidgets` 등 콘솔 명령. `WITH_SLATE_DEBUGGING` 빌드에서 `FSlateInvalidationRoot::GetPerformanceStat()` 사용 가능.

### 4.4 EWidgetUpdateFlags (`FastUpdate/WidgetUpdateFlags.h`)

```
NeedsTick                = 1 << 2   매 프레임 Tick virtual 호출 필요
NeedsActiveTimerUpdate   = 1 << 3   ActiveTimer 콜백 처리 필요
NeedsRepaint             = 1 << 4   인밸리데이션으로 더티
NeedsVolatilePaint       = 1 << 6   휘발성 — 매 프레임 페인트
NeedsVolatilePrepass     = 1 << 7   휘발성 — 매 프레임 prepass
AnyUpdate                = 0xff
```

위젯 작성자가 직접 다루는 일은 거의 없지만, 프로파일링·Slate Insights에서 본다.

---

## 5. ⚠ OnPaint 시 LayerId 관리 / DrawCall 최적화 (의무 섹션)

`OnPaint` 안에서 `FSlateDrawElement::Make*` 호출 패턴이 잘못되면 **레이어 중복(가려짐·깜빡임)** 과 **DrawCall 폭증**이 동시에 일어난다. UMG에서 `NativeOnPaint`/`NativePaint` override를 쓸 때 가장 자주 만나는 함정.

### 5.1 LayerId 관리 — 자식의 반환 LayerId를 반드시 받아라

```cpp
// ❌ 실수: 자식이 어디까지 LayerId를 썼는지 무시 → 자식이 LayerId 5까지 썼는데 부모가 LayerId+1=2 에 그리면 가려짐
virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geo, ..., int32 LayerId, ...) const override
{
    SCompoundWidget::OnPaint(Args, Geo, Cull, Out, LayerId, Style, bEnabled);  // 반환값 무시
    FSlateDrawElement::MakeBox(Out, LayerId + 1, ...);                         // 잘못된 LayerId
    return LayerId + 2;
}

// ✅ 올바름: 자식 OnPaint의 반환 LayerId 받기
virtual int32 OnPaint(...) const override
{
    int32 NewLayer = SCompoundWidget::OnPaint(Args, Geo, Cull, Out, LayerId, Style, bEnabled);
    FSlateDrawElement::MakeBox(Out, NewLayer + 1, ...);                        // 자식 위에 확실히
    return NewLayer + 2;
}

// ✅ 자식보다 아래에 그릴 것은 자식 호출 전에
virtual int32 OnPaint(...) const override
{
    FSlateDrawElement::MakeBox(Out, LayerId, ..., FLinearColor::Black);        // 배경 — LayerId
    int32 ChildLayer = SCompoundWidget::OnPaint(Args, Geo, Cull, Out, LayerId + 1, Style, bEnabled);
    FSlateDrawElement::MakeText(Out, ChildLayer + 1, ...);                     // 오버레이 — 자식 위
    return ChildLayer + 2;
}
```

**핵심 규칙**:

- `LayerId` 가 같으면 **그리기 순서 비결정적** → 깜빡임·뒤틀림. 같은 위젯에서 두 element를 같은 LayerId로 두지 말 것.
- `LayerId` 는 **단조 증가**. 자식이 LayerId 5 까지 썼으면 부모는 6 부터 시작.
- `Super::OnPaint(...)` (자식 페인트) 의 반환값은 **다음 형제·후속 그리기의 시작 LayerId**.
- UMG `UCanvasPanelSlot::ZOrder` 와 Slate `LayerId` 는 **다른 개념**. ZOrder는 부모 패널이 자식을 정렬할 때, LayerId는 한 위젯 안에서. 혼동 금지.

### 5.2 DrawCall 배치 — `FSlateElementBatcher` 가 묶을 수 있게 그려라

`FSlateElementBatcher` 는 다음 조건을 만족하는 연속된 element 들을 한 DrawCall로 배치한다:

| 조건 | 설명 |
|------|------|
| 같은 셰이더 | Box / Border / Text / Line / Spline 등 element 타입이 같음 |
| 같은 텍스처/머티리얼 | 동일 `FSlateResourceHandle` |
| 같은 LayerId | 또는 사이에 다른 텍스처/타입이 끼어들지 않음 |
| 같은 클리핑 | `FSlateClippingZone` 동일 |
| 같은 PixelSnapping/효과 | `ESlateDrawEffect` 동일 |

배치가 깨지는 패턴:

```cpp
// ❌ DrawCall 폭증: 텍스처 A → 텍스처 B → 텍스처 A 가 LayerId 인터리빙
for (const FItem& Item : Items)
{
    FSlateDrawElement::MakeBox(Out, L,   ItemBackground);    // 배치 가능
    FSlateDrawElement::MakeBox(Out, L+1, Item.Icon);         // 텍스처 다름 → 배치 깨짐
    FSlateDrawElement::MakeText(Out, L+2, Item.Name);        // 셰이더 다름 → 배치 깨짐
    L += 3;
}
// → 아이템 N개에 대해 3*N drawcall

// ✅ 두 패스로 나누어 같은 자원끼리 묶기
int32 BackLayer = LayerId, IconLayer = LayerId + 1, TextLayer = LayerId + 2;
for (const FItem& Item : Items)
    FSlateDrawElement::MakeBox(Out, BackLayer, ItemBackground);   // 같은 텍스처 → 1 drawcall
for (const FItem& Item : Items)
    FSlateDrawElement::MakeBox(Out, IconLayer, Item.Icon);        // 아이콘이 atlas면 1 drawcall
for (const FItem& Item : Items)
    FSlateDrawElement::MakeText(Out, TextLayer, Item.Name);       // 폰트 atlas → 1 drawcall
// → 아이템 N개에 대해 3 drawcall
```

**핵심 규칙**:

- **텍스처 아틀라스(`FSlateTextureAtlas`)** 사용 — 작은 아이콘들을 한 텍스처로 묶으면 자동 배치.
- **`FSlateBrush` 인스턴스 재사용** — 매번 `FSlateBrush()` 새로 만들지 말고 정적 멤버나 스타일셋에서 캐시.
- **타입 인터리빙 회피** — Box/Box/Text/Box 보다 Box/Box/Box/Text 순서가 배치 친화.
- **위젯 분할 vs 직접 OnPaint** — 자식 표준 위젯들로 표현 가능하면 그쪽이 batch에 더 유리. 직접 그리는 건 자유도가 큰 대신 batch 책임이 작성자에게 옴.

### 5.3 UMG 에서 OnPaint 사용 시 추가 함정 🛠

UMG 의 `UUserWidget::NativeOnPaint`/`NativePaint` override 는 **마지막 수단**으로만 — 다음 함정이 따라온다:

| 함정 | 영향 | 회피 |
|------|------|------|
| `NativePaint` override 위젯은 **자동 휘발성**처럼 동작 | `SInvalidationPanel`/`UInvalidationBox` 캐시 비활성화 | 가능하면 표준 UMG 위젯 조합으로 표현. 직접 그리기 영역만 작은 SLeafWidget으로 분리해 외부에서 `UInvalidationBox`로 감싸기. |
| `LayerId` 반환 누락 → 자식 위젯이 가려짐 | 텍스트 위에 박스가 덮이는 등 시각 버그 | 반드시 `Super::NativePaint(...)` 의 반환값 사용. |
| 매 프레임 새 `FSlateBrush` 생성 | DrawCall 배치 깨짐 + 메모리 압박 | 멤버에 캐시하거나 `FAppStyle::Get().GetBrush(...)`. |
| `Canvas Panel ZOrder` 와 `LayerId` 혼동 | 의도와 다른 그리기 순서 | ZOrder는 패널이 자식을 정렬할 때만, OnPaint 안에서는 LayerId만 사용. |
| `UMG` 위젯과 직접 그린 element 혼합 | LayerId 충돌 | 직접 그린 영역을 별도 SLeafWidget으로 격리하고 그 LayerId 만 관리. |

> 본 §5.3 의 핵심은 [`UMG/references/UUserWidget.md`](../../UMG/references/UUserWidget.md) 와 [`UMG/references/UWidget.md`](../../UMG/references/UWidget.md) 에서도 의무 섹션으로 다시 다룬다 — UMG 작성 시 매번 잊지 않도록.

### 5.4 디버그 / 측정

- **`Slate.DrawElementsStats`** cvar — 프레임당 element 수·DrawCall 카운트 출력.
- **`Slate.ShowBatching`** — 배치 경계 시각화.
- **Unreal Insights → Slate channel** — element 별 시간·배치 분석. [`Trace/`](../Trace/SKILL.md).
- **`stat SlateRendering`** — 프레임 GPU 시간.

---

## 6. 예제

### 6.1 박스 + 텍스트 결합 (LayerId 단조 증가)

```cpp
virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& Geo, const FSlateRect& Cull,
                      FSlateWindowElementList& Out, int32 LayerId,
                      const FWidgetStyle& Style, bool bEnabled) const override
{
    const FSlateBrush* BG = FCoreStyle::Get().GetBrush("ToolPanel.GroupBorder");
    FSlateDrawElement::MakeBox(Out, LayerId, Geo.ToPaintGeometry(), BG,
                               ESlateDrawEffect::None, FLinearColor::Black);

    FSlateDrawElement::MakeText(Out, LayerId + 1,
        Geo.ToPaintGeometry(FMargin(8.f), FSlateLayoutTransform()),
        Text.Get(), FCoreStyle::Get().GetFontStyle("NormalFont"),
        bEnabled ? ESlateDrawEffect::None : ESlateDrawEffect::DisabledEffect,
        bEnabled ? FLinearColor::White : FLinearColor::Gray);

    return LayerId + 2;
}
```

### 6.2 SInvalidationPanel 활용 패턴 (Slate 모듈에서 사용)

```cpp
// Slate 모듈의 SInvalidationPanel 사용 — 정적 영역 캐싱
ChildSlot
[
    SNew(SInvalidationPanel)
    [
        SNew(SVerticalBox)
        + SVerticalBox::Slot() [ SNew(SBorder) [ ... 자주 안 변하는 헤더 ... ] ]
        + SVerticalBox::Slot() [ SNew(SUniformGridPanel) [ ... 인벤토리 슬롯 ... ] ]
    ]
];
```

### 6.3 SetVolatile vs TSlateAttribute

```cpp
// ❌ 옛 패턴 — 매번 직접 Invalidate
class SOldStyle : public SLeafWidget
{
public:
    void SetTitle(FText InText) { Title = InText; Invalidate(EInvalidateWidgetReason::Layout); }
private:
    FText Title;
};

// ✅ 권장 — TSlateAttribute가 자동 인밸리데이션
class SNewStyle : public SLeafWidget
{
    SLATE_DECLARE_WIDGET(SNewStyle, SLeafWidget)
private:
    TSlateAttribute<FText, EInvalidateWidgetReason::Layout> Title;
};
```

---

## 7. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `FSlateInvalidationRoot::GetPerformanceStat()` 🛠 | SlateInvalidationRoot.h | `WITH_SLATE_DEBUGGING` | 인밸리데이션 단계별 시간 측정. |
| `FSlateInvalidationRoot::GetLastPaintType()` 🛠 | SlateInvalidationRoot.h | `WITH_SLATE_DEBUGGING` | 마지막 Paint가 Slow/Fast 였는지. |
| `Slate.InvalidationDebugging.*` cvar 🛠 | (cvar) | `WITH_SLATE_DEBUGGING` | 디버그 가시화. |
| Slate Insights 트레이스 🛠 | (`Trace/`) | `UE_TRACE_ENABLED` | [`Trace/`](../Trace/SKILL.md) |
| `ESlateDrawEffect::ReverseGamma` 같은 디버그 효과 일부 🛠 | DrawElementCoreTypes.h | (디버그) | 일반 코드 안 씀. |

런타임에서 안전한 API는 `FSlateDrawElement::Make*`, `FSlateBrush`, `FSlateInvalidationRoot::Invalidate*` 전부.

---

## 8. 관련 sub-skill

- [`SWidget/`](../SWidget/SKILL.md) — `OnPaint` virtual + `TSlateAttribute` 자동 인밸리데이션
- [`Layout/`](../Layout/SKILL.md) — `FGeometry::ToPaintGeometry()` 가 페인트 좌표
- [`Styling/`](../Styling/SKILL.md) — `FSlateBrush`/`FSlateColor`/`FSlateFontInfo` 가 그리기 입력
- [`Application/`](../Application/SKILL.md) — `FSlateApplicationBase::Tick` 이 한 프레임의 paint/invalidation 사이클을 조율
- [`Trace/`](../Trace/SKILL.md) — Slate Insights로 인밸리데이션 흐름 분석
