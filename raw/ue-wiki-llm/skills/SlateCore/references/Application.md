---
name: slatecore-application
description: FSlateApplication 글로벌 - GetCursorPos + GetUserIndexForKeyboard + Tooltip + Window Activation.
---

# SlateCore / Application

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.7.4
> 다루는 영역: Slate Application 베이스 — `ISlateApplicationBase`/`FSlateApplicationBase` + 매 프레임 Tick / Paint / Input 흐름 + `SWindow` 베이스 + `FSlateUser` (다중 사용자) + `FSlateThrottleManager` + `FThrottleRequest`
> **Tier 3 핵심 — 엔진 UI 진입점**. 본 문서는 깊이 있게 다룬다.
> 관련 sub-skill: [`SWidget/`](../SWidget/SKILL.md), [`Drawing/`](../Drawing/SKILL.md), [`Input/`](../Input/SKILL.md), [`../../ApplicationCore/`](../../ApplicationCore/SKILL.md)

---

## 1. 개요

`FSlateApplicationBase` 는 Slate UI의 **루트 오케스트레이터**다. 매 프레임 입력을 받고·위젯 트리를 Tick하고·페인트 사이클을 돌리고·렌더러에게 결과를 넘긴다. SlateCore에는 추상 베이스만 있고, 실제 구현(`FSlateApplication`)은 상위 `Slate` 모듈에 있다 — 인스턴스는 게임/에디터 공통으로 하나만 존재(싱글턴).

```
ISlateApplicationBase  (인터페이스 — 미니멀 슬롯)
  └─ FSlateApplicationBase (SlateCore — 추상 베이스, 멤버·공유 상태 보유)
       └─ FSlateApplication  (Slate 모듈 — 실제 구현, FGenericApplication 와 통합)
```

ApplicationCore 와의 관계:

```
[OS]
  ↓ (Win/Mac/Linux/iOS/Android 각 플랫폼별 메시지)
FGenericApplication  (ApplicationCore — OS 추상)
  ↓ FGenericApplicationMessageHandler 호출
FSlateApplication    (Slate — 메시지 → 위젯 라우팅)
  ↓ FWidgetPath / FHittestGrid 로 대상 결정
SWidget::On*Event    (위젯이 FReply 반환)
```

---

## 2. 핵심 헤더와 클래스

### 2.1 SlateCore 측 (이 sub-skill)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Application/SlateApplicationBase.h` | `class FSlateApplicationBase` (L113), `enum class EInvalidateWidgetReason` (L29 forward) | 추상 Application 베이스. 모든 `virtual = 0` 메서드는 `FSlateApplication` 이 구현. |
| `Application/SlateWindowHelper.h` | `FSlateWindowHelper` (정적 헬퍼) | 윈도우 정렬·검색 유틸. |
| `Application/ThrottleManager.h` | `class FThrottleRequest` (L17), `class FSlateThrottleManager` | 엔진 Tick 빈도를 일시적으로 낮추는 매니저 (드래그 중 등). |

### 2.2 Slate 모듈 측 (cross-reference)

이 sub-skill 범위 밖이지만 짝으로 알아야 함:

| 헤더 (Slate 모듈) | 심볼 | 역할 |
|-------------------|------|------|
| `Slate/Public/Framework/Application/SlateApplication.h` | `class FSlateApplication : FSlateApplicationBase` | **실제 구현**. `Get()`/`Initialize()`/`Shutdown()` 정적. |
| `Slate/Public/Framework/Application/SlateUser.h` | `class FSlateUser : TSharedFromThis<FSlateUser>` (L40) | **사용자(SlateUser)** 단위 입력 컨텍스트. 키보드·마우스 한 세트가 한 사용자. 다중 플레이어/스플릿스크린에서 여러 인스턴스. |
| `Slate/Public/Framework/Application/AnalogCursor.h` | `FAnalogCursor` | 게임패드 → 마우스 커서 변환. |
| `Slate/Public/Widgets/SWindow.h` | `class SWindow : SCompoundWidget` | OS 윈도우와 짝지어진 Slate 윈도우. **베이스 메타는 SlateCore의 `Advanced_IsWindow()` 가상**. |

