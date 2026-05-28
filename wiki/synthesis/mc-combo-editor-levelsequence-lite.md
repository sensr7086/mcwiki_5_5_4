---
type: synthesis
title: "KMCProject MCComboEditor — LevelSequence 데이터 모델 lite + AnimNotify Track 스타일 자체 Slate 패널 (Cycle 5d 신규 합성)"
slug: mc-combo-editor-levelsequence-lite
created: 2026-05-15
last_updated: 2026-05-19
project_role: case-study
project: KMCProject
measured_date: 2026-05-19
sources:
  - "[[sources/ue-levelsequence-moviescene]]"
  - "[[sources/ue-levelsequence-tracks]]"
  - "[[sources/ue-levelsequence-sequencer]]"
  - "[[sources/ue-editor-unrealed-asseteditortoolkit]]"
  - "[[sources/ue-editor-unrealed-factories]]"
  - "[[sources/ue-editor-assettools]]"
  - "[[sources/ue-editor-asseteditorapi]]"
  - "[[sources/ue-editor-personatoolkit]]"
  - "[[sources/ue-editor-propertyeditor]]"
  - "[[sources/ue-editor-advancedpreviewscene]]"
  - "[[sources/ue-slatecore-drawing]]"
  - "[[sources/ue-slatecore-swidget]]"
  - "[[sources/ue-slatecore-clipping]]"
  - "[[sources/ue-slate-application]]"
  - "[[sources/ue-slate-liststrees]]"
  - "[[sources/ue-slate-layoutwidgets]]"
  - "[[sources/ue-slate-menu]]"
  - "[[sources/ue-slate-commonwidgets]]"
  - "[[sources/ue-slate-textinput]]"
  - "[[sources/ue-streeview-onexpansionchanged-pattern]]"
  - "[[sources/ue-floatchannel-9-mirror]]"
  - "[[sources/ue-fscopedtransaction-drag-1-entry]]"
  - "[[sources/ue-coreuobject-uobject]]"
  - "[[sources/ue-coreuobject-serialization]]"
  - "[[sources/ue-coreuobject-deprecateduproperty]]"
  - "[[sources/ue-animation-animinstance]]"
  - "[[sources/ue-agent-levelsequence]]"
  - "[[synthesis/mc-combo-section-levelsequence-style-upgrade]]"
  - "[[synthesis/timeline-custom-slate-widget-pattern]]"
  - "[[synthesis/ue-tree-uobject-expansion-bidirectional-sync]]"
  - "[[synthesis/ue-paint-hittest-shared-rowmap]]"
  - "[[synthesis/ue-slate-custom-onpaint-layer-strategy]]"
  - "[[synthesis/ue-editor-preview-mesh-scrub-tick-pattern]]"
entities:
  - "[[entities/IToolkit]]"
  - "[[entities/FTabManager]]"
  - "[[entities/FSlateDrawElement]]"
  - "[[entities/IAssetTools]]"
  - "[[entities/SWidget]]"
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/UAnimMontage]]"
concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Slate-Paint-Cycle]]"
  - "[[concepts/Slate-Editor-Runtime-Separation]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
