---
type: synthesis
title: "KMCProject MCComboEditor — Phase 6-8 인하우스 툴 마스터 (확장성 + 런타임 + Visitor 패턴 완성)"
slug: mc-combo-editor-phase-6-7-inhouse-master
created: 2026-05-20
last_updated: 2026-05-21
project_role: case-study
project: KMCProject
measured_date: 2026-05-21
sources:
  - "[[sources/ue-levelsequence-moviescene]]"
  - "[[sources/ue-levelsequence-tracks]]"
  - "[[sources/ue-animation-animinstance]]"
  - "[[sources/ue-coreuobject-serialization]]"
  - "[[synthesis/mc-combo-editor-phase-5g-5l-drag-ux-suite]]"
  - "[[synthesis/mc-combo-section-levelsequence-style-upgrade]]"
  - "[[synthesis/mc-combo-editor-levelsequence-lite]]"
  - "[[synthesis/ue-track-area-section-paint-anatomy]]"
  - "[[synthesis/ue-tree-uobject-expansion-bidirectional-sync]]"
  - "[[synthesis/mc-combo-editor-phase-8-channel-iterator]]"
concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
status: living
tags: [synthesis, kmcproject, mc-combo, phase-6, phase-6a, phase-6a-2, phase-6b, phase-6b-2, phase-6c, phase-6c-2, phase-6c-2-2, phase-6e, phase-6f, phase-6g, phase-7a, phase-7a-2, phase-8, phase-8-1, phase-8-2, phase-8-2-2, inhouse-master, extensibility, virtual-api, fgraphnodeclass-helper, runtime-evaluation, visitor-pattern, sequencer-lite-completion, track-binding-scope, section-begin-progress-end, asset-level-track, duplicate-policy, cast-removal-100]
citation_disclosure: "🟢 30 — Engine source 직접 인용 (AnimNotifyState BIE / FGraphNodeClassHelper RootClass / UMovieSceneTrack EvaluateAtFrame / Visitor 패턴 IMovieScenePlayer 미러) + KMCProject Phase 6a-8.2.2 실측 + 누적 ue-evaluator 7회 (83→89→91→90→88→91→91) + Cast 24/24 = 100% 제거 매트릭스 + 권고 #1-#5 일괄 반영 (2026-05-21)"
---

# KMCProject MCComboEditor — Phase 6-8 인하우스 툴 마스터 (Visitor 패턴 완성 + 100% Cast)

> **2026-05-21 — 본 페이지는 Phase 6-7 + Phase 8 시리즈 base case study.** Phase 8 의 channel iterator + SSoT 통합 + 권고 #1-#5 반영은 후속 페이지 [[mc-combo-editor-phase-8-channel-iterator]] canonical (본 페이지는 reference). Cast 24/24 = **100% 제거 달성** (Phase 8.2.2). 확장성 추상화 + 자동 발견 + Track binding scope 2 분류 + 런타임 evaluation (Begin/Progress/End BIE + 시간 jump + Solo mute) + Visitor 기반 runtime collector + 중복 정책 정리 + auto-numbering 옵션. **사용자 동작 검증 완료**. **7차 evaluator 91/100 LIVE**.

## 1. Thesis — 인하우스 툴 마스터 의의

| 축 | 이전 (Phase 5p 종료) | Phase 6-8 완료 후 |
| -- | -- | -- |
| **새 Track type 추가** | 4-6 분기 코드 수정 | **0 수정** — virtual override + UCLASS + GetBindingScope() 만 |
| **새 Section type 추가** | 12 Cast 분기 산재 — 모두 수정 의무 | **0 수정** — 7+3 BIE virtual override 만 |
| **C++ Track/Section 자동 발견** | `GetDerivedClasses` 매 메뉴 열림마다 | **캐시 1회** + AssetRegistry hot-reload |
| **BP Track/Section 자동 발견** | **미지원** | **자산 저장 즉시 메뉴 등장** (FGraphNodeClassHelper::OnFilesLoaded) |
| **Track scope 분류** | 모든 Track 가 Binding 아래 (SkeletalMesh 종속) | **SkeletalMesh ↔ Asset 2 분류** + 메뉴 양방향 필터 |
| **Section 런타임 hook** | 없음 — Section 자체 동작 정의 path 없음 | **OnSectionBegin / Progress / End BIE** + 시간 jump 통과 + Solo mute |
| **Runtime collector Cast** | Track type 별 4 Cast 산재 | **Visitor 패턴** — Cast 0, Section 자손이 type-specific dispatch |
| **Cast 분기 누적 제거** | 24 산재 | **24 제거 = 100%** (Phase 8.2.2 — Phase 8 후속 페이지 §8 canonical) |
| **중복 정책** | 모두 차단 (Track 종류 1개) | **scope 별 분리** — SkeletalMesh 차단 / Asset 허용 |
| **Asset Track 중복 instance 식별** | (미지원) | **TrackName auto-suffix** ("Audio #2") + `bAlwaysSuffixFirst` 옵션 |
| **ue-evaluator 점수** | (미평가) | 7회 누적: 83 → 89 → 91 → 90 → 88 → 91 → **91** (live 유지) |

