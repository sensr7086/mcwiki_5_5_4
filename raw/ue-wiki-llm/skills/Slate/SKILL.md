---
name: slate-main
description: Tier 3 Slate 모듈 메인 — EditorApplication 🛠 + Docking 🛠 + Menu 🛠 + Commands 🛠 + GraphEditor 🛠 + Application + CommonWidgets + LayoutWidgets + ListsTrees + TextInput + MiscWidgets + Animation 12개 sub-skill. §8 런타임/에디터 분리 원칙 (4단 방어).
---

# Slate — 모듈 진입점

> Tier 3 · L4 (UI 인프라) · UE 5.7.4 기준
> 위치: `Engine/Source/Runtime/Slate/`
> 의존: **Public** Core, CoreUObject, InputCore, Json, SlateCore, ImageWrapper (+ ApplicationCore — `bCompileAgainstApplicationCore`) / **Private** TraceLog
> 출처: `Slate.Build.cs` 직접 확인
>
> **상위 인덱스**: [`../../references/03_WikiHarness.md`](../../references/03_WikiHarness.md) · 시나리오 §3.12 (새 SWidget·UMG) + 인하우스 툴 시나리오 (향후 추가).

---

## 1. 개요

`Slate`는 [`SlateCore`](../SlateCore/SKILL.md) 위에 **표준 위젯 라이브러리 + Application 본체 + 인하우스 툴 인프라**를 얹는 모듈이다. 게임 UI(`SButton`/`SListView` 등) 와 에디터 도구(`SDockTab`/`FTabManager`/`FUICommandList`/`FMenuBuilder`) 가 한 모듈 안에 공존한다.

```
SlateCore  (위젯 베이스·페인트·인밸리데이션)
  └─ Slate (이 모듈)
       ├─ Application/   FSlateApplication 본체 (게임 + 에디터 공통)
       ├─ Widgets/       표준 위젯 라이브러리 (SButton/SListView/SEditableText 등)
       ├─ Framework/     Docking·MultiBox·Commands·Notifications (인하우스 툴)
       └─ Framework/Text 다중 라인 + 리치 텍스트 (런 시스템)
```

본 sub-skill 묶음은 **두 영역**으로 나뉜다:

- **A. 게임 + 에디터 공통** — 일반 위젯·텍스트·리스트 (게임 UI 작성)
- **B. 인하우스 툴 🛠** — 에디터 도구·사내 툴 작성에 필요한 도킹·메뉴·단축키·노드 그래프 등

---

## 2. 의존·빌드 (`Slate.Build.cs` 요약)

```text
PublicDependencyModuleNames  : Core, CoreUObject, InputCore, Json, SlateCore, ImageWrapper
                              (+ ApplicationCore — bCompileAgainstApplicationCore)
PrivateDependencyModuleNames : TraceLog
PrivateDefinitions           : SLATE_MODULE=1
SharedPCHHeaderFile          : Public/SlateSharedPCH.h
ThirdParty (Public/Private)  : XInput (Win64), SDL3 (Linux 그룹)
```

`SLATE_MODULE=1` 매크로로 모듈 내부 헤더가 자기 자신임을 식별.

---

## 3. 자주 쓰는 API (1줄 요약 — 상세는 각 sub-skill)

```cpp
// Application 진입
FSlateApplication& App = FSlateApplication::Get();    // Application/SKILL.md
TSharedRef<SWindow> W = App.AddWindow(SNew(SWindow).Title(...).ClientSize(FVector2D(800,600)));

// 도킹 탭 (인하우스 툴)
FGlobalTabmanager::Get()->RegisterTabSpawner(TabId, FOnSpawnTab::CreateRaw(this, &FMyTool::SpawnTab));
FGlobalTabmanager::Get()->TryInvokeTab(TabId);

// 메뉴/툴바 빌더
FMenuBuilder Menu(/*ShouldCloseAfterMenuSelection=*/true, MyCommandList);
Menu.AddMenuEntry(FMyCommands::Get().DoThing);
TSharedRef<SWidget> MenuWidget = Menu.MakeWidget();

// 표준 위젯
SNew(SVerticalBox)
+ SVerticalBox::Slot().AutoHeight() [ SNew(SButton).Text(LOCTEXT("Click", "Click")) ]
+ SVerticalBox::Slot().FillHeight(1.f) [ SNew(SListView<TSharedPtr<FItem>>) ];

// 알림 (인하우스 툴)
FNotificationInfo Info(LOCTEXT("Saved", "Saved"));
Info.ExpireDuration = 3.f;
FSlateNotificationManager::Get().AddNotification(Info);
```

