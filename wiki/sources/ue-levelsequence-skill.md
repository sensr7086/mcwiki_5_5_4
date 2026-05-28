---
type: source
title: "UE LevelSequence — Main SKILL (21번째 카테고리, Phase 10)"
slug: ue-levelsequence-skill
source_path: raw/ue-wiki-llm/skills/LevelSequence/SKILL.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, levelsequence, cinematic, sequencer, movierenderpipeline, category-main, enriched, verified]
citation_disclosure: "🟢 18 / 🟡 2 / 🔴 0 · raw 정밀 카테고리 main hub (Engine 5.7.4 검증) · Cycle #14 enrich"
---

# UE LevelSequence — Main SKILL (21번째 카테고리)

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/SKILL.md]] (211L)
> 위치: `Engine/Source/Runtime/MovieScene/` (75+ 헤더) + `MovieSceneTracks/` (43 Tracks) + `Engine/Source/Runtime/LevelSequence/Public/` (18 헤더) + `CinematicCamera/Public/` (6 헤더) + `Engine/Source/Editor/Sequencer/Public/` 🛠 + `Engine/Plugins/MovieScene/MovieRenderPipeline/`
> 10 sub-skill 인덱스 + 결정 트리 + 5.x ECS 평가 흐름 + cross-category 통합 + 함정 10대.
> Cycle #14 enrich (2026-05-15) — Cycle #13 10 sub-skill 1.5~2x enrich 직후 정밀 cross-link.

## 1. Summary

🟢 UE 의 **시네마틱 시스템** 통합 카테고리. 런타임 컷씬 / Sequencer Editor / Movie Render Queue / BP Director 모두 `UMovieSceneSequence` 베이스 공유. cross-category 페어: `UWidgetAnimation` (UMG) / `UCameraAnimationSequence` (Camera) / `UActorSequence` / `UTemplateSequence` 5 자손이 모두 같은 베이스. 5.x ECS 평가 시스템 (`FMovieSceneEntityManager` + 75 EntitySystem 헤더) = Game Thread 안 멀티스레드 안전 (Render Thread X). `FFrameNumber` / `FFrameRate` 의무 (float 시간 X).

## 2. 10 sub-skill 인덱스 🟢

### Tier 1 — 핵심 (5)

| sub-skill | 책임 | 핵심 |
|-----------|------|------|
| ⭐⭐ [[sources/ue-levelsequence-moviescene]] | 베이스 — `UMovieScene` / `UMovieSceneSequence` 14 virtual / `UMovieSceneTrack` 6 PURE_VIRTUAL / `UMovieSceneSection` | `FFrameNumber` / `FQualifiedFrameTime` / Possessable vs Spawnable / Sub Sequence |
| ⭐ [[sources/ue-levelsequence-tracks]] | 빌트인 43종 (Property 16 + Cinematic 8 + Audio-VFX 5 + Animation 3 + World 4 + Sub 1 + Constraint 3 + Event 1 + CVar 1 + Text 1) | `Interp` UPROPERTY meta / 사용 빈도 매트릭스 / 자동화 표준 |
| ⭐⭐⭐ [[sources/ue-levelsequence-levelsequenceplayer]] | **런타임 재생 표준** — 8 Actor 필드 + 30+ Player UFUNCTION + 5종 콜백 | `ALevelSequenceActor` / `ULevelSequencePlayer` / `CreateLevelSequencePlayer` / `OnCameraCut` / `OnFinished` |
| [[sources/ue-levelsequence-director]] | BP Director + Event Track + Binding 참조 + 5.x Custom Clock + Multiplayer NetMulticast | `ULevelSequenceDirector` 6 UFUNCTION / `BlueprintImplementableEvent` |
| [[sources/ue-levelsequence-cinecamera]] | 시네마틱 카메라 9 필드 + Filmback 6 프리셋 + 4 FocusMethod + 2 Rig | `UCineCameraComponent` / `ACineCameraActor` / `FCameraFilmbackSettings` / `ACameraRig_Rail` / `ACameraRig_Crane` |

### Tier 2 — 보조 (5)

