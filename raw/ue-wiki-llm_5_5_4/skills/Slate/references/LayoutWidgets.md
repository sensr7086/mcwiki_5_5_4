---
name: slate-layoutwidgets
description: SHorizontalBox + SVerticalBox + SOverlay + SScrollBox + SBox + SBorder + SExpandableArea - 레이아웃 위젯.
---

# Slate · LayoutWidgets sub-skill

> **모듈**: Slate (Tier 3 — 게임/에디터 공통)
> **위치**: `Engine/Source/Runtime/Slate/Public/Widgets/Layout/` (33 헤더)
> **다루는 범위**: 레이아웃·컨테이너 위젯 — `SBox`·`SBorder`·`SOverlay`·`SHorizontalBox`/`SVerticalBox`(Framework/Layout)·`SScrollBox`·`SSplitter`·`SExpandableArea`·`SSafeZone`·`SScaleBox`·`SDPIScaler`·`SBackgroundBlur`·`SUniformGridPanel`·`SGridPanel`·`SConstraintCanvas` 등.

---

## 1. 개요

Slate 의 **자식 배치/레이아웃 위젯** 묶음. UMG 의 `UVerticalBox`/`UHorizontalBox`/`UCanvasPanel`/`UScrollBox`/`UScaleBox` ([`UMG/PanelWidgets`](../../UMG/references/PanelWidgets.md)) 가 이들의 BP 래퍼.

> **참고**: 일부 베이스 (예: `SBoxPanel` / `SHorizontalBox` / `SVerticalBox`) 는 `Slate/Public/Framework/Layout/` 에. 본 sub-skill은 두 디렉토리를 통합해 다룸.

---

## 2. 핵심 헤더 카테고리

### 2.1 단일 자식 (콘텐츠 래퍼)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `SBox.h` | `SBox` | 사이즈 강제·정렬·패딩 |
| `SBorder.h` | `SBorder` | 테두리 + 단일 자식 |
| `SBackgroundBlur.h` | `SBackgroundBlur` | 배경 블러 효과 |
| `SBackgroundBlurWidget.h` | (관련) | |
| `SDPIScaler.h` | `SDPIScaler` | DPI 자동 스케일 |
| `SScaleBox.h` | `SScaleBox` | 자식 스케일 (Stretch 모드) |
| `SSafeZone.h` | `SSafeZone` | 모바일/콘솔 안전 영역 |
| `SExpandableArea.h` | `SExpandableArea` | 펼침/접기 |
| `SEnableBox.h` | `SEnableBox` | bIsEnabled 토글 |
| `SFxWidget.h` | `SFxWidget` | 시각 효과 (회전·스케일·투명도) |
| `SScissorRectBox.h` | `SScissorRectBox` | 클리핑 |
| `SPopup.h` | `SPopup` | 팝업 |
| `SHeader.h` | `SHeader` | 헤더 (구분선 + 라벨) |

### 2.2 다중 자식 (패널)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `Framework/Layout/SBoxPanel.h` | `SBoxPanel` (베이스) + `SHorizontalBox` + `SVerticalBox` + `SStackBox` | 1축 stack |
| `SOverlay.h` (Framework) | `SOverlay` | Z-order 중첩 |
| `SGridPanel.h` | `SGridPanel` | 가변 셀 그리드 |
| `SUniformGridPanel.h` | `SUniformGridPanel` | 균일 셀 그리드 |
| `SScrollBox.h` | `SScrollBox` | 1축 스크롤 |
| `SSplitter.h` | `SSplitter` | 사용자 조절 가능한 분할 |
| `SRadialBox.h` | `SRadialBox` | 원형 배치 |
| `SResponsiveGridPanel.h` | `SResponsiveGridPanel` | 반응형 그리드 |
| `SConstraintCanvas.h` | `SConstraintCanvas` | Anchor + Offset (UMG UCanvasPanel 의 Slate 베이스) |
| `SLinkedBox.h` | `SLinkedBox` | 사이즈 링크 (그룹) |

### 2.3 보조

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `SScrollBar.h` | `SScrollBar` | 스크롤 바 (SScrollBox 내부 사용) |
| `SScrollBarTrack.h` | `SScrollBarTrack` | 스크롤 트랙 |
| `SScrollBorder.h` | `SScrollBorder` | 스크롤 테두리 |
| `LinkableScrollBar.h` | (헬퍼) | 링크 가능한 스크롤바 |
| `SSeparator.h` | `SSeparator` | 구분선 |
| `SSpacer.h` | `SSpacer` | 빈 공간 |
| `SMissingWidget.h` | `SMissingWidget` | 위젯 누락 표시 |
| `SMenuOwner.h` | `SMenuOwner` | 메뉴 소유 |
| `Anchors.h` | `FAnchors` (struct) | 앵커 정의 (SConstraintCanvas) |

