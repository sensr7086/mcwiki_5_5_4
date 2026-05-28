---
name: slate-commonwidgets
description: SButton + SCheckBox + SComboBox + SImage + SProgressBar + SSpinBox + STextBlock - 일반 위젯.
---

# Slate · CommonWidgets sub-skill

> **모듈**: Slate (Tier 3 — 게임/에디터 공통)
> **위치**: `Engine/Source/Runtime/Slate/Public/Widgets/Input/` (TextInput 외) + 일부 보조
> **다루는 범위**: 표준 입력/일반 위젯 — `SButton`·`SCheckBox`·`SComboBox`·`SComboButton`·`SHyperlink`·`SSlider`·`SSpinBox`·`SInputKeySelector`·`SSegmentedControl`·`SExpandableButton`·`SEditableLabel` 등.

---

## 1. 개요

Slate 의 **표준 인터랙티브 위젯** 묶음. UMG 의 `UButton`/`UCheckBox`/`UComboBox*`/`USlider`/`USpinBox` ([`UMG/StandardWidgets`](../../UMG/references/StandardWidgets.md)) 가 이들의 BP 래퍼. 인하우스 툴에서는 직접 SButton 등 사용.

---

## 2. 핵심 헤더 (Slate/Public/Widgets/Input/)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `SButton.h` | `SButton` | 버튼 (기본) |
| `SCheckBox.h` | `SCheckBox` | 체크박스 (3-상태 가능) |
| `SComboBox.h` | `SComboBox<OptionType>` | 일반 콤보박스 (template) |
| `SComboButton.h` | `SComboButton` | 콤보 버튼 (메뉴 안에 임의 위젯) |
| `STextComboBox.h` | `STextComboBox` | 텍스트 콤보 (FString 옵션) |
| `SEditableComboBox.h` | `SEditableComboBox<OptionType>` | 편집 가능 콤보 |
| `SHyperlink.h` | `SHyperlink` | 클릭 가능 링크 |
| `SRichTextHyperlink.h` | `SRichTextHyperlink` | RichText 안 하이퍼링크 |
| `SSlider.h` | `SSlider` | 슬라이더 (0~1) |
| `SSpinBox.h` | `SSpinBox<NumericType>` | 숫자 스핀박스 (template) |
| `SNumericEntryBox.h` | `SNumericEntryBox<NumericType>` | 숫자 입력 박스 |
| `SNumericDropDown.h` | `SNumericDropDown<NumericType>` | 드롭다운 |
| `SVectorInputBox.h` | `SVectorInputBox` | 벡터 (X/Y/Z) |
| `SRotatorInputBox.h` | `SRotatorInputBox` | 회전자 (Pitch/Yaw/Roll) |
| `SInputKeySelector.h` | `SInputKeySelector` | 단축키 선택 |
| `SSegmentedControl.h` | `SSegmentedControl<OptionType>` | 세그먼트 컨트롤 (탭형 선택) |
| `SExpandableButton.h` | `SExpandableButton` | 접히는 버튼 |
| `SEditableLabel.h` | `SEditableLabel` | 더블클릭 편집 라벨 |
| `SMenuAnchor.h` | `SMenuAnchor` | 팝업 메뉴 앵커 |
| `SSubMenuHandler.h` | `SSubMenuHandler` | 서브메뉴 |

---

## 3. SButton (가장 자주)

### 3.1 SLATE_BEGIN_ARGS 핵심

| 인자 | 의미 |
|------|------|
| `SLATE_EVENT(FOnClicked, OnClicked)` | 클릭 콜백 |
| `SLATE_EVENT(FSimpleDelegate, OnPressed)` | 누름 |
| `SLATE_EVENT(FSimpleDelegate, OnReleased)` | 뗌 |
| `SLATE_EVENT(FSimpleDelegate, OnHovered)` / `OnUnhovered` | 호버 |
| `SLATE_ATTRIBUTE(const FButtonStyle*, ButtonStyle)` | 스타일 (Normal/Hovered/Pressed/Disabled) |
| `SLATE_ATTRIBUTE(FSlateColor, ButtonColorAndOpacity)` | 틴트 |
| `SLATE_ATTRIBUTE(FSlateColor, ForegroundColor)` | 자식 위젯 전경색 |
| `SLATE_ATTRIBUTE(FMargin, ContentPadding)` | 안쪽 여백 |
| `SLATE_ATTRIBUTE(EHorizontalAlignment, HAlign)` | 정렬 |
| `SLATE_ARGUMENT(EButtonClickMethod::Type, ClickMethod)` | DownAndUp / MouseDown / MouseUp |
| `SLATE_ARGUMENT(bool, IsFocusable)` | 포커스 가능? |
| `SLATE_DEFAULT_SLOT(FArguments, Content)` | 자식 위젯 |

