---
type: synthesis
title: "UE 5.7.4 Custom Timeline Slate Widget — Sequencer-lite 패턴 (KMCProject 사례 일반화)"
slug: timeline-custom-slate-widget-pattern
created: 2026-05-18
last_updated: 2026-05-19
project_role: general-pattern
project: vault-general
measured_date: 2026-05-19
status: living
cycle: 5p+5
tier: enriched
sources:
  - "[[sources/ue-levelsequence-moviescene]]"
  - "[[sources/ue-levelsequence-tracks]]"
  - "[[sources/ue-levelsequence-sequencer]]"
  - "[[sources/ue-slate-liststrees]]"
  - "[[sources/ue-slate-layoutwidgets]]"
  - "[[sources/ue-slatecore-drawing]]"
  - "[[sources/ue-slatecore-clipping]]"
  - "[[sources/ue-slatecore-input]]"
  - "[[sources/ue-slate-application]]"
  - "[[sources/ue-editor-asseteditorapi]]"
  - "[[sources/ue-editor-advancedpreviewscene]]"
  - "[[sources/ue-coreuobject-uobject]]"
  - "[[sources/ue-coreuobject-serialization]]"
  - "[[sources/ue-animation-animinstance]]"
  - "[[synthesis/mc-combo-editor-levelsequence-lite]]"
  - "[[synthesis/mc-combo-section-levelsequence-style-upgrade]]"
entities:
  - "[[entities/SWidget]]"
  - "[[entities/FSlateDrawElement]]"
  - "[[entities/IToolkit]]"
  - "[[entities/FTabManager]]"
concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
  - "[[concepts/Slate-Invalidation]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [synthesis, ue-general, timeline, custom-slate, sequencer-lite, anim-notify-track, paint-cycle, drag-mode, sort-cache, lane-allocation, zoom-pan, ruler-tick, hatched-pattern, fscoped-transaction, kmcproject-case-study, ewidgetclipping-cliptobounds, horizontal-scrollbar-viewport-binding, sscrollbar-setstate]
citation_disclosure: "🟢 28+ (vault enriched 16 + KMCProject 실측 5 phase + Engine 권위 직접 verify) / 🟡 0 / 🔴 0"
---

# UE 5.7.4 Custom Timeline Slate Widget — Sequencer-lite 패턴

> **목적**: LevelSequence Sequencer 풀스택을 회피하면서 시간축 기반 Section/Track 편집 UI를 자체 Slate 로 구현하는 일반 패턴 가이드. KMCProject MCComboEditor (Phase 2-5p+8 + Cycle 5p+5) 실측 사례 통합.
>
> **사용처**: 콤보/스토리/시네마틱 외 도메인 특화 시간축 자산 에디터 — Sequencer 의 데이터 모델 (Track + Section + FFrameNumber) 차용하되 Sequencer 모듈 의존을 회피하고 싶은 모든 프로젝트.
>
> **vault scope policy** ([[00_meta/08_VaultScopePolicy]]): 본 페이지는 **UE 일반 영역 (96% scope)** — KMCProject 사례를 inline case study 으로 인용하나 패턴 자체는 모든 프로젝트 적용 가능.

## 1-12 (결정 트리, 핵심 클래스, OnPaint 9-Layer, Drag mode, Sort cache, Lane allocation, Cursor-anchored zoom, Ruler tick, Section paint, NotifyTrackChanged chain, FScopedTransaction drag 1-entry, Outliner row 동적 height — 기존 본문 유지)

## 13. 함정 카탈로그 (40+ from KMCProject 누적)

KMCProject Phase 2-5p+8 + Cycle 5p+5 누적 함정 — 본 일반 패턴 적용 시 회피 의무:

