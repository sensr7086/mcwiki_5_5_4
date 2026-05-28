---
name: slate-textinput
description: SEditableText + SEditableTextBox + SMultiLineEditableText + STextEntryPopup - 텍스트 입력.
---

# Slate · TextInput sub-skill

> **모듈**: Slate (Tier 3 — 게임/에디터 공통)
> **위치**: `Engine/Source/Runtime/Slate/Public/Widgets/Input/` + `Public/Widgets/Text/`
> **다루는 범위**: 텍스트 입력 위젯 — `SEditableText`·`SEditableTextBox`·`SMultiLineEditableText(Box)`·`SSearchBox`·`SSuggestionTextBox`·`STextEntryPopup`·`SRichTextBlock`·`SInlineEditableTextBlock`·`STextBlock` 등.

---

## 1. 개요

UE Slate 의 **텍스트 표시 + 입력** 위젯 묶음. UMG 의 `UEditableText`/`UEditableTextBox`/`UTextBlock`/`URichTextBlock` ([`UMG/StandardWidgets`](../../UMG/references/StandardWidgets.md)) 가 이들의 BP 래퍼. 인하우스 툴에서는 직접 SEditableText 사용.

핵심 묶음:
- **단일 라인 입력**: `SEditableText` / `SEditableTextBox` / `SSearchBox` / `STextEntryPopup` / `SSuggestionTextBox` / `SInlineEditableTextBlock`
- **다중 라인 입력**: `SMultiLineEditableText` / `SMultiLineEditableTextBox`
- **읽기 전용 표시**: `STextBlock` / `SRichTextBlock` / `STextScroller`
- **공통 인터페이스**: `IVirtualKeyboardEntry` / `ISlateEditableTextWidget`

---

## 2. 핵심 헤더

### 2.1 입력 (Widgets/Input/)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `SEditableText.h` | `SEditableText` | 단일 라인 입력 (편집 가능) |
| `SEditableTextBox.h` | `SEditableTextBox` | 박스 스타일 (테두리 포함) |
| `SMultiLineEditableTextBox.h` | `SMultiLineEditableTextBox` | 다중 라인 박스 |
| `SSearchBox.h` | `SSearchBox` | 검색 박스 (X 버튼 포함) |
| `SSuggestionTextBox.h` | `SSuggestionTextBox` | 자동완성 |
| `STextEntryPopup.h` | `STextEntryPopup` | 팝업 입력 |
| `STextComboBox.h` / `STextComboPopup.h` | `STextComboBox` / `STextComboPopup` | 텍스트 콤보 |
| `IVirtualKeyboardEntry.h` | `IVirtualKeyboardEntry` 인터페이스 | 모바일 가상 키보드 |
| `NumericTypeInterface.h` | `INumericTypeInterface<T>` | 숫자 입력 인터페이스 (SSpinBox/SNumericEntryBox) |

### 2.2 텍스트 표시 (Widgets/Text/)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `STextBlock.h` | `STextBlock` | 단일 라인 표시 (읽기 전용) |
| `SRichTextBlock.h` | `SRichTextBlock` | 마크업 + 인라인 위젯 |
| `SMultiLineEditableText.h` | `SMultiLineEditableText` | 다중 라인 (베이스) |
| `SInlineEditableTextBlock.h` | `SInlineEditableTextBlock` | 더블클릭 시 편집 모드 (이름 변경 등) |
| `STextScroller.h` | `STextScroller` | 스크롤 텍스트 |
| `ISlateEditableTextWidget.h` | `ISlateEditableTextWidget` 인터페이스 | 편집 가능 텍스트 |
| `SlateEditableTextLayout.h` | `FSlateEditableTextLayout` | 편집 레이아웃 (내부) |
| `SlateEditableTextTypes.h` | enum/struct | 편집 타입 |
| `SlateTextBlockLayout.h` | `FSlateTextBlockLayout` | 텍스트 블록 레이아웃 (내부) |

---

## 3. SEditableText / SEditableTextBox (단일 라인)

### 3.1 SLATE_BEGIN_ARGS 핵심

| 인자 | 의미 |
|------|------|
| `SLATE_ATTRIBUTE(FText, Text)` | 텍스트 |
| `SLATE_ATTRIBUTE(FText, HintText)` | placeholder |
| `SLATE_ATTRIBUTE(bool, IsReadOnly)` | 읽기 전용 |
| `SLATE_ATTRIBUTE(bool, IsPassword)` | 비밀번호 마스킹 |
| `SLATE_EVENT(FOnTextChanged, OnTextChanged)` | 매 키 입력 |
| `SLATE_EVENT(FOnTextCommitted, OnTextCommitted)` | Enter / 포커스 이탈 |
| `SLATE_ATTRIBUTE(FSlateFontInfo, Font)` | 폰트 |
| `SLATE_ARGUMENT(bool, ClearKeyboardFocusOnCommit)` | Commit 후 포커스 해제 |
| `SLATE_ARGUMENT(int32, MaximumLength)` | 최대 길이 |

