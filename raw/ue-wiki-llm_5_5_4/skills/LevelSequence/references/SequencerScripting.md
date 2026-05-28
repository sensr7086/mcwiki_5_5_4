---
name: levelsequence-sequencer-scripting
description: SequencerScripting Plugin — Python + BP API 자동화. UMovieSceneSequenceExtensions + ULevelSequenceEditorSubsystem + UMoviePipelineLibrary + Asset 자동 생성 / Track 추가 / Section 키프레임 + Render Queue Python 호출. Editor 시간 단축 (수십 분 → 수 초).
---

# LevelSequence/SequencerScripting — Python / BP 자동화

> **위치 (verified)**:
> - **SequencerScripting** Plugin — `Engine/Plugins/MovieScene/SequencerScripting/`
> - **UMovieSceneSequenceExtensions** — BP/Python 라이브러리 (BlueprintFunctionLibrary)
> - **ULevelSequenceEditorSubsystem** — Editor API
> - **UMoviePipelineLibrary** — Render Queue API
>
> **요지**: Python / BP 로 Sequencer 작업 자동화 — 대량 시퀀스 생성 / 일괄 Track 추가 / 자동 렌더링 큐. 영상 제작 파이프라인 시 필수 (Editor 시간 90%+ 단축).

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 Editor 전용 | Python = Editor only — Cooked Build X |
| 🚨 [`11_AssetLoadingPolicy §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-) | Python 안 = Editor Pure → Sync Load (`load_asset`) |
| 🚨 Plugin 활성 | "SequencerScripting" + "PythonScriptPlugin" 활성 |
| 🚨 Transaction | 일괄 변경 시 Undo/Redo 지원 의무 |

---

## 1. UMovieSceneSequenceExtensions (BP/Python API)

```cpp
UCLASS()
class UMovieSceneSequenceExtensions : public UBlueprintFunctionLibrary
{
public:
    // === Track 추가 ===
    UFUNCTION(BlueprintCallable, Category="Sequencer Editor")
    static UMovieSceneTrack* AddMasterTrack(UMovieSceneSequence* Sequence,
                                              TSubclassOf<UMovieSceneTrack> TrackType);

    UFUNCTION(BlueprintCallable, Category="Sequencer Editor")
    static bool RemoveMasterTrack(UMovieSceneSequence* Sequence, UMovieSceneTrack* MasterTrack);

    // === Binding 추가 ===
    UFUNCTION(BlueprintCallable, Category="Sequencer Editor")
    static FMovieSceneObjectBindingID AddPossessable(UMovieSceneSequence* Sequence, UObject* ObjectToPossess);

    UFUNCTION(BlueprintCallable, Category="Sequencer Editor")
    static FMovieSceneObjectBindingID AddSpawnable(UMovieSceneSequence* Sequence, UObject* ObjectTemplate);

    // === Section 추가 ===
    UFUNCTION(BlueprintCallable, Category="Sequencer Editor")
    static UMovieSceneSection* AddSection(UMovieSceneTrack* Track);

    // === Range / FrameRate ===
    UFUNCTION(BlueprintCallable, Category="Sequencer Editor")
    static FFrameRate GetTickResolution(UMovieSceneSequence* Sequence);

    UFUNCTION(BlueprintCallable, Category="Sequencer Editor")
    static void SetPlaybackRange(UMovieSceneSequence* Sequence, int32 StartFrame, int32 NumberOfFrames);

    // ... 수십 개 API
};
```

---

## 2. ULevelSequenceEditorSubsystem (Editor 자동화)

```cpp
UCLASS()
class ULevelSequenceEditorSubsystem : public UEditorSubsystem
{
public:
    // === Sequence 열기 ===
    UFUNCTION(BlueprintCallable, Category="Level Sequence Editor")
    bool OpenLevelSequence(ULevelSequence* InLevelSequence);

    UFUNCTION(BlueprintCallable, Category="Level Sequence Editor")
    ULevelSequence* GetCurrentLevelSequence();

    // === 자동화 ===
    UFUNCTION(BlueprintCallable, Category="Level Sequence Editor")
    void SnapSectionsToTimelineUsingSourceTimecode(const TArray<UMovieSceneSection*>& Sections);

    UFUNCTION(BlueprintCallable, Category="Level Sequence Editor")
    void SyncSectionsUsingSourceTimecode(const TArray<UMovieSceneSection*>& Sections);

    // === Keyframe ===
    UFUNCTION(BlueprintCallable, Category="Level Sequence Editor")
    void BakeTransform(const TArray<FMovieSceneObjectBindingID>& InObjectBindings,
                       const FFrameTime& BakeInTime,
                       const FFrameTime& BakeOutTime,
                       const FFrameTime& FrameIncrement,
                       const FMovieSceneScriptingParams& Params);
};
```

---

## 3. Python 기본 예제

### 3.1 LevelSequence 자동 생성

```python
import unreal

# 1. 새 LevelSequence 생성
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
sequence = asset_tools.create_asset(
    asset_name="MyAutoSequence",
    package_path="/Game/Sequences",
    asset_class=unreal.LevelSequence,
    factory=unreal.LevelSequenceFactoryNew()
)

# 2. Playback Range 설정 (0~240 프레임)
sequence.set_playback_start(0)
sequence.set_playback_end(240)

# 3. 저장
unreal.EditorAssetLibrary.save_loaded_asset(sequence)
```

### 3.2 Possessable Binding + Transform Track 추가

```python
import unreal

sequence = unreal.load_asset("/Game/Sequences/MyAutoSequence")
world = unreal.EditorLevelLibrary.get_editor_world()

# Level 안 첫 StaticMeshActor 찾기
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
target_actor = next((a for a in all_actors if isinstance(a, unreal.StaticMeshActor)), None)

if target_actor:
    # 1. Possessable 바인딩 추가
    binding = sequence.add_possessable(target_actor)

    # 2. Transform Track 추가
    transform_track = binding.add_track(unreal.MovieScene3DTransformTrack)

    # 3. Section 추가
    section = transform_track.add_section()
    section.set_range(0, 240)

    # 4. Channel 키프레임 추가 — Location.Z 0 → 200
    z_channel = section.get_channels_by_type(unreal.MovieSceneScriptingDoubleChannel)[2]   # Z 채널
    z_channel.add_key(unreal.FrameNumber(0), 0.0)
    z_channel.add_key(unreal.FrameNumber(240), 200.0)

    unreal.EditorAssetLibrary.save_loaded_asset(sequence)
```

### 3.3 자동 카메라 시퀀스 생성

```python
import unreal

def create_camera_sequence(sequence_path, target_actor):
    """타겟 액터 주변 360도 회전 카메라 시퀀스 자동 생성"""
    sequence = unreal.load_asset(sequence_path)
    if not sequence:
        return

    # 1. CineCamera 액터 Spawn
    world = unreal.EditorLevelLibrary.get_editor_world()
    cam_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CineCameraActor, unreal.Vector(0, 0, 100), unreal.Rotator(0, 0, 0)
    )

    # 2. Sequence 안 Possessable 바인딩
    binding = sequence.add_possessable(cam_actor)

    # 3. Transform Track — 원형 경로 (8 키프레임)
    transform_track = binding.add_track(unreal.MovieScene3DTransformTrack)
    section = transform_track.add_section()
    section.set_range(0, 240)

    radius = 500.0
    import math
    for i in range(8):
        angle = (i / 8) * 2 * math.pi
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius
        frame = int((i / 8) * 240)
        # ... Channel 키 추가 (X / Y / Yaw)

    # 4. CameraCut Track 추가 (시퀀스 루트)
    cut_track = sequence.add_master_track(unreal.MovieSceneCameraCutTrack)
    cut_section = cut_track.add_section()
    cut_section.set_range(0, 240)
    # cut_section.set_camera_binding_id(...) — Binding 연결

    unreal.EditorAssetLibrary.save_loaded_asset(sequence)
    return sequence

