---
type: source
title: "UE SlateCore — EWidgetClipping + OnPaint cull rect (위젯 영역 클리핑 표준)"
slug: ue-slatecore-clipping
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Clipping.md
source_kind: enriched
source_date: 2026-05-19
ingested: 2026-05-19
last_updated: 2026-05-19
cycle: 5p+5
tier: enriched
related_concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
  - "[[concepts/Slate-Invalidation]]"
related_sources:
  - "[[sources/ue-slatecore-types]]"
  - "[[sources/ue-slatecore-swidget]]"
  - "[[sources/ue-slatecore-drawing]]"
  - "[[sources/ue-slate-layoutwidgets]]"
  - "[[sources/ue-ref-06-invalidationhotspots]]"
trigger: "KMCProject MCComboEditor Cycle 5p+5 — TransformTrack sub-row paint 가 Outliner/TrackArea SSplitter 경계 너머로 흘러나간 시각 함정 (image 보고). EWidgetClipping 정책 명시 회피 — Sequencer-lite 일반화. Cycle 5p+5 evaluator Minor 1 정정 (enum 5종 정확화)."
tags: [ue, slate, slatecore, clipping, widget-clipping, ewidgetclipping, settoolclipping, onpaint, cull-rect, viewport, scissor, sscrollbar]
---

# UE SlateCore — EWidgetClipping + OnPaint cull rect

> Source: `Engine/Source/Runtime/SlateCore/Public/Layout/Clipping.h` L19-L54 (EWidgetClipping enum) + `SWidget.h` L1240/L1243/L1827 (SetClipping API + member) + KMCProject Cycle 5p+5 실측 사례.
> Parent: [[sources/ue-slatecore-skill]] · pair: [[sources/ue-slatecore-types]] §EWidgetClipping

## 1. Summary

Slate widget paint 가 자신의 `AllottedGeometry` 영역 (또는 그 안의 child) 밖으로 흘러나가는 것을 제어하는 두 메커니즘:

1. **`EWidgetClipping` 정책** — widget 단위 명시 (Construct 또는 SetClipping). 자식 paint 가 부모 영역 밖 표시될 지 결정.
2. **`OnPaint MyCullingRect`** — Slate framework 가 매 paint 마다 전달하는 자동 cull rect. cull rect 밖 `FSlateDrawElement::Make*` 호출은 paint queue 에서 자동 제외.

두 메커니즘은 **독립** — Clipping 은 자식 widget 전체에 적용 (paint queue 전부 자동 mask), CullingRect 는 OnPaint 안 명시 draw element 만 cull.

## 2. EWidgetClipping enum 5종 (`Layout/Clipping.h` L19-L54)

⚠ Engine 권위 verify (Cycle 5p+5 evaluator 정정) — 본 enum 은 **5종** (이전 cycle vault 작성 시 "OnDemand_NoChildren" 가공명 + "ClipToBoundsAlways" 누락 → 정정).

| 값 | 동작 | Construct 비용 | runtime 변경 비용 |
| -- | -- | -- | -- |
| `Inherit` (default) | 부모로부터 상속 — root widget 부터 ClipToBounds 가 한 번도 set 안 됐으면 자식이 자유롭게 overflow | 0 | 0 |
| `ClipToBounds` | 자기 AllottedGeometry 으로 자식 paint 강제 clip — Slate framework 가 scissor rect 적용. 부모 clip rect 와 intersect 됨 | 0 | Layout reason (중간) |
| `ClipToBoundsWithoutIntersecting` | self bounds 만 — 부모 clip rect 와 intersect 안 함 (부모 영역 밖이지만 자기 영역 안인 paint 가능) | 0 | Layout reason |
| `ClipToBoundsAlways` | 항상 ClipToBounds (부모가 Inherit 으로 set 했어도 강제 적용) — 자식이 부모를 override | 0 | Layout reason |
| `OnDemand` | 자식 desired size 가 자기보다 크면 lazy clip — Slate 가 자동 판단 (no clip when content fits) | 0 | Layout reason |

**enum 선택 결정 트리**:
- 일반 panel (Splitter 자식 / nested container) → `ClipToBounds` (가장 흔함, 부모 clip rect 와 자연스럽게 intersect)
- top-level widget 또는 부모 무관 clip 강제 → `ClipToBoundsAlways`
- 부모 영역 너머까지 보여주고 싶음 (popup / tooltip 표준은 아님) → `ClipToBoundsWithoutIntersecting`
- content fits 시 clip overhead 회피 → `OnDemand`
- 명시 의도 없으면 → `Inherit` (default)

