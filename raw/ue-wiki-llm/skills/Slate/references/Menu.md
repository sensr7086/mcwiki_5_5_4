---
name: slate-menu
description: 🛠 FMenuBuilder + FExtensibilityManager + FExtender + 메뉴 구성 (5.x ToolMenus 와 비교).
---

# Slate / Menu 🛠

> 부모 모듈: [`Slate`](../SKILL.md) · UE 5.7.4
> 다루는 영역: 메뉴/툴바 빌더 — `FMenuBuilder` · `FMenuBarBuilder` · `FToolBarBuilder` (수직/슬림/유니폼 변형) · `FExtender`/`EExtensionHook` · `FMultiBox`/`FMultiBlock` · `ToolMenuBase` · `SMenuAnchor`/`SExpandableButton`/`SPopup` · `SToolBar*Block` 위젯 + 메인 메뉴/탭 컨텍스트 메뉴 통합 패턴
> 🛠 사실상 에디터/인하우스 툴 빌드 한정 — 게임 UI에서는 직접 SButton/SVerticalBox 조합 권장.
> 관련 sub-skill: [`Commands/`](../Commands/SKILL.md), [`Docking/`](../Docking/SKILL.md), [`EditorApplication/`](../EditorApplication/SKILL.md), [`CommonWidgets/`](../CommonWidgets/SKILL.md)

---

## 1. 개요

인하우스 툴의 메뉴/툴바는 **선언형 Builder 패턴**으로 만든다. `SVerticalBox + SButton` 으로 직접 조립하지 않고, `FMenuBuilder` 같은 전용 빌더에 항목을 쌓은 뒤 마지막에 `MakeWidget()` 으로 위젯을 얻는 방식.

```
명령(FUICommandInfo) ──┐
                       ├─> FMenuBuilder / FToolBarBuilder
사용자 액션(FUIAction) ─┘    .AddMenuEntry / .AddToolBarButton / .BeginSection / .AddSubMenu
                                .MakeWidget() -> TSharedRef<SWidget>

확장(FExtender) → 다른 모듈의 메뉴/툴바 사이에 끼어들기
                  EExtensionHook::Before/After/First
```

**왜 빌더인가** — 메뉴는 (1) 컨텍스트 메뉴 / 메인 메뉴 / 탭 컨텍스트 등 여러 위치에서 같은 항목을 재사용해야 하고 (2) 다른 모듈이 끼어들 수 있어야 하며 (3) 단축키와 자동으로 연결돼야 하기 때문. 이걸 SButton 직접 조립으로 만들면 매번 중복.

---

## 2. 핵심 헤더와 클래스

### 2.1 빌더 사슬 (`Public/Framework/MultiBox/MultiBoxBuilder.h`)

| 클래스 | 위치 | 용도 |
|--------|------|------|
| `class FMultiBoxBuilder` (L33) | 추상 베이스 | 모든 빌더의 베이스. `MakeWidget()` 반환. |
| `class FBaseMenuBuilder : FMultiBoxBuilder` (L240) | 메뉴 공통 | `FMenuBuilder`/`FMenuBarBuilder` 공통 로직. |
| `class FMenuBuilder : FBaseMenuBuilder` (L309) | **드롭다운/컨텍스트 메뉴** | 가장 자주 사용. 컨텍스트 메뉴·우클릭 팝업·메인 메뉴 항목. |
| `class FMenuBarBuilder : FBaseMenuBuilder` (L494) | 메뉴 바 | 윈도우 상단 메뉴 바 (File / Edit / View ...). |
| `class FToolBarBuilder : FMultiBoxBuilder` (L539) | **툴바** | 가로 툴바. |
| `class FVerticalToolBarBuilder : FToolBarBuilder` (L826) | 세로 툴바 | 좌측 사이드바형. |
| `class FUniformToolBarBuilder : FToolBarBuilder` (L841) | 균등 툴바 | 모든 버튼 같은 너비. |
| `class FSlimHorizontalToolBarBuilder : FToolBarBuilder` (L855) | 5.x 슬림 가로 | 에디터 5.x 신표준 (얇은 헤더형). |
| `class FSlimHorizontalUniformToolBarBuilder : FToolBarBuilder` (L912) | 슬림 + 균등 | |
| `class FButtonRowBuilder : FMultiBoxBuilder` (L872) | 버튼 행 | 단순 버튼 묶음. |