**핵심 가치**: 인하우스 디자이너가 게임플레이 콤보 / 입력 시퀀스 / 오디오 큐 / 카메라 동선 등 새 시스템 추가 시 **엔지니어 호출 없이 BP 자손 작성만으로 자동 통합**. Sequencer 통합 비용 회피 + LevelSequence 권위 패턴 미러 + Visitor 패턴으로 type-specific runtime 처리 격리.

## 2. Phase 매트릭스 (16 단계 누적) — **Canonical Phase 정의 (§4/§9 cross-reference)**

| Phase | 내용 | Cast 제거 | 누적 | 핵심 산출 |
| -- | -- | -- | -- | -- |
| **6a** | Section 베이스 2 virtual + `EMCComboRowButtonHints` bitflags | -3 | 3 | TrackArea/OutlinerRow 분기 추상화 1차 |
| **6a cleanup** | `bIsTransformSectionRow` 호환 별칭 제거 (Article 4 권고) | 0 | 3 | 단순성 충족 |
| **6a-2** | `FMCComboSubPropertySpec` USTRUCT + `AppendOutlinerSubProperties` virtual | -4 | 7 | OutlinerView 4 Cast 제거 |
| **6b 1차** | `GetSecondaryDisplayString` + `GetDecorationKeyframes` 데이터-only virtual | -2 | 9 | TrackArea paint decoration |
| **6b-2** | 베이스 channel API 격상 + `EMCComboInterpMode` 베이스 이동 + AddKeyAtScrub hint | -6 | 15 | Channel SSpinBox + context menu |
| **6c 검증** | 신규 `UMCComboAudioTrack` 골격 — 자동 발견 실측 | 0 | 15 | 새 Track 추가 비용 = 2 파일 |
| **6c paint 1차** | TrackArea SubRow label `AppendOutlinerSubProperties` spec 활용 | -1 | 16 | Cast 16/24 = 67% |
| **6e** | `MCComboTrackClassCache` = `FGraphNodeClassHelper(UMCComboTrack)` | 0 | 16 | **C++/BP Track 자동 발견** |
| **6f** | `MCComboSectionClassCache` + Section 자손 entry 표시 | 0 | 16 | **Section 자손 자동 발견** |
| **6f-2** | `Track::AddSection(OverrideClass)` 시그니처 확장 | 0 | 16 | Article 8 정직성 해소 |
| **6g** | `EMCComboTrackBindingScope` enum + Asset/Binding 메뉴 scope 양방향 필터 | 0 | 16 | **Input/Audio Track Asset scope 분리** |
| **7a** | `UMCComboSection::OnSectionBegin/Progress/End` BIE + Track/Asset dispatcher | 0 | 16 | **Sequencer-lite 런타임 API 완성** |
| **7a-2** | 시간 jump 통과 Section + Solo mute + 역방향 시간 처리 | 0 | 16 | **Sequencer 표준 transition** 완성 |
| **6c-2** | `SetSubGroupExpanded` + `AppendSubRowPaintEntries` virtual | -2 | 18 | TransformSection 9 channel 추상화 1차 |
| **8** | **`IMCComboPreviewVisitor` 인터페이스 + `AcceptPreviewVisitor` virtual** | **-4** | **22** | **PreviewSceneViewport collector Cast 0** ([[mc-combo-editor-phase-8-channel-iterator]] §2) |
| **6c-2.2** | `FSubRowDef` channel ptr → `KeyTimes` 필드 교체 — FMCComboFloatKey 의존 0 | 0 (간접) | 22 | 데이터-only paint loop |
| **8.1** | Asset 중복 instance TrackName auto-suffix + `bAlwaysSuffixFirst` 옵션 | 0 | 22 | Asset Track UX 식별 ([[mc-combo-editor-phase-8-channel-iterator]] §3) |
| **8.2 / 8.2.2** | **`GetMutableChannelKeys` + `GetAllChannelNames` + `SortAllChannels` 베이스 virtual + drag/hit-test 마이그레이션** | **-2** | **24** | **100% Cast 달성** ([[mc-combo-editor-phase-8-channel-iterator]] §4) |
| **중복 정책** | Asset scope 중복 허용 / SkeletalMesh scope 차단 유지 | 0 | 24 | **Asset Track 여러 instance 허용** |

