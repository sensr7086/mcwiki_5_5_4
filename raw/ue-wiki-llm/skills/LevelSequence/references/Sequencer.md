---
name: levelsequence-sequencer
description: 🛠 Sequencer Editor — FSequencer + ISequencer + ISequencerTrackEditor + ISequencerSection + MovieSceneTrackEditor. Custom Track UI 작성 (Detail Customization + Drag-Drop + Context Menu). LevelSequenceEditor plugin (ULevelSequenceEditorSubsystem). 4단 분리 원칙 의무.
---

# LevelSequence/Sequencer — Editor 측 (Custom Track UI) 🛠

> **위치 (verified)**:
> - **Sequencer Editor** — `Engine/Source/Editor/Sequencer/Public/` (25+ 헤더 — ISequencer / ISequencerTrackEditor / ISequencerSection 등)
> - **MovieSceneTools** — `Engine/Source/Editor/MovieSceneTools/Public/` (트랙 별 Editor 커스터마이징)
> - **SequencerCore** — `Engine/Source/Editor/SequencerCore/`
> - **SequencerWidgets** — `Engine/Source/Editor/SequencerWidgets/`
> - **LevelSequenceEditor** Plugin — `Engine/Plugins/MovieScene/LevelSequenceEditor/Source/LevelSequenceEditor/`
>
> **요지**: Sequencer 의 **Editor 측 확장**. Custom Track 의 UI / Drag-Drop / Context Menu / Detail 패널 커스터마이징. **Editor 전용** — 4단 분리 의무.

---

## 🚨 공통 정책 (의무)