`DECLARE_DELEGATE_OneParam(FNewMenuDelegate, class FMenuBuilder&)` (L27) — 서브메뉴 콜백 시그니처.

### 2.2 MultiBox 본체 (`Public/Framework/MultiBox/MultiBox.h`)

| 심볼 | 위치 | 역할 |
|------|------|------|
| `class FMultiBlock` (L57) | 메뉴/툴바의 단일 항목 (한 메뉴 entry, 한 툴바 버튼) |
| `class FMultiBox` (L330) | MultiBlock의 컬렉션 — 빌더가 채워서 위젯으로 변환 |
| `class IMultiBlockBaseWidget` (L536) | MultiBlock → 위젯 인터페이스 |
| `class SMultiBlockBaseWidget` (L615) | 표준 구현 |
| `class SMultiBoxWidget` (L659) | MultiBox 전체 표시 위젯 |

일반 코드는 직접 만지지 않음 — 빌더가 자동 생성.

### 2.3 enum / 타입 (`Public/Framework/MultiBox/MultiBoxDefs.h`)

| 심볼 | 위치 | 값 |
|------|------|----|
| `enum class EMultiBoxType : uint8` (L41) | MenuBar / Menu / ToolBar / VerticalToolBar / SlimHorizontalToolBar / UniformToolBar / ButtonRow / SlimHorizontalUniformToolBar 등 |
| `enum class EMultiBlockType : uint8` (L76) | MenuEntry / EditableText / Heading / MenuSeparator / ToolBarButton / ToolBarComboButton / ToolBarSeparator / Widget / ToolBarStackButton / Spacer 등 |
| `class FMultiBoxSettings` (L90) | 전역 설정 (라벨 표시·크기 등) |
| `enum class EUserInterfaceActionType : uint8` (`Commands/UICommandInfo.h:19`) | Button / ToggleButton / RadioButton / Check / CollapsedButton — 항목 동작 타입 |

`enum EMenuPlacement : int` (`SlateCore/Types/SlateEnums.h:213`) — 팝업 메뉴 위치 정책 (MenuPlacement_BelowAnchor 등).

### 2.4 Extender (`Public/Framework/MultiBox/MultiBoxExtender.h`)

| 심볼 | 역할 |
|------|------|
| `class FExtender` (L42) | 메뉴 바 / 메뉴 / 툴바를 외부에서 확장 |
| `namespace EExtensionHook { enum Position { Before, After, First } }` (L24~) | 확장 위치 — 기준 hook 앞/뒤/섹션 시작 |
| `DECLARE_DELEGATE_OneParam(FMenuExtensionDelegate,    FMenuBuilder&)` | 메뉴 확장 콜백 |
| `DECLARE_DELEGATE_OneParam(FMenuBarExtensionDelegate, FMenuBarBuilder&)` | 메뉴 바 확장 콜백 |
| `DECLARE_DELEGATE_OneParam(FToolBarExtensionDelegate, FToolBarBuilder&)` (L19) | 툴바 확장 콜백 |
| `class FExtensionBase` | 등록 핸들 (해제용 — 의도적으로 구현 숨김) |

`FExtender::AddMenuBarExtension` / `AddMenuExtension` / `AddToolBarExtension` — 모두 `(ExtensionHook FName, EExtensionHook::Position, FUICommandList, Delegate)` 시그니처.

### 2.5 ToolMenuBase (`Public/Framework/MultiBox/ToolMenuBase.h`)

