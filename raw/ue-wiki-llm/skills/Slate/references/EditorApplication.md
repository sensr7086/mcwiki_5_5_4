---
name: slate-editorapplication
description: 🛠 SDockTab + SWindow + 에디터 전용 위젯 묶음.
---

# Slate / EditorApplication 🛠

> 부모 모듈: [`Slate`](../SKILL.md) · UE 5.7.4
> 다루는 영역: **인하우스 툴 묶음의 진입점** — `FSlateApplication` 의 에디터/툴 측면 — 정적 진입점 + 매 프레임 Tick 흐름 + `IInputProcessor` 전역 후크 + 윈도우 관리 + `FGlobalTabmanager` 진입
> 🛠 본 sub-skill 은 사실상 에디터·인하우스 툴·standalone 툴 빌드 한정.
> 관련 sub-skill: [`Application/`](../Application/SKILL.md), [`Docking/`](../Docking/SKILL.md), [`Menu/`](../Menu/SKILL.md), [`Commands/`](../Commands/SKILL.md), [`../../SlateCore/Application/`](../../SlateCore/references/Application.md)

---

## 1. 개요

`FSlateApplication` 은 한 프로세스에 **하나만** 존재하는 Slate UI의 루트. 게임/에디터/standalone 툴 빌드가 모두 같은 클래스를 사용하지만, **인하우스 툴** 작성 시 만지는 부분이 따로 있다:

```
FSlateApplication (Slate 모듈)
  ├─ static Create / InitializeAsStandaloneApplication / Shutdown / InitHighDPI / InitializeCoreStyle
  ├─ Tick / PumpMessages / TickPlatform / TickAndDrawWidgets / DrawWindows
  ├─ AddWindow / AddModalWindow / AddWindowAsNativeChild
  ├─ RegisterInputPreProcessor (전역 입력 후크)
  ├─ FGlobalTabmanager::Get() (도킹 진입점)
  └─ FSlateUser 관리 (사용자별 입력 컨텍스트)
```

- **게임 빌드**: 엔진 부트스트랩이 `Initialize` 호출, 게임 코드는 `Get()` 으로 접근만.
- **에디터 빌드**: `UnrealEd` 모듈이 메인 윈도우 + 도킹 시스템을 셋업, 각 툴이 `RegisterNomadTabSpawner` 로 진입.
- **Standalone 인하우스 툴**: `InitializeAsStandaloneApplication` 으로 직접 부트스트랩 (`UnrealHeaderTool` 같은 툴 패턴).

본 sub-skill은 **인하우스 툴 시점**에서 위 흐름을 본다.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Framework/Application/SlateApplication.h` | `class FSlateApplication : FSlateApplicationBase, FGenericApplicationMessageHandler` (L249) | **본체**. 두 베이스를 다중 상속 — `SlateApplicationBase` (Slate 측 추상) + `FGenericApplicationMessageHandler` (OS 메시지 수신). |
| `Public/Framework/Application/IInputProcessor.h` | `class IInputProcessor` (L17) | **전역 입력 후크** 인터페이스. `Tick`/`HandleKeyDown`/`HandleMouseMove` 등 가상 함수. 어떤 위젯보다 먼저 입력 받음. |
| `Public/Framework/Application/SlateUser.h` | `class FSlateUser : TSharedFromThis<FSlateUser>` (L40) | 사용자별 입력 컨텍스트 (포커스/캡처/커서). |
| `Public/Framework/Application/AnalogCursor.h` | `class FAnalogCursor : IInputProcessor` | 게임패드 → 가상 마우스 커서 변환기. |
| `Public/Framework/Application/NavigationConfig.h` | `class FNavigationConfig` (L60), `FNullNavigationConfig` (L143), `FTwinStickNavigationConfig` (L155) | UI 내비게이션 정책. |
| `Public/Framework/Application/MenuStack.h` | `class FMenuStack` (L72), `struct FPopupTransitionEffect` (L30) | 팝업 메뉴 스택. |
| `Public/Framework/Application/IMenu.h` | `class IMenu` (L14), `class IMenuHost` (L29) | 활성 메뉴 인터페이스. |
| `Public/Framework/Application/SWindowTitleBar.h` | `SWindowTitleBar` | 커스텀 타이틀바. |
| `Public/Framework/Application/IPlatformTextField.h` | `IPlatformTextField` | OS 가상 키보드 인터페이스 (모바일 IME). |
| `Public/Framework/Application/IWidgetReflector.h` 🛠 | `IWidgetReflector` | Widget Reflector 인터페이스. |
| `Public/Framework/Application/GestureDetector.h` | `FGestureDetector` | 멀티 터치 제스처 감지 (Pinch/Pan/Rotate). |

---

## 3. 정적 진입점 / 라이프사이클

### 3.1 Application 부트스트랩

```cpp
// === A. 엔진 통합 (게임/에디터 빌드) ===
// 보통 엔진이 호출 — 사용자 코드는 안 씀
FSlateApplication::Create();                                                  // L294
// 또는 GenericApplication 직접 주입:
FSlateApplication::Create(InPlatformApplication);                             // L295

