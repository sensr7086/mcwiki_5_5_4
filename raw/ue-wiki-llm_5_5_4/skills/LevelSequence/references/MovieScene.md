---
name: levelsequence-moviescene
description: UMovieScene + UMovieSceneSequence + UMovieSceneTrack + UMovieSceneSection 베이스 — 모든 시퀀스 시스템 (LevelSequence / WidgetAnimation / CameraAnimationSequence / ActorSequence / TemplateSequence) 의 공통 기반. virtual 후크 + 라이프사이클 + FFrameNumber/FFrameRate + Binding (Possessable/Spawnable) + Sub Sequence.
---

# LevelSequence/MovieScene — 베이스 시스템 ⭐⭐

> **위치 (verified)**:
> - **UMovieScene** — `Engine/Source/Runtime/MovieScene/Public/MovieScene.h`
> - **UMovieSceneSequence** — `Engine/Source/Runtime/MovieScene/Public/MovieSceneSequence.h`
> - **UMovieSceneTrack** — `Engine/Source/Runtime/MovieScene/Public/MovieSceneTrack.h`
> - **UMovieSceneSection** — `Engine/Source/Runtime/MovieScene/Public/MovieSceneSection.h`
> - **IMovieScenePlayer** — `Engine/Source/Runtime/MovieScene/Public/IMovieScenePlayer.h`
> - **UMovieSceneSequencePlayer** — `Engine/Source/Runtime/MovieScene/Public/MovieSceneSequencePlayer.h`
>
> **요지**: 모든 시퀀스 (LevelSequence / UWidgetAnimation / UCameraAnimationSequence / UActorSequence / UTemplateSequence) 의 **공통 베이스**. Track ← Section ← Channel 의 3단 계층 구조.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 5.x ECS 평가 | 평가 = ECS (Game Thread) — Render Thread 안 접근 X |
| 🚨 `FFrameNumber` 의무 | float 시간 X — `FFrameNumber` (정수) + `FFrameRate` 변환 |
| 🚨 [`05_EditorOnlyIndex`](../../../references/05_EditorOnlyIndex.md) | Track/Section 의 Editor 메소드 = `#if WITH_EDITOR` 가드 |
| 🚨 Lifetime | `UMovieScene` = `UPROPERTY()` (UMovieSceneSequence 안 보유) |

---

## 1. 클래스 계층 [verified]

```
UMovieSceneSequence (Sequence 베이스)
├── ULevelSequence          (LevelSequence Plugin)
├── UWidgetAnimation        (UMG 모듈) — UMG 안 위젯 애니메이션
├── UCameraAnimationSequence (EngineCameras Plugin) — 5.x 카메라 애니
├── UActorSequence          (ActorSequence Plugin) — Actor 안 sub-sequence
└── UTemplateSequence       (TemplateSequence Plugin) — 재사용 템플릿

UMovieScene (Track 컨테이너 — Sequence 안 1개)
├── TArray<UMovieSceneTrack*> Tracks
└── 1 RootFolder + Settings (FrameRate / PlaybackRange / ViewRange)

UMovieSceneTrack (Track 베이스)
├── UMovieScenePropertyTrack (Property 베이스)
│   ├── UMovieSceneFloatTrack
│   ├── UMovieSceneDoubleTrack (5.x LWC)
│   ├── UMovieSceneVectorTrack
│   ├── UMovieSceneColorTrack
│   ├── UMovieSceneBoolTrack
│   └── ... (43종 — Tracks.md 참조)
├── UMovieSceneNameableTrack
├── UMovieSceneEventTrack
└── UMovieSceneSubTrack / UMovieSceneCinematicShotTrack

UMovieSceneSection (Section 베이스 — Track 안 시간 구간)
├── UMovieSceneFloatSection
├── UMovieSceneAudioSection
├── UMovieScene3DTransformSection
├── UMovieSceneSkeletalAnimationSection
└── ... (각 Track 당 1+ Section 타입)
```

---

## 2. UMovieSceneSequence 핵심 virtual [verified — LevelSequence.h:38-83]

