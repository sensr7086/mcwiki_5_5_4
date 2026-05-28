---
type: source
title: "UE Editor — ToolMenus sub-skill (5.x 모던 메뉴 표준) 🛠"
slug: ue-editor-toolmenus
source_path: raw/ue-wiki-llm/skills/Editor/references/ToolMenus.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
related_entities:
  - "[[entities/UToolMenus]]"
  - "[[entities/SWidget]]"
  - "[[entities/FUICommandList]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, editor, toolmenus, menu, toolbar, customization, 5x-modern, register-startup-callback, asset-editor-window-menu-tabmanager-not-toolmenus]
---

# UE Editor — ToolMenus sub-skill (5.x 모던 메뉴 표준) 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/ToolMenus.md]] · 15 KB · `Engine/Source/Developer/ToolMenus/` (14 Public 헤더)
> 보강 2026-05-14 — §2.7 ExtendMenu stub 함정 정밀화 + §2.8 RegisterStartupCallback 의무 패턴 + ⭐⭐⭐ §2.9 **AssetEditor Window 메뉴 = TabManager 자체 시스템** (ToolMenus 와 별도) — KMCProject 5 후보 stub 검증

## 1. Summary

UE 5.x 의 **모던 메뉴 시스템**. 기존 `FMenuBuilder` / `FToolBarBuilder` 가 *명령형* (빌더에 한 번에 다 채워서 SWidget 만들기) 인 반면, ToolMenus 는 *선언형*: **이름 기반 메뉴 등록 → 외부 모듈이 같은 이름으로 확장 → 호출 시 모든 등록 항목 합쳐서 위젯 생성**. BP/Python 노출 + `FToolMenuContext` 동적 컨텍스트 + `FCustomizedToolMenu` 사용자 토글 + `FToolMenuProfile` 가시성 — FMenuBuilder 가 못 했던 것 모두 지원. **신규 코드는 ToolMenus 표준**, 기존 `FAssetEditorToolkit` 의 InitToolMenuContext 등은 FExtender 와 혼용 가능.

⭐⭐⭐ **§2.9 핵심 발견**: AssetEditorToolkit (SkeletalMeshEditor / Persona / AnimationEditor 등) 의 **Window 메뉴는 ToolMenus 가 *아닌* TabManager 자체 시스템** — `ExtendMenu("AssetEditor.X.MainMenu.Window")` 영원히 stub. Persona 의 Window 메뉴 추가는 `FPersonaModule::OnRegisterTabs` delegate.

## 2. Key claims

### 2.1. FMenuBuilder vs UToolMenus 비교 (§1)

| 측면 | FMenuBuilder (4.x~) | UToolMenus (5.x 권장) |
| -- | -- | -- |
| 패러다임 | 명령형 빌더 | 선언형 등록·확장 |
| 확장 방식 | `FExtender` + `IExtensibilityManager` | 같은 메뉴 이름에 `ExtendMenu` |
| BP/Python 노출 | ❌ | ✅ `UFUNCTION(BlueprintCallable)` |
| 컨텍스트 객체 | (사용자 정의) | `FToolMenuContext` + `UToolMenuContextBase` |
| Customization | ❌ | ✅ `FCustomizedToolMenu` (사용자 토글) |
| Profile 시스템 | ❌ | ✅ `FToolMenuProfile` (프로파일 별 가시성) |
| 권장 | 레거시 | **신규 코드** (단, AssetEditor 내부 Window 메뉴는 §2.9 — ToolMenus 외 시스템) |

### 2.2. 핵심 헤더 14 (§2)

