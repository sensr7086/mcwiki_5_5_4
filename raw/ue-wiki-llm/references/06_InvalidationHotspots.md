---
name: invalidation-hotspots
description: 위젯별 인밸리데이션 다발 케이스 (STextBlock/RichText/EditableText/ListView/Throbber/NativeOnPaint/TAttribute 람다) + InvalidationBox/ForceVolatile 결정 트리 + NativeTick 회피 계층. UMG 성능 이슈 시 의무.
---

# Invalidation Hotspots — 인밸리데이션이 자주 발생하는 케이스 + 회피 패턴

> Slate / UMG 위젯이 **자주 인밸리데이션을 발생시키는 케이스** 를 위젯별로 분석하고, **회피·완화 패턴** 을 정리. UI 성능 저하의 가장 흔한 원인.
> **부모 가이드**: [`SlateCore/references/Drawing.md §4`](../skills/SlateCore/references/Drawing.md) (인밸리데이션 캐시 흐름) + [`SlateCore/references/Drawing.md §5`](../skills/SlateCore/references/Drawing.md) (OnPaint LayerId/DrawCall) + [`UMG/references/UWidget.md §5`](../skills/UMG/references/UWidget.md) (UWidget 인밸리데이션) + [`UMG/references/UUserWidget.md §5`](../skills/UMG/references/UUserWidget.md) (UUserWidget 인밸리데이션 + NativeOnPaint 함정).
> 갱신 이력: 2026-05-03.

---

## 0. 사용 규칙

1. UI 성능 문제(낮은 FPS·Slate 시간 증가·DrawCall 폭증)가 발생하면 본 인덱스에서 사용 중인 위젯 케이스 확인.
2. **결정 트리** (§7) 로 SInvalidationPanel/UInvalidationBox · ForceVolatile · NativePaint 사용 여부 결정.
3. 디버그·측정은 §8 의 cvar / Insights 채널 활용.

---

## 1. EInvalidateWidgetReason 8종 (복습)

> 자세한 정의는 [`SlateCore/references/Drawing.md §4.2`](../skills/SlateCore/references/Drawing.md) 표.

| reason | 비용 | 발생 시점 |
|--------|------|----------|
| `Layout` | **높음** (자식 트리 prepass + 재배치) | 위젯이 desired size 변경 (텍스트 길이 / 자식 추가 등) |
| `Paint` | 중간 (해당 위젯만 재페인트) | 색·이미지·alpha 변경 |
| `Volatility` | 낮음 | 휘발성 토글 |
| `ChildOrder` | **높음** (Prepass + Layout 함의) | 자식 추가/제거 |
| `RenderTransform` | 낮음 | 회전/스케일/이동만 (레이아웃 변경 없음) |
| `Visibility` | **높음** (Layout 함의) | 가시성 변경 |
| `AttributeRegistration` | 매우 낮음 | TSlateAttribute 바인딩/언바인딩 |
| `Prepass` | **높음** | 자식 트리 desired size 재계산 |

`PaintAndVolatility` / `LayoutAndVolatility` 합성 reason 도 사용.

---

## 2. 위젯별 인밸리데이션 핫스팟 — [`references/InvalidationHotspotsDeep.md`](./references/InvalidationHotspotsDeep.md) ✂️

> **Article 3 Level 3 progressive disclosure 적용** — 메인은 핫스팟 요약 매트릭스 + 회피 전략 / 깊이는 reference.

### 위젯별 hotspot 매트릭스 (요약)

| 위젯 | 주요 hotspot | 회피 전략 | reference |
|------|-------------|----------|-----------|
| `STextBlock` / `UTextBlock` | `SetText` 매 프레임 호출 / `TAttribute<FText>` 람다 평가 | 변경 시만 setter / `Slate Attribute` 5.x 자동 캐싱 | [`§2.1`](./references/InvalidationHotspotsDeep.md) |
| `URichTextBlock` | 전체 trying 재파싱 | DecoratorClasses 캐싱 / 큰 텍스트는 분할 | [`§2.2`](./references/InvalidationHotspotsDeep.md) |
| `SEditableText` / `UEditableTextBox` | 매 키 입력 마다 OnTextChanged | OnTextCommitted 만 사용 (포커스 잃을 때) | [`§2.3`](./references/InvalidationHotspotsDeep.md) |
| `SListView` / `UListView` | RequestListRefresh / RebuildList 매 프레임 | Diff 기반 Add/Remove + RegenerateAllEntries | [`§2.4`](./references/InvalidationHotspotsDeep.md) |
| `SThrobber` / `UThrobber` | bIsAnimating = true → 매 Tick 페인트 | 사용 중에만 Visibility 토글 | [`§2.5`](./references/InvalidationHotspotsDeep.md) |
| `NativeOnPaint` override 위젯 | 자동 휘발성 / 캐시 비활성 | SLeafWidget 분리 + 외부에서 InvalidationBox | [`§2.6`](./references/InvalidationHotspotsDeep.md) |
| `TAttribute<T>` 람다 | 매 평가마다 람다 호출 | `TSlateAttribute` 5.x (자동 캐싱) | [`§2.7`](./references/InvalidationHotspotsDeep.md) |

