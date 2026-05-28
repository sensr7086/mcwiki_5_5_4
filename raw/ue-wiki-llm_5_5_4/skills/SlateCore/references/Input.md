---
name: slatecore-input
description: OnMouseButtonDown/Up + OnMouseMove + OnKeyDown + OnFocusReceived + FReply + FCaptureLostEvent + FocusManager.
---

# SlateCore / Input

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.5.4
> 다루는 영역: 입력 — `FReply`/`FInputEvent`/`FPointerEvent`/`FKeyEvent`/`FFocusEvent`/`FCharacterEvent`/`FAnalogInputEvent`/`FMotionEvent`/`FNavigationEvent` + `FCursorReply`/`FNavigationReply` + `FHittestGrid` + `FNavigationConfig` + Drag-and-Drop
> 관련 sub-skill: [`SWidget/`](../SWidget/SKILL.md), [`Application/`](../Application/SKILL.md), [`Layout/`](../Layout/SKILL.md)

---

## 1. 개요

Slate의 입력 처리는 **이벤트 기반 + Reply 패턴**:

1. OS/Application Layer가 입력 이벤트 생성 (마우스/키보드/터치/게임패드).
2. `FSlateApplication` 이 `FHittestGrid` 로 마우스 위치 → 위젯 경로(`FWidgetPath`) 결정.
3. 경로의 각 위젯에 `OnXxxButtonDown` 등 virtual 호출.
4. 위젯이 `FReply::Handled()` 또는 `FReply::Unhandled()` 반환.
5. Handled면 라우팅 종료, Unhandled면 부모로 버블링.

---

## 2. 핵심 헤더와 클래스

### 2.1 Reply (`Public/Input/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Input/ReplyBase.h` | `template TReplyBase<DerivedType>` | CRTP 베이스. |
| `Input/Reply.h` | `class FReply : TReplyBase<FReply>` (L23), 정적 `FReply::Handled()` (L233), `FReply::Unhandled()` (L241) | 표준 reply. 메서드 체이닝으로 부가 동작 (`CaptureMouse`, `SetUserFocus`, `LockMouseToWidget`, `BeginDragDrop`, `ReleaseMouseCapture` 등). |
| `Input/CursorReply.h` | `class FCursorReply` | 커서 변경 reply (`OnCursorQuery`). |
| `Input/NavigationReply.h` | `class FNavigationReply` | 내비게이션 라우팅 reply. |
| `Input/PopupMethodReply.h` | `class FPopupMethodReply` | 팝업 표시 방식 reply. |

### 2.2 Events (`Public/Input/Events.h`)

| 구조체 | 위치 | 다루는 입력 |
|--------|------|-------------|
| `FFocusEvent` | L50 | 포커스 획득/상실 |
| `FCaptureLostEvent` | L105 | 마우스 캡처 상실 |
| `FInputEvent` | L154 | 입력 이벤트 베이스 (modifier 키, 터치 ID 등 공통) |
| `FKeyEvent : FInputEvent` | L406 | 키보드 키 (`GetKey()`/`GetCharacter()`/`IsRepeat()`) |
| `FAnalogInputEvent` | L521 | 아날로그 (게임패드 스틱 등) |
| `FCharacterEvent` | L597 | 문자 입력 (IME 통합) |
| `FPointerEvent` | L684 | 마우스/터치 포인터 (`GetScreenSpacePosition()`/`GetEffectingButton()`/`GetWheelDelta()`/`GetTouchpadIndex()`) |
| `FMotionEvent` | L1050 | 모션 센서 (틸트·자이로) |
| `FNavigationEvent` | L1141 | UI 내비게이션 (방향/Accept/Cancel) |

### 2.3 라우팅·테스트 (`Public/Input/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Input/HittestGrid.h` | `class FHittestGrid : FNoncopyable` (L27) | 화면 좌표 → 위젯 경로 빠른 조회. 인밸리데이션 루트마다 보유. |
| `Input/DragAndDrop.h` (+ `.inl`) | `FDragDropEvent`, `FDragDropOperation`, `FExternalDragOperation` | 드래그 앤 드롭. |
| `Input/NavigationRouting.h` | `FNavigationConfig`, `FNullNavigationConfig`, `FUINavigationConfig` 등 | 키 → 내비 방향 매핑. 게임패드/방향키 게이팅. |
| `Input/NavigationMethod.h` | `enum class EUINavigation : uint8` (Up/Down/Left/Right/Next/Previous), `enum class EUINavigationAction : uint8` (Accept/Back) | 내비게이션 방향/액션. |
| `Input/NavigationMetadata.h` | `FNavigationMetaData` | 위젯에 부착하는 내비 정책 (`SetNavigationMetaData`). |

---

## 3. FReply 패턴