### 3.2 사용

```cpp
SAssignNew(InputBox, SEditableTextBox)
.Text_Lambda([this]() { return FText::FromString(CurrentValue); })
.HintText(LOCTEXT("Hint", "Enter name..."))
.OnTextChanged_Lambda([this](const FText& NewText)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnTextChanged);
    // 매 키 입력 — 가벼운 처리만
})
.OnTextCommitted_Lambda([this](const FText& NewText, ETextCommit::Type CommitType)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnTextCommitted);
    if (CommitType == ETextCommit::OnEnter || CommitType == ETextCommit::OnUserMovedFocus)
    {
        // 검증 + 저장 (무거운 작업 OK)
    }
});
```

> **🚨 OnTextChanged 함정**: IME 입력 중 매 키 입력마다 호출 — 외부 검증/네트워크 호출 금지. **`OnTextCommitted` 사용 권장** ([`06_InvalidationHotspots.md §2.3`](../../../references/06_InvalidationHotspots.md)).

---

## 4. SSearchBox

`SEditableTextBox` 확장 — X 버튼 + 검색 아이콘 + Throttle:

| 인자 | 의미 |
|------|------|
| `SLATE_EVENT(FOnTextChanged, OnTextChanged)` | (디바운스 적용) |
| `SLATE_EVENT(FOnTextCommitted, OnTextCommitted)` | |
| `SLATE_ARGUMENT(float, DelayChangeNotificationsWhileTyping)` | 입력 중 디바운스 시간 |

```cpp
SNew(SSearchBox)
.OnTextChanged_Lambda([this](const FText& NewText)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnSearchChanged);
    PerformSearch(NewText.ToString());
});
```

---

## 5. SMultiLineEditableText / SMultiLineEditableTextBox (다중 라인)

```cpp
SNew(SMultiLineEditableTextBox)
.Text(LOCTEXT("Default", "Default content..."))
.AllowMultiLine(true)
.AutoWrapText(true)
.OnTextChanged_Lambda(...);
```

코드 에디터 / 에세이 입력 / 채팅 박스 등에 사용.

---

## 6. SSuggestionTextBox — 자동완성

```cpp
TArray<FString> Suggestions = { TEXT("Apple"), TEXT("Banana"), TEXT("Cherry") };

SNew(SSuggestionTextBox)
.SuggestionListMaxHeight(200.0f)
.OnTextChanged_Lambda([this](const FText& Text) { /* 변경 */ })
.OnShowingSuggestions_Lambda([Suggestions](const FString& InCurrentText, TArray<FString>& OutSuggestions)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnShowingSuggestions);
    for (const FString& S : Suggestions)
    {
        if (S.StartsWith(InCurrentText)) { OutSuggestions.Add(S); }
    }
});
```

---

## 7. STextBlock (읽기 전용)

```cpp
SNew(STextBlock)
.Text(LOCTEXT("Hello", "Hello World"))
.Font(FAppStyle::Get().GetFontStyle("LargeFont"))
.ColorAndOpacity(FSlateColor(FLinearColor::White))
.AutoWrapText(true)
.Justification(ETextJustify::Center);
```

자주 쓰는 API:
- `void SetText(const TAttribute<FText>&)` — 자동 인밸리데이션
- `void SetFont(const FSlateFontInfo&)`
- `void SetColorAndOpacity(const FSlateColor&)`
- `void SetJustification(ETextJustify::Type)`

> **🚨 SetText 매 프레임 호출 함정** — 자동 인밸리데이션 → DrawCall 증가. 변경 시에만 호출.

---

## 8. SRichTextBlock (마크업)

```cpp
SNew(SRichTextBlock)
.Text(LOCTEXT("Markup", "<RichText.Header>Title</> Body with <RichText.Highlight>highlight</>."))
.TextStyle(&FAppStyle::Get().GetWidgetStyle<FTextBlockStyle>("RichTextBlock.Default"))
.DecoratorStyleSet(&FAppStyle::Get())
+SRichTextBlock::ImageDecorator()
+SRichTextBlock::HyperlinkDecorator(TEXT("UrlClick"), FSlateHyperlinkRun::FOnClick::CreateLambda(
    [](const FSlateHyperlinkRun::FMetadata& Meta)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_HyperlinkClicked);
        // ...
    }));
```