| 헤더 | 클래스 | 의미 |
| -- | -- | -- |
| `ToolMenus.h` | `UToolMenus` (UCLASS L100) | 글로벌 매니저 (싱글턴) |
| `ToolMenu.h` | `UToolMenu : UToolMenuBase` (L24) | 메뉴 1개 — 섹션·엔트리 보유 |
| `ToolMenuEntry.h` | `FToolMenuEntry` (L165) | 메뉴 항목 1개 |
| `ToolMenuSection.h` | `FToolMenuSection` | 섹션 (구분선 포함) |
| `ToolMenuContext.h` | `FToolMenuContext` + `UToolMenuContextBase` | 동적 컨텍스트 |
| `ToolMenuOwner.h` | `FToolMenuOwner` | 등록 주체 (Plugin/Module/UObject) |
| `ToolMenuDelegates.h` | `FNewToolMenuDelegate` 등 | 동적 섹션·엔트리 |
| `ToolMenuEntryScript.h` | `UToolMenuEntryScript` | BP/Python 으로 항목 생성 |
| `ToolMenuWidgetCollectionContext.h` | `UToolMenuWidgetCollectionContext` | 위젯 컬렉션 |
| `IToolMenusModule.h` | 모듈 | Startup / Shutdown |
| `ToolMenusLog.h` | 로그 | `LogToolMenus` |

⚠ 위치 주의: 5.x 에서 `Engine/Source/Developer/ToolMenus/` (Developer). 별개로 `ToolMenusEditor` 모듈 (Editor 안, UnrealEd 의존) 도 존재 — 추가 에디터 통합.

### 2.3. UToolMenus 글로벌 매니저 API (§3.1)

| API | 라인 | 의미 |
| -- | -- | -- |
| `static UToolMenus* Get()` | — | 싱글턴 — 가장 자주 호출 |
| `RegisterMenu(FName, FName Parent, EMultiBoxType, bool bWarn)` | L161 | 메뉴 등록 (없으면 생성, 있으면 가져옴) |
| `ExtendMenu(FName)` | L169 | 기존 메뉴 확장 — **stub 반환 가능** (§2.7 + §2.9) |
| `FindMenu(FName)` | L185 | 검색만 — stub 도 반환 |
| `IsMenuRegistered(FName) const` | — | 실제 등록 여부 (stub 제외) — ⭐⭐⭐ 진단 핵심 |
| `RemoveMenu(FName)` | L239 | 메뉴 자체 제거 |
| `static AddMenuEntryObject(UToolMenuEntryScript*)` | L205 | BP/Python 항목 추가 |
| `FindMenuCustomization(FName)` | L304 | 사용자 커스터마이징 |
| `FindMenuProfile(FName, FName Profile)` | L319 | 프로파일 별 가시성 |
| `GenerateWidget(FName, const FToolMenuContext&)` | — | 메뉴 → SWidget |
| **`static RegisterStartupCallback(const FSimpleMulticastDelegate::FDelegate&)`** | — | ⭐ **모듈 로드 순서 race 회피** (§2.8) |
| `static UnregisterOwner(FName)` | — | 모듈 unload 시 일괄 정리 |
| `static UnregisterOwnerByName(FName)` | — | (alias) |

### 2.4. ToolMenus 가 *실제* 관리하는 메뉴 이름 — 호스트별 (2026-05-14 정정)

`ExtendMenu` 가 stub 만 반환 = **해당 메뉴 이름이 ToolMenus 에 미등록** (호스트가 ToolMenus 외 시스템 사용). ToolMenus 가 실제 관리하는 메뉴는 다음 세 호스트 한정:

| 호스트 | 등록된 메뉴 이름 (검증된) | 검증 |
| -- | -- | -- |
| **MainFrame** (메인 윈도우) | `MainFrame.MainMenu.File` / `.Edit` / `.Window` / `.Tools` / `.Help` / `.Asset` (5.x) | 🟢 `SkeletalMeshEditor::ExtendMenu` line 1099 가 `MainFrame.MainMenu.Asset` 사용 |
| **LevelEditor** (레벨 에디터 + 메인 윈도우 호스트) | `LevelEditor.LevelEditorToolBar` / `LevelEditor.MainMenu` | 🟢 vault 표준 |
| **ContentBrowser** | `ContentBrowser.AssetContextMenu` / `.AssetContextMenu.<AssetType>` | 🟢 vault 표준 |
| **AssetEditor toolbar** (특정 toolbar) | `AssetEditor.<EditorName>.ToolBar` (예: `AssetEditor.SkeletalMeshEditor.ToolBar`) | 🟡 ExtendToolbar 안 사용 — vault 검증 후속 |
| ❌ **AssetEditor MainMenu** (각 toolkit Window/File 메뉴) | `AssetEditor.<EditorName>.MainMenu.*` 형태 — **ToolMenus 미등록** | 🔴 §2.9 — TabManager 자체 시스템 |