> SlateCore에는 `SWindow` 베이스/forward만 있고 본체는 Slate 모듈. 본 sub-skill은 인터페이스 측면, 구체 동작은 [`Slate/Application/`](../../Slate/references/Application.md) 에서 다룬다 (작성 예정).

---

## 3. 매 프레임 Slate 사이클

`FSlateApplication::Tick(...)` 가 호출하는 단계 (단순화):

```
1. PreTick               — Idle 상태 검사, ThrottleManager 갱신
2. ProcessInput          — OS 메시지 → MessageHandler → 위젯 경로 → On*Event
                            ├─ FHittestGrid 로 대상 위젯 결정
                            ├─ 캡처 위젯이 있으면 그쪽 우선
                            └─ FReply 결과로 캡처/포커스/드래그 갱신
3. TickWidgets           — 등록된 위젯의 SWidget::Tick 호출 + ActiveTimer 콜백
4. PrepareWindowsForRender — SWindow 별 prepass (ComputeDesiredSize 캐시)
5. Paint                 — InvalidationRoot::PaintInvalidationRoot or 일반 OnPaint 사이클
                            ├─ FastPath: 변경된 위젯만 재페인트
                            └─ SlowPath: 전체 그래프
6. DrawWindows           — FSlateRenderer 가 GPU 제출 (SlateRHIRenderer)
7. PostTick              — 후처리, 통계 수집
```

각 단계의 비용은 Unreal Insights `Slate` 채널에서 분석 — [`Trace/`](../Trace/SKILL.md).

### 3.1 ProcessInput 디테일

```
OS 메시지 (WM_MOUSEMOVE, NSEvent, ...)
   ↓ FGenericApplicationMessageHandler::OnMouseMove(...) 등
FSlateApplication 이 메시지 해석
   ↓ FSlateUser 식별 (어느 사용자의 입력?)
   ↓ FHittestGrid 로 위젯 경로 결정 (GetWidgetsAtCursor)
   ↓ FWidgetPath 의 leaf → root 순회하며 OnMouseMove(...) 호출
   ↓ Handled 만나면 라우팅 종료
   ↓ Reply 의 부가 동작 처리 (CaptureMouse / SetUserFocus / BeginDragDrop ...)
```

### 3.2 Paint 사이클 디테일

```
SWindow 별로:
   1. PrepassLayout        — 모든 자식의 ComputeDesiredSize 갱신
   2. ArrangedChildren 생성 — OnArrangeChildren 호출하며 FGeometry 결정
   3. Paint:
        if (InvalidationRoot 있음 && FastPath 가능)
            FSlateInvalidationRoot::PaintInvalidationRoot()  → bRepaintedWidgets
        else
            루트부터 SWidget::OnPaint 재귀
   4. FSlateWindowElementList 가 누적된 element 들을 FSlateRenderer 에 제출
```

자세한 인밸리데이션 캐시 흐름은 [`Drawing/§4`](../Drawing/SKILL.md), LayerId·DrawCall은 [`Drawing/§5`](../Drawing/SKILL.md).

---

## 4. 핵심 API (`FSlateApplicationBase` virtual = 0)

`SlateApplicationBase.h:113~` 의 핵심 추상 메서드들 — 모두 `FSlateApplication` 이 구현:

### 4.1 Application 라이프사이클 / 상태

```cpp
virtual bool IsActive() const = 0;                              // 앱이 활성(포커스 있음) 인지
virtual bool IsInitialized() const;
inline FSlateRenderer* GetRenderer() const;                     // 렌더러 (RHI/Null) 접근
```

### 4.2 SWindow 관리

```cpp
virtual TSharedRef<SWindow> AddWindow(TSharedRef<SWindow> InSlateWindow,
                                      const bool bShowImmediately = true) = 0;
virtual void ArrangeWindowToFrontVirtual(TArray<TSharedRef<SWindow>>& Windows,
                                          const TSharedRef<SWindow>& WindowToBringToFront) = 0;
virtual TSharedPtr<SWindow> GetActiveTopLevelWindow() const = 0;
virtual TSharedPtr<SWindow> GetActiveTopLevelRegularWindow() const = 0;       // 메뉴/툴팁 제외
virtual const TArray<TSharedRef<SWindow>> GetTopLevelWindows() const = 0;     // 가상 윈도우 제외
```