| 정책 | 적용 |
|------|------|
| 🚨 [`05_EditorOnlyIndex`](../../../references/05_EditorOnlyIndex.md) | **모든 코드 `WITH_EDITOR` 가드 + Editor 모듈 분리 (4단)** |
| 🚨 Build.cs | Editor 모듈만 `"Sequencer", "SequencerCore", "SequencerWidgets", "MovieSceneTools", "LevelSequenceEditor"` |
| 🚨 [`11_AssetLoadingPolicy §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-) | Editor Pure 모드 = Sync Load |
| 🚨 Custom Track | Runtime UMovieSceneTrack 자손 / Editor 측 ISequencerTrackEditor 자손 = **2개 모듈 분리** |
| 🚨 Module 등록 | StartupModule 안 `ISequencerModule::RegisterTrackEditor` + ShutdownModule 시 Unregister 페어 |

---

## 1. Sequencer Editor 핵심 인터페이스 [verified — Sequencer/Public/]

| 인터페이스 | 책임 |
|----------|------|
| `ISequencer` | Sequencer 메인 — Selection / Add Track / Add Key |
| `ISequencerModule` | 모듈 진입점 — TrackEditor 등록 |
| `ISequencerTrackEditor` | ⭐⭐ 트랙별 Editor 커스터마이징 (Add 메뉴 / 컨텍스트) |
| `ISequencerSection` | Section UI (그리기 / 편집) |
| `ISequencerChannelInterface` | Channel UI (FloatChannel / IntChannel 등) |
| `ISequencerObjectChangeListener` | Object 변경 감지 (Sequencer 외부에서 변경 시) |
| `ISequencerNumericTypeInterface` | 숫자 입력 UI 커스터마이징 |
| `ISequencerEditorObjectBinding` | Object Binding UI (외부 Add 메뉴) |
| `IKeyArea` | 키프레임 그리기 |
| `MovieSceneTrackEditor` (베이스) | TrackEditor 베이스 클래스 (`FMovieSceneTrackEditor`) |

---

## 2. Custom Track Editor 작성 표준 ⭐

### 2.1 모듈 분리 (4단 분리 의무)

```
[Runtime 모듈] MyTrackRuntime/
├── Build.cs : "MovieScene", "MovieSceneTracks", "Engine"
├── UMyMovieSceneTrack (UMovieSceneTrack 자손)
└── UMyMovieSceneSection (UMovieSceneSection 자손)

[Editor 모듈] MyTrackEditor/
├── Type = "Editor" (uplugin 안)
├── Build.cs : "Sequencer", "MovieSceneTools", "SequencerCore", "MyTrackRuntime"
├── FMyMovieSceneTrackEditor (FMovieSceneTrackEditor 자손)
└── FMyTrackEditorModule (StartupModule 안 등록)
```

### 2.2 FMovieSceneTrackEditor 자손 작성

```cpp
// MyTrackEditor.h (Editor 모듈)
#if WITH_EDITOR
#include "MovieSceneTrackEditor.h"
#include "ISequencerTrackEditor.h"

class FMyMovieSceneTrackEditor : public FMovieSceneTrackEditor
{
public:
    FMyMovieSceneTrackEditor(TSharedRef<ISequencer> InSequencer)
        : FMovieSceneTrackEditor(InSequencer)
    {}

    // [Factory] — ISequencerModule 안 등록 시 호출
    static TSharedRef<ISequencerTrackEditor> CreateTrackEditor(TSharedRef<ISequencer> InSequencer)
    {
        return MakeShared<FMyMovieSceneTrackEditor>(InSequencer);
    }

    // === Track 지원 검증 ===
    virtual bool SupportsType(TSubclassOf<UMovieSceneTrack> TrackClass) const override
    {
        return TrackClass == UMyMovieSceneTrack::StaticClass();
    }

    virtual bool SupportsSequence(UMovieSceneSequence* InSequence) const override
    {
        return InSequence && InSequence->IsA<ULevelSequence>();
    }

    // === Add Track 메뉴 항목 ===
    virtual void BuildAddTrackMenu(FMenuBuilder& MenuBuilder) override
    {
        MenuBuilder.AddMenuEntry(
            FText::FromString(TEXT("My Custom Track")),
            FText::FromString(TEXT("Add custom track for ...")),
            FSlateIcon(),
            FUIAction(FExecuteAction::CreateRaw(this, &FMyMovieSceneTrackEditor::HandleAddCustomTrack))
        );
    }

    // === 트랙 추가 핸들러 ===
    void HandleAddCustomTrack()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(FMyMovieSceneTrackEditor::HandleAddCustomTrack);
        UMovieSceneSequence* Sequence = GetSequencer()->GetFocusedMovieSceneSequence();
        UMovieScene* MovieScene = Sequence ? Sequence->GetMovieScene() : nullptr;
        if (!MovieScene) return;

        const FScopedTransaction Transaction(NSLOCTEXT("MyTrack", "AddCustomTrack", "Add Custom Track"));
        MovieScene->Modify();

        UMyMovieSceneTrack* NewTrack = MovieScene->AddTrack<UMyMovieSceneTrack>();
        UMovieSceneSection* NewSection = NewTrack->CreateNewSection();
        NewSection->SetRange(TRange<FFrameNumber>::All());
        NewTrack->AddSection(*NewSection);

        GetSequencer()->NotifyMovieSceneDataChanged(EMovieSceneDataChangeType::MovieSceneStructureItemAdded);
    }

    // === Section UI 빌드 ===
    virtual TSharedRef<ISequencerSection> MakeSectionInterface(
        UMovieSceneSection& SectionObject,
        UMovieSceneTrack& Track,
        FGuid ObjectBinding) override;
};
#endif
```

### 2.3 Module Startup 등록

```cpp
// MyTrackEditorModule.cpp
class FMyTrackEditorModule : public IModuleInterface
{
public:
    virtual void StartupModule() override
    {
        ISequencerModule& SequencerModule =
            FModuleManager::LoadModuleChecked<ISequencerModule>("Sequencer");

        TrackEditorHandle = SequencerModule.RegisterTrackEditor(
            FOnCreateTrackEditor::CreateStatic(&FMyMovieSceneTrackEditor::CreateTrackEditor)
        );
    }

    virtual void ShutdownModule() override
    {
        if (ISequencerModule* SequencerModule = FModuleManager::GetModulePtr<ISequencerModule>("Sequencer"))
        {
            SequencerModule->UnRegisterTrackEditor(TrackEditorHandle);
        }
    }

private:
    FDelegateHandle TrackEditorHandle;
};

IMPLEMENT_MODULE(FMyTrackEditorModule, MyTrackEditor)
```

---

## 3. ISequencerSection 작성 (UI 그리기)

```cpp
class FMyMovieSceneSectionUI : public ISequencerSection
{
public:
    FMyMovieSceneSectionUI(UMovieSceneSection& InSection)
        : Section(&InSection)
    {}

    // === Section 위치 / 사이즈 ===
    virtual UMovieSceneSection* GetSectionObject() override { return Section; }
    virtual FText GetSectionTitle() const override
    {
        return FText::FromString(TEXT("My Section"));
    }

    // === Section 그리기 ===
    virtual int32 OnPaintSection(FSequencerSectionPainter& InPainter) const override
    {
        return InPainter.PaintSectionBackground();
    }