### 2.5. UToolMenu (메뉴 1개) BP-callable API (§4.1)

- `AddMenuEntry(FName SectionName, FToolMenuEntry Entry)` — 항목 추가
- `AddSection(FName, FText)` — 섹션 추가
- `AddDynamicSection(FName, FNewToolMenuDelegate)` — 동적 섹션 (런타임 결정)
- `FindOrAddSection(FName, FText)` — 섹션 검색 + 없으면 추가

### 2.6. 표준 등록 패턴 — RegisterStartupCallback 의무 (메인 윈도우 / LevelEditor / ContentBrowser 메뉴 한정)

```cpp
#if WITH_EDITOR
void FMyEditorModule::StartupModule()
{
    // ✅ 표준 — 메인 윈도우 / LevelEditor / ContentBrowser 메뉴 확장
    UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateLambda([]
    {
        UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu");
        FToolMenuSection& Section = Menu->FindOrAddSection("MyTools");
        Section.AddMenuEntry("MyAction", LOCTEXT("MyAction", "My Action"),
            LOCTEXT("MyActionTip", "Run my tool"),
            FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Edit"),
            FUIAction(FExecuteAction::CreateStatic(&FMyTool::Run)));
    }));
}

void FMyEditorModule::ShutdownModule()
{
    UToolMenus::UnregisterOwner(FName(TEXT("MyEditorModule")));
}
#endif
```

### 2.7. ⭐ ExtendMenu 함정 — stub 반환 (2026-05-14 정밀화)

`ExtendMenu(FName)` 의 특수 동작 — *항상 valid UToolMenu* 반환:

- 메뉴가 실제 등록되어 있으면 → 해당 UToolMenu 반환 (entry 추가 시 즉시 적용)
- 메뉴가 미등록 상태면 → **stub UToolMenu** 반환 (entry 추가는 stub 에만 — 실제 렌더링 X)

**stub 반환의 2가지 원인** (구분 의무):

| 원인 | 진단 | 해결 |
| -- | -- | -- |
| **A. 시점 race** — 호스트 모듈이 *나중* 로드 → 호출 시점에 메뉴 미등록 | `IsMenuRegistered(Path) == false` *최초* + 호스트 로드 후 `true` | `RegisterStartupCallback` 으로 지연 (§2.8) |
| **B. ToolMenus 외 시스템** — 호스트가 TabManager / FExtender 등 다른 시스템 사용 → ToolMenus 에 *영원히* 미등록 | `IsMenuRegistered(Path) == false` **항상** | ToolMenus 사용 불가 — 호스트별 다른 API 사용 (§2.9) |

⭐ **A vs B 구분** = `IsMenuRegistered` 결과를 **시간 다른 시점에 2회 측정** — A 면 시간 흐름 후 true, B 면 영원히 false.

```cpp
// ❌ 함정 — 시점 잘못 — ExtendMenu 가 stub 반환 후 SkeletalMeshEditor 모듈이 *나중* 로드
void FMyEditorModule::StartupModule()
{
    UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("AssetEditor.SkeletalMeshEditor.MainMenu.Window");
    Menu->FindOrAddSection("MyExt").AddMenuEntry(...);
    // ⚠ stub 에만 추가 — *원인 B* (ToolMenus 외 시스템) 라 영원히 표시 안 됨
}
```

**KMCProject 검증 사례 (2026-05-14)**:

`FMCHitBoneCurveEditorMenu::Register` 가 `RegisterStartupCallback` 으로 5개 후보 경로 시도 → 모두 `IsMenuRegistered=FALSE` 영구 → **원인 B 확정** (Asset Editor 의 Window 메뉴 = TabManager 자체 시스템).