| sub-skill | 책임 | 핵심 |
|-----------|------|------|
| [[sources/ue-levelsequence-sequencer]] 🛠 | Editor 메인 — Custom Track UI 4단 분리 | 9 인터페이스 / `FMovieSceneTrackEditor` 자손 / Module Startup 페어 |
| [[sources/ue-levelsequence-movierenderpipeline]] | 5.x Movie Render Queue (영상 출력) — Output 6 + AA Spatial×Temporal + HighRes Tile | `UMoviePipeline` / `UMoviePipelineMasterConfig` / InProcess vs OutOfProcess |
| [[sources/ue-levelsequence-entitysystemecs]] | 5.x ECS 평가 (75 헤더 / 4 단계) | `FMovieSceneEntityManager` / `FBuiltInComponentTypes` / `IMovieSceneEntityProvider` / Blender / TaskScheduler |
| [[sources/ue-levelsequence-sequencerscripting]] | Python + BP API 자동화 | `UMovieSceneSequenceExtensions` / `ULevelSequenceEditorSubsystem` / `MoviePipelineQueueSubsystem` |
| [[sources/ue-levelsequence-templatesequence]] | 재사용 가능 템플릿 (Binding Type = UClass 추상화) | `UTemplateSequence` / `ATemplateSequenceActor` / `UTemplateSequencePlayer` |

## 3. 🚨 공통 정책 (5건) 🟢

| 정책 | 적용 |
|------|------|
| 🚨 [[concepts/Profiling-Scope-Rule]] | `OnCameraCut` / `OnFinished` / Director Event 등 모든 시퀀스 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| 🚨 [[concepts/Asset-Loading-Policy]] | Editor Pure = Sync Load / Runtime = `TSoftObjectPtr<ULevelSequence>` + Async (`FStreamableManager`) |
| 🚨 [[concepts/Editor-Only-4-Tier-Separation]] | Sequencer / LevelSequenceEditor / MovieRenderPipelineEditor = Runtime/Editor 4단 분리 의무 |
| 🚨 Lifetime | `ULevelSequencePlayer` = `UPROPERTY(Transient)` — 직접 보유 X / Actor 통한 접근 |
| 🚨 5.x ECS | MovieScene 평가 = ECS — Game Thread 안 멀티스레딩 안전 (Render Thread X) |

## 4. 시나리오 결정 트리 🟢 (raw §2)

```
LevelSequence 작업?
├── 게임 안 컷씬 재생 (시네마틱) ⭐⭐⭐    → LevelSequencePlayer + LevelSequence + Tracks
├── BP 통합 (Event Track 콜백)            → Director + Tracks (EventTrack)
├── 시네마틱 카메라 (Focus / Aperture)    → CineCamera + Tracks (CameraCut)
├── 캐릭터 애니메이션 트랙 (Skeletal)    → Tracks (SkeletalAnimationTrack) + Animation 페어
├── Sub Sequence (시퀀스 안 시퀀스)       → Tracks (SubTrack) + LevelSequence
├── 영상 출력 (출시 트레일러)             → MovieRenderPipeline + LevelSequence
├── 커스텀 트랙 작성 (게임 전용 데이터)   → MovieScene (베이스 자손) + Tracks 패턴
├── Sequencer Editor 확장 (커스텀 UI) 🛠 → Sequencer + Editor 4단 분리
├── Python 자동화                          → SequencerScripting
├── 재사용 가능 시퀀스 (캐릭터 별 동일)   → TemplateSequence
└── 5.x ECS 평가 디버깅 / 성능 깊이       → EntitySystemECS + MovieScene
```

## 5. 시나리오 매핑 10종 🟢 (raw §3)

| 시나리오 | 필수 sub-skill | 보조 |
|----------|---------------|------|
| **게임 안 컷씬 재생** ⭐⭐⭐ | LevelSequencePlayer + Tracks | Director (이벤트 시) |
| BP Director Event Track 통합 | Director + Tracks (EventTrack) | LevelSequencePlayer |
| 시네마틱 카메라 (DoF / Filmback) | CineCamera + Tracks (CameraCut) | LevelSequencePlayer |
| 캐릭터 애니메이션 시퀀스 | Tracks (SkeletalAnimationTrack) | + Animation/AnimInstance |
| Sub Sequence (영화 안 영화) | Tracks (SubTrack) + LevelSequence | LevelSequencePlayer |
| Movie Render Queue (영상 출력) | MovieRenderPipeline + LevelSequence | CineCamera |
| 커스텀 트랙 (게임 전용) | MovieScene + Tracks 패턴 | Sequencer (Editor UI) |
| Sequencer Editor 확장 🛠 | Sequencer + ISequencerTrackEditor | Editor (4단 분리) |
| Python / BP 자동화 | SequencerScripting | LevelSequenceEditor |
| 5.x ECS 평가 깊이 | EntitySystemECS + MovieScene | (성능 디버그) |