| 심볼 | 용도 |
|------|------|
| `UCLASS UToolMenuBase` (`.generated.h`) | 사용자 정의 메뉴 베이스 (UObject 기반 — `UToolMenus` 시스템과 통합) |
| `USTRUCT FCustomizedToolMenuEntry` / `FCustomizedToolMenuSection` / `FCustomizedToolMenuNameArray` | 사용자가 메뉴를 커스터마이즈한 결과 직렬화 |
| `enum class ECustomizedToolMenuVisibility { None, Visible, Hidden }` | 항목 가시성 오버라이드 |

> `UToolMenus` (`Editor` 모듈) — 5.x 표준 메뉴 시스템. UCLASS 기반으로 등록·확장. 본 sub-skill 은 `Slate` 모듈의 빌더에 집중하고, `UToolMenus` 의 자세한 활용은 향후 별도 모듈 위키에서.

### 2.6 위젯 — 팝업/메뉴 앵커 (`Public/Widgets/Input/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Widgets/Input/SMenuAnchor.h` | `class SMenuAnchor : public SPanel, public IMenuHost` (L31) | 정확히 위젯 옆에 팝업 메뉴를 띄우는 앵커 위젯. |
| `Widgets/Input/SComboButton.h` | `SComboButton` | 콤보 버튼 — 메뉴를 띄우는 버튼. |
| `Widgets/Input/SExpandableButton.h` | `SExpandableButton` | 클릭 시 본체 + 팝업 묶음. |
| `Widgets/Input/SSubMenuHandler.h` | `SSubMenuHandler` | 서브메뉴 호버 등 인터랙션. |
| `Widgets/Layout/SMenuOwner.h` | `SMenuOwner` | 메뉴 생명주기 관리. |
| `Widgets/Layout/SPopup.h` | `SPopup` | 일반 팝업 컨테이너. |

### 2.7 ToolBar 블록 위젯 (`Public/Framework/MultiBox/`)

| 헤더 | 심볼 | 용도 |
|------|------|------|
| `MultiBox/SToolBarButtonBlock.h` | `FToolBarButtonBlock` | 표준 툴바 버튼. |
| `MultiBox/SToolBarComboButtonBlock.h` | `FToolBarComboButtonBlock` | 콤보 버튼 (메뉴 포함). |
| `MultiBox/SToolBarStackButtonBlock.h` | `FToolBarStackButtonBlock` | 메인 + 보조(arrow) 묶음 5.x. |
| `MultiBox/SUniformToolbarButtonBlock.h` | `FUniformToolbarButtonBlock` | 균등 너비 버튼. |

빌더가 자동 생성 — 직접 만들 일은 거의 없음.

---

## 3. 자주 쓰는 API

### 3.1 컨텍스트 메뉴 (가장 흔함)

```cpp
// 우클릭 팝업 메뉴 (예: 리스트 아이템 우클릭)
TSharedRef<SWidget> MakeContextMenu(TSharedPtr<FMyItem> ContextItem)
{
    FMenuBuilder Menu(/*bInShouldCloseWindowAfterMenuSelection=*/true,
                      MyCommandList,
                      /*InExtender=*/nullptr);

    Menu.BeginSection("Edit", LOCTEXT("EditSection", "Edit"));         // L361
    {
        Menu.AddMenuEntry(FMyCommands::Get().Cut);                       // L267 (FUICommandInfo)
        Menu.AddMenuEntry(FMyCommands::Get().Copy);
        Menu.AddMenuEntry(FMyCommands::Get().Paste);
    }
    Menu.EndSection();                                                   // L366

    Menu.AddMenuSeparator();                                             // L350

    Menu.BeginSection("ItemActions", LOCTEXT("ItemActionsSection", "Item Actions"));
    {
        // 직접 람다 액션 (FUIAction)
        Menu.AddMenuEntry(
            LOCTEXT("Inspect", "Inspect"),                               // L282 시그니처
            LOCTEXT("InspectTip", "Open inspector for this item"),
            FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Inspect"),
            FUIAction(
                FExecuteAction::CreateLambda([ContextItem]() { Inspect(ContextItem); }),
                FCanExecuteAction::CreateLambda([ContextItem]() { return ContextItem.IsValid(); })
            )
        );

        // 서브메뉴
        Menu.AddSubMenu(                                                 // L385
            LOCTEXT("Export", "Export As..."),
            LOCTEXT("ExportTip", "Export this item"),
            FNewMenuDelegate::CreateLambda([](FMenuBuilder& Sub) {
                Sub.AddMenuEntry(LOCTEXT("AsCSV", "CSV"), FText::GetEmpty(),
                                 FSlateIcon(), FUIAction(...));
                Sub.AddMenuEntry(LOCTEXT("AsJSON", "JSON"), FText::GetEmpty(),
                                 FSlateIcon(), FUIAction(...));
            })
        );
    }
    Menu.EndSection();

    return Menu.MakeWidget();
}

// 사용 — SListView::OnContextMenuOpening 등
SNew(SListView<...>)
.OnContextMenuOpening(FOnContextMenuOpening::CreateLambda([this]() {
    return MakeContextMenu(SelectedItem);
}));
```