    // === 컨텍스트 메뉴 ===
    virtual void BuildSectionContextMenu(FMenuBuilder& MenuBuilder, const FGuid& ObjectBinding) override
    {
        MenuBuilder.AddMenuEntry(
            FText::FromString(TEXT("Custom Action")),
            FText::GetEmpty(),
            FSlateIcon(),
            FUIAction(FExecuteAction::CreateLambda([]() { /* ... */ }))
        );
    }

private:
    UMovieSceneSection* Section;
};
```

---

## 4. LevelSequenceEditor Plugin 확장 [grep-listed]

`Plugins/MovieScene/LevelSequenceEditor/` — LevelSequence 전용 Editor 확장.

```cpp
// ULevelSequenceEditorSubsystem (5.x — Editor API)
UCLASS()
class ULevelSequenceEditorSubsystem : public UEditorSubsystem
{
public:
    // BP / Python 호출 가능 — 자동화 API
    UFUNCTION(BlueprintCallable, Category="Level Sequence Editor")
    bool OpenLevelSequence(ULevelSequence* InLevelSequence);

    UFUNCTION(BlueprintCallable, Category="Level Sequence Editor")
    ULevelSequence* GetCurrentLevelSequence();

    // ... 기타 자동화 API
};
```

> 자세한 자동화 = [`SequencerScripting.md`](./SequencerScripting.md).

---

## 5. ISequencer 핵심 API (Editor 안 호출)

```cpp
class ISequencer
{
public:
    // === Sequence 접근 ===
    virtual UMovieSceneSequence* GetFocusedMovieSceneSequence() const = 0;
    virtual UMovieSceneSequence* GetRootMovieSceneSequence() const = 0;

    // === 시간 ===
    virtual FQualifiedFrameTime GetGlobalTime() const = 0;
    virtual void SetGlobalTime(FFrameTime NewTime) = 0;
    virtual FFrameRate GetFocusedDisplayRate() const = 0;
    virtual FFrameRate GetFocusedTickResolution() const = 0;

    // === 변경 알림 ===
    virtual void NotifyMovieSceneDataChanged(EMovieSceneDataChangeType DataChangeType) = 0;
    virtual void NotifyBindingsChanged() = 0;

    // === Selection ===
    virtual FSequencerSelection& GetSelection() = 0;

    // === Refresh ===
    virtual void RefreshTree() = 0;
};
```

---

## 6. EMovieSceneDataChangeType (변경 알림)

```cpp
enum class EMovieSceneDataChangeType : uint8
{
    MovieSceneStructureItemAdded,        // Track/Section 추가
    MovieSceneStructureItemRemoved,       // 제거
    MovieSceneStructureItemsChanged,      // 일괄 변경
    TrackValueChanged,                    // 트랙 값 변경
    TrackValueChangedRefreshImmediately,  // 즉시 갱신
    RefreshAllImmediately,                // 모두 즉시 갱신
    Unknown
};
```

---

## 7. Sequencer 안 Custom Section 데이터 UI

### 7.1 Detail Customization (Section Property 패널)

```cpp
// IDetailCustomization 자손 — Section 의 Details 패널 변경
class FMyMovieSceneSectionDetails : public IDetailCustomization
{
public:
    static TSharedRef<IDetailCustomization> MakeInstance()
    {
        return MakeShared<FMyMovieSceneSectionDetails>();
    }

    virtual void CustomizeDetails(IDetailLayoutBuilder& DetailBuilder) override
    {
        // 자세한 패턴 = Editor/PropertyEditor sub-skill 참조
    }
};

// 등록 (StartupModule 안)
auto& PropertyModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");
PropertyModule.RegisterCustomClassLayout(
    UMyMovieSceneSection::StaticClass()->GetFName(),
    FOnGetDetailCustomizationInstance::CreateStatic(&FMyMovieSceneSectionDetails::MakeInstance)
);
```

---

## 8. 시나리오 4종

### 8.1 게임 전용 트랙 (Inventory / Quest)

```
1. UMyInventoryTrack (UMovieSceneTrack 자손) — Runtime
2. UMyInventorySection (UMovieSceneSection 자손) — Runtime
3. FMyInventoryTrackEditor (FMovieSceneTrackEditor 자손) — Editor
4. FMyInventorySectionUI (ISequencerSection 자손) — Editor
→ Sequencer 안 Add Track 메뉴에 "Inventory" 등장
```

### 8.2 비주얼 디버그 트랙 (개발 전용)

```cpp
// Editor 안 Sequence 안 마커 / 메모 / 디버그 정보
class FDebugMarkerTrackEditor : public FMovieSceneTrackEditor
{
    // OnPaintSection — 마커 그리기 (색상 / 텍스트)
};
```

### 8.3 Audio Cue 미리보기

```cpp
// AudioTrack 안 Wave 파형 미리보기 (Editor only)
// MovieSceneToolsModule 안 이미 구현됨 — 참고
```

### 8.4 Sequence 안 외부 트랙 자동 추가

```cpp
// Possessable 액터 Drop 시 자동 Transform 트랙 생성
class FMyObjectBindingExtension : public ISequencerEditorObjectBinding
{
    // Drag-Drop 시 Default Track 생성 로직
};
```

---

## 9. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | UMovieSceneTrack 자손 = Editor 모듈 작성 (Cooked 깨짐) | Runtime 모듈 / TrackEditor만 Editor 모듈 |
| 2 | StartupModule 안 `RegisterTrackEditor` 후 Unregister 누락 | ShutdownModule 페어 |
| 3 | `WITH_EDITOR` 가드 누락 → Cooked Build 깨짐 | 모든 Sequencer 헤더 include = `#if WITH_EDITOR` |
| 4 | Editor TrackEditor 안 무거운 작업 (매 Tick UI 갱신) | NotifyMovieSceneDataChanged 호출 — 자동 최적화 |
| 5 | Section 그리기 `OnPaintSection` 안 매번 객체 생성 | 캐싱 + 한 번 그리기 |
| 6 | `EMovieSceneDataChangeType::Unknown` 사용 → 전체 재컴파일 | 정확한 타입 (ItemAdded/Removed/Changed) |
| 7 | `GetSequencer()` 호출 시 lifetime 확인 X | TWeakPtr 보관 + Pin() IsValid 검사 |
| 8 | Transaction 없이 변경 → Undo/Redo 깨짐 | `FScopedTransaction` 의무 + `MovieScene->Modify()` |
| 9 | Section 컨텍스트 메뉴 Lambda 안 외부 변수 캡처 | WeakLambda + IsValid 검사 |
| 10 | TrackEditor 안 Render Thread 접근 | Editor = Game Thread 전용 (Sequencer 도 Game Thread) |