> 자세한 코드 예제 + 함정 + 표준 패턴 = reference 참조.

---

## 3. UInvalidationBox 활용 가이드

> 자세한 흐름 [`SlateCore/references/Drawing.md §4`](../skills/SlateCore/references/Drawing.md).

### 3.1 사용해야 할 곳 ✅

- 메인 메뉴 헤더 / 푸터 (절대 안 변함)
- 인벤토리 슬롯 그리드 배경 (슬롯 채워지기 전)
- 캐릭터 정보 패널 정적 부분 (이름·레벨 — 자주 안 변함)
- BP 그래프 에디터의 정적 노드들

### 3.2 두지 말아야 할 곳 ❌

- `URichTextBlock` (마크업 파싱이 매번 캐시 무효)
- `UThrobber`/`UCircularThrobber` (자동 휘발성)
- `NativeOnPaint`/`NativePaint` override 위젯 (자동 휘발성)
- `ForceVolatile(true)` 위젯
- `UProgressBar` 자주 갱신 (체력바 등) — 캐시 무효 비용 > 페인트 절감
- `UListView` 안에 (자체 가상화로 충분)

### 3.3 결정 트리

```
이 위젯/영역이 자주 변하나?
├─ NO  → UInvalidationBox 안에 ✅ (캐시 활용)
└─ YES
    ├─ 매 프레임 변하나?
    │   ├─ YES  → UInvalidationBox 외부 + ForceVolatile(true) 검토 ⚠
    │   └─ NO (1초에 한 번 정도)  → UInvalidationBox 외부, 캐시 무관
    └─ 자주 변하지만 일부만 변하나?
        └─ YES  → 변하는 부분 분리해서 외부에, 정적 부분은 안에 ✅✅
```

---

## 4. ForceVolatile / SetVolatile 결정 트리

```
이 위젯이 진짜 매 프레임 다른가?
├─ YES (전체 화면 GIF / 실시간 그래프 / 회전 Throbber)  → ForceVolatile(true) ✅
│      → SInvalidationPanel/UInvalidationBox 외부에 배치 필수
└─ NO  → ForceVolatile(false) — 캐시 활용 ✅
```

`ComputeVolatility()` virtual override 로 자동 결정도 가능.

---

## 5. NativeTick / Tick 회피 가이드

### 5.1 우선순위 (가장 권장 → 최후 수단)

```
1. 이벤트 기반 (Delegate) — 데이터 변경 시 setter 호출 ✅✅✅
2. RegisterActiveTimer — Slate 자체 타이머 (자동 종료 가능) ✅✅
3. NativeTick — 매 프레임, TickFrequency 결정 ⚠
4. SetVolatile(true) + NativeOnPaint — 사용자 그리기 매 프레임 ❌
```

### 5.2 EWidgetTickFrequency

> [`UMG/references/UUserWidget.md §5.3`](../skills/UMG/references/UUserWidget.md).

| 값 | 동작 | 권장 |
|----|------|------|
| `Never` | 절대 NativeTick 호출 안 함 | **정적 HUD/메뉴** |
| `Auto` | BP tick / 애니메이션 / latent action 시 자동 | 동적 HUD (체력바 보간 등) |

**클래스 단위**: `UCLASS(meta=(DisableNativeTick))` — native tick 비활성, BP tick 만.

### 5.3 RegisterActiveTimer 패턴

```cpp
// SWidget 측 — Slate Animation
ActiveTimerHandle = RegisterActiveTimer(
    /*ExecutionDelay=*/0.f,
    FWidgetActiveTimerDelegate::CreateSP(this, &SMy::TickAnim));

EActiveTimerReturnType SMy::TickAnim(double InCurrentTime, float InDeltaTime)
{
    if (Anim.IsPlaying()) return EActiveTimerReturnType::Continue;
    return EActiveTimerReturnType::Stop;     // 자동 해제
}
```

