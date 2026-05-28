---
name: unrealed-main
description: Editor 전용 UnrealEd 모듈 메인 🛠 — AssetEditorToolkit + Subsystems + Kismet2 + Factories + Elements + Layers + MaterialEditor + Misc 8개 sub-skill. 모두 에디터 전용 — 게임 모듈 의존 금지. 4단 분리 표준.
---

# UnrealEd Module — 메인 SKILL.md

> **카테고리**: `[Slate]` 인하우스 툴 (🛠 에디터 전용 — `WITH_EDITOR` / Build.cs `Type=Editor` 의무)
> **위치**: `Engine/Source/Editor/UnrealEd/`
> **사이즈**: Public 329 + Classes 388 = **717 헤더** (가장 큰 Editor 모듈)
> **빌드 보호**: `Build.cs` 첫 줄에서 `if(!Target.bCompileAgainstEditor) throw new BuildException("Unable to instantiate UnrealEd module for non-editor targets.")` — **에디터 빌드에서만** 사용 가능

---

## 1. 개요

UE 에디터의 **본체 모듈**. 거의 모든 인하우스 에셋 에디터·레벨 도구·BP 컴파일·임포트 파이프라인의 베이스가 여기 있다. 단일 모듈이지만 분량이 거대하므로 본 위키에서는 **8개 sub-skill 로 분할**.

> 🚨 **에디터 분리 4단 방어 의무**: 본 모듈을 사용하는 모든 코드는 [`Slate/SKILL.md §8`](../Slate/SKILL.md) + [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) 의 4단 방어(모듈 분리·uplugin Type=Editor·Build.cs 분기·`#if WITH_EDITOR` 가드) 준수. **게임 모듈에서 직접 의존 금지**.

---

## 2. 의존·빌드 (UnrealEd.Build.cs 요약)

### 2.1 PublicDependencyModuleNames (50+ 모듈)

| 카테고리 | 모듈 |
|----------|------|
| **Core** | `Core` · `CoreUObject` · `ApplicationCore` · `Engine` · `Json` · `Projects` |
| **Slate UI** | `Slate` · `SlateCore` · `UMG` · `EditorFramework` · `ToolMenusEditor` · `ToolWidgets` · `StatusBar` · `WidgetRegistration` |
| **Asset 시스템** | `AssetDefinition` · `AssetTools` · `SourceControl` · `UncontrolledChangelists` · `DirectoryWatcher` · `SandboxFile` |
| **5.x Element System** | `TypedElementFramework` · `TypedElementRuntime` |
| **Interactive Tools** | `InteractiveToolsFramework` · `SubobjectDataInterface` · `SubobjectEditor` |
| **5.x Interchange** | `InterchangeCore` · `InterchangeEngine` |
| **Blueprint** | `BlueprintGraph` |
| **테스트/통신** | `FunctionalTesting` · `AutomationController` · `HTTP` · `NetworkFileSystem` · `UnrealEdMessages` |
| **Audio/Localization** | `AudioEditor` · `Localization` |
| **Mesh** | `MeshDescription` · `StaticMeshDescription` · `MeshBuilder` |
| **기타 에디터** | `EditorSubsystem` · `Documentation` · `MaterialShaderQualitySettings` · `NavigationSystem` · `PhysicsUtilities` · `GameplayTasks` · `TargetPlatform` · `CommonMenuExtensions` · `DeveloperToolSettings` |

### 2.2 PrivateIncludePathModuleNames (20+ 모듈)

`StructViewer` · `MainFrame` · `TurnkeySupport` · `MessagingCommon` · `MovieSceneCapture` · `PlacementMode` · `SettingsEditor` · `ViewportSnapping` · `SourceCodeAccess` · `OutputLog` · `PortalServices` · `PhysicsAssetEditor` · `Media` · `VirtualTexturingEditor` · `HotReload` · `StaticMeshEditor` · `WorkspaceMenuStructure` · `LandscapeEditor` · `Blutility` · `SlateReflector` · `PackagesDialog` · `GraphEditor` · `SourceControlWindows`

### 2.3 빌드 PCH

