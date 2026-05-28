---
name: slate-docking
description: 🛠 FTabManager + FTabSpawnerEntry + FLayoutExtender + SDockTab + SDockingArea - 도킹 시스템.
---

# Slate / Docking 🛠

> 부모 모듈: [`Slate`](../SKILL.md) · UE 5.5.4
> 다루는 영역: 인하우스 툴 도킹 시스템 — `SDockTab` · `FTabManager` · `FGlobalTabmanager` · `SDockingArea` · `FWorkspaceItem` · `FLayoutExtender` · `FLayoutSaveRestore` · `FSpawnTabArgs` · `FTabCommands` · 탭 등록/호출/레이아웃 저장·복원 패턴
> 🛠 사실상 에디터/인하우스 툴 빌드 한정 — 게임 UI에서 거의 사용 안 함.
> 관련 sub-skill: [`EditorApplication/`](../EditorApplication/SKILL.md), [`Menu/`](../Menu/SKILL.md), [`Commands/`](../Commands/SKILL.md), [`CommonWidgets/`](../CommonWidgets/SKILL.md)

---

## 1. 개요

도킹 시스템은 인하우스 툴의 **창 안 창** — 사용자가 탭을 자유롭게 끌어 분할·합치고, 별도 윈도우로 떼어내거나 다시 도킹할 수 있게 한다. UE 에디터 전체 인터페이스(레벨 에디터·콘텐츠 브라우저·디테일·아웃라이너)가 모두 이 위에서 동작.

```
FGlobalTabmanager (싱글턴 — 앱 전역)
   ├─ Major Tabs          (앱 최상위 탭 — 보통 한 노매드 툴 = 한 메이저 탭)
   ├─ Nomad Tabs          (어디든 둘 수 있는 자유 탭 — Output Log/Project Settings/사용자 인하우스 툴)
   └─ FTabManager (자식 — 한 메이저 탭 안의 minor tab 그룹 관리)
        ├─ Minor Tabs     (한 메이저 탭 영역 안의 작은 탭들 — 디테일/아웃라이너/뷰포트)
        └─ FLayout        (FArea / FSplitter / FStack 트리)
             └─ FTab      (탭 위치·상태 정보)
                  └─ SDockTab (실제 위젯)
```

핵심 개념:

- **탭 ID** (`FTabId`/`FName`) — 등록 시 사용하는 식별자.
- **탭 스포너** (`FOnSpawnTab` 콜백) — `FName` → `TSharedRef<SDockTab>` 생성.
- **레이아웃** (`FTabManager::FLayout`) — 탭 트리 구조의 직렬화 가능 표현. ini 저장.
- **워크스페이스 메뉴** (`FWorkspaceItem`) — 메뉴에서 탭을 카테고리별로 그룹화.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Framework/Docking/TabManager.h` | `class FTabManager : TSharedFromThis<FTabManager>` (L386) | **본체**. 탭 스포너 등록·호출·레이아웃 관리. |
| `Public/Framework/Docking/TabManager.h` | `class FGlobalTabmanager : public FTabManager` (L1280) | 앱 전역 싱글턴. `Get()` 정적, `RegisterNomadTabSpawner` (L1315). |
| `Public/Framework/Docking/TabManager.h` | `class FSpawnTabArgs` (L130), `DECLARE_DELEGATE_RetVal_OneParam(TSharedRef<SDockTab>, FOnSpawnTab, const FSpawnTabArgs&)`, `FCanSpawnTab`, `FOnFindTabToReuse` | 스포너 콜백 인자 + 델리게이트 시그니처. |
| `Public/Framework/Docking/TabManager.h` | `struct FMinorTabConfig` (L166) | Minor 탭 등록 설정. |
| `Public/Framework/Docking/TabManager.h` | `enum class ESidebarLocation : uint8` (L34), `enum class ETabIdFlags : uint8` (L46), `struct FTabId` (L54), `enum class ETabReadOnlyBehavior : int32` (L207) | 탭 식별자·사이드바 위치·읽기 전용 정책. |
| `Public/Framework/Docking/TabManager.h` | 내부 클래스 — `FLayoutNode` / `FStack` / `FSplitter` / `FArea` / `FLayout` / `FTab` | 레이아웃 트리. ini 직렬화 가능. |
| `Public/Widgets/Docking/SDockTab.h` | `class SDockTab : public SBorder` (L49) | 탭 위젯 본체. `SLATE_BEGIN_ARGS` 로 Content/TabRole/Label/OnTabClosed/OnTabActivated 설정. |
| `Public/Framework/Docking/WorkspaceItem.h` | `class FWorkspaceItem : TSharedFromThis<FWorkspaceItem>` (L12), 정적 `NewGroup(...)` 4가지 변형 | 메뉴 카테고리 노드. 자식 그룹·탭 트리. |
| `Public/Framework/Docking/LayoutExtender.h` | `class FLayoutExtender : TSharedFromThis<FLayoutExtender>`, `enum class ELayoutExtensionPosition` (Before/After/Above/Below), `typedef TFunction<void(TSharedRef<FTabManager::FArea>)> FAreaExtension` | 다른 모듈의 기본 레이아웃에 탭 끼워 넣기. |
| `Public/Framework/Docking/LayoutService.h` | `struct FLayoutSaveRestore` — `SaveToConfig` / `LoadFromConfig` / `GetAdditionalLayoutConfigIni` 정적 | 레이아웃 ini 저장·복원. |
| `Public/Framework/Docking/TabCommands.h` | `class FTabCommands : TCommands<FTabCommands>` — `CloseMajorTab`/`CloseMinorTab`/`CloseFocusedTab` | 탭 닫기 단축키. |
| `Public/Framework/Docking/STabDrawer.h` | `class STabDrawer` | 사이드바에서 슬라이드 나오는 탭 서랍. |

### 2.1 ETabRole (탭의 위치/역할 분류)

`SDockTab.h` 의 `enum class ETabRole`:

- `MajorTab` — 앱 최상위 탭 (한 도구 = 한 메이저 탭).
- `PanelTab` — 메이저 탭 안의 일반 패널 (디테일/아웃라이너).
- `NomadTab` — 어디든 둘 수 있는 자유 탭 (Output Log, 사용자 도구).
- `DocumentTab` — 한 메이저 탭 안에서 여러 문서 (BP 에디터의 그래프 탭들).
- `NumRoles` — sentinel.

인하우스 툴은 보통 `NomadTab` (단독 윈도우/도킹 자유) 또는 `MajorTab` (전체 앱).

---

## 3. 자주 쓰는 API

### 3.1 탭 스포너 등록 (모듈 StartupModule)

```cpp
// === Nomad 탭 등록 (가장 흔한 인하우스 툴 패턴) ===
FGlobalTabmanager::Get()->RegisterNomadTabSpawner(MyTabId,
    FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnTab))                      // L1499
    .SetDisplayName(LOCTEXT("MyTool", "My Tool"))
    .SetTooltipText(LOCTEXT("MyToolTip", "Open the My Tool window"))
    .SetIcon(FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Tool"))
    .SetGroup(WorkspaceMenu::GetMenuStructure().GetDeveloperToolsMiscCategory());

// === 일반 (Minor) 탭 — 메이저 탭 안의 패널 ===
TabManager->RegisterTabSpawner(MyDetailsTabId,                                   // L988
    FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnDetailsTab))
    .SetDisplayName(LOCTEXT("Details", "Details"))
    .SetGroup(WorkspaceItem);                                                     // FWorkspaceItem
```

### 3.2 탭 호출

```cpp
// 메뉴/단축키에서 탭 열기
FGlobalTabmanager::Get()->TryInvokeTab(MyTabId);                                  // L1049 (virtual)

// 메뉴 항목에서 호출 (자동 위치 결정)
FGlobalTabmanager::Get()->InvokeTabForMenu(MyTabId);                              // L1184