**권장 사용 빈도** ([[sources/ue-ref-06-invalidationhotspots]] §6 표 권위):
- `SetClipping(EWidgetClipping)` → Layout reason 트리거 → **중간 비용**
- **권장: 드뭄** (Construct 1회만 set, 런타임 변경 회피)

## 3. SetClipping API (SWidget.h L1240/L1243/L1827)

```cpp
class SWidget {
public:
    /** Construct 또는 runtime 변경 — Invalidate(Layout) 자동 발행. */
    SLATECORE_API void SetClipping(EWidgetClipping InClipping);  // L1240

    /** Read-only getter. */
    EWidgetClipping GetClipping() const { return Clipping; }     // L1243

private:
    EWidgetClipping Clipping;                                     // L1827 — uint8 멤버
};

// SCompoundWidget 자손 안 — 둘 중 하나:

// 패턴 A — SLATE_ARGUMENT 안 .Clipping(...) 명시 (SCompoundWidget 기본 제공).
SNew(SMyPanel).Clipping(EWidgetClipping::ClipToBounds);

// 패턴 B — Construct 안 SetClipping 직접 호출.
void SMyPanel::Construct(const FArguments& InArgs)
{
    ChildSlot[ /* ... */ ];
    SetClipping(EWidgetClipping::ClipToBounds);  // Construct 마지막 줄 표준 패턴
}
```