```cpp
class UMovieSceneSequence : public UObject
{
public:
    // [1] MovieScene 접근 (의무)
    virtual UMovieScene* GetMovieScene() const = 0;

    // [2] Binding (Possessable / Spawnable)
    virtual void BindPossessableObject(const FGuid& ObjectId,
                                        UObject& PossessedObject,
                                        UObject* Context) = 0;
    virtual bool CanPossessObject(UObject& Object, UObject* InPlaybackContext) const;
    virtual FGuid FindBindingFromObject(UObject* InObject, UObject* Context) const;
    virtual UObject* GetParentObject(UObject* Object) const;
    virtual void UnbindPossessableObjects(const FGuid& ObjectId);
    virtual void GatherExpiredObjects(const FMovieSceneObjectCache& InObjectCache,
                                       TArray<FGuid>& OutInvalidIDs) const;

    // [3] Spawnable 지원
    virtual bool AllowsSpawnableObjects() const;
    virtual UObject* MakeSpawnableTemplateFromInstance(UObject& InSourceObject, FName ObjectName);

    // [4] Director 통합
    virtual UObject* CreateDirectorInstance(TSharedRef<const FSharedPlaybackState> SharedPlaybackState,
                                             FMovieSceneSequenceID SequenceID);

    // [5] Track 지원 검증
    virtual ETrackSupport IsTrackSupportedImpl(TSubclassOf<UMovieSceneTrack> InTrackClass) const;

    // [6] 5.x 신규 — Custom Binding
    virtual bool AllowsCustomBindings() const;
    virtual const FMovieSceneBindingReferences* GetBindingReferences() const;

    // [7] Animation 호환
    virtual bool CanAnimateObject(UObject& InObject) const;
};
```

> **검증**: `LevelSequence.h:43-67` — ULevelSequence 가 위 14 virtual 모두 override.

---

## 3. UMovieScene 핵심 [verified — MovieScene.h]

```cpp
class UMovieScene : public UMovieSceneSignedObject
{
public:
    // === 핵심 멤버 (UPROPERTY) ===

    // 1. Track 컨테이너
    UPROPERTY()
    TArray<TObjectPtr<UMovieSceneTrack>> Tracks;

    // 2. Possessable / Spawnable Binding
    UPROPERTY()
    TArray<FMovieScenePossessable> Possessables;
    UPROPERTY()
    TArray<FMovieSceneSpawnable> Spawnables;

    // 3. CameraCut 마스터 트랙 (특수)
    UPROPERTY(Instanced)
    TObjectPtr<UMovieSceneTrack> CameraCutTrack;

    // 4. Settings
    UPROPERTY()
    FMovieSceneEditorData EditorData;
    UPROPERTY()
    FFrameRate TickResolution;       // 평가 해상도 (보통 24000)
    UPROPERTY()
    FFrameRate DisplayRate;          // 표시 fps (24 / 30 / 60)
    UPROPERTY()
    FMovieSceneNodeGroupCollection NodeGroups;

    // 5. Playback Range
    UPROPERTY()
    FMovieSceneFrameRange PlaybackRange;
    UPROPERTY()
    FMovieSceneFrameRange WorkingRange;
    UPROPERTY()
    FMovieSceneFrameRange ViewRange;

    // === 핵심 API ===
    MOVIESCENE_API const TArray<UMovieSceneTrack*>& GetTracks() const;
    MOVIESCENE_API bool AddGivenTrack(UMovieSceneTrack* Track, const FGuid& ObjectGuid);
    MOVIESCENE_API bool RemoveTrack(UMovieSceneTrack& Track);
    MOVIESCENE_API const TArray<FMovieScenePossessable>& GetPossessables() const;
    MOVIESCENE_API const TArray<FMovieSceneSpawnable>& GetSpawnables() const;
    MOVIESCENE_API TRange<FFrameNumber> GetPlaybackRange() const;
};
```

---

## 4. UMovieSceneTrack 핵심 virtual [verified — MovieSceneTrack.h:312-587]