status: living
tags: [synthesis, kmcproject, mc-combo, levelsequence-lite, moviescene-data-model, anim-notify-track, slate-custom-panel, workflow-centric-application, factory-pattern, ue-5-7, case-study, measured, phase-2-complete, phase-3-complete, sequencer-style-layout, sort-cache, fts-ticker-playback, f4-reverted, phase-4-binding-hierarchy, postload-rename-outer, container-migration, phase-4d-skeletalmesh-picker, phase-4e-thumbnail, lane-allocation-row-index, cursor-anchored-zoom, hatched-selected-only, sequencer-style-section-paint, timeline-dynamic-grow, montage-auto-metadata, adaptive-ruler-density, solo-bidirectional, loop-toggle, row-add-caret, section-duration-ui, section-tooltip-tattribute, c3668-tooltip-trap, trap-30-callineditor-cleanup, phase-5p5-transform-section, phase-5p6-cubic-hermite-prev-next-drag-delete, phase-5p7-9-channel-refactor-single-section-enforce, phase-5p8-outliner-tree-trackarea-subrow-paint-sspinbox-per-channel-diamond, c3668-base-non-virtual-trap, streeview-onexpansionchanged-bidirectional-sync, uobject-expansion-state-uproperty-bitfield, floatchannel-9-mirror, fmath-cubicinterp-catmull-rom, cycle-5p5-clipping-scrollbar, ewidgetclipping-cliptobounds, sscrollbar-horizontal-viewport-binding, cycle-5p6-ruler-layer-circle-paint-button-reorder, makecustomverts-circle-paint, easinghandle-brush, layer-12-strategy, cycle-5p7-montage-mismatch-doubleclick-heightoverride, computetrackextrasubrowcount-generalized, sexpanderarrow-removed-doubleclick-toggle, outliner-row-heightoverride-unified, phase-5a-preview-tick-3axis, phase-5a-set-update-anim-in-editor-fallback, phase-5a-sync-preview-to-scrub-chain, phase-5b-multi-section-sequential-playback, phase-5b-cached-sections-array, phase-5b-section-transition-guard, debugskel-set-position-silent-fail, world-tick-leveltick-all, animinstance-tick-animation-explicit, set-animation-asset-proxy-reset-trap]
citation_disclosure: "🟢 110+ (vault 직접 인용 + KMCProject 2026-05-15~19 빌드 PIE 통과 실측 + Phase 5p+5..5p+8 + Cycle 5p+5/+6/+7 + Phase 5a hotfix + Phase 5b 통합 / Engine 권위 110+건 verify) / 🟡 4 / 🔴 2"
---

# KMCProject MCComboEditor — LevelSequence 데이터 모델 lite + Sequencer-style 레이아웃 + Phase 5p+5..5p+8 + Cycle 5p+5/+6/+7 + Phase 5a/5b

> **Phase 5a hotfix + Phase 5b — Preview runtime playback (multi-section)** — Timeline scrub frame ↔ PreviewMesh AnimMontage 자동 동기. Tick override 3축 명시 + multi-section sequential playback (자동 Section 전환). evaluator 8.4/10 Major 0 / Minor 5 / Tip 4.

> **Phase 진행 상태** (요약):
> - Phase 1-4 마무리 + Phase 5p+5..5p+8: 2026-05-15 ~ 2026-05-18
> - Cycle 5p+5 (Clipping + horizontal SScrollBar + vault 일반화 5종): 2026-05-19
> - Cycle 5p+6 (Ruler L10 + Circle paint + Add reorder + Pin 제거 + DrawFilledCircle helper + layer strategy vault): 2026-05-19
> - Cycle 5p+7 (Montage mismatch + SExpanderArrow 제거 + 더블클릭 + Add Prev/Next 중앙 + HeightOverride 통합): 2026-05-19
> - **Phase 5a hotfix (PreviewMesh Scrub Tick 3축 — Editor world silent fail 해소): 2026-05-19**
> - **Phase 5b (Multi-section sequential playback — Timeline playback time → 자동 Section 전환): 2026-05-19**

## 1. Thesis

