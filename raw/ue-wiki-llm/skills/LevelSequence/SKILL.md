---
name: levelsequence
description: UE 5.7.4 LevelSequence 카테고리 — 시네마틱 / 컷씬 / 영상 시스템. 10 sub-skill (MovieScene 베이스 + Tracks 43종 + LevelSequencePlayer + Director + CineCamera + Sequencer 🛠 + MovieRenderPipeline 5.x + EntitySystem ECS + SequencerScripting + TemplateSequence). 런타임 컷씬 재생 + Sequencer Editor 확장 + Movie Render Queue + BP Director Event Track + UCineCameraComponent + 5.x ECS 평가. [LevelSequence] prefix 호출.
---

# LevelSequence — 시네마틱 / 컷씬 / 영상 시스템

> **위치 (verified)**:
> - **MovieScene** (Runtime 베이스): `Engine/Source/Runtime/MovieScene/` (75 Public 헤더 + EntitySystem 75 + Evaluation 64 + Channels 23)
> - **MovieSceneTracks** (빌트인 트랙): `Engine/Source/Runtime/MovieSceneTracks/` (43 Tracks + Sections + Systems)
> - **LevelSequence** Plugin: `Engine/Source/Runtime/LevelSequence/Public/` (18 헤더 — `ULevelSequence` / `ALevelSequenceActor` / `ULevelSequencePlayer` / `ULevelSequenceDirector`)
> - **CinematicCamera**: `Engine/Source/Runtime/CinematicCamera/Public/` (6 헤더 — `UCineCameraComponent` / `ACineCameraActor` / `UCineCameraSettings` / `ACameraRig_Crane` / `ACameraRig_Rail`)
> - **Sequencer** 🛠 (Editor): `Engine/Source/Editor/Sequencer/Public/`
> - **MovieRenderPipeline** Plugin (5.x): `Engine/Plugins/MovieScene/MovieRenderPipeline/Source/MovieRenderPipelineCore/`
>
> **요지**: UE 의 **시네마틱 시스템** 통합. 런타임 컷씬 / Sequencer Editor / Movie Render Queue / BP Director 모두 `UMovieSceneSequence` 베이스 공유. `UWidgetAnimation` (UMG) / `UCameraAnimationSequence` (Camera) 도 같은 베이스 — cross-category 통합.

---

## 🚨 공통 정책 (자동 적용)

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) | `OnCameraCut` / `OnFinished` 등 모든 시퀀스 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| 🚨 [`11_AssetLoadingPolicy §3`](../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-) | Editor Pure 모드 = Sync Load / Runtime = Soft + Async (LevelSequence 어셋 무거움) |
| 🚨 [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) | Sequencer / LevelSequenceEditor / MovieRenderPipelineEditor = **Editor 모듈 4단 분리 의무** |
| 🚨 Lifetime | `ULevelSequencePlayer` = `UPROPERTY(Transient)` — 직접 보유 X / `ALevelSequenceActor::SequencePlayer` 통한 접근 |
| 🚨 5.x ECS | MovieScene 평가 = ECS (Entity-Component-System) — Game Thread 안 멀티스레딩 안전 |

---

## 1. 10 sub-skill 인덱스

### Tier 1 — 핵심 (5)

