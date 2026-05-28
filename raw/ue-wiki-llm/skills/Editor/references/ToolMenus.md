---
name: toolmenus-main
description: 🛠 ToolMenus 모듈 (5.x 모던) - UToolMenus + UToolMenu + FToolMenuEntry + FToolMenuContext - FMenuBuilder 의 후속.
---

# ToolMenus Module 🛠

> **모듈**: `Engine/Source/Developer/ToolMenus/` (Developer — 에디터 빌드 의존)
> **사이즈**: Public 14 헤더
> **빌드 의존**: `Core` · `CoreUObject` · `ApplicationCore` · `Slate` · `SlateCore` · `InputCore` (모두 Private)
> **카테고리**: `[Slate]` 인하우스 툴 (🛠 에디터 전용)

---

## 1. 개요

UE 5.x 의 **모던 메뉴 시스템**. 기존 `FMenuBuilder` / `FToolBarBuilder` ([`Slate/Menu`](../Slate/references/Menu.md)) 가 *명령형*(빌더에 한 번에 다 채워서 SWidget 만들기) 방식이라면, ToolMenus는 *선언형*: **이름 기반 메뉴 등록 → 외부 모듈이 같은 이름으로 확장 → 호출 시 모든 등록된 항목 합쳐서 위젯 생성**.

**FMenuBuilder vs ToolMenus**:

| 측면 | FMenuBuilder (4.x~) | UToolMenus (5.x 권장) |
|------|---------------------|----------------------|
| 패러다임 | 명령형 빌더 | 선언형 등록·확장 |
| 확장 방식 | `FExtender` 패스 + `IExtensibilityManager` | 같은 메뉴 이름에 `ExtendMenu` |
| BP/Python 노출 | X | ✅ `UFUNCTION(BlueprintCallable)` |
| 컨텍스트 객체 | (사용자 정의) | `FToolMenuContext` + `UToolMenuContextBase` |
| 사용자 정의(Customization) | X | ✅ `FCustomizedToolMenu` (사용자가 항목 토글) |
| Profile 시스템 | X | ✅ `FToolMenuProfile` (프로파일 별 가시성) |
| 권장 시점 | 레거시 | **신규 코드** |

> 신규 인하우스 툴은 **ToolMenus** 사용 권장. 기존 코드(`FAssetEditorToolkit`의 InitToolMenuContext 등) 는 ToolMenus와 FExtender 혼용 가능.

---

## 2. 핵심 헤더

| 헤더 | 클래스/구조 | 의미 |
|------|------------|------|
| `ToolMenus.h` | `UToolMenus` (UCLASS L100) | 글로벌 매니저 (싱글턴) |
| `ToolMenu.h` | `UToolMenu : UToolMenuBase` (L24) | 메뉴 1개 — 섹션·엔트리 보유 |
| `ToolMenuEntry.h` | `FToolMenuEntry` (struct L165) | 메뉴 항목 1개 |
| `ToolMenuSection.h` | `FToolMenuSection` (struct) | 섹션 (구분선 포함) |
| `ToolMenuContext.h` | `FToolMenuContext` + `UToolMenuContextBase` | 동적 컨텍스트 (편집 객체 등) |
| `ToolMenuOwner.h` | `FToolMenuOwner` | 등록 주체 (Plugin/Module/UObject) |
| `ToolMenuDelegates.h` | `FNewToolMenuDelegate` 등 | 동적 섹션·엔트리 델리게이트 |
| `ToolMenuMisc.h` | 기타 헬퍼 | |
| `ToolMenuIteration.h` | 반복 헬퍼 | |
| `ToolMenuEntryScript.h` | `UToolMenuEntryScript` | BP/Python 으로 항목 생성 |
| `ToolMenuWidgetCollectionContext.h` | `UToolMenuWidgetCollectionContext` | 위젯 컬렉션 컨텍스트 |
| `IToolMenusModule.h` | 모듈 인터페이스 | StartupModule/ShutdownModule |
| `ToolMenusLog.h` | 로그 카테고리 | `LogToolMenus` |

> **위치 주의**: UE 5.7 에서 `Engine/Source/Developer/ToolMenus/` (Developer). Editor 빌드에서 자동 활성화. 별개로 `ToolMenusEditor` 모듈 (Editor에 있음 — UnrealEd가 의존) 도 존재 — 추가 에디터 통합.

---

## 3. UToolMenus (글로벌 매니저)

### 3.1 핵심 API (ToolMenus.h)