| LevelSequence 요소 | KMCProject 결정 | 이유 |
| -- | -- | -- |
| (기존 32+ 행 보존 — Phase 1-4 + Phase 5p+5..5p+8 + Cycle 5p+5/+6/+7) | (기존) | (기존) |
| ⭐⭐⭐ **Phase 5a — Scrub-driven Preview Tick 3축 명시** | ✅ **채용** | `SetPosition(Time, false)` 단독은 Editor world (특히 `EWorldType::EditorPreview`) 에서 silent fail — pose 미갱신. `SCompoundWidget::Tick` override 안 (1) `SEditorViewport::Tick` super + (2) `PreviewScene->GetWorld()->Tick(LEVELTICK_All, DeltaTime)` + (3) `PreviewMeshComponent->TickAnimation(DeltaTime, false)` 3축 명시. Engine 권위 — `SkeletalMeshComponent.cpp` L1689 ShouldUpdateTransform + L1732 ShouldTickPose. → 일반화 페이지 [[synthesis/ue-editor-preview-mesh-scrub-tick-pattern]] 신규. |
| ⭐ **Phase 5a — `SetUpdateAnimationInEditor(true)` fallback** | ✅ **채용 (보조)** | `EWorldType::Editor` 분기만 검사 — `EditorPreview` 미진입 시 무효. Tick override 가 primary, 본 flag 는 defense-in-depth (양쪽 적용). |
| ⭐ **Phase 5a — `SyncPreviewToScrub` chain (Timeline → App → Viewport)** | ✅ **채용** | `SMCComboTrackArea` 6 scrub change site → `HostingApp->SyncPreviewToScrub(GlobalFrame)` → `PreviewSceneViewport->SyncToScrubFrame(Frame, TickResolution)`. PreviewSceneViewport `Construct` 안 `Pinned->SetPreviewSceneViewport(SharedThis(this))` 자가 등록. weak-ptr pinning 양 끝. |
| ⭐⭐⭐ **Phase 5b — Multi-section sequential playback (`CachedSections` 배열)** | ✅ **채용** | 이전 단일 Section cache (Phase 5a) → 모든 MontageSection 배열 cache. `LoadAssetPreview` 안 Asset → Bindings × Tracks × Sections 순회 후 `LoadSynchronous` + `CachedSections.Add`. Sequencer-lite scope (Section 개수 < ~20) 가정. `struct FCachedSection { TWeakObjectPtr<UMCComboMontageSection> Section; TWeakObjectPtr<UAnimMontage> Montage; }`. |
| ⭐⭐⭐ **Phase 5b — Section transition guard (`MatchedSection != CurrentActiveSection.Get()`)** | ✅ **채용** | `SyncToScrubFrame` 매 frame 호출. 매칭 Section 변화 시에만 `SetAnimation` + `SetPlayRate` + `Stop` 재호출 — `UAnimSingleNodeInstance::SetAnimationAsset` 의 *Proxy 시간 0 reset* 부작용 회피. Engine 권위 — `AnimSingleNodeInstance.h` L74 InitializeAnimation 트리거. |

## 2-4 (모듈 구조 / 데이터 모델 / 에디터 표준 — 기존 본문 유지)

## 5. 자체 Slate 트랙 패널

(§5.1-§5.13 — 기존 본문 유지 — Cycle 5p+7 포함)

## 5.14 ⭐⭐⭐ Phase 5a hotfix — PreviewMesh Scrub-driven Tick 3축 명시 (2026-05-19 신규)

### 5.14.1 증상

빌드 성공 + 에러 0 + 로그 0 — 그러나 Timeline scrub drag → `SyncToScrubFrame` → `PreviewMeshComponent->SetPosition(LocalSeconds, false)` 정상 호출되지만 **PreviewMesh 정지 (silent fail)**.

### 5.14.2 1차 진단 (vault 참조 결과) — `SetUpdateAnimationInEditor(true)`

Engine source 검증:
- `Source/Runtime/Engine/Private/Components/SkeletalMeshComponent.cpp` L1689 `ShouldUpdateTransform`:
  ```cpp
  if (GetWorld()->WorldType == EWorldType::Editor) {
      if (bUpdateAnimationInEditor) return true;
      return bLODHasChanged;  // ← false 시 SKIP
  }
  ```
- L1732 `ShouldTickPose` 동일 패턴

→ 권고: `#if WITH_EDITOR PreviewMeshComponent->SetUpdateAnimationInEditor(true); #endif`

### 5.14.3 2차 진단 (사용자 검증) — Tick override 3축 명시 필수

`SetUpdateAnimationInEditor(true)` 만으로 부족.
**`FAdvancedPreviewScene` 의 WorldType = `EWorldType::EditorPreview`** (Editor 아님) → 위 분기 미진입 → 무효 가능.

**진짜 해결**: `SCompoundWidget::Tick` override 안 3축 명시 호출.

### 5.14.4 표준 패턴

```cpp
// .h
virtual void Tick(const FGeometry&, const double InCurrentTime, const float InDeltaTime) override;

// .cpp
void SMCComboPreviewSceneViewport::Tick(const FGeometry& AllottedGeometry,
                                         const double InCurrentTime,
                                         const float InDeltaTime)
{
    SEditorViewport::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);        // 1축 Slate base
    PreviewScene->GetWorld()->Tick(LEVELTICK_All, InDeltaTime);                  // 2축 Preview World 전체
    if (PreviewMeshComponent)
    {
        PreviewMeshComponent->TickAnimation(InDeltaTime, /*bNeedsValidRootMotion=*/false);  // 3축 AnimInstance 명시
    }
}
```

### 5.14.5 각 축 역할

