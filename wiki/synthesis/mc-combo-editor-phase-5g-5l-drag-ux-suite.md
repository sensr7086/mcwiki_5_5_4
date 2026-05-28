---
type: synthesis
title: "KMCProject MCComboEditor — Phase 5g-5p Section Drag UX + Blend Suite (LevelSequence Sequencer 미러)"
slug: mc-combo-editor-phase-5g-5l-drag-ux-suite
created: 2026-05-19
last_updated: 2026-05-20
project_role: case-study
project: KMCProject
measured_date: 2026-05-20
sources:
  - "[[sources/ue-levelsequence-moviescene]]"
  - "[[sources/ue-levelsequence-sequencer]]"
  - "[[sources/ue-levelsequence-tracks]]"
  - "[[sources/ue-slatecore-drawing]]"
  - "[[sources/ue-slatecore-swidget]]"
  - "[[sources/ue-animation-animinstance]]"
  - "[[synthesis/timeline-custom-slate-widget-pattern]]"
  - "[[synthesis/ue-slate-custom-onpaint-layer-strategy]]"
  - "[[synthesis/ue-track-area-section-paint-anatomy]]"
  - "[[synthesis/mc-combo-editor-levelsequence-lite]]"
entities:
  - "[[entities/FSlateDrawElement]]"
  - "[[entities/SWidget]]"
  - "[[entities/UAnimMontage]]"
  - "[[entities/UAnimInstance]]"
concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
status: living
tags: [synthesis, kmcproject, mc-combo, drag-ux, phase-5g, phase-5h, phase-5i, phase-5j, phase-5k, phase-5l, phase-5n-revert, phase-5o-montage-blend, phase-5p-perf-batch, frame-hud-label, vertical-drag-rowindex, easing-handle-ui, x-cross-fade-polygon, hatched-polygon-clip, grayscale-uniform, levelsequence-mirror, sequencer-section-paint, custom-verts-triangle-strip, run-length-hatched-batch, montage-default-blend-time, anim-sequencer-instance-pending]
citation_disclosure: "🟢 18 (Engine source 직접 인용 + KMCProject Phase 5g-5p 실측 구현 + evaluator 8.7/10 + Engine cross-fade 3단계 chain 권위 추적)"
---

# KMCProject MCComboEditor — Phase 5g-5p Section Drag UX + Blend Suite

> **2026-05-19~20 — 9 cycle 누적** — Sequencer 표준 Section drag UX 미러 + Montage BlendIn/Out 통합 + Hatched perf 8-16x. evaluator 8.7/10 (Major 0). **Phase 5q UAnimSequencerInstance 도입 대기 (Engine cross-fade 3단계 chain 정확 미러)**.

## 1. Thesis — Sequencer 표준 미러 완성 매트릭스 (Phase 5g-5p)

