---
type: source
title: "UE LevelSequence — LevelSequencePlayer (런타임 재생 표준 ⭐⭐⭐)"
slug: ue-levelsequence-levelsequenceplayer
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/LevelSequencePlayer.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-15
related_entities:
  - "[[entities/AActor]]"
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, levelsequence, runtime-playback, enriched, verified]
citation_disclosure: "🟢 16 / 🟡 1 / 🔴 0 · raw verified Engine 5.7.4 · Cycle #13.1 enrich"
---

# UE LevelSequence — LevelSequencePlayer ⭐⭐⭐

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/LevelSequencePlayer.md]] (501L)
> Parent: [[sources/ue-levelsequence-skill]]
> 위치: `Engine/Source/Runtime/LevelSequence/Public/LevelSequencePlayer.h:27,105,113` + `MovieSceneSequencePlayer.h:192-382` (30+ UFUNCTION)
> **런타임 컷씬 재생의 표준 진입점**.

## 1. Summary

🟢 `ALevelSequenceActor` (Level 안 배치 또는 `CreateLevelSequencePlayer` 정적 헬퍼로 동적 생성) + `ULevelSequencePlayer` (재생 컴포넌트). 직접 NewObject 금지 — Actor 가 Player 라이프타임 소유. `UMovieSceneSequencePlayer` 베이스 30+ UFUNCTION (Play / Pause / Stop / GoTo / Scrub / PlayTo / SetPlaybackPosition / 5종 콜백). 5.x ECS 평가 + Replication + Possessable Binding 동적 교체 지원.

## 2. Key claims

### 2.1 ALevelSequenceActor 8 핵심 필드 🟢 (raw L29-99)

```cpp
UCLASS(hideCategories=(Rendering, Physics, LOD, Activation, Input))
class ALevelSequenceActor : public AActor
{
    UPROPERTY(EditAnywhere, replicated, BlueprintReadOnly, meta=(ExposeOnSpawn))
    TObjectPtr<ULevelSequence> LevelSequenceAsset;            // [1] Sequence 어셋

    UPROPERTY(Instanced, transient, replicated, BlueprintGetter=GetSequencePlayer)
    TObjectPtr<ULevelSequencePlayer> SequencePlayer;          // [2] Player — Instanced+Transient

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FMovieSceneSequencePlaybackSettings PlaybackSettings;     // [3] Playback Settings

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FLevelSequenceCameraSettings CameraSettings;              // [4] Camera (자동 cut)

    UPROPERTY(config, EditAnywhere) bool bUseBurnIn;           // [5] BurnIn (TC/Frame)
    UPROPERTY(Instanced) TObjectPtr<ULevelSequenceBurnIn> BurnInInstance;

    UPROPERTY(EditAnywhere, BlueprintSetter=SetReplicatePlayback)
    bool bReplicatePlayback;                                   // [7] Replication

    UPROPERTY(BlueprintReadOnly) FLevelSequenceBindingReferences BindingOverrides; // [8]
};
```

### 2.2 핵심 API 🟢 (raw L72-99)

| API | 시그니처 / 용도 |
|-----|----------------|
| `GetSequencePlayer()` | BP — Player 접근 (직접 NewObject X) |
| `SetSequence(ULevelSequence*)` | BP — sequence 교체 |
| `SetBinding(BindingID, Actors[])` | Possessable Actor 전체 교체 |
| `AddBinding(BindingID, Actor)` | Possessable Actor 추가 |
| `RemoveBinding(BindingID, Actor)` | 제거 |
| `ResetBinding(BindingID)` | 초기화 |
| `SetReplicatePlayback(bool)` | Multiplayer 동기 활성 |

### 2.3 UMovieSceneSequencePlayer 30+ UFUNCTION 🟢 (raw L138-160 §3)

| 카테고리 | API |
|---------|-----|
| **재생 제어** | `Play()` · `PlayReverse()` · `PlayLooping(NumLoops=-1)` · `Pause()` · `Stop()` · `StopAtCurrentTime()` · `GoToEndAndStop()` · `Scrub()` |
| **시간 이동** | `PlayTo(PlaybackParams, PlayToParams)` · `SetPlaybackPosition(PlaybackParams)` |
| **상태 조회** | `IsPlaying()` · `IsPaused()` · `GetCurrentTime() → FQualifiedFrameTime` · `GetDuration() → FQualifiedFrameTime` · `GetPlaybackSpeed()` / `SetPlaybackSpeed(float)` |
| **범위** | `SetPlayRange(FFrameNumber Start, End)` · `SetPlayRangeInSeconds(float, float)` |

### 2.4 콜백 5종 🟢 (raw §3 + ULevelSequencePlayer.h:113)

```cpp
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLevelSequencePlayerCameraCutEvent,
                                            UCameraComponent*, CameraComponent);
UPROPERTY(BlueprintAssignable) FOnLevelSequencePlayerCameraCutEvent OnCameraCut;

// 베이스 콜백 (UMovieSceneSequencePlayer)
OnPlay         // 시퀀스 시작
OnPause        // pause 진입
OnStop         // stop 진입
OnFinished     // 시퀀스 자연 종료 (Loop -1 = 호출 X)
OnCameraCut    // 카메라 컷 변경 시점 (Game Thread)
```