| 축 | API | 효과 |
| -- | -- | -- |
| 1 | `SEditorViewport::Tick` (= `SCompoundWidget::Tick`) | Slate framework 매 frame 자동 호출 — override 진입점 |
| 2 | `UWorld::Tick(LEVELTICK_All, DeltaTime)` | Preview World 의 모든 actor/component tick (light/sky/floor 시각 일관성) |
| 3 | `USkeletalMeshComponent::TickAnimation(DeltaTime, false)` | AnimInstance 명시 tick → `Proxy.CurrentTime` 기반 pose evaluate → mesh 시각 갱신 |

### 5.14.6 `SyncPreviewToScrub` chain (Timeline → App → Viewport)

```
SMCComboTrackArea 6 scrub change site:
  - SetCurrentScrubFrame (transport tick / Prev/Next / programmatic)
  - OnMouseButtonDown Ruler click
  - OnMouseButtonDown sub-row channel diamond
  - OnMouseButtonDown lane-area diamond
  - OnMouseMove Scrub drag
  - OnMouseMove TransformKey drag + Move/Trim/Slip drag
        ↓
HostingApp->SyncPreviewToScrub(CurrentScrubFrame)
        ↓
FMCComboAssetEditorApplication::SyncPreviewToScrub:
  PreviewSceneViewport.Pin()->SyncToScrubFrame(InGlobalFrame, CurrentAsset->TickResolution)
        ↓
SMCComboPreviewSceneViewport::SyncToScrubFrame:
  Local time 계산 → PreviewMeshComponent->SetPosition(ClampedSeconds, false)
```

PreviewSceneViewport `Construct` 안 자가 등록:
```cpp
if (TSharedPtr<FMCComboAssetEditorApplication> Pinned = HostingApp.Pin())
{
    Pinned->SetPreviewSceneViewport(SharedThis(this));
}
```

### 5.14.7 vault 일반화 페이지 신규

→ [[synthesis/ue-editor-preview-mesh-scrub-tick-pattern]] — 일반화 패턴 (UE 일반 영역, `mc-` 접두사 아님). KMCProject 외 모든 UE 프로젝트 재사용 가능.
→ [[sources/ue-editor-personatoolkit]] §2.4.1 — Trap-PS01/PS02 추가 (PreviewMesh silent fail + SetUpdateAnimationInEditor 단독 의존).

## 5.15 ⭐⭐⭐ Phase 5b — Multi-section sequential playback (2026-05-19 신규)

### 5.15.1 목적

Timeline playback time 이 진행됨에 따라 *어떤 Section 안에 들어가는지* 자동 탐색 → 그 Section 의 Montage 로 PreviewMesh 전환 → LocalSeconds 변환 후 SetPosition. Combo 시퀀스 전체를 PreviewMesh 가 자동 재현.

### 5.15.2 데이터 구조 변경

**이전 (Phase 5a)** — 단일 Section cache:
```cpp
TWeakObjectPtr<UMCComboMontageSection> CachedMontageSection;
TWeakObjectPtr<UAnimMontage> CachedMontage;
```

**신규 (Phase 5b)** — 전체 Section 배열 cache + 활성 Section tracker:
```cpp
struct FCachedSection
{
    TWeakObjectPtr<UMCComboMontageSection> Section;
    TWeakObjectPtr<UAnimMontage> Montage;
};
TArray<FCachedSection> CachedSections;
TWeakObjectPtr<UMCComboMontageSection> CurrentActiveSection;  // 전환 검사용
```

### 5.15.3 `LoadAssetPreview` 재작성

```cpp
CachedSections.Reset();
UMCComboMontageSection* FirstMontageSection = nullptr;  // PreviewMesh 결정용 (첫 Section Skeleton)
for (const TObjectPtr<UMCComboBinding>& BindingPtr : Asset->Bindings)
{
    UMCComboBinding* Binding = BindingPtr.Get();
    if (!Binding) continue;
    for (UMCComboTrack* Track : Binding->Tracks)
    {
        UMCComboMontageTrack* MontageTrack = Cast<UMCComboMontageTrack>(Track);
        if (!MontageTrack) continue;
        for (UMCComboSection* Section : MontageTrack->Sections)
        {
            UMCComboMontageSection* MontageSection = Cast<UMCComboMontageSection>(Section);
            if (!MontageSection || MontageSection->Montage.IsNull()) continue;

            // Editor 측 동기 LoadSynchronous — Cooked 빌드 영향 X
            UAnimMontage* LoadedMontage = MontageSection->Montage.LoadSynchronous();
            if (!LoadedMontage) continue;

            FCachedSection Entry;
            Entry.Section = MontageSection;
            Entry.Montage = LoadedMontage;
            CachedSections.Add(Entry);

            if (!FirstMontageSection) FirstMontageSection = MontageSection;
        }
    }
}
// ... 초기 PreviewMesh = FirstMontageSection 의 Skeleton 의 PreviewMesh ...
CurrentActiveSection = FirstMontageSection;
```

