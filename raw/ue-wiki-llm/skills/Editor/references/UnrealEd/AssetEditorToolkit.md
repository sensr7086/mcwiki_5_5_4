---
name: unrealed-asseteditortoolkit
description: 🛠 FAssetEditorToolkit + FBaseAssetToolkit - 에셋 에디터 윈도우 + 5.x SubobjectEditor + DataLayer 통합.
---

# UnrealEd · AssetEditorToolkit sub-skill 🛠

> **모듈**: UnrealEd (Editor 전용)
> **위치**: `Engine/Source/Editor/UnrealEd/Public/Toolkits/` + `Public/WorkflowOrientedApp/`
> **다루는 범위**: 인하우스 에셋 에디터의 표준 베이스 — `FAssetEditorToolkit` · `FBaseToolkit` · `FSimpleAssetEditor` · `FWorkflowCentricApplication` · `FExtensibilityManager` + Toolbar/Tabs/Modes 등록.

---

## 1. 개요

UE 에디터의 **모든 에셋 에디터** (Material Editor, Blueprint Editor, Animation Editor, Behavior Tree Editor 등) 의 베이스. 인하우스 에셋 에디터를 만들려면 `FAssetEditorToolkit` 자손을 정의하고 `IAssetTypeActions` 와 연결해 더블클릭 시 자동으로 열리도록 한다.

**구성 요소**:
- `FAssetEditorToolkit` — 단일 에셋(또는 묶음) 편집기 베이스
- `FSimpleAssetEditor` — 가장 단순한 형태(디테일 패널만) 즉시 사용 가능
- `FWorkflowCentricApplication` — 모드 전환형 에디터 (Persona·BehaviorTree·BlueprintEditor 패턴)
- `FExtensibilityManager` — 외부 모듈에서 메뉴/툴바 확장
- `IToolkitHost` / `SStandaloneAssetEditorToolkitHost` — 호스팅 프레임

---

## 2. 핵심 헤더와 클래스

### 2.1 헤더 (5.7.4)

| 클래스 | 헤더 | 라인 |
|--------|------|------|
| `FExtensibilityManager` | `Public/Toolkits/AssetEditorToolkit.h` | L57 |
| `IHasMenuExtensibility` | `Public/Toolkits/AssetEditorToolkit.h` | L82 |
| `IHasToolBarExtensibility` | `Public/Toolkits/AssetEditorToolkit.h` | L89 |
| `FAssetEditorToolkit` | `Public/Toolkits/AssetEditorToolkit.h` | L114 |
| `FBaseToolkit` | `Public/Toolkits/BaseToolkit.h` | L27 |
| `FModeToolkit` | `Public/Toolkits/BaseToolkit.h` | L98 |
| `FSimpleAssetEditor` | `Public/Toolkits/SimpleAssetEditor.h` | L12 |
| `FWorkflowCentricApplication` | `Public/WorkflowOrientedApp/WorkflowCentricApplication.h` | (헤더 참조) |
| `FApplicationMode` | `Public/WorkflowOrientedApp/ApplicationMode.h` | (헤더 참조) |
| `FWorkflowTabFactory` | `Public/WorkflowOrientedApp/WorkflowTabFactory.h` | (헤더 참조) |
| `FTabManager` (ref) | `Slate/Public/Framework/Docking/TabManager.h` | (`Slate/Docking` sub-skill) |

### 2.2 IToolkit 인터페이스 베이스

`FAssetEditorToolkit` 은 `IToolkit` 인터페이스(`EditorFramework`) 구현. 핵심 콜백 표는 §4 참조.

---

## 3. 자주 쓰는 API

### 3.1 인스턴스 시작 (가장 자주)