### 3.2 사용

```cpp
SNew(SButton)
.OnClicked_Lambda([this]() -> FReply
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnButtonClicked);
    // 처리
    return FReply::Handled();
})
.HAlign(HAlign_Center)
.ContentPadding(FMargin(8, 4))
[
    SNew(STextBlock).Text(LOCTEXT("Click", "Click Me"))
]
```

---

## 4. SCheckBox

### 4.1 SLATE_BEGIN_ARGS 핵심

| 인자 | 의미 |
|------|------|
| `SLATE_ATTRIBUTE(ECheckBoxState, IsChecked)` | 상태 (Checked/Unchecked/Undetermined) |
| `SLATE_EVENT(FOnCheckStateChanged, OnCheckStateChanged)` | 변경 |
| `SLATE_ATTRIBUTE(const FCheckBoxStyle*, Style)` | 스타일 |
| `SLATE_DEFAULT_SLOT(FArguments, Content)` | 라벨 (옵션) |

### 4.2 사용

```cpp
SNew(SCheckBox)
.IsChecked_Lambda([this]() { return bMyFlag ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; })
.OnCheckStateChanged_Lambda([this](ECheckBoxState NewState)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnCheckChanged);
    bMyFlag = (NewState == ECheckBoxState::Checked);
})
[
    SNew(STextBlock).Text(LOCTEXT("Enable", "Enable Feature"))
];
```

---

## 5. SComboBox<T> (template)

### 5.1 사용 패턴

```cpp
TArray<TSharedPtr<FString>> Options;
Options.Add(MakeShared<FString>(TEXT("Apple")));
Options.Add(MakeShared<FString>(TEXT("Banana")));
TSharedPtr<FString> CurrentSelection = Options[0];

SAssignNew(ComboBox, SComboBox<TSharedPtr<FString>>)
.OptionsSource(&Options)
.InitiallySelectedItem(CurrentSelection)
.OnGenerateWidget_Lambda([](TSharedPtr<FString> Item)
{
    return SNew(STextBlock).Text(FText::FromString(*Item));
})
.OnSelectionChanged_Lambda([this](TSharedPtr<FString> NewSelection, ESelectInfo::Type)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnComboSelection);
    CurrentSelection = NewSelection;
})
[
    SNew(STextBlock).Text_Lambda([this]() { return FText::FromString(*CurrentSelection); })
];
```

### 5.2 STextComboBox (편의)

`TArray<TSharedPtr<FString>>` 전용 — 자동으로 `STextBlock` 생성:

```cpp
SNew(STextComboBox)
.OptionsSource(&Options)
.OnSelectionChanged_Lambda(...);
```

---

## 6. SHyperlink

```cpp
SNew(SHyperlink)
.Text(LOCTEXT("LinkText", "Click here for help"))
.OnNavigate_Lambda([]()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnHyperlinkClicked);
    FPlatformProcess::LaunchURL(TEXT("https://docs.unrealengine.com"), nullptr, nullptr);
});
```

---

## 7. SSlider

```cpp
SNew(SSlider)
.Value_Lambda([this]() { return MyVolume; })
.MinValue(0.0f)
.MaxValue(1.0f)
.StepSize(0.1f)
.OnValueChanged_Lambda([this](float NewValue)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnSliderChanged);
    MyVolume = NewValue;
})
.OnMouseCaptureBegin_Lambda([](){ /* 드래그 시작 */ })
.OnMouseCaptureEnd_Lambda([](){ /* 드래그 끝 */ });
```

---

## 8. SSpinBox<NumericType> (template)

```cpp
SNew(SSpinBox<float>)
.Value_Lambda([this]() { return MyValue; })
.MinValue(0.0f)
.MaxValue(100.0f)
.MinSliderValue(0.0f)
.MaxSliderValue(50.0f)
.Delta(0.1f)                     // 한 step
.SliderExponent(1.5f)            // log scale
.OnValueChanged_Lambda([this](float NewValue) { MyValue = NewValue; })
.OnValueCommitted_Lambda([this](float NewValue, ETextCommit::Type) { MyValue = NewValue; });
```

---

## 9. SVectorInputBox / SRotatorInputBox

```cpp
SNew(SVectorInputBox)
.X_Lambda([this]() { return TOptional<FVector::FReal>(MyVec.X); })
.Y_Lambda([this]() { return TOptional<FVector::FReal>(MyVec.Y); })
.Z_Lambda([this]() { return TOptional<FVector::FReal>(MyVec.Z); })
.OnXChanged_Lambda([this](FVector::FReal V) { MyVec.X = V; })
.OnYChanged_Lambda([this](FVector::FReal V) { MyVec.Y = V; })
.OnZChanged_Lambda([this](FVector::FReal V) { MyVec.Z = V; });
```

