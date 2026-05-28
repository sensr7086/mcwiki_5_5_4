---
type: source
title: "UE Editor — UnrealEd / AssetEditorToolkit sub-skill 🛠 (Toolkit 작성 표준)"
slug: ue-editor-unrealed-asseteditortoolkit
source_path: raw/ue-wiki-llm/skills/Editor/references/UnrealEd/AssetEditorToolkit.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-15
related_entities:
  - "[[entities/IToolkit]]"
  - "[[entities/FTabManager]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, editor, unrealed, asseteditortoolkit, toolkit, workflow-centric, tabmanager, extensibility, toolmenus, workfloworientedapp-folder-vs-module, ubt-ruleserror]
---

# UE Editor — UnrealEd / AssetEditorToolkit sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/UnrealEd/AssetEditorToolkit.md]] · 22 KB raw
> 보강 2026-05-15 (Cycle 5d) — §2.15 신규 `WorkflowOrientedApp` 폴더 vs 모듈 함정 (UBT RulesError, KMCProject MCComboEditor 실측)

## 1. Summary

UE 에디터의 **모든 에셋 에디터** (Material / BP / Animation / BT 등) 의 베이스. `FAssetEditorToolkit` 자손 정의 + `IAssetTypeActions` 연결로 더블클릭 자동 오픈. 5 구성: **`FAssetEditorToolkit`** (단일 에셋 베이스) · **`FSimpleAssetEditor`** (디테일 패널만, 즉시 사용) · **`FWorkflowCentricApplication`** (모드 전환형 — Persona / BehaviorTree / BlueprintEditor) · **`FExtensibilityManager`** (외부 모듈 메뉴/툴바 확장) · **`IToolkitHost` + `SStandaloneAssetEditorToolkitHost`** (호스팅). 위치: `UnrealEd/Public/Toolkits/` + `Public/WorkflowOrientedApp/`. **에디터 전용** — 4단 분리 의무. 5.x = `UToolMenus` 권장 (FExtender 대체).

## 2. Key claims

### 2.1. 헤더 / 클래스

| 클래스 | 헤더 | 라인 |
| -- | -- | -- |
| `FExtensibilityManager` / `IHasMenuExtensibility` / `IHasToolBarExtensibility` / `FAssetEditorToolkit` | `Public/Toolkits/AssetEditorToolkit.h` | L57 / L82 / L89 / L114 |
| `FBaseToolkit` / `FModeToolkit` | `Public/Toolkits/BaseToolkit.h` | L27 / L98 |
| `FSimpleAssetEditor` | `Public/Toolkits/SimpleAssetEditor.h` | L12 |
| `FWorkflowCentricApplication` / `FApplicationMode` / `FWorkflowTabFactory` | `Public/WorkflowOrientedApp/...` | — |
| `FTabManager` (ref) | [[sources/ue-slate-docking]] |

### 2.2. 인스턴스 시작

- `InitAssetEditor(EToolkitMode, IToolkitHost, FName AppId, FTabManager::FLayout, bMenu, bToolbar, ObjectsToEdit)` (L141) — `EToolkitMode::Standalone` (독립) vs `WorldCentric` (레벨 에디터 안). AppIdentifier = GUID-like 고유 키.
- `AddEditingObject(UObject*)` (L349) / `RemoveEditingObject(UObject*)` (L352).

### 2.3. PURE_VIRTUAL — 구현 의무

`GetToolkitFName / GetBaseToolkitName / GetWorldCentricTabPrefix / GetWorldCentricTabColorScale` 4종. `IHasMenuExtensibility` / `IHasToolBarExtensibility` 구현 시 +2 (`GetMenuExtensibilityManager` L85 / `GetToolBarExtensibilityManager` L92). BaseToolkit 베이스에 `GetEditorModeManager()` PURE (BaseToolkit.h L52) 추가.

### 2.4. 라이프사이클 + Super 호출 🟢

| 시그니처 | 위치 | Super |
| -- | -- | -- |
| `RegisterTabSpawners(FTabManager&)` | L151 | **FIRST** (기본 탭 누락 방지) |
| `UnregisterTabSpawners` | L152 | **FIRST** |
| `InitToolMenuContext(FToolMenuContext&)` | L240 | **FIRST** |
| `PostInitAssetEditor` (InitAssetEditor 직후) / `PostRegenerateMenusAndToolbars` / `OnToolkitHostingStarted/Finished` | L327 / L248 / L251-254 | 선택 |
| `OnRequestClose()` (false = 닫기 차단) | (헤더) | 선택 |

