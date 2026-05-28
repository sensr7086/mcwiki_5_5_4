---
name: slate-commands
description: 🛠 FUICommandList + FUICommandInfo + UI_COMMAND 매크로 + InputBindingManager + 단축키.
---

# Slate / Commands 🛠

> 부모 모듈: [`Slate`](../SKILL.md) · UE 5.5.4
> 다루는 영역: 명령·단축키 시스템 — `TCommands<T>` · `FUICommandInfo` · `FUICommandList` · `FUIAction` · `FInputChord` · `FInputBindingManager` · `FBindingContext` · `FGenericCommands` · `Contexts/UIIdentifierContext`/`UIContentContext` · `UI_COMMAND` 매크로 + 사용자 단축키 커스터마이즈
> 🛠 사실상 에디터/인하우스 툴 빌드 한정 (게임은 `EnhancedInput` 사용 권장).
> **🚨 런타임/에디터 분리 원칙은 [`Slate/SKILL.md §8`](../SKILL.md#8--런타임--에디터-분리-원칙-인하우스-툴-묶음-공통-규약)** 의무 규약.
> 관련 sub-skill: [`Menu/`](../Menu/SKILL.md), [`EditorApplication/`](../EditorApplication/SKILL.md), [`Docking/`](../Docking/SKILL.md), [`../../InputCore/`](../../InputCore/SKILL.md)

---

## 1. 개요

Commands 시스템은 **명령(Command)을 정의 → 단축키(Chord)에 바인딩 → 실행 액션(Action)에 매핑**하는 3단 구조다. 인하우스 툴이 메뉴·툴바·단축키를 한 번에 일관성 있게 묶는 표준 방식.

```
TCommands<FMyCommands>             ← 명령 묶음 정의 (싱글턴)
   └─ FUICommandInfo (Open, Save, Close…)  ← 명령 = 이름 + 라벨 + 아이콘 + 기본 단축키
        └─ FInputChord (Ctrl+S 등)          ← 키 + Shift/Ctrl/Alt/Cmd 모디파이어

FUICommandList                     ← 한 컨텍스트(탭/도구)의 명령 → 액션 매핑
   .MapAction(Cmd, FUIAction(Execute, CanExecute, IsChecked))
   .ProcessCommandBindings(KeyEvent)        ← 키 이벤트가 들어오면 해당 명령 실행

FInputBindingManager (전역)        ← 사용자 커스터마이즈 단축키 저장·복원
```

**핵심 분리** — `FUICommandInfo` 는 "무엇을(명령 정의)" 이고, `FUICommandList` 는 "어떻게(누가 실행)" 다. 한 명령 정의를 여러 컨텍스트가 다른 액션으로 매핑 가능 (예: `Save` 가 메인 에디터에서는 Level 저장, BP 에디터에서는 BP 저장).

---

## 2. 핵심 헤더와 클래스

### 2.1 명령 정의 (`Public/Framework/Commands/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Commands.h` | `template<typename CommandContextType> class TCommands : public FBindingContext` (L29) | **명령 묶음 베이스 (싱글턴)** — `Register()`/`Unregister()`/`Get()`/`IsRegistered()` 정적 + `RegisterCommands()` virtual 사용자 구현. |
| `Commands.h` | `UI_COMMAND(CommandId, Friendly, Desc, Type, Chord, ...)` (L22) | 명령 등록 매크로 — `LOCTEXT_NAMESPACE` 필수. |
| `Commands.h` | `UI_COMMAND_EXT(...)` (L19) | 확장 매크로 — namespace 직접 지정. |
| `Commands.h` | `MakeUICommand_InternalUseOnly(...)` (L16) | UI_COMMAND 매크로의 내부 호출 — 직접 호출 금지. |
| `UICommandInfo.h` | `class FUICommandInfo` (L183) | 명령 본체 — 라벨/툴팁/아이콘/기본 chord 보유. |
| `UICommandInfo.h` | `class FUICommandInfoDecl` (L54) | 빌더 — `MakeCommandInfo` 동적 생성 시. |
| `UICommandInfo.h` | `class FBindingContext` (L83) | 명령 묶음의 컨텍스트 (이름·스타일셋). `TCommands` 의 베이스. |
| `UICommandInfo.h` | `enum class EUserInterfaceActionType : uint8` (L19) | Button / ToggleButton / RadioButton / Check / CollapsedButton |
| `UICommandInfo.h` | `enum class EMultipleKeyBindingIndex : uint8` (L41) | Primary / Secondary — 한 명령에 두 단축키 바인딩 가능. |

### 2.2 액션 (`UIAction.h`)

| 심볼 | 역할 |
|------|------|
| `struct FUIAction` (L37) | **실행 콜백 묶음** — `ExecuteAction`(필수)·`CanExecuteAction`·`GetActionCheckState`·`IsActionVisibleDelegate`·`RepeatMode`. |
| `DECLARE_DELEGATE(FExecuteAction)` (L11) | `void()` 실행. |
| `DECLARE_DELEGATE_RetVal(bool, FCanExecuteAction)` (L14) | 실행 가능 여부 — false 면 메뉴/툴바 회색. |
| `DECLARE_DELEGATE_RetVal(bool, FIsActionChecked)` (L17) | 체크 상태 (toggle/radio). |
| `DECLARE_DELEGATE_RetVal(ECheckBoxState, FGetActionCheckState)` (L20) | 3-state 체크 (Checked/Unchecked/Undetermined). |
| `DECLARE_DELEGATE_RetVal(bool, FIsActionButtonVisible)` (L23) | 가시성 동적 결정. |
| `enum class EUIActionRepeatMode` (L27) | RepeatDisabled / RepeatEnabled — chord 누른 채로 반복 실행 여부. |

### 2.3 단축키 (`InputChord.h`)

| 심볼 | 위치 | 역할 |
|------|------|------|
| `USTRUCT FInputChord` (L23) | InputChord.h | **키 + 모디파이어 묶음**. `FKey Key` + `bShift`/`bCtrl`/`bAlt`/`bCmd` 4개 비트. UPROPERTY 노출. |
| `typedef FInputChord FInputGesture` (L19) | (deprecated 4.21) | 옛 이름 — 사용 금지. |

### 2.4 명령 → 액션 매핑 (`UICommandList.h`)

| 심볼 | 위치 | 역할 |
|------|------|------|
| `class FUICommandList` (L14) | UICommandList.h | **한 컨텍스트의 명령→액션 매핑**. 위젯/탭마다 하나 보유. |
| `MapAction` 7가지 오버로드 (L32~L106) | (Execute / + CanExecute / + IsChecked / + GetActionCheckState / + IsVisible / FUIAction / FUIAction+UIActionContext) |
| `Append(TSharedRef<FUICommandList>)` (L111) | 다른 CommandList 의 매핑을 합침 (부모 도구 → 자식 패널 등). |
| `UnmapAction(...)` (L118) | 매핑 해제. |
| `IsActionMapped(...)` (L125) | 매핑 여부. |
| `ExecuteAction(...)` (L133, virtual) | 명령 실행. |
| `CanExecuteAction(...)` (L140) | 가능 여부. |
| `TryExecuteAction(...)` (L148) | CanExecute 체크 후 실행 — false 면 안 함. |
| `GetCheckState(...)` (L162) | 체크 상태 조회. |
| `ProcessCommandBindings(FKeyEvent)` (L170) | **키 이벤트 → 명령 실행 라우팅 — 위젯의 OnKeyDown 에서 호출**. |
| `ProcessCommandBindings(FPointerEvent)` (L178) | 마우스 chord 라우팅. |
| `ProcessCommandBindings(FKey, FModifierKeysState, bool bRepeat)` (L188) | 저수준 변형. |

### 2.5 전역 단축키 매니저 (`InputBindingManager.h`)

| 심볼 | 위치 | 역할 |
|------|------|------|
| `class FInputBindingManager` (L25) | InputBindingManager.h | **앱 전역 명령 등록소** — TCommands 인스턴스를 담아 두고, 사용자 커스터마이즈된 chord 를 ini 에 저장/복원. `Get()` 정적. |
| `class FUserDefinedChords` (L10 forward) | (private 구현) | 사용자가 변경한 chord 저장. |

`TCommands::Register()` 가 내부적으로 `FInputBindingManager::Get()` 에 등록.

### 2.6 표준 명령 (`GenericCommands.h`)

| 심볼 | 명령 |
|------|------|
| `class FGenericCommands : public TCommands<FGenericCommands>` (L11) | **모든 도구가 재사용하는 표준 9개**: Cut, Copy, Paste, Duplicate, Undo, Redo, Delete, Rename, SelectAll |

엔진이 자동 Register — 직접 등록 불필요. `FGenericCommands::Get().Cut` 으로 바로 사용.

### 2.7 컨텍스트 (`Contexts/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Contexts/UIIdentifierContext.h` | `FUIIdentifierContext` | 명령 실행 시 컨텍스트 식별자 전달. |
| `Contexts/UIContentContext.h` | `FUIContentContext` | 명령 실행 시 데이터 컨텍스트 (선택된 객체 등). |

`MapAction(Cmd, FUIAction, FUIActionContext)` (L106) 에서 컨텍스트 함께 전달 — 같은 명령을 여러 객체에 다른 동작으로.

### 2.8 드래그 앤 드롭 (`UICommandDragDropOp.h`)

| 심볼 | 역할 |
|------|------|
| `FUICommandDragDropOp` | 명령 자체를 드래그 — 사용자가 툴바 항목을 드래그해 다른 위치로 옮길 때. 에디터 커스터마이즈 UI 에서 사용. |

---

## 3. 자주 쓰는 API

### 3.1 명령 묶음 정의 (`FMyToolCommands.h/.cpp`)

```cpp
// FMyToolCommands.h
#pragma once
#include "Framework/Commands/Commands.h"
#include "Styling/AppStyle.h"

class FMyToolCommands : public TCommands<FMyToolCommands>
{
public:
    FMyToolCommands()
    : TCommands<FMyToolCommands>(
        TEXT("MyTool"),                                                   // 컨텍스트 이름 (전역 유일)
        NSLOCTEXT("Contexts", "MyTool", "My Tool"),                       // 사용자 표시명
        NAME_None,                                                        // 부모 컨텍스트
        FAppStyle::GetAppStyleSetName())                                  // 아이콘 가져올 스타일셋
    {}

    virtual void RegisterCommands() override;

    TSharedPtr<FUICommandInfo> Open;
    TSharedPtr<FUICommandInfo> Save;
    TSharedPtr<FUICommandInfo> Build;
    TSharedPtr<FUICommandInfo> ToggleAdvanced;
};

// FMyToolCommands.cpp
#include "FMyToolCommands.h"

#define LOCTEXT_NAMESPACE "FMyToolCommands"

void FMyToolCommands::RegisterCommands()
{
    UI_COMMAND(Open,
        "Open",
        "Open the My Tool window",
        EUserInterfaceActionType::Button,
        FInputChord(EKeys::T, /*Shift=*/false, /*Ctrl=*/true, /*Alt=*/true, /*Cmd=*/false));

    UI_COMMAND(Save,
        "Save",
        "Save current state",
        EUserInterfaceActionType::Button,
        FInputChord(EKeys::S, false, true, false, false));                // Ctrl+S

    UI_COMMAND(Build,
        "Build",
        "Build the project",
        EUserInterfaceActionType::Button,
        FInputChord(EKeys::F7));                                          // F7

    UI_COMMAND(ToggleAdvanced,
        "Show Advanced",
        "Toggle advanced settings visibility",
        EUserInterfaceActionType::ToggleButton,                           // 토글
        FInputChord());                                                   // 기본 chord 없음
}

#undef LOCTEXT_NAMESPACE
```

### 3.2 모듈에서 등록·해제

```cpp
// FMyToolModule.cpp
void FMyToolModule::StartupModule()
{
#if WITH_EDITOR
    FMyToolCommands::Register();          // 싱글턴 인스턴스 생성 + RegisterCommands() 자동 호출
    // ...
#endif
}

void FMyToolModule::ShutdownModule()
{
#if WITH_EDITOR
    FMyToolCommands::Unregister();        // FInputBindingManager에서 제거
#endif
}
```

### 3.3 명령 → 액션 매핑 (`FUICommandList`)

```cpp
// 보통 도구 패널 / 툴 모듈 멤버에 보유
TSharedPtr<FUICommandList> Cmds = MakeShared<FUICommandList>();

// 단순 실행
Cmds->MapAction(                                                          // L32
    FMyToolCommands::Get().Open,
    FExecuteAction::CreateLambda([]() {
        FGlobalTabmanager::Get()->TryInvokeTab(FName("MyToolTab"));
    })
);

// 실행 + 가능 검증
Cmds->MapAction(                                                          // L42
    FMyToolCommands::Get().Save,
    FExecuteAction::CreateRaw(this, &FMyToolModule::OnSave),
    FCanExecuteAction::CreateLambda([this]() { return bIsDirty; })
);

// 토글 (Checked 상태 반환)
Cmds->MapAction(                                                          // L53
    FMyToolCommands::Get().ToggleAdvanced,
    FExecuteAction::CreateLambda([this]() { bAdvanced = !bAdvanced; }),
    FCanExecuteAction(),
    FIsActionChecked::CreateLambda([this]() { return bAdvanced; })
);

// FUIAction 직접
FUIAction Action(
    FExecuteAction::CreateRaw(this, &FMyToolModule::OnBuild),
    FCanExecuteAction::CreateLambda([this]() { return !bBuilding; }),
    FGetActionCheckState::CreateLambda([this]() {
        return bBuilding ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
    }),
    FIsActionButtonVisible::CreateLambda([]() { return true; }),
    EUIActionRepeatMode::RepeatDisabled
);
Cmds->MapAction(FMyToolCommands::Get().Build, Action);                    // L96
```

### 3.4 키 이벤트 → 명령 실행 (위젯에 라우팅)

```cpp
class SMyToolPanel : public SCompoundWidget
{
public:
    void Construct(const FArguments& InArgs) { Cmds = InArgs._CommandList; }

    virtual FReply OnKeyDown(const FGeometry&, const FKeyEvent& KeyEvent) override
    {
        // CommandList 가 명령 자동 실행 (chord 일치하는 게 있으면)
        if (Cmds.IsValid() && Cmds->ProcessCommandBindings(KeyEvent))     // L170
        {
            return FReply::Handled();
        }
        return FReply::Unhandled();
    }

    virtual bool SupportsKeyboardFocus() const override { return true; }   // 포커스 받아야 키 이벤트 옴

private:
    TSharedPtr<FUICommandList> Cmds;
};
```

### 3.5 메뉴/툴바와 결합 (Menu sub-skill 과 짝)

```cpp
// FMenuBuilder/FToolBarBuilder 생성자에 CommandList 전달
FMenuBuilder Menu(/*bShouldClose=*/true, Cmds);
Menu.AddMenuEntry(FMyToolCommands::Get().Save);     // 라벨/아이콘/단축키 자동, MapAction 한 액션 자동 호출

FSlimHorizontalToolBarBuilder Tb(Cmds, FMultiBoxCustomization::None);
Tb.AddToolBarButton(FMyToolCommands::Get().Build);
```

자세한 빌더 패턴은 [`Menu/`](../Menu/SKILL.md).

### 3.6 표준 명령 (`FGenericCommands`) 활용

```cpp
Cmds->MapAction(FGenericCommands::Get().Cut,    FExecuteAction::CreateRaw(this, &SMyTool::OnCut));
Cmds->MapAction(FGenericCommands::Get().Copy,   FExecuteAction::CreateRaw(this, &SMyTool::OnCopy));
Cmds->MapAction(FGenericCommands::Get().Paste,  FExecuteAction::CreateRaw(this, &SMyTool::OnPaste),
                FCanExecuteAction::CreateLambda([this]() { return CanPaste(); }));
Cmds->MapAction(FGenericCommands::Get().Undo,   FExecuteAction::CreateRaw(this, &SMyTool::OnUndo));
Cmds->MapAction(FGenericCommands::Get().Delete, FExecuteAction::CreateRaw(this, &SMyTool::OnDelete));
```

엔진이 자동 등록 — `Register()` 불필요. 모든 에디터 도구가 표준 단축키(Ctrl+C/V/X/Z 등) 일관성 유지.

### 3.7 사용자 커스터마이즈 단축키

```cpp
// 사용자가 에디터의 Editor Preferences > Keyboard Shortcuts 에서 chord 변경 가능
// FInputBindingManager 가 자동으로 ini 에 저장·복원
// 코드는 항상 FUICommandInfo 만 참조하면 됨 — 실제 chord 는 사용자 설정 자동 반영

// 현재 chord 조회 (디스플레이용)
const TSharedPtr<const FInputChord> Active =
    FMyToolCommands::Get().Save->GetActiveChord(EMultipleKeyBindingIndex::Primary);
FText Display = Active.IsValid() ? Active->GetInputText() : FText::GetEmpty();
```

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 TCommands<T> — 1개 (필수)

```cpp
virtual void RegisterCommands() override;       // UI_COMMAND 매크로로 명령 정의
```

### 4.2 FUICommandList — 드물게 override

```cpp
virtual void   MapAction(...) override;         // L96, L106 — 매핑 정책 커스텀
virtual bool   ExecuteAction(const TSharedRef<const FUICommandInfo>&) const override;  // L133
```

대부분 그대로 사용. 커스텀 라우팅이 필요한 경우만.

### 4.3 FBindingContext — TCommands 의 베이스

`GetContextName()` / `GetContextDesc()` / `GetStyleSetName()` — TCommands 생성자 인자로 자동 설정.

---

## 5. 인하우스 툴 — 명령·메뉴·툴바·도킹 통합 골격

```cpp
// FMyToolModule.cpp 전체 흐름
void FMyToolModule::StartupModule()
{
#if WITH_EDITOR
    // 1) 명령 등록
    FMyToolCommands::Register();

    // 2) 명령 → 액션 매핑 (모듈 레벨 — 메인 메뉴용)
    GlobalCmds = MakeShared<FUICommandList>();
    GlobalCmds->MapAction(
        FMyToolCommands::Get().Open,
        FExecuteAction::CreateLambda([]() {
            FGlobalTabmanager::Get()->TryInvokeTab(FName("MyToolTab"));
        })
    );

    // 3) 메인 메뉴 Extender (Menu sub-skill 패턴)
    TSharedPtr<FExtender> Ext = MakeShared<FExtender>();
    Ext->AddMenuExtension("WindowLayout", EExtensionHook::After, GlobalCmds,
        FMenuExtensionDelegate::CreateLambda([](FMenuBuilder& Menu) {
            Menu.AddMenuEntry(FMyToolCommands::Get().Open);     // 자동으로 라벨/아이콘/단축키 표시
        }));
    FLevelEditorModule& LE = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
    LE.GetMenuExtensibilityManager()->AddExtender(Ext);
    MenuExtender = Ext;

    // 4) 도킹 탭 등록 (Docking sub-skill)
    FGlobalTabmanager::Get()->RegisterNomadTabSpawner(MyTabId,
        FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnTab))
        .SetDisplayName(LOCTEXT("MyTool", "My Tool"));
#endif
}

TSharedRef<SDockTab> FMyToolModule::SpawnTab(const FSpawnTabArgs& Args)
{
    // 탭 패널마다 별도 CommandList — 패널 내부 단축키
    TSharedRef<FUICommandList> PanelCmds = MakeShared<FUICommandList>();
    PanelCmds->MapAction(FMyToolCommands::Get().Save,
                         FExecuteAction::CreateRaw(this, &FMyToolModule::OnSave),
                         FCanExecuteAction::CreateLambda([this]() { return bDirty; }));
    PanelCmds->MapAction(FMyToolCommands::Get().Build,
                         FExecuteAction::CreateRaw(this, &FMyToolModule::OnBuild));

    // 표준 명령도 추가
    PanelCmds->MapAction(FGenericCommands::Get().Undo,
                         FExecuteAction::CreateRaw(this, &FMyToolModule::OnUndo));

    return SNew(SDockTab).TabRole(ETabRole::NomadTab)
    [
        SNew(SMyToolPanel).CommandList(PanelCmds)        // 패널이 OnKeyDown에서 ProcessCommandBindings
    ];
}

void FMyToolModule::ShutdownModule()
{
#if WITH_EDITOR
    if (FSlateApplication::IsInitialized())
    {
        FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(MyTabId);
        if (MenuExtender.IsValid())
        {
            FLevelEditorModule& LE = FModuleManager::GetModuleChecked<FLevelEditorModule>("LevelEditor");
            LE.GetMenuExtensibilityManager()->RemoveExtender(MenuExtender);
        }
    }
    GlobalCmds.Reset();
    MenuExtender.Reset();
    FMyToolCommands::Unregister();
#endif
}
```

---

## 6. 운영 가이드 / 함정

1. **`UI_COMMAND` 는 `LOCTEXT_NAMESPACE` 필수** — `.cpp` 상단에 `#define LOCTEXT_NAMESPACE "FMyToolCommands"`, 끝에 `#undef LOCTEXT_NAMESPACE`. 누락 시 컴파일 에러.
2. **`TCommands<T>` 컨텍스트 이름 충돌** — `TEXT("MyTool")` 같은 일반명 피하고 `TEXT("MyCompany.MyTool")` 권장. 전역 유일.
3. **`Register()` / `Unregister()` 짝** — `StartupModule` / `ShutdownModule` 둘 다 명시. hot-reload 시 누락하면 댕글링 인스턴스.
4. **`FUICommandList` 의 라이프사이클** — 위젯/탭마다 별도 인스턴스. 모듈 레벨 + 패널 레벨로 분리하는 패턴 권장.
5. **`ProcessCommandBindings` 호출 위치** — 위젯의 `OnKeyDown` 에서. `SupportsKeyboardFocus() = true` 도 필요 (포커스 받아야 키 이벤트 도착).
6. **`Append` 로 부모-자식 매핑 합치기** — 한 패널의 CommandList 가 부모 도구의 CommandList 를 `Append` 하면 부모 단축키도 자식에서 동작.
7. **표준 명령은 직접 Register 금지** — `FGenericCommands` 는 엔진이 자동. `FMyToolCommands::Register()` 안에서 `FGenericCommands::Register()` 호출 X.
8. **chord 충돌** — 같은 chord 를 여러 명령에 바인딩하면 마지막 우선. `FInputBindingManager` 가 충돌 경고. 사용자 커스터마이즈 환경 고려.
9. **`EUIActionRepeatMode::RepeatEnabled`** — 키 holding 시 반복 실행. 줌·팬 같은 연속 동작에만. 일반 명령은 `RepeatDisabled` (기본).
10. **EnhancedInput 과 분리** — 게임 액션은 `EnhancedInput` (UE 5.x 게임 입력 표준). 본 sub-skill 은 에디터 도구 단축키. 두 시스템은 완전 별개 — 혼동 금지.

---

## 7. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

> **🚨 런타임/에디터 분리 원칙은 [`Slate/SKILL.md §8`](../SKILL.md#8--런타임--에디터-분리-원칙-인하우스-툴-묶음-공통-규약) 의무 규약.** `FUICommandList`/`FUICommandInfo` 자체는 런타임 컴파일 OK이지만, 단축키 시스템 통합·`FInputBindingManager` ini 저장·표준 명령(Cut/Copy/Paste 등) 사용은 에디터 컨텍스트에서만 의미. 모든 호출을 `#if WITH_EDITOR` 가드 안 + 에디터 전용 모듈에 분리.

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `TCommands<T>` 클래스 자체 🛠 (실용) | Commands.h | (런타임 컴파일 OK) | 게임 빌드는 `EnhancedInput` 사용 권장. |
| `FInputBindingManager` 사용자 ini 저장 🛠 | InputBindingManager.h | 에디터 ini | `EditorPerProjectIni` 의존 — 게임 빌드에 ini 없음. |
| `FGenericCommands` 자동 등록 🛠 | GenericCommands.h | 에디터 부트스트랩 | 게임 빌드에서는 등록 안 됨. |
| `FUICommandDragDropOp` 🛠 | UICommandDragDropOp.h | 에디터 커스터마이즈 UI | Editor Preferences 키바인딩 화면. |
| `EditPreferences > Keyboard Shortcuts` 🛠 | (UI) | 에디터 | 사용자 커스터마이즈 진입점. |
| `Contexts/UIIdentifierContext`/`UIContentContext` 🛠 | Contexts/ | 에디터 통합 | `UToolMenus` 와 짝. |

---

## 8. 관련 sub-skill

- [`Menu/`](../Menu/SKILL.md) — `FMenuBuilder`/`FToolBarBuilder` 가 `FUICommandList` 와 결합
- [`EditorApplication/`](../EditorApplication/SKILL.md) — `FGlobalTabmanager::Get()->TryInvokeTab(...)` 가 명령 액션 타깃
- [`Docking/`](../Docking/SKILL.md) — `FTabCommands` (탭 닫기 단축키) 가 같은 패턴
- [`../../InputCore/`](../../InputCore/SKILL.md) — `FKey`/`EKeys` 식별자 (FInputChord 의 키 부분)
- [`../../SlateCore/Input/`](../../SlateCore/references/Input.md) — `FKeyEvent`/`FModifierKeysState` (ProcessCommandBindings 입력)
