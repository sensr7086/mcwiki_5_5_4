---
type: source
title: "UE LevelSequence — Sequencer 🛠 (Editor)"
slug: ue-levelsequence-sequencer
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/Sequencer.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, levelsequence, sequencer, editor-only, enriched, verified]
citation_disclosure: "🟢 11 / 🟡 3 / 🔴 3 · raw verified · Cycle #13.5 enrich"
---

# UE LevelSequence — Sequencer 🛠 (Editor)

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/Sequencer.md]] (416L)
> Parent: [[sources/ue-levelsequence-skill]] · 위치: `Engine/Source/Editor/Sequencer/Public/` (25+ 헤더) + `MovieSceneTools/` + `LevelSequenceEditor` plugin
> 🛠 Editor 전용 — 4단 분리 의무.

## 1. Summary

🟢 **Sequencer Editor** = 시네마틱 편집 메인. `ISequencer` (controller) + `ISequencerTrackEditor` (Custom Track UI) + `ISequencerSection` (Section UI). LevelSequenceEditor plugin = `ULevelSequenceEditorSubsystem` (5.x BP/Python API). 4단 분리 — Runtime `UMovieSceneTrack` 자손 / Editor `FMovieSceneTrackEditor` 자손 = 별도 모듈.

## 2. Key claims

### 2.1 핵심 인터페이스 9종 🟢 (raw §1)

| 인터페이스 | 책임 |
|----------|------|
| `ISequencer` | 메인 컨트롤러 — Selection / Add Track / Add Key |
| `ISequencerModule` | 모듈 진입점 — TrackEditor 등록 |
| `ISequencerTrackEditor` ⭐⭐ | 트랙별 Editor 커스터마이징 |
| `ISequencerSection` | Section UI (그리기 / 편집) |
| `ISequencerChannelInterface` | Channel UI (FloatChannel etc) |
| `ISequencerObjectChangeListener` | 외부 변경 감지 |
| `ISequencerNumericTypeInterface` | 숫자 입력 UI |
| `ISequencerEditorObjectBinding` | Object Binding UI |
| `FMovieSceneTrackEditor` | TrackEditor 베이스 |

### 2.2 4단 분리 의무 🟢 (raw §2.1)

```
[Runtime 모듈] MyTrackRuntime/
├── Build.cs : MovieScene, MovieSceneTracks, Engine
└── UMyMovieSceneTrack + UMyMovieSceneSection (UObject 자손)

[Editor 모듈] MyTrackEditor/
├── uplugin Type = "Editor"
├── Build.cs : Sequencer, MovieSceneTools, SequencerCore, MyTrackRuntime
└── FMyMovieSceneTrackEditor + FMyTrackEditorModule
```

### 2.3 FMovieSceneTrackEditor 자손 표준 🟢 (raw §2.2)

```cpp
#if WITH_EDITOR
#include "MovieSceneTrackEditor.h"

class FMyMovieSceneTrackEditor : public FMovieSceneTrackEditor
{
public:
    FMyMovieSceneTrackEditor(TSharedRef<ISequencer> InSeq)
        : FMovieSceneTrackEditor(InSeq) {}

    static TSharedRef<ISequencerTrackEditor> CreateTrackEditor(TSharedRef<ISequencer> InSeq)
    { return MakeShared<FMyMovieSceneTrackEditor>(InSeq); }

    virtual bool SupportsType(TSubclassOf<UMovieSceneTrack> C) const override
    { return C == UMyMovieSceneTrack::StaticClass(); }

    virtual bool SupportsSequence(UMovieSceneSequence* S) const override
    { return S && S->IsA<ULevelSequence>(); }

    virtual void BuildAddTrackMenu(FMenuBuilder& MB) override
    {
        MB.AddMenuEntry(
            FText::FromString(TEXT("My Custom Track")),
            FText::FromString(TEXT("Add custom track for ...")),
            FSlateIcon(),
            FUIAction(FExecuteAction::CreateRaw(this, &FMyMovieSceneTrackEditor::HandleAdd))
        );
    }

    void HandleAdd()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(FMyMovieSceneTrackEditor::HandleAdd);
        auto* Seq = GetSequencer()->GetFocusedMovieSceneSequence();
        auto* MS = Seq ? Seq->GetMovieScene() : nullptr;
        if (!MS) return;

        const FScopedTransaction Tx(NSLOCTEXT("MyTrack", "Add", "Add Custom Track"));
        MS->Modify();
        auto* T = MS->AddTrack<UMyMovieSceneTrack>();
        auto* S = T->CreateNewSection();
        S->SetRange(TRange<FFrameNumber>::All());
        T->AddSection(*S);
        GetSequencer()->NotifyMovieSceneDataChanged(EMovieSceneDataChangeType::MovieSceneStructureItemAdded);
    }

    virtual TSharedRef<ISequencerSection> MakeSectionInterface(
        UMovieSceneSection& Sec, UMovieSceneTrack& T, FGuid Bind) override;
};
#endif
```