FSlateApplication::InitializeCoreStyle();                                     // L301 — 기본 스타일셋 등록

// === B. Standalone 툴 (예: UnrealHeaderTool 같은 별도 exe) ===
TSharedRef<FSlateApplication> App =
    FSlateApplication::InitializeAsStandaloneApplication(MyRenderer);          // L297
// 또는 GenericApplication 도 직접:
TSharedRef<FSlateApplication> App =
    FSlateApplication::InitializeAsStandaloneApplication(MyRenderer, MyPlatformApp);  // L299

// === High-DPI 활성 ===
FSlateApplication::InitHighDPI(/*bForceEnable=*/false);                        // L332
// 메인 호출 전이어야 효과 — 보통 엔진 진입 직후

// === 종료 ===
FSlateApplication::Shutdown(/*bShutdownPlatform=*/true);                       // L326
```

### 3.2 접근

```cpp
if (FSlateApplication::IsInitialized())                                        // L307
{
    FSlateApplication& App = FSlateApplication::Get();                         // L317 — 메인 스레드 / Slate 스레드 / 비동기 로딩 스레드만 안전
    // ...
}
```

`Get()` 내부에 `check( IsInGameThread() || IsInSlateThread() || IsInAsyncLoadingThread() || IsInParallelLoadingThread() )` 가 박혀 있다. 그 외 스레드에서 호출 시 크래시.

---

## 4. 매 프레임 Tick 흐름 (인하우스 툴 관점)

`FSlateApplication::Tick(ESlateTickType)` 가 매 프레임 호출되며 다음을 수행:

```
SlateApplication::Tick(TickType)                      // L394
   ↓
TickTime()                                            // L1201 — DeltaTime 갱신
   ↓
TickPlatform(DeltaTime)                               // L1206
   ↓ PumpMessages()                                   // L400 — OS 메시지 루프
   ↓ FGenericApplication::PollGameDeviceState
   ↓ MessageHandler 호출 → Process*Event(...)         // L1256~1339
   ↓
   ↓ IInputProcessor::Tick / Handle*Event              // 전역 후크 (위젯보다 먼저)
   ↓
TickAndDrawWidgets(DeltaTime)                         // L1211
   ↓ Widget Tick / ActiveTimer 콜백
   ↓ DrawPrepass(window)                              // 사이즈 캐시
   ↓ DrawWindows() / PrivateDrawWindows()             // 페인트 + 렌더 제출
   ↓
ThrottleApplicationBasedOnMouseMovement()             // 자동 throttle
```

`ESlateTickType` (Time / Platform / Widgets / All) 로 단계별 호출 가능 — 인하우스 툴이 자체 메인 루프 가질 때 활용.

### 4.1 Standalone 툴 메인 루프 골격

```cpp
int main()
{
    // 1) Slate 부트스트랩
    GEngineLoop.PreInit(...);
    TSharedPtr<FSlateRenderer> Renderer = FModuleManager::Get().LoadModuleChecked<ISlateRHIRendererModule>("SlateRHIRenderer").CreateSlateRHIRenderer();
    auto App = FSlateApplication::InitializeAsStandaloneApplication(Renderer.ToSharedRef());

    // 2) 윈도우 + 컨텐츠 만들기
    TSharedRef<SWindow> W = SNew(SWindow).Title(LOCTEXT("MyTool", "My Tool"))
                                          .ClientSize(FVector2D(1280, 720));
    App->AddWindow(W);
    W->SetContent(SNew(SVerticalBox) /* tool UI */);

    // 3) 메인 루프
    while (!IsEngineExitRequested())
    {
        BeginExitIfRequested();
        FSlateApplication::Get().PumpMessages();
        FSlateApplication::Get().Tick();
        FCoreDelegates::OnEndFrame.Broadcast();
        FSlateApplication::Get().ThrottleApplicationBasedOnMouseMovement();
        FStats::AdvanceFrame(false);
    }

    // 4) 종료
    FSlateApplication::Shutdown();
    return 0;
}
```

(`UnrealHeaderTool`/`SlateViewer` 같은 standalone 툴이 위 패턴.)

---

## 5. 윈도우 관리

### 5.1 윈도우 추가 패턴

```cpp
// === 일반 윈도우 ===
TSharedRef<SWindow> W = SNew(SWindow)
    .Title(LOCTEXT("Edit", "Edit Properties"))
    .ClientSize(FVector2D(800, 600))
    .SupportsMaximize(true)
    .SupportsMinimize(true)
    [ /* content */ ];