| # | 함정 | 회피 |
| -- | -- | -- |
| 1-39 | (기존 39 카탈로그 — Phase 2c-4g) | (기존) |
| 40 | C3668 base non-virtual override (UMCComboTrack::AddSection 비-virtual 에 자손이 override 시도) | 베이스 `virtual` 격상. 일반화: virtual override 추가 전 base class header grep 의무, C3668 발생 시 90% — (1) base non-virtual, (2) 시그니처 불일치, (3) virtual 누락 |
| 41 | STreeView OnExpansionChanged spurious 콜백 (ApplyExpansionRecursive 안 SetItemExpansion 재진입) | UObject 측 영속 상태 vs Slate 측 인자 비교 후 (`(!!UObj->b*) != bInExpanded`) 만 Modify — dirty 폭주 회피 |
| 42 | RebuildTree 가 STreeView callback (OnExpansionChanged) 안 호출 시 reentrancy risk | `MarkPackageDirty` 만 호출 — RebuildTree 미호출 (TrackArea 는 다음 paint cycle 안 UObject 상태 자동 반영) |
| **43** (Cycle 5p+5) | **SSplitter 자식 panel 의 paint overflow** — Outliner/TrackArea default `EWidgetClipping::Inherit` 시 splitter 가 size 만 분배할 뿐 paint clip 강제 안 함. STableRow STextBlock 이 widget bounds 너머 ghost paint. zoom 시 sub-row label/diamond 도 동일 risk | 양쪽 panel `Construct` 안 `SetClipping(EWidgetClipping::ClipToBounds)` 1회 호출. Engine `SlateCore/Public/Layout/Clipping.h` 권위. 비용 = Layout reason 1회 |

→ KMCProject 사례 상세: [[synthesis/mc-combo-editor-levelsequence-lite]] §7.1.
→ Clipping/SScrollBar 일반화: [[sources/ue-slatecore-clipping]] §6-§8.

## 14. Engine 권위 매트릭스 (UE 5.7.4 — verify 완료)

(기존 26 행 + Cycle 5p+5 신규 2 행)

| 파일 | 라인 | 인용 |
| -- | -- | -- |
| (기존 26 행 보존) | (기존) | (기존) |
| **`Engine/Source/Runtime/SlateCore/Public/Layout/Clipping.h`** | **EWidgetClipping enum** | **Inherit / OnDemand / ClipToBounds / OnDemand_NoChildren — SSplitter 자식 panel paint overflow 회피 표준** |
| **`Engine/Source/Runtime/SlateCore/Public/Widgets/Layout/SScrollBar.h`** | **SetState(InOffsetFraction, InThumbSizeFraction) + FOnUserScrolled delegate** | **Horizontal SScrollBar 양방향 binding (zoom visible window 시각 + drag pan) — ThumbSize = 1/Zoom, Offset = Alpha × (1 - ThumbSize)** |

## 15. KMCProject 사례 매핑

| 패턴 sub-§ | KMCProject phase | 위치 |
| -- | -- | -- |
| (기존 14 행 — Phase 2c~4g-hotfix3b) | (기존) | (기존) |
| §3 OnPaint Phase 5p+8 sub-row paint (13 sub-rows + per-channel mini-diamond) | Phase 5p+8 | SMCComboTrackArea.cpp OnPaint sub-row loop |
| §13 함정 40 (C3668 base non-virtual AddSection) | Phase 5p+7 | MCComboTrack.h virtual 격상 |
| §13 함정 41-42 (STreeView OnExpansionChanged spurious + RebuildTree reentrancy) | Phase 5p+8 | SMCComboOutlinerView::HandleExpansionChanged |
| **§13 함정 43 (SSplitter 자식 panel paint overflow)** | **Cycle 5p+5** | **SMCComboOutlinerView/SMCComboTrackArea Construct SetClipping(ClipToBounds)** |

## 16. ⭐⭐ Clipping + Horizontal Viewport Scrollbar (Cycle 5p+5 신규 sub-§)

### 16.1 SSplitter 자식 panel clipping 의무

→ Engine 권위: `Engine/Source/Runtime/SlateCore/Public/Layout/Clipping.h` — EWidgetClipping enum.
→ vault 상세: [[sources/ue-slatecore-clipping]].

SSplitter 가 size 만 분배하고 paint clip 은 강제 안 함 → 자식 panel 의 STableRow / STextBlock 이 splitter 경계 너머로 흘러나갈 risk. 양쪽 자식 panel Construct 1회 `SetClipping(EWidgetClipping::ClipToBounds)` 표준 패턴:

```cpp
void SCustomTimelineOutliner::Construct(const FArguments& InArgs)
{
    ChildSlot[ /* tree view */ ];
    SetClipping(EWidgetClipping::ClipToBounds);   // ⭐ Construct 마지막 줄
}

void SCustomTimelineTrackArea::Construct(const FArguments& InArgs)
{
    ChildSlot[ /* null or content */ ];
    SetClipping(EWidgetClipping::ClipToBounds);   // ⭐ Construct 마지막 줄
    SetToolTipText(TAttribute<FText>::CreateSP(...));
}
```

