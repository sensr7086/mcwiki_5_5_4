---
type: source
title: "UE LevelSequence — Tracks (빌트인 43종 + Custom 패턴)"
slug: ue-levelsequence-tracks
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/Tracks.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
related_concepts: []
tags: [ue, levelsequence, tracks, enriched, verified, case-study-pair, kmcproject-pair]
citation_disclosure: "🟢 12 / 🟡 3 / 🔴 1 · raw verified · Cycle #13.3 enrich + Cycle 5p §B2 KMCProject case study reverse-link"
---

# UE LevelSequence — Tracks (43종)

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/Tracks.md]] (294L)
> Parent: [[sources/ue-levelsequence-skill]] · 위치: `Engine/Source/Runtime/MovieSceneTracks/Public/Tracks/` (43 헤더)

## 1. Summary

🟢 UE 가 기본 제공하는 트랙 **43종** 카테고리 분류. 모든 트랙 = `UMovieSceneTrack` 자손 + Section 1+ 페어. 5.x 신규 4종 (Double LWC / Rotator / EulerTransform / CVar). Custom Track 작성 = [[sources/ue-levelsequence-moviescene]] §4 참조.

## 2. Property Track 16종 🟢 (raw §1)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneFloatTrack` | `FloatSection` | float (HP/Volume/Opacity) |
| `UMovieSceneDoubleTrack` ⭐5.x | `DoubleSection` | **LWC 정밀** (위치 등) |
| `UMovieSceneIntegerTrack` | `IntegerSection` | int32 |
| `UMovieSceneBoolTrack` | `BoolSection` | true/false |
| `UMovieSceneByteTrack` | `ByteSection` | enum |
| `UMovieSceneEnumTrack` | `EnumSection` | UEnum |
| `UMovieSceneStringTrack` | `StringSection` | FString |
| `UMovieSceneVectorTrack` | `VectorSection` | FVector / 2 / 4 |
| `UMovieSceneColorTrack` | `ColorSection` | FLinearColor |
| `UMovieSceneRotatorTrack` ⭐5.x | `RotatorSection` | FRotator |
| `UMovieScene3DTransformTrack` ⭐ | `3DTransformSection` | 위치/회전/스케일 |
| `UMovieSceneTransformTrack` | `TransformSection` | 일반 Transform |
| `UMovieSceneEulerTransformTrack` ⭐5.x | `EulerTransformSection` | 짐벌락 회피 |
| `UMovieSceneObjectPropertyTrack` | `ObjectPropertySection` | UObject* |
| `UMovieSceneActorReferenceTrack` | `ActorReferenceSection` | Actor 참조 |
| `UMovieScenePrimitiveMaterialTrack` | `PrimitiveMaterialSection` | Material 슬롯 |

### 2.1 `Interp` UPROPERTY meta 🟡 — Property Track 자동 노출

```cpp
UCLASS()
class AMyActor : public AActor
{
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp)  // ⭐ Interp = Sequencer 추적
    float Health = 100.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp)
    FLinearColor TintColor;
};
```

> ⭐ `Interp` 누락 시 Sequencer "+" 버튼에서 추가 불가.

## 3. Cinematic 전용 8종 ⭐ 🟢 (raw §2)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneCameraCutTrack` ⭐⭐ | `CameraCutSection` | **카메라 컷** (활성 카메라 스위치) |
| `UMovieSceneCinematicShotTrack` ⭐⭐ | `CinematicShotSection` | **Shot** (Sub Sequence + 자동 컷) |
| `UMovieSceneCameraAnimTrack` (depr) | — | 4.x — UCameraAnim |
| `UMovieSceneCameraShakeTrack` | `CameraShakeSection` | UCameraShakeBase 트리거 |
| `UMovieSceneCameraShakeSourceShakeTrack` | — | 거리 기반 Shake |
| `UMovieSceneCameraShakeSourceTriggerTrack` | — | Shake Source 트리거 |
| `UMovieSceneFadeTrack` | `FadeSection` | 화면 페이드 |
| `UMovieSceneSlomoTrack` | `SlomoSection` | Global Time Dilation |