```
LogMCAsset: ⚠ stub only Path 'AssetEditor.SkeletalMeshEditor.MainMenu.Window' (index 0) — IsMenuRegistered=FALSE
LogMCAsset: ⚠ stub only Path 'Persona.MainMenu.Window' (index 1) — IsMenuRegistered=FALSE
LogMCAsset: ⚠ stub only Path 'AssetEditor.AnimationEditor.MainMenu.Window' (index 2) — IsMenuRegistered=FALSE
LogMCAsset: ⚠ stub only Path 'AssetEditor.AnimationBlueprintEditor.MainMenu.Window' (index 3) — IsMenuRegistered=FALSE
LogMCAsset: ⚠ stub only Path 'AssetEditor.AnimationSequenceEditor.MainMenu.Window' (index 4) — IsMenuRegistered=FALSE
LogMCAsset: Menu extension complete — 5 / 5 paths registered.
```

→ Persona toolkit 의 Window 메뉴 = §2.9 (TabManager 자체 시스템) → ToolMenus 사용 불가. log: `[2026-05-14] fix | Cycle 5b — Persona Window 메뉴 = TabManager 자체 시스템 발견`.

### 2.8. ⭐ RegisterStartupCallback 의무 패턴 — 원인 A 회피 (2026-05-14 추가) 🟢

#### 2.8.1 배경

UE Module 로드 순서는 의존 그래프로 결정 — *정확한 순서 보장 없음*. ToolMenus 모듈이 다른 메뉴 호스트 모듈 (LevelEditor / MainFrame) 보다 *먼저* 로드되면 — 호스트 메뉴 이름이 ToolMenus 에 아직 등록 안 됨 (= 원인 A — 일시적).

#### 2.8.2 표준 패턴

```cpp
void FMyEditorModule::StartupModule()
{
    UToolMenus::RegisterStartupCallback(
        FSimpleMulticastDelegate::FDelegate::CreateStatic(&FMyEditorModule::RegisterMenuExtensions));
}

void FMyEditorModule::RegisterMenuExtensions()   // 콜백 진입점
{
    UToolMenus* ToolMenus = UToolMenus::Get();
    if (!ToolMenus) return;

    FToolMenuOwnerScoped OwnerScope(FName(TEXT("MyEditorModule")));   // 자동 owner 추적

    UToolMenu* Menu = ToolMenus->ExtendMenu("MainFrame.MainMenu.Window");   // ✅ ToolMenus 관리 메뉴
    // ... entry 추가 ...
}
```

#### 2.8.3 RegisterStartupCallback 동작 의미

- **이미 ToolMenus 초기화 완료** → 콜백 즉시 실행
- **ToolMenus 초기화 진행 중** → 초기화 완료 시점에 실행
- 콜백은 *한 번* 만 호출 — 이후 외부 모듈이 메뉴를 동적으로 추가/제거해도 콜백 재호출 X

→ 메뉴 호스트 모듈이 *콜백 시점 후* 로드되면, ExtendMenu 는 여전히 stub 반환 가능. 그러나 ToolMenus 가 등록된 메뉴는 호스트 모듈 로드 시점에 자동 결합 (등록 자체가 *deferred* — extension 은 메뉴 generate 시 매핑).

#### 2.8.4 결정 가이드

| 시점 | 사용 |
| -- | -- |
| `StartupModule` 직접 안 | ❌ — race 가능 (stub 반환) |
| `RegisterStartupCallback` 안 | ⭐⭐⭐ 표준 — 권장 (메인 윈도우 / LevelEditor / ContentBrowser 메뉴) |
| `OnPostEngineInit` delegate 안 | ⭐⭐ — 더 늦은 시점 (Engine 초기화 완료) — 거의 항상 안전 |
| Tab 첫 spawn 시 | ⭐ — 가장 늦음 — Tab spawn 의무 |
| **Asset Editor 내부 Window 메뉴** | ❌ ToolMenus 사용 불가 — §2.9 (호스트별 OnRegisterTabs delegate) |

