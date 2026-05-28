---
type: source
title: "UE LevelSequence — MovieScene (베이스 ⭐⭐)"
slug: ue-levelsequence-moviescene
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/MovieScene.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-15
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, levelsequence, moviescene, base, enriched, verified]
citation_disclosure: "🟢 13 / 🟡 2 / 🔴 0 · raw verified · Cycle #13.2 enrich"
---

# UE LevelSequence — MovieScene (베이스 ⭐⭐)

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/MovieScene.md]] (449L)
> Parent: [[sources/ue-levelsequence-skill]] · 위치: `Engine/Source/Runtime/MovieScene/`
> 모든 시퀀스 시스템의 *공통 기반* — LevelSequence / WidgetAnimation / CameraAnimationSequence / ActorSequence / TemplateSequence 모두 본 베이스 자손.

## 1. Summary

🟢 4 핵심 클래스 — `UMovieSceneSequence` (베이스) · `UMovieScene` (Track 컨테이너) · `UMovieSceneTrack` (Track 베이스) · `UMovieSceneSection` (시간 구간). Track ← Section ← Channel 3단 계층. 5.x 표준 `FFrameNumber` 의무 (float 시간 X). Cross-category 통합점 — UMG / Camera / Actor / Template 시퀀스 모두 본 베이스 자손.

## 2. Key claims

### 2.1 클래스 계층 🟢 (raw L19-50)

```
UMovieSceneSequence (Sequence 베이스)
├── ULevelSequence           (LevelSequence Plugin)
├── UWidgetAnimation         (UMG)
├── UCameraAnimationSequence (EngineCameras 5.x)
├── UActorSequence           (ActorSequence Plugin)
└── UTemplateSequence        (TemplateSequence Plugin)

UMovieScene (Track 컨테이너 — Sequence 안 1개)
├── TArray<UMovieSceneTrack*> Tracks
├── TArray<FMovieScenePossessable> / Spawnables
└── CameraCutTrack (마스터 특수) + FrameRate + PlaybackRange

UMovieSceneTrack (Track 베이스)
├── UMovieScenePropertyTrack → Float/Double(5.x LWC)/Vector/Color/Bool ...
├── UMovieSceneEventTrack    (Director Event)
└── UMovieSceneSubTrack / CinematicShotTrack

UMovieSceneSection (시간 구간 + 키프레임)
├── UMovieSceneFloatSection / 3DTransformSection / SkeletalAnimationSection ...
```

### 2.2 UMovieSceneSequence 14 virtual 🟢 (raw §2 — LevelSequence.h:43-67)

```cpp
class UMovieSceneSequence : public UObject
{
    virtual UMovieScene* GetMovieScene() const = 0;                       // [1] PURE
    virtual void BindPossessableObject(const FGuid&, UObject&, UObject*) = 0;  // [2]
    virtual bool CanPossessObject(UObject&, UObject*) const;              // [3]
    virtual FGuid FindBindingFromObject(UObject*, UObject*) const;        // [4]
    virtual UObject* GetParentObject(UObject*) const;                     // [5]
    virtual void UnbindPossessableObjects(const FGuid&);                  // [6]
    virtual void GatherExpiredObjects(const FMovieSceneObjectCache&, TArray<FGuid>&) const;  // [7]
    virtual bool AllowsSpawnableObjects() const;                          // [8]
    virtual UObject* MakeSpawnableTemplateFromInstance(UObject&, FName);  // [9]
    virtual UObject* CreateDirectorInstance(TSharedRef<const FSharedPlaybackState>, FMovieSceneSequenceID);  // [10]
    virtual ETrackSupport IsTrackSupportedImpl(TSubclassOf<UMovieSceneTrack>) const;  // [11]
    virtual bool AllowsCustomBindings() const;                            // [12] 5.x
    virtual const FMovieSceneBindingReferences* GetBindingReferences() const;  // [13]
    virtual bool CanAnimateObject(UObject&) const;                        // [14]
};
```

### 2.3 UMovieScene 핵심 멤버 🟢 (raw §3 — MovieScene.h)