CameraCut 구조 — `UMovieScene::CameraCutTrack` 멤버 (특수 슬롯, 일반 Tracks 배열 X):

```
Sequence 루트:
└── CameraCut Track (특수)
    ├── [0~120 프레임]   → CineCamera_01 (Possessable)
    ├── [120~240 프레임] → CineCamera_02
    └── [240~360 프레임] → CineCamera_03
→ Player::OnCameraCut(UCameraComponent*) 콜백
```

## 4. Audio / VFX 5종 🟢 (raw §3)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneAudioTrack` ⭐ | `AudioSection` | USoundCue / USoundWave |
| `UMovieSceneParticleTrack` | `ParticleSection` | UParticleSystem (Cascade) |
| `UMovieSceneParticleParameterTrack` | `ParticleParameterSection` | Cascade 파라미터 |
| `UMovieSceneMaterialTrack` | `MaterialSection` | Material Scalar/Vector |
| `UMovieSceneMaterialParameterCollectionTrack` | `MaterialParameterCollectionSection` | MPC 글로벌 |

> ⚠ Niagara 트랙은 별도 — `Plugins/FX/Niagara/Source/NiagaraAnim/` 안 `UMovieSceneNiagaraTrack`.

## 5. Animation 3종 🟢 (raw §4)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneSkeletalAnimationTrack` ⭐ | `SkeletalAnimationSection` | UAnimSequence 재생 |
| `UMovieSceneCommonAnimationTrack` | — | 베이스 |
| `UMovieSceneSpawnTrack` | `SpawnSection` | Spawnable 등장/사라짐 |

SkeletalAnimation = [[sources/ue-animation-animinstance]] 페어 — Possessable USkeletalMeshComponent 바인딩 후 + 버튼.

### 5.1 ⭐ Case Study: KMCProject UMCComboSection 풀 격상 (Cycle 5p §B2 reverse-link)

> **case study 페어**: [[synthesis/mc-combo-section-levelsequence-style-upgrade]] (Phase 1 handoff document) + [[synthesis/mc-combo-editor-levelsequence-lite]] (Phase 2 누적 합성).
>
> **vault scope 정책** ([[00_meta/08_VaultScopePolicy]]): 본 sub-§은 KMCProject (mc-) 실측 사례를 본 일반 페이지 (ue-) 에 reverse-link 보강한 항목. mc- 페이지가 본 §5 의 `UMovieSceneSkeletalAnimationSection` 패턴을 *검증/적용* 한 결과.

KMCProject `UMCComboSection` 베이스는 `UMovieSceneSkeletalAnimationSection` 의 핵심 파라미터를 차용해 **4 → 12 필드 격상**. Phase 2 evaluator 4 phase 누적 PASS (91.0 / 94.0 / ~88+ / 91.0).

#### 5.1.1 FMovieSceneSkeletalAnimationParams ↔ KMCProject 12 필드 매핑

→ Engine 권위: `Engine/Source/Runtime/MovieSceneTracks/Public/Sections/MovieSceneSkeletalAnimationSection.h` L20-L106 (Params 14 멤버) + `MovieSceneSection.h` L783/L787/L811/L815/L820/L824/L834-L848 (베이스).

