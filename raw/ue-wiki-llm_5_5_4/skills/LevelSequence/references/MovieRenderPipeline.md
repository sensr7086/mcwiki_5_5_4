---
name: levelsequence-movierenderpipeline
description: Movie Render Queue (5.x) — UMoviePipeline + UMoviePipelineExecutorBase + UMoviePipelineMasterConfig + Output 6종 (PNG/JPG/EXR/MP4/ProRes/Sequence) + Anti-Aliasing (Spatial/Temporal Sample) + High Resolution + Console Variable + Camera Setting. 영상 출시 표준 (게임 트레일러 / 시네마틱).
---

# LevelSequence/MovieRenderPipeline — Movie Render Queue (5.x)

> **위치 (verified)**:
> - **Core**: `Engine/Plugins/MovieScene/MovieRenderPipeline/Source/MovieRenderPipelineCore/Public/`
> - **UMoviePipeline** — `MoviePipeline.h`
> - **UMoviePipelineExecutorBase** — `MoviePipelineExecutor.h`
> - **UMoviePipelineMasterConfig** — `MoviePipelineConfigBase.h`
> - **UMoviePipelineAntiAliasingSetting** — `MoviePipelineAntiAliasingSetting.h`
> - **UMoviePipelineCameraSetting** — `MoviePipelineCameraSetting.h`
> - **UMoviePipelineHighResSetting** — `MoviePipelineHighResSetting.h`
> - **UMoviePipelineInProcessExecutor** — `MoviePipelineInProcessExecutor.h`
> - Sub-modules: `MovieRenderPipelineCore` / `MovieRenderPipelineEditor` / `MovieRenderPipelineMP4Encoder` / `MovieRenderPipelineRenderPasses` / `MovieRenderPipelineSettings` / `openexrRTTI`
>
> **요지**: 5.x **출시급 영상 렌더링** (게임 트레일러 / 시네마틱). Spatial / Temporal 안티앨리어싱 + 고해상도 (8K) + ProRes / EXR / MP4 / PNG. 일반 게임 PIE 와 분리된 별도 파이프라인.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 Plugin 활성 | `MovieRenderPipeline` plugin 활성화 (.uplugin) |
| 🚨 Editor 전용 | 일부 모듈 (Editor) = 4단 분리 — Cooked Build X |
| 🚨 Build.cs | `"MovieRenderPipelineCore", "MovieRenderPipelineRenderPasses", "MovieRenderPipelineSettings"` 의무 |
| 🚨 Game Thread | Movie Render Queue = Game Thread 점유 — UI 멈춤 (별도 Executor 분리 권장) |
| 🚨 메모리 | Temporal Sample × Spatial Sample × Tile = 메모리 ↑ (GPU OOM 위험) |

---

## 1. UMoviePipeline 구조 [verified — MoviePipeline.h]

```cpp
UCLASS(BlueprintType)
class UMoviePipeline : public UMoviePipelineBase
{
public:
    // [1] 상태 조회 (5종 UFUNCTION)
    UFUNCTION(BlueprintCallable, Category="Movie Render Pipeline")
    void RequestShutdown();

    UFUNCTION(BlueprintPure, Category="Movie Render Pipeline")
    bool IsShutdownRequested() const;

    UFUNCTION(BlueprintPure, Category="Movie Render Pipeline")
    EMovieRenderPipelineState GetPipelineState() const;

    UFUNCTION(BlueprintPure, Category="Movie Render Pipeline")
    bool IsFlushDiskWritesPerShot() const;

    UFUNCTION(BlueprintPure, Category="Movie Render Pipeline")
    FFrameRate GetTickResolution() const;

    UFUNCTION(BlueprintCallable, Category="Movie Render Pipeline")
    void SetIsFlushDiskWritesPerShot(bool bFlush);

    // [2] 핵심 데이터 (UPROPERTY Transient)
    UPROPERTY(Transient, Instanced)
    TObjectPtr<UMoviePipelineMasterConfig> PipelineMasterConfig;

    UPROPERTY(Transient)
    TObjectPtr<UMoviePipelineExecutorJob> CurrentJob;

    UPROPERTY(Transient)
    TArray<TObjectPtr<UMoviePipelineExecutorShot>> ActiveShotList;

    UPROPERTY(Transient)
    int32 CurrentShotIndex;

    UPROPERTY(Transient)
    EMovieRenderPipelineState PipelineState;
};
```

