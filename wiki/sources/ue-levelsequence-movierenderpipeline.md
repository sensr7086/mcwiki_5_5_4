---
type: source
title: "UE LevelSequence — MovieRenderPipeline (5.x 영상 출력)"
slug: ue-levelsequence-movierenderpipeline
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/MovieRenderPipeline.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_concepts: []
tags: [ue, levelsequence, movierenderpipeline, rendering, enriched, verified]
citation_disclosure: "🟢 11 / 🟡 4 / 🔴 1 · raw verified · Cycle #13.8 enrich"
---

# UE LevelSequence — MovieRenderPipeline (5.x)

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/MovieRenderPipeline.md]] (372L)
> Parent: [[sources/ue-levelsequence-skill]] · 위치: `Engine/Plugins/MovieScene/MovieRenderPipeline/Source/MovieRenderPipelineCore/Public/`

## 1. Summary

🟢 5.x **Movie Render Queue** — 출시급 영상 렌더링 (게임 트레일러 / 시네마틱). `UMoviePipeline` + `UMoviePipelineExecutorBase` + `UMoviePipelineMasterConfig`. Output 6종 (PNG/JPG/BMP/EXR/ProRes/MP4) + Spatial/Temporal Anti-Aliasing + High Resolution Tile + Camera (ShutterAngle/Overscan). Editor 전용 (Cooked Build X).

## 2. Key claims

### 2.1 UMoviePipeline 6 UFUNCTION 🟢 (raw §1 — MoviePipeline.h:54-194)

```cpp
UCLASS(BlueprintType)
class UMoviePipeline : public UMoviePipelineBase
{
    UFUNCTION(BlueprintCallable) void RequestShutdown();
    UFUNCTION(BlueprintPure) bool IsShutdownRequested() const;
    UFUNCTION(BlueprintPure) EMovieRenderPipelineState GetPipelineState() const;
    UFUNCTION(BlueprintPure) bool IsFlushDiskWritesPerShot() const;
    UFUNCTION(BlueprintPure) FFrameRate GetTickResolution() const;
    UFUNCTION(BlueprintCallable) void SetIsFlushDiskWritesPerShot(bool);

    UPROPERTY(Transient, Instanced) TObjectPtr<UMoviePipelineMasterConfig> PipelineMasterConfig;
    UPROPERTY(Transient) TObjectPtr<UMoviePipelineExecutorJob> CurrentJob;
    UPROPERTY(Transient) TArray<TObjectPtr<UMoviePipelineExecutorShot>> ActiveShotList;
    UPROPERTY(Transient) int32 CurrentShotIndex;
    UPROPERTY(Transient) EMovieRenderPipelineState PipelineState;
};
```

### 2.2 EMovieRenderPipelineState 5종 🟡 (raw §2)

| State | 의미 |
|-------|------|
| `Uninitialized` | 초기 |
| `ProducingFrames` | 프레임 생성 중 |
| `Finalize` | 마무리 (디스크 쓰기) |
| `Export` | 외부 인코더 (FFmpeg / Avid) |
| `Finished` | 완료 |

### 2.3 UMoviePipelineMasterConfig 🟢 (raw §3)

```cpp
UCLASS(BlueprintType)
class UMoviePipelineMasterConfig : public UMoviePipelineConfigBase
{
    UFUNCTION(BlueprintCallable)
    UMoviePipelineSetting* FindOrAddSetting(TSubclassOf<UMoviePipelineSetting>);

    UFUNCTION(BlueprintCallable)
    void RemoveSetting(UMoviePipelineSetting*);

    UFUNCTION(BlueprintPure)
    const TArray<UMoviePipelineSetting*>& GetUserSettings() const;
};
```

### 2.4 Output 6종 🟡 (raw §4 — RenderPasses 모듈)

| Output | 사용 시점 |
|--------|----------|
| PNG 8-bit | 일반 트레일러 (편집 전 단계) |
| JPG 8-bit | 미리보기 |
| BMP | 비압축 빠름 |
| **EXR (Half/Full)** | HDR — 컬러 그레이딩 |
| **ProRes** ⭐ | Apple ProRes 422 / 4444 — 영화/TV |
| **MP4 (H.264/H.265)** | 최종 배포 |

### 2.5 Anti-Aliasing (Spatial × Temporal) 🟢 (raw §5)

```cpp
UCLASS()
class UMoviePipelineAntiAliasingSetting : public UMoviePipelineSetting
{
    int32 SpatialSampleCount = 1;        // 공간 (1~64)
    int32 TemporalSampleCount = 1;       // 시간 (1~64) — 모션블러 품질
    EAntiAliasingMethod OverrideAntiAliasingMethod = AAM_None;  // None/FXAA/TAA/TSR/MSAA
    int32 RenderWarmUpCount = 32;        // 워밍업 프레임
    bool bUseCameraCutForWarmUp = false;
};
```

| 등급 | Spatial × Temporal | Warmup | 1프레임 |
|------|-------------------|--------|---------|
| 미리보기 | 1 × 1 | 8 | 빠름 |
| 표준 | 4 × 8 | 32 | 중간 |
| **고품질** ⭐ | 8 × 16 | 32 | 느림 |
| 시네마 | 16 × 32 | 64 | 매우 느림 |
| 최고 | 64 × 64 | 128 | 4K = 분/프레임 |

> ⚠ Spatial × Temporal = 1프레임 당 렌더 횟수 — 16×16=256회.

### 2.6 HighRes Tile 🟢 (raw §6)

