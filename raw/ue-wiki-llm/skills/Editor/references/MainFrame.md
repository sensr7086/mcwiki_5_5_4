---
name: mainframe-main
description: 🛠 MainFrame 모듈 - IMainFrameModule + OnMainFrameCreationFinished + SetApplicationTitleOverride + MainFrame.MainMenu.* 표준 메뉴.
---

# MainFrame Module 🛠

> **모듈**: `Engine/Source/Editor/MainFrame/` (Editor 전용)
> **사이즈**: Public 5 헤더
> **카테고리**: `[Slate]` 인하우스 툴 (🛠 에디터 전용)

---

## 1. 개요

UE 에디터의 **메인 윈도우** 와 그 메뉴/타이틀/단축키 통합. 에디터 시작 시 SWindow 1개를 생성하고 그 안에 LevelEditor·ContentBrowser·기타 도크 탭을 호스팅. 인하우스 툴 작성 시 직접 다루는 일은 드물지만 **메인 메뉴 확장 / 윈도우 타이틀 변경 / 종료 콜백** 등에 사용.

---

## 2. 핵심 헤더

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `MainFrame.h` | `FMainFrame` (Private) | 메인 프레임 로직 |
| `Interfaces/IMainFrameModule.h` | `IMainFrameModule` (L33) | 모듈 인터페이스 — 글로벌 진입 |
| `Interfaces/IEditorMainFrameProvider.h` | `IEditorMainFrameProvider` (L42) | 다중 메인 프레임 (가상) |
| `Settings/` | (서브 디렉토리) | 메인 프레임 설정 |

---

## 3. IMainFrameModule (글로벌 진입)

### 3.1 핵심 API (IMainFrameModule.h L33)

| API | 라인 | 의미 |
|-----|------|------|
| `void CreateDefaultMainFrame(const bool bStartImmersive, const bool bStartPIE)` | L44 | 기본 메인 프레임 생성 (에디터 시작 시 1회) |
| `void RecreateDefaultMainFrame(const bool bStartImmersive, const bool bStartPIE)` | L53 | 재생성 |
| `bool IsRecreatingDefaultMainFrame() const` | L58 | 재생성 중인지 |
| `TSharedRef<SWidget> MakeMainMenu(const TSharedPtr<FTabManager>&, const FName MenuName, FToolMenuContext&) const` | L70 | 메뉴 위젯 생성 |
| `TSharedRef<SWidget> MakeDeveloperTools(const TArray<FMainFrameDeveloperTool>&) const` | L89 | 개발자 도구 위젯 (FPS/Memory 등) |
| `bool IsWindowInitialized() const` | L96 | 메인 윈도우 초기화 완료? |
| `TSharedPtr<SWindow> GetParentWindow() const` | L103 | 메인 SWindow |
| `void SetMainTab(const TSharedRef<SDockTab>&)` | L110 | 메인 탭 |
| `void RequestCloseEditor()` | L126 | 에디터 종료 요청 |
| `void SetLevelNameForWindowTitle(const FString& InLevelFileName)` | L133 | 윈도우 제목 — 레벨명 |
| `void SetApplicationTitleOverride(const FText& NewOverriddenApplicationTitle)` | L140 | 제목 오버라이드 |
| `FString GetLoadedLevelName() const` | L147 | 현재 레벨 |
| `TSharedRef<FUICommandList>& GetMainFrameCommandBindings()` | L149 | 메인 프레임 단축키 |
| `FMainMRUFavoritesList* GetMRUFavoritesList() const` | L156 | MRU/즐겨찾기 |
| `FText GetApplicationTitle(const bool bIncludeGameName) const` | L165 | 제목 텍스트 |
| `void ShowAboutWindow() const` | L170 | About 윈도우 |
| `void EnableTabClosedDelegate()` / `DisableTabClosedDelegate()` | L115 / L120 | 탭 닫힘 콜백 토글 |

### 3.2 콜백 / 이벤트

| 델리게이트 | 라인 | 의미 |
|-----------|------|------|
| `FMainFrameCreationFinishedEvent& OnMainFrameCreationFinished()` | L176 | 메인 프레임 생성 완료 (에디터 시작 직후 무거운 작업 등록 위치) |
| `FMainFrameSDKNotInstalled& OnMainFrameSDKNotInstalled()` | L182 | SDK 미설치 알림 |
| `FMainFrameRequestResource& OnMainFrameRequestResource()` | L189 | 리소스 요청 |

### 3.3 사용 패턴

```cpp
#if WITH_EDITOR
IMainFrameModule& MainFrame = FModuleManager::LoadModuleChecked<IMainFrameModule>("MainFrame");

// 메인 프레임 생성 완료 후 작업
MainFrame.OnMainFrameCreationFinished().AddLambda(
    [](TSharedPtr<SWindow> InRootWindow, bool bIsRunningStartupDialog)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_OnMainFrameReady);
        // 메인 윈도우가 만들어진 뒤에 무거운 작업 (예: 메인 메뉴에 추가, 알림 표시)
        if (bIsRunningStartupDialog) return;
        UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("MainFrame.MainMenu.Tools");
        // ...
    });

// 윈도우 제목 변경
MainFrame.SetApplicationTitleOverride(FText::FromString(TEXT("MyGame Editor")));

// 종료 요청 (저장 다이얼로그 등 트리거)
MainFrame.RequestCloseEditor();
#endif
```