### 4.3 위젯 경로 / 포커스 / 캡처

```cpp
virtual bool FindPathToWidget(TSharedRef<const SWidget> InWidget,
                              FWidgetPath& OutWidgetPath,
                              EVisibility VisibilityFilter = EVisibility::Visible) = 0;
virtual TSharedPtr<SWindow> FindWidgetWindow(TSharedRef<const SWidget> InWidget) const = 0;

virtual bool HasUserFocus(const TSharedPtr<const SWidget> Widget, int32 UserIndex) const = 0;
virtual bool HasAnyUserFocus(const TSharedPtr<const SWidget> Widget) const = 0;
virtual bool DoesWidgetHaveMouseCapture(const TSharedPtr<const SWidget> Widget) const = 0;
virtual bool DoesWidgetHaveMouseCaptureByUser(const TSharedPtr<const SWidget> Widget,
                                               int32 UserIndex, TOptional<int32> PointerIndex) const = 0;
```

### 4.4 마우스/커서/입력 상태

```cpp
virtual TOptional<EFocusCause> HasUserFocusedDescendants(...) const = 0;
virtual FVector2D GetCursorPos() const = 0;
virtual FVector2D GetLastCursorPos() const = 0;
virtual void SetCursorPos(const FVector2D& MouseCoordinate) = 0;

virtual bool IsKeyDown(const FKey& Key, int32 UserIndex = 0) const;
virtual TSharedPtr<ICursor> GetPlatformCursor() const = 0;
```

### 4.5 어트리뷰트·인밸리데이션 통합

```cpp
virtual void InvalidateAllWidgets(bool bClearResourcesImmediately) const = 0;   // 모든 위젯 재페인트
virtual void OnInvalidateAllWidgets(bool bClearResourcesImmediately);
SLATECORE_API static FSlateApplicationBase& Get();                              // 싱글턴 접근
SLATECORE_API static bool IsInitialized();
```

### 4.6 시간

```cpp
inline double GetCurrentTime() const;
inline float GetDeltaTime() const;
```

---

## 5. FSlateUser (다중 사용자/플레이어)

`FSlateUser` 는 한 명의 사용자(키보드+마우스+게임패드 한 세트)를 표현. 스플릿스크린·로컬 멀티플레이에서 여러 인스턴스가 공존.

| 멤버 / 메서드 (개념) | 용도 |
|---------------------|------|
| `int32 UserIndex` | 사용자 식별자 (0 = 기본 키보드/마우스, 1+ = 추가 게임패드 등) |
| `TWeakPtr<SWidget> FocusedWidget` | 키보드 포커스 보유 위젯 |
| `TWeakPtr<SWidget> CaptorWidget` | 마우스 캡처 보유 위젯 |
| `FVector2D CursorPos` | 사용자별 커서 위치 (게임패드 가상 커서 포함) |
| `SetFocus(...)`, `ClearFocus(...)` | 포커스 변경 |
| `LockMouse(...)`, `ReleaseMouseCapture(...)` | 캡처 변경 |
| `RouteFocusChanging`, `RouteFocusReceived/Lost` | 포커스 이동 라우팅 |

자세한 멤버는 `Slate/Public/Framework/Application/SlateUser.h:40` 의 `FSlateUser` 클래스 — Slate 모듈 sub-skill에서 다룬다.

### 5.1 사용자 인덱스 패턴

```cpp
const int32 UserIndex = SlateUser->GetUserIndex();
if (FSlateApplicationBase::Get().HasUserFocus(MyWidget, UserIndex))
{
    // 이 사용자가 MyWidget에 포커스를 가지고 있음
}

// 커서 캡처 (사용자 0 — 기본)
return FReply::Handled().CaptureMouse(SharedThis(this));   // FReply는 내부적으로 user 0
```

---

## 6. FSlateThrottleManager / FThrottleRequest

매 프레임 사이클 빈도를 일시적으로 낮추는 매니저 — 드래그·리사이즈 같은 인터랙티브 동작 중 GPU/CPU 사용 줄이기에 사용.