FSlateApplication::Get().AddWindow(W, /*bShowImmediately=*/true);              // L1576

// === 모달 윈도우 (다른 입력 차단) ===
if (FSlateApplication::Get().CanAddModalWindow())                              // L403
{
    FSlateApplication::Get().AddModalWindow(W, ParentWidget,
                                             /*bSlowTaskWindow=*/false);       // L428
    // 모달 종료까지 블로킹
}

// === 부모 윈도우의 자식 (네이티브 차일드) ===
FSlateApplication::Get().AddWindowAsNativeChild(W, ParentWindow);              // L446
```

### 5.2 윈도우 검색

```cpp
TSharedPtr<SWindow> Top = FSlateApplication::Get().GetActiveTopLevelRegularWindow();
const auto& All = FSlateApplication::Get().GetTopLevelWindows();
TSharedPtr<SWindow> Owner = FSlateApplication::Get().FindWidgetWindow(MyWidget.ToSharedRef());
```

---

## 6. IInputProcessor — 전역 입력 후크

위젯 트리보다 **먼저** 입력을 가로채는 인터페이스. 디버그 오버레이·녹화·매크로 입력·게임패드 → 마우스 변환 등에 사용.

### 6.1 인터페이스 (`IInputProcessor.h:17`)

```cpp
class IInputProcessor
{
public:
    virtual void Tick(const float DeltaTime, FSlateApplication& SlateApp,
                      TSharedRef<ICursor> Cursor) = 0;

    virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent&)             { return false; }
    virtual bool HandleKeyUpEvent(FSlateApplication&, const FKeyEvent&)               { return false; }
    virtual bool HandleAnalogInputEvent(FSlateApplication&, const FAnalogInputEvent&) { return false; }
    virtual bool HandleMouseMoveEvent(FSlateApplication&, const FPointerEvent&)       { return false; }
    virtual bool HandleMouseButtonDownEvent(FSlateApplication&, const FPointerEvent&) { return false; }
    virtual bool HandleMouseButtonUpEvent(FSlateApplication&, const FPointerEvent&)   { return false; }
    virtual bool HandleMouseButtonDoubleClickEvent(FSlateApplication&, const FPointerEvent&) { return false; }
    virtual bool HandleMouseWheelOrGestureEvent(FSlateApplication&, const FPointerEvent&, const FPointerEvent*) { return false; }
    virtual bool HandleMotionDetectedEvent(FSlateApplication&, const FMotionEvent&)   { return false; }
};
```

`true` 반환 시 위젯 트리에 전달 안 함 (소비). `false` 면 통과.

### 6.2 등록

```cpp
TSharedPtr<FMyInputProcessor> Proc = MakeShared<FMyInputProcessor>();
FSlateApplication::Get().RegisterInputPreProcessor(Proc);                      // L1508
// 또는 우선순위 인덱스 지정 (낮을수록 먼저)
FSlateApplication::Get().RegisterInputPreProcessor(Proc, /*Index=*/0);         // L1516
// 또는 타입별 (Pre / Post 등)
FSlateApplication::Get().RegisterInputPreProcessor(Proc, EInputPreProcessorType::Pre);  // L1524