- `PrivatePCHHeaderFile = "Private/UnrealEdPrivatePCH.h"`
- `SharedPCHHeaderFile = "Public/UnrealEdSharedPCH.h"`
- `bEnableExceptions = !Target.bUseAutoRTFMCompiler` — 예외 활성

---

## 3. 디렉토리 구조 (대분류)

### 3.1 Public/ (24개 1차 디렉토리)

```
Public/
├── Toolkits/             ✅ AssetEditorToolkit · BaseToolkit · SimpleAssetEditor · GlobalEditorCommonCommands
├── Subsystems/           ✅ AssetEditorSubsystem · EditorActorSubsystem · EditorAssetSubsystem · ImportSubsystem 등 12개
├── Kismet2/              ✅ BlueprintEditorUtils · KismetEditorUtilities · CompilerResultsLog · DebuggerCommands
├── Elements/             ✅ FTypedElementSelectionSet 5.x System
├── EditorState/          (sub-skill: Misc) FEditorState · 에디터 상태 보존
├── Layers/               ✅ FLayers · 레이어 시스템
├── Bookmarks/            ✅ UWorldBookmark · 카메라 북마크
├── DragAndDrop/          (sub-skill: Misc) FAssetDragDropOp 등
├── Settings/             (sub-skill: Misc) UEditorPerProjectUserSettings 등
├── ImportUtils/          (sub-skill: Misc + Factories)
├── ViewportToolbar/      (sub-skill: Misc)
├── WorkflowOrientedApp/  ✅ AssetEditorToolkit과 통합
├── WorldPartition/       ✅ Layers와 통합
├── AutoReimport/         (sub-skill: Factories)
├── Commandlets/          (sub-skill: Misc)
├── Dialogs/              (sub-skill: Misc)
├── Editor/               (sub-skill: Misc)
├── Features/             (sub-skill: Misc)
├── Instances/            (sub-skill: Misc)
├── Serialization/        (sub-skill: Misc)
├── Tests/                (sub-skill: Misc)
├── Text/                 (sub-skill: Misc)
└── Tools/                (sub-skill: Misc)
```

### 3.2 Classes/ (UCLASS 정의 — 17개 1차 디렉토리)

```
Classes/
├── ActorFactories/        ✅ UActorFactory 자손 → Factories sub-skill
├── Animation/             (sub-skill: Misc) Animation 에디터 클래스
├── Builders/              (sub-skill: Misc) Builder Brush
├── Commandlets/           (sub-skill: Misc) Editor 전용 commandlets
├── CookOnTheSide/         (sub-skill: Misc) Cook 헬퍼
├── Editor/                ✅ UEditorEngine 등 (Subsystems와 통합)
├── Exporters/             ✅ UExporter 자손 → Factories sub-skill
├── Factories/             ✅ UFactory 자손 (가장 큼) → Factories sub-skill
├── MaterialEditor/        ✅ MaterialEditor sub-skill
├── MaterialGraph/         ✅ UMaterialGraph 등 → MaterialEditor sub-skill
├── Preferences/           (sub-skill: Misc) Preferences UCLASS
├── Settings/              (sub-skill: Misc) Settings UCLASS
├── ThumbnailRendering/    (sub-skill: Misc) UThumbnailRenderer 자손
└── UserDefinedStructure/  (sub-skill: Kismet2) UUserDefinedStruct 에디터
```

---

## 4. Sub-skill 인덱스 (8개)

각 sub-skill 은 *개요 → 핵심 헤더/클래스 → 자주 쓰는 API → virtual → 예제 → 에디터 전용 → 함정 → 관련 sub-skill* 의 8섹션 구조를 따른다.

