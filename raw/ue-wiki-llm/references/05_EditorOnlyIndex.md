---
name: editor-only-index
description: 🛠 sub-skill별 Editor 전용 항목 + 런타임/에디터 4단 분리 원칙 + WITH_EDITOR 가드 + 게임 모듈 금지 의존성. 인하우스 툴 / 에디터 콜백 작성 시 의무.
---

# Editor-Only Index — 에디터 전용 항목 통합 인덱스

> 본 위키 sub-skill 들에서 🛠 마커가 붙은 모든 **에디터/툴 빌드 전용** 항목을 한곳에서 보는 인덱스. 게임 쿠킹 빌드(`.exe`/`.pak`)에 들어가지 않거나 의미 없는 코드들의 분류 + 분리 원칙 cross-reference.
> **🚨 분리 원칙 (4단 방어)**: [`Slate/SKILL.md §8`](../skills/Slate/SKILL.md) 의무 규약 — 모듈 분리 / uplugin Type / Build.cs 분기 / `#if WITH_EDITOR` 가드.
> 갱신 이력: 2026-05-03.

---

## 0. 사용 규칙

1. 코드를 **게임 모듈** (`Type=Runtime`) 에 작성할 때 본 인덱스의 모든 항목은 **사용 금지** (또는 `#if WITH_EDITOR` 가드 안에서만).
2. 코드를 **에디터 모듈** (`Type=Editor`) 에 작성할 때만 자유롭게 사용.
3. 가드 매크로 차이:
   - `WITH_EDITOR` → 에디터 빌드 전체 코드 가드 (함수·로직)
   - `WITH_EDITORONLY_DATA` → 데이터 멤버만 (UPROPERTY 등)
   - `WITH_SLATE_DEBUGGING` → Slate 디버그 도구 (Reflector·Insights)
   - `UE_TRACE_ENABLED` → Unreal Insights 트레이스
   - `WITH_METADATA` → 옛 메타데이터 호환

---

## 1. 분리 4단 방어 (요약)

> 자세한 가이드는 [`Slate/SKILL.md §8`](../skills/Slate/SKILL.md). 본 인덱스는 분류·체크리스트 역할.

```
1. 모듈 분리       — Type=Runtime (게임) vs Type=Editor (에디터)
2. uplugin Type    — "Runtime" / "Editor" / "DeveloperTool" / "UncookedOnly"
3. Build.cs 분기   — if (Target.bBuildEditor) 안에 에디터 모듈 의존
4. 헤더 가드       — #if WITH_EDITOR / #if WITH_EDITORONLY_DATA
```

게임 모듈에 다음 모듈을 의존하면 **컴파일 에러** 또는 **쿠킹 실패** — 절대 추가 금지:

`UnrealEd` · `ToolMenus` · `WorkspaceMenuStructure` · `EditorStyle` · `PropertyEditor` · `GraphEditor` · `AppFramework` · `EditorWidgets` · `BlueprintGraph` · `KismetCompiler` · `AssetTools` · `ContentBrowser` · `LevelEditor`

---

## 2. CoreUObject 모듈

### 2.1 CoreUObject/Editor 🛠 (sub-skill 자체가 에디터 묶음)