// 해제 (모듈 셧다운에서)
FSlateApplication::Get().UnregisterInputPreProcessor(Proc);                    // L1538
```

### 6.3 내장 사용처

| 클래스 | 용도 |
|--------|------|
| `FAnalogCursor` (`AnalogCursor.h`) | 게임패드 스틱 → 가상 마우스 커서 (콘솔/TV UI) |
| `FGestureDetector` (`GestureDetector.h`) | 멀티 터치 → Pinch/Pan/Rotate 변환 |

---

## 7. FGlobalTabmanager 진입 (도킹 시스템)

인하우스 툴이 도킹 가능한 탭으로 등록되는 표준 패턴 — 자세한 사용법은 [`Docking/`](../Docking/SKILL.md):

```cpp
TSharedRef<FGlobalTabmanager> Tm = FSlateApplication::Get().GetGlobalTabManager();   // L329 (정적 별칭으로도 노출)
// 또는 FGlobalTabmanager::Get()

Tm->RegisterNomadTabSpawner(MyTabId,
    FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnTab))
    .SetDisplayName(LOCTEXT("MyTool", "My Tool"))
    .SetGroup(WorkspaceMenu::GetMenuStructure().GetDeveloperToolsCategory());

// 호출 (메뉴/단축키에서)
Tm->TryInvokeTab(MyTabId);
```

---

## 8. FSlateUser 관리 (다중 사용자/입력 디바이스)

`FSlateApplication` 이 입력 디바이스마다 `FSlateUser` 를 자동 생성·관리:

```cpp
// 새 사용자 등록 (보통 자동, 가상 사용자 만들 때만 명시)
TSharedRef<FSlateUser> U = FSlateApplication::Get().RegisterNewUser(UserIndex,
                                                                     /*bIsVirtual=*/true);

// 입력 디바이스로부터 사용자 획득
TSharedRef<FSlateUser> U = FSlateApplication::Get().GetOrCreateUser(InputDeviceId);
TSharedRef<FSlateUser> U = FSlateApplication::Get().GetOrCreateUser(InputEvent);
```

`FPlatformUserId` 와 `FInputDeviceId` (Engine 모듈) 가 사용자/디바이스 식별. 자세한 사용자별 포커스/캡처는 [`Application/§3 FSlateUser`](../Application/SKILL.md) 와 [`SlateCore/Application/§5`](../../SlateCore/references/Application.md).

---

## 9. 가상 함수 / 오버라이드 포인트

### 9.1 IInputProcessor (구현 대상)

`IInputProcessor.h:17~` 의 8개 virtual — 위 §6.1 참조. 게임 코드/툴 코드가 직접 상속.

### 9.2 INotificationWidget / IMenu / IMenuHost

알림 위젯·메뉴 컨테이너 인터페이스 — [`Notifications/`](../Notifications/SKILL.md), [`Menu/`](../Menu/SKILL.md) 에서 다룸.

### 9.3 FSlateApplication 자체

`FSlateApplicationBase` 의 모든 추상 메서드 + `FGenericApplicationMessageHandler` 의 OS 메시지 콜백을 구현. 게임/툴 코드가 `FSlateApplication` 을 직접 상속하는 일은 없다.

---

## 10. 예제 — 툴 모듈에서 입력 후크 + 윈도우 + 탭 통합

```cpp
class FMyToolModule : public IModuleInterface
{
public:
    virtual void StartupModule() override
    {
#if WITH_EDITOR
        // 1) 전역 입력 후크 (디버그 오버레이 토글 등)
        InputProc = MakeShared<FMyInputProcessor>();
        FSlateApplication::Get().RegisterInputPreProcessor(InputProc);

        // 2) 도킹 탭 스포너 등록
        FGlobalTabmanager::Get()->RegisterNomadTabSpawner(MyTabId,
            FOnSpawnTab::CreateRaw(this, &FMyToolModule::SpawnTab))
            .SetDisplayName(LOCTEXT("MyTool", "My Tool"))
            .SetGroup(WorkspaceMenu::GetMenuStructure().GetDeveloperToolsCategory());
#endif
    }

    virtual void ShutdownModule() override
    {
#if WITH_EDITOR
        if (FSlateApplication::IsInitialized())
        {
            FSlateApplication::Get().UnregisterInputPreProcessor(InputProc);
            FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(MyTabId);
        }
#endif
        InputProc.Reset();
    }

