---
name: levelsequence-tracks
description: MovieSceneTracks 빌트인 트랙 43종 카테고리 분류 + 자주 쓰는 트랙 (Transform / Float / Audio / Event / Material / Skeletal / CameraCut / CinematicShot / Sub / Visibility / Fade / Spawn / Slomo / DataLayer / Text) + 5.x 신규 (Double / Rotator / EulerTransform / CVar). Section 종류 + Custom Track 패턴 cross-link.
---

# LevelSequence/Tracks — 빌트인 트랙 43종 ⭐

> **위치 (verified)**: `Engine/Source/Runtime/MovieSceneTracks/Public/Tracks/` (43 헤더)
> **요지**: UE 가 기본 제공하는 트랙 카테고리. 모든 트랙 = `UMovieSceneTrack` 자손 + Section 1+ 보유. **Custom Track 작성은 [`MovieScene.md §4.1`](./MovieScene.md#4-umoviescenetrack-핵심-virtual)** 참조.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 Property Track | `UMovieScenePropertyTrack` 자손 = Property 이름 / Path 정확 |
| 🚨 Section Class | 각 Track 당 고유 Section 타입 — `SupportsType` virtual 의무 |
| 🚨 5.x ECS | Property Track = ECS Entity 자동 변환 |
| 🚨 Cooked Build | Editor 메타 (`#if WITH_EDITORONLY_DATA`) — 런타임 평가 무관 |

---

## 1. Property Track 카테고리 (16종 — 가장 흔함)

| 트랙 | 헤더 | Section | 용도 |
|------|------|---------|------|
| `UMovieSceneFloatTrack` | `MovieSceneFloatTrack.h` | `FloatSection` | float 속성 (HP / Volume / Opacity) |
| `UMovieSceneDoubleTrack` ⭐(5.x) | `MovieSceneDoubleTrack.h` | `DoubleSection` | LWC 정밀 — 위치 등 |
| `UMovieSceneIntegerTrack` | `MovieSceneIntegerTrack.h` | `IntegerSection` | 정수 |
| `UMovieSceneBoolTrack` | `MovieSceneBoolTrack.h` | `BoolSection` | true/false |
| `UMovieSceneByteTrack` | `MovieSceneByteTrack.h` | `ByteSection` | enum 값 |
| `UMovieSceneEnumTrack` | `MovieSceneEnumTrack.h` | `EnumSection` | UEnum 값 |
| `UMovieSceneStringTrack` | `MovieSceneStringTrack.h` | `StringSection` | 텍스트 |
| `UMovieSceneVectorTrack` | `MovieSceneVectorTrack.h` | `VectorSection` | FVector / 2 / 4 |
| `UMovieSceneColorTrack` | `MovieSceneColorTrack.h` | `ColorSection` | FLinearColor |
| `UMovieSceneRotatorTrack` ⭐(5.x) | `MovieSceneRotatorTrack.h` | `RotatorSection` | FRotator |
| `UMovieScene3DTransformTrack` ⭐ | `MovieScene3DTransformTrack.h` | `3DTransformSection` | Transform (위치/회전/스케일) |
| `UMovieSceneTransformTrack` | `MovieSceneTransformTrack.h` | `TransformSection` | 일반 Transform |
| `UMovieSceneEulerTransformTrack` (5.x) | `MovieSceneEulerTransformTrack.h` | `EulerTransformSection` | 오일러 회전 (짐벌락 회피) |
| `UMovieSceneObjectPropertyTrack` | `MovieSceneObjectPropertyTrack.h` | `ObjectPropertySection` | UObject* 속성 |
| `UMovieSceneActorReferenceTrack` | `MovieSceneActorReferenceTrack.h` | `ActorReferenceSection` | Actor 참조 |
| `UMovieScenePrimitiveMaterialTrack` | `MovieScenePrimitiveMaterialTrack.h` | `PrimitiveMaterialSection` | Primitive 안 Material 슬롯 |

### 1.1 Property Track 작성 패턴

```cpp
// 1. 자산 측 — Property 노출
UCLASS()
class AMyActor : public AActor
{
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp)   // ⭐ Interp meta = Sequencer 추적 가능
    float Health = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp)
    FLinearColor TintColor;
};

// 2. Sequencer 에서 + 버튼 → Health / TintColor 트랙 추가 자동 가능
```

> ⭐ **`Interp` UPROPERTY meta** = Sequencer 가 자동 트랙 노출. 누락 시 수동 추가 X.

---

## 2. Cinematic 전용 트랙 (8종) ⭐

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneCameraCutTrack` ⭐⭐ | `CameraCutSection` | **카메라 컷** (Sequence 동안 활성 카메라 스위치) |
| `UMovieSceneCinematicShotTrack` ⭐⭐ | `CinematicShotSection` | **Shot** (Sub Sequence + 자동 카메라 컷) — 영화 편집 |
| `UMovieSceneCameraAnimTrack` (deprecated) | — | 4.x — UCameraAnim |
| `UMovieSceneCameraShakeTrack` | `CameraShakeSection` | UCameraShakeBase 트리거 |
| `UMovieSceneCameraShakeSourceShakeTrack` | — | UCameraShakeSourceComponent 통한 거리 기반 Shake |
| `UMovieSceneCameraShakeSourceTriggerTrack` | — | Shake Source 트리거 |
| `UMovieSceneFadeTrack` | `FadeSection` | 화면 페이드 인/아웃 |
| `UMovieSceneSlomoTrack` | `SlomoSection` | Global Time Dilation |

### 2.1 CameraCut 표준 사용

```
Sequencer 안 시퀀스 루트:
└── CameraCut Track (특수 — UMovieScene::CameraCutTrack 멤버)
    ├── [0~120 프레임] → CineCamera_01 (Possessable Binding)
    ├── [120~240 프레임] → CineCamera_02
    └── [240~360 프레임] → CineCamera_03

→ Player::OnCameraCut 콜백 트리거 — UCameraComponent 전달
```

---

## 3. Audio / VFX 트랙 (5종)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneAudioTrack` ⭐ | `AudioSection` | USoundCue / USoundWave |
| `UMovieSceneParticleTrack` | `ParticleSection` | UParticleSystem (Cascade) trigger |
| `UMovieSceneParticleParameterTrack` | `ParticleParameterSection` | Cascade 파라미터 |
| `UMovieSceneMaterialTrack` | `MaterialSection` | Material Parameter (Scalar/Vector) |
| `UMovieSceneMaterialParameterCollectionTrack` | `MaterialParameterCollectionSection` | MPC 글로벌 파라미터 |

---

## 4. Animation 트랙 (3종)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneSkeletalAnimationTrack` ⭐ | `SkeletalAnimationSection` | UAnimSequence 재생 (캐릭터 본 애니) |
| `UMovieSceneCommonAnimationTrack` | — | 베이스 |
| `UMovieSceneSpawnTrack` | `SpawnSection` | Spawnable 등장/사라짐 |

### 4.1 SkeletalAnimation 사용 흐름

```
Sequencer:
1. Possessable = USkeletalMeshComponent 보유 Actor 바인딩
2. + 버튼 → "Animation" → AnimSequence 선택
3. AnimSection.SetRange(Start, End) + LoopCount 설정
→ Animation/AnimInstance §SkeletalAnimationTrack 페어 참조
```

---

## 5. World / Level 트랙 (4종)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneLevelVisibilityTrack` | `LevelVisibilitySection` | 레벨 가시성 (Streaming Level 토글) |
| `UMovieSceneVisibilityTrack` | `VisibilitySection` | 3D 액터 가시성 |
| `UMovieSceneDataLayerTrack` ⭐(5.x) | `DataLayerSection` | World Partition Data Layer 토글 |
| `UMovieSceneCustomPrimitiveDataTrack` | `CustomPrimitiveDataSection` | Primitive Custom Data |

---

## 6. Sub Sequence 트랙 (1종)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneSubTrack` ⭐ | `SubSection` | 다른 Sequence 를 트랙으로 포함 (재귀 가능) |

자세한 사용 = [`MovieScene.md §8 Sub Sequence`](./MovieScene.md#8-sub-sequence-시퀀스-안-시퀀스-grep-listed).

---

## 7. Constraint / Path 트랙 (3종)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieScene3DAttachTrack` | `AttachSection` | Attach to Component |
| `UMovieScene3DPathTrack` | `PathSection` | Spline Path 따라 이동 |
| `UMovieScene3DConstraintTrack` | `ConstraintSection` | Constraint (LookAt / Aim) |

---

## 8. Event / Trigger 트랙 (1종 ⭐)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneEventTrack` ⭐ | `EventTriggerSection` / `EventRepeaterSection` | **BP Director Event 호출** |

자세한 사용 = [`Director.md`](./Director.md).

---

## 9. CVar 트랙 (1종 — 5.x)

| 트랙 | Section | 용도 |
|------|---------|------|
| `UMovieSceneCVarTrack` (5.x) | `CVarSection` | Console Variable 동적 변경 (r.PostProcess / r.DefaultFeature 등) |

영상 출력 시 일시 품질 변경에 유용.

---

## 10. Text 트랙 (Plugin — 1종)

`Plugins/MovieScene/MovieSceneTextTrack/` 플러그인:

| 트랙 | 용도 |
|------|------|
| `UMovieSceneTextTrack` | Burn-in 텍스트 (TC / Frame / Custom) |

---

## 11. 트랙별 사용 빈도 (실무 기준)

| 빈도 | 트랙 |
|------|------|
| **★★★★★** (거의 모든 컷씬) | CameraCut / 3DTransform / SkeletalAnimation / Audio |
| **★★★★** (자주) | Material / Fade / CinematicShot / Sub / Event / Spawn |
| **★★★** (가끔) | Slomo / Visibility / Float / Bool / Color |
| **★★** (드물게) | ParticleParameter / LevelVisibility / DataLayer / CVar / Text |
| **★** (특수) | Constraint / Path / Attach / EulerTransform |

---

## 12. 트랙 추가 표준 코드 (Sequencer 외 — 자동화)

```cpp
// LevelSequenceEditorBlueprintLibrary 또는 UMovieSceneSequenceExtensions 사용
#include "MovieScene.h"
#include "MovieSceneTrack.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Sections/MovieScene3DTransformSection.h"

void AMyTool::AddTransformTrack(ULevelSequence* Seq, AActor* TargetActor, const FTransform& Start, const FTransform& End)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyTool::AddTransformTrack);

    UMovieScene* MovieScene = Seq->GetMovieScene();
    if (!MovieScene) return;

    // 1. Possessable 바인딩
    FGuid Guid = MovieScene->AddPossessable(TargetActor->GetActorLabel(), TargetActor->GetClass());
    Seq->BindPossessableObject(Guid, *TargetActor, TargetActor->GetWorld());

    // 2. Transform Track 추가
    UMovieScene3DTransformTrack* Track = MovieScene->AddTrack<UMovieScene3DTransformTrack>(Guid);

    // 3. Section 생성
    UMovieScene3DTransformSection* Section = Cast<UMovieScene3DTransformSection>(Track->CreateNewSection());
    Section->SetRange(TRange<FFrameNumber>(FFrameNumber(0), FFrameNumber(240)));

    // 4. Section 안 Channel 키프레임 추가 (X/Y/Z/Pitch/Yaw/Roll/...)
    // FloatChannel 안 키프레임 추가 — 자세한 Channel API = MovieScene/Channels/

    Track->AddSection(*Section);
}
```

---

## 13. 함정 & 안티패턴 (8종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | UPROPERTY 안 `Interp` meta 누락 → Sequencer 자동 트랙 X | `UPROPERTY(EditAnywhere, BlueprintReadWrite, Interp)` |
| 2 | `UMovieSceneCameraCutTrack` 일반 Track 으로 추가 | `UMovieScene::CameraCutTrack` 멤버 (특수 슬롯) |
| 3 | float Property 변경 시 `UMovieSceneDoubleTrack` 사용 → 타입 불일치 | float = `FloatTrack` / double = `DoubleTrack` (5.x LWC) |
| 4 | Sequencer 안 추가한 SkeletalAnimation = LoopCount Sequence 동안 자동 | LoopCount 명시 (Section 안 설정) |
| 5 | EventTrack 콜백 호출 위치 = Cooked Build Director BP 누락 | LevelSequence Director BP Cooked 검증 |
| 6 | Slomo Track = 특정 액터 시간만 변경 추측 | Global Time Dilation (모든 액터 영향) |
| 7 | Sub Sequence 안 동일 Possessable Binding 충돌 | Binding ID 별 Override 명시 |
| 8 | CVarTrack 영구 변경 추측 | Sequence 종료 시 자동 복원 (`bRestoreState=true` 시) |

---

## 14. 체크리스트

- [ ] Property Track 사용 시 UPROPERTY 에 `Interp` meta 추가
- [ ] CameraCut = `UMovieScene::CameraCutTrack` 슬롯 사용 (특수)
- [ ] LWC 5.x = `UMovieSceneDoubleTrack` (위치 등)
- [ ] EulerTransform = 짐벌락 회피 (오일러 회전 중요 시)
- [ ] Event Track 사용 시 Director BP 정의 + Cooked Build 검증
- [ ] Sub Sequence 안 Binding 충돌 방지 (Override 명시)
- [ ] DataLayer Track = World Partition 활성 World 만
- [ ] CVar Track = Sequence 종료 시 복원 의무 (`bRestoreState`)
- [ ] SkeletalAnimation = LoopCount + Slot Name 명시
- [ ] Section `SetRange` + Channel 키프레임 모두 설정

---

## 15. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| 43종 Track 헤더 목록 | **[verified]** ✅ | `Engine/Source/Runtime/MovieSceneTracks/Public/Tracks/` 안 ls (43개 확인) |
| 트랙별 Section 클래스 매핑 | **[grep-listed]** ⚠ | 일반 명명 규칙 (TransformTrack → TransformSection) |
| `Interp` UPROPERTY meta | **[inferred]** ❌ | UE 일반 — `MovieScene` 코드 안 `HasAnyPropertyFlags(CPF_Interp)` grep 필요 |
| `UMovieScene::CameraCutTrack` 특수 멤버 | **[verified]** ✅ | `MovieScene.h` 안 UPROPERTY |
| AddTrack / AddPossessable API | **[verified]** ✅ | `MovieScene.h` 안 ENGINE_API 메소드 |
| CVarTrack / DataLayerTrack 5.x | **[grep-listed]** ⚠ | 파일 존재 (`MovieSceneCVarTrack.h` / `MovieSceneDataLayerTrack.h`) |

---

## 16. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인
- ⭐ [`./MovieScene.md`](./MovieScene.md) — 베이스 (Track / Section virtual)
- ⭐ [`./LevelSequencePlayer.md`](./LevelSequencePlayer.md) — 런타임 재생
- [`./Director.md`](./Director.md) — Event Track + BP Director
- [`./CineCamera.md`](./CineCamera.md) — CameraCut 페어
- [`../../Animation/references/AnimInstance.md`](../../Animation/references/AnimInstance.md) — SkeletalAnimation Track 페어
- [`../../Components/references/AudioComponent.md`](../../Components/references/AudioComponent.md) — Audio Track 페어
- [`../../UMG/SKILL.md`](../../UMG/SKILL.md) — UWidgetAnimation Track 19종 (동일 베이스)

---

## 17. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **43종 빌트인 트랙 분류** (Property 16 / Cinematic 8 / Audio-VFX 5 / Animation 3 / World 4 / Sub 1 / Constraint 3 / Event 1 / CVar 1 / Text 1) + 사용 빈도 매트릭스 + 트랙 추가 표준 코드 + 함정 8 + 체크리스트 10 + 신뢰도 태그 6. Engine 5.7.4 검증 — MovieSceneTracks/Public/Tracks/ 43 헤더 ls. |