```cpp
// === 기본 ===
return FReply::Handled();              // 이벤트 소비
return FReply::Unhandled();            // 부모로 버블링

// === 체이닝 (자주) ===
return FReply::Handled()
    .CaptureMouse(SharedThis(this))           // 마우스 캡처 — 다음 모든 마우스 이벤트가 이 위젯에 옴
    .SetUserFocus(SharedThis(this), EFocusCause::Mouse);

return FReply::Handled()
    .ReleaseMouseCapture()
    .EndDragDrop();

return FReply::Handled()
    .BeginDragDrop(MakeShared<FMyDragOp>(/* payload */));

return FReply::Handled()
    .LockMouseToWidget(SharedThis(this));     // 마우스가 위젯 영역 밖으로 못 나감 (FPS 카메라 등)

return FReply::Handled()
    .DetectDrag(SharedThis(this), EKeys::LeftMouseButton);  // 드래그 감지 시작
```

### 3.1 캡처 / 포커스 / 드래그 해제

```cpp
return FReply::Handled().ReleaseMouseCapture();
return FReply::Handled().ClearUserFocus(EFocusCause::Cleared);
return FReply::Handled().CancelFocusRequest();
```

---

## 4. 가상 함수 (오버라이드 포인트) — `SWidget` 입력 virtual

대부분 `FReply` 반환. 기본 구현은 `FReply::Unhandled()` (이벤트 무시). **override 시 처리한 이벤트만 `Handled()` 반환**.

### 4.1 마우스/포인터

| 시그니처 | 설명 |
|----------|------|
| `virtual FReply OnMouseButtonDown(const FGeometry&, const FPointerEvent&)` | 버튼 누름. `GetEffectingButton()` 으로 LeftMouseButton/RightMouseButton/MiddleMouseButton 구분. |
| `virtual FReply OnMouseButtonUp(const FGeometry&, const FPointerEvent&)` | 버튼 뗌. |
| `virtual FReply OnMouseButtonDoubleClick(const FGeometry&, const FPointerEvent&)` | 더블 클릭. |
| `virtual FReply OnMouseMove(const FGeometry&, const FPointerEvent&)` | 마우스 이동. |
| `virtual void OnMouseEnter(const FGeometry&, const FPointerEvent&)` | 위젯 진입. |
| `virtual void OnMouseLeave(const FPointerEvent&)` | 위젯 이탈. |
| `virtual FReply OnMouseWheel(const FGeometry&, const FPointerEvent&)` | 휠 — `GetWheelDelta()`. |
| `virtual FReply OnTouchStarted/Moved/Ended(const FGeometry&, const FPointerEvent&)` | 터치 입력. |
| `virtual FReply OnDragDetected(const FGeometry&, const FPointerEvent&)` | DetectDrag 후 드래그 시작. `BeginDragDrop` reply. |
| `virtual void OnDragEnter(const FGeometry&, const FDragDropEvent&)` | 드래그 진입. |
| `virtual FReply OnDragOver(const FGeometry&, const FDragDropEvent&)` | 드래그 오버. |
| `virtual FReply OnDrop(const FGeometry&, const FDragDropEvent&)` | 드롭. |
| `virtual void OnDragLeave(const FDragDropEvent&)` | 드래그 이탈. |
| `virtual FCursorReply OnCursorQuery(const FGeometry&, const FPointerEvent&) const` | 커서 모양 결정. `FCursorReply::Cursor(EMouseCursor::Hand)`. |

### 4.2 키보드 / 문자

| 시그니처 | 설명 |
|----------|------|
| `virtual FReply OnKeyDown(const FGeometry&, const FKeyEvent&)` | 키 누름. `GetKey()` → `EKeys::Enter` 등. |
| `virtual FReply OnKeyUp(const FGeometry&, const FKeyEvent&)` | 키 뗌. |
| `virtual FReply OnKeyChar(const FGeometry&, const FCharacterEvent&)` | 문자 입력 (IME). 텍스트 박스에서 사용. |
| `virtual FReply OnAnalogValueChanged(const FGeometry&, const FAnalogInputEvent&)` | 아날로그 (게임패드 스틱). |

### 4.3 포커스 / 내비게이션

| 시그니처 | 설명 |
|----------|------|
| `virtual FReply OnFocusReceived(const FGeometry&, const FFocusEvent&)` | 포커스 획득. |
| `virtual void OnFocusLost(const FFocusEvent&)` | 포커스 상실. |
| `virtual void OnFocusChanging(const FWeakWidgetPath&, const FWidgetPath&, const FFocusEvent&)` | 포커스 이동 알림. |
| `virtual FNavigationReply OnNavigation(const FGeometry&, const FNavigationEvent&)` | UI 내비게이션 라우팅 — `FNavigationReply::Explicit(NextWidget)`/`Stop()`/`Escape()`. |

### 4.4 모션 / 캡처

| 시그니처 | 설명 |
|----------|------|
| `virtual FReply OnMotionDetected(const FGeometry&, const FMotionEvent&)` | 디바이스 모션. |
| `virtual void OnMouseCaptureLost(const FCaptureLostEvent&)` | 마우스 캡처 상실 — 정리 필수. |

### 4.5 빈도 낮은 virtual