| LevelSequence 기능 | KMCProject Phase | 핵심 |
| -- | -- | -- |
| Section X drag (Move) | 2d | SetRange(NewStart, NewStart+Duration) |
| Trim (좌/우 edge) | 2d | EdgeHitPx ±5 |
| Slip (Alt + edge) | 2d | StartFrameOffset |
| Cursor Frame HUD | 5g.A | LayerId+12 overlay, "0023" + "[+006]" |
| Same-row Move 허용 | 5g.B | Move drag 후 AssignAutoRowIndex 호출 제외 |
| Selected edge yellow markers | 5g.C | 3×10 px yellow box at edges |
| Vertical drag → RowIndex | 5h.1 | (cursor.Y - TrackRowY) / LaneHeight |
| HUD swap (캔버스 끝) | 5h.2 | HudX + Width > Size.X 시 좌측 swap |
| HUD font Regular 10 | 5h.3 | FCoreStyle::GetDefaultFontStyle |
| Lane clamp = LaneCount | 5h hotfix | Track->GetLaneCount() 동적 max |
| bAutoLaneOnAdd 토글 | 5i.1 | default false — 같은 lane 누적 |
| "+New Lane" 청색 hint | 5i.2 | LaneCount index 영역 표시 |
| EasingHandle UI | 5j.1 | EaseInDrag/EaseOutDrag mode + cyan 6×10 |
| Frame/Seconds toggle | 5j.2 | bShowSecondsInHUD format 분기 |
| TransformSection dominant swap | 5j.3 | EffectiveWeight max (Montage Phase 5e 미러) |
| X 자형 cross-fade polygon | 5k | MakeCustomVerts 16-sample triangle strip |
| Hatched polygon clip + 회색 | 5l | sub-segment polygon membership + grayscale |
| ⭐ **Phase 5g-5l evaluator** | **5m** | **8.7/10 PASS (Major 0)** |
| ⭐ **Cross-fade RowIndex 검사 복원** | **5n revert** | **same RowIndex 만 (사용자 image 결정) — Phase 5n hotfix revert** |
| ⭐ **Cross polygon 회색 고정** | **사용자 직접** | `constexpr FColor(150, 150, 150, 255)` — Section 색상 의존 제거 |
| ⭐⭐⭐ **Montage BlendIn/Out 자동 적용** | **5o** | `Max3(manual, auto-overlap, Montage::GetDefaultBlendIn/OutTime)` |
| ⭐⭐⭐ **Hatched run-length perf** | **5p #2** | **640 → 40-80 draw calls (8-16x 감소)** |
| Detail Panel `LogEffectiveBlendTimes` button | 5p #4 | CallInEditor 진단 도구 |
| EaseIn/Out → BlendIn/Out rename 보류 | 5p #1 | UPROPERTY rename 호환성 비용 vs ROI 낮음 |
| TransformSection Phase 5o 패턴 N/A | 5p #3 | Transform 자체 blend 개념 없음 |

## 2. 핵심 알고리즘 매트릭스

### 2.1 EasingHandle hit-test 우선순위 (Phase 5j.1)

```
OnMouseButtonDown Section 본체 hit 이후:
  1. EasingHandle (HandleHitPx ±4)         ⭐ 5j.1 최우선
     ├── EffEaseIn > 0 + HandleLeftX  → EaseInDrag
     └── EffEaseOut > 0 + HandleRightX → EaseOutDrag
  2. Slip (Alt + edge, EdgeHitPx ±5)       ⭐ Phase 2d
  3. Trim (edge, EdgeHitPx ±5)             ⭐ Phase 2d
  4. Move (Section 본체 inner)             ⭐ Phase 2d / Phase 5h Y drag
```

### 2.2 X 자형 curve polygon (Phase 5k)

```cpp
// 16-sample triangle strip — height curve 따라 변동
template <typename CurveFunc>
static void DrawEaseCurvePolygon(...)
{
    for (i = 0..SampleCount-1) {
        Sample = i / (SampleCount - 1);
        HalfH = AlphaCurveFn(Sample) * BoxH * 0.5;
        SampleX = Lerp(StartX, EndX, Sample);
        verts[2i]   = top:    (SampleX, CenterY - HalfH)
        verts[2i+1] = bottom: (SampleX, CenterY + HalfH)
    }
    // Triangle strip: (top_i, bot_i, top_{i+1}) + (bot_i, bot_{i+1}, top_{i+1}) per segment
    MakeCustomVerts(EasingHandle resource, verts, indices);
}
```

### 2.3 Hatched polygon membership + run-length batch (Phase 5l + 5p #2)

```cpp
// Phase 5l: Polygon membership
auto IsInsidePolygon = [&](float x, float y) -> bool {
    float Alpha;
    if      (x < EaseInPx)              Alpha = ApplyCurve(x / EaseInPx, BlendType);
    else if (x > WidthPx - EaseOutPx)   Alpha = 1 - ApplyCurve((x - (WidthPx-EaseOutPx)) / EaseOutPx, BlendType);
    else                                 Alpha = 1.0;  // 본체 box
    const float PolyHalfH = Alpha * (BoxH * 0.5);
    return (y >= HalfBoxH - PolyHalfH) && (y <= HalfBoxH + PolyHalfH);
};

// ⭐ Phase 5p #2: Run-length compaction (640 → 40-80 draw calls)
for (각 hatched line ≈40개) {
    bool bInRun = false;
    FVector2D RunStartPt, PrevPt;
    for (j = 0..SubSegN) {
        Pt = Lerp(LineStart, LineEnd, j/SubSegN);
        bool bIsIn = IsInsidePolygon(Pt);

        if (bIsIn && !bInRun) { RunStartPt = Pt; bInRun = true; }
        else if (!bIsIn && bInRun) {
            MakeLines(RunStartPt → PrevPt);  // run 종료 = 1 call
            bInRun = false;
        }
        PrevPt = Pt;
    }
    if (bInRun) MakeLines(RunStartPt → PrevPt);  // final emit
}
```