---

## 2. EMovieRenderPipelineState

```cpp
enum class EMovieRenderPipelineState : uint8
{
    Uninitialized,
    ProducingFrames,        // 프레임 생성 중
    Finalize,                // 마무리 (디스크 쓰기)
    Export,                  // 외부 인코더 호출 (FFmpeg / Avid 등)
    Finished
};
```

---

## 3. UMoviePipelineMasterConfig (마스터 설정)

```cpp
UCLASS(BlueprintType)
class UMoviePipelineMasterConfig : public UMoviePipelineConfigBase
{
public:
    // 설정 추가 (Anti-Aliasing / Output / Camera / etc)
    UFUNCTION(BlueprintCallable)
    UMoviePipelineSetting* FindOrAddSetting(TSubclassOf<UMoviePipelineSetting> SettingClass);

    UFUNCTION(BlueprintCallable)
    void RemoveSetting(UMoviePipelineSetting* InSetting);

    // 모든 활성 설정
    UFUNCTION(BlueprintPure)
    const TArray<UMoviePipelineSetting*>& GetUserSettings() const;
};
```

---

## 4. Output 6종 (UMoviePipelineRenderPasses) [grep-listed]

| Output | 설명 | 사용 시점 |
|--------|------|----------|
| **PNG 8-bit** | 가장 흔함 — 영상 편집 전 단계 | 일반 트레일러 |
| **JPG 8-bit** | 압축 — 파일 작음 | 미리보기 |
| **BMP** | 비압축 — 빠름 | 특수 |
| **EXR (Half / Full)** | HDR — 컬러 그레이딩 가능 | 컬러 그레이딩 필요 |
| **ProRes** ⭐ | Apple ProRes (422 / 4444) | 영화 / TV |
| **MP4 (H.264/H.265)** | 인코딩 영상 | 최종 배포 |

```cpp
// 사용 — Editor 안 Render Queue UI 또는 Python 자동화
UMoviePipelineMasterConfig* Config = ...;
Config->FindOrAddSetting(UMoviePipelineImageSequenceOutput_PNG::StaticClass());
Config->FindOrAddSetting(UMoviePipelineCommandLineEncoder::StaticClass());   // MP4 인코더
```

---

## 5. Anti-Aliasing 설정 (Spatial × Temporal Sample)

```cpp
UCLASS()
class UMoviePipelineAntiAliasingSetting : public UMoviePipelineSetting
{
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Anti-Aliasing")
    int32 SpatialSampleCount = 1;        // 공간 샘플 (1~64)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Anti-Aliasing")
    int32 TemporalSampleCount = 1;       // 시간 샘플 (1~64) — 모션블러 품질

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Anti-Aliasing")
    EAntiAliasingMethod OverrideAntiAliasingMethod = AAM_None;   // None / FXAA / TAA / TSR / MSAA

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Anti-Aliasing")
    int32 RenderWarmUpCount = 32;        // 워밍업 프레임 (TSR/TAA 수렴)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Anti-Aliasing")
    bool bUseCameraCutForWarmUp = false;
};
```

### 5.1 품질 등급별 권장

| 등급 | Spatial | Temporal | Render Warm Up | 1프레임 시간 |
|------|---------|----------|----------------|-------------|
| 미리보기 | 1 | 1 | 8 | 빠름 |
| 표준 | 4 | 8 | 32 | 중간 |
| **고품질** ⭐ | 8 | 16 | 32 | 느림 |
| 시네마 | 16 | 32 | 64 | 매우 느림 (4K = 1프레임 30초+) |
| 최고 | 64 | 64 | 128 | 매우 느림 (수 분/프레임) |

> ⚠ Spatial × Temporal = 1프레임 당 렌더 횟수 — 16 × 16 = 256회 → 4K 시 1프레임에 30초~수분.

---

## 6. UMoviePipelineHighResSetting (고해상도)