| sub-skill | 책임 | 핵심 클래스 |
|-----------|------|------------|
| [`MovieScene`](./references/MovieScene.md) ⭐⭐ | 베이스 — `UMovieScene` / `UMovieSceneSequence` / `UMovieSceneTrack` / `UMovieSceneSection` virtual + 라이프사이클 | `UMovieScene` / `IMovieScenePlayer` / `FMovieSceneSequenceID` / `FFrameNumber` / `FQualifiedFrameTime` |
| [`Tracks`](./references/Tracks.md) ⭐ | 빌트인 트랙 43종 + 작성 표준 | Transform / Float / Audio / Event / Material / Skeletal / CameraCut / CinematicShot / Sub / Visibility / Fade / Spawn / Slomo / DataLayer |
| [`LevelSequencePlayer`](./references/LevelSequencePlayer.md) ⭐⭐⭐ | **런타임 재생 표준** — Play/Pause/Stop/GoTo + BP API | `ALevelSequenceActor` / `ULevelSequencePlayer` / `FMovieSceneSequencePlaybackParams` / `OnCameraCut` / `OnFinished` |
| [`Director`](./references/Director.md) | BP Director + Event Track + Binding 참조 | `ULevelSequenceDirector` / `UFUNCTION(BlueprintImplementableEvent)` |
| [`CineCamera`](./references/CineCamera.md) | 시네마틱 카메라 + Filmback/Focus/Aperture/Rig | `UCineCameraComponent` / `ACineCameraActor` / `FCameraFilmbackSettings` / `FCameraFocusSettings` / `ACameraRig_Rail` / `ACameraRig_Crane` |

### Tier 2 — 보조 (5)

| sub-skill | 책임 | 핵심 |
|-----------|------|------|
| [`Sequencer`](./references/Sequencer.md) 🛠 | Editor 메인 — 커스텀 트랙 UI | `FSequencer` / `ISequencer` / `ISequencerTrackEditor` / `ISequencerSection` |
| [`MovieRenderPipeline`](./references/MovieRenderPipeline.md) | 5.x Movie Render Queue (영상 출력) | `UMoviePipeline` / `UMoviePipelineExecutorBase` / `UMoviePipelineMasterConfig` / Output 6종 |
| [`EntitySystemECS`](./references/EntitySystemECS.md) | 5.x ECS 평가 시스템 (성능 깊이) | `FMovieSceneEntityManager` / `FBuiltInComponentTypes` / `IMovieSceneEntityProvider` |
| [`SequencerScripting`](./references/SequencerScripting.md) | Python / BP API (자동화) | `UMovieSceneSequenceExtensions` / `ULevelSequenceEditorSubsystem` |
| [`TemplateSequence`](./references/TemplateSequence.md) | 재사용 가능 템플릿 (BindingType 추상화) | `UTemplateSequence` / `FTemplateSequenceObjectBindingID` |

---

## 2. 시나리오 결정 트리

```
LevelSequence 작업?
├── 게임 안 컷씬 재생 (시네마틱) ⭐⭐⭐    → LevelSequencePlayer + LevelSequence + Tracks
├── BP 통합 (Event Track 콜백)            → Director + Tracks/EventTrack
├── 시네마틱 카메라 (Focus / Aperture)    → CineCamera + Tracks/CameraCut
├── 캐릭터 애니메이션 트랙 (Skeletal)    → Tracks/SkeletalAnimationTrack + Animation 페어
├── Sub Sequence (시퀀스 안 시퀀스)       → Tracks/SubTrack + LevelSequence
├── 영상 출력 (출시 트레일러)             → MovieRenderPipeline + LevelSequence
├── 커스텀 트랙 작성 (게임 전용 데이터)   → MovieScene (베이스 자손) + Tracks 패턴
├── Sequencer Editor 확장 (커스텀 UI) 🛠 → Sequencer + Editor 4단 분리
├── Python 자동화                          → SequencerScripting
├── 재사용 가능 시퀀스 (캐릭터 별 동일)   → TemplateSequence
└── 5.x ECS 평가 디버깅 / 성능 깊이       → EntitySystemECS + MovieScene
```

---

## 3. 시나리오 매핑 (10종)