| API | 라인 | 의미 |
|-----|------|------|
| `static UToolMenus* Get()` | (헤더) | 싱글턴 접근 — 가장 자주 호출 |
| `UToolMenu* RegisterMenu(FName Name, FName Parent=NAME_None, EMultiBoxType Type=Menu, bool bWarnIfAlreadyRegistered=true)` | L161 | 메뉴 등록 (없으면 생성, 있으면 가져옴) |
| `UToolMenu* ExtendMenu(FName Name)` | L169 | 기존 메뉴 확장 (같은 이름) — 외부 모듈에서 사용 |
| `UToolMenu* FindMenu(FName Name)` | L185 | 검색만 |
| `void RemoveMenu(FName MenuName)` | L239 | 메뉴 자체 제거 |
| `static bool AddMenuEntryObject(UToolMenuEntryScript*)` | L205 | BP/Python 항목 추가 |
| `static bool RemoveMenuEntryObject(UToolMenuEntryScript*)` | L209 | 제거 |
| `FCustomizedToolMenu* FindMenuCustomization(FName Name)` | L304 | 사용자 커스터마이징 |
| `FToolMenuProfile* FindMenuProfile(FName MenuName, FName ProfileName)` | L319 | 프로파일 별 가시성 |
| `TSharedRef<SWidget> GenerateWidget(FName MenuName, const FToolMenuContext& Context)` | (헤더) | 메뉴 → SWidget 생성 |

### 3.2 표준 메뉴 이름 규약

UE 에디터의 표준 메뉴 이름 — 외부 모듈이 `ExtendMenu` 시 사용:

| 메뉴 이름 | 위치 |
|-----------|------|
| `MainFrame.MainMenu.File` | 메인 윈도우 — File 메뉴 |
| `MainFrame.MainMenu.Edit` | Edit 메뉴 |
| `MainFrame.MainMenu.Window` | Window 메뉴 |
| `MainFrame.MainMenu.Tools` | Tools 메뉴 |
| `MainFrame.MainMenu.Help` | Help 메뉴 |
| `LevelEditor.LevelEditorToolBar` | 레벨 에디터 툴바 |
| `LevelEditor.MainMenu` | 레벨 에디터 메뉴 |
| `ContentBrowser.AssetContextMenu` | 에셋 컨텍스트 메뉴 (모든 에셋) |
| `ContentBrowser.AssetContextMenu.<AssetType>` | 특정 에셋 타입 |
| `AssetEditor.<EditorName>.MainMenu` | 인하우스 에디터의 메뉴 |
| `AssetEditor.<EditorName>.ToolBar` | 인하우스 에디터의 툴바 |

---

## 4. UToolMenu (메뉴 1개)

### 4.1 BP 노출 API (ToolMenu.h)

| 메서드 | UFUNCTION | 의미 |
|--------|-----------|------|
| `AddMenuEntry(FName SectionName, FToolMenuEntry Entry)` | L32 | 항목 추가 |
| `AddSection(FName Name, FText Label=GetEmpty, FToolMenuInsert InsertPosition=Default)` | L35 | 섹션 추가 |
| `AddDynamicSection(FName SectionName, FNewToolMenuDelegate Delegate, FToolMenuInsert InsertPosition=Default)` | L44 | 동적 섹션 — 호출 시점에 생성 |
| `AddSubMenu(FToolMenuOwner Owner, FName SectionName, FName Name, FText Label, FText ToolTip, FNewToolMenuDelegate ConstructUnderObject)` | L56 | 서브메뉴 |
| `RemoveSection(FName)` / `RemoveEntry(FName Section, FName Entry)` | L47 / L50 | 제거 |
| `FindSection(FName)` | L53 | 섹션 찾기 |

### 4.2 virtual 함수 (UToolMenuBase override)

| 시그니처 | 라인 | 의미 |
|----------|------|------|
| `virtual bool IsEditing() const override` | L130 | 편집 모드인지 |
| `virtual FName GetSectionName(FName InEntryName) const override` | L131 | 엔트리의 섹션 이름 |
| `virtual bool ContainsSection(FName InName) const override` | L132 | 섹션 존재? |
| `virtual bool ContainsEntry(FName InName) const override` | L133 | 엔트리 존재? |
| `virtual FCustomizedToolMenu* FindMenuCustomization() const override` | L134 | 사용자 커스터마이징 |
| `virtual void OnMenuDestroyed() override` | L141 | 소멸 |

---

## 5. FToolMenuEntry (항목 1개)

### 5.1 구조 (ToolMenuEntry.h L165)

```cpp
struct FToolMenuEntry
{
    FToolMenuEntry(const FToolMenuOwner InOwner, const FName InName, EMultiBlockType InType);
    
    FToolMenuOwner Owner;       // 등록 주체
    FName Name;                  // 항목 이름 (고유)
    EMultiBlockType Type;        // MenuEntry / ToolBarButton / Separator / Heading / Widget 등
    // ... Label / ToolTip / Icon / FUIAction / FUICommandInfo
    // ... SubMenuData / ToolBarData / WidgetData / OptionsDropdownData
    FToolMenuVisibilityChoice VisibilityChoice;
    // ... Style / FToolMenuEntryStyle
};
```

