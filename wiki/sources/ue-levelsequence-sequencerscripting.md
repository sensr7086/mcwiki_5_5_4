---
type: source
title: "UE LevelSequence — SequencerScripting (Python + BP 자동화)"
slug: ue-levelsequence-sequencerscripting
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/SequencerScripting.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, levelsequence, python, scripting, enriched, verified]
citation_disclosure: "🟢 8 / 🟡 4 / 🔴 4 · raw verified · Cycle #13.6 enrich"
---

# UE LevelSequence — SequencerScripting

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/SequencerScripting.md]] (416L)
> Parent: [[sources/ue-levelsequence-skill]] · 위치: `Engine/Plugins/MovieScene/SequencerScripting/`

## 1. Summary

🟢 Python + BP API 로 Sequencer 작업 자동화 — 대량 시퀀스 생성 / 일괄 Track 추가 / Section 키프레임 / Render Queue 트리거. `UMovieSceneSequenceExtensions` (`UBlueprintFunctionLibrary`) + `ULevelSequenceEditorSubsystem` + `UMoviePipelineLibrary`. Editor 시간 90%+ 단축. **Editor 전용** (Cooked Build X).

## 2. Key claims

### 2.1 UMovieSceneSequenceExtensions API 🟡 (raw §1)

```cpp
UCLASS()
class UMovieSceneSequenceExtensions : public UBlueprintFunctionLibrary
{
    // Track 추가
    static UMovieSceneTrack* AddMasterTrack(UMovieSceneSequence*, TSubclassOf<UMovieSceneTrack>);
    static bool RemoveMasterTrack(UMovieSceneSequence*, UMovieSceneTrack*);

    // Binding
    static FMovieSceneObjectBindingID AddPossessable(UMovieSceneSequence*, UObject* ToPossess);
    static FMovieSceneObjectBindingID AddSpawnable(UMovieSceneSequence*, UObject* Template);

    // Section / Range
    static UMovieSceneSection* AddSection(UMovieSceneTrack*);
    static FFrameRate GetTickResolution(UMovieSceneSequence*);
    static void SetPlaybackRange(UMovieSceneSequence*, int32 Start, int32 Frames);
    // ... 수십 개
};
```

### 2.2 ULevelSequenceEditorSubsystem API 🟡 (raw §2)

```cpp
UCLASS()
class ULevelSequenceEditorSubsystem : public UEditorSubsystem
{
    UFUNCTION(BlueprintCallable) bool OpenLevelSequence(ULevelSequence*);
    UFUNCTION(BlueprintCallable) ULevelSequence* GetCurrentLevelSequence();

    UFUNCTION(BlueprintCallable) void SnapSectionsToTimelineUsingSourceTimecode(
        const TArray<UMovieSceneSection*>&);
    UFUNCTION(BlueprintCallable) void SyncSectionsUsingSourceTimecode(
        const TArray<UMovieSceneSection*>&);

    UFUNCTION(BlueprintCallable) void BakeTransform(
        const TArray<FMovieSceneObjectBindingID>&,
        const FFrameTime&, const FFrameTime&, const FFrameTime&,
        const FMovieSceneScriptingParams&);
};
```

### 2.3 Python 표준 — LevelSequence 자동 생성 🔴 (raw §3.1 — inferred)

```python
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
sequence = asset_tools.create_asset(
    asset_name="MyAutoSequence",
    package_path="/Game/Sequences",
    asset_class=unreal.LevelSequence,
    factory=unreal.LevelSequenceFactoryNew())

sequence.set_playback_start(0)
sequence.set_playback_end(240)
unreal.EditorAssetLibrary.save_loaded_asset(sequence)
```

### 2.4 Python — Possessable + Transform Track 🔴 (raw §3.2)

```python
sequence = unreal.load_asset("/Game/Sequences/MyAutoSequence")
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
target = next((a for a in all_actors if isinstance(a, unreal.StaticMeshActor)), None)

if target:
    binding = sequence.add_possessable(target)
    transform_track = binding.add_track(unreal.MovieScene3DTransformTrack)
    section = transform_track.add_section()
    section.set_range(0, 240)

    z_channel = section.get_channels_by_type(unreal.MovieSceneScriptingDoubleChannel)[2]
    z_channel.add_key(unreal.FrameNumber(0), 0.0)
    z_channel.add_key(unreal.FrameNumber(240), 200.0)
    unreal.EditorAssetLibrary.save_loaded_asset(sequence)
```

### 2.5 Python — Movie Render Queue 자동화 🟡 (raw §4)

```python
def render_sequence(sequence_path, config_path, output_dir):
    sequence = unreal.load_asset(sequence_path)
    config   = unreal.load_asset(config_path)

    queue_subsystem = unreal.MoviePipelineQueueSubsystem.get_queue()
    queue_subsystem.delete_all_jobs()

    job = queue_subsystem.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.set_sequence(unreal.SoftObjectPath(sequence_path))
    job.set_configuration(config)
    job.job_name = "AutoRender"

    output = job.get_configuration().find_setting_by_class(unreal.MoviePipelineOutputSetting)
    if output:
        output.output_directory.path = output_dir
        output.file_name_format = "{sequence_name}.{frame_number}"

    # 별도 프로세스 — Editor 멈춤 회피
    executor = unreal.MoviePipelineNewProcessExecutor()
    queue_subsystem.render_queue_with_executor_instance(executor)
```