| 시그니처 | 설명 |
|----------|------|
| `virtual TOptional<FVirtualPointerPosition> TranslateMouseCoordinateForCustomHitTestChild(...)` | 3D 위젯 등 커스텀 히트 테스트. |
| `virtual bool SupportsKeyboardFocus() const` | 키보드 포커스 받을 수 있는지 (기본 false — 텍스트박스/버튼은 true). |
| `virtual bool IsInteractable() const` | 입력 인터랙션 대상인지. |
| `virtual TSharedPtr<IToolTip> GetToolTip()` | 툴팁 제공. |

---

## 5. 예제

### 5.1 클릭 가능한 박스

```cpp
class SClickBox : public SLeafWidget
{
public:
    SLATE_BEGIN_ARGS(SClickBox) {}
        SLATE_EVENT(FSimpleDelegate, OnClicked)
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs) { OnClickedDelegate = InArgs._OnClicked; }

protected:
    virtual int32 OnPaint(...) const override { /* draw box */ return LayerId + 1; }
    virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(64, 32); }
    virtual bool SupportsKeyboardFocus() const override { return true; }

    virtual FReply OnMouseButtonDown(const FGeometry& Geo, const FPointerEvent& E) override
    {
        if (E.GetEffectingButton() == EKeys::LeftMouseButton)
        {
            return FReply::Handled().CaptureMouse(SharedThis(this));
        }
        return FReply::Unhandled();
    }

    virtual FReply OnMouseButtonUp(const FGeometry& Geo, const FPointerEvent& E) override
    {
        if (E.GetEffectingButton() == EKeys::LeftMouseButton && HasMouseCapture())
        {
            if (Geo.IsUnderLocation(E.GetScreenSpacePosition()))
                OnClickedDelegate.ExecuteIfBound();
            return FReply::Handled().ReleaseMouseCapture();
        }
        return FReply::Unhandled();
    }

    virtual FCursorReply OnCursorQuery(const FGeometry& Geo, const FPointerEvent& E) const override
    {
        return FCursorReply::Cursor(EMouseCursor::Hand);
    }

private:
    FSimpleDelegate OnClickedDelegate;
};
```

### 5.2 드래그 앤 드롭

```cpp
// 출발 위젯
virtual FReply OnMouseButtonDown(const FGeometry& Geo, const FPointerEvent& E) override
{
    if (E.GetEffectingButton() == EKeys::LeftMouseButton)
        return FReply::Handled().DetectDrag(SharedThis(this), EKeys::LeftMouseButton);
    return FReply::Unhandled();
}

virtual FReply OnDragDetected(const FGeometry& Geo, const FPointerEvent& E) override
{
    auto Op = MakeShared<FMyItemDragOp>();
    Op->ItemId = MyId;
    return FReply::Handled().BeginDragDrop(Op);
}

// 목표 위젯
virtual FReply OnDragOver(const FGeometry&, const FDragDropEvent& E) override
{
    if (TSharedPtr<FMyItemDragOp> Op = E.GetOperationAs<FMyItemDragOp>())
        return FReply::Handled();
    return FReply::Unhandled();
}

virtual FReply OnDrop(const FGeometry&, const FDragDropEvent& E) override
{
    if (TSharedPtr<FMyItemDragOp> Op = E.GetOperationAs<FMyItemDragOp>())
    {
        AcceptItem(Op->ItemId);
        return FReply::Handled();
    }
    return FReply::Unhandled();
}
```

### 5.3 내비게이션 라우팅

```cpp
virtual FNavigationReply OnNavigation(const FGeometry&, const FNavigationEvent& E) override
{
    if (E.GetNavigationType() == EUINavigation::Right && NextRightWidget.IsValid())
        return FNavigationReply::Explicit(NextRightWidget.Pin());
    return FNavigationReply::Escape();    // 부모로 위임
}
```

### 5.4 커서 캡처 + 락

```cpp
// FPS 카메라처럼 마우스를 위젯에 가둠
return FReply::Handled()
    .CaptureMouse(SharedThis(this))
    .LockMouseToWidget(SharedThis(this))
    .UseHighPrecisionMouseMovement(SharedThis(this));
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| (없음 — 본 영역은 거의 전부 런타임) | — | — | 입력 라우팅은 게임 빌드에서도 동일하게 동작. |

> 일부 디버그 시각화(`Slate.DebugInputs.IsEnabled` cvar 등)는 `WITH_SLATE_DEBUGGING` 가드. 게임 코드 영향 없음.

---

## 7. 관련 sub-skill

- [`SWidget/`](../SWidget/SKILL.md) — 모든 입력 virtual 의 본체
- [`Application/`](../Application/SKILL.md) — `FSlateApplicationBase` 가 OS 이벤트를 받아 위젯에 라우팅
- [`Layout/`](../Layout/SKILL.md) — `FWidgetPath` / `FArrangedWidget` 가 라우팅 경로
- [`Drawing/`](../Drawing/SKILL.md) — 인밸리데이션과 입력은 `FHittestGrid` 를 공유
- [`InputCore/`](../../InputCore/SKILL.md) — `FKey`/`EKeys` 식별자 자체는 InputCore 모듈