| 시나리오 | 필수 sub-skill | 보조 |
|----------|---------------|------|
| **게임 안 컷씬 재생** ⭐⭐⭐ | LevelSequencePlayer + Tracks | Director (이벤트 시) |
| BP Director Event Track 통합 | Director + Tracks/EventTrack | LevelSequencePlayer |
| 시네마틱 카메라 (DoF / Filmback) | CineCamera + Tracks/CameraCut | LevelSequencePlayer |
| 캐릭터 애니메이션 시퀀스 | Tracks/SkeletalAnimationTrack | + Animation/AnimInstance |
| Sub Sequence (영화 안 영화) | Tracks/SubTrack + LevelSequence | LevelSequencePlayer |
| Movie Render Queue (영상 출력) | MovieRenderPipeline + LevelSequence | CineCamera |
| 커스텀 트랙 (게임 전용) | MovieScene + Tracks 패턴 | Sequencer (Editor UI) |
| Sequencer Editor 확장 🛠 | Sequencer + ISequencerTrackEditor | Editor (4단 분리) |
| Python / BP 자동화 | SequencerScripting | LevelSequenceEditor |
| 5.x ECS 평가 깊이 | EntitySystemECS + MovieScene | (성능 디버그) |

---

## 4. 5.x ECS 평가 흐름 (핵심)

```
[Game Thread]
ULevelSequencePlayer::Tick(DT)
  ↓
FMovieSceneEntityManager::Update()         ⭐ 5.x ECS 평가 엔진
  ↓
ECS 단계:
[1] Instantiation       — Track → Entity 변환
[2] Evaluation          — Entity 안 Component 값 계산
[3] Blending            — 여러 트랙 결과 블렌딩 (Float / Vector / Transform / etc)
[4] Application         — 최종 결과 게임 오브젝트에 적용 (Transform / Material / Audio)
  ↓
콜백 (OnCameraCut / OnFinished / Event Track)
```

**5.x 신규**: 멀티스레드 안전 (단, Game Thread 안에서만 — Render Thread X).

---

## 5. cross-category 통합 (페어 매트릭스)

| 카테고리 | 통합 |
|----------|------|
| `AssetClasses/Camera` | `UCameraAnimationSequence : ULevelSequence` (5.x 카메라 애니) |
| `UMG` | `UWidgetAnimation : UMovieSceneSequence` — 동일 베이스 / Track 19종 (Margin / 2DTransform / WidgetMaterial 등) |
| `Animation/AnimInstance` | `Tracks/SkeletalAnimationTrack` — 본 애니메이션 트랙 |
| `Components/AudioComponent` | `Tracks/AudioTrack` — 오디오 큐 |
| `Components/CameraComponent` | `Tracks/CameraCutTrack` — 카메라 스위치 |
| `Components/RenderingComponents` | `Tracks/MaterialTrack` / `MaterialParameterCollectionTrack` |
| `Editor` | `LevelSequenceEditor` plugin + `Sequencer` (Editor 4단 분리) |
| `GameFramework/World` | `Tracks/LevelVisibilityTrack` — 레벨 스트리밍 통합 |

---

## 6. Build.cs 의존성 (시나리오별)

```csharp
// 런타임 컷씬 재생
PrivateDependencyModuleNames.AddRange(new[] {
    "Core", "CoreUObject", "Engine",
    "MovieScene", "MovieSceneTracks",        // 베이스
    "LevelSequence",                          // ULevelSequence / Player / Director
    "CinematicCamera",                        // UCineCameraComponent (선택)
});

// Editor 확장 (Sequencer 커스텀 트랙)
PrivateDependencyModuleNames.AddRange(new[] {
    // 위 항목 +
    "Sequencer", "SequencerCore", "SequencerWidgets",
    "MovieSceneTools",                       // ISequencerTrackEditor
    "LevelSequenceEditor",
});

// Movie Render Queue
PrivateDependencyModuleNames.AddRange(new[] {
    "MovieRenderPipelineCore",
    "MovieRenderPipelineRenderPasses",
    "MovieRenderPipelineSettings",
});
```

---

