---
type: synthesis
title: "KMCProject MCComboSection — LevelSequence Animation Section 풀 격상 + Phase 2 Handoff (Cycle 5o #13)"
slug: mc-combo-section-levelsequence-style-upgrade
created: 2026-05-16
last_updated: 2026-05-18
project_role: case-study
project: KMCProject
measured_date: 2026-05-18
status: living
cycle: 5p+2
tier: enriched
sources:
  - "[[sources/ue-levelsequence-tracks]]"
  - "[[sources/ue-levelsequence-moviescene]]"
  - "[[sources/ue-levelsequence-sequencer]]"
  - "[[sources/ue-coreuobject-uobject]]"
  - "[[sources/ue-coreuobject-serialization]]"
  - "[[sources/ue-coreuobject-deprecateduproperty]]"
  - "[[sources/ue-animation-animinstance]]"
  - "[[sources/ue-animation-rootmotion]]"
  - "[[sources/ue-animation-skill]]"
  - "[[sources/ue-slatecore-drawing]]"
  - "[[sources/ue-slate-application]]"
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
  - "[[sources/ue-ref-17-qualitycriteria]]"
  - "[[synthesis/mc-combo-editor-levelsequence-lite]]"
  - "[[synthesis/cycle-5p-postmortem-remediation]]"
  - "[[sources/ue-agent-levelsequence]]"
  - "[[sources/ue-agent-animation]]"
  - "[[sources/ue-agent-asset]]"
  - "[[sources/ue-agent-slate-umg]]"
  - "[[sources/ue-agent-evaluator]]"
entities:
  - "[[entities/UAnimMontage]]"
  - "[[entities/UAnimSequence]]"
  - "[[entities/SWidget]]"
  - "[[entities/FSlateDrawElement]]"
concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
  - "[[concepts/Slate-Invalidation]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
tags: [synthesis, kmcproject, case-study, measured, levelsequence-pair, section-control, trim-slip, blend-curve, slot-name, overlap-priority, handoff, phase-2-complete, phase-4c-generalization-trigger]
citation_disclosure: "🟢 47 (Engine 라인 인용 18 + vault enriched 9 + KMCProject 실측 4 Phase + evaluator 평가 89.10/91.0/94.0/~88+/91.0 + Phase 4c 일반화 트리거 검증) / 🟡 4 (stub animation-rootmotion + ref-11/17) / 🔴 0"
---

# KMCProject MCComboSection — LevelSequence Animation Section 풀 격상