```cpp
class UMovieScene : public UMovieSceneSignedObject
{
    UPROPERTY() TArray<TObjectPtr<UMovieSceneTrack>> Tracks;
    UPROPERTY() TArray<FMovieScenePossessable> Possessables;
    UPROPERTY() TArray<FMovieSceneSpawnable> Spawnables;
    UPROPERTY(Instanced) TObjectPtr<UMovieSceneTrack> CameraCutTrack;  // 마스터
    UPROPERTY() FFrameRate TickResolution;            // 평가 해상도 (보통 24000)
    UPROPERTY() FFrameRate DisplayRate;               // 표시 fps (24/30/60)
    UPROPERTY() FMovieSceneFrameRange PlaybackRange;  // [Start, End]
    UPROPERTY() FMovieSceneFrameRange WorkingRange;
    UPROPERTY() FMovieSceneFrameRange ViewRange;
};
```

### 2.4 UMovieSceneTrack 6 PURE_VIRTUAL 🟢 (raw §4 — MovieSceneTrack.h:388-575)

| # | virtual | 용도 |
|---|---------|------|
| 1 | `IsEmpty()` | 트랙에 Section 0 검사 |
| 2 | `SupportsType(TSubclassOf<USection>)` | Section 종류 지원 |
| 3 | `CreateNewSection()` | Section 새로 생성 (Editor + Runtime) |
| 4 | `GetAllSections()` | TArray<Section*> 접근 |
| 5 | `HasSection(const Section&)` | Section 소유 검사 |
| 6 | `GetDisplayName()` | Editor 표시명 (`WITH_EDITORONLY_DATA` 가드) |

```cpp
// Custom Track 표준
UCLASS()
class UMyMovieSceneTrack : public UMovieSceneTrack
{
    GENERATED_BODY()
    UPROPERTY() TArray<TObjectPtr<UMovieSceneSection>> Sections;
public:
    virtual bool IsEmpty() const override { return Sections.IsEmpty(); }
    virtual bool SupportsType(TSubclassOf<UMovieSceneSection> C) const override
    { return C == UMyMovieSceneSection::StaticClass(); }
    virtual UMovieSceneSection* CreateNewSection() override
    { return NewObject<UMyMovieSceneSection>(this, NAME_None, RF_Transactional); }
    virtual const TArray<UMovieSceneSection*>& GetAllSections() const override
    { return reinterpret_cast<const TArray<UMovieSceneSection*>&>(Sections); }
    virtual bool HasSection(const UMovieSceneSection& S) const override
    { return Sections.Contains(&S); }
#if WITH_EDITORONLY_DATA
    virtual FText GetDisplayName() const override { return FText::FromString(TEXT("My Track")); }
#endif
};
```

### 2.5 UMovieSceneSection 핵심 🟢 (raw §5 — MovieSceneSection.h:318-695)

```cpp
class UMovieSceneSection : public UMovieSceneSignedObject
{
    UPROPERTY() FMovieSceneFrameRange SectionRange;       // [Start, End] FrameNumber
    UPROPERTY() EMovieSceneBlendType BlendType;            // Absolute / Additive / Relative ...
    UPROPERTY() FMovieSceneEasingSettings Easing;          // 5.x

    virtual void SetRange(const TRange<FFrameNumber>&);
    virtual void SetBlendType(EMovieSceneBlendType);
    virtual FMovieSceneTimeWarpVariant* GetTimeWarp();     // 5.x Time Warp
    virtual void OnBindingIDsUpdated(...);
};
```

`EMovieSceneBlendType` 5종 🟡: **Absolute** (덮어쓰기) / **Additive** (가산) / **Relative** (Initial 기준 오프셋) / `AbsoluteFromAdditive` 5.x / `AdditiveFromBase` 5.x.

### 2.6 FFrameNumber + FFrameRate 표준 🟢 (raw §6)

```cpp
struct FFrameNumber { int32 Value; };                  // 정수 프레임
struct FFrameRate   { int32 Numerator=24000, Denominator=1; };

const FFrameRate TickRes = MovieScene->GetTickResolution();   // 24000
const FFrameRate DisplayRate = MovieScene->GetDisplayRate(); // 24/30/60

FFrameNumber FrameAt2s = (TickRes * 2.0).RoundToFrame();      // 시간 → Frame
double Seconds = FrameAt2s / TickRes;                          // Frame → 시간

// Display fps 환산
FFrameNumber DispFrame = FFrameRate::TransformTime(
    FFrameTime(FrameAt2s), TickRes, DisplayRate).GetFrame();
```

> 🚨 float 시간 사용 X — 24fps = 1/24 = 0.041666... 무한 소수 → 정밀도 손실.

### 2.7 Binding (Possessable vs Spawnable) 🟢 (raw §7)

