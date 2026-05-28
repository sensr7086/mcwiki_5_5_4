---
name: slate-miscwidgets
description: SThrobber + SCircularThrobber + SProgressBar + SSeparator + SSpacer - 보조 위젯.
---

# Slate · MiscWidgets sub-skill

> **모듈**: Slate (Tier 3 — 게임/에디터 공통)
> **위치**: `Engine/Source/Runtime/Slate/Public/Widgets/` 의 기타 카테고리
> **다루는 범위**: 다른 sub-skill에 안 들어가는 보조 위젯 — Notifications · Colors · Images · Navigation · Accessibility · Docking · LayerManager + Framework/MultiBox.

---

## 1. 개요

Slate 의 **잡다 위젯·서비스** 묶음. 다른 sub-skill (CommonWidgets / LayoutWidgets / TextInput / ListsTrees / Animation / Application) 에 안 속하는 영역 정리.

---

## 2. Notifications (`Widgets/Notifications/` + `Framework/Notifications/`)

### 2.1 헤더

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `Widgets/Notifications/SNotificationList.h` | `SNotificationList` | 알림 목록 (트레이) |
| `Widgets/Notifications/INotificationWidget.h` | `INotificationWidget` 인터페이스 | 사용자 정의 알림 |
| `Widgets/Notifications/SCompletionAssist.h` | `SCompletionAssist` | 자동완성 도움 |
| `Widgets/Notifications/SErrorHint.h` / `SErrorText.h` | 에러 표시 | |
| `Widgets/Notifications/SPopUpErrorText.h` | 팝업 에러 | |
| `Widgets/Notifications/SProgressBar.h` | `SProgressBar` | 진행 바 |
| `Widgets/Notifications/SWidgetSnapshotVisualizer.h` 🛠 | 스냅샷 | |
| `Framework/Notifications/NotificationManager.h` | `FSlateNotificationManager` | 글로벌 알림 매니저 |

### 2.2 사용 패턴 — 토스트 알림

```cpp
FNotificationInfo Info(LOCTEXT("Saved", "Asset saved successfully"));
Info.ExpireDuration = 3.0f;
Info.bUseLargeFont = false;
Info.Image = FAppStyle::GetBrush("Icons.SuccessWithColor");
Info.Hyperlink = FSimpleDelegate::CreateLambda([]()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_NotificationHyperlink);
    // 클릭 시 동작
});
Info.HyperlinkText = LOCTEXT("Show", "Show in browser");

FSlateNotificationManager::Get().AddNotification(Info);
```

### 2.3 진행 바 (SProgressBar)

```cpp
SNew(SProgressBar)
.Percent_Lambda([this]() { return CurrentProgress; })
.FillColorAndOpacity(FLinearColor::Green)
.BackgroundImage(FAppStyle::GetBrush("ProgressBar.Background"));
```

UMG `UProgressBar` 가 본 위젯의 BP 래퍼.

---

## 3. Colors (`Widgets/Colors/`)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `SColorBlock.h` | `SColorBlock` | 단일 색 사각형 |
| `SColorPicker.h` | `SColorPicker` | 색 선택 다이얼로그 |
| `SColorWheel.h` | `SColorWheel` | 색상 휠 |
| `SColorSpectrum.h` | `SColorSpectrum` | 색 스펙트럼 |
| `SColorThemes.h` | `SColorThemes` | 색 테마 라이브러리 |
| `SSimpleGradient.h` | `SSimpleGradient` | 그라데이션 |

```cpp
// 사용자 색 선택 다이얼로그
FColorPickerArgs Args;
Args.bUseAlpha = true;
Args.bOnlyRefreshOnOk = false;
Args.InitialColor = MyColor;
Args.OnColorCommitted = FOnLinearColorValueChanged::CreateLambda([this](FLinearColor NewColor)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnColorCommitted);
    MyColor = NewColor;
});
OpenColorPicker(Args);
```

---

## 4. Images (`Widgets/Images/`)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `SImage.h` | `SImage` | 이미지 (FSlateBrush 기반) |
| `SThrobber.h` | `SThrobber` + `SCircularThrobber` | 로딩 인디케이터 (자동 휘발성) |
| `SLayeredImage.h` (일부) | `SLayeredImage` | 다층 이미지 |

```cpp
SNew(SImage)
.Image(FAppStyle::Get().GetBrush("Icons.Save"))
.ColorAndOpacity(FSlateColor(FLinearColor::White))
.OnMouseButtonDown_Lambda([](const FGeometry& Geom, const FPointerEvent& Event) -> FReply
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SImage_OnClicked);
    return FReply::Handled();
});

SNew(SThrobber)
.Visibility(EVisibility::Collapsed)        // 평소 숨김 — 로딩 시만 Visible
.NumPieces(8)
.Animate(SThrobber::All);
```

> **🚨 SThrobber 자동 휘발성** — InvalidationBox 안에 넣어도 캐시 효과 X ([`06_InvalidationHotspots.md §2.4`](../../../references/06_InvalidationHotspots.md)).

---

## 5. Navigation (`Widgets/Navigation/`)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `SBreadcrumbTrail.h` | `SBreadcrumbTrail<NodeType>` | 브레드크럼 (경로 표시) |

```cpp
SNew(SBreadcrumbTrail<TSharedPtr<FString>>)
.OnCrumbClicked_Lambda([this](TSharedPtr<FString> Crumb)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SBreadcrumb_OnCrumbClicked);
    NavigateTo(*Crumb);
});
```