### 5.15.4 `SyncToScrubFrame` 3단계 재작성

```cpp
void SMCComboPreviewSceneViewport::SyncToScrubFrame(int32 InGlobalFrame, FFrameRate InTickResolution)
{
    if (!PreviewMeshComponent || CachedSections.Num() == 0) return;

    // 1) 매칭 Section 선형 탐색 — InGlobalFrame ∈ [Start, End] 인 첫 Section.
    UMCComboMontageSection* MatchedSection = nullptr;
    UAnimMontage* MatchedMontage = nullptr;
    int32 MatchedStartFrame = 0;
    for (const FCachedSection& Entry : CachedSections)
    {
        UMCComboMontageSection* Sec = Entry.Section.Get();
        UAnimMontage* Mon = Entry.Montage.Get();
        if (!Sec || !Mon) continue;
        const int32 SF = Sec->GetStartFrame().Value;
        const int32 EF = Sec->GetEndFrame().Value;
        if (InGlobalFrame >= SF && InGlobalFrame <= EF)
        {
            MatchedSection = Sec; MatchedMontage = Mon; MatchedStartFrame = SF;
            break;
        }
    }
    if (!MatchedSection || !MatchedMontage) return;  // hold last pose (Section 사이 gap / 범위 밖)

    // 2) ⭐ Section 전환 검사 — 이전 활성 Section 과 다르면 SetAnimation/SetPlayRate 재호출.
    //    매 frame SetAnimation 폭주 회피 — UAnimSingleNodeInstance::SetAnimationAsset 가
    //    InitializeAnimation + Proxy 시간 0 reset → 매 frame 호출 시 SetPosition 무효화.
    if (MatchedSection != CurrentActiveSection.Get())
    {
        PreviewMeshComponent->SetAnimation(MatchedMontage);
        PreviewMeshComponent->SetPlayRate(MatchedSection->PlayRate);
        PreviewMeshComponent->Stop();  // SetAnimation 자동 Play 활성화 방지 — scrub 일관성
        CurrentActiveSection = MatchedSection;
    }

    // 3) Local time 변환 + SetPosition.
    const int32 LocalFrameValue = InGlobalFrame - MatchedStartFrame;
    const float LocalSeconds = static_cast<float>(InTickResolution.AsSeconds(FFrameTime(FFrameNumber(LocalFrameValue))));
    const float ClampedSeconds = FMath::Clamp(LocalSeconds, 0.0f, MatchedMontage->GetPlayLength());
    PreviewMeshComponent->SetPosition(ClampedSeconds, /*bFireNotifies=*/false);
}
```

### 5.15.5 핵심 설계 결정 4건

| 결정 | 근거 |
| -- | -- |
| **Section 전환 검사 (`MatchedSection != CurrentActiveSection.Get()`) 의무** | `AnimSingleNodeInstance.h` L74 `SetAnimationAsset` = `InitializeAnimation` + Proxy 시간 0 reset. 매 frame 호출 시 매 frame 시간 0 → 자체 SetPosition 무효화. |
| **선형 탐색** | Sequencer-lite scope (Section < ~20) 가정. 대규모 시 binary search + sorted cache 격상 가능 (M3 후속). |
| **Section 중첩 시 첫 매칭 우선 (Outliner 등록 순서)** | Phase 4f lane allocation 가 중첩 허용. 우선순위 정의 별도 — M3 (OverlapPriority desc sort) 후속. |
| **매칭 없음 → hold (직전 pose)** | 사용자 시각 일관성. ref pose reset 옵션 Phase 5c 검토 (T3). |

### 5.15.6 evaluator 결과 (general-purpose role) — 8.4/10

