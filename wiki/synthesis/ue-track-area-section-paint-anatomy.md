---
type: synthesis
title: "UE Sequencer-lite Custom TrackArea — Section Paint Pipeline Anatomy (정확한 시각화 기반)"
slug: ue-track-area-section-paint-anatomy
created: 2026-05-19
last_updated: 2026-05-19
project_role: knowledge-pattern
project: cross-project
sources:
  - "[[sources/ue-slatecore-drawing]]"
  - "[[sources/ue-slatecore-swidget]]"
  - "[[sources/ue-slatecore-clipping]]"
  - "[[sources/ue-levelsequence-moviescene]]"
  - "[[sources/ue-levelsequence-sequencer]]"
  - "[[sources/ue-levelsequence-tracks]]"
  - "[[synthesis/timeline-custom-slate-widget-pattern]]"
  - "[[synthesis/ue-slate-custom-onpaint-layer-strategy]]"
  - "[[synthesis/ue-paint-hittest-shared-rowmap]]"
entities:
  - "[[entities/FSlateDrawElement]]"
  - "[[entities/FGeometry]]"
  - "[[entities/SWidget]]"
concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
status: living
tags: [synthesis, ue-slate, sequencer-lite, track-area, section-paint, onpaint-anatomy, frame-to-pixel, ease-curve-gradient, multi-stop-curve, blend-type-visualization, kmcproject-verified, paint-data-dependency-trap]
citation_disclosure: "🟢 12 (Engine source 직접 인용 + KMCProject MCComboEditor Phase 2-5e 실측 검증)"
---

# UE Sequencer-lite Custom TrackArea — Section Paint Pipeline Anatomy

> **One-liner**: 자체 Slate TrackArea 안 Section box paint = (1) Frame→Pixel 좌표계 + (2) Row Y 누적 layout + (3) Multi-Layer OnPaint (본체/border/EaseIn-Out gradient/weight bar/keyframe diamond) + (4) **데이터 의존 조건부 paint** (EaseInFrames>0 등). 시각화 미표시 원인의 90% = 데이터가 default 0 일 때 조건부 paint skip — paint 코드 자체 버그 아님.

## 1. Paint Pipeline 전체 흐름

```
SWidget::OnPaint(args, geometry, cullRect, drawElements, layerId, style, parentEnabled)
   ↓
[1] 좌표계 변환 helper 호출 — FrameToPixelX / PixelXToFrame
[2] Row layout 누적 — BuildPaintRows → 매 Row 의 RowY 계산
[3] 매 Row 안 매 Section 순회 (sort cache 적용)
[4] Section box paint — 9-Layer (L1 본체, L2 EaseIn/Out gradient, L3 reverse, L4 weight bar, L5+ 추가 정보)
[5] Ruler / Scrub head overlay (L10/L11 — content L0..L9 위)
   ↓
return LayerId + N  (가장 위 layer 반환)
```

본 문서는 [4] Section box paint 의 **9-Layer 정확 분해 + 데이터 의존성** 에 집중.

## 2. 좌표계 — Frame ↔ Pixel

### 2.1 Asset-global Frame Space

- Asset `PlaybackDuration` (FFrameNumber) 가 timeline 전체 길이
- 모든 Section 의 `SectionRange` (Start, End) 가 Asset frame 좌표
- TickResolution (보통 24000) 가 frame → seconds 변환 단위

### 2.2 Pixel Space (Slate AllottedGeometry)

- TrackArea 의 horizontal 크기 = `AllottedGeometry.GetLocalSize().X`
- Ruler height 22 + Track lane 영역 = 나머지 vertical

### 2.3 변환 helper

```cpp
float FrameToPixelX(const FGeometry& Geom, int32 GlobalFrame) const
{
    // Phase 4g cursor-anchored zoom 반영:
    //   VisibleFrameRange = PlaybackDuration / ViewZoomFactor
    //   ViewStartFrame    = (PlaybackDuration - VisibleFrameRange) × ViewStartAlpha
    //   X = (GlobalFrame - ViewStartFrame) / VisibleFrameRange × Geom.GetLocalSize().X
    // ViewZoomFactor==1.0 시 ViewStartFrame=0 → 단순 비례.
}

int32 PixelXToFrame(const FGeometry& Geom, float LocalPx) const
{
    // 역변환 — Drag/Click 시 사용.
}
```

⭐ **함정**: zoom/pan 적용 후 `Section StartPx < 0` 또는 `> Geom.LocalSize().X` 가능 — Slate clip 이 처리하지만 큰 음수 시 paint 비용 낭비. cull rect 검사로 skip 권장.