#### 2.8.5 함정 / 안티패턴

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | `StartupModule` 직접 `ExtendMenu` 호출 (메인 윈도우 메뉴) | `RegisterStartupCallback` 으로 감싸기 |
| 2 | 콜백 안 `UToolMenus::Get() == nullptr` 검사 누락 | 의무 — RegisterStartupCallback 시점에도 null 가능 (드뭄) |
| 3 | 콜백 안 `FToolMenuOwnerScoped` 미사용 | 자동 owner 추적 누락 → `UnregisterOwner` 누락 시 dangling |
| 4 | 같은 owner 안 같은 entry 이름 중복 등록 | `MC_OpenEditor_%d` index 부착 또는 다른 owner 사용 |
| 5 | 콜백 안 람다 캡처에 모듈 멤버 직접 참조 | static 함수로 분리 — 모듈 unload 시 dangling 방어 |
| 6 ⭐⭐⭐ | **Asset Editor 내부 Window 메뉴를 ToolMenus 로 시도** — `RegisterStartupCallback` 으로도 stub | §2.9 — `FPersonaModule::OnRegisterTabs` 등 호스트별 delegate 사용 |

### 2.9. ⭐⭐⭐ AssetEditor Window 메뉴 = TabManager 자체 시스템 — ToolMenus 외 (2026-05-14 추가) 🟢

#### 2.9.1 핵심 발견

`FAssetEditorToolkit::InitAssetEditor` (`Engine/Source/Editor/UnrealEd/Private/Toolkits/AssetEditorToolkit.cpp` L222) 가 각 Editor 에 **자체 TabManager** 생성:

```cpp
const TSharedRef<FTabManager> NewTabManager = FGlobalTabmanager::Get()->NewTabManager(NewMajorTab.ToSharedRef());
NewTabManager->SetOnPersistLayout(...);
NewTabManager->SetAllowWindowMenuBar(true);   // ⭐ Window 메뉴 활성화 — TabManager 자체 시스템
this->TabManager = NewTabManager;
```

`SetAllowWindowMenuBar(true)` → 해당 Editor 의 메인 SWindow 가 **자체 Window 메뉴** 가짐. 이 메뉴는 **TabManager 의 LocalWorkspace 카테고리** 시스템 — ToolMenus 와 별도 시스템.

#### 2.9.2 등록 표준 — RegisterTabSpawner (TabManager 측)

```cpp
// FAssetEditorToolkit::RegisterTabSpawners (L342)
void FAssetEditorToolkit::RegisterTabSpawners(const TSharedRef<FTabManager>& InTabManager)
{
    const auto& LocalCategories = InTabManager->GetLocalWorkspaceMenuRoot()->GetChildItems();
    AssetEditorTabsCategory = LocalCategories.Num() > 0 ? LocalCategories[0] : InTabManager->GetLocalWorkspaceMenuRoot();
    // 자손 toolkit 이 InTabManager->RegisterTabSpawner("MyTab", ...)
    //   .SetGroup(AssetEditorTabsCategory) 형태로 등록 → Window 메뉴에 자동 표시
}
```

#### 2.9.3 ⭐ Persona / SkeletalMeshEditor / Animation* — `FPersonaModule::OnRegisterTabs` delegate

Persona toolkit 의 Window 메뉴에 항목 추가하는 *진짜 표준* — 외부 모듈에서:

```cpp
// PersonaModule.h L70 + L550
DECLARE_MULTICAST_DELEGATE_TwoParams(FOnRegisterTabs, FWorkflowAllowedTabSet&, TSharedPtr<FAssetEditorToolkit>);

class FPersonaModule
{
    virtual FOnRegisterTabs& OnRegisterTabs() { return OnRegisterTabsDelegate; }
};
```

**5개 Persona 모드에서 호출** (검증):

| 모드 파일 | 라인 | 호출 |
| -- | -- | -- |
| `SkeletalMeshEditorMode.cpp` | L120 | `PersonaModule.OnRegisterTabs().Broadcast(TabFactories, InHostingApp);` |
| `SkeletonEditorMode.cpp` | L111 | 동일 |
| `AnimationEditorMode.cpp` | L125 | 동일 |
| `AnimationBlueprintEditorMode.cpp` | L203 | 동일 |
| `AnimationBlueprintInterfaceEditorMode.cpp` | L93 | 동일 |

→ **delegate 1회 등록 = 5개 Persona toolkit 모두 Window 메뉴 자동 표시**.

#### 2.9.4 적용 패턴