### 2.5 표준 패턴 1 — Level 배치 + Auto-Play 🟢 (raw §4)

```cpp
// 1) Level Editor 에서 ALevelSequenceActor drag-drop + Details:
//    - LevelSequenceAsset = IntroCutscene
//    - PlaybackSettings.bAutoPlay = true
// 2) 게임 트리거 시 Tag 매칭 검색
void AMyCtrl::OnEnterZone()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyCtrl::OnEnterZone);
    for (TActorIterator<ALevelSequenceActor> It(GetWorld()); It; ++It)
    {
        if (It->ActorHasTag(TEXT("IntroCutscene")))
        {
            if (auto* P = It->GetSequencePlayer())
            {
                P->OnFinished.AddDynamic(this, &AMyCtrl::OnFinished);
                P->Play();
            }
            break;
        }
    }
}
```

> ⚠ `TActorIterator` 매 프레임 사용 금지 — 한 번만 + Tag Map 캐싱.

### 2.6 표준 패턴 2 — 런타임 동적 생성 + Soft Reference 🟢 (raw §5)

```cpp
UPROPERTY(EditAnywhere, Category="Cutscene")
TSoftObjectPtr<ULevelSequence> CutsceneSeq;

TWeakObjectPtr<ALevelSequenceActor> SpawnedActor;
TSharedPtr<FStreamableHandle> AsyncHandle;

void PlayCutscene()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(PlayCutscene);
    if (CutsceneSeq.IsNull()) return;
    AsyncHandle = UAssetManager::GetStreamableManager().RequestAsyncLoad(
        CutsceneSeq.ToSoftObjectPath(),
        FStreamableDelegate::CreateWeakLambda(this,
            [WeakThis = TWeakObjectPtr<AMyTrigger>(this)]()
            { if (WeakThis.IsValid()) WeakThis->OnCutsceneLoaded(); })
    );
}

void OnCutsceneLoaded()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(OnCutsceneLoaded);
    if (auto* L = CutsceneSeq.Get(); IsValid(L))
    {
        FMovieSceneSequencePlaybackSettings S; S.bAutoPlay = true; S.LoopCount.Value = 0;
        ALevelSequenceActor* Out = nullptr;
        auto* P = ULevelSequencePlayer::CreateLevelSequencePlayer(GetWorld(), L, S, Out);
        if (P && Out)
        {
            SpawnedActor = Out;
            P->OnFinished.AddDynamic(this, &AMyTrigger::OnFinished);
        }
    }
}

virtual void EndPlay(const EEndPlayReason::Type R) override
{
    TRACE_CPUPROFILER_EVENT_SCOPE(EndPlay);
    if (AsyncHandle.IsValid()) { AsyncHandle->CancelHandle(); AsyncHandle.Reset(); }
    Super::EndPlay(R);
}
```

### 2.7 표준 패턴 3 — Possessable Binding 동적 교체 🟢 (raw §6)

```cpp
// Player 캐릭터를 시퀀스 안 등장시키기
void AMyGM::StartIntroCutscene(APlayerController* PC)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(StartIntroCutscene);
    APawn* Pawn = PC->GetPawn();
    if (!IsValid(Pawn)) return;

    ALevelSequenceActor* C = FindCutsceneByTag(TEXT("IntroCutscene"));
    if (!IsValid(C)) return;

    // Sequencer 에디터에서 미리 만든 Binding ID
    FMovieSceneObjectBindingID PlayerBinding;
    PlayerBinding.SetGuid(FGuid(TEXT("ABCDEF...")));   // BP 자산 권장
    C->AddBinding(PlayerBinding, Pawn);
    C->GetSequencePlayer()->Play();
}
```

### 2.8 FMovieSceneSequencePlaybackSettings 11 필드 🟡 (raw §7)

```cpp
USTRUCT(BlueprintType) struct FMovieSceneSequencePlaybackSettings
{
    float PlayRate = 1.0f;                    // 재생 속도
    int32 StartTime = 0;                      // 시작 프레임
    FMovieSceneSequenceLoopCount LoopCount;   // 0=1회 / -1=무한 / N=N회
    bool bRandomStartTime;
    bool bRestoreState;                       // 종료 시 원래 상태 복원
    bool bDisableMovementInput;               // 재생 중 이동 입력 차단
    bool bDisableLookAtInput;                 // 카메라 입력 차단
    bool bHidePlayer;                         // 플레이어 캐릭터 숨김
    bool bHideHud;                            // HUD 숨김
    bool bPauseAtEnd;                         // 끝에서 Pause (Stop 대신)
    bool bAutoPlay = false;                   // BeginPlay 자동 재생
};
```

### 2.9 Replication 의무 🟢 (raw §8.5)