```cpp
// ThrottleManager.h:17
class FThrottleRequest
{
    bool IsValid() const { return Index != INDEX_NONE; }
private:
    int32 Index;
};

class FSlateThrottleManager  // (개념)
{
public:
    static FSlateThrottleManager& Get();
    FThrottleRequest EnterResponsiveMode();          // 인터랙티브 모드 진입
    void LeaveResponsiveMode(FThrottleRequest& Req); // 종료
    bool IsAllowingExpensiveTasks() const;           // 현재 throttle 중인지
};
```

사용 패턴 (드래그 시작 / 종료):

```cpp
FThrottleRequest Req;
virtual FReply OnMouseButtonDown(const FGeometry& Geo, const FPointerEvent& E) override
{
    if (E.GetEffectingButton() == EKeys::LeftMouseButton)
    {
        Req = FSlateThrottleManager::Get().EnterResponsiveMode();
        return FReply::Handled().CaptureMouse(SharedThis(this));
    }
    return FReply::Unhandled();
}

virtual FReply OnMouseButtonUp(const FGeometry& Geo, const FPointerEvent& E) override
{
    if (Req.IsValid()) FSlateThrottleManager::Get().LeaveResponsiveMode(Req);
    return FReply::Handled().ReleaseMouseCapture();
}
```

---

## 7. 가상 함수 (오버라이드 포인트)

게임 코드는 `FSlateApplicationBase` 를 직접 상속하지 않는다 — 엔진이 `FSlateApplication` 으로 구현 제공. 그러나 다음 hook 들은 실용:

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `static FSlateApplicationBase& Get()` | SlateApplicationBase.h | 싱글턴 접근 (런타임에서 자주). |
| `static bool IsInitialized()` | SlateApplicationBase.h | Slate 사용 가능 여부 체크 — 모듈 초기화 단계에서 필요. |
| `virtual void OnInvalidateAllWidgets(bool)` | SlateApplicationBase.h | 전체 인밸리데이션 hook (override 거의 없음). |

`SWidget::Advanced_IsWindow()` (SlateCore SWidget.h:1523) → `SWindow` 만 true. 일반 코드가 SWindow 자체를 상속하는 건 드물다.

---

## 8. 예제

### 8.1 Application 사용 가능 검사 + 윈도우 추가

```cpp
if (FSlateApplicationBase::IsInitialized())
{
    auto& App = FSlateApplicationBase::Get();   // FSlateApplicationBase&
    // 활성 최상위 윈도우 위에 새 모달 윈도우 추가
    TSharedRef<SWindow> Modal = SNew(SWindow)
        .Title(LOCTEXT("MyModal", "Confirm"))
        .ClientSize(FVector2D(400, 200))
        .SupportsMinimize(false)
        .SupportsMaximize(false)
        [
            SNew(STextBlock).Text(LOCTEXT("Q", "Are you sure?"))
        ];

    // FSlateApplication 측 정적 헬퍼 사용 (Slate 모듈)
    FSlateApplication::Get().AddModalWindow(Modal,
        App.GetActiveTopLevelRegularWindow().ToSharedRef());
}
```

### 8.2 Tick 빈도 throttle

```cpp
class SDragHandle : public SLeafWidget
{
    virtual FReply OnMouseButtonDown(const FGeometry&, const FPointerEvent& E) override
    {
        if (E.GetEffectingButton() == EKeys::LeftMouseButton)
        {
            ThrottleHandle = FSlateThrottleManager::Get().EnterResponsiveMode();
            return FReply::Handled().CaptureMouse(SharedThis(this));
        }
        return FReply::Unhandled();
    }
    virtual FReply OnMouseButtonUp(const FGeometry&, const FPointerEvent&) override
    {
        if (ThrottleHandle.IsValid())
            FSlateThrottleManager::Get().LeaveResponsiveMode(ThrottleHandle);
        return FReply::Handled().ReleaseMouseCapture();
    }

    FThrottleRequest ThrottleHandle;
};
```

### 8.3 위젯 경로 검색 (디버그/툴)

```cpp
FWidgetPath Path;
if (FSlateApplicationBase::Get().FindPathToWidget(MyWidget.ToSharedRef(), Path,
                                                   EVisibility::All))
{
    UE_LOG(LogSlate, Log, TEXT("Path depth: %d"), Path.Widgets.Num());
}
```