> **🚨 RichText 인밸리데이션 다발** — [`06_InvalidationHotspots.md §2.2`](../../../references/06_InvalidationHotspots.md) 참조. SetText 잦은 호출 금지.

---

## 9. SInlineEditableTextBlock (더블클릭 편집)

```cpp
SNew(SInlineEditableTextBlock)
.Text_Lambda([this]() { return FText::FromString(MyName); })
.OnTextCommitted_Lambda([this](const FText& NewText, ETextCommit::Type)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_OnNameCommitted);
    MyName = NewText.ToString();
})
.IsSelected(this, &SMyWidget::IsItemSelected);    // 선택 시에만 편집 가능
```

아웃라이너의 액터 이름 변경 / 컨텐츠 브라우저의 에셋 이름 변경 등에 사용.

---

## 10. STextEntryPopup (팝업 입력)

```cpp
TSharedRef<STextEntryPopup> Popup = SNew(STextEntryPopup)
.Label(LOCTEXT("EnterName", "Enter Name:"))
.OnTextCommitted_Lambda([this](const FText& Text, ETextCommit::Type Type)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyWidget_PopupCommitted);
    if (Type == ETextCommit::OnEnter) { /* ... */ }
});

FSlateApplication::Get().PushMenu(...,Popup,...);
```

이름 변경 다이얼로그 / 비밀번호 입력 등.

---

## 11. ISlateEditableTextWidget (인터페이스)

`SEditableText` / `SMultiLineEditableText` 가 구현. 편집 가능한 텍스트의 공통 API:

```cpp
virtual FText GetText() const = 0;
virtual void SetText(const FText& InText) = 0;
virtual bool IsReadOnly() const = 0;
virtual void Refresh() = 0;
// ... 기타
```

---

## 12. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `SCompoundWidget::Construct` | (자체) | 위젯 빌드 |
| `SEditableText::OnKeyDown` | **FIRST** + check | 키 처리 |
| `SEditableText::OnFocusReceived/Lost` | **FIRST** | 포커스 |
| `STextBlock::OnPaint` | (자체) | 페인트 |

---

## 13. 함정

| 함정 | 회피 |
|------|------|
| `OnTextChanged` 안에서 외부 검증·네트워크 호출 | `OnTextCommitted` 사용 |
| `STextBlock::SetText` 매 프레임 호출 | 변경 시에만 호출 (이전값 비교) |
| `SRichTextBlock::SetText` 잦은 호출 | 마크업 파싱 + STextBlock 재생성 — 매우 무거움. ScrollBox+VerticalBox 패턴 |
| 비밀번호 입력 — `IsPassword` 누락 | UPROPERTY 와 별개로 SLATE 인자에 명시 |
| 다중 라인 입력 — `AllowMultiLine`/`AutoWrapText` 누락 | 둘 다 명시 |
| `SInlineEditableTextBlock` `IsSelected` 누락 | 항상 편집 모드 — 의도 X |
| Hyperlink 클릭 람다 강 캡처 | TWeakPtr |
| 콜백 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) — IME 매 키 입력 + 자동완성 콜백 등 모두 |
| 모바일 가상 키보드 — `IVirtualKeyboardEntry` 미구현 | (자동 처리되지만) 커스텀 입력 시 인터페이스 구현 |

---

## 14. 에디터 전용? 🛠

런타임 — **게임/에디터 공통**. UMG 의 `UEditableText`/`UTextBlock`/`URichTextBlock` 이 본 위젯의 BP 래퍼.

---

## 15. 관련 sub-skill

- [`UMG/StandardWidgets`](../../UMG/references/StandardWidgets.md) — UEditableText / UTextBlock / URichTextBlock (BP 래퍼)
- [`SlateCore/Text`](../../SlateCore/references/Text.md) — FSlateFontInfo / HarfBuzz / FreeType
- [`SlateCore/Drawing`](../../SlateCore/references/Drawing.md) — 자동 인밸리데이션
- [`SlateCore/Input`](../../SlateCore/references/Input.md) — FKeyEvent / FCharacterEvent
- [`Slate/CommonWidgets`](../CommonWidgets/SKILL.md) — SButton·SCheckBox 등 표준 위젯
- 교차: [`06_InvalidationHotspots.md §2.2 / §2.3`](../../../references/06_InvalidationHotspots.md) (RichText / EditableText 핫스팟) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