Super 호출 통합 → [[sources/ue-ref-04-overrideindex]] §6.

### 2.5. 윈도우 관리 API

| API | 라인 | 의미 |
| -- | -- | -- |
| `FocusWindow(UObject*)` | L165 | 특정 객체로 포커스 |
| `CloseWindow()` / `CloseWindow(EAssetEditorCloseReason)` | L167 / L168 | 닫기 시도 (false = 사용자 거부) |
| `OnRequestClose()` virtual | (헤더) | 기본 true. 저장 미완료 시 false → 닫기 차단 |
| `InvokeTab(FTabId)` | L170 | 탭 활성화 |

### 2.6. 메뉴 / 툴바 / 뷰포트

`CreateMenuBar` (L242) / `GetToolMenuToolbarName` (L239) / `GenerateCommonActionsToolbar` (L340) / `AddGraphEditorPinActionsToContextMenu` (L313) / `AddViewportOverlayWidget(SWidget, int32 ZOrder)` (L259) / `RemoveViewportOverlayWidget` (L262) / `OnViewportDragEnter/Leave/Drop` (L316-318).

### 2.7. 콘텐츠 / 객체 관리 API

`GetObjectsCurrentlyBeingEdited` (L154) / `GetSaveableObjects` (L346) / `AddEditingObject` / `RemoveEditingObject` (L349-352) / `CanSaveAsset` (L355) / `SaveAsset_Execute` / `IsAssetEditor` (true) / `IsPrimaryEditor` (L169) / `IsSimpleAssetEditor` / BaseToolkit `ProcessCommandBindings(FKeyEvent&)` (BaseToolkit.h L44) / `IsBlueprintEditor()` (L49).

### 2.8. ToolMenu (5.x 권장) — FExtender 대체

`FExtender` (4.x) → 5.x 는 `UToolMenus`. `InitToolMenuContext(FToolMenuContext&)` (L240) override + `FToolMenuOwnerScoped` 패턴 → [[sources/ue-editor-toolmenus]].

```cpp
// 5.x 권장 — Editor StartupModule 안
UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("AssetEditor.MyAssetEditor.MainMenu");
FToolMenuSection& Sec = Menu->FindOrAddSection("MySection");
Sec.AddMenuEntry("MyEntry", LOCTEXT("MyEntry", "Custom"), FText(), FSlateIcon(),
    FToolUIAction(FToolMenuExecuteAction::CreateLambda([](const FToolMenuContext&){ /*...*/ })));
```

### 2.9. 표준 패턴 — Tab 등록 + Layout

```cpp
void FMyAssetEditor::RegisterTabSpawners(const TSharedRef<FTabManager>& InTabManager)
{
    FAssetEditorToolkit::RegisterTabSpawners(InTabManager);     // Super FIRST 의무
    WorkspaceMenuCategory = InTabManager->AddLocalWorkspaceMenuCategory(
        LOCTEXT("WorkspaceMenu", "My Asset Editor"));
    InTabManager->RegisterTabSpawner(DetailsTabId, FOnSpawnTab::CreateSP(this, &FMyAssetEditor::SpawnDetailsTab))
        .SetDisplayName(LOCTEXT("DetailsTab", "Details"))
        .SetGroup(WorkspaceMenuCategory.ToSharedRef());
}

TSharedRef<FTabManager::FLayout> Layout =
    FTabManager::NewLayout("Standalone_MyAssetEditor_Layout_v1.0")   // 모듈/에셋 prefix + 버전 의무
    ->AddArea(FTabManager::NewPrimaryArea()->SetOrientation(Orient_Horizontal)
        ->Split(FTabManager::NewStack()->SetSizeCoefficient(0.7f)->AddTab(ViewportTabId, ETabState::OpenedTab))
        ->Split(FTabManager::NewStack()->SetSizeCoefficient(0.3f)->AddTab(DetailsTabId, ETabState::OpenedTab)));
```

생성자에서 `MenuExtensibilityManager = MakeShared<FExtensibilityManager>()` 의무.

### 2.10. IAssetTypeActions 연결