**비용**: Layout reason 1회 (Construct 1회만 set, 런타임 변경 회피). [[sources/ue-ref-06-invalidationhotspots]] §6 권위.

### 16.2 OnPaint 안 명시 cull (CullingRect 보강)

SWidget::OnPaint 의 `MyCullingRect` 가 paint queue 안 element 를 자동 cull 하지만, `FSlateDrawElement::Make*` 호출 비용은 발생 — element 가 많은 경우 (ruler tick × N 초 × FPS / 13 sub-row × N keys) 명시 cull 의무:

```cpp
const float PxX = FrameToPixelX(Geometry, KeyGlobalFrame);
if (PxX < -DiamondSize || PxX > Size.X + DiamondSize) continue;  // 명시 cull
FSlateDrawElement::MakeLines(...);
```

→ KMCProject TrackArea ruler tick (§8) + sub-row diamond (Phase 5p+8) 양쪽 적용.

### 16.3 Horizontal Viewport Scrollbar (zoom visible window 시각)

→ Engine 권위: `Engine/Source/Runtime/SlateCore/Public/Widgets/Layout/SScrollBar.h` — `SetState(InOffsetFraction, InThumbSizeFraction)` + `FOnUserScrolled` delegate.

zoom + pan 만 있고 scrollbar 없으면 사용자가 visible window 위치/크기 시각 정보 부재. Horizontal SScrollBar 양방향 binding 표준:

**Mapping 공식**:
```
ThumbSizeFraction = 1.0 / ViewZoomFactor       (1.0 zoom = full thumb, 50x = 1/50)
OffsetFraction    = ViewStartAlpha * (1.0 - ThumbSizeFraction)
// 역변환 (사용자 drag → ViewStartAlpha):
ViewStartAlpha    = OffsetFraction / max(eps, 1.0 - ThumbSizeFraction)
```

**Delegate 양방향 sync 패턴**:

```cpp
// SCustomTimelineTrackArea.h
DECLARE_DELEGATE(FOnViewportChanged);

SLATE_BEGIN_ARGS(SCustomTimelineTrackArea) {}
    SLATE_ARGUMENT(...)
    SLATE_EVENT(FOnViewportChanged, OnViewportChanged)
SLATE_END_ARGS()

FOnViewportChanged OnViewportChangedDelegate;

// SCustomTimelineTrackArea.cpp Construct
OnViewportChangedDelegate = InArgs._OnViewportChanged;

// SCustomTimelineTrackArea.cpp OnMouseWheel / SetViewStartAlpha
ViewZoomFactor = ...; ViewStartAlpha = ...;
Invalidate(EInvalidateWidgetReason::Paint);
OnViewportChangedDelegate.ExecuteIfBound();  // ⭐ Timeline → SScrollBar SetState 트리거

// SCustomTimeline.cpp Construct (SSplitter 직후 슬롯)
+ SVerticalBox::Slot().AutoHeight()
[
    SAssignNew(HorizontalScrollBar, SScrollBar)
        .Orientation(Orient_Horizontal)
        .Thickness(FVector2D(8.0f, 8.0f))
        .OnUserScrolled(this, &SCustomTimeline::HandleHorizontalScrolled)
]

// SCustomTimeline.cpp handlers
void SCustomTimeline::HandleHorizontalScrolled(float InOffsetFraction)
{
    const float Zoom = TrackArea->GetViewZoomFactor();
    const float ThumbSize = (Zoom > 0.0f) ? (1.0f / Zoom) : 1.0f;
    const float TrackSpan = FMath::Max(1e-4f, 1.0f - ThumbSize);
    const float NewAlpha = FMath::Clamp(InOffsetFraction / TrackSpan, 0.0f, 1.0f);
    TrackArea->SetViewStartAlpha(NewAlpha);  // ⭐ 역변환 + setter chain
}

void SCustomTimeline::HandleViewportChanged()
{
    const float Zoom = TrackArea->GetViewZoomFactor();
    const float Alpha = TrackArea->GetViewStartAlpha();
    const float ThumbSize = FMath::Clamp(1.0f / Zoom, 0.02f, 1.0f);
    const float Offset = Alpha * FMath::Max(0.0f, 1.0f - ThumbSize);
    HorizontalScrollBar->SetState(Offset, ThumbSize);  // ⭐ 직접 SetState
}
```