| # | Sub-skill | 다루는 영역 | 주요 헤더/심볼 |
|---|-----------|-------------|----------------|
| 1 | [`AssetEditorToolkit/`](./AssetEditorToolkit/SKILL.md) 🛠 | **인하우스 에셋 에디터 작성 표준** — `FAssetEditorToolkit` · `BaseToolkit` · `SimpleAssetEditor` · `FWorkflowCentricApplication` · `IToolkitHost` · `FExtensibilityManager` + Toolbar/Tabs/Modes 등록 | `Public/Toolkits/*.h` + `Public/WorkflowOrientedApp/*.h` |
| 2 | [`Subsystems/`](./Subsystems/SKILL.md) 🛠 | 에디터 서브시스템 12개 — `UAssetEditorSubsystem` · `UEditorActorSubsystem` · `UEditorAssetSubsystem` · `UImportSubsystem` · `UPanelExtensionSubsystem` · `UPropertyVisibilityOverrideSubsystem` 등 | `Public/Subsystems/*.h` + `EditorSubsystem` 모듈 |
| 3 | [`Kismet2/`](./Kismet2/SKILL.md) 🛠 | 블루프린트 통합 — `FBlueprintEditorUtils` · `FKismetEditorUtilities` · `FCompilerResultsLog` · `FKismetReinstanceUtilities` · `FDebuggerCommands` + UUserDefinedStruct 에디터 | `Public/Kismet2/*.h` + `Classes/UserDefinedStructure/*.h` |
| 4 | [`Factories/`](./Factories/SKILL.md) 🛠 | Asset 임포트 파이프라인 — `UFactory` · `UActorFactory` · `UExporter` · Reimport 인터페이스 + Interchange 통합 | `Classes/Factories/*.h` + `Classes/ActorFactories/*.h` + `Classes/Exporters/*.h` + `Public/AutoReimport/` |
| 5 | [`Elements/`](./Elements/SKILL.md) 🛠 | 5.x Element Selection System — `FTypedElementSelectionSet` · `ITypedElementWorldInterface` · `FTypedElementHandle` | `Public/Elements/*.h` + `TypedElementFramework`/`TypedElementRuntime` 모듈 |
| 6 | [`Layers/`](./Layers/SKILL.md) 🛠 | Layers · Bookmarks · WorldPartition 에디터 통합 | `Public/Layers/*.h` + `Public/Bookmarks/*.h` + `Public/WorldPartition/*.h` |
| 7 | [`MaterialEditor/`](./MaterialEditor/SKILL.md) 🛠 | Material 에디터 통합 — `UMaterialGraph` · `UMaterialGraphNode` · `UMaterialEditingLibrary` | `Classes/MaterialEditor/*.h` + `Classes/MaterialGraph/*.h` |
| 8 | [`Misc/`](./Misc/SKILL.md) 🛠 | Settings · Preferences · ImportUtils · Tools · ViewportToolbar · Dialogs · Animation · Builders · CookOnTheSide · ThumbnailRendering 기타 유틸 | `Public/Settings/`/`Tools/`/`Dialogs/`/`Text/`/`Tests/`/etc. + `Classes/Settings/`/`Preferences/`/`Animation/`/etc. |

---

## 5. 🚨 작성·인용 규칙 (UnrealEd 사용 시 의무)

### 5.1 4단 분리 방어

UnrealEd 본체는 게임 빌드(Shipping/Test/Server)에서 **컴파일에서 빠진다**. 사용 시:

1. **모듈 분리** — 인하우스 툴은 별도 `Editor` 모듈로 분리 (Build.cs `Type=Editor`)
2. **uplugin** — 플러그인이라면 `"Type": "Editor"` (런타임 모듈은 별도 `Type=Runtime`)
3. **Build.cs 분기** — `if (Target.bBuildEditor)` 또는 `if (Target.Type == TargetType.Editor)` 안에서만 의존 추가
4. **`#if WITH_EDITOR` 가드** — UnrealEd 헤더 include + 사용 코드 모두 가드

자세한 [`Slate/SKILL.md §8`](../Slate/SKILL.md) + [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

### 5.2 Toolkit 라이프사이클 의무

`FAssetEditorToolkit` 자손 작성 시:

- `InitAssetEditor(...)` 첫 줄에서 `Super 호출 X` (자손이 호출하는 게 베이스를 트리거)
- `RegisterTabSpawners` / `UnregisterTabSpawners` 는 **반드시 Super 호출** ([`04_OverrideIndex.md §6`](../../references/04_OverrideIndex.md))
- `GetToolkitFName` / `GetBaseToolkitName` / `GetWorldCentricTabPrefix` / `GetWorldCentricTabColorScale` 는 **PURE_VIRTUAL** — 의무 구현
- 소멸 시 `OnRequestClose` 가 false 면 닫기 거부 가능 (저장 미완료 등)

### 5.3 Subsystem 사용 표준

```cpp
// 게임 모듈에서는 직접 접근 X — Editor 모듈에서만
#if WITH_EDITOR
if (UAssetEditorSubsystem* Sub = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>())
{
    Sub->OpenEditorForAsset(MyAsset);
}
#endif
```

### 5.4 프로파일링 스코프 의무

UnrealEd 콜백·Subsystem Tick·Toolkit `Tick`/`OnRequestClose` 등 모든 매 프레임/델리게이트 진입점에 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) 의 스코프 부착.