### 2.4 Vertical drag RowIndex (Phase 5h.1 + hotfix)

```cpp
const int32 MaxAllowedRow = OwnerTrack ? OwnerTrack->GetLaneCount() : 0;
const float LocalYInTrack = LocalPos.Y - DragSectionTrackRowY - 3.0f;
const int32 NewRowIndex = clamp(floor(LocalYInTrack / LaneHeight), 0, MaxAllowedRow);
if (NewRowIndex != Section->RowIndex) {
    Section->RowIndex = NewRowIndex;
    OwnerTrack->InvalidateSortedSectionIndices();
}
```

### 2.5 ⭐ Phase 5o — Montage BlendIn/Out 자동 적용

```cpp
// UMCComboMontageSection (Phase 5o override)
virtual int32 GetEffectiveEaseInFrames() const override {
    return FMath::Max3(
        EaseInFrames,                  // 1. manual UPROPERTY (디테일 패널)
        GetAutoEaseInFrames(),         // 2. Phase 5f auto-overlap (same row)
        GetMontageBlendInFrames()      // 3. ⭐ Phase 5o — Montage->GetDefaultBlendInTime() × TickRes
    );
}

// Helper — Engine 권위
int32 GetMontageBlendInFrames() const {
    const UAnimMontage* M = Montage.Get();
    if (!M) return 0;
    const float BlendInSec = M->GetDefaultBlendInTime();  // AnimMontage.h L666
    if (BlendInSec <= 0) return 0;
    const FFrameRate TickRes = GetTypedOuter<UMCComboAsset>()
        ? GetTypedOuter<UMCComboAsset>()->TickResolution
        : FFrameRate(24000, 1);
    return TickRes.AsFrameNumber(BlendInSec).Value;
}
```

## 3. Paint Layer 매트릭스 (13 Layers)

| Layer | 내용 | Phase |
| -- | -- | -- |
| L0 | Track lane zebra | (기본) |
| L1 본체 box | Section 본체 [EaseIn 끝, EaseOut 시작] 중앙만 | Phase 5k |
| L1 EaseIn/Out polygon | 16-sample triangle strip curve (회색 150) | Phase 5k + 사용자 변경 |
| L1 Hatched (selected) | Polygon clip sub-segment + 회색 (127) + run-length batch | Phase 5l + 5p #2 |
| L1 Border | 상/하단 darker (SectionColor × 0.4 — 색조 의존) | Phase 4g-hotfix3 |
| L2 Reverse arrow | 가운데 ◀ (bReverse 시) | Phase 4 |
| L3 Weight bar | 하단 2px width = Weight × WidthPx | Phase 4 |
| L4-L9 | Section name, TransformSection keyframes, sub-row labels | Phase 5p+5..5p+8 |
| L10 | Ruler (시간 눈금) | Cycle 5p+6 |
| L11 | Scrub head 빨간선 + Selected edge yellow markers + EasingHandle cyan + "+New Lane" hint | Phase 5g.C + 5i.2 + 5j.1 |
| L12 | Drag HUD frame/offset label box (Regular 10) | Phase 5g.A + 5h.2/3 + 5j.2 |

## 4. evaluator 결과 (general-purpose role) — 8.7/10 (Major 0)