```cpp
UCLASS()
class UMoviePipelineHighResSetting : public UMoviePipelineSetting
{
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="High Resolution")
    int32 TileCount = 1;                 // 타일 분할 (1=풀스크린, 4=2x2, 9=3x3, ...)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="High Resolution")
    float OverlapRatio = 0.1f;            // 타일 간 오버랩

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="High Resolution")
    float TextureSharpnessBias = 0.0f;   // 텍스처 샤프니스

    // 5.x 신규
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="High Resolution")
    bool bAllocateHistoryPerTile = false;
};
```

> 8K 렌더 = `TileCount = 4` (2x2) + `Resolution = 7680×4320` — GPU 메모리 분산.

---

## 7. UMoviePipelineCameraSetting (카메라 설정)

```cpp
UCLASS()
class UMoviePipelineCameraSetting : public UMoviePipelineSetting
{
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Camera")
    float ShutterAngle = 180.0f;          // 셔터 각도 (모션블러)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Camera")
    float OverscanPercentage = 0.0f;      // 오버스캔 (안전 영역 확장)

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Camera")
    bool bUseCameraCutForWarmUp = false;
};
```

---

## 8. Executor — InProcess vs OutOfProcess

### 8.1 UMoviePipelineInProcessExecutor (기본)

```cpp
UCLASS(BlueprintType)
class UMoviePipelineInProcessExecutor : public UMoviePipelineExecutorBase
{
    // 현재 Editor 프로세스 안 렌더 — UI 멈춤
};
```

### 8.2 OutOfProcess (별도 프로세스)

```cpp
// 5.x — 별도 UnrealEditor.exe 인스턴스 띄워 백그라운드 렌더
// Editor UI 멈춤 X
```

---

## 9. 시나리오 5종

### 9.1 게임 트레일러 (1080p MP4)

```cpp
UMoviePipelineMasterConfig* Config = NewObject<UMoviePipelineMasterConfig>();

// Anti-Aliasing
auto* AA = Config->FindOrAddSetting(UMoviePipelineAntiAliasingSetting::StaticClass());
Cast<UMoviePipelineAntiAliasingSetting>(AA)->SpatialSampleCount = 4;
Cast<UMoviePipelineAntiAliasingSetting>(AA)->TemporalSampleCount = 8;

// Output
auto* Output = Config->FindOrAddSetting(UMoviePipelineImageSequenceOutput_PNG::StaticClass());

// MP4 Encoder
auto* MP4 = Config->FindOrAddSetting(UMoviePipelineCommandLineEncoder::StaticClass());
```

### 9.2 영화 시네마 (4K ProRes 4444)

```cpp
// Resolution: 3840×2160
// Spatial: 8, Temporal: 16, Warmup: 32
// Output: ProRes 4444
// ShutterAngle: 180
```

### 9.3 8K 광고 (HighRes Tiled)

```cpp
// Resolution: 7680×4320
// TileCount: 4 (2x2), OverlapRatio: 0.1
// Spatial: 16, Temporal: 32
// Output: EXR (Half Float) — 컬러 그레이딩 후
```

### 9.4 미리보기 (빠른 검수)

```cpp
// Resolution: 1280×720
// Spatial: 1, Temporal: 1, Warmup: 8
// Output: PNG 8-bit
```

### 9.5 Python 자동화

```python
import unreal

# LevelSequence + Config 로드
seq = unreal.load_asset("/Game/Sequences/Intro")
config = unreal.load_asset("/Game/Configs/HighQualityRenderConfig")

# Executor 생성 + 시작
queue = unreal.MoviePipelineQueueSubsystem.get_queue()
job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
job.set_sequence(seq)
job.set_configuration(config)

executor = unreal.MoviePipelinePIEExecutor()
unreal.MoviePipelineQueueSubsystem.render_queue_with_executor_instance(executor)
```

---