---

## 6. 자주 쓰는 진입점 (1줄 — 자세한 건 각 sub-skill)

| 시나리오 | 진입점 | sub-skill |
|----------|--------|-----------|
| 새 인하우스 에셋 에디터 | `FAssetEditorToolkit` 상속 + `InitAssetEditor` | AssetEditorToolkit |
| 외부에서 에셋 에디터 열기 | `GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->OpenEditorForAsset(...)` | Subsystems |
| 액터 일괄 변경 | `UEditorActorSubsystem::SetActorTransform` 등 | Subsystems |
| BP 헬퍼 (재컴파일·검색·추가) | `FBlueprintEditorUtils::*` static | Kismet2 |
| 에셋 임포트 자동화 | `UAutomatedAssetImportData` + `UFactory::FactoryCreateBinary` | Factories |
| 새 액터 스폰 메뉴 | `UActorFactory` 상속 + `Place Actors` 등록 | Factories |
| 5.x 선택 시스템 | `UEditorActorSubsystem::SelectNothing` + `FTypedElementSelectionSet` | Elements + Subsystems |
| 레이어 토글 | `ULayersSubsystem`(EditorFramework) + `FLayers` | Layers |
| 새 머티리얼 표현식 | `UMaterialExpression` 자손 + `UMaterialGraphNode_Knot` | MaterialEditor |
| 디테일 패널 커스터마이징 | (`PropertyEditor` 모듈 — 별도 sub-skill) | (외부) |
| ToolMenu 등록 | (`ToolMenus` 모듈 — 별도 sub-skill) | (외부) |

---

## 7. 관련 모듈 / 외부 sub-skill

- **상위 (의존됨)**: 거의 모든 Editor 모듈 (LevelEditor / GraphEditor / Persona / MaterialEditor / BlueprintEditor 등)
- **하위 (의존)**: Slate / SlateCore / UMG / CoreUObject / Engine / EditorFramework / EditorSubsystem / AssetTools / TypedElementFramework / Interchange
- **연계 sub-skill**:
  - [`Slate/EditorApplication`](../Slate/references/EditorApplication.md) — FSlateApplication 본체 + IInputProcessor (UnrealEd가 이 위에서 동작)
  - [`Slate/Docking`](../Slate/references/Docking.md) — SDockTab/FTabManager (Toolkit이 이걸 사용)
  - [`Slate/Menu`](../Slate/references/Menu.md) + [`Slate/Commands`](../Slate/references/Commands.md) — 메뉴/단축키
  - [`Slate/GraphEditor`](../Slate/references/GraphEditor.md) — 노드 그래프 에디터 (UnrealEd의 인하우스 노드 도구가 이걸 사용)
  - [`CoreUObject/Editor`](../CoreUObject/references/Editor.md) — PostEditChange / Modify / IsDataValid
  - [`CoreUObject/Cooking`](../CoreUObject/references/Cooking.md) — IsEditorOnly / NeedsLoadFor*
- **교차 인덱스**:
  - [`04_OverrideIndex.md`](../../references/04_OverrideIndex.md) — Toolkit/Subsystem virtual + Super 호출 규약
  - [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) — 4단 분리 방어
  - [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — Toolkit Tick / Subsystem 콜백 / 임포트 람다 등 스코프 의무

---

## 8. 갱신 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-04 | 최초 작성. UnrealEd.Build.cs 50+ Public 의존 + 24개 Public 디렉토리 + 17개 Classes 디렉토리 분석. **8개 sub-skill 분할안** 확정 (AssetEditorToolkit/Subsystems/Kismet2/Factories/Elements/Layers/MaterialEditor/Misc). 4단 분리 방어 + Toolkit 라이프사이클 + Subsystem 사용 표준 명시. |