---

## 3. SHorizontalBox / SVerticalBox (가장 자주)

```cpp
SNew(SVerticalBox)
+SVerticalBox::Slot()                       // Auto 사이즈
.AutoHeight()                               // 또는 .AutoWidth() (HBox)
.Padding(0, 4)
.HAlign(HAlign_Center)
[ SNew(STextBlock).Text(LOCTEXT("Header", "Header")) ]

+SVerticalBox::Slot()                       // Fill — 남는 공간 차지
.FillHeight(1.0f)
[ SNew(SScrollBox) /* ... */ ]

+SVerticalBox::Slot()
.AutoHeight()
[ SNew(SButton).Text(LOCTEXT("OK", "OK")) ];
```

### 3.1 슬롯 API

| API | 의미 |
|-----|------|
| `AutoWidth()` / `AutoHeight()` | DesiredSize 사용 |
| `FillWidth(float)` / `FillHeight(float)` | 비율 분배 |
| `Padding(FMargin)` | 안쪽 여백 |
| `HAlign(EHorizontalAlignment)` / `VAlign(EVerticalAlignment)` | 정렬 |
| `MaxWidth(float)` / `MaxHeight(float)` | 최대 크기 |

---

## 4. SBox (사이즈 강제)

```cpp
SNew(SBox)
.WidthOverride(200)
.HeightOverride(100)
.HAlign(HAlign_Center)
.VAlign(VAlign_Center)
[ SNew(STextBlock).Text(LOCTEXT("Hi", "Hi")) ];
```

자주 쓰는 인자:
- `WidthOverride` / `HeightOverride` — 절대값
- `MinDesiredWidth` / `MaxDesiredWidth`
- `MinAspectRatio` / `MaxAspectRatio`
- `Padding`

---

## 5. SBorder (테두리 + 단일 자식)

```cpp
SNew(SBorder)
.BorderImage(FAppStyle::Get().GetBrush("PropertyWindow.AssetThumbnailBorder"))
.BorderBackgroundColor(FLinearColor::White)
.Padding(8)
.HAlign(HAlign_Center)
[ SNew(STextBlock).Text(LOCTEXT("Hello", "Hello")) ];
```

`OnMouseButtonDown` SLATE_EVENT 도 있어 클릭 영역으로도 사용.

---

## 6. SOverlay (Z-order 중첩)

```cpp
SNew(SOverlay)
+SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Fill)
[ SNew(SImage).Image(BackgroundBrush) ]
+SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
[ SNew(STextBlock).Text(LOCTEXT("Loading", "Loading...")) ]
+SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top).Padding(8)
[ SNew(SButton).Text(LOCTEXT("Close", "X")) ];
```

자식 추가 순서가 Z-order. `Padding`/`HAlign`/`VAlign` 슬롯 인자.

---

## 7. SScrollBox

```cpp
SNew(SScrollBox)
.Orientation(Orient_Vertical)            // 또는 Orient_Horizontal
.OnUserScrolled_Lambda([](float CurrentOffset)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyScrollBox_OnUserScrolled);
    // ...
})
+SScrollBox::Slot()[ /* 자식 */ ]
+SScrollBox::Slot()[ /* 자식 */ ];
```

자주 쓰는 API:
- `void ScrollToStart()` / `ScrollToEnd()`
- `void ScrollDescendantIntoView(TSharedPtr<SWidget>, bool bScrollIntoView=true, EDescendantScrollDestination=...)`
- `float GetScrollOffset() const`

---

## 8. SSplitter (사용자 조절)

```cpp
SNew(SSplitter)
.Orientation(Orient_Horizontal)
+SSplitter::Slot().Value(0.3f)
[ SNew(SBorder)[ SNew(STextBlock).Text(LOCTEXT("Left", "Left Panel")) ] ]
+SSplitter::Slot().Value(0.7f)
[ SNew(SBorder)[ SNew(STextBlock).Text(LOCTEXT("Right", "Right Panel")) ] ];
```

`OnSplitterFinishedResizing_Lambda` 등 콜백.

---

## 9. SExpandableArea (펼침/접기)

```cpp
SNew(SExpandableArea)
.AreaTitle(LOCTEXT("Settings", "Settings"))
.InitiallyCollapsed(false)
.OnAreaExpansionChanged_Lambda([](bool bIsExpanded){ TRACE_CPUPROFILER_EVENT_SCOPE(SMyArea_OnExpansionChanged); })
.BodyContent()[ SNew(SVerticalBox) /* ... */ ];
```

---

## 10. SGridPanel / SUniformGridPanel