### 3.2 툴바 (Slim Horizontal — 5.x 표준)

```cpp
TSharedRef<SWidget> MakeToolBar()
{
    FSlimHorizontalToolBarBuilder Tb(MyCommandList, FMultiBoxCustomization::None);

    Tb.BeginSection("Tools");
    {
        Tb.AddToolBarButton(FMyCommands::Get().Build);
        Tb.AddToolBarButton(FMyCommands::Get().Run);

        Tb.AddSeparator();                                               // L735

        Tb.AddComboButton(                                               // L653
            FUIAction(),
            FOnGetContent::CreateRaw(this, &FMyTool::MakeBuildSettingsMenu),
            LOCTEXT("BuildSettings", "Settings"),
            LOCTEXT("BuildSettingsTip", "Build settings"),
            FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Settings"),
            /*bInSimpleComboBox=*/false
        );
    }
    Tb.EndSection();

    return Tb.MakeWidget();
}
```

### 3.3 메뉴 바 (윈도우 상단 — File / Edit / View ...)

```cpp
TSharedRef<SWidget> MakeMenuBar()
{
    FMenuBarBuilder Mb(MyCommandList);

    Mb.AddPullDownMenu(
        LOCTEXT("File", "File"),
        LOCTEXT("FileTip", "File operations"),
        FNewMenuDelegate::CreateRaw(this, &FMyTool::FillFileMenu),
        "File"   // ← Extension hook 이름 (다른 모듈이 이 이름 기준으로 끼어들 수 있게)
    );

    Mb.AddPullDownMenu(
        LOCTEXT("Edit", "Edit"),
        LOCTEXT("EditTip", "Edit operations"),
        FNewMenuDelegate::CreateRaw(this, &FMyTool::FillEditMenu),
        "Edit"
    );

    return Mb.MakeWidget();
}

void FMyTool::FillFileMenu(FMenuBuilder& Menu)
{
    Menu.BeginSection("FileBasic", LOCTEXT("FileBasicSection", "File"));
    Menu.AddMenuEntry(FMyCommands::Get().NewProject);
    Menu.AddMenuEntry(FMyCommands::Get().OpenProject);
    Menu.AddMenuEntry(FMyCommands::Get().Save);
    Menu.EndSection();

    Menu.AddMenuSeparator();
    Menu.AddMenuEntry(FMyCommands::Get().Exit);
}
```

### 3.4 Extender — 다른 모듈의 메뉴/툴바에 끼어들기