상세 시그니처·오버로드·사용 패턴은 다음 sub-skill에서 다룬다.

---

## 4. 사용 예제 (인하우스 툴 골격)

```cpp
// FMyToolModule.h / .cpp 요지
class FMyToolModule : public IModuleInterface
{
public:
    virtual void StartupModule() override
    {
        // 1) 단축키 등록
        FMyToolCommands::Register();

        // 2) 명령 → 실행 매핑
        Cmds = MakeShared<FUICommandList>();
        Cmds->MapAction(FMyToolCommands::Get().Open,
                        FExecuteAction::CreateRaw(this, &FMyToolModule::OpenWindow));

        // 3) 메인 메뉴에 항목 등록 (Extender 패턴)
        TSharedPtr<FExtender> MainMenuExt = MakeShared<FExtender>();
        MainMenuExt->AddMenuExtension("Tools", EExtensionHook::After, Cmds,
            FMenuExtensionDelegate::CreateRaw(this, &FMyToolModule::AddMenu));

        // 4) 탭 스포너 등록 (도킹 시스템)
        FGlobalTabmanager::Get()->RegisterNomadTabSpawner(MyTabId,
            FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnTab))
            .SetDisplayName(LOCTEXT("MyTool", "My Tool"));
    }

    TSharedRef<SDockTab> SpawnTab(const FSpawnTabArgs& Args)
    {
        return SNew(SDockTab).TabRole(ETabRole::NomadTab)
            [ SNew(SVerticalBox) /* 툴 컨텐츠 */ ];
    }
};
```

위 흐름의 각 부분은 인하우스 툴 묶음 sub-skill에서 자세히.

---

## 5. Sub-skill 인덱스 (메인 + 13개)

각 sub-skill은 *개요 → 핵심 헤더/클래스 → 자주 쓰는 API → virtual → 예제 → 에디터 전용 → 관련 sub-skill* 일관 구조.

### 5.A 게임 + 에디터 공통 — 일반 위젯/시스템