```cpp
// 가변 그리드
SNew(SGridPanel)
.FillColumn(0, 1.0f).FillColumn(1, 2.0f)
+SGridPanel::Slot(0, 0)[ SNew(STextBlock).Text(LOCTEXT("Name", "Name:")) ]
+SGridPanel::Slot(1, 0)[ SNew(SEditableTextBox) ]
+SGridPanel::Slot(0, 1)[ SNew(STextBlock).Text(LOCTEXT("Count", "Count:")) ]
+SGridPanel::Slot(1, 1)[ SNew(SSpinBox<int32>) ];

// 균일 그리드
SNew(SUniformGridPanel)
.SlotPadding(FMargin(4))
.MinDesiredSlotWidth(100)
.MinDesiredSlotHeight(100)
+SUniformGridPanel::Slot(0, 0)[ /* ... */ ]
+SUniformGridPanel::Slot(1, 0)[ /* ... */ ];
```

---

## 11. SConstraintCanvas (Anchor 기반 — UMG UCanvasPanel 의 Slate 베이스)

```cpp
SNew(SConstraintCanvas)
+SConstraintCanvas::Slot()
.Anchors(FAnchors(0, 0, 1, 1))               // Stretch 전체
.Offset(FMargin(20, 20, 20, 20))
[ SNew(SImage).Image(MinimapBrush) ];
```

---

## 12. SSafeZone / SDPIScaler / SScaleBox

```cpp
SNew(SSafeZone)
.IsTitleSafe(true)                     // TitleSafe vs ActionSafe
.Padding(20)
[ MainContent ];

SNew(SDPIScaler)
.DPIScale(1.5f)                       // 1.0 = 일반, 0.5 = 축소, 2.0 = 확대
[ MainContent ];

SNew(SScaleBox)
.Stretch(EStretch::ScaleToFit)        // None / Fill / ScaleToFit / ScaleToFill / ScaleBySafeZone / UserSpecified / UserSpecifiedWithClipping / ScaleToFitX / Y
[ ImageContent ];
```

---

## 13. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `SCompoundWidget::Construct` | (자체) | 위젯 빌드 |
| `SBoxPanel::OnArrangeChildren(FGeometry, FArrangedChildren&)` | (자체) | 자식 배치 |
| `SBoxPanel::ComputeDesiredSize(float)` | (자체) | 사이즈 계산 |
| `SOverlay::OnArrangeChildren` | (자체) | Z-order 배치 |
| `SScrollBox::Tick` | **FIRST** | 매 프레임 스크롤 진행 |

사용자 정의 패널 작성 시 `SPanel` 자손 — `OnArrangeChildren` / `ComputeDesiredSize` / `GetChildren` PURE override 의무.

---

## 14. 함정

| 함정 | 회피 |
|------|------|
| `SVerticalBox::Slot().FillHeight(1.0f)` 만 — 모든 자식 Auto 일 때 Fill 의미 X | 최소 한 개 Fill 자식 필요 시에만 |
| `SOverlay` Z-order 직접 설정 시도 | 자식 추가 순서로 결정 — 변경하려면 RemoveSlot + 다시 +SOverlay::Slot |
| `SScrollBox` 안 자식 100+ | `SListView` 로 대체 |
| `SBox::WidthOverride` 매 프레임 변경 | TSlateAttribute 활용 (자동 인밸리데이션) |
| `SSplitter::Value` 사용자 조절 후 저장 안 함 | `OnSplitterFinishedResizing` 콜백에서 저장 |
| `SConstraintCanvas` Anchor 매 프레임 변경 | TSlateAttribute |
| `SSafeZone` 빠뜨림 (모바일) | 메인 HUD 루트는 SSafeZone 으로 감쌈 |
| `SDPIScaler` 와 `SScaleBox` 차이 | SDPIScaler는 DPI 스케일, SScaleBox는 콘텐츠 fit |
| `SBoxPanel` 매 프레임 자식 추가/제거 | ChildOrder 인밸리데이션 — 변경된 자식만 |
| `Tick` override 시 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) |

---

## 15. 에디터 전용? 🛠

런타임 — **게임/에디터 공통**.

---

## 16. 관련 sub-skill

- [`UMG/PanelWidgets`](../../UMG/references/PanelWidgets.md) — UVerticalBox/UCanvasPanel/UScrollBox 등 (BP 래퍼)
- [`Slate/CommonWidgets`](../CommonWidgets/SKILL.md) — SButton/SCheckBox 자식 위젯
- [`Slate/TextInput`](../TextInput/SKILL.md) — STextBlock 자식
- [`SlateCore/Layout`](../../SlateCore/references/Layout.md) — FGeometry / FArrangedChildren / FChildren / FMargin / EVisibility / SBoxPanel::FSlot 베이스
- [`SlateCore/SWidget`](../../SlateCore/references/SWidget.md) — SPanel 베이스 (사용자 정의 패널)
- 교차: [`06_InvalidationHotspots.md §2.5`](../../../references/06_InvalidationHotspots.md) (panel 별 hotspot) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