```cpp
void FAssetTypeActions_MyAsset::OpenAssetEditor(const TArray<UObject*>& InObjects, TSharedPtr<IToolkitHost> EditWithin)
{
    EToolkitMode::Type Mode = EditWithin.IsValid() ? EToolkitMode::WorldCentric : EToolkitMode::Standalone;
    for (UObject* Obj : InObjects)
        if (UMyAsset* A = Cast<UMyAsset>(Obj))
            MakeShared<FMyAssetEditor>()->InitMyAssetEditor(Mode, EditWithin, A);
}
```

자세히 → [[sources/ue-editor-assettools]].

### 2.11. SimpleAssetEditor — 단순 케이스

디테일 패널만 필요하면 직접 자손 작성 대신 `FSimpleAssetEditor::CreateEditor` (SimpleAssetEditor.h L30):

```cpp
virtual void OpenAssetEditor(const TArray<UObject*>& InObjects, TSharedPtr<IToolkitHost> EditWithin) override
{
    FSimpleAssetEditor::CreateEditor(EToolkitMode::Standalone, EditWithin, InObjects);
}
```

`SetPropertyVisibilityDelegate(FIsPropertyVisible)` 로 디테일 패널 필터링 가능.

### 2.12. 인하우스 에디터 모듈 구조

```
MyGameEditor/                        ← Build.cs Type=Editor 분리 모듈
├── MyGameEditor.Build.cs            ← UnrealEd / AssetTools / PropertyEditor 의존
├── Public/Toolkits/MyAssetEditor.h          ← FAssetEditorToolkit 자손
├── Public/Toolkits/MyAssetEditorTabs.h      ← FName 상수
├── Public/AssetActions/AssetTypeActions_MyAsset.h
└── Private/
    ├── MyGameEditorModule.cpp       ← StartupModule (Register*) / ShutdownModule (Unregister*)
    ├── Toolkits/MyAssetEditor.cpp
    └── AssetActions/AssetTypeActions_MyAsset.cpp
```

KMCProject 의 `MCEditorModule` 이 동일 패턴 — `MCStoryAssetEditorApplication.h` 가 본 베이스의 자손 ([[sources/ue-docs-claude]] §architecture).

### 2.13. 함정 10대 🟡

1. 게임 모듈 직접 의존 → Editor 모듈 분리 + `Type=Editor`
2. `RegisterTabSpawners` 안 Super 누락 → 기본 탭 미등록
3. PURE_VIRTUAL 4종 미구현 → 컴파일 에러
4. `MenuExtensibilityManager` 초기화 누락 → 외부 모듈 확장 불가
5. 레이아웃 키 충돌 → 모듈/에셋 prefix
6. 레이아웃 변경 시 같은 키 유지 → `_v2.0` 버전 증가 (사용자 설정 리셋 의무)
7. `OpenEditorForAsset` 직접 호출 → `UAssetEditorSubsystem::OpenEditorForAsset` 사용 ([[sources/ue-editor-unrealed-subsystems]])
8. 닫힐 때 정리 누락 → `OnRequestClose` + 저장 다이얼로그
9. `Tick` override 시 스코프 누락 → `TRACE_CPUPROFILER_EVENT_SCOPE` ([[sources/ue-ref-07-profilingscopeRule]])
10. `FSimpleAssetEditor::CreateEditor` 후 변경 시도 → 커스텀은 직접 자손

### 2.14. Build.cs (Editor 모듈만) 🛠

`UnrealEd` / `EditorFramework` / `PropertyEditor` / `AssetTools` / `Slate` / `SlateCore`. uplugin module `"Type": "Editor"` 의무. → [[sources/ue-ref-05-editoronlyindex]] §3 4단 방어.

### 2.15. ⭐⭐⭐ `WorkflowOrientedApp` — 폴더 vs 모듈 함정 (UBT RulesError, 2026-05-15 추가, KMCProject MCComboEditor 실측) 🟢

#### 2.15.1 함정 시그니처 — `RulesError: Could not find definition for module 'WorkflowOrientedApp'`

`FWorkflowCentricApplication` / `FApplicationMode` / `FWorkflowTabFactory` / `FWorkflowAllowedTabSet` 헤더가 `WorkflowOrientedApp/` 디렉토리 아래 있고, include 경로가 `#include "WorkflowOrientedApp/WorkflowCentricApplication.h"` 패턴이라 **"이건 별도 모듈인가?"** 가설 합리적 — 그래서 `Build.cs` 에 의존 추가 시도:

```csharp
// ❌ MyEditorModule.Build.cs — UBT RulesError
PublicDependencyModuleNames.AddRange(new string[]
{
    "Core", "CoreUObject", "Engine",
    "UnrealEd",
    "WorkflowOrientedApp",   // ❌ 그런 모듈 X — UBT 가 *.Build.cs 검색 실패
    ...
});
```

UBT 출력:

```
ERROR: Could not find definition for module 'WorkflowOrientedApp',
       (referenced via Target -> MyEditorModule.Build.cs)
Result: Failed (RulesError)
```

#### 2.15.2 원인 — 실제 위치는 `UnrealEd` 모듈 안의 **폴더**

```
Engine/Source/Editor/UnrealEd/
├── UnrealEd.Build.cs                       ← 실제 모듈 정의
├── Public/
│   ├── Toolkits/                            ← FAssetEditorToolkit / FBaseToolkit
│   │   └── AssetEditorToolkit.h
│   └── WorkflowOrientedApp/                 ← ⚠ 별도 모듈 X — UnrealEd 의 폴더
│       ├── WorkflowCentricApplication.h    ← FWorkflowCentricApplication
│       ├── ApplicationMode.h               ← FApplicationMode
│       ├── WorkflowTabManager.h            ← FWorkflowTabFactory / FWorkflowAllowedTabSet
│       └── WorkflowUObjectDocuments.h
```

`UnrealEd.Build.cs` 가 `Public/` 하위 *모든* 헤더를 export → `WorkflowOrientedApp/` 도 같은 모듈에 속함. include path 가 `WorkflowOrientedApp/X.h` 인 것은 **물리적 폴더 path** 일 뿐 모듈 경계가 아님.

#### 2.15.3 정답 — `UnrealEd` 의존성만 추가

```csharp
// ✅ MyEditorModule.Build.cs
PublicDependencyModuleNames.AddRange(new string[]
{
    "Core", "CoreUObject", "Engine",
    "UnrealEd",   // ⭐ 이 한 줄로 WorkflowOrientedApp/* 모든 헤더 + Toolkits/* 모두 가시화
    "Slate", "SlateCore",
    "PropertyEditor", "AssetTools", "ToolMenus",
    ...
});
```

cpp / 헤더의 include 는 그대로 유지:

```cpp
#include "WorkflowOrientedApp/WorkflowCentricApplication.h"   // OK — UnrealEd 모듈 안의 Public 경로
#include "WorkflowOrientedApp/ApplicationMode.h"
#include "WorkflowOrientedApp/WorkflowTabManager.h"
```

KMCProject 검증 (2026-05-15) — `MCEditorModule.Build.cs` 에 `WorkflowOrientedApp` 시도 후 RulesError → 제거 + `UnrealEd` 의존성 단독 유지로 빌드 통과. log: `[2026-05-15] fix | MCComboEditor Build.cs WorkflowOrientedApp RulesError — UnrealEd 단독 의존`.

#### 2.15.4 UnrealEd 모듈 안 폴더 vs 모듈 매트릭스

`Engine/Source/Editor/UnrealEd/Public/` 하위 폴더는 모두 **UnrealEd 모듈** — 별도 모듈로 오해 금지:

| 폴더 (Public/) | 헤더 예시 | 모듈 |
| -- | -- | -- |
| `Toolkits/` | `AssetEditorToolkit.h` / `BaseToolkit.h` / `SimpleAssetEditor.h` | UnrealEd |
| `WorkflowOrientedApp/` | `WorkflowCentricApplication.h` / `ApplicationMode.h` / `WorkflowTabManager.h` | UnrealEd |
| `Kismet2/` | `BlueprintEditor.h` / `BlueprintEditorUtils.h` | UnrealEd |
| `EditorModes/` | `EdMode.h` / `EditorModeManager.h` | UnrealEd |
| `EditorReimportHandler/` | (재import 보조) | UnrealEd |
| `Tests/` | (Editor automation) | UnrealEd |

⭐ **검증 방법** — 폴더 vs 모듈 의심 시:

```
1. Engine/Source/ 하위 Build.cs 전체 grep
   grep -r "class .*Build.cs" Engine/Source/Editor/  (Linux)
   gci -Recurse Engine/Source/Editor -Filter *.Build.cs  (PowerShell)
2. 의심 폴더에 *.Build.cs 가 없으면 = 모듈 아님 — 상위 폴더의 Build.cs 검색
3. include path 의 첫 segment 가 폴더명일 수 있음 — 모듈명과 무관
```