## 6. 5.x ECS 평가 흐름 🟢 (raw §4)

```
[Game Thread]
ULevelSequencePlayer::Tick(DT)
  ↓
FMovieSceneEntityManager::Update()         ⭐ 5.x ECS 평가 엔진 (75 EntitySystem 헤더)
  ↓
ECS 4 단계:
[1] Instantiation       — Track → Entity 변환 (IMovieSceneEntityProvider::ImportEntity)
[2] Evaluation          — Entity 안 Component 값 계산 (FloatChannel → FloatResult)
[3] Blending            — 여러 트랙 결과 합성 (Absolute / Additive / Relative / 5.x AbsoluteFromAdditive)
[4] Application         — UPROPERTY / BlueprintSetter 호출 (Transform / Material / Audio)
  ↓
콜백 (OnCameraCut / OnFinished / Event Track Director)
```

**5.x 신규**: TaskGraph 기반 멀티스레드 안전 — 데이터 의존성 자동 분석 + 충돌 없는 System 들 병렬 실행 (단, **Game Thread 안에서만** — Render Thread X).

자세한 = [[sources/ue-levelsequence-entitysystemecs]] §2.1-2.10.

## 7. cross-category 통합 (페어 매트릭스) 🟢 (raw §5)

| 카테고리 | 통합 |
|----------|------|
| `AssetClasses/Camera` | `UCameraAnimationSequence : ULevelSequence` (5.x 카메라 애니) |
| `UMG` | `UWidgetAnimation : UMovieSceneSequence` — 동일 베이스 / Track 19종 (Margin / 2DTransform / WidgetMaterial 등) |
| `Animation/AnimInstance` | `Tracks/SkeletalAnimationTrack` — 본 애니메이션 트랙 |
| `Components/AudioComponent` | `Tracks/AudioTrack` — USoundCue / USoundWave |
| `Components/CameraComponent` | `Tracks/CameraCutTrack` — `UMovieScene::CameraCutTrack` (특수 슬롯) |
| `Components/RenderingComponents` | `Tracks/MaterialTrack` / `MaterialParameterCollectionTrack` |
| `Editor` | `LevelSequenceEditor` plugin + `Sequencer` (Editor 4단 분리) |
| `GameFramework/World` | `Tracks/LevelVisibilityTrack` — 레벨 스트리밍 통합 + 5.x `DataLayerTrack` (WorldPartition) |
| `Blueprint` | `ULevelSequenceDirector` `BlueprintImplementableEvent` |
| `Networking` | `bReplicatePlayback` + Server Authoritative (Multiplayer 컷씬) |
| `Render/PostProcess` | DoF 매트릭스 + Movie Render Queue AntiAliasing |

## 8. Build.cs 의존성 시나리오별 🟢 (raw §6)

```csharp
// [1] 런타임 컷씬 재생 (가장 일반)
PrivateDependencyModuleNames.AddRange(new[] {
    "Core", "CoreUObject", "Engine",
    "MovieScene", "MovieSceneTracks",        // 베이스
    "LevelSequence",                          // ULevelSequence / Player / Director
    "CinematicCamera",                        // UCineCameraComponent (선택)
});

// [2] Editor 확장 (Sequencer 커스텀 트랙) — [1] +
PrivateDependencyModuleNames.AddRange(new[] {
    "Sequencer", "SequencerCore", "SequencerWidgets",
    "MovieSceneTools",                       // ISequencerTrackEditor
    "LevelSequenceEditor",
});
// uplugin Type = "Editor" 또는 Module Type = Editor + WhitelistPlatforms

// [3] Movie Render Queue
PrivateDependencyModuleNames.AddRange(new[] {
    "MovieRenderPipelineCore",
    "MovieRenderPipelineRenderPasses",
    "MovieRenderPipelineSettings",
});

// [4] Python 자동화 — Plugin 활성
// PythonScriptPlugin + SequencerScripting 활성 (Project Settings)
```

