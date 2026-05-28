---
type: source
title: "UE refs — 05 EditorOnlyIndex (4단 분리 hub)"
slug: ue-ref-05-editoronlyindex
source_path: raw/ue-wiki-llm/references/05_EditorOnlyIndex.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Slate-Editor-Runtime-Separation]]"
tags: [ue, reference, editor, separation, with-editor, build-cs, governance]
---

# UE refs — 05 EditorOnlyIndex 🚨

> Source: [[raw/ue-wiki-llm/references/05_EditorOnlyIndex.md]] · CLAUDE.md §0.1.4 cross-cutting 인덱스

## 1. Summary

본 vault sub-skill 의 **🛠 마커가 붙은 모든 Editor / 툴 빌드 전용 항목** 통합 인덱스. 게임 쿠킹 빌드 (`.exe` / `.pak`) 에 들어가지 않거나 의미 없는 코드의 분류 + 분리 원칙 cross-reference. 🚨 **4단 방어 의무** — [[sources/ue-slate-skill]] §8 + KMCProject `MCEditorModule` 분리 사례. 권위 concept = [[concepts/Editor-Only-4-Tier-Separation]] / [[concepts/Slate-Editor-Runtime-Separation]].

## 2. 사용 규칙 🟢

1. **게임 모듈** (`Type=Runtime`) 코드 작성 시 본 인덱스의 항목은 **사용 금지** (또는 `#if WITH_EDITOR` 가드 안)
2. **에디터 모듈** (`Type=Editor`) 만 자유 사용
3. 가드 매크로 차이:
   - `WITH_EDITOR` — 에디터 빌드 전체 코드 가드 (함수 / 로직)
   - `WITH_EDITORONLY_DATA` — **데이터 멤버만** (UPROPERTY 등)
   - `WITH_SLATE_DEBUGGING` — Slate 디버그 (Reflector / Insights)
   - `UE_TRACE_ENABLED` — Unreal Insights 트레이스
   - `WITH_METADATA` — 옛 메타데이터 호환

## 3. 🚨 4단 방어 (분리 원칙) 🟢

```
1. 모듈 분리       — Type=Runtime (게임) vs Type=Editor (에디터)
2. uplugin Type    — "Runtime" / "Editor" / "DeveloperTool" / "UncookedOnly"
3. Build.cs 분기   — if (Target.bBuildEditor) 안에 에디터 모듈 의존
4. 헤더 가드       — #if WITH_EDITOR / #if WITH_EDITORONLY_DATA
```

🚨 **게임 모듈 의존 금지 모듈** (의존 시 컴파일 에러 / 쿠킹 실패):

`UnrealEd` · `ToolMenus` · `WorkspaceMenuStructure` · `EditorStyle` · `PropertyEditor` · `GraphEditor` · `AppFramework` · `EditorWidgets` · `BlueprintGraph` · `KismetCompiler` · `AssetTools` · `ContentBrowser` · `LevelEditor`

## 4. 카테고리별 Editor 전용 항목 매트릭스 🟢

### 4.1. CoreUObject (Tier 1)

| sub-skill | 핵심 🛠 항목 | 가드 |
| -- | -- | -- |
| [[sources/ue-coreuobject-editor]] | `PreEditChange / PostEditChangeProperty / PostEditChangeChainProperty` + `Modify` + `PreEditUndo / PostEditUndo` + `PostTransacted` + `IsDataValid` + `BeginCacheForCookedPlatformData` | `WITH_EDITOR` |
| [[sources/ue-coreuobject-cooking]] | `Cooker/*` + `UEnumCookedMetaData` + `FArchiveCookContext` | `WITH_EDITOR` |
| [[sources/ue-coreuobject-reflection]] | `SetMetaData / RemoveMetaData / GetAuthoredName / GetBoolMetaDataHierarchical` + UPROPERTY 메타 (EditAnywhere / Category / UIMin 등) | `WITH_EDITOR` / `WITH_EDITORONLY_DATA` |
| [[sources/ue-coreuobject-property]] | `FField::SetMetaData / RemoveMetaData` + `UPropertyWrapper` | `WITH_EDITORONLY_DATA` |
| [[sources/ue-coreuobject-gc]] | `EnableFrankenGCMode` + `FReferenceChainSearch` + `GarbageCollectionHistory` | 디버그 / `ENABLE_GC_HISTORY` |
| [[sources/ue-coreuobject-serialization]] | `FEditorBulkData` + `UE::FDerivedData` + `FBaseCookedPackageWriter` + `IBulkDataRegistry` + `FArchiveStackTrace` | `WITH_EDITORONLY_DATA` / `WITH_EDITOR` |
| [[sources/ue-coreuobject-package]] | `UPackage::SetDirtyFlag` + `Save(...)` + `FSavePackageArgs/Settings/Context` + `PackageReload.h` + `LinkerDiff.h` | `WITH_EDITOR` |