| API | 메모 |
|-----|------|
| `void InitAssetEditor(EToolkitMode::Type Mode, TSharedPtr<IToolkitHost> InitToolkitHost, FName AppIdentifier, TSharedRef<FTabManager::FLayout> StandaloneDefaultLayout, bool bCreateDefaultStandaloneMenu, bool bCreateDefaultToolbar, const TArray<UObject*>& ObjectsToEdit, ...)` | AssetEditorToolkit.h L141 — 표준 진입. `EToolkitMode::Standalone`(독립 윈도우) 또는 `EToolkitMode::WorldCentric`(레벨 에디터 안). FAppIdentifier 는 GUID-like 고유 키. |
| `void InitAssetEditor(..., UObject* ObjectToEdit, ...)` | L142 — 단일 객체 편집 편의 |
| `void AddEditingObject(UObject* Object)` | L349 — 추가 편집 객체 |
| `void RemoveEditingObject(UObject* Object)` | L352 — 제거 |

`FTabManager::FLayout` 작성 패턴 (자세한 [`Slate/Docking`](../../Slate/references/Docking.md)):

```cpp
TSharedRef<FTabManager::FLayout> StandaloneDefaultLayout =
    FTabManager::NewLayout("Standalone_MyAssetEditor_Layout_v1.0")
    ->AddArea
    (
        FTabManager::NewPrimaryArea()->SetOrientation(Orient_Vertical)
        ->Split(FTabManager::NewStack()->AddTab(MyDetailsTabId, ETabState::OpenedTab))
        ->Split(FTabManager::NewStack()->AddTab(MyViewportTabId, ETabState::OpenedTab))
    );
```

### 3.2 Tab 등록 / 해제

`RegisterTabSpawners(TSharedRef<FTabManager>)` / `UnregisterTabSpawners(TSharedRef<FTabManager>)` override 후:

```cpp
void FMyAssetEditor::RegisterTabSpawners(const TSharedRef<FTabManager>& InTabManager)
{
    FAssetEditorToolkit::RegisterTabSpawners(InTabManager);     // ← Super FIRST 의무
    
    InTabManager->RegisterTabSpawner(MyDetailsTabId, FOnSpawnTab::CreateSP(this, &FMyAssetEditor::SpawnDetailsTab))
        .SetDisplayName(NSLOCTEXT("MyEditor", "DetailsTab", "Details"))
        .SetGroup(GetWorkspaceMenuCategory());
}
```

### 3.3 메뉴 / 툴바 확장 (`FExtensibilityManager`)

자손에서 `IHasMenuExtensibility` / `IHasToolBarExtensibility` 구현 → 외부 모듈이 `FExtender` 추가 가능:

```cpp
class FMyAssetEditor : public FAssetEditorToolkit, public IHasMenuExtensibility, public IHasToolBarExtensibility
{
    // ...
    virtual TSharedPtr<FExtensibilityManager> GetMenuExtensibilityManager() override { return MenuExtensibilityManager; }
    virtual TSharedPtr<FExtensibilityManager> GetToolBarExtensibilityManager() override { return ToolBarExtensibilityManager; }

    TSharedPtr<FExtensibilityManager> MenuExtensibilityManager;
    TSharedPtr<FExtensibilityManager> ToolBarExtensibilityManager;
};
```

생성자에서 초기화:

```cpp
FMyAssetEditor::FMyAssetEditor()
{
    MenuExtensibilityManager = MakeShared<FExtensibilityManager>();
    ToolBarExtensibilityManager = MakeShared<FExtensibilityManager>();
}
```

### 3.4 ToolMenu 통합 (5.x 권장)

UE 5.x 부터는 `FExtender` 대신 `UToolMenus` 사용 권장. `FAssetEditorToolkit::InitToolMenuContext(FToolMenuContext&)` (L240) override + `FToolMenuOwnerScoped` 패턴. 자세한 [`ToolMenus`](../../ToolMenus/SKILL.md)(향후 작성).

### 3.5 윈도우 관리

| API | 메모 |
|-----|------|
| `void FocusWindow(UObject* ObjectToFocusOn = nullptr)` | L165 — 포커스 |
| `bool CloseWindow()` | L167 — 닫기 시도 (false 면 사용자 거부) |
| `bool CloseWindow(EAssetEditorCloseReason InCloseReason)` | L168 — 이유 명시 |
| `virtual bool OnRequestClose() { return true; }` | 기본 true. 저장 미완료 시 false 반환 → 닫기 차단 |
| `void InvokeTab(const FTabId& TabId)` | L170 — 탭 활성화 |