```cpp
// MyEditorModule::StartupModule
FPersonaModule& PersonaModule = FModuleManager::LoadModuleChecked<FPersonaModule>("Persona");
OnRegisterTabsHandle = PersonaModule.OnRegisterTabs().AddStatic(&FMyMenu::OnRegisterTabs);

// 콜백 — Persona toolkit 마다 호출
void FMyMenu::OnRegisterTabs(FWorkflowAllowedTabSet& TabFactories, TSharedPtr<FAssetEditorToolkit> Toolkit)
{
    TabFactories.RegisterFactory(MakeShared<FMyTabFactory>(Toolkit));
    // FWorkflowTabFactory 자손 작성 의무 — CreateTabBody / GetTabIcon / GetTabLabel
}

// MyEditorModule::ShutdownModule
if (FModuleManager::Get().IsModuleLoaded("Persona"))
{
    FPersonaModule& PersonaModule = FModuleManager::GetModuleChecked<FPersonaModule>("Persona");
    PersonaModule.OnRegisterTabs().Remove(OnRegisterTabsHandle);
}
```

#### 2.9.5 다른 호스트 — LevelEditor / WorldPartition

같은 패턴 — 모듈마다 `OnRegisterTabs` delegate 노출:

| 모듈 | delegate | 호출 시점 | 사용 사례 |
| -- | -- | -- | -- |
| `FPersonaModule::OnRegisterTabs()` | Persona 5 모드 spawn | (위) | 모든 Persona toolkit Window 메뉴 |
| `FLevelEditorModule::OnRegisterTabs()` | Level Editor TabManager 생성 | `SLevelEditor.cpp` L1600 | LevelEditor Window 메뉴 (`WorldPartitionEditor` / `WorldBookmark` 등 사용) |
| `FBlueprintEditorModule::OnRegisterTabs()` (추정) | Blueprint Editor spawn | 🔴 INFERRED | Blueprint Editor Window 메뉴 |

#### 2.9.6 Window 메뉴 시스템 매트릭스 (3 호스트 카테고리)

| 호스트 | Window 메뉴 시스템 | 등록 API |
| -- | -- | -- |
| **메인 윈도우 / LevelEditor** | ToolMenus (`MainFrame.MainMenu.Window` / `LevelEditor.MainMenu.Window`) | `UToolMenus::Get()->ExtendMenu(...)` + `RegisterStartupCallback` |
| **AssetEditor (Persona / SkeletalMeshEditor / 등)** | ⭐ TabManager 자체 + `OnRegisterTabs` delegate | `FPersonaModule::OnRegisterTabs().AddStatic(...)` + FWorkflowTabFactory |
| **Standalone Nomad Tab (글로벌)** | GlobalTabmanager Window 메뉴 | `FGlobalTabmanager::Get()->RegisterNomadTabSpawner(...).SetMenuType(ETabSpawnerMenuType::Default)` |

#### 2.9.7 결정 가이드

```
사용자에게 메뉴 항목 노출 위치?
  ├── 메인 윈도우 (Level Editor 호스트) Window/File/Tools/Asset 메뉴
  │     → ToolMenus + RegisterStartupCallback (§2.6)
  ├── 특정 Asset Editor (Persona / SkeletalMeshEditor / Animation*) Window 메뉴
  │     → FPersonaModule::OnRegisterTabs + FWorkflowTabFactory (§2.9.3)
  ├── 모든 Editor 의 Window 메뉴 (글로벌)
  │     → FGlobalTabmanager::RegisterNomadTabSpawner + ETabSpawnerMenuType::Default
  └── ContentBrowser asset 우클릭 메뉴
        → ToolMenus `ContentBrowser.AssetContextMenu.<AssetType>`
```

#### 2.9.8 KMCProject 검증 사례 — 5 후보 stub 의 정확한 원인 진단

```cpp
// MCHitBoneCurveEditorMenu.cpp 시도:
ToolMenus->ExtendMenu("AssetEditor.SkeletalMeshEditor.MainMenu.Window");   // ❌ stub
ToolMenus->ExtendMenu("Persona.MainMenu.Window");                          // ❌ stub
ToolMenus->ExtendMenu("AssetEditor.AnimationEditor.MainMenu.Window");      // ❌ stub
ToolMenus->ExtendMenu("AssetEditor.AnimationBlueprintEditor.MainMenu.Window");   // ❌ stub
ToolMenus->ExtendMenu("AssetEditor.AnimationSequenceEditor.MainMenu.Window");    // ❌ stub
// 모두 IsMenuRegistered=FALSE 영구 → 원인 B (ToolMenus 외 시스템) 확정
// 진짜 fix = FPersonaModule::OnRegisterTabs delegate 사용 (§2.9.3)
```