> ⭐ **Article 9 SSoT** — 본 매트릭스가 Phase 정의의 **canonical source**. §4 (virtual API 매트릭스) 와 §9 (Cast 위치 매트릭스) 는 Phase number 만 reference, 누적/내용 중복 X. Phase 8 시리즈 (8 / 8.1 / 8.2 / 8.2.2) 의 상세 case study 는 후속 페이지 [[mc-combo-editor-phase-8-channel-iterator]] canonical.

## 3. 5단계 데이터 모델 (Phase 6g + 중복 정책 + 8.1 auto-numbering)

```
UMCComboAsset
 ├─ TickResolution / DisplayRate / PlaybackDuration
 ├─ bAlwaysSuffixFirst                          ⭐ Phase 8.1 (권고 #3) — Asset auto-numbering 정책 옵션
 ├─ AssetLevelTracks[]                          ⭐ Phase 6g — Binding 무관, 중복 허용
 │   ├─ UMCComboInputTrack    (scope=Asset)     ⭐ 같은 클래스 N instance OK
 │   ├─ UMCComboAudioTrack    (scope=Asset)     ⭐ TrackName = "Audio" (1st instance)
 │   ├─ UMCComboAudioTrack    (scope=Asset)     ⭐ TrackName = "Audio #2" (2nd instance auto-suffix)
 │   └─ ... (사용자 BP scope=Asset 자손)
 │       └─ Sections[]
 │           └─ Virtual API (Phase 6/7/8) — §4 매트릭스 참조
 └─ Bindings[]
     ├─ UMCComboBinding (SkeletalMesh + 메타)
     │   └─ Tracks[] (scope=SkeletalMesh only) — **중복 차단** (Phase 3+ 옵션 C)
     │       ├─ UMCComboMontageTrack   ⭐ Mesh 별 1개만
     │       ├─ UMCComboTransformTrack ⭐ Mesh 별 1개만
     │       └─ ...
     └─ ...
```

## 4. Section 베이스 13+3 virtual API 매트릭스

> Phase 번호는 §2 reference. 본 매트릭스는 **virtual signature + default / Montage / Transform 동작 + 호출처** 만 명시.

| Virtual | Phase | Default | Montage | Transform | 호출처 |
| -- | -- | -- | -- | -- | -- |
| `GetOutlinerSubRowCount()` | 6a | 3 | 4 | 3 + 3·bExpand | TrackArea ComputeTrackExtraSubRowCount |
| `GetEditorRowButtonHints()` | 6a | None | None | KeyframeNav \| AddKeyAtScrub | OutlinerRow + OutlinerView 메뉴 |
| `AppendOutlinerSubProperties(Specs&)` | 6a-2 | 3 spec | 4 (+ SlotName) | 3 group + 9 channel | OutlinerView AppendSubPropertyItems |
| `GetSecondaryDisplayString()` | 6b 1차 | "" | SlotName | "" | TrackArea L5 (Yellow 라벨) |
| `GetDecorationKeyframes()` | 6b 1차 | {} | {} | GetUniqueKeyTimes() | TrackArea L6 + nav |
| `GetChannelValueAtLocalFrame(Name, Frame)` | 6b-2 | 0.0f | (default) | 9 channel 보간 | OutlinerRow SSpinBox |
| `SetChannelKeyAtGlobalFrame(Name, Frame, Val, Mode)` | 6b-2 | no-op | (default) | 1 channel key | SSpinBox Commit |
| `AddKeyAtGlobalFrame(Frame, Mode)` | 6b-2 | no-op | (default) | 9 channel SetKeyAll | Add Key 메뉴 |
| `SetSubGroupExpanded(GroupName, bExpanded)` | 6c-2 | no-op | (default) | bExpand* mutate + Modify | OutlinerView SubProperty 토글 |
| `AppendSubRowPaintEntries(Entries&)` | 6c-2 | {} | (default) | 3 group + 9 channel + KeyTimes | TrackArea SubRow paint |
| **`AppendSubRowPaintEntriesWithSectionRow(Entries&)`** | **권고 #2** | **dummy + AppendSubRowPaintEntries** | (default) | (default) | **TrackArea drag start hit-test** |
| **`GetMutableChannelKeys(Name)`** | **8.2** | **{}** | (default) | **9 channel pointer-to-member** | **TrackArea drag/hit-test** |
| **`GetAllChannelNames()`** | **8.2.2** | **{}** | (default) | **9 ChannelName SSoT** | **TrackArea drag mid** |
| **`SortAllChannels()`** | **8.2.2** | **no-op** | (default) | **9 channel Sort (SSoT iterate)** | **TrackArea drag end** |
| **`AcceptPreviewVisitor(Visitor&)`** | **8** | **VisitGenericSection** | **VisitMontageSection** | **VisitTransformSection** | **PreviewSceneViewport collector** |
| **`OnSectionBegin/Progress/End(Context, ...)`** | 7a BIE | (native X) | (BP 책임) | (BP 책임) | Track::EvaluateAtFrame |