> `FindPathToWidget` 은 비싸다 — 매 프레임 호출 금지. 보통 디버깅·자동화 테스트에서만.

### 8.4 활성 윈도우 필터

```cpp
const auto& App = FSlateApplicationBase::Get();
TSharedPtr<SWindow> Top = App.GetActiveTopLevelRegularWindow();   // 메뉴/툴팁 제외
for (TSharedRef<SWindow> W : App.GetTopLevelWindows())
{
    UE_LOG(LogSlate, Log, TEXT("Window: %s"), *W->GetTitle().ToString());
}
```

---

## 9. 운영 가이드 / 함정

1. **`FSlateApplication::Get()` vs `FSlateApplicationBase::Get()`** — 둘 다 같은 인스턴스를 가리키지만 타입이 다르다. SlateCore 코드에서는 `FSlateApplicationBase&`, Slate 모듈/에디터 코드에서는 `FSlateApplication&` 으로 받아 더 많은 메서드 사용. **Slate 헤더 include 가능하면 후자 권장**.
2. **싱글턴 의존 회피** — 라이브러리/플러그인 코드에서 `IsInitialized()` 체크 후 사용. 단위 테스트 환경에는 Slate 미초기화 상태가 있다.
3. **윈도우 추가는 메인 스레드만** — `AddWindow`/`AddModalWindow` 는 게임 스레드에서만 안전.
4. **throttle 누락** — `EnterResponsiveMode` 만 호출하고 `Leave` 안 하면 영구 throttle. `FThrottleRequest` 멤버를 RAII 처럼 다룰 것.
5. **포커스 사용자별 분리** — `HasUserFocus(W, /*UserIndex=*/0)` 와 `HasUserFocus(W, /*UserIndex=*/1)` 은 다른 사용자. 멀티플레이/스플릿스크린에서 로컬 사용자 인덱스를 항상 명시.
6. **`InvalidateAllWidgets`** 는 비싸다 — 테마 전환 같은 글로벌 변화에만. 일반 변경은 위젯 단위 `Invalidate(reason)`.
7. **드래그 중 모달 윈도우** — 모달이 ProcessInput을 가로채므로 외부 드래그는 멈춘다. 의도된 동작이지만 UX 설계 시 주의.

---

## 10. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `FSlateApplication::AddModalWindow(...)` 일부 옵션 🛠 | Slate 측 | (런타임에도 시그니처 존재) | 에디터에서 자주, 게임 빌드는 보통 비-모달 UI 사용. |
| Slate Insights / Reflector 통합 🛠 | (Trace/Debugging) | `WITH_SLATE_DEBUGGING` | [`Trace/`](../Trace/SKILL.md) |
| `Slate.DebugWidgets`, `Widget Reflector` 콘솔 명령 🛠 | (cvar/UI) | `WITH_SLATE_DEBUGGING` | 위젯 트리 시각화. |
| Slate Reflector 위젯 (`FWidgetReflector`) 🛠 | Slate 모듈 | `WITH_SLATE_DEBUGGING` | 에디터 전용. |

런타임에서 안전한 API는 `FSlateApplicationBase::Get()` / `IsInitialized` / 윈도우 관리 / 포커스 조회 / `FSlateThrottleManager` 전부.

---

## 11. 관련 sub-skill

- [`SWidget/`](../SWidget/SKILL.md) — `FSlateApplicationBase::FindPathToWidget` 가 `FWidgetPath` 빌드
- [`Drawing/`](../Drawing/SKILL.md) — Tick 마지막 단계의 Paint / Renderer 제출
- [`Input/`](../Input/SKILL.md) — `ProcessInput` 단계가 `FReply` 라우팅
- [`Layout/`](../Layout/SKILL.md) — `PrepassLayout` 이 `ComputeDesiredSize` 호출
- [`../../ApplicationCore/`](../../ApplicationCore/SKILL.md) — `FGenericApplication` / `FGenericApplicationMessageHandler` 가 OS 메시지를 SlateApplication에 전달
- [`Trace/`](../Trace/SKILL.md) — `Slate` Insights 채널로 Tick 단계별 분석
- [`../../Slate/Application/`](../../Slate/references/Application.md) — 실제 `FSlateApplication` 본체 (작성 예정)