### 3.6 SimpleAssetEditor — 즉시 사용

가장 단순한 케이스 (디테일 패널만 있으면 충분) 는 `FSimpleAssetEditor` 사용:

```cpp
// IAssetTypeActions 자손에서
virtual void OpenAssetEditor(const TArray<UObject*>& InObjects, TSharedPtr<IToolkitHost> EditWithinLevelEditor) override
{
    FSimpleAssetEditor::CreateEditor(EToolkitMode::Standalone, EditWithinLevelEditor, InObjects);
}
```

`InitEditor` (SimpleAssetEditor.h L30) 가 모든 셋업을 처리. `SetPropertyVisibilityDelegate(FIsPropertyVisible)` 로 디테일 패널 필터링 가능.

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 PURE_VIRTUAL — 자손 의무 구현

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual FName GetToolkitFName() const = 0` | L155 | 고유 식별자 (예: `"MyAssetEditor"`) |
| `virtual FText GetBaseToolkitName() const = 0` | L156 | 표시 이름 |
| `virtual FString GetWorldCentricTabPrefix() const = 0` | L160 | WorldCentric 모드 탭 prefix |
| `virtual FLinearColor GetWorldCentricTabColorScale() const = 0` | (override) | 탭 색조 |
| `virtual TSharedPtr<FExtensibilityManager> GetMenuExtensibilityManager() = 0` | L85 | (`IHasMenuExtensibility` 구현 시) |
| `virtual TSharedPtr<FExtensibilityManager> GetToolBarExtensibilityManager() = 0` | L92 | (`IHasToolBarExtensibility` 구현 시) |

### 4.2 라이프사이클 (Super 호출 의무)

| 시그니처 | 위치 | Super | 의미 |
|----------|------|-------|------|
| `virtual void RegisterTabSpawners(TSharedRef<FTabManager>)` | L151 | **FIRST** | 탭 등록 |
| `virtual void UnregisterTabSpawners(TSharedRef<FTabManager>)` | L152 | **FIRST** | 탭 해제 |
| `virtual ~FAssetEditorToolkit()` | L148 | (자동) | 소멸 |
| `virtual void PostInitAssetEditor()` | L327 | (선택) | InitAssetEditor 직후 |
| `virtual void PostRegenerateMenusAndToolbars()` | L248 | (선택) | 메뉴 재생성 후 |
| `virtual bool OnRequestClose()` | (헤더) | (선택) | 닫기 직전 — false 면 차단 |
| `virtual void InitToolMenuContext(FToolMenuContext& MenuContext)` | L240 | **FIRST** | ToolMenu 컨텍스트 |
| `virtual void OnToolkitHostingStarted(TSharedRef<IToolkit> Toolkit)` | L251 | (선택) | 호스팅 시작 |
| `virtual void OnToolkitHostingFinished(TSharedRef<IToolkit> Toolkit)` | L254 | (선택) | 호스팅 종료 |

### 4.3 콘텐츠 / 객체 관리

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual const TArray<UObject*>* GetObjectsCurrentlyBeingEdited() const` | L154 | 편집 중 객체 |
| `virtual void GetSaveableObjects(TArray<UObject*>& OutObjects) const` | L346 | 저장 대상 (Save 시) |
| `virtual void AddEditingObject(UObject* Object)` | L349 | 추가 |
| `virtual void RemoveEditingObject(UObject* Object)` | L352 | 제거 |
| `virtual bool CanSaveAsset() const { return true; }` | L355 | 저장 가능? |
| `virtual void SaveAsset_Execute()` | (헤더) | 저장 실행 |
| `virtual bool IsAssetEditor() const` | L153 | (true) |
| `virtual bool IsPrimaryEditor() const { return true; }` | L169 | 메인 에디터인지 |
| `virtual bool IsSimpleAssetEditor() const { return false; }` | (override) | 단순 에디터인지 |

