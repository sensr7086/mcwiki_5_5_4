---
name: levelsequence-player
description: ALevelSequenceActor + ULevelSequencePlayer 런타임 재생 표준 ⭐⭐⭐ — Play/Pause/Stop/GoTo + BP API + OnCameraCut/OnFinished/OnPlay 콜백 + Replication + 어셋 로드 정책 + AOE/Cutscene 시나리오. UMovieSceneSequencePlayer 베이스 API 30+ 메소드.
---

# LevelSequence/LevelSequencePlayer — 런타임 재생 표준 ⭐⭐⭐

> **위치 (verified)**:
> - **ALevelSequenceActor** — `Engine/Source/Runtime/LevelSequence/Public/LevelSequenceActor.h`
> - **ULevelSequencePlayer** — `Engine/Source/Runtime/LevelSequence/Public/LevelSequencePlayer.h:27, 105, 113`
> - **UMovieSceneSequencePlayer** (베이스) — `Engine/Source/Runtime/MovieScene/Public/MovieSceneSequencePlayer.h:192-382` (30+ UFUNCTION)
>
> **요지**: **런타임 컷씬 재생의 표준 진입점**. `ALevelSequenceActor` = Level 안 배치 + `ULevelSequencePlayer` = 재생 컴포넌트. 직접 NewObject X — Actor 통한 접근.

---

## 🚨 공통 정책 (의무)

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule`](../../../references/07_ProfilingScopeRule.md) | 모든 시퀀스 콜백 (OnCameraCut/OnFinished/OnPlay) 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| 🚨 [`11_AssetLoadingPolicy §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-) | Runtime = `TSoftObjectPtr<ULevelSequence>` + Async (LevelSequence 어셋 무거움 — 수십 MB 가능) |
| 🚨 Lifetime | `ULevelSequencePlayer` = `UPROPERTY(Instanced, Transient)` — Actor 가 소유, 직접 NewObject X |
| 🚨 [`10_ComponentPolicies §3`](../../../references/10_ComponentPolicies.md) | Sequence 콜백 람다 안 `TWeakObjectPtr<this>` + IsValid |
| 🚨 Replication | 멀티플레이 = `bReplicatePlayback=true` 명시 + `bReplicates=true` |

---

## 1. ALevelSequenceActor 구조 [verified — LevelSequenceActor.h]