```cpp
UCLASS()
class UMoviePipelineHighResSetting : public UMoviePipelineSetting
{
    int32 TileCount = 1;             // 1=풀스크린, 4=2x2, 9=3x3
    float OverlapRatio = 0.1f;        // 타일 간 오버랩
    float TextureSharpnessBias = 0.0f;
    bool bAllocateHistoryPerTile = false;  // 5.x
};
```

8K 렌더 = `TileCount=4` (2x2) + `Resolution=7680×4320` → GPU 메모리 분산.

### 2.7 Camera Setting 🟢 (raw §7)

```cpp
UCLASS()
class UMoviePipelineCameraSetting : public UMoviePipelineSetting
{
    float ShutterAngle = 180.0f;          // 모션블러 (영화 표준)
    float OverscanPercentage = 0.0f;      // 안전 영역 확장
    bool bUseCameraCutForWarmUp = false;
};
```

### 2.8 Executor — InProcess vs OutOfProcess 🟡 (raw §8)

| Executor | 특성 |
|----------|------|
| `UMoviePipelineInProcessExecutor` | 기본 — UI 멈춤 (Game Thread 점유) |
| `UMoviePipelineNewProcessExecutor` ⭐ | 5.x 별도 프로세스 — 백그라운드 |
| `UMoviePipelinePIEExecutor` | PIE 안 렌더 |

### 2.9 5 시나리오 🟢 (raw §9)

| # | 시나리오 | 핵심 설정 |
|---|---------|----------|
| 1 | 게임 트레일러 (1080p MP4) | Spatial 4 / Temporal 8 / PNG+MP4 |
| 2 | 영화 시네마 (4K ProRes 4444) | Spatial 8 / Temporal 16 / Warmup 32 / ShutterAngle 180 |
| 3 | 8K 광고 (HighRes Tile) | 7680×4320 / TileCount 4 / Overlap 0.1 / EXR Half |
| 4 | 빠른 미리보기 | 720p / 1×1 / PNG |
| 5 | Python 자동화 | `MoviePipelineQueueSubsystem` + `PIEExecutor` |

```python
# §9.5 Python
queue = unreal.MoviePipelineQueueSubsystem.get_queue()
job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
job.set_sequence(unreal.load_asset("/Game/Seq/Intro"))
job.set_configuration(unreal.load_asset("/Game/Configs/HQ"))
executor = unreal.MoviePipelineNewProcessExecutor()
queue.render_queue_with_executor_instance(executor)
```

## 3. 함정 10 🟢 (raw §10)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Spatial × Temporal 너무 높음 → GPU OOM | 8×16 까지 + HighRes Tile |
| 2 | HighRes OverlapRatio 0 → 경계선 | 0.1+ 권장 |
| 3 | TSR Warmup 0 → 첫 프레임 깜빡임 | RenderWarmUpCount ≥ 32 |
| 4 | InProcess Editor 멈춤 모름 | OutOfProcess (백그라운드) |
| 5 | MP4 Encoder = 자동 FFmpeg 추측 | FFmpeg 별도 설치 + 경로 |
| 6 | Audio MP4 자동 통합 추측 | 별도 WAV + 후처리 |
| 7 | Possessable = Editor 만 → 렌더 누락 | Spawnable 변환 또는 Level 영구 |
| 8 | ShutterAngle 360 → 모션블러 과 | 180 (영화 표준 1/48 sec @ 24fps) |
| 9 | CVar Track 영구 변경 추측 | `bRestoreState=true` |
| 10 | Cooked Build 렌더 시도 | Editor 전용 |

## 4. 체크리스트 🟢 (raw §11)

- [ ] MovieRenderPipeline plugin 활성
- [ ] Build.cs = MovieRenderPipelineCore / RenderPasses
- [ ] AntiAliasing Spatial/Temporal/Warmup 명시
- [ ] HighRes Tile = OverlapRatio 0.1+
- [ ] Output 종류 결정 (PNG/EXR/ProRes/MP4)
- [ ] MP4 = FFmpeg 경로 설정
- [ ] Audio = 별도 + 후처리
- [ ] OutOfProcess Executor 권장
- [ ] Possessable = Spawnable 검토
- [ ] ShutterAngle = 180
- [ ] Cooked Build 호출 X
- [ ] GPU 메모리 모니터

## 5. 신뢰도 🟢 (raw §12)

| 항목 | tier | 출처 |
|------|------|------|
| UMoviePipeline 6 UFUNCTION | 🟢 verified | `MoviePipeline.h:54-194` |
| EMovieRenderPipelineState | 🟡 grep-listed | enum 추정 |
| UMoviePipelineMasterConfig + ExecutorJob/Shot | 🟢 verified | `MoviePipeline.h:321-410` |
| Output 6종 | 🟡 grep-listed | RenderPasses 모듈 헤더 |
| AntiAliasing / HighRes / Camera Setting | 🟡 grep-listed | 헤더 존재 |
| Python `MoviePipelineQueueSubsystem` | 🔴 inferred | 공식 문서 검증 |
| OutOfProcess Executor 5.x | 🟡 grep-listed | `MoviePipelineNewProcessExecutor.h` |

## 6. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 페어: [[sources/ue-levelsequence-levelsequenceplayer]] (렌더 대상 sequence) · [[sources/ue-levelsequence-cinecamera]] (Filmback/Aperture) · [[sources/ue-levelsequence-tracks]] (CVarTrack 품질) · [[sources/ue-levelsequence-sequencerscripting]] (Python 자동화)
- Render 페어: [[sources/ue-render-postprocess]] (영상 PostProcess)
- Build.cs: `MovieRenderPipelineCore` + `MovieRenderPipelineRenderPasses` + `MovieRenderPipelineSettings`
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