### 4.4 메뉴 / 툴바

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual TSharedPtr<SWidget> CreateMenuBar(...)` | L242 | 커스텀 메뉴 바 (override 시 nullptr 대신 위젯 반환) |
| `virtual FName GetToolMenuToolbarName(FName& OutParentName) const` | L239 | 툴바 메뉴 이름 |
| `virtual UToolMenu* GenerateCommonActionsToolbar(FToolMenuContext& MenuContext)` | L340 | 공통 액션 툴바 |
| `virtual void AddGraphEditorPinActionsToContextMenu(FToolMenuSection& InSection) const` | L313 | 노드 핀 컨텍스트 메뉴 |

### 4.5 뷰포트 / 드래그앤드롭

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual void AddViewportOverlayWidget(TSharedRef<SWidget>, int32 ZOrder)` | L259 | 뷰포트 위 오버레이 |
| `virtual void RemoveViewportOverlayWidget(TSharedRef<SWidget>)` | L262 | 제거 |
| `virtual void OnViewportDragEnter(...)` | L316 | 뷰포트 드래그 진입 |
| `virtual void OnViewportDragLeave(...)` | L317 | 이탈 |
| `virtual FReply OnViewportDrop(...)` | L318 | 드롭 |

### 4.6 BaseToolkit (베이스) — 자주 안 만지는 영역

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual FName GetToolkitContextFName() const` | BaseToolkit.h L42 | 컨텍스트 이름 |
| `virtual bool ProcessCommandBindings(const FKeyEvent&)` | L44 | 단축키 |
| `virtual bool IsBlueprintEditor() const { return false; }` | L49 | BP 에디터인지 |
| `virtual TSharedRef<FWorkspaceItem> GetWorkspaceMenuCategory() const` | L50 | 워크스페이스 메뉴 카테고리 |
| `virtual FEditorModeTools& GetEditorModeManager() const = 0` | L52 | EdMode 매니저 (PURE) |
| `virtual void CreateEditorModeManager()` | L76 | EdMode 매니저 생성 |

> **Super 호출 통합 표**: [`04_OverrideIndex.md §6`](../../../references/04_OverrideIndex.md). 라이프사이클 (Init/Register) → Super FIRST. 정리 (Unregister) → Super FIRST (베이스가 등록한 것 먼저 정리).

---

## 5. 예제 — 인하우스 에셋 에디터 작성 (전체 골격)

### 5.1 디렉토리 / 모듈 구조

```
MyGameEditor/                        ← Build.cs Type=Editor (별도 모듈)
├── MyGameEditor.Build.cs            ← UnrealEd, AssetTools, PropertyEditor 의존
├── Public/
│   ├── Toolkits/
│   │   ├── MyAssetEditor.h          ← FAssetEditorToolkit 자손
│   │   └── MyAssetEditorTabs.h      ← FName 상수 모음
│   └── AssetActions/
│       └── AssetTypeActions_MyAsset.h ← FAssetTypeActions_Base 자손
└── Private/
    ├── MyGameEditorModule.cpp       ← StartupModule/ShutdownModule
    ├── Toolkits/MyAssetEditor.cpp
    └── AssetActions/AssetTypeActions_MyAsset.cpp
```

### 5.2 헤더 — `MyAssetEditor.h`

```cpp
#pragma once
#if WITH_EDITOR
#include "Toolkits/AssetEditorToolkit.h"

class UMyAsset;
class IDetailsView;

class FMyAssetEditor : public FAssetEditorToolkit, public IHasMenuExtensibility, public IHasToolBarExtensibility
{
public:
    FMyAssetEditor();
    virtual ~FMyAssetEditor();

    // 외부 진입 — IAssetTypeActions 가 호출
    void InitMyAssetEditor(const EToolkitMode::Type Mode, const TSharedPtr<IToolkitHost>& InitToolkitHost, UMyAsset* InAsset);