```cpp
UCLASS(hideCategories=(Rendering, Physics, LOD, Activation, Input))
class ALevelSequenceActor : public AActor
{
public:
    // [1] 핵심 — Sequence 어셋 (Soft Reference)
    UPROPERTY(EditAnywhere, replicated, BlueprintReadOnly,
              Category="General", meta=(AllowedClasses="/Script/LevelSequence.LevelSequence", ExposeOnSpawn))
    TObjectPtr<ULevelSequence> LevelSequenceAsset;     // 또는 SoftPtr 권장

    // [2] Player (Instanced + Transient — 직접 NewObject 금지)
    UPROPERTY(Instanced, transient, replicated, BlueprintReadOnly,
              BlueprintGetter=GetSequencePlayer, Category="Playback")
    TObjectPtr<ULevelSequencePlayer> SequencePlayer;

    // [3] Playback Settings
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Playback",
              meta=(ShowOnlyInnerProperties, ExposeOnSpawn))
    FMovieSceneSequencePlaybackSettings PlaybackSettings;

    // [4] Camera Settings (자동 카메라 cut 처리)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cameras",
              meta=(ShowOnlyInnerProperties, ExposeOnSpawn))
    FLevelSequenceCameraSettings CameraSettings;

    // [5] BurnIn (영상 출력 시 TC / Frame 정보)
    UPROPERTY(config, EditAnywhere, BlueprintReadWrite, Category="General")
    bool bUseBurnIn;
    UPROPERTY(Instanced, EditAnywhere, BlueprintReadWrite, Category="General",
              meta=(EditCondition=bUseBurnIn))
    TObjectPtr<ULevelSequenceBurnIn> BurnInInstance;

    // [6] Override Instance Data (Spawnable / Possessable replacement)
    UPROPERTY(Instanced, BlueprintReadWrite, Category="General")
    TObjectPtr<UMovieSceneSequencePlaybackSettings_DEPRECATED> DeprecatedPlaybackSettings;

    // [7] Replication
    UPROPERTY(EditAnywhere, DisplayName="Replicate Playback", BlueprintReadWrite,
              BlueprintSetter=SetReplicatePlayback, Category=Replication, meta=(ExposeOnSpawn))
    bool bReplicatePlayback;

    // [8] Bindings Override
    UPROPERTY(BlueprintReadOnly, Category="General")
    FLevelSequenceBindingReferences BindingOverrides;

public:
    // === API ===

    UFUNCTION(BlueprintCallable, Category="Sequencer|Player")
    ULevelSequencePlayer* GetSequencePlayer() const;

    UFUNCTION(BlueprintCallable, Category="Sequencer|Player")
    void SetSequence(ULevelSequence* InSequence);

    UFUNCTION(BlueprintSetter)
    void SetReplicatePlayback(bool bInReplicatePlayback);

    UFUNCTION(BlueprintCallable, Category = "Sequencer|Player|Bindings")
    void SetBinding(FMovieSceneObjectBindingID Binding, const TArray<AActor*>& Actors);

    UFUNCTION(BlueprintCallable, Category = "Sequencer|Player|Bindings")
    void AddBinding(FMovieSceneObjectBindingID Binding, AActor* Actor);

    UFUNCTION(BlueprintCallable, Category = "Sequencer|Player|Bindings")
    void RemoveBinding(FMovieSceneObjectBindingID Binding, AActor* Actor);

    UFUNCTION(BlueprintCallable, Category = "Sequencer|Player|Bindings")
    void ResetBinding(FMovieSceneObjectBindingID Binding);
};
```

---

## 2. ULevelSequencePlayer API [verified — LevelSequencePlayer.h]

```cpp
UCLASS(BlueprintType)
class ULevelSequencePlayer : public UMovieSceneSequencePlayer
{
public:
    // === BP 정적 헬퍼 (가장 자주 사용) ===
    UFUNCTION(BlueprintCallable, Category="Sequencer|Player",
              meta=(WorldContext="WorldContextObject", DynamicOutputParam="OutActor"))
    static ULevelSequencePlayer* CreateLevelSequencePlayer(
        UObject* WorldContextObject,
        ULevelSequence* LevelSequence,
        FMovieSceneSequencePlaybackSettings Settings,
        ALevelSequenceActor*& OutActor);

    // === Camera Cut Event (5.x) ===
    DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLevelSequencePlayerCameraCutEvent,
                                                  UCameraComponent*, CameraComponent);

    UPROPERTY(BlueprintAssignable, Category="Cinematic")
    FOnLevelSequencePlayerCameraCutEvent OnCameraCut;
};
```

---

## 3. UMovieSceneSequencePlayer 베이스 API 30+ [verified — :192-382]