### 4.2. SlateCore (Tier 3)

| sub-skill | 핵심 🛠 항목 | 가드 |
| -- | -- | -- |
| [[sources/ue-slatecore-trace]] 🛠 | `FSlateTrace` + `FSlateDebugging` + Widget Reflector + `Slate.*` cvar | `UE_SLATE_TRACE_ENABLED` / `WITH_SLATE_DEBUGGING` |
| [[sources/ue-slatecore-drawing]] §7 | `FSlateInvalidationRoot::GetPerformanceStat` + `Slate.InvalidationDebugging.*` cvar | `WITH_SLATE_DEBUGGING` |
| [[sources/ue-slatecore-styling]] | `USlateWidgetStyleAsset` + `FStarshipCoreStyle` + `FAppStyle` + `FSlateIconFinder` | 에디터 통합 |

### 4.3. Slate (Tier 3) — 인하우스 툴 묶음 전체

> [[sources/ue-slate-skill]] §8 의무 규약 — 본 묶음 5 sub-skill 사실상 에디터/툴 한정.

- [[sources/ue-slate-editorapplication]] 🛠 — `IWidgetReflector` + `AddModalWindow` + `FSlateApplication::SetFixedDeltaTime`
- [[sources/ue-slate-docking]] 🛠 — 모든 탭 스포너 등록 + `FLayoutSaveRestore` + `FLayoutExtender` + `STabDrawer`
- [[sources/ue-slate-menu]] 🛠 — 모든 `F*Builder` + `UToolMenuBase` + `IExtensibilityManager` + `FMultiBoxSettings`
- [[sources/ue-slate-commands]] 🛠 — `TCommands<T>` + `FInputBindingManager` + `FGenericCommands` + `FUICommandDragDropOp`
- [[sources/ue-slate-grapheditor]] 🛠 — `UEdGraph::GraphGuid / Serialize / BuildSubobjectMapping` + `UEdGraphNode::bCanResizeNode / GetNodeContextMenuActions` + GraphEditor 모듈 전체 + BlueprintGraph / KismetCompiler

### 4.4. UMG (Tier 3)

| sub-skill | 핵심 🛠 항목 | 가드 |
| -- | -- | -- |
| [[sources/ue-umg-uwidget]] | `IsDesignTime` + `RebuildDesignWidget` + `CreateDesignerOutline` + `GetDisplayNameBase` + `SetDisplayLabel / SetCategoryName` + `EWidgetDesignFlags` + `SetLockedInDesigner` | `WITH_EDITOR` |
| [[sources/ue-umg-uuserwidget]] | `NativePreConstruct` 디자이너 동작 + `EWidgetDesignFlags::Designing/Previewing` + `bCanCallPreConstruct` + `BindWidget` 메타 | `WITH_EDITOR` / UMG 컴파일러 |

### 4.5. Editor 🛠 (모든 sub-skill)

본 카테고리 전체가 Editor 빌드 전용. → [[sources/ue-editor-skill]] (메인) · [[sources/ue-editor-unrealed]] · 9 UnrealEd sub-skill · 5 AssetEditorAPI · 9 모듈 ([[sources/ue-editor-editorframework]] / [[sources/ue-editor-editorsubsystem]] / [[sources/ue-editor-assettools]] / [[sources/ue-editor-propertyeditor]] / [[sources/ue-editor-toolmenus]] / [[sources/ue-editor-mainframe]] / [[sources/ue-editor-leveleditor]] / [[sources/ue-editor-assetregistry]] / [[sources/ue-editor-editorwidgets]]).