    // FAssetEditorToolkit interface
    virtual void RegisterTabSpawners(const TSharedRef<FTabManager>& TabManager) override;
    virtual void UnregisterTabSpawners(const TSharedRef<FTabManager>& TabManager) override;
    virtual FName GetToolkitFName() const override;
    virtual FText GetBaseToolkitName() const override;
    virtual FString GetWorldCentricTabPrefix() const override;
    virtual FLinearColor GetWorldCentricTabColorScale() const override;

    // IHasMenuExtensibility / IHasToolBarExtensibility
    virtual TSharedPtr<FExtensibilityManager> GetMenuExtensibilityManager() override { return MenuExtensibilityManager; }
    virtual TSharedPtr<FExtensibilityManager> GetToolBarExtensibilityManager() override { return ToolBarExtensibilityManager; }

private:
    TSharedRef<SDockTab> SpawnDetailsTab(const FSpawnTabArgs& Args);
    TSharedRef<SDockTab> SpawnViewportTab(const FSpawnTabArgs& Args);

    TWeakObjectPtr<UMyAsset> EditingAsset;
    TSharedPtr<IDetailsView> DetailsView;
    TSharedPtr<FExtensibilityManager> MenuExtensibilityManager;
    TSharedPtr<FExtensibilityManager> ToolBarExtensibilityManager;
};
#endif // WITH_EDITOR
```

### 5.3 구현 — `MyAssetEditor.cpp`

```cpp
#include "Toolkits/MyAssetEditor.h"
#if WITH_EDITOR
#include "MyAsset.h"
#include "PropertyEditorModule.h"
#include "Framework/Docking/TabManager.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"

#define LOCTEXT_NAMESPACE "MyAssetEditor"

const FName MyAssetEditorAppIdentifier(TEXT("MyAssetEditorApp"));
const FName DetailsTabId(TEXT("MyAssetEditor_Details"));
const FName ViewportTabId(TEXT("MyAssetEditor_Viewport"));

FMyAssetEditor::FMyAssetEditor()
{
    MenuExtensibilityManager = MakeShared<FExtensibilityManager>();
    ToolBarExtensibilityManager = MakeShared<FExtensibilityManager>();
}

FMyAssetEditor::~FMyAssetEditor()
{
    // 정리는 베이스가 처리
}

void FMyAssetEditor::InitMyAssetEditor(const EToolkitMode::Type Mode, const TSharedPtr<IToolkitHost>& InitToolkitHost, UMyAsset* InAsset)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(FMyAssetEditor_InitMyAssetEditor);    // ← 프로파일링 스코프
    EditingAsset = InAsset;

    // 디테일 뷰 생성
    FPropertyEditorModule& PropertyEditorModule = FModuleManager::GetModuleChecked<FPropertyEditorModule>("PropertyEditor");
    FDetailsViewArgs Args;
    Args.bHideSelectionTip = true;
    DetailsView = PropertyEditorModule.CreateDetailView(Args);
    DetailsView->SetObject(InAsset);

    // 레이아웃 정의
    TSharedRef<FTabManager::FLayout> Layout =
        FTabManager::NewLayout("Standalone_MyAssetEditor_Layout_v1.0")
        ->AddArea(
            FTabManager::NewPrimaryArea()->SetOrientation(Orient_Horizontal)
            ->Split(FTabManager::NewStack()->SetSizeCoefficient(0.7f)->AddTab(ViewportTabId, ETabState::OpenedTab))
            ->Split(FTabManager::NewStack()->SetSizeCoefficient(0.3f)->AddTab(DetailsTabId, ETabState::OpenedTab))
        );

    // 베이스 호출 — 실제 윈도우/탭/메뉴 생성
    InitAssetEditor(Mode, InitToolkitHost, MyAssetEditorAppIdentifier, Layout,
        /*bCreateDefaultStandaloneMenu=*/true, /*bCreateDefaultToolbar=*/true,
        /*ObjectToEdit=*/InAsset);
}