`Engine/Source/Editor/UnrealEd/Public/WorkflowOrientedApp/` 에 `*.Build.cs` 없음 → `UnrealEd.Build.cs` (상위) 가 진짜 모듈 정의.

#### 2.15.5 유사 함정 — 다른 폴더-처럼-보이는-모듈-아닌-위치

| 의심 include | 실제 모듈 | 진단 |
| -- | -- | -- |
| `#include "Toolkits/AssetEditorToolkit.h"` | UnrealEd | Toolkits 모듈 X |
| `#include "Kismet2/BlueprintEditor.h"` | UnrealEd | Kismet2 모듈 X (Kismet 은 별도 모듈) |
| `#include "PropertyEditor/Public/IDetailCustomization.h"` | PropertyEditor | OK — PropertyEditor 가 실제 모듈 |
| `#include "AssetTools/Public/IAssetTypeActions.h"` | AssetTools | OK — 일부는 Developer 모듈 |
| `#include "SlateCore/Public/Layout/Geometry.h"` | SlateCore | OK |

#### 2.15.6 KMCProject Build.cs 채용 규약 (2026-05-15)

```csharp
// MCEditorModule.Build.cs — Toolkit/Workflow 통합 표준
public class MCEditorModule : ModuleRules
{
    public MCEditorModule(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core", "CoreUObject", "Engine",
            "Slate", "SlateCore",
            "UnrealEd",            // ⭐ FWorkflowCentricApplication / FApplicationMode / FWorkflowTabFactory + Toolkits 모두 export
            "AssetTools",
            "PropertyEditor",
            "ToolMenus",
            "EditorStyle", "EditorWidgets",
            "AdvancedPreviewScene",
            "WorkspaceMenuStructure",
            // NOTE: FWorkflowCentricApplication / FApplicationMode / FWorkflowTabFactory 는
            //       UnrealEd 모듈 안 Public/WorkflowOrientedApp/ 폴더에 위치 (별도 모듈 X).
            //       UnrealEd 의존성으로 충분.
        });
    }
}
```

⭐ **Build.cs 안 주석으로 함정 회피 메모 의무** — 미래 갱신 시 다시 `"WorkflowOrientedApp"` 추가 시도 방지.

#### 2.15.7 함정 매트릭스 (Cycle 5d Build.cs 후보)

| 시도 | 결과 | 정답 |
| -- | -- | -- |
| `"WorkflowOrientedApp"` 추가 | UBT RulesError | `UnrealEd` 단독 |
| `"Toolkits"` 추가 | UBT RulesError | `UnrealEd` 단독 |
| `"Kismet2"` 추가 | UBT RulesError | `UnrealEd` 단독 (Kismet 은 별도 모듈) |
| `"WorkflowCentricApplication"` 추가 | UBT RulesError | `UnrealEd` 단독 |

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어 sub-skill: [[sources/ue-editor-unrealed-subsystems]] (`UAssetEditorSubsystem` 외부 진입) / [[sources/ue-editor-assettools]] (`IAssetTypeActions`) / [[sources/ue-editor-asseteditorapi]] (실행 중 접근) / [[sources/ue-editor-propertyeditor]] (Details Tab) / [[sources/ue-editor-toolmenus]] (5.x 메뉴) / [[sources/ue-editor-unrealed-kismet2]] (`FBlueprintEditor` 자손)
- Slate: [[sources/ue-slate-docking]] (FTabManager / SDockTab) / [[sources/ue-slate-menu]] / [[sources/ue-slate-commands]] (FUICommandList)
- 횡단: [[sources/ue-ref-04-overrideindex]] §6 (Super 규약) / [[sources/ue-ref-05-editoronlyindex]] (4단 분리) / [[sources/ue-ref-07-profilingscopeRule]]
- ⭐⭐⭐ §2.15 페어 — [[sources/ue-coreuobject-uobject]] §2.13 (forward-declared UObject 자손 → UObject\* 변환 C2664, Cycle 5d 같은 KMCProject MCComboEditor 실측)
- MC-시리즈 사례: [[sources/ue-docs-claude]] (KMCProject `MCEditorModule` 동일 패턴) · [[synthesis/mc-combo-editor-levelsequence-lite]] (KMCProject MCComboEditor — §2.15 적용 사례, Cycle 5d)

### 관련 fix log

- ⭐⭐⭐ `[2026-05-15] fix | MCComboEditor Build.cs WorkflowOrientedApp RulesError — UnrealEd 단독 의존` — §2.15 1차 검증