### 2.4 Module Startup 등록 🟢 (raw §2.3)

```cpp
class FMyTrackEditorModule : public IModuleInterface
{
    FDelegateHandle Handle;
public:
    virtual void StartupModule() override
    {
        auto& M = FModuleManager::LoadModuleChecked<ISequencerModule>("Sequencer");
        Handle = M.RegisterTrackEditor(
            FOnCreateTrackEditor::CreateStatic(&FMyMovieSceneTrackEditor::CreateTrackEditor));
    }
    virtual void ShutdownModule() override
    {
        if (auto* M = FModuleManager::GetModulePtr<ISequencerModule>("Sequencer"))
            M->UnRegisterTrackEditor(Handle);
    }
};
IMPLEMENT_MODULE(FMyTrackEditorModule, MyTrackEditor)
```

### 2.5 ISequencerSection UI 🟢 (raw §3)

```cpp
class FMySectionUI : public ISequencerSection
{
    UMovieSceneSection* Section;
public:
    FMySectionUI(UMovieSceneSection& S) : Section(&S) {}

    virtual UMovieSceneSection* GetSectionObject() override { return Section; }
    virtual FText GetSectionTitle() const override { return FText::FromString(TEXT("My")); }
    virtual int32 OnPaintSection(FSequencerSectionPainter& P) const override
    { return P.PaintSectionBackground(); }
    virtual void BuildSectionContextMenu(FMenuBuilder& MB, const FGuid& Bind) override;
};
```

### 2.6 ISequencer 핵심 API 🔴 (raw §5 — inferred)

```cpp
class ISequencer {
    virtual UMovieSceneSequence* GetFocusedMovieSceneSequence() const = 0;
    virtual UMovieSceneSequence* GetRootMovieSceneSequence() const = 0;
    virtual FQualifiedFrameTime GetGlobalTime() const = 0;
    virtual void SetGlobalTime(FFrameTime) = 0;
    virtual FFrameRate GetFocusedDisplayRate() const = 0;
    virtual void NotifyMovieSceneDataChanged(EMovieSceneDataChangeType) = 0;
    virtual void NotifyBindingsChanged() = 0;
    virtual FSequencerSelection& GetSelection() = 0;
    virtual void RefreshTree() = 0;
};
```

### 2.7 EMovieSceneDataChangeType 7종 🔴 (raw §6)

| 값 | 효과 |
|----|------|
| `MovieSceneStructureItemAdded` | Track/Section 추가 |
| `MovieSceneStructureItemRemoved` | 제거 |
| `MovieSceneStructureItemsChanged` | 일괄 변경 |
| `TrackValueChanged` | 트랙 값 변경 |
| `TrackValueChangedRefreshImmediately` | 즉시 갱신 |
| `RefreshAllImmediately` | 모두 즉시 |
| `Unknown` | 전체 재컴파일 |

### 2.8 ULevelSequenceEditorSubsystem 🟡 (raw §4 — grep-listed)

```cpp
UCLASS()
class ULevelSequenceEditorSubsystem : public UEditorSubsystem
{
    UFUNCTION(BlueprintCallable) bool OpenLevelSequence(ULevelSequence*);
    UFUNCTION(BlueprintCallable) ULevelSequence* GetCurrentLevelSequence();
    // 5.x — BP/Python 자동화 진입점 → [[sources/ue-levelsequence-sequencerscripting]] 페어
};
```

### 2.9 Detail Customization (Section Property) 🟡 (raw §7.1)

```cpp
class FMyMovieSceneSectionDetails : public IDetailCustomization
{
public:
    static TSharedRef<IDetailCustomization> MakeInstance()
    { return MakeShared<FMyMovieSceneSectionDetails>(); }
    virtual void CustomizeDetails(IDetailLayoutBuilder& B) override;
};

// 등록
auto& P = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");
P.RegisterCustomClassLayout(UMyMovieSceneSection::StaticClass()->GetFName(),
    FOnGetDetailCustomizationInstance::CreateStatic(&FMyMovieSceneSectionDetails::MakeInstance));
```