void FMyAssetEditor::RegisterTabSpawners(const TSharedRef<FTabManager>& InTabManager)
{
    FAssetEditorToolkit::RegisterTabSpawners(InTabManager);     // ← Super FIRST 의무

    WorkspaceMenuCategory = InTabManager->AddLocalWorkspaceMenuCategory(LOCTEXT("WorkspaceMenu", "My Asset Editor"));
    
    InTabManager->RegisterTabSpawner(DetailsTabId, FOnSpawnTab::CreateSP(this, &FMyAssetEditor::SpawnDetailsTab))
        .SetDisplayName(LOCTEXT("DetailsTab", "Details"))
        .SetGroup(WorkspaceMenuCategory.ToSharedRef());

    InTabManager->RegisterTabSpawner(ViewportTabId, FOnSpawnTab::CreateSP(this, &FMyAssetEditor::SpawnViewportTab))
        .SetDisplayName(LOCTEXT("ViewportTab", "Viewport"))
        .SetGroup(WorkspaceMenuCategory.ToSharedRef());
}

void FMyAssetEditor::UnregisterTabSpawners(const TSharedRef<FTabManager>& InTabManager)
{
    FAssetEditorToolkit::UnregisterTabSpawners(InTabManager);   // ← Super FIRST 의무
    InTabManager->UnregisterTabSpawner(DetailsTabId);
    InTabManager->UnregisterTabSpawner(ViewportTabId);
}

TSharedRef<SDockTab> FMyAssetEditor::SpawnDetailsTab(const FSpawnTabArgs& Args)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(FMyAssetEditor_SpawnDetailsTab);
    return SNew(SDockTab).Label(LOCTEXT("DetailsTab", "Details"))[ DetailsView.ToSharedRef() ];
}

TSharedRef<SDockTab> FMyAssetEditor::SpawnViewportTab(const FSpawnTabArgs& Args)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(FMyAssetEditor_SpawnViewportTab);
    return SNew(SDockTab).Label(LOCTEXT("ViewportTab", "Viewport"))[ SNew(SBox) /* TODO: SViewport */ ];
}

FName FMyAssetEditor::GetToolkitFName() const               { return FName("MyAssetEditor"); }
FText FMyAssetEditor::GetBaseToolkitName() const            { return LOCTEXT("AppLabel", "My Asset Editor"); }
FString FMyAssetEditor::GetWorldCentricTabPrefix() const    { return LOCTEXT("WorldCentricTabPrefix", "MyAsset ").ToString(); }
FLinearColor FMyAssetEditor::GetWorldCentricTabColorScale() const { return FLinearColor(0.2f, 0.6f, 0.9f, 0.5f); }