| Engine 출처 | Engine 필드 | KMCProject 필드 | 차이 / 결정 |
| -- | -- | -- | -- |
| `MovieSceneSection.h L787-788` | `FMovieSceneFrameRange SectionRange` | **`FMCComboFrameRange SectionRange`** (USTRUCT 래퍼) | KMCProject 가 `MovieSceneFrameMigration.h L26-L104` (FMovieSceneFrameRange) 패턴 미러. UPROPERTY 부착 위해 `TRange<FFrameNumber>` 직접 부착 불가 (UHT 미지원) → USTRUCT 래퍼 의무 |
| `MovieSceneSkeletalAnimationSection.h L60` | `FFrameNumber StartFrameOffset` | `FFrameNumber StartFrameOffset` | (동일 — Slip 인터랙션) |
| L68 | `FFrameNumber EndFrameOffset` | (회피) | KMCProject 는 SectionRange 끝점으로 충분 |
| L72 | `float PlayRate` | `float PlayRate` (MVP) | Q1 결정 — `FMovieSceneFloatChannel` 회피 (Sequencer 모듈 의존 X) |
| L76 | `bool bReverse` | `uint8 bReverse : 1` (bitfield) | KMCProject 가 `MovieSceneSection.h L820/L824` bitfield 패턴 적용 |
| L80 | `FName SlotName` | `FName SlotName` (자손 UMCComboMontageSection only) | UMCComboInputSection / NotifySection 은 SlotName 의미 없음 — 자손 specific 결정 |
| L84 | `FMovieSceneSkeletalAnimationParams::Weight` | `float Weight` (MVP) | Q1 결정 — float (MVP) |
| L88 | `UMirrorDataTable* MirrorDataTable` | (회피) | KMCProject 도메인 외 |
| `MovieSceneSection.h L811-812` | `int32 RowIndex` | `int32 RowIndex` | (동일) |
| L815-816 | `int32 OverlapPriority` | `int32 OverlapPriority` (primary) | Q2 결정 — OverlapPriority primary + Tracks 배열 secondary |
| L820/L824 | `uint32 bIsActive : 1 / bIsLocked : 1` | `uint8 bIsActive : 1 / bIsLocked : 1` | KMCProject 가 `uint8 :1` 로 더 타이트 packing (Engine 본가 `BodyInstanceCore.h L38-L59` `uint8 :1` 사례 4건 verify) |
| L783 + L111-178 | `FMovieSceneEasingSettings Easing` | `int32 EaseInFrames` + `int32 EaseOutFrames` (MVP) | KMCProject 가 `IMovieSceneEasingFunction` 인터페이스 회피 — frame count 단순화 |

#### 5.1.2 베이스 → 자손 specific (Phase 2b)

| 자손 Section | KMCProject 결정 | 비고 |
| -- | -- | -- |
| `UMCComboMontageSection` | (유지) Montage + StartSectionName / (삭제) PlayRate (베이스 inheritance) / **(신규) SlotName + bSkipAnimNotifiers** | Engine `AnimInstance.h L437/L442/L605/L1619` SlotName 권위 4건 verify |
| `UMCComboInputSection` | 변경 없음 (베이스 신규 필드는 기본값 사용) | InputAction 도메인 |
| `UMCComboNotifySection` | 변경 없음 | GameplayTag 도메인 |

#### 5.1.3 시간축 UI — 9-Layer OnPaint + 7 EDragMode (Phase 2c/2d)

`UMovieSceneSkeletalAnimationSection` 의 Sequencer UI (Trim/Slip/Move drag mode) 패턴을 KMCProject `SMCComboTrackPanel` 의 자체 OnPaint 로 구현:
- **9 LayerId** (배경/룰러 → 본체 → Blend 그라데이션 → Reverse → Weight bar → SlotName → PlayRate × → OverlapPriority z-order → dim/lock → 선택 outline) — `Algo::StableSort` + `TInlineAllocator<16>` (Engine `Array.h L752 explicit` cross-type copy-init 회피)
- **7 EMCComboDragMode** (None/Scrub/Move/TrimLeft/TrimRight/SlipLeft/SlipRight) + `ComputeEdgeHitPx` 적응형 (5px / Width<20 시 0.25 / MinEdgePx 2px floor / Section<10px Slip 비활성)
- **`OnCursorQuery` override** — `Engine/SlateCore/Public/Input/CursorReply.h L33` (FCursorReply::Cursor) + `ICursor.h L17~` 5 EMouseCursor 권위

#### 5.1.4 발견된 함정 5건 (vault 일반화 후보 — Cycle 5p)