| 기준 | 점수 | 핵심 |
| -- | -- | -- |
| Engine authority | 9/10 | SEditorViewport::Tick / World::Tick(LEVELTICK_All) / TickAnimation / SetPosition / SetAnimation 모두 시그니처 검증 통과 |
| Policy compliance | 8/10 | `#if WITH_EDITOR` guard / TWeakObjectPtr lifetime / vault cross-link 표준 준수 |
| Pitfall awareness | 9/10 | Editor world tick skip / SetAnimationAsset proxy reset / auto-Play 후 Stop / GetPlayLength clamp / Section gap hold 모두 명시 처리 |
| Performance/Memory | 8/10 | 선형 탐색 < ~20 합리적 / WeakPtr GC-safe / cache 는 LoadAssetPreview 1회 build |
| Maintainability | 8/10 | FCachedSection 명확 / Phase tag history trace / Phase 5c extension point 명시 |

**Major 0 / Minor 5 / Tip 4** (모두 비차단):

- M1 — **Asset edit 시 cache 재생성 미수행** — `LoadAssetPreview()` Construct 1회. `NotifyTrackChanged` 안 `ReloadPreviewCache` 훅 권장. ⭐ 우선 (디자이너 워크플로 실용성)
- M2 — **Skeleton 통일 미강제** — 첫 Section Skeleton 의 PreviewMesh 만 set. 후속 Section 다른 Skeleton 시 SetAnimation 시 Engine warning + pose freeze. Cache build 시 Skeleton 검사 + skip + UE_LOG Warning
- M3 — **Section overlap order-dependent match** — 선형 탐색 첫 매칭. `OverlapPriority` / `RowIndex` 이미 존재 — 활용 안 함. 게임플레이 evaluator 와 preview 불일치 위험
- M4 — **`TickAnimation` 명시 vs `bUpdateAnimationInEditor` 중복** — anim graph 매 frame 2회 evaluate. canonical path 하나 선택 (현재 belt+suspenders)
- M5 — 헤더 L34 doc comment 누락 (trivial)

**Tip 4**:
- T1 — Cache rebuild path 시 CurrentActiveSection nullptr reset 의무
- T2 — MatchedStartFrame int32 wrap bound 명시 (24000 fps × 24hr+ 시)
- T3 — Phase 5c gap handling 시 sticky-hold to last Section's *end pose* (mid-pose freeze 보다 결정적)
- T4 — `SyncPreviewToScrub` 안 TickResolution.IsValid() 방어적 검사 (div-by-zero 회피)

**Per-change 점수**:
- Phase 5a — Tick override 3축: **9/10** (M4 nit 만)
- Phase 5a — SetUpdateAnimationInEditor flag: **8/10** (M4 만 차감)
- Phase 5a — SyncPreviewToScrub chain: **9/10** (T4 trivial)
- Phase 5b — CachedSections 구조/배열: **8/10** (M1+M2 차감)
- Phase 5b — Section transition guard: **9/10** (M3 만 차감)

### 5.15.7 후속 처리 우선순위

1. **M1 (Cache invalidation on edit)** — `NotifyTrackChanged` → `ReloadPreviewCache` 훅. ⭐ 우선
2. **M3 (Overlap priority)** — `OverlapPriority` desc sort
3. **M2 (Skeleton uniformity)** — UE_LOG Warning + skip
4. **M4 (Double-tick)** — canonical path 결정 (flag 또는 Tick 중 하나)
5. T1-T4 — 선택 적용

## 6 (자산 동기화 — 기존 본문 유지)

## 7. 빌드 함정 매트릭스 (54 건 + Phase 5a/5b 신규 2건)

### 7.1 발생한 함정 + fix

