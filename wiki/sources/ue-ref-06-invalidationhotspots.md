---
type: source
title: "UE refs — 06 InvalidationHotspots (Slate/UMG 인밸리데이션 hub)"
slug: ue-ref-06-invalidationhotspots
source_path: raw/ue-wiki-llm/references/06_InvalidationHotspots.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
  - "[[concepts/Slate-Paint-Cycle]]"
tags: [ue, reference, slate, umg, invalidation, hotspot, performance]
---

# UE refs — 06 InvalidationHotspots 🚨

> Source: [[raw/ue-wiki-llm/references/06_InvalidationHotspots.md]] · CLAUDE.md §0.1.4 cross-cutting 인덱스

## 1. Summary

Slate / UMG 위젯이 **자주 인밸리데이션을 발생시키는 케이스** 위젯별 분석 + 회피·완화 패턴. UI 성능 저하의 가장 흔한 원인. 위젯 7종 (STextBlock / URichTextBlock / SEditableText / SListView / SThrobber / NativeOnPaint / TAttribute 람다) hotspot 매트릭스 + InvalidationBox / ForceVolatile / NativeTick 회피 계층. 권위 concept = [[concepts/Slate-Invalidation]].

## 2. EInvalidateWidgetReason 8종 🟢

| reason | 비용 | 발생 시점 |
| -- | -- | -- |
| **`Layout`** | **높음** (자식 트리 prepass + 재배치) | desired size 변경 (텍스트 길이 / 자식 추가) |
| `Paint` | 중간 (해당 위젯 재페인트) | 색 / 이미지 / alpha 변경 |
| `Volatility` | 낮음 | 휘발성 토글 |
| **`ChildOrder`** | **높음** (Prepass + Layout 함의) | 자식 추가 / 제거 |
| `RenderTransform` | 낮음 | 회전 / 스케일 / 이동만 (레이아웃 변경 없음) |
| **`Visibility`** | **높음** (Layout 함의) | 가시성 변경 |
| `AttributeRegistration` | 매우 낮음 | TSlateAttribute 바인딩 / 언바인딩 |
| **`Prepass`** | **높음** | 자식 트리 desired size 재계산 |

`PaintAndVolatility` / `LayoutAndVolatility` 합성 reason 도 사용.

## 3. 위젯별 hotspot 매트릭스 🟢

| 위젯 | 주요 hotspot | 회피 전략 |
| -- | -- | -- |
| `STextBlock` / `UTextBlock` | `SetText` 매 프레임 호출 / `TAttribute<FText>` 람다 평가 | 변경 시만 setter / 5.x `TSlateAttribute` 자동 캐싱 |
| `URichTextBlock` | 전체 trying 재파싱 | DecoratorClasses 캐싱 / 큰 텍스트 분할 |
| `SEditableText` / `UEditableTextBox` | 매 키 입력 OnTextChanged | **`OnTextCommitted` 만 사용** (포커스 잃을 때) |
| `SListView` / `UListView` | `RequestListRefresh` / `RebuildList` 매 프레임 | Diff 기반 Add/Remove + `RegenerateAllEntries` |
| `SThrobber` / `UThrobber` | `bIsAnimating=true` → 매 Tick 페인트 | 사용 중에만 Visibility 토글 |
| `NativeOnPaint` override 위젯 | 자동 휘발성 / 캐시 비활성 | SLeafWidget 분리 + 외부에서 InvalidationBox |
| `TAttribute<T>` 람다 | 매 평가마다 람다 호출 | **`TSlateAttribute` 5.x** (자동 캐싱) |

## 4. UInvalidationBox 결정 트리 🟢

```
이 위젯/영역이 자주 변하나?
├─ NO  → UInvalidationBox 안에 ✅ (캐시 활용)
└─ YES
    ├─ 매 프레임? → UInvalidationBox 외부 + ForceVolatile(true) 검토
    └─ 일부만 변하나? → 변하는 부분만 분리해서 외부에 ✅✅
```

**✅ 사용해야 할 곳**: 메인 메뉴 헤더 / 인벤토리 슬롯 배경 / 캐릭터 정보 패널 정적 부분 / BP 그래프 정적 노드.

**❌ 두지 말아야 할 곳**: `URichTextBlock` / `UThrobber` (자동 휘발성) / `NativeOnPaint` override / `ForceVolatile(true)` / 자주 갱신 `UProgressBar` (체력바) / `UListView` 안에 (자체 가상화).

## 5. NativeTick 회피 계층 🟢

```
1. 이벤트 기반 (Delegate) — 데이터 변경 시 setter 호출 ✅✅✅
2. RegisterActiveTimer — Slate 자체 타이머 (자동 종료 가능) ✅✅
3. NativeTick — 매 프레임, TickFrequency 결정 ⚠
4. SetVolatile(true) + NativeOnPaint — 사용자 그리기 매 프레임 ❌
```