| 카테고리 | API | 시그니처 |
|---------|-----|---------|
| **재생 제어** | `Play()` | `void Play()` |
| | `PlayReverse()` | `void PlayReverse()` |
| | `PlayLooping(NumLoops=-1)` | 무한 / 횟수 |
| | `Pause()` | 일시정지 |
| | `Stop()` | 정지 (Begin 으로) |
| | `StopAtCurrentTime()` | 현재 위치 정지 |
| | `GoToEndAndStop()` | 끝으로 (Adheres to 'When Finished') |
| | `Scrub()` | 스크럽 모드 |
| **시간 이동** | `PlayTo(PlaybackParams, PlayToParams)` | 지정 위치까지 |
| | `SetPlaybackPosition(PlaybackParams)` | 즉시 이동 |
| **상태 조회** | `IsPlaying()` | `bool` |
| | `IsPaused()` | `bool` |
| | `GetCurrentTime()` | `FQualifiedFrameTime` |
| | `GetDuration()` | `FQualifiedFrameTime` |
| | `GetPlaybackSpeed()` / `SetPlaybackSpeed(float)` | 재생 속도 |
| **범위** | `SetPlayRange(FFrameNumber Start, FFrameNumber End)` (Frames) | 범위 설정 |
| | `SetPlayRangeInSeconds(float Start, float End)` | Sec 단위 |
| **콜백 이벤트** | `OnPlay` | `FOnMovieSceneSequencePlayerEvent` |
| | `OnPause` | 동일 |
| | `OnStop` | 동일 |
| | `OnFinished` | 동일 (Loop 종료 X — 완전 종료 시) |

---

## 4. 표준 패턴 1 — Level 안 배치 (가장 흔함)

```cpp
// 1. Level Editor 에서 ALevelSequenceActor drag-drop
// 2. Details 패널 안 LevelSequenceAsset 설정 + PlaybackSettings 조정
// 3. BeginPlay 시 자동 재생 (PlaybackSettings.bAutoPlay=true) 또는 BP 트리거

// C++ 게임 트리거 — 자동 검색 후 재생
void AMyPlayerCharacter::OnEnterCutsceneZone()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyPlayerCharacter::OnEnterCutsceneZone);

    // Level 안 첫 LevelSequenceActor 검색 (또는 Tag 매칭 권장)
    for (TActorIterator<ALevelSequenceActor> It(GetWorld()); It; ++It)
    {
        if (It->ActorHasTag(TEXT("IntroCutscene")))
        {
            if (ULevelSequencePlayer* Player = It->GetSequencePlayer())
            {
                Player->OnFinished.AddDynamic(this, &AMyPlayerCharacter::OnCutsceneFinished);
                Player->Play();
            }
            break;
        }
    }
}

void AMyPlayerCharacter::OnCutsceneFinished()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyPlayerCharacter::OnCutsceneFinished);
    EnableInput(...);   // 플레이어 입력 복원
}
```

> ⚠ **`TActorIterator` 매 프레임 사용 X** — 처음 한 번만. 정기 사용 시 `UWorldSubsystem` 안 캐싱 ([`SpatialPartition/TOctree2`](../../SpatialPartition/references/TOctree2.md) 또는 Tag Map).

---

## 5. 표준 패턴 2 — 런타임 동적 생성 (Soft Reference)