// 이미 살아있는 탭 찾기 (활성화 안 하고 조회만)
TSharedPtr<SDockTab> Existing = TabManager->FindExistingLiveTab(MyTabId);         // L1057

// 등록 여부 확인
bool bRegistered = TabManager->HasTabSpawner(MyTabId);                            // L1144
```

### 3.3 SpawnTab 콜백 골격

```cpp
TSharedRef<SDockTab> FMyToolModule::SpawnTab(const FSpawnTabArgs& Args)
{
    return SNew(SDockTab)
        .TabRole(ETabRole::NomadTab)              // 또는 MajorTab/PanelTab/DocumentTab
        .Label(LOCTEXT("MyTool", "My Tool"))
        .OnTabClosed_Lambda([](TSharedRef<SDockTab>) { /* 정리 */ })
        [
            SNew(SVerticalBox)
            // 메뉴/툴바: Menu/SKILL.md 의 FMenuBuilder/FToolBarBuilder
            // 단축키:   Commands/SKILL.md 의 FUICommandList
            // 컨텐츠:   사용자 위젯
        ];
}
```

### 3.4 레이아웃 직접 정의 (메이저 탭 안의 minor 탭 트리)

```cpp
TSharedRef<FTabManager::FLayout> Layout = FTabManager::NewLayout("MyTool_Layout_v1")
    ->AddArea
    (
        FTabManager::NewPrimaryArea()->SetOrientation(Orient_Horizontal)
        ->Split
        (
            FTabManager::NewSplitter()->SetOrientation(Orient_Vertical)->SetSizeCoefficient(0.3f)
            ->Split( FTabManager::NewStack()->SetSizeCoefficient(0.5f)->AddTab(OutlinerTabId, ETabState::OpenedTab) )
            ->Split( FTabManager::NewStack()->SetSizeCoefficient(0.5f)->AddTab(DetailsTabId,  ETabState::OpenedTab) )
        )
        ->Split
        (
            FTabManager::NewStack()->SetSizeCoefficient(0.7f)->AddTab(ViewportTabId, ETabState::OpenedTab)
        )
    );

// 사용 (보통 메이저 탭의 SpawnTab 안에서):
TSharedRef<SDockTab> MajorTab = SNew(SDockTab).TabRole(ETabRole::MajorTab);
TSharedRef<FTabManager> ChildTM = FGlobalTabmanager::Get()->NewTabManager(MajorTab);
ChildTM->RegisterTabSpawner(OutlinerTabId, FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnOutliner));
ChildTM->RegisterTabSpawner(DetailsTabId,  FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnDetails));
ChildTM->RegisterTabSpawner(ViewportTabId, FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnViewport));

TSharedRef<SWidget> TabContent = ChildTM->RestoreFrom(Layout, MajorTab->GetParentWindow()).ToSharedRef();
MajorTab->SetContent(TabContent);
```

### 3.5 레이아웃 저장 / 복원 (`FLayoutSaveRestore`)

```cpp
// 저장 (보통 OnPersistLayout 콜백에서)
TabManager->SetOnPersistLayout(                                                   // L963
    FTabManager::FOnPersistLayout::CreateLambda([](const TSharedRef<FTabManager::FLayout>& Lay) {
        FLayoutSaveRestore::SaveToConfig(GEditorLayoutIni, Lay);
    }));

// 복원
TSharedRef<FTabManager::FLayout> Loaded =
    FLayoutSaveRestore::LoadFromConfig(GEditorLayoutIni, DefaultLayout);
```

`GEditorLayoutIni` 또는 자체 ini 경로 사용. 기본 레이아웃은 코드에서 정의(`NewLayout("MyTool_Layout_v1")`).

### 3.6 워크스페이스 메뉴 그룹

```cpp
// 자체 카테고리 만들기
TSharedRef<FWorkspaceItem> Group = FWorkspaceItem::NewGroup(
    LOCTEXT("MyToolsGroup", "My Tools"),
    FSlateIcon(FAppStyle::GetAppStyleSetName(), "MyToolGroup.Icon"));