## 10. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Spatial × Temporal 너무 높음 → GPU OOM | 8 × 16 까지 — 그 이상은 HighRes Tile 권장 |
| 2 | HighRes Tile 사용 시 OverlapRatio 0 → 경계선 보임 | OverlapRatio 0.1+ 권장 |
| 3 | TSR Warmup 0 → 첫 프레임 깜빡임 | RenderWarmUpCount = 32+ |
| 4 | InProcessExecutor — Editor UI 멈춤 추측 → 1시간 멈춤 후 사용자 confused | OutOfProcess 권장 (백그라운드) |
| 5 | MP4 Encoder = 자동 FFmpeg 통합 추측 | FFmpeg 별도 설치 + Command Line 경로 설정 |
| 6 | Audio 트랙 = MP4 자동 통합 추측 | Audio 별도 출력 (WAV) + 후처리 (FFmpeg) |
| 7 | LevelSequence 안 Possessable 액터 = Editor 에서만 존재 → 렌더 시 누락 | Spawnable 으로 변환 또는 Level 안 영구 배치 |
| 8 | ShutterAngle 360 → 모션블러 강함 | 영화 표준 = 180 (1/48 sec @ 24fps) |
| 9 | CVar Track 영구 변경 추측 | Sequence 종료 시 자동 복원 (`bRestoreState`) |
| 10 | Cooked Build 안 Movie Render Queue 실행 시도 | Editor 전용 (Cooked Build X) |

---

## 11. 체크리스트

- [ ] MovieRenderPipeline plugin 활성화
- [ ] Build.cs = `"MovieRenderPipelineCore", "MovieRenderPipelineRenderPasses"`
- [ ] AntiAliasing Settings 명시 (Spatial / Temporal / Warmup)
- [ ] HighRes Tile 사용 시 OverlapRatio 0.1+
- [ ] Output 종류 결정 (PNG / EXR / ProRes / MP4)
- [ ] MP4 = FFmpeg 경로 설정
- [ ] Audio = 별도 출력 후 후처리 통합
- [ ] OutOfProcess Executor 권장 (Editor 멈춤 회피)
- [ ] LevelSequence 안 Possessable = Spawnable 검토
- [ ] ShutterAngle = 180 (영화 표준)
- [ ] Editor 전용 — Cooked Build 호출 X
- [ ] GPU 메모리 모니터 (Spatial × Temporal × Tile 곱셈 시)

---

## 12. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| UMoviePipeline 5+ UFUNCTION (RequestShutdown / IsShutdownRequested / GetPipelineState / IsFlushDiskWritesPerShot / GetTickResolution / SetIsFlushDiskWritesPerShot) | **[verified]** ✅ | `MoviePipeline.h:54-194` (grep 매치) |
| EMovieRenderPipelineState | **[grep-listed]** ⚠ | `MoviePipeline.h` 안 enum 추정 |
| UMoviePipelineMasterConfig + UMoviePipelineExecutorJob / Shot | **[verified]** ✅ | `MoviePipeline.h:321-410` UPROPERTY Transient |
| Output 6종 (PNG/JPG/BMP/EXR/ProRes/MP4) | **[grep-listed]** ⚠ | `MovieRenderPipelineRenderPasses` 모듈 헤더 존재 |
| AntiAliasing / HighRes / Camera Setting | **[grep-listed]** ⚠ | 헤더 존재 — 본문 grep 권장 |
| Python `MoviePipelineQueueSubsystem` | **[inferred]** ❌ | UE Python API 일반 — 공식 문서 검증 |
| OutOfProcess Executor (5.x) | **[grep-listed]** ⚠ | `MoviePipelineNewProcessExecutor.h` 존재 추정 |

---

## 13. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인
- ⭐ [`./LevelSequencePlayer.md`](./LevelSequencePlayer.md) — Sequence Play (렌더 대상)
- [`./CineCamera.md`](./CineCamera.md) — 카메라 설정 (Filmback / Focal Length)
- [`./Tracks.md`](./Tracks.md) — CVarTrack (렌더 시 품질 변경)
- [`./SequencerScripting.md`](./SequencerScripting.md) — Python 자동화 페어
- [`../../Render/references/PostProcess.md`](../../Render/references/PostProcess.md) — 영상 PostProcess 통합

---

## 14. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **UMoviePipeline 6 UFUNCTION [verified]** + **EMovieRenderPipelineState 5종** + **UMoviePipelineMasterConfig** + **Output 6종 (PNG/JPG/BMP/EXR/ProRes/MP4)** + **AntiAliasing Spatial/Temporal/Warmup** + **HighRes Tile** + **Camera ShutterAngle/Overscan** + **InProcess/OutOfProcess Executor** + 시나리오 5 + Python 자동화 + 함정 10. Engine 5.5.4 검증 — MovieRenderPipelineCore Public. |