#undef LOCTEXT_NAMESPACE
#endif // WITH_EDITOR
```

### 5.4 IAssetTypeActions 와 연결

```cpp
// AssetTypeActions_MyAsset.cpp
virtual void OpenAssetEditor(const TArray<UObject*>& InObjects, TSharedPtr<IToolkitHost> EditWithinLevelEditor) override
{
    EToolkitMode::Type Mode = EditWithinLevelEditor.IsValid() ? EToolkitMode::WorldCentric : EToolkitMode::Standalone;
    for (UObject* Obj : InObjects)
    {
        if (UMyAsset* Asset = Cast<UMyAsset>(Obj))
        {
            TSharedRef<FMyAssetEditor> Editor = MakeShared<FMyAssetEditor>();
            Editor->InitMyAssetEditor(Mode, EditWithinLevelEditor, Asset);
        }
    }
}
```

자세한 IAssetTypeActions 등록은 [`AssetTools` sub-skill](../../AssetTools/SKILL.md)(향후 작성).

### 5.5 SimpleAssetEditor — 단순 케이스

디테일 패널만 필요하면:

```cpp
virtual void OpenAssetEditor(const TArray<UObject*>& InObjects, TSharedPtr<IToolkitHost> EditWithinLevelEditor) override
{
    FSimpleAssetEditor::CreateEditor(EToolkitMode::Standalone, EditWithinLevelEditor, InObjects);
}
```

`FSimpleAssetEditor` 가 모든 셋업 처리. 추가 위젯이 필요하면 직접 `FAssetEditorToolkit` 자손 작성.

---

## 6. 🚨 함정 / 안티패턴

| 함정 | 회피 |
|------|------|
| 게임 모듈에서 직접 의존 (`#include "Toolkits/AssetEditorToolkit.h"`) | Editor 모듈로 분리 + Build.cs `Type=Editor` |
| `RegisterTabSpawners` 안에서 Super 누락 | Super FIRST 의무 — 안 하면 기본 탭(Details 등) 등록 안 됨 |
| `GetToolkitFName` / `GetBaseToolkitName` / `GetWorldCentricTabPrefix` 미구현 | PURE_VIRTUAL — 컴파일 에러 |
| `MenuExtensibilityManager` 초기화 누락 | 생성자에서 `MakeShared<FExtensibilityManager>()` 의무 |
| 레이아웃 키 (`"Standalone_..."`) 충돌 | 모듈/에셋 별 고유 키 (네임스페이스 prefix) |
| 레이아웃 변경 시 키 동일 유지 | 새 레이아웃은 `_v2.0` 등 버전 증가 — 기존 사용자 설정 리셋 |
| `OpenEditorForAsset` 직접 호출 | `UAssetEditorSubsystem::OpenEditorForAsset(MyAsset)` 사용 (Singleton 보장) |
| 에디터 닫힐 때 정리 누락 | `OnRequestClose` override + 저장 다이얼로그 |
| `Tick` override 시 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) 의무 |
| `FSimpleAssetEditor::CreateEditor` 후 추가 변경 시도 | 단순 케이스 전용 — 커스텀 필요하면 직접 자손 작성 |

---

## 7. 에디터 전용 표기 🛠

**전체 sub-skill이 에디터 전용** (`WITH_EDITOR`). 본 sub-skill을 인용하는 모든 코드:
- 헤더 include는 `#if WITH_EDITOR` 안
- Build.cs에서 `if (Target.bBuildEditor)` 안에서 `"UnrealEd"`, `"EditorFramework"`, `"PropertyEditor"`, `"AssetTools"` 의존 추가
- uplugin 의 모듈은 `"Type": "Editor"`

자세한 4단 분리 방어는 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) + [`Slate/SKILL.md §8`](../../Slate/SKILL.md).

---

## 8. 관련 sub-skill

- [`UnrealEd/SKILL.md`](../SKILL.md) — UnrealEd 메인 + 의존·빌드 + 8개 sub-skill 인덱스
- [`UnrealEd/Subsystems`](../Subsystems/SKILL.md) — UAssetEditorSubsystem (외부 진입 — `OpenEditorForAsset`)
- [`UnrealEd/Kismet2`](../Kismet2/SKILL.md) — BP 에디터의 `FBlueprintEditor` 가 본 베이스의 자손
- [`Slate/Docking`](../../Slate/references/Docking.md) — FTabManager / SDockTab / FLayoutSaveRestore
- [`Slate/Menu`](../../Slate/references/Menu.md) + [`Slate/Commands`](../../Slate/references/Commands.md) — FMenuBuilder / FUICommandList
- [`Slate/EditorApplication`](../../Slate/references/EditorApplication.md) — FSlateApplication 기반
- [`PropertyEditor/SKILL.md`](../../PropertyEditor/SKILL.md) (향후) — IDetailsView / IDetailCustomization
- [`AssetTools/SKILL.md`](../../AssetTools/SKILL.md) (향후) — IAssetTypeActions / FAssetTypeActions_Base
- [`ToolMenus/SKILL.md`](../../ToolMenus/SKILL.md) (향후) — UToolMenus / UToolMenu (5.x 신규 메뉴 시스템)
- 교차 인덱스: [`04_OverrideIndex.md §6`](../../../references/04_OverrideIndex.md) (Toolkit Super 규약) · [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) (4단 분리) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (Toolkit Tick·SpawnTab 람다 스코프)