// 또는 엔진 표준 그룹 사용 (UnrealEd 측 WorkspaceMenuStructureModule)
auto& MenuStructure = WorkspaceMenu::GetMenuStructure();
TSharedRef<FWorkspaceItem> Devs = MenuStructure.GetDeveloperToolsMiscCategory();

// 스포너에 그룹 지정
FGlobalTabmanager::Get()->RegisterNomadTabSpawner(MyTabId, FOnSpawnTab::CreateRaw(...))
    .SetGroup(Devs);
```

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 FTabManager (드물게 override)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual TSharedPtr<SDockTab> TryInvokeTab(const FTabId&, bool bInvokeAsInactive=false)` | TabManager.h L1049 | 탭 호출 — 커스텀 정책 시 override. |
| `virtual bool CanCloseManager(const TSet<TSharedRef<SDockTab>>&)` | (FGlobalTabmanager) | 닫기 차단 (저장 안 된 변경 등). |
| `FLayoutNode::AsStack/AsSplitter/AsArea` | TabManager.h | 레이아웃 트리 다형 캐스트. |

### 4.2 SDockTab 콜백 (델리게이트로 받음)

```cpp
// SLATE_EVENT 인자로 바인딩
SLATE_EVENT(FOnTabClosedCallback,    OnTabClosed)             // 닫힘 후
SLATE_EVENT(FOnTabActivatedCallback, OnTabActivated)          // 활성화 (포커스/클릭)
SLATE_EVENT(FSimpleDelegate,         OnTabRelocated)          // 다른 위치로 이동
SLATE_EVENT(FSimpleDelegate,         OnTabDraggedOverDockArea)
SLATE_EVENT(FCanCloseTab,            OnCanCloseTab)           // 닫기 전 검증 (false 반환 시 차단)
SLATE_EVENT(FOnPersistVisualState,   OnPersistVisualState)    // 비주얼 상태 저장 시점
SLATE_EVENT(FExtendContextMenu,      OnExtendContextMenu)     // 컨텍스트 메뉴 항목 추가
SLATE_EVENT(FSimpleDelegate,         OnTabDrawerClosed)
```

### 4.3 SDockTab SWidget virtual (드래그/입력)

`SDockTab : SBorder` 가 다음을 override:

- `OnMouseButtonDown`/`Up`/`DoubleClick`
- `OnDragDetected` — 탭을 떼어내 다른 영역으로
- `OnDragEnter`/`OnDragLeave`/`OnDrop`
- `OnTouchStarted`/`Ended`

일반 코드는 거의 만지지 않음 (도킹 시스템이 자동 처리).

---

## 5. 인하우스 툴 모듈 골격 (실용)