| # | Sub-skill | 다루는 영역 | 주요 헤더/심볼 |
|---|-----------|-------------|----------------|
| 1 | [`Application/`](./Application/SKILL.md) | `FSlateApplication` 본체 (게임/에디터 공통) · `FSlateUser` · `AnalogCursor` · `IInputProcessor` · `NavigationConfig`(Null/TwinStick) · `IMenu`/`MenuStack` · `SWindowTitleBar` | `Framework/Application/*` |
| 2 | [`CommonWidgets/`](./CommonWidgets/SKILL.md) | `SButton`/`SCheckBox`/`SImage`/`STextBlock`/`SHyperlink`/`SSpacer`/`SBorder`/`SSegmentedControl` | `Widgets/Input/SButton.h` 등 |
| 3 | [`LayoutWidgets/`](./LayoutWidgets/SKILL.md) | `SBoxPanel`/`SOverlay`/`SUniformGridPanel`/`SGridPanel`/`SWrapBox`/`SBox`/`SCanvas`/`SInvalidationPanel`/`SScrollBox`/`SScaleBox`/`SDPIScaler`/`SSafeZone`/`SExpandableArea` | `Widgets/Layout/*`, `Widgets/SCanvas.h`, `Widgets/SInvalidationPanel.h` |
| 4 | [`ListsTrees/`](./ListsTrees/SKILL.md) | `SListView`/`STreeView`/`STileView`/`STableViewBase`/`STableRow`/`SHeaderRow`/`SExpanderArrow`/`IItemsSource`/`ITableRow`/`TreeFilterHandler` | `Widgets/Views/*`, `Framework/Views/*` |
| 5 | [`TextInput/`](./TextInput/SKILL.md) | `SEditableText`/`Box`·`SMultiLineEditableText`/`Box`·`SSearchBox`·`SInlineEditableTextBlock`·`SRichTextBlock`·`IRun`·`ITextLayoutMarshaller`·`SlateEditableTextLayout` | `Widgets/Text/*`, `Widgets/Input/SEditableText*.h`, `Framework/Text/*` |
| 6 | [`MiscWidgets/`](./MiscWidgets/SKILL.md) | `SSlider`/`SSpinBox`/`SColor*`(Colors)·`SThrobber`/`SViewport`/`SVirtualWindow`/`SBackgroundBlur`/`SFxWidget`/`SBreadcrumbTrail`/`SLayerManager`/`STooltipPresenter` | `Widgets/Input/SSlider.h`, `Widgets/Colors/*`, `Widgets/Images/*`, `Widgets/SViewport.h` 등 |
| 7 | [`Animation/`](./Animation/SKILL.md) | `FAnimatedAttribute`·`FAnimatedAttributeManager`·`FAttributeInterpolator` (5.x 어트리뷰트 보간 — SlateCore Animation 위 레이어) | `Framework/Animation/*` |

### 5.B 인하우스 툴 🛠 — 에디터 도구 / 사내 툴 작성

| # | Sub-skill | 다루는 영역 | 주요 헤더/심볼 |
|---|-----------|-------------|----------------|
| 8 | [`EditorApplication/`](./EditorApplication/SKILL.md) 🛠 | **본 묶음의 진입점** — `FSlateApplication::Create`/`InitializeAsStandaloneApplication`/`InitializeCoreStyle`/`InitHighDPI`/`Shutdown` · `Tick`/`PumpMessages`/`TickPlatform`/`TickAndDrawWidgets` · 인하우스 툴 진입 흐름 · `IInputProcessor` 전역 후크 등록 | `Framework/Application/SlateApplication.h` (에디터 측면), `Framework/Application/IInputProcessor.h` |
| 9 | [`Docking/`](./Docking/SKILL.md) 🛠 | **인하우스 툴 핵심** — `SDockTab` · `FTabManager` · `FGlobalTabmanager` · `SDockingArea` · `FWorkspaceItem` · `FLayoutExtender` · `FLayoutService` · `FSpawnTabArgs` · `TabCommands` · `STabDrawer` · 탭 등록 패턴 | `Framework/Docking/*`, `Widgets/Docking/SDockTab.h` |
| 10 | [`Menu/`](./Menu/SKILL.md) 🛠 | 메뉴/툴바 빌더 — `FMenuBuilder`·`FToolBarBuilder`·`FMultiBoxExtender` · `MultiBox`/`MultiBoxDefs`·`ToolMenuBase` · `SToolBarButton/Combo/Stack/UniformBlock` · `SMenuAnchor`/`SMenuOwner`/`SSubMenuHandler` · `SExpandableButton`·`SPopup` | `Framework/MultiBox/*`, `Widgets/Input/SMenuAnchor.h`, `Widgets/Input/SExpandableButton.h` 등 |
| 11 | [`Commands/`](./Commands/SKILL.md) 🛠 | 단축키 시스템 — `FUICommandList`·`FUICommandInfo`·`FInputBindingManager`·`FInputChord`·`FUIAction`·`FUICommandDragDropOp`·`FGenericCommands`·`Contexts/` | `Framework/Commands/*` |
| 12 | [`Notifications/`](./Notifications/SKILL.md) 🛠 | 토스트/에러/진행도 — `FSlateNotificationManager`·`SNotificationList`/`Background`·`GlobalNotification`·`INotificationWidget`·`SErrorHint`/`SErrorText`/`SPopUpErrorText`·`SProgressBar` | `Framework/Notifications/*` |
| 13 | [`GraphEditor/`](./GraphEditor/SKILL.md) 🛠 | 노드 그래프 에디터 — **EdGraph 코어** (`UEdGraph`/`UEdGraphNode`/`UEdGraphPin`/`UEdGraphSchema` — Engine 모듈) + **GraphEditor 모듈** (`SGraphPanel`/`SGraphNode`/`SGraphPin`/`FNodeFactory`/`FConnectionDrawingPolicy`/`SGraphActionMenu`/`SGraphPalette` — Editor 모듈) · 인하우스 노드 에디터 작성 패턴 | `Engine/Classes/EdGraph/*` (런타임), `Engine/Source/Editor/GraphEditor/Public/*` (에디터 — **본 위키 정식 분석 범위 외**, 인하우스 툴 필수라 예외 처리) |