```cpp
UCLASS()
class AMyCutsceneTrigger : public AActor
{
    GENERATED_BODY()

    // Soft Reference — 메모리 효율
    UPROPERTY(EditAnywhere, Category="Cutscene")
    TSoftObjectPtr<ULevelSequence> CutsceneSeq;

    UPROPERTY()
    TWeakObjectPtr<ALevelSequenceActor> SpawnedActor;

    TSharedPtr<FStreamableHandle> AsyncHandle;

    void PlayCutscene()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyCutsceneTrigger::PlayCutscene);
        if (CutsceneSeq.IsNull()) return;

        // [1] Async Load (LevelSequence 어셋 = 수십 MB 가능)
        FStreamableManager& SM = UAssetManager::GetStreamableManager();
        AsyncHandle = SM.RequestAsyncLoad(
            CutsceneSeq.ToSoftObjectPath(),
            FStreamableDelegate::CreateWeakLambda(this,
                [WeakThis = TWeakObjectPtr<AMyCutsceneTrigger>(this)]()
                {
                    if (WeakThis.IsValid())
                    {
                        WeakThis->OnCutsceneLoaded();
                    }
                })
        );
    }

    void OnCutsceneLoaded()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyCutsceneTrigger::OnCutsceneLoaded);
        ULevelSequence* Loaded = CutsceneSeq.Get();
        if (!IsValid(Loaded)) return;

        // [2] BP 정적 헬퍼로 Player + Actor 동시 생성
        FMovieSceneSequencePlaybackSettings Settings;
        Settings.bAutoPlay = true;
        Settings.LoopCount.Value = 0;       // 1회 재생

        ALevelSequenceActor* OutActor = nullptr;
        ULevelSequencePlayer* Player = ULevelSequencePlayer::CreateLevelSequencePlayer(
            GetWorld(), Loaded, Settings, OutActor);

        if (Player && OutActor)
        {
            SpawnedActor = OutActor;
            Player->OnFinished.AddDynamic(this, &AMyCutsceneTrigger::OnCutsceneFinished);
            Player->OnCameraCut.AddDynamic(this, &AMyCutsceneTrigger::OnCameraCutChanged);
        }
    }

    UFUNCTION()
    void OnCutsceneFinished()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyCutsceneTrigger::OnCutsceneFinished);

        // [3] Actor 정리 + Handle Release
        if (ALevelSequenceActor* Actor = SpawnedActor.Get())
        {
            Actor->Destroy();
        }
        if (AsyncHandle.IsValid())
        {
            AsyncHandle->ReleaseHandle();
            AsyncHandle.Reset();
        }
    }

    UFUNCTION()
    void OnCameraCutChanged(UCameraComponent* NewCamera)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyCutsceneTrigger::OnCameraCutChanged);
        // 카메라 컷 변경 — DoF / Effect 적용 가능
    }

    virtual void EndPlay(const EEndPlayReason::Type Reason) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMyCutsceneTrigger::EndPlay);
        if (AsyncHandle.IsValid())
        {
            AsyncHandle->CancelHandle();
            AsyncHandle.Reset();
        }
        Super::EndPlay(Reason);
    }
};
```

---

## 6. 표준 패턴 3 — Possessable Binding 동적 변경

게임 캐릭터를 시퀀스 안 바인딩 (예: 플레이어 캐릭터를 컷씬에 등장).

```cpp
void AMyGameMode::StartIntroCutscene(APlayerController* PC)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyGameMode::StartIntroCutscene);
    APawn* PlayerPawn = PC->GetPawn();
    if (!IsValid(PlayerPawn)) return;

    // 1. LevelSequenceActor 검색 (Tag 기반)
    ALevelSequenceActor* CutsceneActor = FindCutsceneByTag(TEXT("IntroCutscene"));
    if (!IsValid(CutsceneActor)) return;

    // 2. Possessable Binding 동적 교체
    //    PlayerCharacterBinding = Sequence 에디터에서 미리 만든 Binding ID
    FMovieSceneObjectBindingID PlayerBinding;
    PlayerBinding.SetGuid(FGuid(TEXT("ABCDEF123456...")));   // 또는 BP 자산에서 가져옴

    CutsceneActor->AddBinding(PlayerBinding, PlayerPawn);

    // 3. 재생
    if (ULevelSequencePlayer* Player = CutsceneActor->GetSequencePlayer())
    {
        Player->Play();
    }
}
```

---

## 7. FMovieSceneSequencePlaybackSettings 필드

```cpp
USTRUCT(BlueprintType)
struct FMovieSceneSequencePlaybackSettings
{
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float PlayRate = 1.0f;                    // 재생 속도

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 StartTime = 0;                      // 시작 프레임 (FFrameNumber)

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FMovieSceneSequenceLoopCount LoopCount;   // 0 = 1회 / -1 = 무한 / N = N회

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bRandomStartTime;                    // 랜덤 시작

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bRestoreState;                       // 종료 시 원래 상태 복원

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bDisableMovementInput;               // 재생 중 입력 차단

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bDisableLookAtInput;                 // 카메라 입력 차단

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bHidePlayer;                         // 플레이어 캐릭터 숨김

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bHideHud;                            // HUD 숨김

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bPauseAtEnd;                         // 끝에서 Pause (Stop 대신)

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bAutoPlay = false;                   // BeginPlay 자동 재생
};
```