디테일 패널 / 디버그 도구에서 자주 사용.

---

## 10. SInputKeySelector — 단축키 캡처

```cpp
SNew(SInputKeySelector)
.SelectedKey_Lambda([this]() { return MyChord; })
.OnKeySelected_Lambda([this](const FInputChord& NewChord)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnKeySelected);
    MyChord = NewChord;
});
```

`Edit > Editor Preferences > Keyboard Shortcuts` 같은 UI에서 사용. `EditorWidgets/SInputChord` 와 유사하지만 SInputKeySelector 는 더 통합된 형태.

---

## 11. SSegmentedControl<OptionType>

탭 형태의 다중 선택:

```cpp
TArray<TSharedPtr<FString>> Modes = { MakeShared<FString>("Easy"), MakeShared<FString>("Normal"), MakeShared<FString>("Hard") };

SNew(SSegmentedControl<TSharedPtr<FString>>)
.Value_Lambda([this]() { return CurrentMode; })
.OnValueChanged_Lambda([this](TSharedPtr<FString> NewMode) { CurrentMode = NewMode; })
+SSegmentedControl<TSharedPtr<FString>>::Slot(Modes[0]).Text(LOCTEXT("Easy", "Easy"))
+SSegmentedControl<TSharedPtr<FString>>::Slot(Modes[1]).Text(LOCTEXT("Normal", "Normal"))
+SSegmentedControl<TSharedPtr<FString>>::Slot(Modes[2]).Text(LOCTEXT("Hard", "Hard"));
```

---

## 12. SMenuAnchor — 팝업 메뉴 앵커

```cpp
SAssignNew(MenuAnchor, SMenuAnchor)
.Placement(MenuPlacement_BelowAnchor)
.OnGetMenuContent_Lambda([this]()
{
    return SNew(SBox)[ /* 팝업 콘텐츠 */ ];
})
[
    SNew(SButton)
    .OnClicked_Lambda([this]() -> FReply
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_TogglePopup);
        MenuAnchor->SetIsOpen(!MenuAnchor->IsOpen());
        return FReply::Handled();
    })
    [ SNew(STextBlock).Text(LOCTEXT("Open", "Open Menu")) ]
];
```

---

## 13. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `SCompoundWidget::Construct` | (자체) | 위젯 빌드 |
| `SButton::OnMouseButtonDown/Up` | **FIRST** | 클릭 처리 |
| `SButton::OnPaint` | (자체) | 스타일 페인트 |
| `SCheckBox::OnMouseButtonUp` | **FIRST** | 토글 |

대부분의 SLATE 위젯은 직접 override 안 하고 SLATE_EVENT 콜백으로 처리.

---

## 14. 함정

| 함정 | 회피 |
|------|------|
| `OnClicked` 람다 강 캡처 | TWeakPtr / `CreateWeakLambda` |
| `OnClicked` 콜백 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) |
| `SButton` Content 누락 | 빈 버튼 — 항상 자식 위젯 명시 |
| `SCheckBox` 3-상태 무시 | `ECheckBoxState::Undetermined` 처리 |
| `SComboBox<T>` Options 가 빈 배열 | nullptr 반환 — 검사 |
| `SSlider::OnValueChanged` 매 픽셀마다 호출 | `OnMouseCaptureEnd` 에서 최종 값만 저장하는 패턴 |
| `SSpinBox` Delta 누락 | 키 입력으로 변경 안 됨 |
| `SVectorInputBox` 더블 vs 플로트 — `FVector::FReal` 일관성 | 5.x 부터 double 기본 |
| `SHyperlink::OnNavigate` 안 외부 URL — `FPlatformProcess::LaunchURL` 사용 시 보안 검사 | 사용자 신뢰 가능한 URL만 |

---

## 15. 에디터 전용? 🛠

런타임 — **게임/에디터 공통**.

---

## 16. 관련 sub-skill

- [`UMG/StandardWidgets`](../../UMG/references/StandardWidgets.md) — UButton/UCheckBox/UComboBox/USlider/USpinBox (BP 래퍼)
- [`Slate/TextInput`](../TextInput/SKILL.md) — STextBlock / SEditableText (자식 위젯으로 자주 들어감)
- [`Slate/LayoutWidgets`](../LayoutWidgets/SKILL.md) — SHorizontalBox / SVerticalBox 안에 배치
- [`SlateCore/Styling`](../../SlateCore/references/Styling.md) — FButtonStyle / FCheckBoxStyle
- [`SlateCore/Input`](../../SlateCore/references/Input.md) — FReply / FInputChord
- [`Slate/Commands`](../Commands/SKILL.md) — SButton 과 TCommands<T> 통합
- 교차: [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (OnClicked / OnValueChanged 람다 스코프)