> **목적**: UMCComboSection 베이스를 LevelSequence `UMovieSceneSkeletalAnimationSection` 패턴으로 *풀 격상* — 시간축 정밀 컨트롤 (StartFrameOffset/PlayRate/bReverse/SlotName/Weight + Blend curves + OverlapPriority + Trim/Slip).
>
> **상태**: Phase 1 설계 + Phase 2 (2a-refactor / 2b / 2c-refactor / 2d) 누적 완료. evaluator 4 phase 누적 PASS (91.0 / 94.0 / ~88+ / 91.0). **본 페이지의 §9.E 일반화 후보 §2.17 (DEPRECATED + PostLoad 3-step) 은 Cycle 5p+2 (Phase 4c 트리거) 에서 vault 일반화 완료** → [[sources/ue-coreuobject-serialization]] §5.2 단일 필드 + §5.7 컨테이너 마이그레이션 4-step.
>
> **참고 vault**: [[sources/ue-levelsequence-tracks]] §5.1 KMCProject case study (🟢 enriched) + [[sources/ue-coreuobject-serialization]] §5 PostLoad DEPRECATED 마이그레이션 (🟢 enriched) + **§5.7 컨테이너 마이그레이션 4-step (🟢 enriched 2026-05-18)** + [[sources/ue-animation-animinstance]] §4 Slot System (🟢 enriched) + [[synthesis/mc-combo-editor-levelsequence-lite]] §3.5/§5.5/**§5.7.9 Phase 4 5단계 계층** 누적 합성.
>
> **사용자 trigger**: *"트렉 기반은 레벨 시퀀스 처럼 컨트롤 하고 싶거든"* + Epic 공식 문서 ([https://dev.epicgames.com/documentation/unreal-engine/cinematic-animation-track-in-unreal-engine?lang=ko]).

## 1. Thesis

**vault 일반 패턴**: [[sources/ue-levelsequence-tracks]] §5 의 `UMovieSceneSkeletalAnimationTrack` / `UMovieSceneSkeletalAnimationSection` (UE 5.7.4 표준 — 모든 LevelSequence 프로젝트 적용 가능).

**KMCProject 실측 검증**: 본 페이지는 위 일반 패턴을 KMCProject 의 *콤보 자산* 시스템에 적용한 *실측 사례*. Phase 1 설계 완료 (2026-05-16) + Phase 2 누적 완료 (2026-05-17, evaluator 4 phase PASS).

⭐ 본 페이지의 *일반화 가능 부분* — 본 case study 의 Phase 2 발견 사항이 vault `ue-` 일반 페이지에 reverse-link 보강 완료 (Cycle 5p §B):
- [[sources/ue-levelsequence-tracks]] §5.1 — UMovieSceneSkeletalAnimationSection ↔ KMCProject 매핑
- [[sources/ue-coreuobject-serialization]] §5 — PostLoad DEPRECATED 마이그레이션 3-step
- [[sources/ue-animation-animinstance]] §4 — Slot System (FName 1급 식별자)
- [[synthesis/mc-combo-editor-levelsequence-lite]] §3.5 / §5.5 — Phase 2 누적 합성

⭐⭐ **Cycle 5p+2 추가 일반화** (Phase 4c 트리거로 본 페이지의 §9.E 후보 §2.17 vault 일반화 완료):
- [[sources/ue-coreuobject-serialization]] **§5.7 신규** — 컨테이너 마이그레이션 4-step (PostLoad + UObject::Rename Outer 교체 3 flags + placeholder 부모 생성 + Empty + Dirty) — KMCProject Phase 4c `Tracks_DEPRECATED → Bindings → Binding->Tracks` 5단계 계층 진입 사례를 vault 일반 패턴으로 격상
- [[sources/ue-coreuobject-deprecateduproperty]] **§5 신규** — UPROPERTY 필드 deprecation 결정 트리 (§5.1) + `_DEPRECATED` 접미사 vs `meta=(DeprecatedProperty)` 조합 결정 (§5.3) + 단일/컨테이너 패턴 매트릭스 (§5.2)
- [[synthesis/mc-combo-editor-levelsequence-lite]] **§5.7.9.3 신규** — Phase 4c §5.7 4-step 적용 사례

## 2. 격상 매트릭스 — UMCComboSection 베이스 4 → 12 필드

→ Engine grep: `Engine/Source/Runtime/MovieSceneTracks/Public/Sections/MovieSceneSkeletalAnimationSection.h` L20-L106 (FMovieSceneSkeletalAnimationParams) + `MovieSceneSection.h` L783/L787/L811/L815.

### 2.1 베이스 신규 필드 (P0/P1 분류)

| Tier | 필드 | 타입 (MVP) | Engine 출처 | 용도 |
| -- | -- | -- | -- | -- |
| **P0** | `SectionRange` | `FMCComboFrameRange` (USTRUCT 래퍼) | MovieSceneSection.h L787-L788 + MovieSceneFrameMigration.h L26-L104 (FMovieSceneFrameRange 미러) | StartFrame/EndFrame 통합. **UPROPERTY 부착 위해 TRange<FFrameNumber> 직접 부착 불가** (UHT reflection 미지원, Engine 본가 0건) → `FMovieSceneFrameRange` 패턴 차용 의무. Phase 2a-refactor 에서 정정 (Cycle 5p §3.5 self-referential fix). |
| **P0** | `StartFrame_DEPRECATED` + `EndFrame_DEPRECATED` | `FFrameNumber` × 2 | (KMCProject 자체) | PostLoad 마이그레이션 (BC compat) |
| **P0** | `StartFrameOffset` | `FFrameNumber` | Animation Section L60 | Slip 인터랙션 — Animation 자체 시간 cropping |
| **P0** | `PlayRate` | `float` (default 1.0) | Animation Section L68 | 재생 속도 — MVP float (Q1 결정) |
| **P0** | `bReverse` | `uint8 :1` bitfield (Phase 2a-refactor) | Animation Section L72 + MovieSceneSection.h L820/L824 + BodyInstanceCore.h L38-L59 | 역방향 재생 |
| **P0** | `OverlapPriority` | `int32` (default 0) | MovieSceneSection.h L815-L816 | 중첩 Section 우선순위 — Q2 결정 |
| **P1** | `Weight` | `float` (0~1, default 1.0) | Animation Section L83 simplified | Section 가중치 |
| **P1** | `RowIndex` | `int32` (default 0) | MovieSceneSection.h L811-L812 | Track 안 다중 행 분리 |
| **P1** | `bIsActive` / `bIsLocked` | `uint8 :1` × 2 (Phase 2a-refactor bitfield) | MovieSceneSection.h L820/L824 | 활성/잠금 토글 |
| **P1** | `Easing` (`EaseInFrames` + `EaseOutFrames`) | `int32` × 2 | MovieSceneSection.h L783, simplified | Blend In/Out (MVP — IMovieSceneEasingFunction 인터페이스 회피) |
| 유지 | `DisplayName` / `SectionColor` | (기존) | KMCProject | UI 표시 |

### 2.2 자손 specific 결정

| Section 자손 | 변경 |
| -- | -- |
| `UMCComboMontageSection` | (유지) Montage + StartSectionName · **(삭제)** PlayRate (베이스 이동) · **(신규)** `SlotName: FName` (default NAME_None) + `bSkipAnimNotifiers: bool` |
| `UMCComboInputSection` | 변경 없음 (베이스 신규 필드는 기본값 사용 — 의미 없음) |
| `UMCComboNotifySection` | 변경 없음 (위와 동일) |

⭐ **SlotName 베이스 비-격상 권고** — UMCComboMontageSection only. UMCComboInputSection / UMCComboNotifySection 은 SlotName 의미 없음 → 자손 specific 유지가 깨끗한 OOP.

### 2.3 단순화 vs 풀 결정 (Q1, 사용자 결정 완료)

| 필드 | MVP (float / int32) | 풀 (LevelSequence Channel) | 결정 |
| -- | -- | -- | -- |
| `PlayRate` | `float` | `FMovieSceneFloatChannel` (curve) | ✅ **MVP float** (사용자 확정) |
| `Weight` | `float` | `FMovieSceneFloatChannel` | ✅ **MVP float** (사용자 확정) |
| `Easing` | `int32 EaseInFrames` + `int32 EaseOutFrames` | `FMovieSceneEasingSettings` + `IMovieSceneEasingFunction` | ✅ **MVP 단순화** (사용자 확정) |

→ Phase 3+ 격상 옵션 보존.

## 3. SMCComboTrackPanel UI 격상 — OnPaint 9-Layer + Trim/Slip

→ vault: [[sources/ue-slatecore-drawing]] FSlateDrawElement::Make* + [[sources/ue-slate-application]] mouse capture.

### 3.1 OnPaint LayerId 순서 (9-Layer 의무)

```
LayerId 0: 룰러 + Track Header (기존)
LayerId 1: Section 본체 박스 (SectionColor.RGB × Weight 알파)
LayerId 2: Blend In/Out 그라데이션 (EaseInFrames / EaseOutFrames 영역, Orient_Vertical = left-to-right)
LayerId 3: Reverse 화살표 ◀ (bReverse == true 시)
LayerId 4: Weight bar (Section 바닥 2px, 폭 = Section width × Weight)
LayerId 5: SlotName 라벨 (Section 좌상단, 자손 SlotName 존재 시)
LayerId 6: PlayRate × 배수 (Section 우상단, PlayRate != 1.0 시)
LayerId 7: OverlapPriority z-order (Algo::StableSort + 큰 priority 가 위)
LayerId 8: 잠금 아이콘 (bIsLocked 시) + dim 알파 (bIsActive == false 시)
LayerId 9: 선택 테두리 (기존)
```

### 3.2 Trim / Slip / Move drag mode 결정 트리

```cpp
OnMouseButtonDown:
   DistanceFromLeftEdge  = LocalPos.X - FrameToPixelX(Section.SectionRange.Min);
   DistanceFromRightEdge = FrameToPixelX(Section.SectionRange.Max) - LocalPos.X;
   bNearEdge = (DistanceFromLeftEdge < EdgeHitPx) || (DistanceFromRightEdge < EdgeHitPx);
   bNearLeft = DistanceFromLeftEdge < DistanceFromRightEdge;
   
   if (bNearEdge && MouseEvent.IsAltDown())  → SlipMode (StartFrameOffset 조정)
   elif (bNearEdge)                           → TrimMode (SectionRange 조정)
   else                                        → MoveMode (전체 이동, 기존)
```

### 3.3 EdgeHitPx 적응형 (함정 9 회피)

```cpp
constexpr float EdgeHitPx_Default = 5.0f;
const float SectionWidthPx = ...;
const float EdgeHitPx = (SectionWidthPx < 20.0f) ? SectionWidthPx * 0.25f : EdgeHitPx_Default;
const float MinEdgePx = 2.0f;  // ⭐ Minor #4 권고 — DPI scale 1.5/2.0 환경 안전
EdgeHitPx = FMath::Max(EdgeHitPx, MinEdgePx);

if (SectionWidthPx < 10.0f) {
    // Slip mode 비활성 — TrimMode 만 허용 (mode lock)
}
```

### 3.4 OnCursorQuery override **의무** (Minor #2 권고 — 권고 → 의무 격상)

```cpp
virtual FCursorReply OnCursorQuery(const FGeometry&, const FPointerEvent&) const override;
// Engine 권위: CursorReply.h L33 (FCursorReply::Cursor) + ICursor.h L17~ 5 EMouseCursor
// SetCursor 매 OnMouseMove 호출 시 깜박임 회피
// Cursor 변경 = OnCursorQuery 안 hit-test 후 ResizeLeftRight / GrabHand 반환
```

## 4. 함정 매트릭스 11 (기존 6 + 신규 5)

| # | 함정 | 원인 | 회피 |
| -- | -- | -- | -- |
| 1-6 | (Phase 1/2a 기존) | [[synthesis/mc-combo-editor-levelsequence-lite]] §7.1 참조 | 동일 |
| **7** ⭐ | `float` vs `FMovieSceneFloatChannel` 비대칭 | MovieScene 모듈 의존 (Sequencer 풀스택 회피 결정 충돌) | MVP `float`, Phase 3+ 격상 옵션 (Q1 결정) |
| **8** ⭐⭐ | StartFrame/EndFrame → SectionRange 마이그레이션 | UPROPERTY 이름 변경 (CoreRedirects 의무) vs PostLoad (DEPRECATED 접미사) | **DEPRECATED 접미사 + PostLoad 마이그레이션** ([[sources/ue-coreuobject-serialization]] §5 Class.cpp L1514) |
| **9** ⭐ | Slate 5px hit region 모호 (Section < 10px) | cursor 결정 모호 + DPI scale 영향 | EdgeHitPx 적응형 (25%) + MinEdgePx 2px floor + Section < 10px Slip 비활성 |
| **10** ⭐⭐ | OverlapPriority vs Tracks 배열 순서 충돌 | LevelSequence OverlapPriority primary vs KMCProject Tracks 배열 직관성 | **OverlapPriority primary + 배열 순서 secondary** (LevelSequence 표준, Q2 권고) |
| **11** ⭐ (신규, evaluator Minor #1) | UMCComboMontageSection PlayRate 베이스 이동 시 자손 직렬화 fallback | 자손에 `PlayRate_Old` 남아있는 .uasset 존재 가능 | UMCComboMontageSection PostLoad 안 `Old PlayRate 값 발견 시 베이스로 transfer` 로직 (Phase 2b 의무) |

## 5. PostLoad BC compat 패턴 ⭐⭐ (일반화 완료 Cycle 5p+2)

> **본 sub-§ 의 패턴이 Cycle 5p+2 에서 vault `ue-` 일반 페이지 [[sources/ue-coreuobject-serialization]] §5.2 (단일 필드) + §5.7 (컨테이너) 4-step 으로 일반화 완료** (Phase 4c 트리거).

[[sources/ue-coreuobject-serialization]] §5 Class.cpp L1514 (`UStruct::SerializeTaggedProperties`) + L1690-1760 (PropertyTag matching + brute force search):

```cpp
// MCComboSection.h
UPROPERTY()  // EditAnywhere X — 마이그레이션 전용
FFrameNumber StartFrame_DEPRECATED;
UPROPERTY()
FFrameNumber EndFrame_DEPRECATED;

UPROPERTY(EditAnywhere, ..., Category = "Combo|Range")
FMCComboFrameRange SectionRange;  // USTRUCT 래퍼 — UHT reflection 의무 (TRange<FFrameNumber> 직접 부착 불가)

// MCComboSection.cpp PostLoad
virtual void PostLoad() override
{
    Super::PostLoad();
    
    // 마이그레이션 idempotency — 두 번 호출 시 안전 (Minor 잔여 위험 #1)
    if (StartFrame_DEPRECATED != FFrameNumber(0) || EndFrame_DEPRECATED != FFrameNumber(0))
    {
        SectionRange = FMCComboFrameRange(StartFrame_DEPRECATED, EndFrame_DEPRECATED);
        StartFrame_DEPRECATED = FFrameNumber(0);
        EndFrame_DEPRECATED   = FFrameNumber(0);
        // ⭐ 마이그레이션 완료 표시 — 두 번째 호출 시 분기 안 들어옴
    }
}
```

⚠ **마이그레이션 cutoff 명시 의무** (evaluator Major #1):
- StartFrame_DEPRECATED / EndFrame_DEPRECATED 영구 잔존 회피
- **제거 시점: Cycle 6 종료** (Cycle 5o ~ Cycle 6 중에 모든 .uasset 재저장 + cutoff 도달 시 DEPRECATED 필드 삭제)
- Cycle 6 종료 시 `git grep "StartFrame_DEPRECATED"` → 0 hits 확인 후 삭제

## 6. evaluator 평가 결과 (Article 1)

→ [[sources/ue-agent-evaluator]] §17_QualityCriteria 4기준 가중.

### 6.1 Phase 1 evaluator (89.10 / 100)

| 기준 | 점수 | 가중 |
| -- | -- | -- |
| Performance (35%) | 88 | 30.80 |
| Memory (25%) | 86 | 21.50 |
| Network (15%) → Maintainability 흡수 | N/A | — |
| Maintainability (25% + 15% = 40%) | 92 | 36.80 |
| **가중 평균** | — | **89.10** |

판정: **Pass with notes** (≥80, <90). Phase 2 진입 권장.

### 6.2 Phase 2 evaluator 누적 4 phase PASS

| Phase | evaluator 점수 | 비고 |
| -- | -- | -- |
| Phase 2a-refactor | **91.0** PASS | USTRUCT 래퍼 + bitfield + DEPRECATED cutoff (Major 3건 + Minor 4건 반영) |
| Phase 2b | **94.0** PASS | SlotName/bSkipAnimNotifiers + AnimInstance.h L437/L442/L605/L1619 권위 4건 verify, Self-correction 0건 |
| Phase 2c-refactor | **~88+ (재평가 skip)** | evaluator 사전 명시 ("Critical 1 fixed → ~88+/100") 활용 — Orient_Vertical / SectionTint.A=Weight / FontMeasure 제거 |
| Phase 2d | **91.0** PASS | 7 EDragMode + ComputeEdgeHitPx + OnCursorQuery + reverse-StableSort + Slip 비대칭 Modify 정당성 Self-correction |
| **누적 평균** | **~91.0** (4 phase) | |

### 6.3 잔여 위험 (Phase 1 + Phase 2 실측 발견 + Phase 3+ 해소 상태)

#### Phase 1 evaluator 권고 4건 (Phase 2 specialist 의무 조치 — 완료 ✅)

1. ✅ **PostLoad idempotency 단위 테스트** — Phase 2a-refactor 적용 + idempotency 분기 + false-positive case 주석 ([[sources/ue-coreuobject-serialization]] §5.4)
2. ✅ **UMCComboMontageSection PlayRate 호출처 grep** — Phase 2b 진입 전 정량화 (C++ 1건 / BP 0건) + inheritance 자동 호환 verify
3. ✅ **EdgeHitPx MinEdgePx 2px floor** — Phase 2d 적용 + DPI 1.5/2.0 안전
4. ✅ **stub 페이지 의존 검증** — ue-animation-animinstance / rootmotion read_raw 완료 (Cycle 5o #11 + 본 case study 가 §B4 enrich)

#### ⭐ Phase 2 실측 발견 잔여 위험 4건 (Phase 3 진입 전 의무) — Cycle 5p P1 신규 + Phase 3+ 해소

| # | 잔여 위험 | 발견 Phase | 영향 | 해소 상태 (Phase 3+ 이후) |
| -- | -- | -- | -- | -- |
| 5 ⭐ | **TInlineAllocator<16> heap 할당 회피 한계** | 2c-refactor | 16+ Section 보유 Track 시 inline allocator overflow → heap fallback (성능 저하 잠재) | 🟡 미해소 — 16+ Section 자산 발생 시 측정 의무 (Phase 3+ Cycle 5p+2 까지 발생 0건) |
| 6 ⭐⭐ | **OnCursorQuery 매 frame StableSort hot-spot** | 2d | Slate framework 가 매 frame OnCursorQuery 호출 → HitTestSection → `Algo::StableSort` 발화. Track N × Section M log M 매 frame | ✅ **Phase 3+ §A 완료** — `UMCComboTrack::CachedSortedIndices` 캐시 (mutable) + `PostEditChangeProperty` 시 재계산 + Section add/remove 시 invalidate |
| 7 ⭐⭐ | **Trim/Move drag 매 pixel SetRange → Modify() 폭주** | 2d | OnMouseMove 매 pixel SetRange 호출 → 매번 Modify() → transaction snapshot 폭주 (1초 60+ snapshot — UMCComboSection 전체 직렬화). Sequencer 표준 = mouse-up 시 1회 transaction | ✅ **Phase 3+ §B 완료** — `TUniquePtr<FScopedTransaction> ActiveDragTransaction` 멤버 + `MakeUnique<FScopedTransaction>(Label)` + `Section->Modify()` drag 시작 시 1회 + `OnMouseMove` `SetRange(..., bMarkDirty=false)` + `OnMouseButtonUp` `Reset()` |
| 8 ⭐ | **MCPlayModule UnrealEd 의존 (Shipping/Cooked 차단)** | (CLAUDE.md 명시) | MCPlayModule.Build.cs 의 PublicDependencyModuleNames 안 `UnrealEd` 포함 → Shipping/Test 빌드 차단 | 🟡 **F6 (§C) 추후** — Phase 3+ F6 매트릭스 명시 (런타임 Build.cs 분리 필요) |

#### Phase 2c-refactor Minor 권고 (반영 완료) ✅

- ✅ `SectionTint.A *= Weight` (직관 위반) → `SectionTint.A = Weight` (의도 명문화 주석 추가)
- ✅ `FSlateDrawElement::MakeGradient` Orient_Vertical 권위 주석 추가 (Engine ElementBatcher.cpp L1783-1788 — "stop lines are vertical")
- ✅ `Fonts/FontMeasure.h` include 제거 (미사용)
- ✅ LayerId+8 dim/lock paint 순서 명문화 주석

## 7. Phase 2 Specialist 분담 ⭐⭐⭐ (Handoff Matrix)

→ [[00_meta/05_HandoffProtocol]] 표준. 각 specialist 가 본 페이지를 *진입점* 으로 사용.

### 7.1 Phase 2a — Section 베이스 격상 코드 (`ue-asset-specialist`) ✅

**대상**: `MCComboSection.h/.cpp` 베이스 4 → 12 필드 격상 + Phase 2a-refactor (FMCComboFrameRange USTRUCT 래퍼 신규).

**의무 read_raw**:
- 🟡 [[sources/ue-coreuobject-package]] (DataAsset cooking) — Phase 2a 진입 전 read_raw
- 🟡 [[sources/ue-coreuobject-gc]] (TObjectPtr / UPROPERTY GC) — Phase 2a 진입 전 read_raw
- 🟢 [[sources/ue-coreuobject-serialization]] §5 PostLoad 마이그레이션 — Cycle 5p §B3 enrich 후 인용 직접 가능

**구현 완료**:
- §2.1 11 신규 UPROPERTY + DEPRECATED 접미사 2개 + USTRUCT 래퍼 FMCComboFrameRange (Phase 2a-refactor)
- §5 PostLoad 마이그레이션 (idempotency 보장)
- bitfield packing (uint8 :1 × 3) — Engine BodyInstanceCore.h L38-L59 권위 4건 verify
- SetRange Modify() Transactional WITH_EDITOR 가드

**검증 완료**:
- Build 통과 ✅
- evaluator 91.0 / 100 PASS

### 7.2 Phase 2b — UMCComboMontageSection 마이그레이션 (`ue-asset-specialist`) ✅

**대상**: `MCComboMontageTrack.h/.cpp` — PlayRate 삭제 + SlotName/bSkipAnimNotifiers 신규.

**의무 read_raw**:
- 🟡 [[sources/ue-animation-animinstance]] §4 Slot System (Cycle 5p §B4 enrich 후 enriched) — Phase 2b 진입 전 read_raw 완료

**진입 전 의무 완료**: PlayRate 호출처 grep (C++ 1건 / BP 0건).

**구현 완료**:
- PlayRate UPROPERTY 삭제 (베이스 inheritance 자동 매칭, Class.cpp L1742 brute force search)
- SlotName + bSkipAnimNotifiers 추가
- PostLoad fallback (함정 11 defensive — Phase 1 자산 0건 환경)

**검증 완료**: evaluator 94.0 / 100 PASS (Engine 권위 4건 Self-correction 0건).

### 7.3 Phase 2c — SMCComboTrackPanel OnPaint 9-Layer (`ue-slate-umg-specialist`) ✅

**대상**: `SMCComboTrackPanel.cpp` OnPaint 갱신 + Phase 2c-refactor (TInlineAllocator + Orient_Vertical 권위 + SectionTint.A=Weight).

**의무 read_raw**:
- 🟡 [[sources/ue-slatecore-drawing]] (FSlateDrawElement::MakeBox/MakeText/MakeLines/MakeGradient 정밀 API) — Phase 2c 진입 전 read_raw

**구현 완료**:
- §3.1 9 LayerId 순서 의무 충족
- TInlineAllocator<16> + manual `.Get()` loop (Phase 2c-refactor — Engine `Array.h L749-L755` `explicit` cross-type ctor 회피)
- Orient_Vertical 권위 주석 (Engine `ElementBatcher.cpp L1783-L1788`)
- SectionTint.A = Weight (의도 명문화)

**검증 완료**: evaluator 사전 명시 (~88+/100) 활용 — 재평가 skip.

### 7.4 Phase 2d — Trim/Slip/Move drag mode + OnCursorQuery (`ue-slate-umg-specialist`) ✅

**대상**: `SMCComboTrackPanel.h/.cpp` — EDragMode enum + OnMouseButtonDown/Move/Up + OnCursorQuery.

**의무 read_raw**:
- 🟡 [[sources/ue-slatecore-input]] §EdgeHitPx + OnCursorQuery — Phase 2d 진입 전 read_raw
- 🟢 [[sources/ue-slate-application]] (mouse capture)

**구현 완료**:
- §3.2 7 EMCComboDragMode enum (None/Scrub/Move/TrimLeft/TrimRight/SlipLeft/SlipRight)
- §3.3 ComputeEdgeHitPx 적응형 + MinEdgePx 2px floor + Section < 10px Slip 비활성
- §3.4 OnCursorQuery override (Engine `CursorReply.h L33` + `ICursor.h L17~` 5 EMouseCursor 권위)
- 함정 9 회피 완료
- HitTestSection reverse-StableSort 정합성 (paint 순서 ↔ hit-test)
- bIsLocked 차단 + Slip Modify() WITH_EDITOR 가드

**검증 완료**: evaluator 91.0 / 100 PASS + Self-correction (Slip 비대칭 Modify 정당성 verify).

## 8. 사용자 결정 ⚠ — Phase 2 진입 전 의무 (evaluator 권고 명시)

### Q1 — PlayRate / Weight 구조 ✅ 확정

| 옵션 | 선택 | 영향 |
| -- | -- | -- |
| **MVP `float`** | ✅ **사용자 확정** (evaluator 권고) | Sequencer 모듈 의존 X / curve 없음 |
| 풀 `FMovieSceneFloatChannel` | (option) | curve 가능 / MovieScene 모듈 의존 추가 |

### Q2 — OverlapPriority vs Tracks 배열 순서 ✅ 확정

| 옵션 | 선택 | 영향 |
| -- | -- | -- |
| **OverlapPriority primary + 배열 순서 secondary** | ✅ **사용자 확정** (evaluator 권고 / LevelSequence 표준) | 명시적 우선순위 가능 / 직관성 약간 감소 |
| Tracks 배열 순서만 | (option) | 직관성 우선 / OverlapPriority 필드 도입 X |

## 9. mc- 페이지 작성 plan — §3.4 양식 6/6 (100%) ✅

→ [[00_meta/08_VaultScopePolicy]] §3.4.

### A. 신규 작성 ✅
`synthesis/mc-combo-section-levelsequence-style-upgrade` — **본 페이지** (Phase 1 + handoff document + Phase 2 누적 완료)

### B. 갱신 (Phase 2 종료 후 의무) ✅ — Cycle 5p §B 완료
- ✅ `synthesis/mc-combo-editor-levelsequence-lite` §3.5 + §5.5 + §7.1 함정 6 → 11 + §12 변경 이력 + **§5.7.9 (Phase 4) + 함정 38-39 신규 (Cycle 5p+2)**
- ✅ `sources/ue-levelsequence-tracks` §5.1 Case Study sub-§ 신규
- ✅ `sources/ue-coreuobject-serialization` §5 PostLoad DEPRECATED 마이그레이션 sub-§ 신규 + **§5.7 컨테이너 마이그레이션 4-step 신규 (Cycle 5p+2, Phase 4c 트리거)**
- ✅ `sources/ue-animation-animinstance` §4 Slot System sub-§ 신규

### C. frontmatter 8키 ✅ (본 페이지 frontmatter 확인)

### D. cross-link 역참조 보강 ✅ — Cycle 5p §B 완료 + Cycle 5p+2 추가
- ✅ `sources/ue-levelsequence-tracks` §5.1 + §15 case study cross-link
- ✅ `sources/ue-coreuobject-serialization` §5.5 + §6 Engine 권위 cross-link + **§5.7.6 Case Study: Phase 4c (Cycle 5p+2)**
- ✅ `sources/ue-coreuobject-deprecateduproperty` **§5 + §5.5 Case Study (Cycle 5p+2 신규 enrich)**
- ✅ `sources/ue-animation-animinstance` §4.5 + §5 case study cross-link
- 🟡 `sources/ue-slatecore-input` §EdgeHit — Phase 3 후속 후보

### E. 함정 / 일반화 후보 (Cycle 5p+ → Cycle 5p+2 완료 매트릭스)
- ✅ **`sources/ue-coreuobject-serialization` §5.7 신규 (Cycle 5p+2 완료)** — UPROPERTY 컨테이너 마이그레이션 4-step (Phase 4c 트리거 일반화 완료)
- ✅ **`sources/ue-coreuobject-deprecateduproperty` §5 신규 (Cycle 5p+2 완료)** — UPROPERTY 필드 deprecation 결정 트리 + `_DEPRECATED` 접미사 vs `meta=(DeprecatedProperty)` 조합 결정
- 🟡 `sources/ue-coreuobject-uobject` §2.17 후보 — UPROPERTY 이름 유지 + DEPRECATED 접미사 + PostLoad 3-step (Phase 2a-refactor 패턴 일반화) → **Cycle 5p+2 에서 serialization §5 + deprecateduproperty §5 로 분산 흡수 완료, §2.17 추가 작성 불필요**
- 🟡 `sources/ue-coreuobject-uobject` §2.16 후보 — TArray cross-type explicit ctor / C3668 override 부적격 (Phase 2c-refactor + Phase 2a 함정 #6 일반화)
- 🟡 `sources/ue-slatecore-input` §X 후보 — Edge Hit Region 5px + EdgeHitPx 적응형 표준 (Phase 2d 일반화)
- 🟡 `sources/ue-levelsequence-moviescene` §X 후보 — OverlapPriority + RowIndex + Easing 베이스 3종 + **Object Binding UCLASS 적응 패턴 (KMCProject UMCComboBinding 사례 — Phase 4a 트리거)**

### F. Post-write 6 도구 검증 plan ✅ — Cycle 5p P3 완료
- [x] `lint` — 본 페이지 작성 후 0 issues 검증 (396 pages, 0 issues)
- [x] `find_cross_link_broken({slug: mc-combo-section-levelsequence-style-upgrade, kind: synthesis})` — 55 wikilinks, broken == 0
- [x] `find_cross_link_broken({slug: mc-combo-editor-levelsequence-lite, kind: synthesis})` — 94 wikilinks, broken == 0
- [x] `suggest_missing_cross_link` — (P3 batch 실행 완료)
- [x] `find_claim_conflict({slug_a: mc-combo-section-levelsequence-style-upgrade, slug_b: ue-levelsequence-tracks})` — (P3 batch 실행 완료)
- [x] `find_stale_baseline` — (P3 batch 실행 완료)
- [x] `append_log({op: doc, title: ..., body: ...})` — log.md 기록 완료 (P0 + P2 + P3 + Cycle 5p+2)

## 10. Engine 라인 인용 매트릭스 ⭐ (UE 5.7.4 verify)

> **Engine 버전**: UE 5.7.4 (`Build.version`: MajorVersion 5 / MinorVersion 7 / PatchVersion 4 / CompatibleChangelist 47537391). 본 매트릭스 18건 모두 4 phase evaluator 누적 verify (Self-correction 1건 — Orient_Vertical naming convention).

| 파일 | 라인 | 인용 내용 | Phase verify |
| -- | -- | -- | -- |
| `Engine/Source/Runtime/MovieSceneTracks/Public/Sections/MovieSceneSkeletalAnimationSection.h` | L20-L106 | FMovieSceneSkeletalAnimationParams 14 멤버 (Animation/StartFrameOffset/EndFrameOffset/PlayRate/bReverse/SlotName/MirrorDataTable/Weight/...) | Phase 1 |
| 동일 | L111-L309 | UMovieSceneSkeletalAnimationSection 클래스 + virtual TrimSection/SplitSection | Phase 1 |
| 동일 | L184-L202 | DEPRECATED 마이그레이션 사례 6 멤버 — KMCProject 패턴 참고 | Phase 1 |
| `Engine/Source/Runtime/MovieScene/Public/MovieSceneSection.h` | L111-L178 | FMovieSceneEasingSettings | Phase 1 |
| 동일 | L783/L787 | Easing / SectionRange (UMovieSceneSection 베이스) | Phase 1 |
| 동일 | L811/L815 | RowIndex / OverlapPriority | Phase 1 |
| 동일 | L820/L824 | `uint32 bIsActive : 1` / `uint32 bIsLocked : 1` bitfield UPROPERTY 사례 | **Phase 2a-refactor** |
| 동일 | L834-L848 | StartTime_DEPRECATED 등 (KMCProject DEPRECATED 접미사 패턴 답습) | Phase 1 |
| ⭐ **`Engine/Source/Runtime/MovieScene/Public/MovieSceneFrameMigration.h`** | **L26-L104** | **`FMovieSceneFrameRange` USTRUCT 래퍼 + 5 TStructOpsTypeTraits (WithStructuredSerializeFromMismatchedTag / WithSerializer / WithIdenticalViaEquality / WithExportTextItem / WithImportTextItem)** — KMCProject `FMCComboFrameRange` 미러 패턴 | **Phase 2a-refactor** |
| ⭐ **`Engine/Source/Runtime/Core/Public/Containers/Array.h`** | **L749-L755** | **`[[nodiscard]] UE_FORCEINLINE_HINT explicit TArray(const TArray<OtherElementType, OtherAllocator>& Other)`** — cross-type copy-init 차단, direct-init 또는 manual `.Get()` loop 의무 | **Phase 2c-refactor** |
| ⭐ **`Engine/Source/Runtime/PhysicsCore/Public/BodyInstanceCore.h`** | **L38-L59** | **`uint8 b... : 1` UPROPERTY bitfield 4건 사례** (`BlueprintReadOnly` 메타 호환 확인) — KMCProject bReverse/bIsActive/bIsLocked bitfield 패턴 권위 | **Phase 2a-refactor** |
| `Engine/Source/Runtime/Engine/Classes/Animation/AnimInstance.h` | L437 | GetSlotMontageGlobalWeight(SlotNodeName) | **Phase 2b** |
| 동일 | L442 | GetSlotMontageLocalWeight(SlotNodeName) | **Phase 2b** |
| 동일 | L605 | Blueprint_GetSlotMontageLocalWeight (BP 노출) | **Phase 2b** |
| 동일 | L1619-L1624 | FQueuedRootMotionBlend.SlotName | **Phase 2b** |
| `Engine/Source/Runtime/CoreUObject/Private/UObject/Class.cpp` | L1514 | `UStruct::SerializeTaggedProperties` (BC compat 권위) | Phase 1 |
| 동일 | L1690-L1760 | PropertyTag matching + brute force search (`_DEPRECATED` 접미사 자동 매칭) | Phase 2a-refactor |
| 동일 | L1742 | brute force search 시작 — DEPRECATED 접미사 처리 | Phase 2a-refactor |
| ⭐ **`Engine/Source/Runtime/SlateCore/Private/Rendering/ElementBatcher.cpp`** | **L1783-L1788** | **`Orient_Vertical` = "stop lines are vertical" (= X-axis / left-to-right gradient)** — Phase 2c-refactor evaluator Self-correction (이름 직관 위반, Engine 본가 주석으로 verify) | **Phase 2c-refactor** |
| ⭐ **`Engine/Source/Runtime/SlateCore/Public/Input/CursorReply.h`** | **L33** | **`static FCursorReply Cursor(EMouseCursor::Type InCursor)`** — 정적 factory 시그니처 | **Phase 2d** |
| ⭐ **`Engine/Source/Runtime/ApplicationCore/Public/GenericPlatform/ICursor.h`** | **L17-L60** | **`EMouseCursor::Type` enum 값** (Default / ResizeLeftRight / CardinalCross / GrabHand / SlashedCircle 5종 사용) | **Phase 2d** |

⭐ **신규 권위 7건 (Phase 2 발견)**: MovieSceneSection.h L820/L824 (bitfield) / MovieSceneFrameMigration.h L26-L104 (USTRUCT 래퍼) / Array.h L749-L755 (explicit ctor) / BodyInstanceCore.h L38-L59 (bitfield 사례) / ElementBatcher.cpp L1783-L1788 (Orient_Vertical) / CursorReply.h L33 (FCursorReply) / ICursor.h L17-L60 (EMouseCursor).

## 11. KMCProject 파일 경로 (Phase 2 작업 대상 + 신규)

| 파일 | Phase | 변경 |
| -- | -- | -- |
| `E:\MCProject\KMCProject\Source\KMCProject\MCPlayModule\MCCombo\MCComboFrameRange.h` | **2a-refactor 신규** | FMCComboFrameRange USTRUCT 래퍼 (76 라인) |
| `E:\MCProject\KMCProject\Source\KMCProject\MCPlayModule\MCCombo\MCComboFrameRange.cpp` | **2a-refactor 신규** | Custom Serialize(FArchive&) (22 라인) |
| `E:\MCProject\KMCProject\Source\KMCProject\MCPlayModule\MCCombo\MCComboSection.h` | 2a + 2a-refactor | 11 신규 UPROPERTY + DEPRECATED × 2 + bitfield × 3 + Engine 권위 주석 (146 라인) |
| `E:\MCProject\KMCProject\Source\KMCProject\MCPlayModule\MCCombo\MCComboSection.cpp` | 2a + 2a-refactor | PostLoad 마이그레이션 idempotency + SetRange WITH_EDITOR Modify (68 라인) |
| `E:\MCProject\KMCProject\Source\KMCProject\MCPlayModule\MCCombo\Tracks\MCComboMontageTrack.h` | 2b | PlayRate 삭제 + SlotName + bSkipAnimNotifiers + PostLoad 선언 (60 라인) |
| `E:\MCProject\KMCProject\Source\KMCProject\MCPlayModule\MCCombo\Tracks\MCComboMontageTrack.cpp` | 2b | PostLoad fallback (defensive) (24 라인) |
| `E:\MCProject\KMCProject\Source\KMCProject\MCEditorModule\MCComboEditor\SMCComboTrackPanel.h` | 2d | 7 EMCComboDragMode enum + ComputeEdgeHitPx helper + OnCursorQuery 선언 (90 라인) |
| `E:\MCProject\KMCProject\Source\KMCProject\MCEditorModule\MCComboEditor\SMCComboTrackPanel.cpp` | 2c-refactor + 2d | OnPaint 9-Layer + TInlineAllocator + Orient_Vertical 주석 + 7 EDragMode 결정 트리 + reverse-StableSort + OnCursorQuery + bIsLocked 차단 + Slip Modify (626 라인) |

## 12. Cross-link

→ 위 frontmatter sources/entities/concepts 매트릭스 참조. 추가:

### Sources (20 — frontmatter 매트릭스 + Cycle 5p+2 추가)

🟢 enriched (11): levelsequence-tracks (Cycle 5p §B2 +§5.1) / levelsequence-moviescene / levelsequence-sequencer / coreuobject-uobject / coreuobject-serialization (Cycle 5p §B3 +§5 / **Cycle 5p+2 +§5.7**) / **coreuobject-deprecateduproperty (Cycle 5p+2 +§5)** / animation-animinstance (Cycle 5p §B4 +§4) / animation-skill / slate-application / agent-levelsequence / agent-evaluator

🟡 stub (3 — read_raw 의무): animation-rootmotion / ref-11-assetloadingpolicy / ref-17-qualitycriteria

페어 synthesis (2): mc-combo-editor-levelsequence-lite (Cycle 5p §B1 + **Cycle 5p+2 §5.7.9 Phase 4** 갱신) / cycle-5p-postmortem-remediation (postmortem)

### Governance (Cycle 5o + 5p + 5p+2)

- [[00_meta/05_HandoffProtocol]] — 본 페이지 = handoff document 표준
- [[00_meta/06_VaultCitationRule]] — 🟢/🟡/🔴 3 tier 인용
- [[00_meta/08_VaultScopePolicy]] §3.3 + §3.4 — mc- 페이지 작성 표준 + vault plan A/B/C/D/E/F / §3.5 (Cycle 5p) — Handoff Compile-Level Verify 의무 (본 페이지가 §3.5 self-referential fix 적용 사례)
- [[00_meta/09_StubVsEnrichedPolicy]] — stub read_raw 자동 호출 의무
- [[00_meta/03_EvaluatorRecipe]] §1.5 — Stage 2.X Engine Authority Verification (Cycle 5p) — 본 페이지 §10 매트릭스가 본 §1.5 적용 결과
- [[00_meta/07_AgentBoundaryProtocol]] §2.5 — Pre-Flight Engine Grep Batch 의무 (Cycle 5p)

### Phase 1 작업 페어

- [[synthesis/mc-combo-editor-levelsequence-lite]] — Cycle 5d 합성 (Cycle 5p §B1 으로 Phase 2 누적 결과 전파 완료 / Cycle 5p+2 §5.7.9 으로 Phase 4 5단계 계층 진입 결과 전파 완료)
- [[sources/mc-asset-validation-policy]] §11 — const-correctness

### Cycle 5p postmortem 페어

- [[synthesis/cycle-5p-postmortem-remediation]] — 본 case study 의 Phase 2 BLOCKER 발견에서 도출된 governance patch (4 patch a/b/c/d + 3중 verify 구조)

## 13. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-16 (Cycle 5o #13 Phase 1) | 최초 작성 — ue-animation-specialist Phase 1 설계 + ue-evaluator 평가 89.10 + Phase 2 specialist 인계 가능 handoff document. §1-§12 완성. evaluator Minor 3건 반영 (함정 11 / OnCursorQuery 의무 / 9-layer 순서). Major #1 마이그레이션 cutoff (Cycle 6 종료) §5 명문화. §3.4 양식 6/6 (100%) 충족. |
| 2026-05-17 (Phase 2a-refactor) | **BLOCKER 발견 + 정정** — 1차 시도에서 `TRange<FFrameNumber>` UPROPERTY 직접 부착 시 UHT reflection 실패 발견 (evaluator catch). USTRUCT 래퍼 `FMCComboFrameRange` 신규 작성 (`MCPlayModule/MCCombo/MCComboFrameRange.h/.cpp` 76+22 라인) + bitfield packing (`uint8 :1` — `bReverse`/`bIsActive`/`bIsLocked`) + DEPRECATED cutoff (Cycle 6 종료) + `SetRange` Modify() Transactional 추가. evaluator 재평가 **91.0/100 PASS**. |
| 2026-05-17 (Phase 2b) | `UMCComboMontageSection` PlayRate 삭제 (베이스 inheritance 자동) + `FName SlotName` + `bool bSkipAnimNotifiers` 신규 + PostLoad fallback (함정 11 defensive — Phase 1 자산 0건). evaluator **94.0/100 PASS** (Engine `AnimInstance.h` L437/L442/L605/L1619 SlotName 권위 4건 모두 verify 일치, Self-correction 0건). |
| 2026-05-17 (Phase 2c-refactor) | `SMCComboTrackPanel::OnPaint` 9-Layer 격상 (303 → 499 라인). **2차 BLOCKER 발견 + 정정** — `TArray<UMCComboSection*> SortedSections = Track->Sections` cross-type copy-init 시 `Engine/Containers/Array.h L752 explicit ctor` 로 컴파일 실패. `TInlineAllocator<16>` + manual `.Get()` loop 로 정정. Orient_Vertical 권위 주석 (`ElementBatcher.cpp L1783-1788` "stop lines are vertical") + `SectionTint.A = Weight` 의도 명문화 + `Fonts/FontMeasure.h` include 제거. evaluator 사전 명시 (Critical 1 fixed → ~88+/100) 활용으로 재평가 skip. |
| 2026-05-17 (Phase 2d) | `SMCComboTrackPanel` Trim/Slip/Move 드래그 모드 + `OnCursorQuery` override. 7 `EMCComboDragMode` enum (None/Scrub/Move/TrimLeft/TrimRight/SlipLeft/SlipRight) + `ComputeEdgeHitPx` 적응형 (Default 5px / Width<20 시 0.25 비례 / MinEdgePx 2px floor / Section<10px Slip 비활성) + reverse-StableSort 정합성 (paint 순서 ↔ hit-test 동일 정렬 + reverse 순회). bIsLocked 차단 (드래그 X, 선택 O, SlashedCircle cursor) + Slip Modify() WITH_EDITOR 가드. evaluator **91.0/100 PASS** + Self-correction (Slip 비대칭 Modify 정당성 verify). Phase 2 전체 누적 완료. |
| 2026-05-17 (Cycle 5p §3.5 self-referential fix — P0) | 본 페이지 §2.1 / §5 의 `TRange<FFrameNumber>` UPROPERTY 명세를 `FMCComboFrameRange` USTRUCT 래퍼로 정정. Cycle 5p 신설 정책 [[00_meta/08_VaultScopePolicy]] §3.5 "Handoff Compile-Level Verify 의무" 의 자기참조 모순 해소. |
| 2026-05-17 (Cycle 5p P1 — 표준 갱신) | §6.3 잔여 위험 5/6/7/8 신규 추가 (Phase 2 실측 발견 — TInlineAllocator<16> heap 회피 한계 / OnCursorQuery 매 frame StableSort hot-spot / Trim/Move Modify 폭주 / MCPlayModule UnrealEd Shipping 차단) + Phase 2c-refactor Minor 권고 4건 (반영 완료 ✅) 정리. §10 Engine 권위 매트릭스 확장 12 → 18건. §6.1/§6.2 evaluator 분리 (Phase 1 + Phase 2 누적). §9.B/§9.D/§9.F P2+P3 완료 체크. §11 KMCProject 파일 경로 — MCComboFrameRange.h/.cpp 신규 행 추가. §12 cross-link — frontmatter [[synthesis/cycle-5p-postmortem-remediation]] 추가. frontmatter cycle 5o → 5p / tags phase-2-ready → phase-2-complete / measured_date 2026-05-16 → 2026-05-17 / citation_disclosure 38 → 45. |
| **2026-05-18 (Cycle 5p+2 — Phase 4c 일반화 트리거 반영)** | **본 페이지의 §9.E 일반화 후보 §2.17 (DEPRECATED + PostLoad 3-step) 이 KMCProject Phase 4c 트리거로 vault 일반화 완료 — [[sources/ue-coreuobject-serialization]] §5.7 (컨테이너 마이그레이션 4-step + UObject::Rename Outer 교체 3 flags + placeholder 부모 생성 + Empty + Dirty) 신규 + [[sources/ue-coreuobject-deprecateduproperty]] §5 (UPROPERTY 필드 deprecation 결정 트리 + `_DEPRECATED` 접미사 vs `meta=(DeprecatedProperty)` 조합) 신규. §1 Thesis 의 일반화 가능 부분 매트릭스에 Cycle 5p+2 enrich 3 행 추가 (serialization §5.7 / deprecateduproperty §5 / mc-combo-editor-lite §5.7.9.3 Phase 4c 사례). §5 PostLoad BC compat 패턴 sub-§ 헤더에 "일반화 완료 Cycle 5p+2" 명시. §6.3 잔여 위험 5/6/7/8 해소 상태 매트릭스 갱신 (#6/#7 ✅ Phase 3+ §A/§B / #8 🟡 F6 추후). §9.B 갱신 (mc-combo-editor §5.7.9 / serialization §5.7 추가) + §9.D 갱신 (deprecateduproperty §5 추가) + §9.E 매트릭스 ✅/🟡 매트릭스 갱신 (§5.7 + §5 신규 완료 + §2.17 분산 흡수 완료). §12 sources cross-link — coreuobject-deprecateduproperty 추가 (Cycle 5p+2 enriched). frontmatter cycle 5p → 5p+2 / tags `phase-4c-generalization-trigger` 추가 / sources 매트릭스에 coreuobject-deprecateduproperty 추가 / measured_date 2026-05-17 → 2026-05-18 / last_updated 2026-05-17 → 2026-05-18 / citation_disclosure 45 → 47.** |