| # | 함정 | 원인 | fix | Phase |
| -- | -- | -- | -- | -- |
| 1-54 | (Phase 1-Cycle 5p+7 누적) | (기존) | (기존) | 1~5p+7 |
| **55 (Phase 5a)** | **`UDebugSkelMeshComponent::SetPosition` 만 호출 → silent fail (Editor world 안 pose 미갱신, 빌드 OK + 에러 0)** | `SetPosition` 은 `Proxy.CurrentTime` 만 set. Pose 재평가는 component Tick 경유 의무. `EWorldType::EditorPreview` 안 `ShouldTickPose`/`ShouldUpdateTransform` 가 `bUpdateAnimationInEditor` 검사하지만 default false + WorldType 분기 미진입 시 SKIP. | `SCompoundWidget::Tick` override 안 3축 명시: `SEditorViewport::Tick` + `PreviewScene->GetWorld()->Tick(LEVELTICK_All, DeltaTime)` + `PreviewMeshComponent->TickAnimation(DeltaTime, false)`. `SetUpdateAnimationInEditor(true)` 는 보조 fallback. | **Phase 5a** |
| **56 (Phase 5b)** | **매 frame `SetAnimation` 호출 시 Proxy 시간 0 reset → 자체 SetPosition 무효화** | `UAnimSingleNodeInstance::SetAnimationAsset` 가 `InitializeAnimation` + 시간 0 reset (Engine `AnimSingleNodeInstance.h` L74). Multi-section sequential playback 시 매 frame Section 매칭 + SetAnimation 호출 → 매 frame 시간 0 → SetPosition 무효. | **Section transition guard** — `if (MatchedSection != CurrentActiveSection.Get()) { SetAnimation + SetPlayRate + Stop + Update CurrentActiveSection; }`. 이전 활성 Section 과 같으면 SetAnimation skip → 다음 SetPosition 정상 작동. | **Phase 5b** |

### 7.2 회피한 함정 (사전 vault 적용)

(기존 + **Phase 5a/5b 신규**:
- vault [[synthesis/ue-editor-preview-mesh-scrub-tick-pattern]] PS01/PS02/PS03/PS04 4종 — 사전 격상으로 KMCProject 다음 case study 가 동일 함정 회피 가능
- [[sources/ue-editor-personatoolkit]] §2.4.1 + 함정 10/11 — Persona toolkit 외부 자체 PreviewScene 시 Tick 3축 의무 vault 명시)

## 8. 4 종 품질 자체 평가 (Phase 5b 진입 후)

| 기준 | 점수 | 근거 |
| -- | -- | -- |
| Performance (35%) | 90 / 100 | Phase 5a Tick 3축 — anim graph 매 frame 1-2회 evaluate (M4 — flag + 명시 중복 시 2회). M4 정리 시 1회. Phase 5b 선형 탐색 < 20 — 무시 가능. |
| Memory (25%) | 95 / 100 | FCachedSection 배열 ~16 byte/entry × N < ~320 byte. CurrentActiveSection 8 byte. 무시 가능. M1 fix 시 ReloadPreviewCache 호출 시점 메모리 재할당 (Reset + Add) — 매 NotifyTrackChanged 1회 — 부담 없음. |
| Network (15%) | N/A → 100 | Editor only 만점 |
| Maintainability (25%) | 89 / 100 | Cycle 5p+7 (89) + Phase 5a/5b 추가 — Phase tag history trace 명확. M5 (header doc comment), M4 (canonical path 결정) 정리 시 92. |

**가중 평균**: (90 × 0.35) + (95 × 0.25) + (100 × 0.15) + (89 × 0.25) = **91.5 / 100** (PASS, ≥ 90).

## 9-10 (회피 결정 / Cross-link — 기존 본문 유지)

### 관련 fix log (KMCProject 2026-05-15 ~ 2026-05-19)

(기존 22건 유지 + Cycle 5p+7 1건)
- ⭐⭐⭐ **`[2026-05-19] fix | MCComboEditor Phase 5a hotfix — Editor PreviewMesh scrub silent fail (Tick override 명시)`**. 2 진단 (1차 SetUpdateAnimationInEditor → 2차 Tick override 3축). Engine 권위 — SkeletalMeshComponent.cpp L1689/L1732. 사용자 검증 통과.
- ⭐⭐⭐ **`[2026-05-19] feature | MCComboEditor Phase 5b — Multi-section sequential playback (Timeline playback time → 자동 Section 전환)`**. CachedSections 배열 + Section transition guard. Engine 권위 — AnimSingleNodeInstance.h L74 SetAnimationAsset Proxy reset.
- ⭐⭐⭐ **`[2026-05-19] verify | MCComboEditor Phase 5a hotfix + Phase 5b 통합 evaluator — 8.4/10 (Major 0 / Minor 5 / Tip 4)`**. Per-criterion 9/8/9/8/8 (Engine authority/Policy/Pitfall/Perf/Maint). Per-change 9/8/9/8/9. PASS.

## 11. 후속 검증 후보

### 11.1 Phase 매트릭스 (Phase 5b 진입 후)