⚠ **runtime 빈번 호출 금지** — `SetClipping` 은 Layout reason 발행 → 자식 트리 prepass + 재배치 ([[sources/ue-ref-06-invalidationhotspots]] §2 "Layout" 비용 **높음").

## 4. OnPaint MyCullingRect — 자동 cull (independent)

`SWidget::OnPaint` 의 3번째 매개변수 `MyCullingRect` (FSlateRect) — Slate framework 가 매 paint 마다 widget visible 영역으로 미리 계산해 전달. `FSlateDrawElement::Make*` 가 호출되더라도 좌표가 cull rect 밖이면 paint queue 에 추가 안 됨.

```cpp
int32 SMyPanel::OnPaint(const FPaintArgs& Args,
                        const FGeometry& AllottedGeometry,
                        const FSlateRect& MyCullingRect,    // ← 자동 cull 경계
                        FSlateWindowElementList& OutDrawElements,
                        int32 LayerId,
                        const FWidgetStyle& InWidgetStyle,
                        bool bParentEnabled) const
{
    // MakeBox/MakeLines/MakeText 가 MyCullingRect 밖 좌표를 받으면 자동 cull.
    FSlateDrawElement::MakeBox(
        OutDrawElements, LayerId,
        AllottedGeometry.ToPaintGeometry(/* offset 가 cull rect 밖이면 자동 skip */ ...),
        ...
    );
}
```

⚠ **명시 cull 권장**: cull rect 밖 좌표 element 도 `Make*` 호출 비용 (작성 + push) 은 발생. 시간축 ruler tick / sub-row diamond 처럼 많은 element 작성 시 명시 cull 의무:

```cpp
const float PxX = FrameToPixelX(Geometry, KeyGlobalFrame);
if (PxX < -DiamondSize || PxX > Size.X + DiamondSize) continue;  // 명시 cull
FSlateDrawElement::MakeLines(...);
```

## 5. EWidgetClipping vs MyCullingRect — 결정 트리

| 시나리오 | 권장 | 이유 |
| -- | -- | -- |
| 자식 widget 전체 (STableRow / SBox / 등) 가 overflow 가능성 | **EWidgetClipping::ClipToBounds** (Construct 1회) | 자식 paint 전부 자동 mask — 명시 cull 불가능 |
| OnPaint 안 직접 `Make*` 호출하는 leaf widget (custom timeline 등) | **명시 cull `if (PxX < -X || PxX > Size.X + X) continue`** | element 작성 비용 자체 회피 (cull rect 자동 처리는 push 후 cull) |
| SSplitter / SSplitterPanel 자식 panel | **양쪽 자식 모두 ClipToBounds** | splitter 경계 너머 paint 흘러나감 회피 (KMCProject Cycle 5p+5 실측 함정) |
| zoom + pan viewport (custom timeline) | **ClipToBounds + 명시 cull 양쪽** | zoom 시 sub-row label / tick 모두 viewport 밖 → 둘 다 작동 의무 |
| 부모 Clipping 무관 강제 clip (e.g., modal popup 영역) | **ClipToBoundsAlways** | 부모가 Inherit 으로 set 해도 자식이 자기 영역 강제 |

## 6. KMCProject 실측 함정 — Outliner ↔ TrackArea SSplitter 경계 overflow

**증상** (Cycle 5p+5 image 보고):
- Outliner Track row 의 SHorizontalBox 안 STextBlock ("Transform") 이 SSplitter 좌측 panel width 보다 길어짐
- splitter line 너머로 paint 가 흘러나가 우측 TrackArea 영역과 시각 충돌
- 사용자가 splitter drag 으로 좁히면 텍스트가 잘리지 않고 ghost 처럼 우측 panel 영역 침범

**원인**:
- SMCComboOutlinerView (좌측) + SMCComboTrackArea (우측) 모두 `EWidgetClipping::Inherit` (default)
- SSplitter 가 size 만 분배할 뿐 자식 panel 의 paint clip 은 강제 안 함
- STableRow / SHorizontalBox 의 텍스트 element 가 자유롭게 우측 panel 영역까지 paint

**fix (2 line 추가, Cycle 5p+5 적용)**:
```cpp
// SMCComboOutlinerView::Construct (Construct 마지막 줄):
SetClipping(EWidgetClipping::ClipToBounds);

// SMCComboTrackArea::Construct (Construct 마지막 줄):
SetClipping(EWidgetClipping::ClipToBounds);
```

**효과**:
- splitter 경계 (좌/우 panel) 외 paint 자동 mask
- STableRow 안 STextBlock 이 overflow 시 잘림 ("Tra…")
- sub-row label / per-channel diamond 가 TrackArea bounds 외 (좌측 6px label 영역) 자동 cull

## 7. 자매 메커니즘 — Horizontal scrollbar (SScrollBar) 양방향 binding

⚠ scope note: SScrollBar 자체는 `Slate` 모듈 (SlateCore 아님). 본 §은 Cycle 5p+5 사례 통합 의 편의로 포함 — 분리 페이지 후보.

zoom 시 visible window 가 PlaybackDuration / ViewZoomFactor — 사용자가 어디 보고 있는지 시각화 + drag pan 표준:

**Engine 권위**: `Engine/Source/Runtime/Slate/Public/Widgets/Layout/SScrollBar.h`
- `void SetState(float InOffsetFraction, float InThumbSizeFraction, bool bCallOnUserScrolled = false)` (L97) — thumb 위치 + 크기 직접 set. **3번째 인자 default `false` → OnUserScrolled callback 재발행 안 함 (re-entrancy 안전)**.
- `SLATE_EVENT(FOnUserScrolled, OnUserScrolled)` (L21/L53) — 사용자 drag broadcast (InOffsetFraction)

**Mapping (KMCProject Cycle 5p+5 사례)**:
```
ThumbSizeFraction = 1.0 / ViewZoomFactor    (1.0 = full / 50x = 1/50)
OffsetFraction    = ViewStartAlpha * (1.0 - ThumbSizeFraction)
```

**역변환 (사용자 drag → ViewStartAlpha)**:
```
ViewStartAlpha = OffsetFraction / max(eps, 1.0 - ThumbSizeFraction)
```

**TrackArea ↔ ScrollBar 양방향 sync 패턴**:
- TrackArea OnMouseWheel / SetViewStartAlpha → `FOnViewportChanged` delegate broadcast → Timeline `HandleViewportChanged` → `ScrollBar->SetState(...)` 갱신
- ScrollBar OnUserScrolled → Timeline `HandleHorizontalScrolled` → `TrackArea->SetViewStartAlpha(...)`

**re-entrancy 안전성**: `SetState` 3번째 인자 default `false` 라 `SetState` → `OnUserScrolled` 재발행 안 함 → guard flag 불필요. 단 `true` 명시 시 무한 루프 risk → 호출처 명시 `false` 주석 권장.

## 8. 자매 메커니즘 — STableViewBase scroll offset (item-space vs pixel-space)

**Engine 권위**: `Engine/Source/Runtime/Slate/Public/Widgets/Views/STableViewBase.h`
- `float GetScrollOffset() const` (L170) — **item 단위** (1.0 = 1 STableRow)
- `void SetScrollOffset(float InScrollOffset)` (L173) — 동일 item 단위
- `DECLARE_DELEGATE_OneParam(FOnTableViewScrolled, double /*InScrollOffset*/)` (L75) — item 단위

⚠ **함정**: 외부 widget 이 pixel 단위 scroll offset 을 기대하는 경우 변환 필수.

**KMCProject Cycle 5p+5 hotfix**:
- 증상: Outliner ~5 items 스크롤 시 TrackArea 거의 안 움직임 (28× under-applied)
- 원인: `OnTreeViewScrolled(double InScrollOffset)` 가 item 단위 (1.0 = 1 row) 인데 `TrackArea::SetVerticalScrollOffset(float InOffsetPx)` 는 pixel 단위
- fix: `static_cast<float>(InScrollOffset) * LaneHeight (28.0f)` 곱셈
- ⚠ 다중 lane Track (HeightOverride 56/84/…) 시 단순 곱셈 누적 desync — 더 정확한 sync 위해 pixel 단위 `GetScrollOffset` 알고리즘 (Engine STableViewBase 내부 계산) 또는 RowHeight 가중치 합산

## 9. 함정 카탈로그

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | SSplitter 자식 panel 이 default Inherit 일 때 splitter 경계 overflow | 양쪽 panel Construct 안 `SetClipping(ClipToBounds)` |
| 2 | `SetClipping` 매 frame 호출 (TAttribute 잘못 사용) | Construct 1회만 — Layout reason 비용 회피 |
| 3 | cull rect 밖 `MakeLines` 수만 push (push 후 cull, 작성 비용은 발생) | 명시 `if (PxX < ... || PxX > ...) continue` 가드 |
| 4 | SScrollBar SetState 가 OnUserScrolled 재진입 트리거 | `SetState` 3번째 인자 default `false` — Engine 내부 guard. 단 plumbing 변경 시 명시 |
| 5 | zoom 변경 후 SScrollBar thumb 갱신 누락 | TrackArea 측 delegate broadcast 의무 (OnViewportChanged) |
| 6 | ClipToBounds + render transform 조합 시 transform 영역까지 clip | render transform widget 은 별도 SOverlay + Clipping::Inherit 둘러싸기 |
| 7 | STableViewBase OnTreeViewScrolled item-unit → 외부 pixel-unit 오해 | `OutlinerView->GetScrollOffset() * RowHeight` 또는 pixel-space API 사용. 다중 lane 시 단순 곱셈 누적 desync |
| 8 | `ClipToBounds` 와 `ClipToBoundsWithoutIntersecting` 혼용 | 부모 clip rect 와 intersect 여부 의식. 대부분 `ClipToBounds` 가 정답 (intersect 활성). 부모 영역 밖이지만 자기 영역 안 paint 필요 시만 후자 |

## 10. Cross-link

### vault sources
- [[sources/ue-slatecore-types]] §EWidgetClipping (enum 단순 정의 — 5종으로 정정 필요)
- [[sources/ue-slatecore-swidget]] §SWidget API
- [[sources/ue-slatecore-drawing]] FSlateDrawElement / ToPaintGeometry
- [[sources/ue-slate-layoutwidgets]] §SScrollBox (자동 scroll 컨테이너 — 단순 케이스)
- [[sources/ue-ref-06-invalidationhotspots]] §6 SetClipping Layout reason 비용 표

### concepts
- [[concepts/Slate-Paint-Cycle]] — OnPaint 사이클
- [[concepts/Slate-Invalidation]] — Layout reason 비용

### KMCProject 사례
- [[synthesis/mc-combo-editor-levelsequence-lite]] §5.11 (Cycle 5p+5 — Clipping + SScrollBar fix + scroll sync hotfix)
- [[synthesis/timeline-custom-slate-widget-pattern]] §16 (Clipping + Horizontal scrollbar 일반화)

## 11. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-19 (Cycle 5p+5) | 최초 작성 — EWidgetClipping enum 4종 (잘못된 "OnDemand_NoChildren" 가공명 포함) + SetClipping API + OnPaint MyCullingRect 자동 cull + 결정 트리 (Clipping vs CullingRect) + SSplitter 자식 overflow 함정 + SScrollBar 양방향 binding 보조 + 6 함정 카탈로그. KMCProject Cycle 5p+5 사례 inline. |
| **2026-05-19 (Cycle 5p+5 evaluator Minor 1 정정)** | **§2 enum 표 정정 — 4종 → 5종 (Inherit / ClipToBounds / ClipToBoundsWithoutIntersecting / ClipToBoundsAlways / OnDemand) + "OnDemand_NoChildren" 가공명 제거 + "ClipToBoundsAlways" / "ClipToBoundsWithoutIntersecting" 신규 추가. Engine 권위 `Clipping.h L19-L54` verify. §2 enum 선택 결정 트리 신규 추가. §3 SetClipping API 권위 라인 보강 (L1240/L1243/L1827). §5 결정 트리 ClipToBoundsAlways 행 추가. §7 SScrollBar `SetState` 3번째 인자 `bCallOnUserScrolled` default `false` 명시 (re-entrancy 안전성). §8 STableViewBase scroll offset (item-space vs pixel-space) 신규 sub-§ (KMCProject Cycle 5p+5 hotfix 사례). §9 함정 카탈로그 6→8 (item-unit/pixel-unit 오해 + ClipToBounds 변형 혼용). frontmatter trigger 에 evaluator Minor 1 정정 명시.** |