| 함정 | 일반화 대상 | 권위 |
| -- | -- | -- |
| `UPROPERTY() TRange<FFrameNumber>` UHT 미지원 | [[sources/ue-coreuobject-uobject]] §2.17 후보 — USTRUCT 래퍼 의무 패턴 | `MovieSceneFrameMigration.h L26-L104` |
| TArray cross-type copy-init `explicit` ctor | [[sources/ue-coreuobject-uobject]] §2.16 후보 — TArray<TObjectPtr<T>> → TArray<T*> 변환 | `Array.h L752` |
| `Modify()` 폭주 (drag 매 pixel SetRange) | [[sources/ue-coreuobject-uobject]] §2.17 후보 — Transaction 일괄 처리 패턴 | (관습) |
| OnCursorQuery 매 frame StableSort | [[sources/ue-slatecore-input]] §X 후보 — Hit-test caching 패턴 | (관습) |
| Slate Edge Hit Region 5px ↔ DPI scale | [[sources/ue-slatecore-input]] §X 후보 — EdgeHitPx 적응형 표준 | (관습) |

## 6. World / Level 4종 🟢 (raw §5)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneLevelVisibilityTrack` | `LevelVisibilitySection` | Streaming Level 토글 |
| `UMovieSceneVisibilityTrack` | `VisibilitySection` | 3D Actor 가시성 |
| `UMovieSceneDataLayerTrack` ⭐5.x | `DataLayerSection` | World Partition Data Layer 토글 |
| `UMovieSceneCustomPrimitiveDataTrack` | `CustomPrimitiveDataSection` | Primitive Custom Data |

## 7. Sub Sequence 1종 🟢 (raw §6)

`UMovieSceneSubTrack` ⭐ — 다른 Sequence 트랙 포함 (재귀 가능). 자세한 사용 = [[sources/ue-levelsequence-moviescene]] §2.8.

## 8. Constraint / Path 3종 🟢 (raw §7)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieScene3DAttachTrack` | `AttachSection` | Component Attach |
| `UMovieScene3DPathTrack` | `PathSection` | Spline Path 이동 |
| `UMovieScene3DConstraintTrack` | `ConstraintSection` | Constraint (LookAt / Aim) |

## 9. Event / CVar / Text 3종 🟢 (raw §8-10)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneEventTrack` ⭐ | `EventTriggerSection` / `EventRepeaterSection` | **BP Director Event** ([[sources/ue-levelsequence-director]]) |
| `UMovieSceneCVarTrack` 5.x | `CVarSection` | Console Variable 키프레임 |
| `UMovieSceneTextTrack` (plugin) | — | Burn-in 텍스트 (영상 출력) |

## 10. 사용 빈도 매트릭스 🟢 (raw §11)

| 빈도 | 트랙 |
|------|------|
| ★★★★★ | CameraCut · 3DTransform · SkeletalAnimation · Audio |
| ★★★★ | Material · Fade · CinematicShot · Sub · Event · Spawn |
| ★★★ | Slomo · Visibility · Float · Bool · Color |
| ★★ | ParticleParameter · LevelVisibility · DataLayer · CVar · Text |
| ★ | Constraint · Path · Attach · EulerTransform |

## 11. Track 추가 자동화 표준 🟢 (raw §12)

```cpp
#include "MovieScene.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Sections/MovieScene3DTransformSection.h"

void AMyTool::AddTransformTrack(ULevelSequence* Seq, AActor* T)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyTool::AddTransformTrack);
    UMovieScene* MS = Seq->GetMovieScene();
    if (!MS) return;
    FGuid Guid = MS->AddPossessable(T->GetActorLabel(), T->GetClass());
    Seq->BindPossessableObject(Guid, *T, T->GetWorld());
    auto* Track = MS->AddTrack<UMovieScene3DTransformTrack>(Guid);
    auto* Sec = Cast<UMovieScene3DTransformSection>(Track->CreateNewSection());
    Sec->SetRange(TRange<FFrameNumber>(FFrameNumber(0), FFrameNumber(240)));
    Track->AddSection(*Sec);
}
```

## 12. 함정 8 🟢 (raw §13)

| # | 함정 | 정답 |
|---|------|------|
| 1 | UPROPERTY `Interp` meta 누락 | `EditAnywhere, BlueprintReadWrite, Interp` |
| 2 | CameraCut 일반 Track 으로 추가 | `UMovieScene::CameraCutTrack` (특수 슬롯) |
| 3 | float Property → DoubleTrack 사용 | float = FloatTrack / double = DoubleTrack |
| 4 | SkeletalAnimation LoopCount 자동 추측 | Section 안 명시 |
| 5 | EventTrack Director BP Cooked 누락 | Cooked 검증 의무 |
| 6 | Slomo 특정 액터만 추측 | Global Time Dilation |
| 7 | Sub Sequence 동일 Binding 충돌 | Binding ID Override |
| 8 | CVarTrack 영구 변경 추측 | `bRestoreState=true` 시 자동 복원 |