```cpp
// 예: LevelEditor 의 "Window" 메뉴 끝에 내 도구 항목 추가
TSharedPtr<FExtender> Ext = MakeShared<FExtender>();

Ext->AddMenuExtension(
    "WindowLayout",                    // ExtensionHook — 호스트 모듈이 메뉴 만들 때 BeginSection 의 이름
    EExtensionHook::After,             // 그 섹션 뒤에 추가
    Cmds,                              // 명령 리스트
    FMenuExtensionDelegate::CreateLambda([](FMenuBuilder& Menu) {
        Menu.AddMenuEntry(FMyCommands::Get().OpenMyTool);
    })
);

// 호스트 모듈에 등록 (예: LevelEditorModule)
FLevelEditorModule& LevelEditor = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
LevelEditor.GetMenuExtensibilityManager()->AddExtender(Ext);

// 해제 (ShutdownModule)
LevelEditor.GetMenuExtensibilityManager()->RemoveExtender(Ext);
```

호스트 모듈이 `IExtensibilityManager` 노출해야 가능 — UnrealEd / LevelEditor / 대부분 표준 에디터 모듈은 노출.

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 빌더 — 거의 override 안 함

`FMultiBoxBuilder::MakeWidget` 가 virtual이지만 일반적으로 그대로 사용. 모든 표준 빌더는 잘 동작.

### 4.2 SMenuAnchor (`SMenuAnchor.h:31`) — 커스텀 팝업

`SMenuAnchor : SPanel, IMenuHost`. SPanel이라 `OnArrangeChildren`/`ComputeDesiredSize`/`GetChildren` 구현. `IMenuHost` 측은 메뉴 생명주기.

게임 코드는 그냥 `SNew(SMenuAnchor)` 사용 — 직접 상속 거의 없음.

### 4.3 UToolMenuBase 🛠

`UCLASS` 라 UObject 가상 함수 적용. 자세한 라이프사이클은 [`CoreUObject/UObject/`](../../CoreUObject/references/UObject.md).

---

## 5. 인하우스 툴 — 메뉴/툴바 통합 골격

```cpp
// SMyToolPanel.cpp 안에서 — 한 도킹 탭의 컨텐츠 구성
void SMyToolPanel::Construct(const FArguments& InArgs)
{
    CommandList = InArgs._CommandList;        // Commands/SKILL.md 에서 만들어 전달

    ChildSlot
    [
        SNew(SVerticalBox)

        // 1) 상단 메뉴 바
        + SVerticalBox::Slot().AutoHeight()
        [ MakeMenuBar() ]

        // 2) 그 아래 툴바 (SlimHorizontal — 5.x 권장)
        + SVerticalBox::Slot().AutoHeight()
        [ MakeToolBar() ]

        // 3) 본 컨텐츠
        + SVerticalBox::Slot().FillHeight(1.f)
        [
            SNew(SListView<TSharedPtr<FItem>>)
            .ListItemsSource(&Items)
            .OnGenerateRow(this, &SMyToolPanel::OnGenerateItemRow)
            .OnContextMenuOpening(this, &SMyToolPanel::OnContextMenuOpening)
        ]

        // 4) 하단 상태 바 (선택)
        + SVerticalBox::Slot().AutoHeight()
        [ MakeStatusBar() ]
    ];
}

TSharedPtr<SWidget> SMyToolPanel::OnContextMenuOpening()
{
    return MakeContextMenu(GetSelectedItem());   // §3.1 패턴
}
```

---

## 6. 운영 가이드 / 함정