### 5.2 헬퍼 (정적 생성자)

| 함수 | 의미 |
|------|------|
| `FToolMenuEntry::InitMenuEntry(FName Name, FText Label, FText ToolTip, FSlateIcon Icon, FUIAction Action, EUserInterfaceActionType=Button)` | 일반 메뉴 항목 |
| `FToolMenuEntry::InitMenuEntryWithCommandList(FName Name, TSharedPtr<FUICommandList> CommandList, TSharedPtr<FUICommandInfo> CommandInfo)` | TCommands<T> 와 연결 |
| `FToolMenuEntry::InitToolBarButton(FName Name, FUIAction Action, FText Label, FText ToolTip, FSlateIcon Icon, EUserInterfaceActionType=Button)` | 툴바 버튼 |
| `FToolMenuEntry::InitSubMenu(FName Name, FText Label, FText ToolTip, FNewToolMenuDelegate ConstructUnderObject, bool bInOpenSubMenuOnClick=false, FSlateIcon=FSlateIcon())` | 서브 메뉴 |
| `FToolMenuEntry::InitSeparator(FName Name)` | 구분선 |
| `FToolMenuEntry::InitWidget(FName Name, TSharedRef<SWidget> Widget, FText Label, bool bNoIndent=false, bool bSearchable=true)` | 임의 위젯 삽입 |

---

## 6. FToolMenuContext (컨텍스트)

```cpp
FToolMenuContext Context;
Context.AddObject(MyAsset);            // UObject 추가 — 콜백에서 GetContext<T>() 로 접근
Context.AppendCommandList(CommandList); // 단축키 셋

// 메뉴 위젯 생성
TSharedRef<SWidget> Menu = UToolMenus::Get()->GenerateWidget("MyEditor.MainMenu", Context);
```

콜백 안에서:

```cpp
void HandleEntry(UToolMenu* InMenu)
{
    if (UMyContext* Ctx = InMenu->FindContext<UMyContext>())
    {
        // Ctx->Asset 등 접근
    }
}
```

---

## 7. 작성 패턴

### 7.1 메뉴 등록 (StartupModule)

```cpp
#if WITH_EDITOR
void FMyEditorModule::StartupModule()
{
    if (UToolMenus::IsToolMenuUIEnabled())
    {
        UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FMyEditorModule::RegisterMenus));
    }
    else
    {
        // 폴백: 직접 등록
        RegisterMenus();
    }
    OwnerScoped = MakeUnique<FToolMenuOwnerScoped>(this);
}

void FMyEditorModule::RegisterMenus()
{
    FToolMenuOwnerScoped OwnerScoped(this);    // RAII — Shutdown 시 자동 제거

    UToolMenu* MainMenu = UToolMenus::Get()->ExtendMenu("MainFrame.MainMenu.Tools");
    FToolMenuSection& Section = MainMenu->FindOrAddSection("MyTools");
    
    Section.AddMenuEntry(
        "OpenMyEditor",
        LOCTEXT("OpenMyEditor", "Open My Editor"),
        LOCTEXT("OpenMyEditorTip", "Opens the custom editor"),
        FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Launch"),
        FUIAction(FExecuteAction::CreateRaw(this, &FMyEditorModule::OpenMyEditor)));
}

void FMyEditorModule::ShutdownModule()
{
    UToolMenus::UnRegisterStartupCallback(this);
    UToolMenus::UnregisterOwner(this);    // 이 모듈이 추가한 모든 항목 자동 제거
}
#endif
```

### 7.2 컨텍스트 메뉴 (에셋 우클릭)

```cpp
UToolMenu* AssetMenu = UToolMenus::Get()->ExtendMenu("ContentBrowser.AssetContextMenu.MyAsset");
FToolMenuSection& Section = AssetMenu->FindOrAddSection("MyAssetActions");

Section.AddDynamicEntry("ProcessAsset", FNewToolMenuSectionDelegate::CreateLambda(
    [](FToolMenuSection& InSection)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyAssetMenu_DynamicEntry);   // ← 람다 스코프 의무

        UContentBrowserAssetContextMenuContext* Context = InSection.FindContext<UContentBrowserAssetContextMenuContext>();
        if (!Context || Context->SelectedAssets.IsEmpty()) return;

        InSection.AddMenuEntry(
            "ProcessAsset",
            LOCTEXT("ProcessAsset", "Process Asset"),
            LOCTEXT("ProcessAssetTip", "Process selected assets"),
            FSlateIcon(),
            FUIAction(FExecuteAction::CreateLambda([SelectedAssets = Context->SelectedAssets]()
            {
                TRACE_CPUPROFILER_EVENT_SCOPE(MyAssetMenu_Execute);
                for (const FAssetData& Data : SelectedAssets) { /* ... */ }
            })));
    }));
```