---

## 6. Accessibility (`Widgets/Accessibility/`)

| 헤더 | 의미 |
|------|------|
| `SlateAccessibleWidgets.h` | 접근성 위젯 통합 (스크린 리더) |

거의 사용 안 함 — Engine이 자동 처리.

---

## 7. Docking (`Widgets/Docking/`) — Slate 게임 측면 (편의)

| 헤더 | 의미 |
|------|------|
| `SDockingTabStack.h` | (Private 노출) |

> 전체 Docking은 [`Slate/Docking`](../Docking/SKILL.md) 🛠 sub-skill에서 다룸.

---

## 8. LayerManager (`Widgets/LayerManager/`)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `STooltipPresenter.h` | `STooltipPresenter` | 툴팁 표시 |
| `SPopupLayer.h` | `SPopupLayer` | 팝업 레이어 |

내부 시스템 — 직접 사용 거의 X.

---

## 9. MultiBox (`Framework/MultiBox/`)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `MultiBoxBuilder.h` | `FBaseMenuBuilder` 등 | (이미 [`Slate/Menu`](../Menu/SKILL.md) sub-skill 에서 다룸) |
| `MultiBoxDefs.h` | `EMultiBlockType`/`EMultiBoxType` enum | |
| `MultiBox.h` | `FMultiBox` | 메뉴/툴바 베이스 |

자세한 — [`Slate/Menu`](../Menu/SKILL.md) sub-skill.

---

## 10. SWidgetSwitcher

`Widgets/Layout/SWidgetSwitcher.h` (또는 Layout 카테고리) — 한 번에 한 자식만 표시:

```cpp
SAssignNew(Switcher, SWidgetSwitcher)
.WidgetIndex_Lambda([this]() { return CurrentTabIndex; })
+SWidgetSwitcher::Slot()[ TabAContent ]
+SWidgetSwitcher::Slot()[ TabBContent ]
+SWidgetSwitcher::Slot()[ TabCContent ];
```

UMG `UWidgetSwitcher` 가 본 위젯의 BP 래퍼.

---

## 11. SViewport (3D 뷰포트 호스트)

`Widgets/SViewport.h` — 3D 뷰포트 (FViewportClient 호스팅). 인하우스 에디터의 메인 3D 영역.

```cpp
TSharedPtr<FMyViewportClient> ViewportClient = MakeShared<FMyViewportClient>();
SAssignNew(Viewport, SViewport)
.RenderTargetMirrorMode(ESlateMirrorMode::None)
.IsEnabled(true)
.EnableGammaCorrection(false)
[ /* 오버레이 위젯 */ ];

Viewport->SetViewportInterface(ViewportClient.ToSharedRef());
```

`FViewportClient` 자손 + `IInputProcessor` 통합으로 3D 입력 처리.

---

## 12. SVirtualKeyboardEntry (모바일)

가상 키보드 통합. 거의 자동 — 직접 사용 X.

---

## 13. 가상 함수 / Super 호출

대부분 SCompoundWidget — Construct 안에서 ChildSlot 채우기. virtual override 거의 없음.

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `INotificationWidget::ExpireWidget()` 등 | (override 시 자체 처리) | 사용자 정의 알림 |
| `SThrobber::Tick` | **FIRST** | 매 프레임 회전 진행 (자동 휘발성) |
| `SColorPicker::OnColorChanged` | (콜백) | 색 선택 |

---

## 14. 함정

| 함정 | 회피 |
|------|------|
| `FSlateNotificationManager::AddNotification` Hyperlink 람다 강 캡처 | TWeakPtr |
| `SThrobber` 항상 표시 | 로딩 시에만 Visible (Collapsed 기본) |
| `SColorPicker` 다이얼로그 — 비동기 결과 | `OnColorCommitted` 콜백에서 처리 |
| `SImage::Image` 매 프레임 변경 | TAttribute 활용 (자동 인밸리데이션) |
| `SViewport` ViewportClient 라이프사이클 | TSharedPtr — 자동 정리 |
| `SBreadcrumbTrail` 이전 경로 — `PopCrumb` 누락 | 명시적 호출 |
| `SProgressBar` 매 프레임 SetPercent | 변경 시에만 호출 |
| 알림 ExpireDuration 0 또는 너무 긴 값 | 합리적 (3~5초) |
| 콜백 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) |

---

## 15. 에디터 전용? 🛠

대부분 런타임 — 게임/에디터 공통. 단:
- `SWidgetSnapshotVisualizer` 🛠 — 에디터 전용
- 일부 디버그 위젯 — 에디터 전용

---

## 16. 관련 sub-skill

- [`UMG/StandardWidgets`](../../UMG/references/StandardWidgets.md) — UImage/UThrobber/UProgressBar (BP 래퍼)
- [`Slate/CommonWidgets`](../CommonWidgets/SKILL.md) — 표준 입력 위젯
- [`Slate/LayoutWidgets`](../LayoutWidgets/SKILL.md) — 레이아웃 패널
- [`Slate/Menu`](../Menu/SKILL.md) — MultiBox 시스템
- [`Slate/Docking`](../Docking/SKILL.md) — 도킹 시스템
- [`SlateCore/Drawing`](../../SlateCore/references/Drawing.md) — FSlateBrush · FSlateColor
- 교차: [`06_InvalidationHotspots.md §2.4`](../../../references/06_InvalidationHotspots.md) (Throbber 자동 휘발성) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