## 5. 분리 체크리스트 🟢

새 인하우스 툴 / 에디터 기능 작성 시:

- [ ] 별도 에디터 모듈 (`MyToolEditor`) 만들었는가?
- [ ] uplugin Modules 배열에 `Type=Editor` + `LoadingPhase=PostEngineInit` 등록?
- [ ] 에디터 모듈 Build.cs 에만 `UnrealEd / ToolMenus / PropertyEditor` 의존 추가?
- [ ] **게임 모듈 Build.cs 에는 `UnrealEd / GraphEditor` 등 절대 추가 X**?
- [ ] 같은 클래스에 런타임+에디터 멤버 섞을 때 `WITH_EDITORONLY_DATA / WITH_EDITOR` 가드?
- [ ] `FGlobalTabmanager / FUICommandList / FMenuBuilder` 호출이 `#if WITH_EDITOR` 가드 안?
- [ ] `IsDataValid / PostEditChangeProperty / GetAssetRegistryTags` 가 `#if WITH_EDITOR` 가드?
- [ ] **Cooked Build 검증** (`-run=Cook -targetplatform=WindowsClient`) — 산출물에 에디터 dll / uasset 안 섞임?

## 6. KMCProject 사례 (실전 적용)

KMCProject 의 모듈 구조 — 4단 방어 직접 적용:

| 모듈 | Type | 의존 | 의미 |
| -- | -- | -- | -- |
| `KMCProject` | Runtime | (기본) | 게임 베이스 |
| `MCPlayModule` | Runtime | **🚨 `UnrealEd` 의존** | 임시 — 쿠킹 빌드 불가 (CLAUDE.md 명시) |
| `MCPlayUMGModule` | Runtime | MCPlayModule | UMG |
| `MCEditorModule` | **Editor** | UnrealEd / EditorSubsystem / PropertyEditor / AssetTools | 에디터 전용 |

🚨 `MCPlayModule.Build.cs` 의 `UnrealEd` 의존은 **본 정책 위반** — 향후 `if (Target.bBuildEditor)` 가드 안으로 이동 필요. → [[sources/ue-docs-claude]] §architecture.

## 7. 함정 (5대) 🟡

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | 게임 모듈에 `UnrealEd` 의존 추가 | 즉시 Cooked 빌드 실패 — Editor 모듈 분리 |
| 2 | `WITH_EDITOR` 가드 없이 `PostEditChangeProperty` override | Cooked 빌드 컴파일 에러 |
| 3 | `WITH_EDITORONLY_DATA` UPROPERTY 를 게임 코드에서 접근 | `#if WITH_EDITORONLY_DATA` 가드 필요 |
| 4 | uplugin `"Type": "Runtime"` + Editor 모듈 코드 | "Type": "Editor" / "UncookedOnly" 권장 |
| 5 | 4단 중 일부만 적용 (가드만 + 모듈 분리 X) | 4단 모두 의무 — 모듈 분리 우선 |

## 8. Cross-link

- 권위 concept: [[concepts/Editor-Only-4-Tier-Separation]] · [[concepts/Slate-Editor-Runtime-Separation]]
- 자매 hub: [[sources/ue-ref-03-wikiharness]] · [[sources/ue-ref-04-overrideindex]] · [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-10-componentpolicies]] · [[sources/ue-ref-11-assetloadingpolicy]]
- 분리 의무 규약: [[sources/ue-slate-skill]] §8 (Slate 인하우스 툴 분리 4단 방어 표준)
- Editor 카테고리: [[sources/ue-editor-skill]] (10 sub-skill 전체 적용)
- MC-시리즈: [[sources/ue-docs-claude]] (KMCProject `MCEditorModule` 분리 사례)
- Build / Cooking: [[sources/ue-build-skill]] · [[sources/ue-coreuobject-cooking]]