## 3. Row Y Layout — `BuildPaintRows` 누적

```cpp
struct FPaintRow
{
    enum class EType : uint8 { BindingHeader, Track };
    EType Type;
    UMCComboBinding* Binding;  // 두 타입 모두 set
    UMCComboTrack*   Track;    // null = BindingHeader
};

void BuildPaintRows(TArray<FPaintRow>& Out) const
{
    // Asset->Bindings × Binding->Tracks 평탄화
    // Binding 마다 1 BindingHeader 행 + N Track 행
}

float ComputeRowHeight(const FPaintRow& Row) const
{
    if (Row.Type == BindingHeader) return BindingHeaderHeight;  // 28
    // Track: LaneHeight × LaneCount + (펼침 시) sub-row × LaneHeight
    return LaneHeight * Row.Track->GetLaneCount() + Track->ComputeExtraSubRowHeight();
}
```

매 row Y 누적:
```cpp
float AccumY = RulerHeight + VerticalScrollOffset;  // 22 + scroll
for (Row : PaintRows) {
    const float RowY = AccumY;
    AccumY += ComputeRowHeight(Row);
    // Row 안 Section paint
}
```

⭐ **함정**: Outliner 의 `STableRow` height 와 본 ComputeRowHeight 가 *정확히 일치* 의무. Cycle 5p+7 hotfix 가 `SBox::HeightOverride` 통합으로 봉합 — vault [[synthesis/mc-combo-editor-levelsequence-lite]] §5.13.5.

## 4. Section Box 9-Layer 정확 분해

각 Section box 의 paint 순서 + LayerId 오프셋:

| Layer | 내용 | 조건 | Default 시 표시? |
| -- | -- | -- | -- |
| **L0** (Base) | Track lane 영역 배경 zebra | 항상 | ✅ |
| **L1** | Section 본체 색상 box (`SectionColor` × `Weight` alpha) | 항상 | ✅ |
| **L1** (overlay) | Section 본체 위 hatched pattern (45° 대각선) | `Section == SelectedSection` | ⚠ Selected 시만 |
| **L1** (border) | 상단/하단 1.5px 어두운 border (`SectionColor × 0.4`) | 항상 | ✅ |
| **L2** | **EaseIn gradient** (Multi-stop curve) | **`Section->EaseInFrames > 0`** | ❌ **default 0 시 skip** |
| **L2** | **EaseOut gradient** (Multi-stop curve) | **`Section->EaseOutFrames > 0`** | ❌ **default 0 시 skip** |
| **L3** | Reverse 화살표 ◀ | `Section->bReverse` | ⚠ flag true 시만 |
| **L4** | Weight bar (하단 2px, width = Weight × WidthPx) | `Weight > 0` | ✅ 기본 1.0 |
| **L5** | TransformSection keyframe diamond | TransformSection 안 keys.Num() > 0 | ⚠ Transform 만 |
| **L6+** | Section 이름 label (text) | 항상 | ✅ |
| **L7+** | Hover tooltip outline | hover 시 | ⚠ hover 만 |

### 4.1 ⭐⭐⭐ L2 EaseIn/Out Gradient — Multi-stop Curve

```cpp
auto BuildBlendStops = [Section](float WidthInPx, bool bEaseIn) -> TArray<FSlateGradientStop>
{
    constexpr int32 SampleCount = 5;  // 0, 0.25, 0.5, 0.75, 1.0
    const float MaxAlpha = Clamp(Section->Weight, 0, 1);

    TArray<FSlateGradientStop> Stops;
    for (int32 i = 0; i < SampleCount; ++i) {
        const float Alpha = i / (SampleCount - 1);
        const float CurveAlpha = ApplyBlendCurve(Alpha, Section->BlendType);  // Linear/Cubic/Step
        const float StopWeight = bEaseIn ? CurveAlpha : (1 - CurveAlpha);

        FLinearColor StopCol = Section->SectionColor;
        StopCol.A = StopWeight * MaxAlpha;
        Stops.Add(FSlateGradientStop(Alpha * WidthInPx, StopCol));
    }
    return Stops;
};

if (Section->EaseInFrames > 0) {
    const float EaseInPx = WidthPx × clamp(EaseInFrames / Duration);
    if (EaseInPx > 1.0f) {
        Stops = BuildBlendStops(EaseInPx, /*bEaseIn=*/true);
        FSlateDrawElement::MakeGradient(..., Stops, Orient_Vertical, ...);
    }
}
```