---

## 10. 체크리스트

- [ ] Runtime / Editor 모듈 4단 분리
- [ ] uplugin Type = Editor (TrackEditor 모듈)
- [ ] Build.cs = Sequencer / MovieSceneTools / SequencerCore 의존
- [ ] `WITH_EDITOR` 가드 모든 Sequencer include
- [ ] StartupModule 안 RegisterTrackEditor + ShutdownModule Unregister
- [ ] `FMovieSceneTrackEditor::SupportsType` / `SupportsSequence` override
- [ ] `BuildAddTrackMenu` 안 추가 항목 등록
- [ ] HandleAddCustomTrack = `FScopedTransaction` + `Modify()`
- [ ] `NotifyMovieSceneDataChanged` 호출 (변경 시)
- [ ] ISequencerSection MakeSectionInterface override
- [ ] Section 그리기 = 캐싱 + 한 번 (매 Tick X)

---

## 11. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| Sequencer Public 헤더 25+ (ISequencer / ITrackEditor / ISection / ...) | **[verified]** ✅ | `Source/Editor/Sequencer/Public/` ls (25+ 확인) |
| FMovieSceneTrackEditor 베이스 | **[grep-listed]** ⚠ | `MovieSceneTrackEditor.h` 헤더 존재 |
| ISequencerModule::RegisterTrackEditor / UnRegisterTrackEditor | **[inferred]** ❌ | UE 일반 — 본문 grep 필요 |
| EMovieSceneDataChangeType 7종 | **[inferred]** ❌ | UE 일반 — enum grep 권장 |
| ULevelSequenceEditorSubsystem | **[grep-listed]** ⚠ | `LevelSequenceEditor` 플러그인 헤더 존재 |
| ISequencer API (GetFocusedMovieSceneSequence / SetGlobalTime / NotifyMovieSceneDataChanged) | **[inferred]** ❌ | UE 일반 — `ISequencer.h` grep 권장 |

---

## 12. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인
- [`./MovieScene.md`](./MovieScene.md) — Runtime Track/Section 베이스
- [`./Tracks.md`](./Tracks.md) — 빌트인 트랙 43종
- [`./SequencerScripting.md`](./SequencerScripting.md) — Python / BP 자동화
- 🚨 [`../../../references/05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) — 4단 분리 의무
- [`../../Editor/SKILL.md`](../../Editor/SKILL.md) — Editor 카테고리
- [`../../Editor/references/PropertyEditor.md`](../../Editor/references/PropertyEditor.md) — Detail Customization

---

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **Sequencer Editor 핵심 인터페이스 9종** + **FMovieSceneTrackEditor 자손 작성 표준** (SupportsType / BuildAddTrackMenu / HandleAddCustomTrack / MakeSectionInterface) + **Module StartupModule 등록 페어** + **ISequencerSection** (OnPaintSection / BuildSectionContextMenu) + **ULevelSequenceEditorSubsystem** + **ISequencer API** + **EMovieSceneDataChangeType** + **Detail Customization** + 시나리오 4 + 함정 10. Engine 5.7.4 검증 — Source/Editor/Sequencer/Public ls. |