```cpp
class UMovieSceneTrack : public UMovieSceneSignedObject
{
public:
    // === PURE_VIRTUAL (의무 override) ===
    virtual bool IsEmpty() const PURE_VIRTUAL(UMovieSceneTrack::IsEmpty, return true;);
    virtual bool SupportsType(TSubclassOf<UMovieSceneSection> SectionClass) const PURE_VIRTUAL(SupportsType, return false;);
    virtual UMovieSceneSection* CreateNewSection() PURE_VIRTUAL(CreateNewSection, return nullptr;);
    virtual const TArray<UMovieSceneSection*>& GetAllSections() const PURE_VIRTUAL(GetAllSections, static TArray<UMovieSceneSection*> Empty; return Empty;);
    virtual bool HasSection(const UMovieSceneSection& Section) const PURE_VIRTUAL(HasSection, return false;);
    virtual FText GetDisplayName() const PURE_VIRTUAL(GetDisplayName, return FText::FromString(TEXT("Unnamed")););

    // === virtual (선택 override) ===
    virtual int8 GetEvaluationFieldVersion() const { return 0; }
    virtual bool PopulateEvaluationTree(TMovieSceneEvaluationTree<FMovieSceneTrackEvaluationData>& OutData) const;
    virtual void PreCompileImpl(FMovieSceneTrackPreCompileResult& OutPreCompileResult);
    virtual void OnAddedToMovieSceneImpl(UMovieScene* InMovieScene);
    virtual void OnRemovedFromMovieSceneImpl();
    virtual void RemoveAllAnimationData() {}
    virtual bool SupportsMultipleRows() const;
    virtual EMovieSceneTrackEasingSupportFlags SupportsEasing(FMovieSceneSupportsEasingParams& Params) const;
    virtual void SetSectionToKey(UMovieSceneSection* InSection) {};
    virtual UMovieSceneSection* GetSectionToKey() const { return nullptr; }
    virtual FName GetTrackName() const { return NAME_None; }
    virtual void OnSectionAddedImpl(UMovieSceneSection* Section);
    virtual void OnSectionRemovedImpl(UMovieSceneSection* Section);
    virtual FText GetTrackRowDisplayName(int32 RowIndex) const;
};
```

### 4.1 Custom Track 작성 표준 (의무 6 virtual)

```cpp
UCLASS()
class UMyMovieSceneTrack : public UMovieSceneTrack
{
    GENERATED_BODY()

    UPROPERTY()
    TArray<TObjectPtr<UMovieSceneSection>> Sections;

public:
    // [1] PURE_VIRTUAL 의무 — 6개
    virtual bool IsEmpty() const override { return Sections.IsEmpty(); }
    virtual bool SupportsType(TSubclassOf<UMovieSceneSection> SectionClass) const override
    {
        return SectionClass == UMyMovieSceneSection::StaticClass();
    }
    virtual UMovieSceneSection* CreateNewSection() override
    {
        return NewObject<UMyMovieSceneSection>(this, NAME_None, RF_Transactional);
    }
    virtual const TArray<UMovieSceneSection*>& GetAllSections() const override
    {
        return reinterpret_cast<const TArray<UMovieSceneSection*>&>(Sections);
    }
    virtual bool HasSection(const UMovieSceneSection& Section) const override
    {
        return Sections.Contains(&Section);
    }
#if WITH_EDITORONLY_DATA
    virtual FText GetDisplayName() const override { return FText::FromString(TEXT("My Track")); }
#endif

    // [2] Section 추가/제거
    void AddSection(UMovieSceneSection& Section)
    {
        Sections.Add(&Section);
        OnSectionAddedImpl(&Section);
    }
};
```

---

## 5. UMovieSceneSection 핵심 [verified — MovieSceneSection.h:318-695]

```cpp
class UMovieSceneSection : public UMovieSceneSignedObject
{
public:
    // === 범위 관리 ===
    UPROPERTY()
    FMovieSceneSectionEvalOptions EvalOptions;
    UPROPERTY()
    FMovieSceneFrameRange SectionRange;       // [Start, End] FrameNumber

    virtual void SetRange(const TRange<FFrameNumber>& NewRange);
    virtual void SetBlendType(EMovieSceneBlendType InBlendType);

    // === 블렌딩 ===
    UPROPERTY()
    EMovieSceneBlendType BlendType;           // Absolute / Additive / Relative

    // === Easing (5.x) ===
    UPROPERTY()
    FMovieSceneEasingSettings Easing;

    // === Channel API (Float/Vector/Color 등 키프레임 데이터) ===
    virtual void GetSnapTimes(TArray<FFrameNumber>& OutSnapTimes, bool bGetSectionBorders) const;
    virtual const UMovieSceneSection* OverlapsWithSections(const TArray<UMovieSceneSection*>& Sections,
                                                            int32 TrackDelta = 0,
                                                            int32 TimeDelta = 0) const;
    virtual void InitialPlacement(const TArray<UMovieSceneSection*>& Sections,
                                   FFrameNumber InStartTime, int32 InDuration, bool bAllowMultipleRows);
    virtual void InitialPlacementOnRow(...);

    // === Time Warp (5.x) ===
    virtual FMovieSceneTimeWarpVariant* GetTimeWarp();

    // === Easing / Weight ===
    virtual float GetTotalWeightValue(FFrameTime InTime) const;

    // === Binding ===
    virtual void OnBindingIDsUpdated(const TMap<FFixedObjectBindingID, FFixedObjectBindingID>& OldFixedToNewFixedMap,
                                      FMovieSceneSequenceID LocalSequenceID,
                                      TSharedRef<FSharedPlaybackState> SharedPlaybackState);
    virtual void GetReferencedBindings(TArray<FGuid>& OutBindings);

#if WITH_EDITOR
    virtual UObject* GetSourceObject() const { return nullptr; }
    virtual bool ShowCurveForChannel(const void* Channel) const { return true; }
#endif
};
```