> 🛠 묶음의 `Docking`/`Menu`/`Commands`/`Notifications` 는 게임 빌드에도 컴파일은 되지만, 주 사용처가 에디터/인하우스 툴이라 분류 표시. `EditorApplication`/`GraphEditor` 는 사용처가 사실상 에디터 빌드 한정.

> `GraphEditor/` 의 GraphEditor 모듈 부분은 본 위키 메타 규칙(`Engine/Source/Runtime/`만 분석)의 **예외**다. 인하우스 노드 에디터 작성에 필수라 인덱스 + 핵심 클래스 정도만 다루고, 깊은 분할은 향후 별도 모듈 위키(`skills/GraphEditor/`)로 분리 예정.

---

## 6. 관련 모듈

- **상위 (의존됨)**: `UMG`, `SlateRHIRenderer`, `EditorWidgets`, `WidgetCarousel`, `AdvancedWidgets`, `AppFramework`, `GameMenuBuilder`, 거의 모든 에디터 모듈 (`UnrealEd`/`PropertyEditor`/`GraphEditor` 등).
- **하위 (의존)**: [`SlateCore/`](../SlateCore/SKILL.md), `Core`, `CoreUObject`, `InputCore`, `Json`, `ImageWrapper`, `TraceLog`, `ApplicationCore`(옵션).
- **연계**:
  - [`SlateCore/Application/`](../SlateCore/references/Application.md) — `FSlateApplicationBase` 추상 베이스
  - [`SlateCore/SWidget/`](../SlateCore/references/SWidget.md) — 모든 표준 위젯의 베이스
  - [`SlateCore/Drawing/`](../SlateCore/references/Drawing.md) — 인밸리데이션·LayerId·DrawCall 가이드
  - [`UMG/`](../UMG/SKILL.md) — Slate 위에 BP 노출 레이어
  - [`ApplicationCore/`](../ApplicationCore/SKILL.md) — OS 추상 (윈도우/이벤트/입력)

---

## 7. 작성·인용 규칙

전체 위키 공통 규칙을 따른다 — `skills/CoreUObject/SKILL.md §7.1` 의 에디터 전용 표기 규칙(🛠 마커 + `WITH_EDITOR`/`WITH_EDITORONLY_DATA` 가드 명시) + 라인 번호 직접 grep 검증.

추가로 Slate 모듈 특수 규약:

- `SNew`/`SAssignNew` 매크로 사용 — `new SWidget()` 직접 호출 금지.
- 람다에서 위젯/객체 캡처는 `TWeakPtr<SWidget>`/`TWeakObjectPtr<UObject>` 사용.
- 인하우스 툴 묶음(🛠)은 `WITH_EDITOR` 가드 안에서만 호출 권장.
- `GraphEditor/` 의 GraphEditor 모듈 인용은 본 위키 분석 범위 외 — 메타 안내 명시 필수.
- 인용 라인은 5.7.4 트리에서 직접 grep — 마이너 패치에 따라 ±수십 라인.