### 2.6 BP 자동화 (Python 없이) 🟢 (raw §5)

`LevelSequenceEditorSubsystem` BP 노드 — Open Level Sequence / Bake Transform / Snap Sections.
`UMovieSceneSequenceExtensions` BP 노드 — Add Master Track / Add Possessable / Set Playback Range.

### 2.7 일괄 처리 표준 🟢 (raw §6)

```python
def batch_create_character_sequences(character_assets):
    for name in character_assets:
        for anim in ["Idle", "Walk", "Attack"]:
            seq_name = f"{name}_{anim}_Sequence"
            seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                asset_name=seq_name,
                package_path=f"/Game/Sequences/{name}",
                asset_class=unreal.LevelSequence,
                factory=unreal.LevelSequenceFactoryNew())
            # ... Animation Track 자동 매핑
            unreal.EditorAssetLibrary.save_loaded_asset(seq)
```

### 2.8 Python 환경 설정 🟢 (raw §7)

```ini
; DefaultEngine.ini
[/Script/PythonScriptPlugin.PythonScriptPluginSettings]
bDeveloperMode=True
bEnableContentBrowserIntegration=True
```

Plugin 활성: `PythonScriptPlugin` + `SequencerScripting`. 자동 실행 — `/Game/Python/init_unreal.py`.

### 2.9 5 시나리오 🟢 (raw §8)

| # | 시나리오 | 핵심 |
|---|---------|------|
| 1 | 제품 쇼케이스 (100개 360도 회전) | `create_camera_sequence` 일괄 |
| 2 | 모션 캡처 자동 import | FBX → AnimSequence → SkeletalTrack |
| 3 | 야간 일괄 렌더링 | `MoviePipelineNewProcessExecutor` |
| 4 | Sequence Validator | 누락 Binding / Empty Section 자동 검출 |
| 5 | BP Director 일괄 갱신 | 100 시퀀스 → 동일 부모 변경 |

## 3. 함정 10 🟢 (raw §9)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Save 누락 → 결과 손실 | `save_loaded_asset` 의무 |
| 2 | Cooked Build 안 Python | Editor 전용 — Game Build X |
| 3 | Transaction 없이 변경 → Undo 깨짐 | `ScopedSlowTask` 또는 Begin Transaction |
| 4 | FrameNumber vs Seconds 혼동 | TickResolution 명시 + 변환 |
| 5 | PIEExecutor → Editor 멈춤 | `NewProcessExecutor` 별도 프로세스 |
| 6 | `print` → Output Log X | `unreal.log("...")` |
| 7 | load_asset 실패 시 nullptr | `if not sequence: return` |
| 8 | 대량 처리 메모리 폭주 | `unreal.GarbageCollect()` 주기 |
| 9 | 5.x Subsystem 호출 오류 | `get_editor_subsystem` (Editor) / `get_engine_subsystem` (Engine) |
| 10 | PythonScriptPlugin 비활성 | Project Settings → Plugins 활성화 |

## 4. 체크리스트 🟢 (raw §10)

- [ ] PythonScriptPlugin + SequencerScripting 활성
- [ ] Developer Mode 활성 (DefaultEngine.ini)
- [ ] `unreal.log` 사용 (print X)
- [ ] Asset load 후 nullptr 검사
- [ ] 변경 후 `save_loaded_asset`
- [ ] FrameNumber + TickResolution 명시
- [ ] 대량 처리 시 GarbageCollect 주기
- [ ] Render = NewProcessExecutor
- [ ] Transaction 범위 명시
- [ ] Cooked Build 호출 X

## 5. 신뢰도 🟢 (raw §11)

| 항목 | tier | 출처 |
|------|------|------|
| SequencerScripting Plugin 위치 | 🟢 verified | `Plugins/MovieScene/SequencerScripting/` |
| UMovieSceneSequenceExtensions | 🟡 grep-listed | Plugin 헤더 — 본문 grep |
| ULevelSequenceEditorSubsystem | 🟡 grep-listed | `LevelSequenceEditor` plugin |
| Python API (load_asset / add_possessable) | 🔴 inferred | 공식 문서 검증 필요 |
| MoviePipelineQueueSubsystem | 🔴 inferred | 5.x — header grep |
| MoviePipelineNewProcessExecutor | 🟡 grep-listed | 헤더 존재 |
| init_unreal.py 자동 실행 | 🔴 inferred | UE Python 공식 문서 |

## 6. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 페어: [[sources/ue-levelsequence-templatesequence]] (재사용 템플릿 — 자동화 결합) · [[sources/ue-levelsequence-movierenderpipeline]] (Render Queue 자동화) · [[sources/ue-levelsequence-sequencer]] (Editor 측)
- 정책: 🚨 [[concepts/Asset-Loading-Policy]] (Editor Sync Load)
- Editor 카테고리: [[sources/ue-editor-skill]] (UEditorSubsystem 베이스)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