### 7.3 툴바 등록 (인하우스 에디터)

```cpp
// FAssetEditorToolkit 자손에서
virtual FName GetToolMenuToolbarName(FName& OutParentName) const override
{
    OutParentName = "AssetEditor.DefaultToolBar";
    return "AssetEditor.MyEditor.ToolBar";    // 자손 툴바 이름
}

virtual void InitToolMenuContext(FToolMenuContext& MenuContext) override
{
    FAssetEditorToolkit::InitToolMenuContext(MenuContext);    // ← Super FIRST
    MenuContext.AddObject(EditingAsset.Get());
}
```

---

## 8. UToolMenuEntryScript (BP/Python)

```cpp
UCLASS(Blueprintable)
class UMyMenuScript : public UToolMenuEntryScript
{
    GENERATED_BODY()
public:
    UMyMenuScript()
    {
        Data.Menu = "MainFrame.MainMenu.Tools";
        Data.Section = "MyTools";
        Data.Name = "MyScriptedEntry";
        Data.Label = NSLOCTEXT("MyEditor", "ScriptedEntry", "Scripted Entry");
    }

    virtual void Execute(const FToolMenuContext& Context) override
    {
        // BP에서 override 가능
    }
};
```

`UToolMenus::AddMenuEntryObject(NewObject<UMyMenuScript>())` 로 등록.

---

## 9. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `UToolMenuEntryScript::Execute(const FToolMenuContext&)` | (override 시 자체 처리) | 항목 클릭 |
| `UToolMenu::OnMenuDestroyed()` | **FIRST** | 소멸 정리 |
| `IModuleInterface::StartupModule` | (override 시 RegisterMenus 호출) | RegisterStartupCallback 사용 권장 |

---

## 10. 함정

| 함정 | 회피 |
|------|------|
| `RegisterMenu` 결과 사용 후 캐싱 | UToolMenu* 는 매번 `FindMenu`/`ExtendMenu` 호출 권장 |
| 모듈 Shutdown 시 등록 항목 안 정리 | `FToolMenuOwnerScoped` RAII + `UToolMenus::UnregisterOwner(this)` |
| `RegisterMenu` 가 nullptr 반환 — `UToolMenus::IsToolMenuUIEnabled` false | `RegisterStartupCallback` 사용해 활성화 후 등록 |
| 같은 메뉴 이름에 다른 모듈이 동시 등록 | 이름 충돌 — 모듈명 prefix (`MyPlugin.MainMenu.Tools`) |
| `FToolMenuContext` 에 객체 추가 안 함 | 콜백에서 GetContext 실패 |
| `FNewToolMenuDelegate` 람다에 강한 캡처 | `CreateWeakLambda` 또는 weak ptr |
| 동적 섹션 람다에 스코프 누락 | [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| FMenuBuilder 와 ToolMenus 동시 사용 시 순서 혼란 | UE 5.x는 ToolMenus 우선 — FMenuBuilder는 레거시 호환 |
| BP에서 `UToolMenuEntryScript::Execute` 호출 시점 | 항목 클릭 후 — 빈도 낮으나 무거우면 스코프 부착 |

---

## 11. 에디터 전용 표기 🛠

본 모듈 자체는 **Developer** 모듈이지만 **에디터 빌드에서만 사용** (Slate UI가 활성화된 환경). 게임 런타임 빌드에서는 비활성. 모든 사용 코드는 `#if WITH_EDITOR` + Build.cs `Type=Editor` (4단 분리 — [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md)).

---

## 12. 관련 sub-skill

- [`Slate/Menu`](../Slate/references/Menu.md) — 레거시 FMenuBuilder/FToolBarBuilder/FExtender (4.x)
- [`Slate/Commands`](../Slate/references/Commands.md) — TCommands<T> / FUICommandList — ToolMenus와 통합 (`InitMenuEntryWithCommandList`)
- [`Slate/EditorApplication`](../Slate/references/EditorApplication.md) — FSlateApplication
- [`Slate/Docking`](../Slate/references/Docking.md) — SDockTab과 통합 (탭 메뉴)
- [`UnrealEd/AssetEditorToolkit`](../UnrealEd/AssetEditorToolkit/SKILL.md) — `InitToolMenuContext` / `GetToolMenuToolbarName`
- [`UnrealEd/Subsystems`](../UnrealEd/Subsystems/SKILL.md) — UEditorSubsystem 안에서 메뉴 등록
- 교차: [`04_OverrideIndex.md`](../../references/04_OverrideIndex.md) · [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) (동적 섹션·엔트리 콜백 람다 스코프 의무)