## 13. 체크리스트 🟢 (raw §14)

- [ ] Property Track 대상 UPROPERTY = `Interp` meta
- [ ] CameraCut = `UMovieScene::CameraCutTrack` (특수)
- [ ] LWC 5.x = `DoubleTrack` (위치 등)
- [ ] EulerTransform = 짐벌락 회피
- [ ] Event Track = Director BP + Cooked 검증
- [ ] Sub Sequence Binding 충돌 방지
- [ ] DataLayer = World Partition World 만
- [ ] CVar = `bRestoreState` 의무

## 14. 신뢰도 🟢 (raw §15)

| 항목 | tier | 출처 |
|------|------|------|
| 43종 Track 헤더 | 🟢 verified | `MovieSceneTracks/Public/Tracks/` ls |
| 트랙 → Section 매핑 | 🟡 grep-listed | 명명 규칙 |
| `Interp` UPROPERTY 동작 | 🔴 inferred | `CPF_Interp` grep 필요 |
| `UMovieScene::CameraCutTrack` 특수 멤버 | 🟢 verified | `MovieScene.h` UPROPERTY |
| AddTrack / AddPossessable API | 🟢 verified | `MovieScene.h` ENGINE_API |
| CVarTrack / DataLayerTrack 5.x | 🟡 grep-listed | 파일 존재 |
| **§5.1 FMovieSceneSkeletalAnimationParams 14 멤버 ↔ KMCProject 12 필드 매핑** | 🟢 verified | `MovieSceneSkeletalAnimationSection.h L20-L106` + `MovieSceneSection.h L783/L787/L811/L815/L820/L824/L834-L848` (Phase 2 evaluator 11 권위 4 phase 누적 verify) |

## 15. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 베이스: [[sources/ue-levelsequence-moviescene]] (Track/Section virtual)
- 페어: [[sources/ue-levelsequence-levelsequenceplayer]] (런타임 재생) · [[sources/ue-levelsequence-director]] (Event Track) · [[sources/ue-levelsequence-cinecamera]] (CameraCut)
- 카테고리 페어: [[sources/ue-animation-animinstance]] (Skeletal) · [[sources/ue-components-audiocomponent]] (Audio) · [[sources/ue-umg-skill]] (UWidgetAnimation 동일 베이스)
- ⭐ **Case study (mc-, Cycle 5p §B2)**:
  - [[synthesis/mc-combo-section-levelsequence-style-upgrade]] (Phase 1 handoff document — UMCComboSection 풀 격상)
  - [[synthesis/mc-combo-editor-levelsequence-lite]] (Phase 2 누적 합성 — LevelSequence 데이터 모델 lite + 9-Layer OnPaint + 7 EDragMode)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 3
- 추가 (5.5.4 에만): 0
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `> **위치 (verified)**: `Engine/Source/Runtime/MovieSceneTracks/Public/Tracks/` (43 → > **위치 (verified)**: `Engine/Source/Runtime/MovieSceneTracks/Public/Tracks/` (UE`
- `| 43종 Track 헤더 목록 | **[verified]** ✅ | `Engine/Source/Runtime/MovieSceneTracks/P → | 43종 Track 헤더 목록 | **[verified]** ✅ | `Engine/Source/Runtime/MovieSceneTracks/P`
- `| 2026-05-13 | 최초 작성. **43종 빌트인 트랙 분류** (Property 16 / Cinematic 8 / Audio-VFX 5 → | 2026-05-13 | 최초 작성. **43종 빌트인 트랙 분류** (Property 16 / Cinematic 8 / Audio-VFX 5`

**5.5.4 에만 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/LevelSequence/references/Tracks.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/LevelSequence/references/Tracks.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
