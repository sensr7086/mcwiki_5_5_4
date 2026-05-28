---
type: source
title: "UE Editor — LevelEditor sub-skill 🛠 (메인 레벨 에디터 본체)"
slug: ue-editor-leveleditor
source_path: raw/ue-wiki-llm/skills/Editor/references/LevelEditor.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/IToolkit]]"
  - "[[entities/UToolMenus]]"
  - "[[entities/FUICommandList]]"
  - "[[entities/USubsystem]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, editor, leveleditor, viewport, slate, tcommands, levelviewport, sequencer, element-system]
---

# UE Editor — LevelEditor sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/LevelEditor.md]] · 13 KB raw · `Engine/Source/Editor/LevelEditor/` 19 Public 헤더

## 1. Summary

UE 에디터의 *가장 중심* — **메인 레벨 에디터** 본체. 메인 뷰포트 / 아웃라이너 / 디테일 패널 / 트랜스폼 위젯 / 툴바 / 뷰포트 클라이언트 통합. 인하우스 툴이 메인 에디터에 항목 추가 / 뷰포트 상호작용 시 진입점. 핵심 7 객체: **`FLevelEditorModule`** (모듈 진입) · **`ILevelEditor`** (`SCompoundWidget + IToolkitHost`) · **`SLevelViewport`** · **`ULevelEditorSubsystem`** (BP 헬퍼) · **`FLevelEditorCommands`** (`TCommands<T>`) · **`FLevelEditorActions`** · **`FLevelEditorContextMenu`**. 콜백 4종 (`OnLevelEditorCreated` / `OnActorSelectionChanged` / `OnComponentsEdited` / `OnRedrawLevelEditingViewports`) 으로 외부 모듈 후크.

## 2. Key claims

### 2.1. 핵심 헤더

| 헤더 | 클래스 / 라인 | 의미 |
| -- | -- | -- |
| `LevelEditor.h` | `FLevelEditorModule` L70 + `LevelEditorTabIds` L33 | 모듈 진입 + 표준 탭 ID |
| `ILevelEditor.h` | `ILevelEditor` L28 | 위젯 인터페이스 |
| `LevelEditorActions.h` | `FLevelEditorCommands` (TCommands L31) + `FLevelEditorActionCallbacks` L703 | 단축키 + 콜백 |
| `LevelEditorSubsystem.h` | `ULevelEditorSubsystem` L38 | BP 헬퍼 |
| `LevelEditorContextMenu.h` / `LevelEditorMenuContext.h` | `FLevelEditorContextMenu` / `ULevelEditorMenuContext` | 컨텍스트 메뉴 |
| `SLevelViewport.h` / `LevelViewportLayout.h` / `LevelViewportTabContent.h` | `SLevelViewport` | 뷰포트 위젯 + 레이아웃 |
| `Elements/` | (5.x) Element System | `FTypedElementSelectionSet` 진입 |

### 2.2. FLevelEditorModule 핵심 API 🟢

| API | 라인 | 의미 |
| -- | -- | -- |
| `StartupModule` / `ShutdownModule` | L80 / L85 | 모듈 라이프사이클 |
| `SummonSelectionDetails()` | L102 | 선택 디테일 호출 |
| `SummonWorldBrowser{Hierarchy,Details,Composition}()` | L110-112 | 월드 브라우저 |
| `AttachSequencer(SWidget, IAssetEditorInstance)` | L119 | 시퀀서 부착 |
| `StartPlayInEditorSession()` | L124 | PIE 시작 |
| `GoImmersiveWithActiveLevelViewport(bool)` / `ToggleImmersiveOnActiveLevelViewport()` | L129 / L134 | 몰입 모드 |
| `GetFirstLevelEditor()` / `GetLevelEditorTab()` | L137 / L140 | 첫 인스턴스 (대부분 유일) |
| `GetFirstActiveViewport()` | L147 | 첫 뷰포트 |

### 2.3. 멀티캐스트 델리게이트 4종 (외부 후크 진입점) 🟢

- **`OnLevelEditorCreated()`** ⭐ — `ILevelEditor` 인스턴스 생성. 사용자 정의 항목 추가 시점
- `OnActorSelectionChanged()` — 액터 선택 변경 (4.x). **5.x 는 Element System 권장**
- `OnComponentsEdited()` — 컴포넌트 편집
- `OnRedrawLevelEditingViewports()` — 뷰포트 재페인트

### 2.4. 표준 사용 패턴

```cpp
#if WITH_EDITOR
void FMyEditorModule::StartupModule()
{
    FLevelEditorModule& Module = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");

    Module.OnLevelEditorCreated().AddLambda([this](TSharedPtr<ILevelEditor> InLevelEditor)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_OnLevelEditorCreated);   // [[sources/ue-ref-07-profilingscopeRule]]
        // 사용자 정의 항목 추가
    });

    // 메뉴 확장 — ToolMenus 사용 권장
    UToolMenu* ToolBar = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar");
    FToolMenuSection& Section = ToolBar->FindOrAddSection("MyTools");
    Section.AddMenuEntry(...);
}
#endif
```