    TSharedRef<SDockTab> SpawnTab(const FSpawnTabArgs& Args)
    {
        return SNew(SDockTab).TabRole(ETabRole::NomadTab)
        [
            SNew(SVerticalBox)
            // 메뉴/툴바: Menu/SKILL.md
            // 단축키:   Commands/SKILL.md
            // 알림:     Notifications/SKILL.md
            // 그래프:   GraphEditor/SKILL.md
        ];
    }

private:
    TSharedPtr<class IInputProcessor> InputProc;
    static const FName MyTabId;
};
```

---

## 11. 운영 가이드 / 함정 (인하우스 툴 시점)

1. **`Get()` 는 메인 스레드 한정** — `IsInGameThread() || IsInSlateThread() || ...` 만 통과. 워커/렌더 스레드에서 호출 금지 → 크래시.
2. **`IsInitialized()` 체크 필수** — 모듈 셧다운 순서가 꼬일 때 Slate가 먼저 사라질 수 있음. `Shutdown` 시 `IsInitialized` 후 접근.
3. **`AddModalWindow` 는 블로킹** — 입력을 가로채고 자체 메시지 루프 도림. 함수가 반환할 때까지 호출 측 로직 정지.
4. **InputPreProcessor 는 모든 위젯보다 먼저** — `true` 반환 시 위젯이 입력 못 받음. 위젯 정상 동작 막지 않게 신중히 (필요한 키만 소비).
5. **Standalone 툴 메인 루프** — `PumpMessages` + `Tick` 둘 다 호출. `Tick(All)` 이 내부에서 `TickPlatform` 도 호출하지만, OS 메시지를 더 자주 펌프하려면 별도 호출.
6. **HighDPI** — `InitHighDPI` 는 `Create` 보다 먼저. 그렇지 않으면 첫 윈도우가 잘못된 DPI로 생성.
7. **`FGlobalTabmanager` 가 없는 환경** — Standalone 툴에서 도킹 불필요하면 `AddWindow` 만으로 충분.
8. **모듈 셧다운에서 등록 해제 누락** — InputProcessor / TabSpawner / CommandList 등 모두 `ShutdownModule` 에서 명시적 해제. 누락 시 다음 hot-reload에서 댕글링.

---

## 12. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

> **🚨 런타임/에디터 분리 원칙은 [`Slate/SKILL.md §8`](../SKILL.md#8--런타임--에디터-분리-원칙-인하우스-툴-묶음-공통-규약) 의무 규약.** 본 sub-skill 의 모든 호출은 게임 .exe 에 들어가지 않게 4단 계층(모듈 분리 / uplugin Type / Build.cs 의존 분기 / `#if WITH_EDITOR` 가드)으로 보호.

본 sub-skill 은 사실상 전부 에디터/툴 빌드 한정. 다만 일부 메서드는 게임 빌드에도 컴파일됨:

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `IWidgetReflector` 🛠 | Application/IWidgetReflector.h | `WITH_SLATE_DEBUGGING` | Widget Reflector 진입점. |
| `AddModalWindow(...)` 일부 옵션 🛠 (실용) | Application/SlateApplication.h L428 | (런타임 시그니처 존재) | 게임 빌드에서 모달 사용은 드물고, 사용 시 입력 차단으로 게임플레이 멈춤. |
| Widget Reflector 진입 (`Slate.DebugWidgets` 콘솔) 🛠 | (cvar) | `WITH_SLATE_DEBUGGING` | 위젯 트리 시각화. |
| `FSlateApplication::SetFixedDeltaTime` 🛠 (실용) | Application/SlateApplication.h L1142 | (런타임 존재) | 자동화 테스트·녹화 — 게임에서 드뭄. |
| 메인 메뉴 / 툴바 통합 🛠 | (Menu/SKILL.md) | `WITH_EDITOR` | 에디터 메뉴 등록. |

게임 빌드에서 안전한 인하우스 툴 API는 `FSlateApplication::Get()` / `IsInitialized` / 윈도우 추가 / 입력 처리 정도. 도킹·메뉴·단축키 시스템은 코드 자체는 컴파일되지만 게임 UI에서 거의 사용 안 함.

---

## 13. 관련 sub-skill

- [`Application/`](../Application/SKILL.md) — 게임/에디터 공통 본체 (`FSlateUser` 등)
- [`Docking/`](../Docking/SKILL.md) — `FGlobalTabmanager`/`SDockTab` 자세히
- [`Menu/`](../Menu/SKILL.md) — `FMenuBuilder`/`FToolBarBuilder` 와 메인 메뉴 통합
- [`Commands/`](../Commands/SKILL.md) — `FUICommandList`/`FUICommandInfo` 단축키
- [`Notifications/`](../Notifications/SKILL.md) — `FSlateNotificationManager` 토스트
- [`GraphEditor/`](../GraphEditor/SKILL.