---

## 4. IEditorMainFrameProvider (다중 메인 프레임 — 가상)

`Interfaces/IEditorMainFrameProvider.h` L42 — `IModularFeature` 자손. 표준 메인 프레임 외에 **사용자 정의 메인 프레임** 을 제공할 때 구현.

| 시그니처 | 라인 | 의미 |
|----------|------|------|
| `virtual bool IsRequestingMainFrameControl() const = 0` | L59 | 컨트롤 요청? |
| `virtual FMainFrameWindowOverrides GetDesiredWindowConfiguration() const = 0` | L65 | 윈도우 설정 |
| `virtual TSharedRef<SWidget> CreateMainFrameContentWidget() const = 0` | L72 | 메인 콘텐츠 |

거의 모든 인하우스 툴 작업에서는 사용 안 함. 표준 메인 프레임으로 충분.

---

## 5. 메인 메뉴 확장 (가장 자주)

`IMainFrameModule::MakeMainMenu` 가 호출하는 메뉴는 **`UToolMenus`** 로 등록 ([`ToolMenus`](../ToolMenus/SKILL.md)). 표준 메뉴 이름:

| 이름 | 위치 |
|------|------|
| `MainFrame.MainMenu.File` | File 메뉴 |
| `MainFrame.MainMenu.Edit` | Edit |
| `MainFrame.MainMenu.Window` | Window |
| `MainFrame.MainMenu.Tools` | Tools |
| `MainFrame.MainMenu.Help` | Help |
| `MainFrame.MainTabMenu` | 메인 탭 (워크스페이스 메뉴) |

```cpp
UToolMenu* ToolsMenu = UToolMenus::Get()->ExtendMenu("MainFrame.MainMenu.Tools");
FToolMenuSection& Section = ToolsMenu->FindOrAddSection("MyToolsSection");
Section.AddMenuEntry(...);
```

---

## 6. 단축키 등록 (메인 프레임 단축키)

```cpp
TSharedRef<FUICommandList>& Bindings = MainFrame.GetMainFrameCommandBindings();
Bindings->MapAction(MyCommandInfo, FExecuteAction::CreateLambda([]()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_MainFrameShortcut);
    // ...
}));
```

자세한 TCommands<T> — [`Slate/Commands`](../Slate/references/Commands.md).

---

## 7. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `IMainFrameModule::*` | (override 시 자체 처리) | pure virtual 다수 — 직접 구현 안 함 |
| `IEditorMainFrameProvider::*` | (override 시 자체 처리) | 인하우스 메인 프레임 시 |
| `IModuleInterface::StartupModule` (자손) | (override 시 등록) | OnMainFrameCreationFinished 등록 위치 |

---

## 8. 함정

| 함정 | 회피 |
|------|------|
| `OnMainFrameCreationFinished` 늦게 등록 — 이미 발화 후 | 모듈 StartupModule 안에서 등록 |
| `bIsRunningStartupDialog` 검사 누락 | 시작 다이얼로그 모드에서는 메뉴 없음 — 검사 의무 |
| `RequestCloseEditor` 직접 호출 후 저장 안 함 | 닫기 다이얼로그가 자동 트리거되지만 사용자 정의 검사 시 `OnRequestClose` 람다 등록 |
| `SetApplicationTitleOverride` 매 프레임 호출 | 변경 시에만 호출 |
| 메인 프레임 미초기화 시 `GetParentWindow` 사용 | `IsWindowInitialized` 검사 필수 |
| 람다·콜백 스코프 누락 | [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) |
| 게임 모듈에서 의존 | 4단 분리 |

---

## 9. 에디터 전용 🛠

전체 모듈 에디터 빌드 전용. 4단 분리 — [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

---

## 10. 관련 sub-skill

- [`ToolMenus`](../ToolMenus/SKILL.md) — `MainFrame.MainMenu.*` 표준 메뉴 이름 + 등록
- [`Slate/Commands`](../Slate/references/Commands.md) — `GetMainFrameCommandBindings`
- [`Slate/Docking`](../Slate/references/Docking.md) — FTabManager / FGlobalTabmanager
- [`Slate/EditorApplication`](../Slate/references/EditorApplication.md) — FSlateApplication 베이스
- [`LevelEditor`](../LevelEditor/SKILL.md) — 메인 프레임 안에 호스트되는 가장 큰 도구
- [`UnrealEd/AssetEditorToolkit`](../UnrealEd/AssetEditorToolkit/SKILL.md) — 별도 윈도우 (메인 프레임 외)
- 교차: [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) (OnMainFrameCreationFinished 람다 스코프)