### 2.5. 표준 메뉴/툴바 이름 (ToolMenus 호환)

- `LevelEditor.LevelEditorToolBar` (메인 툴바) / `LevelEditor.MainMenu`
- `LevelEditor.MainMenu.File` / `.Edit` / `.Window` / `.Tools` / `.Help`
- `LevelEditor.LevelEditorViewportToolBar` (뷰포트 툴바)
- `LevelEditor.ActorContextMenu`

→ [[sources/ue-editor-toolmenus]] §2.4.

### 2.6. FLevelEditorCommands — TCommands<T> 표준 단축키

`LevelEditorActions.h:L31` — `TCommands<FLevelEditorCommands>` 자손. `FLevelEditorActionCallbacks` (L703) 가 모든 액션 실행 콜백 보유 (static 함수들).

```cpp
class FLevelEditorCommands : public TCommands<FLevelEditorCommands>
{
public:
    FLevelEditorCommands() : TCommands<FLevelEditorCommands>(
        "LevelEditor", NSLOCTEXT("..", "..", ".."), NAME_None, FAppStyle::GetAppStyleSetName()) {}
    virtual void RegisterCommands() override;     // UI_COMMAND 매크로들
    TSharedPtr<FUICommandInfo> PlayInEditor, SelectAll;
    // ... 50+
};
```

### 2.7. SLevelViewport / ULevelEditorSubsystem

**SLevelViewport** (`SLevelViewport.h`) — 4-Up / 단일 / 분할 모든 뷰포트 모드. `SEditorViewport` 자손. `FEditorViewportClient` 가 뷰포트 클라이언트 (입력 / 카메라 / 그리기). 사용자 EdMode 의 `Render` / `DrawHUD` 가 본 클라이언트에서 호출. **직접 자손 작성 권장 안 됨** — 대신 `FEditorViewportClient` 자손 + `SEditorViewport` wrap.

**ULevelEditorSubsystem** (`LevelEditorSubsystem.h:L38`) — Python / BP 노출 헬퍼. **에디터 자동화** 진입점: `EditorPlaySimulate()` / `EditorSetGameView(bool)` / `IsInPIE()` / `IsInSIE()` / `GetSelectedLevelActors()`. → [[sources/ue-subsystem-skill]].

### 2.8. 5.x Element System 통합

`Elements/` 폴더 — 4.x 의 `OnActorSelectionChanged` 가 5.x 에서 **`FTypedElementSelectionSet`** 으로 진화. Actor 외 Component / SubObject 도 선택 가능. → [[sources/ue-editor-unrealed-elements]].

### 2.9. 함정 (6대) 🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | 게임 모듈에서 `LevelEditor` 직접 의존 | 4단 분리 위반 — Editor 모듈 분리 |
| 2 | `OnActorSelectionChanged` 만 (4.x legacy) | 5.x = Element System (SubObject 누락 회피) |
| 3 | `GetFirstLevelEditor()` nullptr 가능 (Editor 시작 직후 / Commandlet) | IsValid 검사 의무 |
| 4 | `FLevelEditorCommands::Register()` 두 번 호출 | assert — 1회만 |
| 5 | `SLevelViewport` 직접 자손 | `FEditorViewportClient` 자손 + `SEditorViewport` wrap |
| 6 | `AttachSequencer` 후 detach 누락 | Sequencer 종료 시 dangling — detach 의무 |

## 3. Open questions

- 5.x `FTypedElementSelectionSet` 마이그레이션 — 기존 `OnActorSelectionChanged` 코드 이전 시점
- Multi-Viewport 시 `GetFirstActiveViewport()` 의 *active* 결정 — 마지막 클릭? 포커스?
- WorldPartition + Outliner 의 lazy load — [[sources/ue-spatialpartition-worldpartitionruntime]] 페어
- 5.x Multi-User Editing (`Concert`) 콜백 4종 트리거 여부

## 4. Cross-link

- 카테고리 main: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 자매 sub-skill: [[sources/ue-editor-toolmenus]] (메뉴 확장 진입) / [[sources/ue-editor-mainframe]] / [[sources/ue-editor-unrealed-elements]] (5.x Element System) / [[sources/ue-editor-unrealed-asseteditortoolkit]] (WorldCentric host)
- 페어 카테고리: [[sources/ue-slate-skill]] (`SEditorViewport` / Docking) / [[sources/ue-subsystem-skill]] (UEditorSubsystem)
- 5.x WorldPartition: [[sources/ue-spatialpartition-worldpartitionruntime]]
- 횡단 정책: [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-07-profilingscopeRule]]
