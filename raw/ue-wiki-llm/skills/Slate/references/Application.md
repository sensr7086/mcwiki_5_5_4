---
name: slate-application
description: SButton + SImage + SBox + SBorder + STextBlock + SOverlay - 게임 런타임 공용 위젯.
---

# Slate · Application sub-skill (게임 공통)

> **모듈**: Slate (Tier 3 — 게임/에디터 공통)
> **위치**: `Engine/Source/Runtime/Slate/Public/Framework/Application/` (11 헤더)
> **다루는 범위**: `FSlateApplication` 의 게임 측면 + `FSlateUser` + `IInputProcessor` + `MenuStack` + `NavigationConfig` + 게이패드/제스처 + `SWindowTitleBar`.

> **🛠 에디터 측면**: [`Slate/EditorApplication`](../EditorApplication/SKILL.md) 이 별도 — 인하우스 툴 묶음. 본 sub-skill은 **게임 빌드에서도 동작하는 부분** 중심.

---

## 1. 개요

UE 게임이 시작되면 `FSlateApplication::Create()` → 메인 루프에 통합 → `Tick`/`PumpMessages`/`DrawWindows`. 게임 UI(UMG/SWidget)가 모두 본 시스템 위에서 동작. 본 sub-skill은 *게임에서 직접 다루는 부분* 만 다룸 — Tick 진입점·SlateUser·IInputProcessor·NavigationConfig·MenuStack.

---

## 2. 핵심 헤더 (Slate/Public/Framework/Application/)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `SlateApplication.h` | `FSlateApplication` | 본체 (게임/에디터 공통) — 자세히 [`Slate/EditorApplication`](../EditorApplication/SKILL.md) §3 |
| `SlateUser.h` | `FSlateUser` | 사용자 (1명/멀티) — 포커스/캡처/마우스 |
| `IInputProcessor.h` | `IInputProcessor` (인터페이스) | 전역 입력 후크 |
| `MenuStack.h` | `FMenuStack` + `IMenu` | 팝업 메뉴 스택 |
| `IMenu.h` | `IMenu` 인터페이스 | 메뉴 인스턴스 |
| `NavigationConfig.h` | `FNavigationConfig` + 자손 | 게임패드/방향키 내비 |
| `AnalogCursor.h` | `FAnalogCursor` (`IInputProcessor` 자손) | 게임패드 → 마우스 커서 |
| `GestureDetector.h` | `FGestureDetector` | 터치 제스처 (Pinch/Pan) |
| `SWindowTitleBar.h` | `SWindowTitleBar` | 윈도우 타이틀 바 |
| `IPlatformTextField.h` | `IPlatformTextField` | OS 가상 키보드 |
| `IWidgetReflector.h` | `IWidgetReflector` 🛠 | Widget Reflector 인터페이스 (에디터 디버그) |

---

## 3. FSlateApplication 게임 측면

### 3.1 정적 진입 (게임/에디터 공통)

[`Slate/EditorApplication §3`](../EditorApplication/SKILL.md) 에서 deep dive — 본 sub-skill은 게임 측면만:

| API | 의미 |
|-----|------|
| `static FSlateApplication& Get()` | 싱글턴 (게임/에디터 공통) |
| `static bool IsInitialized()` | 초기화 여부 |
| `void Tick(ESlateTickType=All)` | 게임 메인 루프에서 자동 호출 |
| `void DrawWindows()` | 자동 호출 |
| `bool ProcessKeyDownEvent(FKeyEvent)` | 키 입력 (게임 input 시스템이 호출) |
| `bool ProcessMouseButtonDownEvent(...)` | 마우스 입력 |
| `void RegisterInputPreProcessor(TSharedPtr<IInputProcessor>, int32 Index=INDEX_NONE)` | 입력 후크 등록 (가장 자주) |
| `void UnregisterInputPreProcessor(TSharedPtr<IInputProcessor>)` | 해제 |

### 3.2 SWindow 관리

| API | 의미 |
|-----|------|
| `TSharedRef<SWindow> AddWindow(TSharedRef<SWindow>, bool bShowImmediately=true)` | 창 추가 |
| `void RequestDestroyWindow(TSharedRef<SWindow>)` | 닫기 요청 |
| `TSharedPtr<SWindow> GetActiveTopLevelWindow() const` | 현재 활성 창 |
| `TArray<TSharedRef<SWindow>> GetTopLevelWindows() const` | 모든 최상위 창 |

---

## 4. FSlateUser — 사용자 (멀티/스플릿스크린)

### 4.1 인터페이스 (SlateUser.h)

각 사용자(플레이어)별로 분리된 포커스/캡처/마우스 상태:

| API | 의미 |
|-----|------|
| `int32 GetUserIndex() const` | 사용자 ID |
| `TSharedPtr<SWidget> GetFocusedWidget() const` | 포커스 위젯 |
| `bool SetFocus(TSharedRef<SWidget>, EFocusCause=SetDirectly)` | 포커스 설정 |
| `void ClearFocus(EFocusCause=Cleared)` | 해제 |
| `bool HasMouseCapture() const` | 캡처 중? |
| `void ReleaseCapture()` | 캡처 해제 |
| `FVector2D GetCursorPosition() const` | 커서 위치 |
| `void SetCursorPosition(const FVector2D&)` | 위치 설정 |

### 4.2 사용

```cpp
TSharedRef<FSlateUser> User = FSlateApplication::Get().GetUser(0);    // 플레이어 0
User->SetFocus(MyWidget.ToSharedRef());

// 멀티플레이어 스플릿 — 각자 분리
for (int32 i = 0; i < 4; i++)
{
    if (TSharedPtr<FSlateUser> P = FSlateApplication::Get().GetUser(i))
    {
        P->SetFocus(PlayerHUDs[i]);
    }
}
```

---

## 5. IInputProcessor — 전역 입력 후크 (게임 자주 사용)

### 5.1 인터페이스 (IInputProcessor.h)

```cpp
class IInputProcessor
{
public:
    virtual void Tick(const float DeltaTime, FSlateApplication& SlateApp, TSharedRef<ICursor> Cursor) = 0;
    virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent&) { return false; }
    virtual bool HandleKeyUpEvent(FSlateApplication&, const FKeyEvent&) { return false; }
    virtual bool HandleAnalogInputEvent(FSlateApplication&, const FAnalogInputEvent&) { return false; }
    virtual bool HandleMouseMoveEvent(FSlateApplication&, const FPointerEvent&) { return false; }
    virtual bool HandleMouseButtonDownEvent(FSlateApplication&, const FPointerEvent&) { return false; }
    virtual bool HandleMouseButtonUpEvent(FSlateApplication&, const FPointerEvent&) { return false; }
    virtual bool HandleMouseButtonDoubleClickEvent(FSlateApplication&, const FPointerEvent&) { return false; }
    virtual bool HandleMouseWheelOrGestureEvent(FSlateApplication&, const FPointerEvent&, const FPointerEvent*) { return false; }
    virtual bool HandleMotionDetectedEvent(FSlateApplication&, const FMotionEvent&) { return false; }
};
```

### 5.2 사용 (게임 단축키 / 디버그 후크)

```cpp
class FMyInputProcessor : public IInputProcessor
{
public:
    virtual void Tick(float DeltaTime, FSlateApplication& App, TSharedRef<ICursor> Cursor) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(FMyInputProcessor_Tick);   // ← 매 프레임 스코프 의무
    }

    virtual bool HandleKeyDownEvent(FSlateApplication& App, const FKeyEvent& KeyEvent) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(FMyInputProcessor_KeyDown);
        if (KeyEvent.GetKey() == EKeys::F12)
        {
            // 디버그 콘솔 토글 등
            return true;     // 차단
        }
        return false;        // 통과
    }
};

// 게임 시작 시 등록
FSlateApplication::Get().RegisterInputPreProcessor(MakeShared<FMyInputProcessor>());
```

자세한 — [`Slate/EditorApplication §6.1`](../EditorApplication/SKILL.md) (8 virtual 표).

---

## 6. NavigationConfig — 게임패드/방향키 내비

### 6.1 베이스 (NavigationConfig.h)

`FNavigationConfig` — 어떤 키가 어떤 방향(Up/Down/Left/Right) 으로 매핑되는지 + Tab/Enter 등 수락·취소 키:

| API | 의미 |
|-----|------|
| `EUINavigation GetNavigationDirectionFromKey(const FKeyEvent&) const` | 키 → 방향 |
| `EUINavigation GetNavigationDirectionFromAnalogKey(const FKeyEvent&) const` | 아날로그 |
| `EUINavigationAction GetNavigationActionFromKey(const FKeyEvent&) const` | 액션 (Accept/Back) |

### 6.2 자손

| 자손 | 의미 |
|------|------|
| `FNavigationConfig` | 베이스 — 표준 키보드 |
| `FNullNavigationConfig` | 비활성 |
| `FTwinStickNavigationConfig` | 듀얼 스틱 게임패드 |
| (사용자 정의 가능) | |

### 6.3 사용

```cpp
TSharedRef<FNavigationConfig> Config = MakeShared<FTwinStickNavigationConfig>();
FSlateApplication::Get().SetNavigationConfig(Config);

// 사용자별
FSlateApplication::Get().GetUser(0)->SetUserNavigationConfig(Config);
```