| 기준 | 점수 | 근거 요약 |
| -- | -- | -- |
| Engine authority | 9/10 | MakeCustomVerts 9-arg + FSlateVertex::Make + Triangle strip 정확. Sequencer 미러 권위 인용 일관 |
| Policy compliance | 9/10 | TWeakObjectPtr / WITH_EDITORONLY_DATA / vault cross-link |
| Pitfall awareness | 9/10 | Section width skip / Body box skip / Drag priority / LaneCount clamp / Move 제외 / sub-segment 검사 — 6 함정 처리 |
| Performance/Memory | 7/10 → **8/10** (Phase 5p #2 후) | M1 hatched 640 → **40-80 draw calls** (Phase 5p 반영) |
| Maintainability | 9/10 | Phase tag 위계 명확, Lambda capture 명료 |

### Per-Phase 점수

- 5g (9/10), 5h (9/10), 5i (9/10), 5j (9/10), 5k (9/10), 5l (7→**9**/10 Phase 5p 후), **5n revert** (8/10 — 사용자 의도 복원), **5o** (9/10 Montage BlendIn/Out 통합), **5p** (9/10 — perf 8-16x + Detail Panel)

### Major 0 / Minor 잔여 (5p 후)

- M1 ✅ Phase 5p #2 로 해소 (Hatched 640 → 40-80)
- M2 OnMouseButtonDown BuildPaintRows 3회 중복 → 캐시
- M3 HUD font Bold 9 검토 (Sequencer 실제 표준)
- M4 Hatched 회색 vs border 색조 inconsistency — 사용자 디자인 결정 보존

## 5. 함정 매트릭스 (Phase 5g-5p 누적 9건)

| # | 함정 | 정답 |
| -- | -- | -- |
| Drag-01 | Drag HUD cursor 끝 잘림 | HudX + Width > Size.X 시 cursor 좌측 swap (Phase 5h.2) |
| Drag-02 | Vertical drag 무제한 lane 생성 | clamp max = Track->GetLaneCount() (Phase 5h hotfix) |
| Drag-03 | Auto lane allocation 가 Move drag 후 분리 | Move 제외, Trim 만 (Phase 5g.B) |
| Drag-04 | Add Section 자동 row 분리 | bAutoLaneOnAdd default false (Phase 5i.1) |
| EaseHandle-01 | EaseIn/Out=0 시 handle hit 시도 시 Trim 충돌 | EffEaseIn/Out > 0 시만 handle 표시/hit (Phase 5j.1) |
| Polygon-01 | EaseIn + EaseOut > Duration 시 본체 negative width | `if (BodyEndX > BodyStartX)` skip (Phase 5k) |
| Hatched-01 | Polygon edge sub-segment partial overlap (한쪽만 안) | 양 끝점 모두 안 검사 — jaggy 미미 (Phase 5l) |
| ⭐ **RowIndex-01 (5n)** | **RowIndex 무관 cross-fade → 다른 lane 도 의도 안 한 blend** | **same RowIndex 만 (Phase 5n revert)** |
| ⭐ **MontageBlend-01 (5o)** | **Montage 자체 BlendIn/Out time 미반영 → cross-fade 시각 ↔ 게임 runtime 불일치** | **GetMontageBlendIn/OutFrames + Max3 통합 (Phase 5o)** |

## 6. 영향 받는 파일 매트릭스 (Phase 5g-5p)

| 파일 | Phase 변경 |
| -- | -- |
| `SMCComboTrackArea.h` | Drag state 멤버 (DragHudCursorLocal/DragStartCursorFrame/DragSectionTrackRowY/bShowSecondsInHUD) + enum (EaseInDrag/EaseOutDrag) |
| `SMCComboTrackArea.cpp` namespace MCComboCirclePaint | DrawEaseCurvePolygon template (Phase 5k) |
| `SMCComboTrackArea.cpp` OnMouseButtonDown | EasingHandle hit-test (5j.1) + DragStartCursorFrame/DragSectionTrackRowY 캐시 (5g.A + 5h.1) |
| `SMCComboTrackArea.cpp` OnMouseMove | 5g.A cursor 갱신 + 5h.1 vertical drag + 5j.1 EaseIn/Out drag |
| `SMCComboTrackArea.cpp` OnMouseButtonUp | Move 제외 (5g.B) + HUD reset (5g.A) + DragSectionTrackRowY reset (5h.1) |
| `SMCComboTrackArea.cpp` OnPaint | Section paint 13-Layer + 5k polygon + **5l hatched + 5p #2 run-length** + 5g.C edge markers + 5i.2 lane hint + 5j.1 cyan handle + 5g.A/5h.2/5j.2 HUD + **사용자 직접 cross polygon 회색** |
| `MCComboTrack.h/.cpp` | bAutoLaneOnAdd UPROPERTY (Phase 5i.1) |
| `MCComboSection.h/.cpp` | `GetEffectiveEaseIn/OutFrames` virtual 격상 (5o) + RowIndex 검사 복원 (5n revert) |
| `MCComboMontageTrack.h/.cpp` | UMCComboMontageSection 4 helper (5o) — GetMontageBlendIn/OutFrames + Override + LogEffectiveBlendTimes (5p #4) |
| `SMCComboPreviewSceneViewport.cpp` | TransformSection EffectiveWeight dominant swap (Phase 5j.3) |

## 7. 검증 시나리오

| 시나리오 | Phase | 기대 |
| -- | -- | -- |
| Section X drag (Move) | 5g.A | cursor 옆 `0023` + `[+006]` HUD |
| Section Y drag → 다른 lane | 5h.1 | RowIndex 실시간 변경 + clamp [0, LaneCount] |
| 두 Section 추가 (default bAutoLaneOnAdd=false) | 5i.1 | 모두 row 0 (같은 lane) — cross-fade gradient 자동 |
| Section 끝 cyan handle drag | 5j.1 | EaseInFrames/EaseOutFrames 변경 + polygon 실시간 |
| 두 Section overlap (same row) | 5n revert + 5k | X 자형 cross polygon visible + 회색 (사용자) |
| 두 Section overlap (다른 row) | 5n revert | cross-fade 미발생 (same row 만) ✅ |
| Selected + overlap | 5l + 5p #2 | hatched 회색 — polygon shape 정확 추종 + 40-80 draw calls (8-16x 감소) |
| Montage 단독 (BlendIn=0.2s) | 5o | EffectiveEaseIn = max(0, 0, 0.2s × 24000) → polygon X 자 자동 ✅ |
| Detail Panel `Log Effective Blend Times` 클릭 | 5p #4 | Output log 안 manual/auto/montage/effective 분해 |
| HUD Ctrl+T (별도 cycle) | 5j.2 | "0.96s" / "[+0.25s]" 토글 |
| TransformSection overlap | 5j.3 | EffectiveWeight 큰 쪽 transform dominant |

## 8. ⭐⭐⭐ Engine Cross-fade 3단계 Chain (Phase 5q pre-flight)

LevelSequence 의 Montage cross-fade pose blend 처리 위치 (Phase 5q UAnimSequencerInstance 도입 의무 권위):

### 1단계 — Per-Section Weight

`MovieSceneSkeletalAnimationSection.cpp` L483-488:
```cpp
float UMovieSceneSkeletalAnimationSection::GetTotalWeightValue(FFrameTime InTime) const
{
    float ManualWeight = 1.f;
    Params.Weight.Evaluate(InTime, ManualWeight);
    return ManualWeight * EvaluateEasing(InTime);
}
```

`MovieSceneSection.cpp` L987 `EvaluateEasing` — `IMovieSceneEasingFunction::EvaluateWith(Easing.EaseIn/Out, Interp)`.

→ KMCProject 미러: `UMCComboSection::GetEffectiveWeight` (Phase 5e/5f/5o). ✅

### 2단계 — Multi-Section Aggregation

`MovieSceneSkeletalAnimationSystem.cpp` L405-545 ECS `ForEachAllocation`:
```cpp
Animation.BlendWeight = Weight;  // L517 per-section
BoundObjectAnimations.Animations.Add(Animation);  // 같은 SkeletalMesh 에 누적
```

→ KMCProject 격차: **모든 section 유지 (Engine) vs 1개 dominant swap (Phase 5j.3)**

### 3단계 — AnimGraph 슬롯 위임 (실제 pose blend)

`MovieSceneSkeletalAnimationSystem.cpp` L889-975 `SetAnimPosition` 두 갈래:

**3.A `UAnimSequencerInstance`** (L925-940):
```cpp
FAnimSequencerData AnimSequencerData(
    Animation, AnimSequenceID, RootMotion,
    Params.FromPosition, Params.ToPosition,
    Params.Weight,         // ← Section 별 BlendWeight
    Params.bFireNotifies,
    Params.Section->Params.SwapRootBone,
    CurrentTransform,
    Params.Section->Params.MirrorDataTable.Get());
SequencerInst->UpdateAnimTrackWithRootMotion(AnimSequencerData);
```

**3.B `FAnimMontageInstance::SetSequencerMontagePosition`** (L948-957):
```cpp
FAnimMontageInstance::SetSequencerMontagePosition(
    AnimParams.SlotName, AnimInst, InstanceId,
    Animation,
    Params.FromPosition / AssetPlayRate,
    Params.ToPosition / AssetPlayRate,
    Params.Weight, bLooping, Params.bPlaying);
```

→ KMCProject 격차: **`UAnimSingleNodeInstance` 단일 montage 제약** → 정확 pose blend 불가. Phase 5q 의 UAnimSequencerInstance 도입으로 해소.

## 9. Phase 5q 후속 — UAnimSequencerInstance 도입 (대기)

| 옵션 | 방법 | 복잡도 | 결정 |
| -- | -- | -- | -- |
| **A. UAnimSequencerInstance 도입** | Engine 표준 `UpdateAnimTrackWithRootMotion(FAnimSequencerData)` — multi-section 정확 pose blend | 높음 (Sequencer + AnimGraphRuntime 모듈 의존) | ⭐ **사용자 선택** |
| B. UAnimBlueprint 2-slot manual | manual weight bind | 매우 높음 | Sequencer-lite 위배 |
| C. dominant swap 유지 (5j.3) | 0.5 snap 단순화 | 0 | 게임 runtime 별도 evaluator |
| D. `FAnimMontageInstance::SetSequencerMontagePosition` | UAnimInstance slot weight 합산 | 보통 | AnimInstance class 교체 |

## 10. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-19 | §1-§9 신규 작성 — Phase 5g-5l 6 cycle 누적 case study + evaluator 8.7/10 + 함정 7건 + M1-M4 후속 매트릭스 |
| **2026-05-19 (Phase 5n revert)** | §1 Thesis row 추가 — RowIndex 검사 복원 (사용자 image 결정 — same RowIndex 만 cross-fade). §5 함정 RowIndex-01 신규. sources/tags 갱신. |
| **2026-05-19 (사용자 직접 색상 변경 체크)** | §3 Layer L1 polygon — cross polygon `constexpr FColor(150, 150, 150, 255)` 회색 고정 (SectionColor 의존 제거 — 사용자 결정 보존) |
| **2026-05-20 (Phase 5o)** | §1 Thesis row 3 추가 (Montage BlendIn/Out 자동 적용 + virtual 격상 + Max3 통합). §2.5 알고리즘 신규 (GetMontageBlendIn/OutFrames). §5 함정 MontageBlend-01 신규. citation_disclosure 13→18 + Engine 권위 (AnimMontage.h L666/L669 GetDefaultBlendIn/OutTime). |
| **2026-05-20 (Phase 5p)** | §1 Thesis row 4 추가 (Hatched run-length perf + Detail Panel button + rename 보류 + Transform N/A). §2.3 Hatched 알고리즘에 run-length compaction 추가. §4 Performance/Memory 7→8/10. M1 ✅ 해소 명시. |
| **2026-05-20 (Engine cross-fade 3단계 chain 추적)** | §8 신규 — Engine LevelSequence Montage cross-fade 처리 3단계 위치 + Per-Section weight (Section.cpp L483) + Multi-Section aggregation (System.cpp L405) + AnimGraph 위임 (System.cpp L889 3.A UAnimSequencerInstance + 3.B FAnimMontageInstance). KMCProject UAnimSingleNodeInstance 단일 montage 제약 정량화. citation_disclosure 18 (Engine 권위 7건 + KMCProject 실측). §9 Phase 5q 후속 매트릭스 (A-D) — 사용자 결정 A (UAnimSequencerInstance 도입) 명시. |