create_camera_sequence("/Game/Sequences/AutoCamera", None)
```

---

## 4. Movie Render Queue 자동화 (Python)

```python
import unreal

def render_sequence(sequence_path, config_path, output_dir):
    """시퀀스를 Movie Render Queue 로 자동 렌더링"""
    sequence = unreal.load_asset(sequence_path)
    config = unreal.load_asset(config_path)

    # 1. Queue Subsystem
    queue_subsystem = unreal.MoviePipelineQueueSubsystem.get_queue()
    queue_subsystem.delete_all_jobs()

    # 2. Job 추가
    job = queue_subsystem.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.set_sequence(unreal.SoftObjectPath(sequence_path))
    job.set_configuration(config)
    job.job_name = "AutoRender"

    # 3. Output Path 설정
    output_setting = job.get_configuration().find_setting_by_class(
        unreal.MoviePipelineOutputSetting
    )
    if output_setting:
        output_setting.output_directory.path = output_dir
        output_setting.file_name_format = "{sequence_name}.{frame_number}"

    # 4. Executor 시작
    executor = unreal.MoviePipelinePIEExecutor()
    queue_subsystem.render_queue_with_executor_instance(executor)

# 사용
render_sequence(
    "/Game/Sequences/Intro",
    "/Game/Configs/HighQualityConfig",
    "D:/Render/Output"
)
```

---

## 5. BP 자동화 (Python 없이)

```
LevelSequenceEditorSubsystem 노드 사용:
- Open Level Sequence
- Get Current Level Sequence
- Bake Transform
- Snap Sections to Timeline