```cpp
// FMyToolModule.h
class FMyToolModule : public IModuleInterface
{
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;

private:
    static const FName MyTabId;
    TSharedRef<SDockTab> SpawnTab(const FSpawnTabArgs& Args);

    TSharedPtr<class FUICommandList> Cmds;
};

const FName FMyToolModule::MyTabId(TEXT("MyTool"));

// FMyToolModule.cpp
void FMyToolModule::StartupModule()
{
#if WITH_EDITOR
    // 1) 단축키 등록 (Commands/SKILL.md)
    FMyToolCommands::Register();
    Cmds = MakeShared<FUICommandList>();
    Cmds->MapAction(FMyToolCommands::Get().Open,
        FExecuteAction::CreateLambda([]() {
            FGlobalTabmanager::Get()->TryInvokeTab(FMyToolModule::MyTabId);
        }));

    // 2) Nomad 탭 스포너 등록
    FGlobalTabmanager::Get()->RegisterNomadTabSpawner(MyTabId,
        FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnTab))
        .SetDisplayName(LOCTEXT("MyTool", "My Tool"))
        .SetTooltipText(LOCTEXT("MyToolTip", "Open My Tool"))
        .SetIcon(FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Tool"))
        .SetGroup(WorkspaceMenu::GetMenuStructure().GetDeveloperToolsMiscCategory());

    // 3) 메인 메뉴에 항목 추가 (Menu/SKILL.md 의 Extender 패턴)
    // ...
#endif
}

void FMyToolModule::ShutdownModule()
{
#if WITH_EDITOR
    if (FSlateApplication::IsInitialized())
    {
        FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(MyTabId);
    }
    if (Cmds.IsValid())
    {
        Cmds.Reset();
        FMyToolCommands::Unregister();
    }
#endif
}

TSharedRef<SDockTab> FMyToolModule::SpawnTab(const FSpawnTabArgs& Args)
{
    // 한 메이저/노매드 탭 안에 minor 탭 트리를 두는 패턴
    TSharedRef<SDockTab> MajorTab = SNew(SDockTab)
        .TabRole(ETabRole::NomadTab)
        .Label(LOCTEXT("MyTool", "My Tool"));

    TSharedRef<FTabManager> ChildTM = FGlobalTabmanager::Get()->NewTabManager(MajorTab);

    static const FName OutlinerId(TEXT("MyTool.Outliner"));
    static const FName DetailsId (TEXT("MyTool.Details"));
    ChildTM->RegisterTabSpawner(OutlinerId, FOnSpawnTab::CreateLambda([](const FSpawnTabArgs&) {
        return SNew(SDockTab).TabRole(ETabRole::PanelTab).Label(LOCTEXT("Outliner", "Outliner"))
               [ /* outliner 위젯 */ ];
    }));
    ChildTM->RegisterTabSpawner(DetailsId, FOnSpawnTab::CreateLambda([](const FSpawnTabArgs&) {
        return SNew(SDockTab).TabRole(ETabRole::PanelTab).Label(LOCTEXT("Details", "Details"))
               [ /* details 위젯 */ ];
    }));

    TSharedRef<FTabManager::FLayout> Layout = FTabManager::NewLayout("MyTool_Layout_v1")
        ->AddArea(
            FTabManager::NewPrimaryArea()->SetOrientation(Orient_Horizontal)
            ->Split( FTabManager::NewStack()->SetSizeCoefficient(0.3f)->AddTab(OutlinerId, ETabState::OpenedTab) )
            ->Split( FTabManager::NewStack()->SetSizeCoefficient(0.7f)->AddTab(DetailsId,  ETabState::OpenedTab) )
        );

    // 저장된 사용자 레이아웃이 있으면 그것을 우선
    Layout = FLayoutSaveRestore::LoadFromConfig(GEditorLayoutIni, Layout);

    ChildTM->SetOnPersistLayout(
        FTabManager::FOnPersistLayout::CreateLambda([](const TSharedRef<FTabManager::FLayout>& Lay) {
            FLayoutSaveRestore::SaveToConfig(GEditorLayoutIni, Lay);
        }));

    TSharedPtr<SWidget> Content = ChildTM->RestoreFrom(Layout, MajorTab->GetParentWindow());
    if (Content.IsValid()) MajorTab->SetContent(Content.ToSharedRef());

    return MajorTab;
}
```

---

## 6. FLayoutExtender — 다른 모듈의 레이아웃에 끼어들기

```cpp
// 다른 모듈의 기본 레이아웃에 내 탭 추가 (예: 레벨 에디터에 패널 추가)
TSharedRef<FLayoutExtender> Ext = MakeShared<FLayoutExtender>();
Ext->ExtendLayout(
    /*PredecessorTabId=*/FTabId(TEXT("LevelEditor.SelectionDetails")),
    ELayoutExtensionPosition::After,
    FTabManager::FTab(FTabId(TEXT("MyTool.Details")), ETabState::OpenedTab));

// 호스트 모듈이 노출하는 레이아웃 익스텐션 등록 API에 전달
LevelEditorModule.AddCustomLayoutExtension(Ext);
```

호스트 모듈이 `FLayoutExtender` 를 받아주는 구조여야 함 (UnrealEd / LevelEditor 등 표준 모듈은 노출).