| # | 항목 | 상태 |
|---|---|---|
| Phase 1-Phase 5p+8 + Cycle 5p+5/+6/+7 (누적) | (기존) | ✅ 완료 |
| **Phase 5a hotfix — PreviewMesh Scrub Tick 3축** | **Editor world silent fail 해소 + Tick override + SyncPreviewToScrub chain + flag fallback** | ✅ **완료** |
| **Phase 5b — Multi-section sequential playback** | **CachedSections 배열 + Section transition guard + 자동 Section 전환** | ✅ **완료** |
| **Phase 5a/5b 통합 evaluator** | **8.4/10 PASS (Major 0 / Minor 5 / Tip 4)** | ✅ **완료** |
| Phase 5a/5b Minor 정리 (M1-M5) | M1 (cache rebuild on NotifyTrackChanged) ⭐ 우선 / M3 (OverlapPriority sort) / M2 (Skeleton uniformity Warning) / M4 (canonical Tick path) / M5 (doc comment) | 🟡 선택 |
| Phase 5c — Section gap handling + AnimNotify 전파 | sticky-hold end pose (T3) + StartFrameOffset 반영 + bFireNotifies | 🟡 후속 |
| Phase 5d — Transform Section runtime evaluation 통합 | Transform Track scrub → actor world transform 적용 | 🟡 후속 |

### 11.2 vault 일반화 후보

- [x] 기존 11 종 모두 완료 (+ Phase 5a `synthesis/ue-editor-preview-mesh-scrub-tick-pattern`) ✅

## 12. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-15 ~ 2026-05-18 (Phase 1-Phase 5p+8) | (기존 14 행 누적) |
| 2026-05-19 (Cycle 5p+5) | (기존) |
| 2026-05-19 (Cycle 5p+6) | (기존) |
| 2026-05-19 (Cycle 5p+7) | (기존) |
| **2026-05-19 (Phase 5a hotfix — PreviewMesh Scrub Tick 3축)** | **§1 Thesis 3 행 신규 (Tick 3축 / SetUpdateAnimationInEditor fallback / SyncPreviewToScrub chain) + §5.14 신규 sub-§ 7개 (5.14.1-5.14.7 — 증상/1차 진단/2차 진단/표준 패턴/축 역할/chain/일반화 페이지) + §7.1 함정 55 (SetPosition silent fail) 신규 + §11.1 Phase 5a 행 ✅ + §12 변경 이력. sources cross-link [[synthesis/ue-editor-preview-mesh-scrub-tick-pattern]] 추가 (신규 일반화 페이지). entities cross-link [[entities/USkeletalMeshComponent]] + [[entities/UAnimMontage]] 추가. frontmatter tags 3 추가 (phase-5a-preview-tick-3axis / phase-5a-set-update-anim-in-editor-fallback / phase-5a-sync-preview-to-scrub-chain).** |
| **2026-05-19 (Phase 5b — Multi-section sequential playback)** | **§1 Thesis 2 행 신규 (CachedSections 배열 / Section transition guard) + §5.15 신규 sub-§ 7개 (5.15.1-5.15.7 — 목적/데이터 구조/LoadAssetPreview/SyncToScrubFrame/설계 결정/evaluator/후속 처리) + §7.1 함정 56 (SetAnimationAsset Proxy reset) 신규 + §8 91.5/100 PASS + §11.1 Phase 5b 행 ✅ + §11.1 Phase 5c/5d 후속 후보 추가 + §12 변경 이력. frontmatter tags 4 추가 (phase-5b-multi-section-sequential-playback / phase-5b-cached-sections-array / phase-5b-section-transition-guard / set-animation-asset-proxy-reset-trap).** |
| **2026-05-19 (Phase 5a/5b 통합 evaluator)** | **8.4/10 PASS (Major 0 / Minor 5 / Tip 4). Per-criterion 9/8/9/8/8 (Engine authority/Policy/Pitfall/Perf/Maint). Per-change 9/8/9/8/9. M1 우선 (cache rebuild on NotifyTrackChanged). citation_disclosure 102+→110+ / Engine 권위 102+→110+건 verify. frontmatter tags 3 추가 (debugskel-set-position-silent-fail / world-tick-leveltick-all / animinstance-tick-animation-explicit). title 갱신 — Phase 5a/5b 통합.** |