## 9. 함정 10대 🟢 (raw §7)

| # | 함정 | 정답 | sub-skill |
|---|------|------|-----------|
| 1 | `ULevelSequencePlayer` 직접 NewObject | `ALevelSequenceActor::SequencePlayer` (Transient + Instanced) 또는 `CreateLevelSequencePlayer` | LevelSequencePlayer §3 #1 |
| 2 | 매 프레임 `Play()` 호출 → 재시작 폭주 | `IsPlaying()` 검사 | LevelSequencePlayer §3 #3 |
| 3 | LevelSequence Hard Reference 매번 로드 | `TSoftObjectPtr<ULevelSequence>` + Async (`FStreamableManager`) | [[concepts/Asset-Loading-Policy]] |
| 4 | PIE OK / Cooked 안 BP Director 누락 | `CreateDirectorInstance` virtual + Cooked Test | Director §3 #1 |
| 5 | `OnFinished` AddDynamic 후 Remove 누락 | EndPlay 안 페어 | LevelSequencePlayer §3 #4 |
| 6 | Custom Track 을 Editor 모듈에 작성 | Runtime UMovieSceneTrack / Editor `ISequencerTrackEditor` 4단 분리 | Sequencer §2.2 |
| 7 | `OnCameraCut` 매 프레임 호출 추측 | 카메라 컷 변경 시점만 — 매 프레임 X | LevelSequencePlayer §3 #11 |
| 8 | Movie Render Queue InProcess → UI 멈춤 | `UMoviePipelineNewProcessExecutor` (별도 프로세스) | MovieRenderPipeline §2.8 |
| 9 | `FFrameNumber` vs `float` 혼동 | 5.x 정수 프레임 의무 — `FFrameRate` 변환 (`TransformTime`) | MovieScene §2.6 |
| 10 | Spawnable / Possessable 혼동 | Spawnable = Sequence 가 직접 Spawn / Possessable = 외부 Actor | MovieScene §2.7 |

## 10. 체크리스트 🟢 (raw §8)

- [ ] 런타임 = `ALevelSequenceActor` 통한 접근 (직접 NewObject X)
- [ ] LevelSequence 어셋 = `TSoftObjectPtr` + Async Load
- [ ] Editor 도구 = `TryLoad` Sync ([[concepts/Asset-Loading-Policy]] §3)
- [ ] `OnFinished` / `OnPlay` / `OnPause` / `OnCameraCut` BeginPlay 등록 + EndPlay 해제
- [ ] 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] Custom Track = Runtime / Custom TrackEditor = Editor (4단 분리)
- [ ] `FFrameNumber` / `FFrameRate` 명시 (float 시간 X)
- [ ] Cooked Build 검증 — BP Director / Event Track 동작
- [ ] Movie Render Queue = OutOfProcess Executor (게임 멈춤 회피)
- [ ] Replicated = `HasAuthority()` + `bReplicatePlayback=true`
- [ ] Possessable Binding Guid = BP 자산 (하드코딩 X)
- [ ] EndPlay 안 Async Handle Cancel/Release

## 11. 자동 로드 7 파일 (specialist 호출 시) 🟡

specialist (`ue-wiki-llm:ue-levelsequence-specialist`) plugin 활성 시 자동 로드:

1. `skills/LevelSequence/SKILL.md` (메인 — 본 페이지)
2. `skills/LevelSequence/references/LevelSequencePlayer.md` ⭐⭐⭐
3. 사용자 요청 sub-skill (MovieScene/Tracks/Director/CineCamera/Sequencer/MovieRenderPipeline/etc)
4. 🚨 `references/07_ProfilingScopeRule.md`
5. 🚨 `references/11_AssetLoadingPolicy.md`
6. 🚨 `references/05_EditorOnlyIndex.md`
7. (페어) `skills/Animation/SKILL.md` (Skeletal Animation Track 시)

**현 상태** 🟡 — plugin 미등록 (G3 게이트 대기, [[sources/ue-agent-levelsequence]] 페어).

## 12. 신뢰도 🟢 (raw §11)