**Re-entrancy 회피**: SScrollBar::SetState 가 OnUserScrolled callback 재트리거 안 함 (Engine 내부 guard) — `bSyncingScroll` guard flag 불필요. (반면 OnTreeViewScrolled / SetScrollOffset 사이는 재진입 가능 — Phase 3c §B `bSyncingScroll` 명시 guard 의무.)

### 16.4 결정 트리 — 어디에 적용?

| 시나리오 | Clipping | Scrollbar |
| -- | -- | -- |
| SSplitter 자식 panel (Outliner / TrackArea / 등) | **ClipToBounds 의무** | (Track row scroll 은 STreeView 내장 — STableViewBase L170/L173) |
| Zoom + pan viewport (TrackArea) | ClipToBounds (sub-row label/diamond cull 추가) | **Horizontal SScrollBar 의무** (사용자 visible window 시각) |
| 단순 list / static panel | Inherit (default) OK | (필요 시 SScrollBox) |

## 17. Cross-link

### vault sources (vault scope policy — UE 일반 96%)

→ frontmatter sources 매트릭스 16 sources. 핵심:
- [[sources/ue-levelsequence-moviescene]] §2.5 (FFrameNumber/FFrameRate/UMovieSceneSection 데이터 모델 권위)
- [[sources/ue-levelsequence-tracks]] §5 (UMovieSceneSkeletalAnimationSection)
- [[sources/ue-slatecore-drawing]] (FSlateDrawElement)
- [[sources/ue-slatecore-clipping]] **(Cycle 5p+5 신규)** — EWidgetClipping + OnPaint MyCullingRect + SScrollBar 양방향 binding
- [[sources/ue-slatecore-input]] (OnCursorQuery / OnMouseWheel)
- [[sources/ue-slate-liststrees]] (STreeView)
- [[sources/ue-coreuobject-serialization]] §5 + §5.7

### KMCProject 사례 (vault scope policy — mc- 4%)

- [[synthesis/mc-combo-editor-levelsequence-lite]] (Phase 1-5p+8 + Cycle 5p+5 누적 합성)
- [[synthesis/mc-combo-section-levelsequence-style-upgrade]] (Phase 2 handoff)

### Governance

- [[00_meta/08_VaultScopePolicy]] §3 (mc- ↔ ue- reverse-link 의무)
- [[00_meta/03_EvaluatorRecipe]] §1.5 (Engine Authority Verification)

## 18. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-18 (Cycle 5p+3) | 최초 작성 — KMCProject MCComboEditor Phase 2-4g 누적 사례를 UE 일반 패턴으로 격상. §1-§16 (기존 §17→§17/Cross-link, §17→§18 변경 이력) 완성. 39+ 함정 카탈로그 / Engine 권위 27+ 인용 매트릭스 / 14 sub-§ KMCProject 사례 매핑. vault scope policy 준수 (UE 일반 96% 영역). |
| **2026-05-19 (Cycle 5p+5 — Clipping + Horizontal scrollbar 일반화 추가)** | **§13 함정 카탈로그 4 행 신규 (40 C3668 base non-virtual / 41 STreeView spurious 콜백 / 42 RebuildTree reentrancy / 43 SSplitter 자식 paint overflow). §14 Engine 권위 매트릭스 2 행 신규 (SlateCore/Public/Layout/Clipping.h EWidgetClipping enum / SlateCore/Public/Widgets/Layout/SScrollBar.h SetState + FOnUserScrolled). §15 KMCProject 사례 매핑 4 행 추가 (Phase 5p+8 sub-row paint / 함정 40-43 매핑). §16 sub-§ 4개 신규 (Clipping + Horizontal Viewport Scrollbar 일반화 — SSplitter 자식 clipping 의무 / OnPaint 명시 cull / Horizontal SScrollBar 양방향 binding 공식 + 코드 패턴 / 결정 트리). §17 Cross-link sources 매트릭스 [[sources/ue-slatecore-clipping]] 추가. frontmatter tags 3 추가 (ewidgetclipping-cliptobounds / horizontal-scrollbar-viewport-binding / sscrollbar-setstate). citation_disclosure 25+→28+ / Engine 권위 27+→29+건.** |