---

## 7. AnalogCursor — 게임패드 → 마우스 커서

`FAnalogCursor` (IInputProcessor 자손) — 게임패드 스틱 입력으로 마우스 커서 이동:

```cpp
TSharedRef<FAnalogCursor> Cursor = MakeShared<FAnalogCursor>();
Cursor->SetAcceleration(2.0f);
FSlateApplication::Get().RegisterInputPreProcessor(Cursor);
```

UMG 메뉴 등에서 게임패드로 클릭 시뮬레이션할 때 자주 사용.

---

## 8. GestureDetector — 터치 제스처

`FGestureDetector` — 터치 입력 → Pinch/Pan/Rotate 제스처 검출. 모바일 UI에서 사용.

---

## 9. MenuStack — 팝업 메뉴

### 9.1 IMenu (MenuStack.h, IMenu.h)

`FSlateApplication::PushMenu(...)` 가 반환하는 메뉴 인스턴스. 팝업 메뉴 / 콤보 / 컨텍스트 메뉴 등.

```cpp
TSharedPtr<IMenu> Menu = FSlateApplication::Get().PushMenu(
    /*InParentWidget=*/AsShared(),
    /*WidgetPath=*/FWidgetPath(),
    /*InContent=*/MyMenuContent,
    /*SummonLocation=*/FSlateApplication::Get().GetCursorPos(),
    /*TransitionEffect=*/FPopupTransitionEffect(FPopupTransitionEffect::ContextMenu));

// 닫기
Menu->Dismiss();
```

---

## 10. SWindowTitleBar

`SWindowTitleBar` — 커스텀 윈도우 타이틀 바. 인하우스 툴이 표준 OS 타이틀 대신 자체 타이틀을 그릴 때.

---

## 11. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `IInputProcessor::Tick(...)` | (override 시 자체 처리) | PURE — 매 프레임 + 스코프 의무 |
| `IInputProcessor::Handle*Event(...)` | (override 시 자체 처리) | false 반환 = 통과 |
| `FNavigationConfig::GetNavigationDirectionFromKey(...)` | **FIRST** (커스텀 매핑 추가 시) | 베이스가 표준 키 처리 |
| `FAnalogCursor::Tick(...)` | **FIRST** | 베이스가 커서 이동 처리 |

---

## 12. 함정

| 함정 | 회피 |
|------|------|
| `IInputProcessor::Tick` 스코프 누락 | 매 프레임 — `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |
| `IInputProcessor` Shutdown 시 Unregister 누락 | 게임 종료 시 dangling — `UnregisterInputPreProcessor` 의무 |
| `FSlateApplication::Get()` 검사 없이 호출 — 미초기화 | `FSlateApplication::IsInitialized()` 검사 |
| 멀티플레이 스플릿 — 한 사용자만 포커스 처리 | `GetUser(N)` 별로 분리 |
| `FAnalogCursor` 게임 패드 + UMG 메뉴 | OK 패턴 — IInputProcessor 등록 |
| `FNavigationConfig` 사용자 정의 후 적용 안 됨 | `SetNavigationConfig` 또는 사용자별 `SetUserNavigationConfig` |
| `MenuStack::Dismiss` 안 함 | 팝업 사라지지 않음 — 명시적 닫기 |
| 핸들러 람다 강한 캡처 | TWeakPtr 또는 `CreateWeakLambda` |

---

## 13. 에디터 전용? 🛠

**런타임 모듈** — 게임/에디터 공통. 단:
- `IWidgetReflector` 는 에디터 빌드만 (자세한 [`SlateCore/Trace`](../../SlateCore/references/Trace.md))
- Slate/EditorApplication sub-skill은 별도 — FGlobalTabmanager / 인하우스 툴 측면

---

## 14. 관련 sub-skill

- [`Slate/EditorApplication`](../EditorApplication/SKILL.md) 🛠 — 본 모듈의 에디터 측면 (FGlobalTabmanager 등)
- [`SlateCore/Application`](../../SlateCore/references/Application.md) — `FSlateApplicationBase` (베이스 인터페이스)
- [`SlateCore/Input`](../../SlateCore/references/Input.md) — `FReply`/`FKeyEvent`/`FPointerEvent`
- [`Slate/Commands`](../Commands/SKILL.md) — TCommands<T> + 단축키
- [`UMG/UUserWidget`](../../UMG/references/UUserWidget.md) — Native* 입력 콜백 (게임 UI에서)
- [`SlateCore/Trace`](../../SlateCore/references/Trace.md) 🛠 — Widget Reflector
- 교차: [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) (IWidgetReflector 한정) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (IInputProcessor::Tick 스코프 의무)