> 본 sub-skill 의 거의 모든 항목이 에디터 전용. 자세한 표는 [`CoreUObject/references/Editor.md §4`](../skills/CoreUObject/references/Editor.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `PreEditChange(FProperty*)` 🛠 | Object.h L431 | `WITH_EDITOR` |
| `PreEditChange(FEditPropertyChain&)` 🛠 | Object.h L439 | `WITH_EDITOR` |
| `CanEditChange(FProperty*) const` 🛠 | Object.h L450 | `WITH_EDITOR` |
| `PostEditChangeProperty(FPropertyChangedEvent&)` 🛠 | Object.h L473 | `WITH_EDITOR` |
| `PostEditChangeChainProperty(FPropertyChangedChainEvent&)` 🛠 | Object.h L479 | `WITH_EDITOR` |
| `Modify(bool)` 🛠 (의미상) | Object.h L308 | (런타임 시그니처) |
| `IsCapturingAsRootObjectForTransaction()` 🛠 | Object.h L311 | `WITH_EDITOR` |
| `LoadedFromAnotherClass(FName)` 🛠 | Object.h L325 | `WITH_EDITOR` |
| `PreEditUndo()` / `PostEditUndo()` 🛠 | Object.h L485 / L488 | `WITH_EDITOR` |
| `PostTransacted(FTransactionObjectEvent&)` 🛠 | Object.h L498 | `WITH_EDITOR` |
| `IsSelectedInEditor()` 🛠 | Object.h L517 | `WITH_EDITOR` |
| `PostRename(UObject*, FName)` 🛠 (실효) | Object.h L523 | (런타임) |
| `PreDuplicate(FObjectDuplicationParameters&)` 🛠 | Object.h L532 | `WITH_EDITOR` |
| `PostDuplicate(EDuplicateMode::Type)` 🛠 (실효) | Object.h L539 | (런타임) |
| `GetAssetRegistryTags(FAssetRegistryTagsContext)` 🛠 | Object.h L898 | `WITH_EDITORONLY_DATA` 영향 |
| `IsDataValid(FDataValidationContext&) const` 🛠 | Object.h L1098 | `WITH_EDITOR` |
| `BeginCacheForCookedPlatformData(ITargetPlatform*)` 🛠 | Object.h L1211 | `WITH_EDITOR` |
| `IsCachedCookedPlatformDataLoaded(ITargetPlatform*)` 🛠 | Object.h L1218 | `WITH_EDITOR` |
| `IEditorPathObjectInterface` 🛠 | EditorPathObjectInterface.h | `WITH_EDITOR` |

### 2.2 CoreUObject/Cooking 🛠

> [`CoreUObject/references/Cooking.md §6`](../skills/CoreUObject/references/Cooking.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `Cooker/*` 헤더 (의존 추적·결정론·MP) 🛠 | (디렉토리) | `WITH_EDITOR` 위주 |
| `UDEPRECATED_MetaData` 🛠 | MetaData.h L33 | `Deprecated` (5.x) |
| `FMetaData` (`#if WITH_METADATA`) 🛠 | MetaData.h | `WITH_METADATA` |
| `FArchiveCookContext` 🛠 | ArchiveCookContext.h L13 | `WITH_EDITOR` |
| `UEnumCookedMetaData`/`UStructCookedMetaData`/`UClassCookedMetaData` 🛠 | CookedMetaData.h L124/L144/L164 | (런타임 잔존) |

### 2.3 CoreUObject/Reflection 🛠 (메타 편집)

> [`CoreUObject/references/Reflection.md §6`](../skills/CoreUObject/references/Reflection.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `SetMetaData(TCHAR*/FName, TCHAR*)` 🛠 | Class.h L307·L308 | `WITH_EDITOR` |
| `RemoveMetaData(...)` 🛠 | Class.h L377·L378 | `WITH_EDITOR` |
| `GetAuthoredName()` 🛠 | Class.h L234 | `WITH_EDITOR` |
| `GetBoolMetaDataHierarchical(FName)` / `GetStringMetaDataHierarchical(...)` 🛠 | Class.h L855·L858 | `WITH_EDITOR` |
| UPROPERTY 메타 키 (EditAnywhere/EditCondition/Category/UIMin/ClampMin/DisplayName/ToolTip) | (메타) | `WITH_EDITORONLY_DATA` |

### 2.4 CoreUObject/Property 🛠

> [`CoreUObject/references/Property.md §6`](../skills/CoreUObject/references/Property.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `FField::SetMetaData/RemoveMetaData` 🛠 | Field.h | `WITH_EDITORONLY_DATA` |
| `UPropertyWrapper` / `UMulticastDelegatePropertyWrapper` / `UMulticastInlineDelegatePropertyWrapper` 🛠 | PropertyWrapper.h L22/L53/L65 | `UCLASS(Transient, MinimalAPI)` |
| UPROPERTY 메타 (EditAnywhere/EditCondition 등) | (메타) | `WITH_EDITORONLY_DATA` |

### 2.5 CoreUObject/GC 🛠 (디버그)

> [`CoreUObject/references/GC.md §6`](../skills/CoreUObject/references/GC.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `EnableFrankenGCMode(bool)` 🛠 | GarbageCollection.h L93 | 디버그/실험 |
| `ShouldFrankenGCRun()` 🛠 | GarbageCollection.h L98 | 동상 |
| `FReferenceChainSearch` 🛠 (실용) | ReferenceChainSearch.h | 디버그 |
| `GarbageCollectionHistory.h` 🛠 | (전체) | `ENABLE_GC_HISTORY` |
| `DumpClusterToLog(...)` 🛠 | UObjectClusters.h L22 | 디버그 |

### 2.6 CoreUObject/Serialization 🛠

> [`CoreUObject/references/Serialization.md §6`](../skills/CoreUObject/references/Serialization.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `FEditorBulkData` 🛠 | EditorBulkData.h L131 | `WITH_EDITORONLY_DATA` |
| `FEditorBulkDataReader/Writer` 🛠 | EditorBulkDataReader.h, Writer.h | `WITH_EDITORONLY_DATA` |
| `UE::FDerivedData`, `FCacheKey`, `FValueId` 🛠 | DerivedData.h | DDC = `DerivedDataCache` 모듈 |
| `FBaseCookedPackageWriter` 🛠 | BasePackageWriter.h L21 | 쿠킹 |
| `IBulkDataRegistry` 🛠 | BulkDataRegistry.h | `WITH_EDITOR` |
| `FArchiveStackTrace` 🛠 | ArchiveStackTrace.h | `WITH_EDITOR` (결정론) |
| `PreSave/PostSaveRoot/CollectSaveOverrides` 🛠 (실용) | Object.h L267·L275·L288 | (런타임 시그니처, 사용처는 SavePackage·쿠킹) |

### 2.7 CoreUObject/Package 🛠

> [`CoreUObject/references/Package.md §6`](../skills/CoreUObject/references/Package.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `UPackage::SetDirtyFlag(bool)` 🛠 (실용) | Package.h L651 | 에디터 의미 |
| `UPackage::Save(...)` 🛠 (실용) | Package.h | 쿠킹·에디터 |
| `FSavePackageArgs/Settings/Context` 🛠 | SavePackage.h L62/L186/L225 | 쿠킹·에디터 |
| `ISavePackageValidator` 🛠 | SavePackage.h L134 | (5.2 deprecated) |
| `FArchiveSavePackageCollector` 🛠 | SavePackage.h L365 | 저장 시 |
| `FLinkerSave`/`FSaveContext` 🛠 | LinkerSave.h L47/L34 | 저장 시 |
| `PackageReload.h` 🛠 | (전체) | `WITH_EDITOR` |
| `LinkerDiff.h` 🛠 | (전체) | `WITH_EDITOR` |

### 2.8 CoreUObject/StructUtils 🛠 (UUserDefinedStruct 측)

> [`CoreUObject/references/StructUtils.md §6`](../skills/CoreUObject/references/StructUtils.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `UUserDefinedStruct::PrimaryStruct/ErrorMessage/EditorData` 🛠 | UserDefinedStruct.h | `WITH_EDITORONLY_DATA` |
| `UUserDefinedStruct::PostDuplicate/GetAssetRegistryTags/PostLoad/PreSaveRoot` 🛠 | UserDefinedStruct.h | `WITH_EDITOR` |
| `UUserDefinedStructEditorDataBase` 🛠 | UserDefinedStructEditorUtils.h L13 | `WITH_EDITORONLY_DATA` |
| `meta=(BaseStruct=...)` (FInstancedStruct UPROPERTY 메타) 🛠 | (메타) | `WITH_EDITORONLY_DATA` |

### 2.9 CoreUObject/ObjectHandles 🛠 (디버그·추적)

> [`CoreUObject/references/ObjectHandles.md §6`](../skills/CoreUObject/references/ObjectHandles.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `TObjectPtr<T>` 내부 lazy-resolve 🛠 | ObjectPtr.h | `WITH_EDITORONLY_DATA` |
| `ObjectHandleTracking.h` 🛠 | (전체) | `WITH_EDITOR` |
| `meta=(AllowedClasses=...)`, `meta=(MetaClass=...)`, `meta=(BaseStruct=...)` 🛠 | (메타) | `WITH_EDITORONLY_DATA` |

### 2.10 CoreUObject/Network — 거의 없음

게임 빌드에 동작. 일부 Iris (5.x) 추적은 `UE_TRACE_ENABLED`.

### 2.11 CoreUObject/DeprecatedUProperty 🛠

> [`CoreUObject/references/DeprecatedUProperty.md §6`](../skills/CoreUObject/references/DeprecatedUProperty.md).

UnrealTypePrivate.h 의 33개 옛 UProperty 클래스 — 호환성 위주, 신규 코드 사용 금지. `USE_UPROPERTY_LOAD_DEFERRING` (`WITH_EDITORONLY_DATA` 의존).

---

## 3. SlateCore 모듈

### 3.1 SlateCore/Trace 🛠 (sub-skill 자체가 디버그 묶음)

> [`SlateCore/references/Trace.md §9`](../skills/SlateCore/references/Trace.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `FSlateTrace` 🛠 | Trace/SlateTrace.h | `UE_SLATE_TRACE_ENABLED` |
| `FSlateDebugging` 🛠 | Debugging/SlateDebugging.h | `WITH_SLATE_DEBUGGING` |
| `FSlateCrashReporterHandler` 🛠 | Debugging/SlateCrashReporterHandler.h | (개발 빌드) |
| `Widget Reflector` (FWidgetReflector — Slate 모듈) 🛠 | Slate 측 | `WITH_SLATE_DEBUGGING` |
| `Slate.*` cvar 다수 🛠 | (콘솔) | 디버그·개발 |
| `LLM_DECLARE_TAG_API(SlateUI, ...)` 🛠 | Trace/SlateMemoryTags.h | `LLM_ENABLED` |
| `UE_WITH_SLATE_DEBUG_WIDGETLIST` 🛠 | Debugging/SlateDebugging.h | (디버그) |

### 3.2 SlateCore/Drawing 🛠 (디버그)

> [`SlateCore/references/Drawing.md §7`](../skills/SlateCore/references/Drawing.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `FSlateInvalidationRoot::GetPerformanceStat()` 🛠 | SlateInvalidationRoot.h | `WITH_SLATE_DEBUGGING` |
| `FSlateInvalidationRoot::GetLastPaintType()` 🛠 | SlateInvalidationRoot.h | `WITH_SLATE_DEBUGGING` |
| `Slate.InvalidationDebugging.*` cvar 🛠 | (cvar) | `WITH_SLATE_DEBUGGING` |

### 3.3 SlateCore/Styling 🛠

| 항목 | 위치 | 가드 |
|------|------|------|
| `USlateWidgetStyleAsset` 🛠 | SlateWidgetStyleAsset.h L17 | UCLASS — 에디터 편집 |
| `USlateWidgetStyleContainerBase` 🛠 | SlateWidgetStyleContainerBase.h | UCLASS |
| `FStarshipCoreStyle` 🛠 (실용) | StarshipCoreStyle.h | (런타임 존재, 주 사용 에디터) |
| `FAppStyle` 🛠 (실용) | AppStyle.h | 게임은 `FUMGCoreStyle` 권장 |
| `FSlateIconFinder` 🛠 | SlateIconFinder.h | 에디터 통합 |

### 3.4 SlateCore/SWidget 🛠 (일부)

| 항목 | 위치 | 가드 |
|------|------|------|
| `Debug_GetChildrenForReflector()` 🛠 | SWidget.h L871 | 디버그 |
| 접근성(Accessibility) 일부 경로 🛠 | `Public/Widgets/Accessibility/` | 접근성 가드 |

### 3.5 SlateCore/Property·Types 🛠

| 항목 | 위치 | 가드 |
|------|------|------|
| `FInvisibleToWidgetReflectorMetaData` 🛠 | Types/InvisibleToWidgetReflectorMetaData.h | `WITH_SLATE_DEBUGGING` |
| `FReflectionMetaData` 🛠 | Types/ReflectionMetadata.h | `WITH_SLATE_DEBUGGING` |
| `FTrackedMetaData` 🛠 | Types/TrackedMetaData.h | `WITH_SLATE_DEBUGGING` |

### 3.6 그 외 SlateCore — 거의 없음

`SWidget`/`Layout`/`Input`/`Application`/`Animation`/`Text` 본체는 게임 빌드에서도 동작.

---

## 4. Slate 모듈 — 인하우스 툴 묶음 (전체가 🛠)

### 4.1 분리 원칙 (가장 중요)

> [`Slate/SKILL.md §8`](../skills/Slate/SKILL.md) 의무 규약.

본 묶음 5개 sub-skill (`EditorApplication`/`Docking`/`Menu`/`Commands`/`GraphEditor`) 은 **전체가 사실상 에디터/툴 빌드 한정**. 코드 자체는 일부 게임 빌드에 컴파일되지만, 사용처가 거의 없거나 의미가 약함.

### 4.2 Slate/EditorApplication 🛠

> [`Slate/references/EditorApplication.md §12`](../skills/Slate/references/EditorApplication.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `IWidgetReflector` 🛠 | Application/IWidgetReflector.h | `WITH_SLATE_DEBUGGING` |
| `AddModalWindow(...)` 🛠 (실용) | Application/SlateApplication.h L428 | (런타임 시그니처) |
| Widget Reflector 콘솔 명령 🛠 | (cvar) | `WITH_SLATE_DEBUGGING` |
| `FSlateApplication::SetFixedDeltaTime` 🛠 (실용) | Application/SlateApplication.h L1142 | (런타임 존재) |
| 메인 메뉴 / 툴바 통합 🛠 | (Menu/SKILL.md) | `WITH_EDITOR` |

### 4.3 Slate/Docking 🛠

> [`Slate/references/Docking.md §8`](../skills/Slate/references/Docking.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| 모든 탭 스포너 등록 🛠 | TabManager.h | `WITH_EDITOR` 권장 |
| `FLayoutSaveRestore` 🛠 | LayoutService.h | 에디터 ini |
| `WorkspaceMenu::GetMenuStructure()` 🛠 | (별도 모듈) | 에디터 모듈 |
| `FLayoutExtender` 🛠 | LayoutExtender.h | 에디터 패턴 |
| `STabDrawer` 🛠 | STabDrawer.h | 에디터 5.x 사이드바 |

### 4.4 Slate/Menu 🛠

> [`Slate/references/Menu.md §7`](../skills/Slate/references/Menu.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| 모든 `F*Builder` 🛠 | MultiBoxBuilder.h | (런타임 컴파일 됨) |
| `UToolMenuBase` 🛠 | ToolMenuBase.h | UCLASS |
| `IExtensibilityManager` 🛠 | (호스트 모듈별) | 에디터 모듈 |
| `FAppStyle::Get().GetBrush(...)` 메뉴 아이콘 🛠 (실용) | (런타임 존재) | 게임은 `FUMGCoreStyle` |
| `FMultiBoxSettings` 🛠 | MultiBoxDefs.h L90 | 에디터 환경 설정 |

### 4.5 Slate/Commands 🛠

> [`Slate/references/Commands.md §7`](../skills/Slate/references/Commands.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `TCommands<T>` 클래스 자체 🛠 (실용) | Commands.h | (런타임 컴파일 OK) |
| `FInputBindingManager` 사용자 ini 저장 🛠 | InputBindingManager.h | 에디터 ini |
| `FGenericCommands` 자동 등록 🛠 | GenericCommands.h | 에디터 부트스트랩 |
| `FUICommandDragDropOp` 🛠 | UICommandDragDropOp.h | 에디터 커스터마이즈 UI |
| `EditPreferences > Keyboard Shortcuts` 🛠 | (UI) | 에디터 |
| `Contexts/UIIdentifierContext`/`UIContentContext` 🛠 | Contexts/ | 에디터 통합 |

### 4.6 Slate/GraphEditor 🛠 (sub-skill 자체가 에디터 묶음)

> [`Slate/references/GraphEditor.md §8`](../skills/Slate/references/GraphEditor.md).

**EdGraph 런타임** (Engine 모듈) 은 게임 빌드 OK이지만 시각화/편집 측은 모두 에디터.

| 항목 | 위치 | 가드 |
|------|------|------|
| `UEdGraph::SubGraphs/GraphGuid/InterfaceGuid` 🛠 | EdGraph.h | `WITH_EDITORONLY_DATA` |
| `UEdGraph::PostInitProperties/PostLoad/Serialize/BuildSubobjectMapping` 🛠 | EdGraph.h | `WITH_EDITORONLY_DATA` |
| `UEdGraphNode::bCanResizeNode/bCommentBubble*/bCanRenameNode/NodeUpgradeMessage/bUnrelated` 🛠 | EdGraphNode.h | `WITH_EDITORONLY_DATA` |
| `UEdGraphNode::GetNodeContextMenuActions/ValidateNodeDuringCompilation/GetMenuEntries/MakeNameValidator/OnRenameNode/SupportsCommentBubble/OnCommentBubbleToggled/CreateVisualWidget/CreateNodeImage` 🛠 | EdGraphNode.h L896~L967 | `WITH_EDITOR` |
| `UEdGraphPin::bHidden/bAdvancedView/bDeprecated/bDisplayAsMutableRef` 등 | EdGraphPin.h | `WITH_EDITORONLY_DATA` |
| `UEdGraphSchema` 의 모든 50+ virtual 🛠 | EdGraphSchema.h | (UClass 자체는 런타임) |
| **GraphEditor 모듈 전체** 🛠 | `Engine/Source/Editor/GraphEditor/` | 모듈 `Type=Editor` |
| `BlueprintGraph`/`KismetCompiler` 🛠 | `Engine/Source/Editor/` | 모듈 `Type=Editor` |

### 4.7 SlateRHIRenderer (Build.cs 분기)

UMG/Slate 모두 — 비-서버 빌드만 의존. `Target.Type != TargetType.Server` 일 때만 `SlateRHIRenderer` 추가.

---

## 5. UMG 모듈

### 5.1 UMG/UWidget 🛠 (디자이너 통합)

> [`UMG/references/UWidget.md §8`](../skills/UMG/references/UWidget.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `IsDesignTime()` 🛠 | Widget.h | `WITH_EDITOR` |
| `RebuildDesignWidget(TSharedRef<SWidget>)` 🛠 | Widget.h | `WITH_EDITOR` |
| `CreateDesignerOutline(TSharedRef<SWidget>)` 🛠 | Widget.h | `WITH_EDITOR` |
| `GetDisplayNameBase()` 🛠 | Widget.h | `WITH_EDITOR` |
| `SetDisplayLabel(FString)` 🛠 | Widget.h L973 | `WITH_EDITOR` |
| `SetCategoryName(FString)` 🛠 | Widget.h L979 | `WITH_EDITOR` |
| `EWidgetDesignFlags` 🛠 | Widget.h | `WITH_EDITOR` |
| `SetLockedInDesigner(bool)` 🛠 | Widget.h L486 | `WITH_EDITOR` |

### 5.2 UMG/UUserWidget 🛠

> [`UMG/references/UUserWidget.md §8`](../skills/UMG/references/UUserWidget.md).

| 항목 | 위치 | 가드 |
|------|------|------|
| `NativePreConstruct` 디자이너 동작 🛠 (실용) | UserWidget.h L1575 | (런타임 존재) |
| `EWidgetDesignFlags::Designing/Previewing` 🛠 | (UWidget) | `WITH_EDITOR` |
| `bCanCallPreConstruct` (WidgetBlueprintGeneratedClass) 🛠 | WidgetBlueprintGeneratedClass.h | `WITH_EDITORONLY_DATA` |
| `BindWidget` 메타 검증 🛠 | (UPROPERTY 메타) | UMG 컴파일러 |
| `bCanCallInitializedWithoutPlayerContext` 🛠 | WidgetBlueprintGeneratedClass.h | (Widget Preview용) |

### 5.3 UMG 의 `Editor/` 폴더

| 항목 | 위치 | 가드 |
|------|------|------|
| `WidgetCompilerLog.h` 🛠 | UMG/Public/Editor/WidgetCompilerLog.h | (UMG 컴파일러 — 에디터) |

---

## 6. 분리 체크리스트 (작업 시작 전)

새 인하우스 툴 / 에디터 기능 작성 시 다음 체크:

- [ ] 별도 에디터 모듈 (`MyToolEditor`) 만들었는가?
- [ ] uplugin Modules 배열에 `Type=Editor` + `LoadingPhase=PostEngineInit` 으로 등록했는가?
- [ ] 에디터 모듈 Build.cs 에만 `UnrealEd`/`ToolMenus`/`PropertyEditor` 등 의존 추가했는가?
- [ ] 게임 모듈 Build.cs 에는 `UnrealEd`/`GraphEditor` 등 절대 추가하지 않았는가?
- [ ] 같은 클래스에 런타임 + 에디터 멤버 섞을 때 `WITH_EDITORONLY_DATA` / `WITH_EDITOR` 가드했는가?
- [ ] `FGlobalTabmanager`/`FUICommandList`/`FMenuBuilder` 호출이 모두 `#if WITH_EDITOR` 가드 안인가?
- [ ] `IsDataValid`/`PostEditChangeProperty`/`GetAssetRegistryTags` 가 `#if WITH_EDITOR` 가드인가?
- [ ] 쿠킹 빌드로 검증 — 산출물에 에디터 dll/uasset 안 섞였는가? (`-run=Cook -targetplatform=WindowsClient`)

---

## 7. 갱신 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-03 | 최초 작성. 11개 sub-skill (CoreUObject 9 + SlateCore 5 + Slate 5 + UMG 2) 의 🛠 항목 통합. 분리 4단 방어 cross-reference. |