## 5. Track binding scope + 중복 정책 매트릭스

| Track 자손 | scope | 위치 | 메뉴 | **중복** | 식별 |
| -- | -- | -- | -- | -- | -- |
| `UMCComboMontageTrack` | SkeletalMesh | Binding->Tracks | Binding ⊕ | 🚫 차단 | TrackName 단일 |
| `UMCComboTransformTrack` | SkeletalMesh | Binding->Tracks | Binding ⊕ | 🚫 차단 | TrackName 단일 |
| `UMCComboNotifyTrack` | SkeletalMesh | Binding->Tracks | Binding ⊕ | 🚫 차단 | TrackName 단일 |
| `UMCComboInputTrack` | **Asset** | Asset->AssetLevelTracks | **Asset ⊕** | ✅ **허용** | **auto-suffix** ⭐ Phase 8.1 |
| `UMCComboAudioTrack` | **Asset** | Asset->AssetLevelTracks | **Asset ⊕** | ✅ **허용** | **auto-suffix** ⭐ Phase 8.1 |
| (사용자 BP) | CDO `GetBindingScope()` 결정 | scope 자동 라우팅 | scope 자동 분기 | scope 별 정책 자동 | scope 별 정책 자동 |

**중복 정책 근거**:
- **SkeletalMesh scope 차단**: 1 mesh 안 같은 Track 종류 모호 — Mesh 별 시스템 단일 의미.
- **Asset scope 허용**: 사용자가 같은 Track 여러 instance 의도 (예: AudioTrack 2개 — 다른 SoundCue / 다른 PlayRate / 다른 lane).
- **auto-suffix 식별** (Phase 8.1 + 권고 #3): 첫 instance `Audio` / 2nd `Audio #2` (default) — `bAlwaysSuffixFirst=true` 시 첫 instance 부터 `Audio #1`.

## 6. FGraphNodeClassHelper 자동 발견 매트릭스 (Phase 6e/6f)

| 캐시 | RootClass | 호출처 | 효과 |
| -- | -- | -- | -- |
| `MCComboTrackClassCache` | `UMCComboTrack::StaticClass()` | OutlinerView Asset ⊕ + Binding ⊕ | C++/BP Track 자손 자동 발견 + AssetRegistry hot-reload |
| `MCComboSectionClassCache` | `UMCComboSection::StaticClass()` | OutlinerView Track ⊕ (자손 entry) | C++/BP Section 자손 자동 발견 |

Story/Parts editor 패턴 미러 (`MCStoryClassCache` / `MCPartsClassCache` / `MCStoryDecoratorClassCache`).

## 7. Phase 7a-2 — Runtime evaluation transition (완성)

`UMCComboTrack::EvaluateAtFrame(CurrentGlobalFrame, PrevGlobalFrame, DeltaSeconds, Context)`:

```cpp
// ⭐ Phase 7a-2 — 역방향 시간 + 통과 Section 처리
const bool bHasPrev = (PrevGlobalFrame != INDEX_NONE);
const int32 RangeLo = bHasPrev ? FMath::Min(PrevGlobalFrame, CurrentGlobalFrame) : CurrentGlobalFrame;
const int32 RangeHi = bHasPrev ? FMath::Max(PrevGlobalFrame, CurrentGlobalFrame) : CurrentGlobalFrame;

for (Section : Sections)
{
    if (!Section || !Section->bIsActive) continue;
    if (IsSectionEffectivelyMuted(Section)) continue;  // ⭐ Phase 7a-2 — Solo mute

    const bool bWasIn = bHasPrev && Section->IsFrameInSection(PrevGlobalFrame);
    const bool bIsIn  = Section->IsFrameInSection(CurrentGlobalFrame);

    if (!bWasIn && bIsIn)   Section->OnSectionBegin(Context);
    if (bIsIn)              Section->OnSectionProgress(Context, Alpha, DeltaSeconds);
    if (bWasIn && !bIsIn)   Section->OnSectionEnd(Context);

    // ⭐ Phase 7a-2 — 통과 Section (Sequencer 표준 — scrub jump)
    // ⭐ evaluator 권고 #1 fence-post 명시:
    //   교차 검사 `SecStart <= RangeHi && SecEnd >= RangeLo` 는 **closed-closed** interval (양 끝점 포함).
    //   IsFrameInSection 자체도 closed-closed (Start <= F <= End) — 정합 의무.
    //   Edge: SecEnd == RangeLo 시 통과 판정 (Section 끝 frame 도 발화 보장).
    if (!bWasIn && !bIsIn && bHasPrev)
    {
        const int32 SecStart = Section->GetStartFrame().Value;
        const int32 SecEnd   = Section->GetEndFrame().Value;
        if (SecStart <= RangeHi && SecEnd >= RangeLo)
        {
            Section->OnSectionBegin(Context);
            Section->OnSectionEnd(Context);  // Progress skip (지나친 의미)
        }
    }
}
```

| Prev in | Curr in | Section 통과 | 호출 | Sequencer 표준 |
| -- | -- | -- | -- | -- |
| false | true | — | Begin + Progress | AnimNotifyState ReceiveBegin + Tick |
| true | true | — | Progress | ReceiveTick |
| true | false | — | End | ReceiveEnd |
| false | false | **통과** ⭐ | **Begin + End** | scrub jump 시 발화 |
| false | false | 미통과 | (skip) | — |

## 8. Phase 8 — Visitor 패턴 (runtime collector 추상화)

> **상세 case study + Phase 8 시리즈 (8 / 8.1 / 8.2 / 8.2.2) 누적 진척**: [[mc-combo-editor-phase-8-channel-iterator]] canonical. 본 절은 요약만.

### 인터페이스 (`MCComboPreviewVisitor.h`, **runtime 모듈**)

```cpp
class MCPLAYMODULE_API IMCComboPreviewVisitor
{
public:
    virtual ~IMCComboPreviewVisitor() = default;
    virtual void VisitMontageSection(UMCComboMontageSection* Section) {}
    virtual void VisitTransformSection(UMCComboTransformSection* Section) {}
    virtual void VisitGenericSection(UMCComboSection* Section) {}
};
```

Slate 의존 X — forward declare 만. Engine 권위: `IMovieScenePlayer` 패턴 미러.

### Section 베이스 + 자손 dispatch

```cpp
void UMCComboSection::AcceptPreviewVisitor(V) { V.VisitGenericSection(this); }
void UMCComboMontageSection::AcceptPreviewVisitor(V) { V.VisitMontageSection(this); }
void UMCComboTransformSection::AcceptPreviewVisitor(V) { V.VisitTransformSection(this); }
```

**Cast 4개 제거** — Phase 8 의 핵심 ROI. + Phase 8.2.2 의 channel iterator 로 **잔존 2 Cast 도 제거 → 24/24 = 100%**. (자세히 [[mc-combo-editor-phase-8-channel-iterator]] §2/§4)

### 새 Section type 추가 비용 (3 곳, 정직성)

1. Visitor 인터페이스에 `VisitX` 메서드 추가 (default no-op) — runtime 모듈 헤더 변경 + 빌드 재현 ⚠
2. Section 자손이 `AcceptPreviewVisitor` override 안 `Visitor.VisitX(this)` 호출
3. Collector 구현체 (Editor 측) 에서 `VisitX` override (필요 시)

→ collector **본체 무수정**. Cast 분기 산재 vs interface 통합 — 정직한 trade-off.

## 9. Cast 분기 제거 위치 매트릭스 (24/24 = 100%)

> Phase 번호 + 누적은 §2 reference. Phase 8 시리즈 6 위치 + 잔존 0 의 상세는 [[mc-combo-editor-phase-8-channel-iterator]] §8 canonical.

| 위치 | Phase | 상태 |
| -- | -- | -- |
| `SMCComboTrackArea::ComputeTrackExtraSubRowCount` (TransformSection + MontageSection) | 6a | ✅ 제거 |
| `SMCComboOutlinerRow::Construct (bIsTransformSectionRow)` | 6a | ✅ 제거 |
| `SMCComboOutlinerView::AppendSubPropertyItems` (Cast 4 분기) | 6a-2 | ✅ 제거 |
| `SMCComboTrackArea` L1007 (Montage SlotName) + L1040 (Transform diamond) | 6b 1차 | ✅ 제거 |
| `SMCComboOutlinerRow` L595/626/687/703 (channel SSpinBox + Prev/Next nav) | 6b-2 | ✅ 제거 |
| `SMCComboOutlinerView` L717/854 (context menu + HandleAddTransformKey) | 6b-2 | ✅ 제거 |
| `SMCComboTrackArea` L1193 (Montage SubRow Slot Name) | 6c 1차 | ✅ 제거 |
| `SMCComboOutlinerView` L384 (SubProperty group expand) + `SMCComboTrackArea` L1156 (sub-row label) | 6c-2 | ✅ 제거 |
| **`SMCComboPreviewSceneViewport.cpp` collector (4 Cast: Montage/Transform Track + Section)** | **8** | **✅ Visitor** |
| **`SMCComboTrackArea` drag start (L1568) + hit-test (L1668) + drag mid (L1877) + drag end (L2030)** | **8.2.2** | **✅ Channel iterator (`GetMutableChannelKeys` + `GetAllChannelNames` + `SortAllChannels`)** |

## 10. ue-evaluator 평가 매트릭스 (누적 7회)

| 평가 | Phase | 점수 | 판정 |
| -- | -- | -- | -- |
| 1차 | 6a 단독 | 83 | evaluated |
| 2차 | 6a cleanup + 6a-2 + 6b 1차 | **89** | live |
| 3차 | 6b-2 | **91** | live (+2) |
| 4차 | 6e | **90** | live (-1, ShutdownModule cleanup 즉시 반영) |
| 5차 | 6c 검증 + 6f + 6c paint 1차 | 88 | evaluated (Article 8 위반 — Phase 6f-2 hotfix 후 재평가) |
| **6차** | **Phase 7a + 7a-2 + 8 + 6c-2/6c-2.2 + 중복 정책 통합** | **91** | **live** (+3 from 88) |
| **7차** | **Phase 8.1 + 8.2 + 8.2.2 (Cast 24/24 = 100%)** | **91** | **live** (±0 — 권고 #1-#5 누적 부채 반영) |

## 11. 사용 시나리오 — 인하우스 디자이너 워크플로우

### A: 새 Section type 추가 (C++ 1 파일)

```cpp
UCLASS(BlueprintType)
class UMCComboDamageSection : public UMCComboSection
{
    UPROPERTY() float DamageAmount = 10.0f;
    // 13 virtual default 사용 가능 — override 0
};
UCLASS(BlueprintType)
class UMCComboDamageTrack : public UMCComboTrack
{
    virtual TSubclassOf<UMCComboSection> SupportsSectionClass() const override
    {
        return UMCComboDamageSection::StaticClass();
    }
    // GetBindingScope default = SkeletalMesh
};
```

→ 빌드 후 Editor 자동 동작 (Phase 6e/6f).

### B: BP 디자이너 — Section 동작 정의 (Phase 7a)

`BP_MCComboDamageSection_Heavy`:
```
OnSectionBegin(Context)    → MyCharacter->StartHeavyAttack()
OnSectionProgress(Context, Alpha, DeltaTime) → if Alpha > 0.7 → SpawnSlashEffect(Alpha)
OnSectionEnd(Context)      → MyCharacter->ApplyDamage(DamageAmount * Weight)
```

### C: Asset-level Track 추가 (중복 허용 + auto-numbering, Phase 8.1)

```
Asset ⊕ → MCComboAudioTrack 클릭 (1st instance) → TrackName "Audio"
Asset ⊕ → MCComboAudioTrack 클릭 (2nd instance) → TrackName "Audio #2" ⭐ auto-suffix
각 instance Section 별 다른 SoundCue + PlayRate 설정
```

(Detail Panel 안 `bAlwaysSuffixFirst=true` 토글 시 첫 instance 부터 `Audio #1`)

### D: 새 type-specific runtime 처리 (Phase 8 Visitor, 엔지니어)

엔지니어가 `UMCComboCameraSection` 추가 시:
1. **Visitor 인터페이스 확장** (1 메서드 추가, runtime 모듈)
2. **Section 자손 override** (1 줄, Visit 호출)
3. **Collector 구현체** (Editor 측, 필요 시만)

→ PreviewSceneViewport 본체 무수정. 자세히 [[mc-combo-editor-phase-8-channel-iterator]] §11A.

## 12. 함정 매트릭스 (Phase 6-8 누적 13건)

> Phase 8 시리즈 신규 함정 4건 (Visitor-Cycle-01 / Visitor-Module-01 / Bitfield-PtrMember-01 / BP-Override-Mismatch-01) 은 [[mc-combo-editor-phase-8-channel-iterator]] §9 canonical.

| # | 함정 | Phase | 정답 |
| -- | -- | -- | -- |
| Abstraction-01 | DRY 위반 — `GetOutlinerSubRowCount` ↔ `AppendOutlinerSubProperties` 정합 자손 책임 | 6a-2 | docstring 명시 + 향후 non-virtual + spec 자동 계산 |
| Slate-Free-01 | 베이스 헤더 Slate 의존 회피 | 6a/6b/8 | `FText / FName / int32 / FFrameNumber` + `Misc/EnumClassFlags.h` 만. Visitor interface 도 forward declare 만 |
| Forward-Ref-01 | spec ParentIndex forward reference | 6a-2 | `!ParentToUse.IsValid() → ParentItem` 폴백 |
| Type-Specific-01 | Section 자손 entry 메뉴 표시 vs 베이스 생성 mismatch | 6f→6f-2 | `Track::AddSection(OverrideClass)` 시그니처 확장 |
| Cache-Lifecycle-01 | FGraphNodeClassHelper 캐시 ShutdownModule cleanup 누락 | 6e | `MCComboTrackClassCache.Reset()` |
| Scope-Filter-01 | Asset/Binding 메뉴 Track scope 무관 entry 등장 | 6g | 양방향 `CDO->GetBindingScope()` 필터 |
| ChannelName-Protocol-01 | "Location.X" magic string 네임스페이스 충돌 | 6b-2 | docstring 에 명명 규약 명시 |
| Jump-Section-01 | 시간 jump 통과 Section Begin+End 미호출 | 7a → 7a-2 | `[RangeLo, RangeHi]` 교차 검사 + Begin+End 동시 호출. **closed-closed fence-post 명시 의무**. |
| Visitor-Cycle-01 → §9 후속 | header inline 호출 시 IMCComboPreviewVisitor 완전 정의 의무 | 8 | cpp 분리 + `MCComboPreviewVisitor.h` include cpp 측 |
| Visitor-Module-01 → §9 후속 | Cast 분기 산재 → interface 통합 trade-off | 8 | 시나리오 D 의 비용 (3 곳) 정직 명시 |
| Bitfield-PtrMember-01 → §9 후속 | UPROPERTY bitfield pointer-to-member 불가 | 8 (권고 #1) | free function pointer 우회 |
| BP-Override-Mismatch-01 → §9 후속 | channel iterator 3 메서드 BP override 의미 불가 | 8.2.2 (권고 #4) | UFUNCTION 의도적 미부착 + docstring 근거 |

## 13. Engine 권위 인용 매트릭스

| Engine API | KMCProject 미러 | 사용처 |
| -- | -- | -- |
| `UAnimNotifyState::ReceivedNotifyBegin/Tick/End` | `UMCComboSection::OnSectionBegin/Progress/End` BIE | Phase 7a |
| `FGraphNodeClassHelper(UClass* RootClass)` | `MCComboTrackClassCache` + `MCComboSectionClassCache` | Phase 6e/6f |
| `FGraphNodeClassHelper::AddObservedBlueprintClasses` | 동일 호출 패턴 | Phase 6e/6f |
| `UMovieSceneTrack::EvaluateAtFrame` (개념) | `UMCComboTrack::EvaluateAtFrame` (시간 jump 통과 포함) | Phase 7a + 7a-2 |
| `UMovieSceneSection::IsFrameInSection` (의미) | `UMCComboSection::IsFrameInSection` | Phase 7a |
| `FAssetData / FToolMenuEntry` spec-as-data 패턴 | `FMCComboSubPropertySpec` USTRUCT | Phase 6a-2 |
| `FRichCurveKey + ERichCurveInterpMode` | `FMCComboFloatKey + EMCComboInterpMode` | Phase 6b-2 |
| `ENUM_CLASS_FLAGS` macro | `EMCComboRowButtonHints` | Phase 6a |
| **`IMovieScenePlayer` (MovieScene 모듈) — runtime interface + Editor 구현체 패턴** | **`IMCComboPreviewVisitor` + `FLoadAssetPreviewCollector`** | **Phase 8** |
| `UAnimMontage::GetDefaultBlendIn/OutTime` | `GetMontageBlendIn/OutFrames` | Phase 5o (이전 cycle) |
| **Pointer-to-member (C++ 표준)** | **`MCComboTransformChannelTable::Channels[].MemberPtr`** | **Phase 8 SSoT (권고 #1)** |
| **`FName` SSoT 패턴 (NameTable 인덱스)** | **`MCComboTransformChannelTable::Channels[].ChannelName`** | **Phase 8 SSoT (권고 #1)** |

## 14. 후속 Phase 권고

| Phase | 내용 | 우선순위 | ROI |
| -- | -- | -- | -- |
| **7b / 9.0** | `UMCComboPlayerComponent` (Actor Tick → Asset::EvaluateAtFrame chain) | **높음** | **실 런타임 검증 진입** |
| 9.1 | `UMCComboVectorSection` / `ColorSection` — Phase 8 SSoT 테이블 패턴 재사용 검증 | 중 | 새 channel type 추가 비용 실측 |
| ~~8.1~~ ✅ | ~~`UMCComboTrack::DisplayName` UPROPERTY 강화~~ → **완료** (Phase 8.1 + 권고 #3) | — | — |
| ~~8.2~~ ✅ | ~~잔존 2 Cast (drag/hit-test)~~ → **완료** (Phase 8.2 / 8.2.2 — 24/24 100%) | — | — |
| DRY 정리 | `GetOutlinerSubRowCount` non-virtual + spec 자동 계산 | 낮음 | Article 2 (SSoT) 강화 |
| 인자명 통일 | 베이스 `GlobalFrame` vs 자손 `InGlobalFrame` — UE 표준 `In` prefix | 낮음 | evaluator 권고 |
| synthesis split | 본 페이지 + Phase 8 후속 페이지 ([[mc-combo-editor-phase-8-channel-iterator]]) 패턴 — Phase 9+ 시 추가 분리 권고 | 중 | 페이지 분량 절제 (Article 8) |

## 15. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-20 (초안) | Phase 6a → 7a 12 단계 통합 case study 신규. Cast 16/24 = 67% 매트릭스. ue-evaluator 5회 평가. 시나리오 A/B/C. |
| 2026-05-20 (Phase 7a-2 + 8 + 6c-2.2 + 중복 정책 통합) | 16 단계 누적 확장. Cast -4 = 22/24 (92%). 함정 9번째 Visitor-Cycle-01. 시나리오 D. citation_disclosure 24→28. |
| 2026-05-20 (evaluator 권고 #1+#3+#4+#5 일괄 반영) | §7 fence-post 명시 (closed-closed interval). §12 함정 10번째 Visitor-Module-01 (모듈 경계 비용). §14 Phase 8.2 design sketch (`GetMutableChannelKeys`). §2 canonical 명시 + §4/§9 cross-reference 패턴 (Article 9 SSoT 강화). citation_disclosure 28 유지 (6차 evaluator 91/100 추가). |
| **2026-05-21 (Phase 8.1 / 8.2 / 8.2.2 + 7차 권고 #1-#5 반영)** | **§1 Thesis Cast 24/24 = 100% 갱신 + Asset auto-numbering 추가. §2 Phase 매트릭스 3행 추가 (8 / 8.1 / 8.2 / 8.2.2 / 중복 정책) — 누적 24. §3 데이터 모델 `bAlwaysSuffixFirst` + auto-suffix 표기. §4 virtual API 13+3 (channel iterator 3 + AppendSubRowPaintEntriesWithSectionRow 1 추가). §5 매트릭스 auto-suffix 식별 컬럼 추가. §8/§9 Phase 8 후속 페이지 ([[mc-combo-editor-phase-8-channel-iterator]]) cross-link. §10 7차 평가 91 LIVE 추가. §11C auto-suffix 시나리오. §12 함정 4건 후속 페이지 reference. §14 Phase 8.1/8.2 완료 strike-through. citation_disclosure 30.** |