- `bReplicatePlayback = true` (Editor Details 또는 `SetReplicatePlayback`)
- Server authoritative — `HasAuthority()` 검사 후 `Play()` 호출
- 클라이언트 측 호출 시 desync — 서버 측 명령만 replicate
- Frame position smooth interpolated (latency hide)

### 2.10 5 시나리오 🟢 (raw §8)

| # | 시나리오 | 핵심 |
|---|---------|------|
| 1 | 게임 인트로 (Auto-Play) | `bAutoPlay=true` + `bHidePlayer=true` + `bHideHud=true` |
| 2 | 트리거 박스 컷씬 | `NotifyActorBeginOverlap` → `PlayCutscene` |
| 3 | 게임 종료 시퀀스 | `PlayTo({FFrameNumber, EUpdatePositionMethod::Play}, ToParams)` |
| 4 | 다이얼로그 (Sub Sequence) | MainSequence 안 SubTrack — 코드 X |
| 5 | 멀티플레이어 동기 | `bReplicatePlayback=true` + `HasAuthority()` |

## 3. 함정 12 🟢 (raw §9)

| # | 함정 | 정답 |
|---|------|------|
| 1 | `ULevelSequencePlayer` 직접 NewObject | `ALevelSequenceActor::SequencePlayer` 또는 `CreateLevelSequencePlayer` |
| 2 | LevelSequence Hard Reference | `TSoftObjectPtr<ULevelSequence>` + Async ([[concepts/Asset-Loading-Policy]]) |
| 3 | 매 프레임 `Play()` → 재시작 폭주 | `IsPlaying()` 검사 |
| 4 | `OnFinished` AddDynamic 후 RemoveDynamic 누락 | EndPlay 안 페어 |
| 5 | TActorIterator 매 프레임 | 1회 + `UWorldSubsystem` 캐싱 |
| 6 | `bDisableMovementInput` 후 OnFinished 안 EnableInput 누락 | 콜백 안 복원 |
| 7 | Replicated 시퀀스 클라이언트 Play | `HasAuthority()` 검사 |
| 8 | Possessable Binding Guid 하드코딩 | BP 자산 + 이름 매칭 |
| 9 | Cooked 안 BP Director 누락 | Cooked Test 의무 |
| 10 | Async Handle 누락 → 메모리 누수 | EndPlay 안 `Cancel/Release` |
| 11 | `OnCameraCut` Render Thread 추측 | Game Thread 호출 |
| 12 | Spawnable Actor 외부 Destroy → 크래시 | Sequence 가 lifetime 관리 |

## 4. 체크리스트 🟢 (raw §10)

- [ ] LevelSequence = `TSoftObjectPtr` + Async Load
- [ ] `ULevelSequencePlayer` = Actor 통한 접근 (직접 NewObject X)
- [ ] `OnFinished` / `OnPlay` / `OnCameraCut` BeginPlay 등록 + EndPlay 해제
- [ ] 모든 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] `IsPlaying()` 검사 후 `Play()` 호출
- [ ] `bDisableMovementInput` 시 OnFinished 안 EnableInput 복원
- [ ] Replicated = `HasAuthority()` + `bReplicatePlayback=true`
- [ ] Possessable Binding = BP 자산 (Guid 하드코딩 X)
- [ ] EndPlay 안 Async Handle Cancel/Release
- [ ] FFrameNumber 사용 (float 시간 X)
- [ ] Cooked Build 검증 — Director BP 동작 확인

## 5. 신뢰도 🟢 (raw §11)

| 항목 | tier | 출처 |
|------|------|------|
| ALevelSequenceActor 멤버/API | 🟢 verified | `LevelSequenceActor.h:38-213` |
| ULevelSequencePlayer + OnCameraCut | 🟢 verified | `LevelSequencePlayer.h:27,105,113` |
| UMovieSceneSequencePlayer 30+ API | 🟢 verified | `MovieSceneSequencePlayer.h:192-382` |
| FMovieSceneSequencePlaybackSettings 필드 | 🟡 grep-listed | USTRUCT 일반 패턴 |
| CreateLevelSequencePlayer 정적 헬퍼 | 🟢 verified | `LevelSequencePlayer.h:105` |
| AddBinding/RemoveBinding/SetBinding/ResetBinding | 🟢 verified | `LevelSequenceActor.h:177-213` |
| bReplicatePlayback Replication | 🟢 verified | `LevelSequenceActor.h:116` replicated |

## 6. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 베이스: [[sources/ue-levelsequence-moviescene]] (`UMovieSceneSequence` + `UMovieSceneSequencePlayer`)
- 페어: [[sources/ue-levelsequence-tracks]] · [[sources/ue-levelsequence-director]] (BP Event Track) · [[sources/ue-levelsequence-cinecamera]] (CameraCut) · [[sources/ue-levelsequence-templatesequence]] (재사용)
- 정책: 🚨 [[concepts/Profiling-Scope-Rule]] · 🚨 [[concepts/Asset-Loading-Policy]] · 🚨 [[concepts/Component-Policies-6]]
- 페어 Actor: [[entities/AActor]] (BeginPlay/EndPlay 페어)