## 7. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | `ULevelSequencePlayer` 직접 NewObject | `ALevelSequenceActor::SequencePlayer` 통한 접근 (Player = Transient + Instanced) |
| 2 | 매 프레임 `Play()` 호출 → 시퀀스 재시작 폭주 | `bIsPlaying` 검사 + `IsActive()` |
| 3 | LevelSequence Hard Reference 매번 로드 | Soft (`TSoftObjectPtr<ULevelSequence>`) + Async ([`11_AssetLoadingPolicy`](../../references/11_AssetLoadingPolicy.md)) |
| 4 | Editor PIE 안 동작하지만 Cooked Build 시 BP Director 누락 | `CreateDirectorInstance` virtual 검증 + Cooked Test |
| 5 | 시퀀스 종료 시 `OnFinished` 콜백 누락 | `OnFinished.AddDynamic(...)` BeginPlay 시 의무 등록 |
| 6 | Custom Track = Runtime 모듈에 작성 (Cooked OK) | UMovieSceneTrack 자손 = Runtime / `ISequencerTrackEditor` = Editor 4단 분리 |
| 7 | `OnCameraCut` 매 프레임 호출 추측 | 카메라 컷 변경 시점만 호출 — 매 프레임 X |
| 8 | `MoviePipelineRenderQueue` 실행 중 게임 Tick 진행 추측 | Movie Render Queue = Game Thread 점유 — UI 멈춤 (별도 Executor 분리) |
| 9 | `FFrameNumber` vs `float` 혼동 | 5.x = `FFrameNumber` (정수 프레임 단위) — `FFrameRate` 변환 의무 |
| 10 | Spawnable / Possessable 혼동 | Spawnable = Sequence 가 직접 생성 / Possessable = 외부 Actor 바인딩 |

---

## 8. 체크리스트

- [ ] 런타임 = `ALevelSequenceActor` + `ULevelSequencePlayer` 통한 접근 (직접 NewObject X)
- [ ] LevelSequence 어셋 = `TSoftObjectPtr<ULevelSequence>` + Async Load (Runtime)
- [ ] Editor 도구 = `TryLoad` Sync ([`11_AssetLoadingPolicy §3`](../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-))
- [ ] `OnFinished` / `OnPlay` / `OnPause` / `OnCameraCut` 콜백 BeginPlay 시 등록 + EndPlay 해제
- [ ] 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] Custom Track = Runtime 모듈 / Custom TrackEditor = Editor 모듈 (4단 분리)
- [ ] `FFrameNumber` / `FFrameRate` 명시 — float 시간 변환 시 정확
- [ ] Cooked Build 검증 — BP Director / Event Track 동작 확인
- [ ] Movie Render Queue = 별도 Executor 분리 (게임 멈춤 회피)

---

## 9. 관련 / cross-link

### 카테고리 외부

- ⭐ [`AssetClasses/Camera.md`](../AssetClasses/references/Camera.md) — UCameraAnimationSequence (ULevelSequence 자손)
- ⭐ [`UMG/SKILL.md`](../UMG/SKILL.md) — UWidgetAnimation (UMovieSceneSequence 자손, 동일 베이스)
- [`Animation/AnimInstance.md`](../Animation/references/AnimInstance.md) — SkeletalAnimationTrack 페어
- [`Components/AudioComponent.md`](../Components/references/AudioComponent.md) — AudioTrack 페어
- [`Components/CameraComponent.md`](../Components/references/CameraComponent.md) — CameraCutTrack 페어
- [`Editor/SKILL.md`](../Editor/SKILL.md) — Sequencer Editor 통합

### 횡단 정책

- 🚨 [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) — Sequencer / LevelSequenceEditor 4단 분리
- 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — 콜백 스코프 의무
- 🚨 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) — LevelSequence 어셋 Soft Reference

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 카테고리 신설. 10 sub-skill (MovieScene + Tracks 43종 + LevelSequencePlayer ⭐⭐⭐ + Director + CineCamera + Sequencer 🛠 + MovieRenderPipeline 5.x + EntitySystemECS + SequencerScripting + TemplateSequence) + 결정 트리 + 시나리오 10종 + 5.x ECS 평가 흐름 + cross-category 통합 (Camera/UMG/Animation/Audio/Render) + 함정 10대. Engine 5.7.4 검증 (LevelSequence/MovieScene/MovieSceneTracks/CinematicCamera/Sequencer/MovieRenderPipeline Source). |