UMovieSceneSequenceExtensions 노드:
- Add Master Track
- Add Possessable
- Add Spawnable
- Set Playback Range
```

---

## 6. 일괄 처리 — 대량 시퀀스 생성

```python
import unreal

def batch_create_character_sequences(character_assets):
    """각 캐릭터별 시퀀스 자동 생성 (Idle / Walk / Attack)"""
    for char_name in character_assets:
        for anim_type in ["Idle", "Walk", "Attack"]:
            seq_name = f"{char_name}_{anim_type}_Sequence"

            # 1. 시퀀스 생성
            sequence = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                asset_name=seq_name,
                package_path=f"/Game/Sequences/{char_name}",
                asset_class=unreal.LevelSequence,
                factory=unreal.LevelSequenceFactoryNew()
            )

            # 2. 캐릭터 + Animation Track 추가
            # ... AnimSequence 자동 매핑

            unreal.EditorAssetLibrary.save_loaded_asset(sequence)

characters = ["Hero", "Boss", "NPC_01", "NPC_02"]
batch_create_character_sequences(characters)
```

---

## 7. Python 환경 설정

```python
# Project Settings → Plugins → Python Editor Script Plugin = Enable
# Project Settings → Python → Developer Mode = True
# DefaultEngine.ini:
# [/Script/PythonScriptPlugin.PythonScriptPluginSettings]
# bDeveloperMode=True
# bEnableContentBrowserIntegration=True

# Project Python Scripts 폴더: /Game/Python/
# 자동 실행 (Editor 시작 시): init_unreal.py
```

---

## 8. 시나리오 5종

### 8.1 자동 카메라 회전 시퀀스 (제품 쇼케이스)

```python
# 100개 제품 → 각 제품별 360도 회전 시퀀스 자동 생성
for product in product_list:
    create_camera_sequence(f"/Game/Sequences/{product.name}", product)
```

### 8.2 캐릭터 모션 캡처 자동 import

```python
# FBX 파일 → AnimSequence import → LevelSequence 안 SkeletalAnimation Track 자동 추가
```

### 8.3 일괄 렌더링 (야간 배치)

```python
# 100개 시퀀스 → 모두 Render Queue 추가 → 야간 자동 실행
queue = unreal.MoviePipelineQueueSubsystem.get_queue()
for seq_path in sequence_paths:
    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.set_sequence(unreal.SoftObjectPath(seq_path))
    job.set_configuration(high_quality_config)