**EWidgetTickFrequency**: `Never` (정적 HUD / 메뉴 — 권장) · `Auto` (동적 HUD — BP tick / 애니메이션 / latent action 시 자동). 클래스 단위: `UCLASS(meta=(DisableNativeTick))`.

**RegisterActiveTimer 패턴**:

```cpp
ActiveTimerHandle = RegisterActiveTimer(/*ExecutionDelay=*/0.f,
    FWidgetActiveTimerDelegate::CreateSP(this, &SMy::TickAnim));

EActiveTimerReturnType SMy::TickAnim(double InCurrentTime, float InDeltaTime)
{
    if (Anim.IsPlaying()) return EActiveTimerReturnType::Continue;
    return EActiveTimerReturnType::Stop;   // 자동 해제
}
```

NativeTick 보다 가벼움 + 자동 종료 + TickFrequency 무관.

## 6. UWidget setter 자동 trigger 표

| setter | 자동 trigger reason | 비용 | 권장 빈도 |
| -- | -- | -- | -- |
| `SetVisibility(Visible↔Collapsed)` | `Visibility` (Layout 함의) | **높음** | 영구 변경만 |
| `SetVisibility(Visible↔Hidden)` | `Visibility` (공간 유지) | 중간 | 잦은 토글 |
| `SetIsEnabled(bool)` | `Paint` | 낮음 | 자유 |
| `SetRenderTransform(FWidgetTransform)` | `RenderTransform` | 낮음 | 매 프레임 OK |
| `SetRenderOpacity(float)` | `Paint` | 낮음 | 자유 |
| `SetClipping(EWidgetClipping)` | `Layout` | 중간 | 드뭄 |
| `SetCursor(EMouseCursor::Type)` | (없음) | 0 | 자유 |
| `ForceVolatile(true)` | `Volatility` | 한 번 | 신중 |

## 7. 디버그 / 측정

| 명령 | 효과 |
| -- | -- |
| `Slate.InvalidationDebugging.IsEnabled 1` | 인밸리데이션 발행 가시화 |
| `Slate.DrawElementsStats 1` | 프레임당 element 수 · DrawCall 카운트 |
| `Slate.ShowBatching 1` | DrawCall 배치 경계 색칠 |
| `Slate.GlobalInvalidation 1` | 전체 인밸리데이션 테스트 |
| `WidgetReflector` | 위젯 트리 시각화 + 클릭 식별 (에디터 🛠) |
| `stat Slate` / `stat SlateInvalidation` | 시간 측정 |
| `Trace.Start cpu,frame,gpu,slate` | Insights 트레이스 |

**FSlateDebugging** (`WITH_SLATE_DEBUGGING`) — `FSlateDebugging::WidgetInvalidate.AddLambda` 으로 자주 발행 위젯 식별. → [[sources/ue-slatecore-trace]] 🛠.

## 8. 핵심 원칙 7가지

1. **`URichTextBlock` 자주 갱신 회피** — `STextBlock` 분리 또는 throttle.
2. **`UListView::RequestListRefresh` 빈도 최소화** — `IUserListEntry::OnListItemObjectSet` 콜백.
3. **`Throbber` / `NativeOnPaint` 위젯** 은 `UInvalidationBox` 외부.
4. **`SetVisibility(Collapsed)` 잦은 토글 회피** — `Hidden` 또는 `SetRenderOpacity(0)`.
5. **`UCanvasPanelSlot::SetPosition` 드래그 중** → `SetRenderTransform`.
6. **`NativeTick` 마지막 수단** — 이벤트 → ActiveTimer → Tick.
7. **`Slate.InvalidationDebugging.IsEnabled 1`** 로 실측 — 추정 X.

## 9. Cross-link

- 권위 concept: [[concepts/Slate-Invalidation]] · [[concepts/Slate-Paint-Cycle]] · [[concepts/UMG-Super-Call-Convention]]
- 깊이 자료: [[sources/ue-ref-deep-invalidationhotspots]] (위젯별 정밀 코드 패턴)
- 자매 정책 hub: [[sources/ue-ref-07-profilingscopeRule]] (Tick / OnRep 스코프) · [[sources/ue-ref-04-overrideindex]] (RebuildWidget §3 사이클) · [[sources/ue-ref-08-overlaphotspots]] (Components hotspot 페어)
- 적용 카테고리: [[sources/ue-umg-skill]] · [[sources/ue-slatecore-skill]] · [[sources/ue-slate-skill]]
- 깊이 source: [[sources/ue-slatecore-drawing]] §4-5 (인밸리데이션 캐시) · [[sources/ue-umg-uwidget]] §5 · [[sources/ue-umg-uuserwidget]] §5 · [[sources/ue-umg-invalidationdeep]] (deep)
- Trace: [[sources/ue-slatecore-trace]] 🛠 (FSlateDebugging / Slate Insights)
