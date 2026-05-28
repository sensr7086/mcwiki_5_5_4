---
type: source
title: "UE Editor — EditorFramework sub-skill 🛠 (IToolkit / UEdMode 베이스)"
slug: ue-editor-editorframework
source_path: raw/ue-wiki-llm/skills/Editor/references/EditorFramework.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-12
related_entities:
  - "[[entities/IToolkit]]"
  - "[[entities/UEdMode]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, editor, editorframework, itoolkit, uedmode, placement, element-system]
---

# UE Editor — EditorFramework sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/EditorFramework.md]] · 11 KB raw · `Editor/EditorFramework/` 20 헤더

## 1. Summary

UnrealEd 가 의존하는 **에디터 베이스 모듈**. Editor 모듈 중 *가장 가볍고 의존성 적음* — 인하우스 툴 작성 시 베이스로 자주 사용. 책임 4가지: (1) **`IToolkit` / `IToolkitHost`** 인터페이스 정의 — UnrealEd 의 `FAssetEditorToolkit` 이 구현, (2) **`UEdMode`** — 5.x InteractiveTool 진입점 (`FEdMode` legacy 후계), (3) **`UPlacementSubsystem`** — 5.x 액터 배치 추상화, (4) **`UEditorElementSubsystem`** — 5.x Typed Element System Editor 어댑터.

## 2. Key claims

### 2.1. 파일 카테고리 8

| 카테고리 | 헤더 |
| -- | -- |
| Toolkits | `IToolkit.h` · `IToolkitHost.h` · `ToolkitManager.h` · `AssetEditorModeUILayer.h` |
| Tools / EdMode | `Tools/Modes.h` · `Tools/AssetEditorContextInterface.h` · `EditorModes.h` |
| Subsystems | `Subsystems/EditorElementSubsystem.h` · `Subsystems/PlacementSubsystem.h` |
| Elements (5.x) | `Elements/Framework/TypedElement*.h` · `Elements/Interfaces/TypedElementDetailsInterface.h` |
| Factories | `Factories/AssetFactoryInterface.h` |
| Viewport | `EditorViewportLayout.h` · `ViewportTabContent.h` · `InViewportUIDragOperation.h` · `SDepthBar.h` |
| Styling | `DepthBarStyle.h` |
| 모듈 | `EditorFrameworkModule.h` · `UnrealWidgetFwd.h` |

### 2.2. IToolkit (인터페이스) — `FAssetEditorToolkit` 이 구현

PURE_VIRTUAL 5종: `GetToolkitFName()` / `GetBaseToolkitName()` / `GetWorldCentricTabPrefix()` / `GetWorldCentricTabColorScale()` / `GetWorkspaceMenuCategory()` / `GetEditorModeManager()`.

추가 virtual: `RegisterTabSpawners` / `UnregisterTabSpawners` / `BringToolkitToFront()` / `GetInlineContent()` / `IsAssetEditor()` / `IsHosted()` / `GetToolkitHost()`.

### 2.3. IToolkitHost (인터페이스) — `SStandaloneAssetEditorToolkitHost` 가 구현

PURE_VIRTUAL: `GetParentWidget()` / `GetTabManager()` / `GetWorld()` / `GetEditorModeManager()`.

추가: `BringToFront()` / `GetTabSpot(EToolkitTabSpot::Type)` / `OnToolkitHostingStarted/Finished(TSharedRef<IToolkit>)`.

### 2.4. FToolkitManager — 활성 Toolkit 글로벌

```cpp
FToolkitManager::Get().RegisterNewToolkit(MyToolkit);
FToolkitManager::Get().CloseToolkit(MyToolkit);
```

### 2.5. UEdMode — 5.x InteractiveTool 진입점

`Tools/Modes.h` — `FEdMode` (legacy) 후계. UCLASS 기반 — BP/Python 노출 가능.

핵심 virtual: `Enter()` / `Exit()` / `Tick(FEditorViewportClient*, float DeltaTime)` / `MouseMove` / `InputKey` / `InputAxis` / `Render(const FSceneView*, FViewport*, FPrimitiveDrawInterface*)` / `DrawHUD(...)` / `IsCompatibleWith(FEditorModeID)` — 다른 모드와 공존 가능 여부.

5.x **InteractiveToolsFramework** 통합 — `UEdMode` 자손이 `UInteractiveToolManager` 보유 → 모달 도구 (예: Modeling Mode) 등록.

### 2.6. UPlacementSubsystem (5.x) — 액터 배치 추상화

`Subsystems/PlacementSubsystem.h` — 컨텐츠 브라우저 드래그→레벨 / Place Actors 패널 / 프로시저럴 배치의 공통 진입. `IAssetFactoryInterface` (`Factories/AssetFactoryInterface.h`) 자손이 각 에셋 타입의 배치 동작 정의.

### 2.7. UEditorElementSubsystem (5.x) — Typed Element 어댑터

`Subsystems/EditorElementSubsystem.h` — Actor / Component / SubObject 통합 선택 시스템의 Editor 측 어댑터. 4.x `OnActorSelectionChanged` 의 5.x 후계 (→ [[sources/ue-editor-leveleditor]] §2.9).

### 2.8. 함정

- `IToolkit` 구현 시 PURE_VIRTUAL 5종 미구현 → 컴파일 에러
- `FEdMode` (legacy) 신규 코드 사용 → 5.x `UEdMode` 표준
- `OnToolkitHostingStarted` 안 Super 호출 의무
- `UEdMode::Render` / `DrawHUD` 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` ([[concepts/Editor-Only-4-Tier-Separation]] / [[concepts/Profiling-Scope-Rule]])
- `UPlacementSubsystem` 외 직접 SpawnActor 시도 (Place Actors 통합 깨짐)

### 2.9. Build.cs

```csharp
PrivatePublicDependencyModuleNames.AddRange(new[] {
    "EditorFramework", "EditorSubsystem",
    "InteractiveToolsFramework",
    "TypedElementFramework", "TypedElementRuntime"
});
```

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]] (`FAssetEditorToolkit` 자손이 `IToolkit` 구현)
- 페어: [[sources/ue-editor-unrealed-asseteditortoolkit]] (Toolkit 구현체) / [[sources/ue-editor-unrealed-elements]] (5.x Typed Element) / [[sources/ue-editor-unrealed-subsystems]] (UAssetEditorSubsystem 페어)
- 횡단: [[sources/ue-ref-04-overrideindex]] §6 (Super 규약) · [[sources/ue-ref-05-editoronlyindex]]
- 5.x InteractiveTools: [[sources/ue-editor-leveleditor]] (Element System)