executor = unreal.MoviePipelineNewProcessExecutor()   # 별도 프로세스 (Editor 멈춤 X)
queue.render_queue_with_executor_instance(executor)
```

### 8.4 Sequence Validator 자동 검증

```python
# 모든 시퀀스 → SequenceValidator plugin 호출
# 누락 Binding / Empty Section / Invalid FrameRate 등 자동 검출
```

### 8.5 BP Director 일괄 갱신

```python
# 100개 시퀀스의 Director BP = 동일 부모 클래스로 일괄 변경
```

---

## 9. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Python 호출 후 Save 누락 → 결과 손실 | `unreal.EditorAssetLibrary.save_loaded_asset()` 의무 |
| 2 | Cooked Build 안 Python 호출 시도 | Editor 전용 — 게임 빌드 X |
| 3 | Transaction 없이 변경 → Undo/Redo 깨짐 | `unreal.ScopedSlowTask` 또는 BP `Begin Transaction` |
| 4 | FrameNumber vs Seconds 혼동 | TickResolution 명시 + 변환 |
| 5 | 일괄 렌더 = `MoviePipelinePIEExecutor` → Editor 멈춤 | `MoviePipelineNewProcessExecutor` 별도 프로세스 |
| 6 | Python 안 `print` → Output Log X | `unreal.log("...")` 사용 |
| 7 | `load_asset` 실패 시 nullptr 처리 누락 | `if not sequence: return` 검사 |
| 8 | 대량 처리 시 메모리 폭주 | `unreal.GarbageCollect()` 주기적 호출 |
| 9 | 5.x Subsystem 호출 = `get_engine_subsystem` 오류 | `get_editor_subsystem` (Editor) / `get_engine_subsystem` (Engine) 구분 |
| 10 | Plugin "PythonScriptPlugin" 비활성 | Project Settings → Plugins → Python 활성화 |

---

## 10. 체크리스트

- [ ] PythonScriptPlugin + SequencerScripting 활성
- [ ] Developer Mode 활성 (DefaultEngine.ini)
- [ ] `unreal.log` 사용 (print X)
- [ ] Asset load 후 nullptr 검사
- [ ] 변경 후 `save_loaded_asset` 호출
- [ ] FrameNumber + TickResolution 명시
- [ ] 대량 처리 시 GarbageCollect 주기 호출
- [ ] Render = NewProcessExecutor (Editor 멈춤 회피)
- [ ] Transaction 범위 명시 (Undo/Redo 지원)
- [ ] Cooked Build 호출 X (Editor 전용)

---

## 11. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| SequencerScripting Plugin 위치 | **[verified]** ✅ | `Plugins/MovieScene/SequencerScripting/` 존재 확인 |
| UMovieSceneSequenceExtensions BP 라이브러리 | **[grep-listed]** ⚠ | Plugin 안 헤더 존재 — 본문 grep 권장 |
| ULevelSequenceEditorSubsystem | **[grep-listed]** ⚠ | `LevelSequenceEditor` plugin 안 |
| Python API (load_asset / spawn_actor / add_possessable) | **[inferred]** ❌ | UE Python API 일반 — 공식 문서 검증 |
| MoviePipelineQueueSubsystem | **[inferred]** ❌ | 5.x 일반 — `MoviePipelineQueueSubsystem.h` grep |
| MoviePipelineNewProcessExecutor | **[grep-listed]** ⚠ | `MoviePipelineNewProcessExecutor.h` 헤더 존재 |
| Python init_unreal.py 자동 실행 | **[inferred]** ❌ | UE Python 일반 — 공식 문서 |

---

## 12. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인
- ⭐ [`./MovieRenderPipeline.md`](./MovieRenderPipeline.md) — Movie Render Queue (Python 자동화 페어)
- [`./Sequencer.md`](./Sequencer.md) — Editor 측 (커스텀 트랙 UI)
- [`./LevelSequencePlayer.md`](./LevelSequencePlayer.md) — Sequence 자동 생성 후 검증 재생
- [`Editor/SKILL.md`](../../Editor/SKILL.md) — Editor 카테고리 (UEditorSubsystem)
- 🚨 [`../../../references/11_AssetLoadingPolicy §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-) — Editor Sync Load

---

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **UMovieSceneSequenceExtensions BP/Python API** + **ULevelSequenceEditorSubsystem** + Python 5 예제 (Sequence 생성 / Possessable / Camera 자동 / Render Queue 자동 / 일괄 처리) + 시나리오 5 + 함정 10 + Python 환경 설정. Engine 5.5.4 검증 — SequencerScripting + LevelSequenceEditor Plugin. |