**Engine 권위**:
- `FSlateDrawElement::MakeGradient` — `ElementBatcher.cpp` L1783-1788 (Orient_Vertical = left-to-right gradient, stop lines are vertical)
- BlendType 곡선:
  - Linear: alpha 그대로
  - Cubic: `3a² - 2a³` (smoothstep — Sequencer 표준 미러)
  - Step: `alpha < 0.5 ? 0 : 1` (hard cut)

### 4.2 Hatched Pattern (selected 시)

45° 대각선 line 반복 + box 안 manual clip:
```cpp
for (float DiagX = -BoxH; DiagX < WidthPx; DiagX += HatchSpacing) {
    // line: (DiagX, 0) → (DiagX + BoxH, BoxH)
    // clip to box [0..WidthPx]
    FSlateDrawElement::MakeLines(...);
}
```

Sequencer Animation Section 스트라이프 시각 미러 — vault [[synthesis/mc-combo-editor-levelsequence-lite]] §Cycle 5p+3 hatched pattern.

## 5. ⭐⭐⭐ 데이터 의존성 매트릭스 — 시각화 미표시 원인 TOP 5

| # | 증상 | 근본 원인 | 확인 방법 | 해결 |
| -- | -- | -- | -- | -- |
| 1 ⭐⭐⭐ | **EaseIn/Out gradient 안 보임** | `Section->EaseInFrames == 0 && EaseOutFrames == 0` (default) | 디테일 패널 안 Easing 카테고리 직접 확인 | (a) 디테일 패널 안 명시 입력 / (b) overlap 자동 detection 구현 / (c) EasingHandle UI 추가 |
| 2 ⭐⭐ | **dominant swap 무동작 (overlap 시 동일 Section 유지)** | EaseIn/Out=0 → EffectiveWeight = Section.Weight × 1 × 1 → 두 Section 동률 → first-match 항상 동일 | log/inspector — `GetEffectiveWeight` 값 dump | (1) 과 동일 — EaseIn/Out 데이터 의무 |
| 3 ⭐ | Section 본체 box 안 보임 | `Section->Weight == 0` 또는 `SectionColor.A == 0` | `Section->Weight` 값 확인 | Weight 1.0 default 복원 |
| 4 ⭐ | Hatched pattern 안 보임 | `Section != SelectedSection.Get()` (Cycle 5p+3 결정 — selected 만) | SelectedSection 검사 | Section 클릭 select |
| 5 | reverse 화살표 안 보임 | `Section->bReverse == false` | bReverse flag 확인 | bReverse=true 명시 |

⭐⭐⭐ **#1 + #2 가 절대 다수 (90%+)** — Sequencer 의 EasingHandle UI 가 자동 가시화하지만 자체 TrackArea 안 동일 UI 없으면 사용자가 데이터 0 인 상태에서 "왜 안 보이지?" 함정.

## 6. Cross-fade 자동화 옵션 매트릭스

| 옵션 | 구현 복잡도 | UX | 데이터 변경 |
| -- | -- | -- | -- |
| **A. 디테일 패널 manual** (현재) | 0 | 낮음 — 디자이너가 매 Section EaseIn/Out 직접 입력 의무 | EaseInFrames / EaseOutFrames |
| **B. Overlap 자동 detection (read-only)** | 보통 | 높음 — Section 겹치면 자동 cross-fade 시각 + EffectiveWeight | 데이터 불변 (계산만) |
| **C. EasingHandle UI** | 높음 | 매우 높음 — Sequencer 표준 미러 (Section 끝 삼각형 드래그) | EaseInFrames / EaseOutFrames |
| **D. B + C 조합 — auto + manual override** | 매우 높음 | 최고 | bAutoBlendOnOverlap flag + manual override |

### 6.1 권장 — Option B (다음 cycle)

Section overlap 자동 detection 의사 코드:
```cpp
int32 UMCComboSection::GetAutoEaseInFrames() const
{
    // 이 Section 의 시작점이 다른 Section 의 끝점 안에 있는지 검사
    int32 BestOverlap = 0;
    for (Other in Track->Sections) {
        if (Other == this || Other->RowIndex != this->RowIndex) continue;
        if (Other->GetEndFrame().Value > this->GetStartFrame().Value
            && Other->GetStartFrame().Value < this->GetStartFrame().Value)
        {
            const int32 Overlap = Other->GetEndFrame().Value - this->GetStartFrame().Value;
            BestOverlap = max(BestOverlap, Overlap);
        }
    }
    return BestOverlap;
}
```

`GetEffectiveWeight` / paint 안 `max(EaseInFrames, GetAutoEaseInFrames())` 사용 → 데이터 불변 + 자동 시각.

## 7. Engine 권위 인용