### 5.1 EMovieSceneBlendType

| Type | 설명 |
|------|------|
| `Absolute` | 절대 값 — 다른 트랙 무시 |
| `Additive` | 가산 — 다른 트랙 값에 더함 |
| `Relative` | 상대 — Initial 값 기준 오프셋 |
| `AbsoluteFromAdditive` | 5.x 신규 |
| `AdditiveFromBase` | 5.x 신규 |

---

## 6. FFrameNumber + FFrameRate 표준

```cpp
// 5.x 표준 — 정수 프레임 + 분리된 Rate
struct FFrameNumber
{
    int32 Value;                          // 정수 프레임
};

struct FFrameRate
{
    int32 Numerator   = 24000;            // TickResolution 기본
    int32 Denominator = 1;
};

// 변환 — 의무
const FFrameRate TickRes = MovieScene->GetTickResolution();   // 보통 24000
const FFrameRate DisplayRate = MovieScene->GetDisplayRate(); // 보통 24/30/60 fps

// 시간 → FrameNumber
FFrameNumber FrameAt2Sec = (TickRes * 2.0).RoundToFrame();

// FrameNumber → 시간 (초)
double Seconds = FrameAt2Sec / TickRes;

// Display fps 환산
FFrameNumber DisplayFrame = FFrameRate::TransformTime(
    FFrameTime(FrameAt2Sec), TickRes, DisplayRate).GetFrame();
```

> 🚨 **float 시간 사용 X** — TickResolution 누락 시 정밀도 손실 (24fps = 1/24 = 0.041666... 무한 소수).

---

## 7. Binding (Possessable vs Spawnable) [verified]

| 구분 | Possessable | Spawnable |
|------|-------------|-----------|
| 정의 | Sequence **외부 Actor** 바인딩 | Sequence 가 **직접 Spawn** |
| Lifetime | Sequence 외부 (Level 안 Actor) | Sequence Play 동안만 |
| `FGuid` | `FMovieScenePossessable` | `FMovieSceneSpawnable` |
| 사용 시점 | 게임 캐릭터 / 환경 액터 시퀀스 통합 | 컷씬 전용 액터 (촛불 / 임시 효과) |
| 메모리 | 외부 Actor 메모리 사용 | Sequence 가 NewObject (Transient) |

### 7.1 Possessable 바인딩 코드

```cpp
// LevelSequence::BindPossessableObject (LevelSequence.h:43)
void ULevelSequence::BindPossessableObject(const FGuid& ObjectId,
                                            UObject& PossessedObject,
                                            UObject* Context)
{
    // 1. BindingReferences 안 액터 등록
    BindingReferences.AddBinding(ObjectId, &PossessedObject, Context);
}
```

---

## 8. Sub Sequence (시퀀스 안 시퀀스) [grep-listed]

```cpp
// UMovieSceneSubTrack — 다른 Sequence 를 트랙으로 포함
// 자세한 API = MovieSceneSubTrack.h
class UMovieSceneSubTrack : public UMovieSceneTrack
{
    UPROPERTY()
    TArray<TObjectPtr<UMovieSceneSection>> SubSections;
    // SubSection.SubSequence = 자식 Sequence 참조
};

// 사용
ULevelSequence* MainSeq = ...;
ULevelSequence* SubSeq  = ...;

UMovieSceneSubTrack* SubTrack = MainSeq->GetMovieScene()->AddTrack<UMovieSceneSubTrack>();
UMovieSceneSubSection* Section = Cast<UMovieSceneSubSection>(SubTrack->CreateNewSection());
Section->SetSequence(SubSeq);
Section->SetRange(TRange<FFrameNumber>(StartFrame, EndFrame));
SubTrack->AddSection(*Section);
```

---