1. **`bShouldCloseWindowAfterMenuSelection`** — 첫 인자. true 면 메뉴 항목 클릭 시 메뉴 자동 닫힘 (대부분의 경우 OK). false 는 다중 선택 메뉴(체크박스 토글) 등에 사용.
2. **CommandList 누락** — 빌더 생성자에 `nullptr` 넘기면 `AddMenuEntry(FUICommandInfo)` 가 동작 안 함 — 액션 매핑 안 되어 있어 회색으로 보임. 항상 `MyCmds` 또는 `nullptr` 명시 의도적으로.
3. **ExtensionHook 이름은 호스트와 정확히 일치** — `"WindowLayout"` 같은 hook 이름은 호스트 모듈 코드 보거나 문서 확인 필요. 잘못된 hook 은 무시됨 (에러 안 남).
4. **`FNewMenuDelegate`** 람다 캡처 — 위젯/객체는 `TWeakPtr`/`TWeakObjectPtr` 로. 강 참조 시 메뉴 닫혀도 객체 유지됨.
5. **5.x 슬림 툴바** — `FSlimHorizontalToolBarBuilder` 는 에디터 5.x 표준. 옛 `FToolBarBuilder` 는 두꺼운 옛 스타일. 새 도구는 슬림 권장.
6. **섹션은 항상 `BeginSection` + `EndSection` 쌍** — 누락 시 메뉴 그룹화 깨짐.
7. **`AddPullDownMenu` (메뉴 바)** vs **`AddSubMenu` (메뉴)** — 메뉴 바의 최상위 항목은 PullDown, 메뉴 안의 중첩은 SubMenu.
8. **`UToolMenus` 사용 권장 (5.x)** — 본 sub-skill 의 `FMenuBuilder` 직접 사용은 옛 패턴이지만 여전히 유효. 5.x 신규 코드는 `UToolMenus::Get()->RegisterMenu(...)` 가 사용자 커스터마이즈·검색 등 더 풍부. (별도 위키 예정.)
9. **컨텍스트 메뉴 캐싱 금지** — `MakeContextMenu(SelectedItem)` 처럼 매번 새로 만들기. 캐시 시 SelectedItem 변경 반영 안 됨.
10. **Extender 해제** — `ShutdownModule` 에서 `RemoveExtender` 명시. 모듈 hot-reload 시 댕글링.

---

## 7. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

> **🚨 런타임/에디터 분리 원칙은 [`Slate/SKILL.md §8`](../SKILL.md#8--런타임--에디터-분리-원칙-인하우스-툴-묶음-공통-규약) 의무 규약.** `FMenuBuilder`/`FToolBarBuilder` 자체는 컴파일 OK이지만, 메인 메뉴/메뉴 바 통합·`UToolMenus` 사용·`IExtensibilityManager` 호출은 `UnrealEd` 의존이라 **에디터 모듈로 분리** 후 `#if WITH_EDITOR` 가드 안에서만.

본 sub-skill 전체가 사실상 에디터/툴 빌드 전용. 게임 빌드에서는 직접 SButton/SVerticalBox 조합으로 UI를 만드는 것이 일반적.

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| 모든 `F*Builder` 🛠 | MultiBoxBuilder.h | (런타임 컴파일 됨) | 게임 UI에서 사용 안 함. |
| `UToolMenuBase` 🛠 | ToolMenuBase.h | UCLASS — 에디터 통합 | `UToolMenus` 모듈은 Editor 측. |
| `IExtensibilityManager` 🛠 | (호스트 모듈별) | 에디터 모듈 | LevelEditor/UnrealEd 등이 노출. |
| `FAppStyle::Get().GetBrush(...)` 메뉴 아이콘 🛠 (실용) | (런타임 존재) | 게임 빌드는 `FUMGCoreStyle` | 자세히 [`../../SlateCore/Styling/`](../../SlateCore/references/Styling.md). |
| `FMultiBoxSettings` 🛠 | MultiBoxDefs.h L90 | 에디터 환경 설정 | 사용자 커스터마이즈. |

---

## 8. 관련 sub-skill

- [`Commands/`](../Commands/SKILL.md) — `FUICommandList` / `FUICommandInfo` (메뉴 항목의 액션 측)
- [`Docking/`](../Docking/SKILL.md) — 메뉴/툴바를 띄우는 `SDockTab` 컨텐츠
- [`EditorApplication/`](../EditorApplication/SKILL.md) — `FGlobalTabmanager::Get()->TryInvokeTab(...)` 가 메뉴 액션 타깃
- [`CommonWidgets/`](../CommonWidgets/SKILL.md) — `SMenuAnchor`/`SComboButton`/`SExpandableButton` 베이스
- [`../../SlateCore/Styling/`](../../SlateCore/references/Styling.md) — `FAppStyle` 의 메뉴/툴바 아이콘