---

## 8. 시나리오 5종

### 8.1 게임 인트로 컷씬 (Auto-Play)

```cpp
// Level 안 ALevelSequenceActor 배치 + Details 패널 설정:
// - LevelSequenceAsset = IntroCutscene
// - PlaybackSettings.bAutoPlay = true
// - PlaybackSettings.LoopCount.Value = 0
// - PlaybackSettings.bHidePlayer = true
// - PlaybackSettings.bHideHud = true
// → BeginPlay 자동 재생, OnFinished 콜백으로 정리
```

### 8.2 트리거 박스 컷씬 (PlayCutscene UI 미러링)

```cpp
void AMyTriggerBox::NotifyActorBeginOverlap(AActor* Other)
{
    if (Cast<APlayerController>(Other->GetInstigatorController()))
    {
        PlayCutscene();   // §5 표준 패턴 호출
    }
}
```

### 8.3 게임 종료 시퀀스 (PlayTo)

```cpp
// 특정 위치까지만 재생 후 정지
FMovieSceneSequencePlaybackParams StartParams;
StartParams.Frame.FrameNumber = FFrameNumber(0);

FMovieSceneSequencePlayToParams ToParams;
ToParams.bExclusive = false;

Player->SetPlaybackPosition(StartParams);
Player->PlayTo({FFrameNumber(150), EUpdatePositionMethod::Play}, ToParams);
```

### 8.4 다이얼로그 시스템 (Sub Sequence 토글)

```cpp
// MainSequence 안 SubSequence Track — 다이얼로그 별 별도 Sequence
// MainSequence 가 자동 SubSequence 호출 — 코드 없이 Sequencer 안 배치
```

### 8.5 멀티플레이어 동기 (Replicated)

```cpp
// ALevelSequenceActor::bReplicatePlayback = true 설정
// 서버에서 Play() 호출 시 모든 클라이언트 동기 재생
ALevelSequenceActor* Cutscene = FindCutsceneByTag(TEXT("Boss"));
Cutscene->SetReplicatePlayback(true);

if (HasAuthority())
{
    Cutscene->GetSequencePlayer()->Play();
}
```

---

## 9. 함정 & 안티패턴 (12종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | `ULevelSequencePlayer` 직접 NewObject | `ALevelSequenceActor::SequencePlayer` 또는 `CreateLevelSequencePlayer` 정적 헬퍼 |
| 2 | LevelSequence Hard Reference | `TSoftObjectPtr<ULevelSequence>` + Async ([`11_AssetLoadingPolicy`](../../../references/11_AssetLoadingPolicy.md)) |
| 3 | 매 프레임 `Play()` 호출 → 재시작 폭주 | `IsPlaying()` 검사 후 호출 |
| 4 | `OnFinished` AddDynamic 후 RemoveDynamic 누락 → EndPlay 시 댕글링 | EndPlay 안 RemoveDynamic 페어 |
| 5 | TActorIterator 매 프레임 검색 | `TActorIterator` = 처음 1회 / 정기 사용 = `UWorldSubsystem` 캐싱 |
| 6 | `bDisableMovementInput=true` 후 시퀀스 종료 입력 복원 누락 | OnFinished 안 `EnableInput` |
| 7 | Replicated 시퀀스 클라이언트 Play 호출 → 서버 동기 깨짐 | `HasAuthority()` 검사 + 서버에서만 Play |
| 8 | Possessable Binding 어셋 Guid 하드코딩 | BP 자산 + 이름 매칭 (`UMovieSceneBindingID`) |
| 9 | Cooked Build 안 BP Director 누락 | LevelSequence Director BP = Cooked 포함 검증 |
| 10 | LevelSequence 메모리 누수 (Async Handle 누락) | EndPlay 안 Handle Release |
| 11 | `OnCameraCut` Render Thread 호출 추측 | Game Thread 호출 |
| 12 | Spawnable 액터 Destroy 후 Sequence 재생 → 크래시 | Spawnable = Sequence 가 lifetime 관리 (외부 Destroy X) |