## 9. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Custom Track 6 PURE_VIRTUAL 누락 → 컴파일 실패 | IsEmpty / SupportsType / CreateNewSection / GetAllSections / HasSection / GetDisplayName 모두 override |
| 2 | `GetDisplayName()` Runtime 모듈 안 (Editor 데이터) | `#if WITH_EDITORONLY_DATA` 가드 |
| 3 | float 시간 사용 → 24fps 정밀도 손실 | `FFrameNumber` + `FFrameRate` 변환 |
| 4 | Section `SetRange` 후 `OnSectionAddedImpl` 호출 누락 | `AddSection` 표준 헬퍼 사용 |
| 5 | `SectionToKey` 미설정 → Editor 키 추가 시 잘못된 Section | `SetSectionToKey` virtual override |
| 6 | Possessable / Spawnable 혼동 | 외부 Actor = Possessable / 일회용 = Spawnable |
| 7 | Sub Sequence 안 Loop = 외부 Sequence 도 Loop 추측 | Sub Sequence Loop 분리 가능 |
| 8 | UMovieScene Possessables / Spawnables 직접 수정 | `AddPossessable` / `AddSpawnable` API 사용 |
| 9 | Track 안 Section 직접 NewObject | `Track->CreateNewSection()` 표준 패턴 |
| 10 | 5.x ECS — Render Thread 안 평가 추측 | Game Thread 안에서만 |

---

## 10. 체크리스트

- [ ] Custom Track = 6 PURE_VIRTUAL 모두 override
- [ ] `GetDisplayName` / `GetTrackRowDisplayName` = `#if WITH_EDITORONLY_DATA` 가드
- [ ] `CreateNewSection` = `NewObject` + `RF_Transactional` flag
- [ ] `FFrameNumber` 사용 — float 시간 X
- [ ] `TickResolution` / `DisplayRate` 명시 — `MovieScene->GetTickResolution()` 호출
- [ ] Possessable / Spawnable 결정 (외부 Actor / 일회용)
- [ ] Sub Sequence 사용 시 Loop / Time Scale 명시
- [ ] Render Thread 접근 X — Game Thread 전용
- [ ] Section `SetRange` + `BlendType` + `Easing` 명시
- [ ] `OnSectionAddedImpl` / `OnSectionRemovedImpl` virtual override (필요 시)

---

## 11. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| UMovieSceneSequence 14 virtual | **[verified]** ✅ | `LevelSequence.h:43-67` (override 14건 확인) |
| UMovieSceneTrack PURE_VIRTUAL 6종 | **[verified]** ✅ | `MovieSceneTrack.h:388, 481, 522, 529, 537, 575` |
| UMovieSceneSection virtual | **[verified]** ✅ | `MovieSceneSection.h:318, 447, 509, 520, 567, 577, 587` |
| UMovieScene 멤버 / API | **[verified]** ✅ | `MovieScene.h` 안 grep |
| 5.x ECS 평가 흐름 (Instantiation → Evaluation → Blending → Application) | **[grep-listed]** ⚠ | `MovieScene/Public/EntitySystem/` 64 헤더 존재 |
| EMovieSceneBlendType 5종 | **[inferred]** ❌ | UE 일반 — `MovieSceneBlendType.h` grep 필요 |
| Sub Sequence API 패턴 | **[grep-listed]** ⚠ | `MovieSceneSubTrack.h` 파일 존재 / 본문 미상세 |

---

## 12. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인
- ⭐ [`./Tracks.md`](./Tracks.md) — 빌트인 트랙 43종 카테고리
- ⭐ [`./LevelSequencePlayer.md`](./LevelSequencePlayer.md) — 런타임 재생 표준
- [`./EntitySystemECS.md`](./EntitySystemECS.md) — 5.x ECS 평가 (성능 깊이)
- [`./Sequencer.md`](./Sequencer.md) — Editor 측 (커스텀 트랙 UI)
- 🚨 [`../../../references/05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md)
- 🚨 [`../../../references/07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)

---

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **UMovieSceneSequence 14 virtual** [verified] + **UMovieSceneTrack 6 PURE_VIRTUAL** + **UMovieSceneSection virtual** + **UMovieScene 멤버 / API** + **Custom Track 작성 표준** + **FFrameNumber/FFrameRate 표준** + **Possessable vs Spawnable** + **Sub Sequence** + 함정 10대 + 체크리스트 10개 + 신뢰도 태그 7종. Engine 5.5.4 grep 검증 — LevelSequence.h:43-67 / MovieSceneTrack.h:388-575 / MovieSceneSection.h:318-695. |