---

## 7. 운영 가이드 / 함정

1. **`MyTabId` FName 충돌** — 모든 노매드 탭은 전역 식별자. `FName(TEXT("MyTool"))` 같은 일반명 피하고 `FName(TEXT("MyCompany.MyTool"))` 같은 네임스페이스 prefix.
2. **레이아웃 버전** — `FTabManager::NewLayout("MyTool_Layout_v1")` 의 `_v1`. 레이아웃 구조 바꿀 때마다 `_v2`, `_v3` 으로 증가 — 옛 사용자 ini 가 새 트리와 호환 안 되면 자동으로 기본값 fallback.
3. **`ShutdownModule` 누락** — `UnregisterNomadTabSpawner` 안 호출하면 hot-reload 시 댕글링.
4. **ETabRole 잘못 선택** — Major/Minor/Nomad 차이를 정확히. Minor 탭을 Nomad 로 등록하면 떼어내기 등 동작이 어색.
5. **`OnPersistVisualState`** — 탭의 사용자 정의 상태(예: 분할 비율, 선택된 아이템) 저장. 호출 시점에 모든 위젯이 살아있어야.
6. **`FindExistingLiveTab`** 후 `nullptr` 가능 — 탭이 닫혔거나 다른 탭매니저에 있음. 항상 valid 체크.
7. **메이저 탭 안의 minor 탭 트리 스포너 등록** — 매번 `SpawnTab` 호출마다 `ChildTM->RegisterTabSpawner` 가 다시 — idempotent 인지 확인 (보통 unregister-register 패턴).
8. **`WorkspaceMenu::GetMenuStructure()`** — `WorkspaceMenuStructureModule` 의존. 인하우스 툴 모듈 Build.cs 에 추가.
9. **`GEditorLayoutIni`** 는 에디터 빌드 전용 — standalone 툴은 자체 ini 경로 사용 (`FPaths::GeneratedConfigDir() / TEXT("MyTool.ini")` 등).
10. **`FTabId` vs `FName`** — 등록은 `FName`, 조회/스폰은 `FTabId`(내부 `FName + Instance Id` 쌍). 단순 케이스는 `FName` 만으로 충분.

---

## 8. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

> **🚨 런타임/에디터 분리 원칙은 [`Slate/SKILL.md §8`](../SKILL.md#8--런타임--에디터-분리-원칙-인하우스-툴-묶음-공통-규약) 의무 규약.** `FGlobalTabmanager` 호출은 모두 `#if WITH_EDITOR` 안에. `WorkspaceMenuStructure` 모듈은 게임 빌드에 없으므로 `Build.cs` 의 `bBuildEditor` 분기로 의존성 분리.

본 sub-skill 전체가 사실상 에디터/툴 빌드 한정. 게임 빌드에서도 코드 자체는 컴파일되지만 사용처 거의 없음.

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| 모든 탭 스포너 등록 🛠 | TabManager.h | `WITH_EDITOR` 권장 | 게임 UI는 다른 패턴 사용. |
| `FLayoutSaveRestore` 🛠 | LayoutService.h | 에디터 ini 의존 | `GEditorLayoutIni` 가 에디터 빌드만 정의. |
| `WorkspaceMenu::GetMenuStructure()` 🛠 | (별도 모듈 `WorkspaceMenuStructure`) | 에디터 모듈 | 게임 빌드에는 모듈 없음. |
| `FLayoutExtender` 🛠 | LayoutExtender.h | 에디터 패턴 | 호스트 모듈이 노출해야 가능. |
| `STabDrawer` 🛠 | STabDrawer.h | 에디터 5.x 사이드바 | |

---

## 9. 관련 sub-skill

- [`EditorApplication/`](../EditorApplication/SKILL.md) — `FGlobalTabmanager::Get()` 진입점
- [`Menu/`](../Menu/SKILL.md) — `FMenuBuilder` 로 메인 메뉴에 탭 호출 항목 추가
- [`Commands/`](../Commands/S