---

## 10. 체크리스트

- [ ] LevelSequence 어셋 = `TSoftObjectPtr` + Async Load
- [ ] `ULevelSequencePlayer` = Actor 통한 접근 (직접 NewObject X)
- [ ] `OnFinished` / `OnPlay` / `OnCameraCut` BeginPlay 시 등록 + EndPlay 해제 페어
- [ ] 모든 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] `IsPlaying()` 검사 후 `Play()` 호출 (매 프레임 폭주 회피)
- [ ] `bDisableMovementInput` 시 OnFinished 안 EnableInput 복원
- [ ] Replicated = `HasAuthority()` 검사 + `bReplicatePlayback=true`
- [ ] Possessable Binding = BP 자산 매칭 (Guid 하드코딩 X)
- [ ] EndPlay 안 Async Handle Cancel/Release
- [ ] FFrameNumber 사용 (float 시간 X)
- [ ] Cooked Build 검증 — Director BP 동작 확인

---

## 11. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| ALevelSequenceActor 멤버 / API | **[verified]** ✅ | `LevelSequenceActor.h:38-213` |
| ULevelSequencePlayer + OnCameraCut | **[verified]** ✅ | `LevelSequencePlayer.h:27, 105, 113` |
| UMovieSceneSequencePlayer 30+ API (Play/Pause/Stop/GoTo/Scrub/PlayTo/SetPlaybackPosition) | **[verified]** ✅ | `MovieSceneSequencePlayer.h:192-382` (grep 매치) |
| FMovieSceneSequencePlaybackSettings 필드 | **[grep-listed]** ⚠ | `MovieSceneSequencePlayer.h` 안 USTRUCT 일반 패턴 |
| CreateLevelSequencePlayer 정적 헬퍼 | **[verified]** ✅ | `LevelSequencePlayer.h:105` UFUNCTION |
| AddBinding / RemoveBinding / SetBinding / ResetBinding | **[verified]** ✅ | `LevelSequenceActor.h:177-213` |
| bReplicatePlayback Replication | **[verified]** ✅ | `LevelSequenceActor.h:116` UPROPERTY replicated |
| FMovieSceneSequenceLoopCount | **[inferred]** ❌ | UE 일반 — `MovieSceneSequencePlaybackSettings.h` grep 필요 |

---

## 12. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인
- ⭐ [`./MovieScene.md`](./MovieScene.md) — 베이스 (Sequence / Track / Section)
- [`./Tracks.md`](./Tracks.md) — 빌트인 트랙 43종
- [`./Director.md`](./Director.md) — BP Director + Event Track
- [`./CineCamera.md`](./CineCamera.md) — 카메라 컷
- 🚨 [`../../../references/11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — Soft + Async
- 🚨 [`../../../references/07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
- [`GameFramework/Actor.md`](../../GameFramework/references/Actor.md) — BeginPlay/EndPlay 페어

---

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **ALevelSequenceActor 전체 멤버 / API [verified]** (LevelSequenceAsset / SequencePlayer / PlaybackSettings / CameraSettings / Replication / BindingOverrides) + **ULevelSequencePlayer + OnCameraCut [verified]** + **UMovieSceneSequencePlayer 30+ API [verified]** (Play/Pause/Stop/GoTo/Scrub/PlayTo/SetPlaybackPosition/IsPlaying/GetCurrentTime/SetPlaybackSpeed). 표준 패턴 3종 (Level 배치 / 런타임 동적 / Possessable 교체) + 시나리오 5종 + 함정 12 + 체크리스트 11. |