| 인용 | 위치 | 적용 |
| -- | -- | -- |
| `FMovieSceneEasingSettings` | `MovieSceneSection.h` L111-L178 | EaseInFrames / EaseOutFrames MVP baseline |
| `IMovieSceneEasingFunction` | `MovieSceneEasingFunction.h` | KMCProject MVP 회피 → 3종 enum |
| `FSlateDrawElement::MakeGradient` | `ElementBatcher.cpp` L1783-1788 | Orient_Vertical multi-stop gradient |
| `FSlateDrawElement::MakeBox` | `SlateDrawElement.h` | Section 본체 / border |
| `FSlateDrawElement::MakeLines` | `SlateDrawElement.h` | Hatched pattern |
| `STableViewBase::GetScrollOffset` | `STableViewBase.h` L170 | Outliner ↔ TrackArea Y 동기 |
| Sequencer EasingHandle brush | `StarshipStyle.cpp` L2318 (`Sequencer.Section.EasingHandle`) | 자체 widget 안 동일 brush 차용 가능 |

## 8. KMCProject 검증 사례 매트릭스

| 항목 | Phase | 상태 |
| -- | -- | -- |
| L1 본체 box + Weight alpha | Phase 4 | ✅ |
| L1 hatched pattern (selected 시) | Cycle 5p+3 | ✅ |
| L1 border 1.5px | Phase 4g-hotfix3 | ✅ |
| L2 EaseIn/Out 2-stop linear gradient | Phase 4 | ✅ |
| L2 5-stop multi-sample curve (BlendType) | Phase 5e | ✅ |
| L5 TransformSection keyframe diamond | Phase 5p+5..5p+8 | ✅ |
| **#1 데이터 의존 trap (EaseIn/Out=0 시 paint skip)** | **Phase 5e 발견 (2026-05-19)** | ⚠ **사용자 보고** — Option B/C 후속 의무 |
| Overlap 자동 detection (Option B) | Phase 5f 후보 | 🟡 후속 |
| EasingHandle UI (Option C) | Phase 5g 후보 | 🟡 후속 |

## 9. 함정 매트릭스 (신규 7)

| # | 함정 | 정답 |
| -- | -- | -- |
| TA01 ⭐⭐⭐ | **EaseIn/Out 데이터가 default 0 → paint 코드는 OK 인데 시각화 0** | (a) 디테일 패널 명시 / (b) 자동 detection / (c) EasingHandle UI |
| TA02 ⭐⭐ | **dominant swap 무동작 → 두 Section EffectiveWeight 동률 (EaseIn/Out=0)** | TA01 과 동일 — 데이터 의무 |
| TA03 ⭐ | `Section->Weight` 0 → 본체 box 안 보임 | ctor default 1.0 확인 |
| TA04 ⭐ | Hatched pattern 무동작 → SelectedSection 미선택 | Section 클릭 (Cycle 5p+3 의도) |
| TA05 ⭐ | `EaseInPx > 1.0f` 가드 — sub-pixel gradient skip (paint 비용 회피) | EaseInFrames 가 너무 작으면 (1 frame 등) 시각 무시 가능 — 디자이너 의도 명확화 |
| TA06 ⭐ | OverlapPriority sort 와 EffectiveWeight dominant swap 충돌 | sort 는 deterministic ordering 만, EffectiveWeight 가 *실제* 결정 — Phase 5e 통합 후 정상 |
| TA07 ⭐ | Section width < 2px clamp (`FMath::Max(2.0f, EndPx - StartPx)`) | 매우 작은 Section paint 가시성 보장 |

## 10. 후속 검증 후보

- [ ] Option B (overlap 자동 detection) 구현 + 데이터 불변 + 시각 자동 — Phase 5f 우선
- [ ] Option C (EasingHandle UI) — Section 끝 삼각형 드래그 — Phase 5g
- [ ] cull rect 적용 — `cullRect` 검사로 화면 밖 Section paint skip
- [ ] BlendType 별 sub-sample 수 동적 조정 (Cubic 7-stop, Linear 2-stop, Step 3-stop)
- [ ] Hatched pattern 의 모든 Section paint (selected 외) — 디자이너 의도 검증

## 11. Cross-link

- [[synthesis/timeline-custom-slate-widget-pattern]] §9-Layer OnPaint — 본 페이지의 상위 일반화
- [[synthesis/ue-slate-custom-onpaint-layer-strategy]] §Content/Overlay/Cursor 3계 — Ruler/Scrub 와의 layer 분리
- [[synthesis/ue-paint-hittest-shared-rowmap]] — Paint + Hit-test row descriptor 공유 의무
- [[synthesis/mc-combo-editor-levelsequence-lite]] §5.13.5 + §Phase 5e — KMCProject 검증 사례