→ **5개 후보 모두 stub** = ToolMenus 가 *AssetEditor 내부 Window 메뉴를 관리하지 않는다는 결정적 증거*. log: `[2026-05-14] fix | Cycle 5b — Persona Window 메뉴 = TabManager 자체 시스템 발견`.

### 2.10. 후속 enrichment 후보 (2026-05-14)

| # | 후보 | 트리거 |
| -- | -- | -- |
| 1 | `AssetEditor.<X>.ToolBar` ToolMenus 등록 검증 | SkeletalMeshEditor::ExtendToolbar 의 GetToolMenuToolbarName 검증 — Toolbar 는 ToolMenus 인지? |
| 2 | `FBlueprintEditorModule::OnRegisterTabs` delegate 검증 (🔴 INFERRED) | Blueprint Editor Window 메뉴 추가 시 |
| 3 | `FCustomizedToolMenu` vs `FToolMenuProfile` 사용자 토글 | Cycle 5d 후보 |
| 4 | `UToolMenuContextBase` 자손 작성 패턴 | Cycle 6 |

## 3. Cross-link

- 카테고리 main: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 자매 sub-skill: [[sources/ue-editor-mainframe]] (메인 윈도우 후크) · [[sources/ue-editor-leveleditor]] (레벨 에디터 메뉴 진입)
- Legacy 페어: [[sources/ue-slate-menu]] / [[sources/ue-slate-commands]] (FMenuBuilder / FUICommandList 베이스)
- 횡단 정책: [[sources/ue-ref-05-editoronlyindex]]
- ⭐⭐⭐ **Persona Window 메뉴 표준**: [[sources/ue-editor-personatoolkit]] §2.6 (FPersonaModule::OnRegisterTabs delegate 패턴)
- AssetEditor TabManager 시스템: [[sources/ue-editor-asseteditorapi]] §3.x (Window 메뉴 = TabManager 자체)

### KMCProject 검증 사례

- `[2026-05-13] fix | Persona Window 메뉴 항목 미표시 fix — 다중 경로 fallback + RegisterStartupCallback 지연 호출` — §2.7 / §2.8 1차 시도 (불완전 fix — 원인 A 가정)
- ⭐⭐⭐ `[2026-05-14] fix | Cycle 5b — Persona Window 메뉴 = TabManager 자체 시스템 발견` — §2.9 정확한 진단 (원인 B — ToolMenus 외 시스템) + FPersonaModule::OnRegisterTabs 표준 발견

## 4. Open questions

- [ ] `ToolMenusEditor` 모듈 (Editor 안) vs `ToolMenus` (Developer) — 사용 결정 시점
- [ ] BP `UToolMenuEntryScript` 의 라이프사이클 — Plugin 비활성화 시 자동 cleanup?
- [ ] `FCustomizedToolMenu` 사용자 토글 — 저장 위치 (DefaultEditorPerProjectUserSettings.ini?)
- [ ] 5.x `FToolMenuProfile` — 프로파일 정의 + 가시성 적용 시점
- [ ] §2.4 `AssetEditor.<X>.ToolBar` — Toolbar 도 ToolMenus 인지 검증 (SkeletalMeshEditor::ExtendToolbar)
- [ ] §2.9.5 다른 호스트의 OnRegisterTabs delegate (Blueprint Editor / Material Editor / Niagara Editor 등) (🔴 INFERRED)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에만): 0
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `> **위치 주의**: UE 5.7 에서 `Engine/Source/Developer/ToolMenus/` (Developer). Editor  → > **위치 주의**: UE 5.5 에서 `Engine/Source/Developer/ToolMenus/` (Developer). Editor `

**5.5.4 에만 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Editor/references/ToolMenus.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Editor/references/ToolMenus.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