| 항목 | tier | 출처 |
|------|------|------|
| 5 모듈 위치 (MovieScene / Tracks / LevelSequence / CinematicCamera / Sequencer / MovieRenderPipeline) | 🟢 verified | Engine 5.7.4 폴더 ls |
| 75 EntitySystem 헤더 | 🟢 verified | `MovieScene/Public/EntitySystem/` ls |
| 43 Track 헤더 | 🟢 verified | `MovieSceneTracks/Public/Tracks/` ls |
| 18 LevelSequence 헤더 | 🟢 verified | `LevelSequence/Public/` ls |
| 6 CinematicCamera 헤더 | 🟢 verified | `CinematicCamera/Public/` ls |
| ECS 4 단계 / 75 헤더 | 🟢 verified | EntitySystemECS §6 |
| MovieRenderPipeline 6 UFUNCTION | 🟢 verified | `MoviePipeline.h:54-194` (MovieRenderPipeline §2.1) |
| Cross-category 페어 5 자손 | 🟢 verified | `LevelSequence.h:43-67` virtual override 매트릭스 |

## 13. Cross-link

### Sub-skills (10)

[[sources/ue-levelsequence-moviescene]] · [[sources/ue-levelsequence-tracks]] · [[sources/ue-levelsequence-levelsequenceplayer]] · [[sources/ue-levelsequence-director]] · [[sources/ue-levelsequence-cinecamera]] · [[sources/ue-levelsequence-sequencer]] · [[sources/ue-levelsequence-movierenderpipeline]] · [[sources/ue-levelsequence-entitysystemecs]] · [[sources/ue-levelsequence-sequencerscripting]] · [[sources/ue-levelsequence-templatesequence]]

### Agent + 페어

- [[sources/ue-agent-levelsequence]] (15번째 agent — plugin 미등록 / G3 게이트 대기)
- 페어 합성: [[synthesis/mc-combo-editor-levelsequence-lite]] (KMCProject 2026-05-15 — LevelSequence 데이터 모델 lite + AnimNotify Track 자체 Slate 패널 — Cycle #13 enrich 직후 vault 인용)

### 카테고리 페어

- [[sources/ue-assetclasses-camera]] (UCameraAnimationSequence — ULevelSequence 자손)
- [[sources/ue-umg-skill]] (UWidgetAnimation — UMovieSceneSequence 자손, 동일 베이스)
- [[sources/ue-animation-animinstance]] (SkeletalAnimationTrack)
- [[sources/ue-components-audiocomponent]] (AudioTrack)
- [[sources/ue-components-cameracomponent]] (CameraCutTrack)
- [[sources/ue-editor-skill]] (Sequencer / LevelSequenceEditor)
- [[sources/ue-blueprint-skill]] (Director BlueprintImplementableEvent)
- [[sources/ue-networking-skill]] (Replicated Multicast / Server Authoritative)
- [[sources/ue-render-postprocess]] (DoF / Movie Render Queue AA)

### 횡단 정책

- 🚨 [[concepts/Profiling-Scope-Rule]] — 콜백 스코프 의무
- 🚨 [[concepts/Asset-Loading-Policy]] — LevelSequence 어셋 Soft Reference
- 🚨 [[concepts/Editor-Only-4-Tier-Separation]] — Sequencer / LevelSequenceEditor 4단 분리
- [[sources/ue-ref-07-profilingscopeRule]] / [[sources/ue-ref-11-assetloadingpolicy]] / [[sources/ue-ref-05-editoronlyindex]]
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에만): 3
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `> - **CinematicCamera**: `Engine/Source/Runtime/CinematicCamera/Public/` (6 헤더 — → > - **MovieScene** (Runtime 베이스): `Engine/Source/Runtime/MovieScene/` (UE 5.5 — `

**5.5.4 에만 (5.7.4 에 없음)**:
- `> - **MovieSceneTracks** (빌트인 트랙): `Engine/Source/Runtime/MovieSceneTracks/` (UE 5.5 — Tracks 41 + Sections + Systems, 총`
- `> - **LevelSequence** Runtime 모듈: `Engine/Source/Runtime/LevelSequence/Public/` (UE 5.5 — 16 헤더 — `ULevelSequence` / `AL`
- `> - **CinematicCamera**: `Engine/Source/Runtime/CinematicCamera/Public/` (UE 5.5 — 6 헤더 — `UCineCameraComponent` / `ACin`

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/LevelSequence/SKILL.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/LevelSequence/SKILL.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