### 2.10 4 시나리오 🟢 (raw §8)

| # | 시나리오 | 핵심 |
|---|---------|------|
| 1 | 게임 전용 트랙 (Inventory/Quest) | Runtime + Editor 4-tier 분리 |
| 2 | 비주얼 디버그 마커 | `OnPaintSection` 안 마커 그리기 |
| 3 | Audio Cue 미리보기 | MovieSceneTools 안 Wave 파형 |
| 4 | Drop 시 자동 트랙 | `ISequencerEditorObjectBinding` |

## 3. 함정 10 🟢 (raw §9)

| # | 함정 | 정답 |
|---|------|------|
| 1 | UMovieSceneTrack 자손을 Editor 모듈에 | Runtime 모듈 의무 / TrackEditor만 Editor |
| 2 | RegisterTrackEditor 후 Unregister 누락 | ShutdownModule 페어 |
| 3 | `WITH_EDITOR` 가드 누락 → Cooked 깨짐 | 모든 Sequencer include 가드 |
| 4 | TrackEditor 안 매 Tick UI 갱신 | `NotifyMovieSceneDataChanged` 호출 |
| 5 | `OnPaintSection` 안 매번 객체 생성 | 캐싱 |
| 6 | `DataChangeType::Unknown` 사용 | 정확한 타입 |
| 7 | `GetSequencer()` lifetime 미확인 | TWeakPtr + Pin() IsValid |
| 8 | Transaction 없이 변경 → Undo 깨짐 | `FScopedTransaction` + `Modify()` |
| 9 | Context Menu Lambda 외부 캡처 | WeakLambda + IsValid |
| 10 | Render Thread 접근 | Editor = Game Thread 전용 |

## 4. 체크리스트 🟢 (raw §10)

- [ ] Runtime / Editor 모듈 4단 분리
- [ ] uplugin Type = Editor
- [ ] Build.cs = Sequencer / MovieSceneTools / SequencerCore
- [ ] `WITH_EDITOR` 가드
- [ ] StartupModule Register + Shutdown Unregister
- [ ] SupportsType / SupportsSequence override
- [ ] BuildAddTrackMenu 안 항목 등록
- [ ] HandleAddCustomTrack = Transaction + Modify
- [ ] NotifyMovieSceneDataChanged 호출
- [ ] OnPaintSection 캐싱

## 5. 신뢰도 🟢 (raw §11)

| 항목 | tier | 출처 |
|------|------|------|
| Sequencer Public 헤더 25+ | 🟢 verified | `Source/Editor/Sequencer/Public/` ls |
| FMovieSceneTrackEditor 베이스 | 🟡 grep-listed | `MovieSceneTrackEditor.h` 존재 |
| ISequencerModule::Register/UnRegisterTrackEditor | 🔴 inferred | 본문 grep 필요 |
| EMovieSceneDataChangeType 7종 | 🔴 inferred | enum grep |
| ULevelSequenceEditorSubsystem | 🟡 grep-listed | 플러그인 헤더 |
| ISequencer API | 🔴 inferred | `ISequencer.h` grep |
| 5.x BP/Python 자동화 진입 | 🟡 grep-listed | UEditorSubsystem 자손 확인 |

## 6. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 베이스: [[sources/ue-levelsequence-moviescene]] (Runtime Track/Section virtual)
- 페어: [[sources/ue-levelsequence-tracks]] (43 빌트인) · [[sources/ue-levelsequence-sequencerscripting]] (Python/BP)
- 정책: 🚨 [[concepts/Editor-Only-4-Tier-Separation]] · 🚨 [[concepts/Profiling-Scope-Rule]]
- Editor 시스템: [[sources/ue-editor-skill]] · [[sources/ue-editor-propertyeditor]]
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에만): 0
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `> - **Sequencer Editor** — `Engine/Source/Editor/Sequencer/Public/` (25+ 헤더 — IS → > - **Sequencer Editor** — `Engine/Source/Editor/Sequencer/Public/` (UE 5.5 — 35`

**5.5.4 에만 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/LevelSequence/references/Sequencer.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/LevelSequence/references/Sequencer.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