| 구분 | Possessable | Spawnable |
|------|-------------|-----------|
| 정의 | Sequence **외부 Actor** 바인딩 | Sequence 가 **직접 Spawn** |
| Lifetime | 외부 (Level 안 Actor) | Sequence Play 동안만 |
| 식별 | `FMovieScenePossessable` | `FMovieSceneSpawnable` |
| 사용 | 게임 캐릭터 / 환경 액터 | 컷씬 전용 (촛불 / 임시 효과) |
| 메모리 | 외부 Actor | Sequence NewObject (Transient) |

### 2.8 Sub Sequence 🟡 (raw §8 — grep-listed)

`UMovieSceneSubTrack` — 다른 Sequence 트랙으로 포함. CinematicShotTrack 도 같은 메커니즘.

```cpp
UMovieSceneSubTrack* SubTrack = MainSeq->GetMovieScene()->AddTrack<UMovieSceneSubTrack>();
auto* Sec = Cast<UMovieSceneSubSection>(SubTrack->CreateNewSection());
Sec->SetSequence(SubSeq);
Sec->SetRange(TRange<FFrameNumber>(StartFrame, EndFrame));
```

## 3. 함정 10 🟢 (raw §9)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Custom Track 6 PURE_VIRTUAL 누락 | 모두 override + `WITH_EDITORONLY_DATA` 가드 |
| 2 | `GetDisplayName()` Runtime 모듈 (Editor 데이터) | `#if WITH_EDITORONLY_DATA` |
| 3 | float 시간 → 24fps 정밀도 손실 | `FFrameNumber` + `FFrameRate` |
| 4 | Section `SetRange` 후 `OnSectionAddedImpl` 누락 | `AddSection` 표준 헬퍼 |
| 5 | `SectionToKey` 미설정 → Editor 키 추가 오류 | `SetSectionToKey` override |
| 6 | Possessable / Spawnable 혼동 | 외부 Actor = Possessable / 일회용 = Spawnable |
| 7 | Sub Sequence Loop = 외부 Loop 추측 | Sub Loop 분리 가능 |
| 8 | Possessables / Spawnables 직접 수정 | `AddPossessable` / `AddSpawnable` API |
| 9 | Section 직접 NewObject | `Track->CreateNewSection()` |
| 10 | 5.x ECS — Render Thread 평가 추측 | Game Thread 전용 |

## 4. 체크리스트 🟢 (raw §10)

- [ ] Custom Track = 6 PURE_VIRTUAL override + Editor 데이터 가드
- [ ] `CreateNewSection` = `NewObject + RF_Transactional`
- [ ] `FFrameNumber` 사용 (float 시간 X)
- [ ] `TickResolution` / `DisplayRate` 명시
- [ ] Possessable / Spawnable 결정
- [ ] Sub Sequence Loop / Time Scale 명시
- [ ] Render Thread 접근 X
- [ ] Section `SetRange` + `BlendType` + `Easing`

## 5. 신뢰도 🟢 (raw §11)

| 항목 | tier | 출처 |
|------|------|------|
| UMovieSceneSequence 14 virtual | 🟢 verified | `LevelSequence.h:43-67` override |
| UMovieSceneTrack 6 PURE_VIRTUAL | 🟢 verified | `MovieSceneTrack.h:388,481,522,529,537,575` |
| UMovieSceneSection virtual | 🟢 verified | `MovieSceneSection.h:318-695` |
| UMovieScene 멤버 / API | 🟢 verified | `MovieScene.h` grep |
| 5.x ECS 흐름 | 🟡 grep-listed | `MovieScene/Public/EntitySystem/` 75 헤더 |
| EMovieSceneBlendType 5종 | 🟡 inferred | `MovieSceneBlendType.h` grep 필요 |
| Sub Sequence API | 🟡 grep-listed | `MovieSceneSubTrack.h` 존재 |

## 6. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 자손 시퀀스: [[sources/ue-levelsequence-levelsequenceplayer]] (`ULevelSequence`) · [[sources/ue-umg-skill]] (`UWidgetAnimation`) · [[sources/ue-assetclasses-camera]] (`UCameraAnimationSequence`)
- 트랙: [[sources/ue-levelsequence-tracks]] (43 빌트인) · [[sources/ue-levelsequence-director]] (Event Track)
- ECS: [[sources/ue-levelsequence-entitysystemecs]] (5.x)
- 정책: 🚨 [[concepts/Profiling-Scope-Rule]] · 🚨 [[concepts/Editor-Only-4-Tier-Separation]]