NativeTick 보다 가벼움 + 자동 종료 가능 + TickFrequency 무관.

---

## 6. setter 자동 trigger 표 (UWidget)

> [`UMG/references/UWidget.md §5.2`](../skills/UMG/references/UWidget.md) 표 재구성.

| setter | 자동 trigger reason | 비용 | 권장 빈도 |
|--------|---------------------|------|----------|
| `SetVisibility(Visible↔Collapsed)` | `Visibility` (Layout 함의) | **높음** | 영구 변경만 |
| `SetVisibility(Visible↔Hidden)` | `Visibility` (공간 유지) | 중간 | 잦은 토글 |
| `SetIsEnabled(bool)` | `Paint` | 낮음 | 자유 |
| `SetRenderTransform(FWidgetTransform)` | `RenderTransform` | 낮음 | 매 프레임 OK |
| `SetRenderOpacity(float)` | `Paint` | 낮음 | 자유 |
| `SetClipping(EWidgetClipping)` | `Layout` | 중간 | 드뭄 |
| `SetCursor(EMouseCursor::Type)` | (없음) | 0 | 자유 |
| `ForceVolatile(true)` | `Volatility` | 한 번 | 신중 |
| 사용자 정의 setter | (자동 없음 — Slate setter 호출 또는 `Invalidate(reason)`) | reason 따라 | — |

---

## 7. 디버그 / 측정 도구

### 7.1 콘솔 cvar

| 명령 | 효과 |
|------|------|
| `Slate.InvalidationDebugging.IsEnabled 1` | 인밸리데이션 발행 가시화 |
| `Slate.DrawElementsStats 1` | 프레임당 element 수·DrawCall 카운트 |
| `Slate.ShowBatching 1` | DrawCall 배치 경계 색칠 |
| `Slate.GlobalInvalidation 1` | 전체 인밸리데이션 (테스트) |
| `Slate.DebugWidgets` | 모든 위젯 트리 로그 |
| `WidgetReflector` | 위젯 트리 시각화 + 클릭으로 위젯 식별 (에디터) |

### 7.2 stat / Insights

```bash
stat Slate              # Slate 전체
stat SlateRendering     # 렌더링 시간
stat SlateInvalidation  # 인밸리데이션 시간
```

Unreal Insights — `Slate` 채널 활성:

```bash
UnrealEditor.exe -trace=cpu,frame,gpu,slate
```

`FSlateInvalidationRoot::GetPerformanceStat()` 🛠 (`WITH_SLATE_DEBUGGING`) — 단계별 시간 (`WidgetsPreUpdate`/`WidgetsAttribute`/`WidgetsPrepass`/`WidgetsUpdate`/`InvalidationProcessing`).

### 7.3 FSlateDebugging 콜백 (코드)

```cpp
#if WITH_SLATE_DEBUGGING
FSlateDebugging::WidgetInvalidate.AddLambda([](const FSlateDebuggingInvalidateArgs& Args)
{
    UE_LOG(LogTemp, Log, TEXT("Invalidate: %s reason=%s"),
        *Args.Widget->GetTypeAsString(),
        *LexToString(Args.InvalidateReason));
});
#endif
```

자주 발행하는 위젯 식별 가능. 자세히 [`SlateCore/references/Trace.md §4`](../skills/SlateCore/references/Trace.md).

---

## 8. 핵심 원칙 7가지

1. **`URichTextBlock` 자주 갱신 회피** — `STextBlock` 으로 분리하거나 갱신 빈도 throttle.
2. **`UListView` 의 `RequestListRefresh` 빈도 최소화** — `IUserListEntry::OnListItemObjectSet` 콜백으로 데이터만 갱신.
3. **`Throbber`/`NativeOnPaint` override 위젯** 은 `UInvalidationBox` 외부에.
4. **`SetVisibility(Collapsed)` 잦은 토글 회피** — `Hidden` 또는 `SetRenderOpacity(0)` 으로.
5. **`UCanvasPanelSlot::SetPosition` 드래그 중** → `SetRenderTransform` 으로 대체.
6. **`NativeTick` 마지막 수단** — 이벤트 기반 → ActiveTimer → Tick 순.
7. **`Slate.InvalidationDebugging.IsEnabled 1`** 로 실측 — 추정으로 최적화하지 말 것.

---

## 9. 갱신 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-03 | 최초 작성. 위젯별 핫스팟 8묶음 + UInvalidationBox 결정 트리 + ForceVolatile 결정 트리 + NativeTick 회피 가이드 + setter trigger 표 + 디버그 cvar/Insights/FSlateDebugging. |
