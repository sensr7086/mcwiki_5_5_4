---
name: umg-standardwidgets
description: UButton + UImage + UCheckBox + UTextBlock + UProgressBar + URichTextBlock + UComboBoxString - 표준 위젯.
---

# UMG · StandardWidgets sub-skill

> **모듈**: UMG (Tier 3 · Slate 카테고리)
> **위치**: `Engine/Source/Runtime/UMG/Public/Components/`
> **다루는 범위**: 게임 UI에서 가장 자주 쓰이는 표준 위젯 — Button / CheckBox / Image / TextBlock / RichTextBlock / ProgressBar / Throbber / Slider / SpinBox / EditableText / ComboBox 등.

---

## 1. 개요

`UWidget` 자손 중 **실제 시각·인터랙션을 담당하는 단일-목적 위젯** 들. 대부분 `UContentWidget` 또는 `UWidget` 직속 자손이며, 내부에 대응하는 `SXxx` Slate 위젯 1개를 보유. **`SynchronizeProperties()`** 는 모두 부모 `UWidget` 패턴 (Super FIRST + 캐시된 SXxx 에 setter 위임) 을 따른다.

> **인밸리데이션 함정 의무**: 본 sub-skill 의 위젯 중 다수(특히 RichText/EditableText/ProgressBar/Throbber)는 [`06_InvalidationHotspots.md`](../../../references/06_InvalidationHotspots.md) 의 핫스팟 표에 등장. 다중 갱신·매 프레임 페인트 함정 주의.

---

## 2. 핵심 헤더와 클래스

### 2.1 베이스 사슬 별 분류

| 베이스 | 위젯 |
|--------|------|
| `UWidget` 직속 | `UImage` · `UProgressBar` · `UThrobber` · `UCircularThrobber` · `USlider` · `USpinBox` · `UEditableText` · `UEditableTextBox` · `UComboBox` · `UComboBoxString` · `UComboBoxKey` |
| `UContentWidget` (1개 자식) | `UButton` · `UCheckBox` · `UBorder` · `UNamedSlot` · `UInvalidationBox` · `UScaleBox` · `USizeBox` · `USafeZone` · `UMenuAnchor` · `URetainerBox` · `UExpandableArea` |
| `UTextLayoutWidget` (텍스트 레이아웃 공통) | `UTextBlock` · `URichTextBlock` · `UMultiLineEditableText` · `UMultiLineEditableTextBox` |

### 2.2 핵심 헤더 (5.7.4 라인)

| 클래스 | 헤더 | 클래스 라인 |
|--------|------|-------------|
| `UButton` | `Button.h` | L32 |
| `UCheckBox` | `CheckBox.h` | L31 |
| `UImage` | `Image.h` | L30 |
| `UTextBlock` | `TextBlock.h` | L23 |
| `URichTextBlock` | `RichTextBlock.h` | L39 |
| `URichTextBlockDecorator` | `RichTextBlockDecorator.h` | L45 |
| `UProgressBar` | `ProgressBar.h` | L21 |
| `UThrobber` | `Throbber.h` | L19 |
| `UCircularThrobber` | `CircularThrobber.h` | L22 |
| `USlider` | `Slider.h` | L26 |
| `USpinBox` | `SpinBox.h` | L19 |
| `UEditableText` | `EditableText.h` | L25 |
| `UEditableTextBox` | `EditableTextBox.h` | L26 |
| `UMultiLineEditableText` | `MultiLineEditableText.h` | L21 |
| `UMultiLineEditableTextBox` | `MultiLineEditableTextBox.h` | L21 |
| `UComboBoxString` | `ComboBoxString.h` | L21 |
| `UComboBoxKey` | `ComboBoxKey.h` | L18 |

---

## 3. 자주 쓰는 API (위젯별)

### 3.1 UButton (`Button.h`)

| API | 메모 |
|-----|------|
| `void SetStyle(const FButtonStyle&)` | `FButtonStyle` 자체 교체 (Normal/Hovered/Pressed/Disabled 4상태) |
| `void SetColorAndOpacity(FLinearColor)` / `SetBackgroundColor(FLinearColor)` | 틴트 |
| `void SetClickMethod/TouchMethod/PressMethod(...)` | 인터랙션 정책 |
| `void SetIsEnabled(bool)` | (UWidget 베이스 상속) — 비활성 시 Disabled 스타일 자동 |
| 이벤트 (BlueprintAssignable) | `OnClicked` · `OnPressed` · `OnReleased` · `OnHovered` · `OnUnhovered` |

**함정**: `UButton` 은 **단일 자식 콘텐츠** (`UContentWidget`) — 자식이 없으면 텍스트가 안 보인다. 디자이너에서 `Button > TextBlock` 패턴이 표준.

### 3.2 UCheckBox (`CheckBox.h`)

| API | 메모 |
|-----|------|
| `ECheckBoxState GetCheckedState()` / `void SetCheckedState(ECheckBoxState)` | 3상태 (Unchecked/Checked/Undetermined) |
| `bool IsChecked()` / `void SetIsChecked(bool)` | 2상태 편의 |
| `void SetClickMethod(...)` | |
| 이벤트 | `OnCheckStateChanged(bool bIsChecked)` |

**FieldNotify**: `CheckedState` 는 `meta=(FieldNotify)` 마킹 → MVVM 통합 (자세한 [`UMG/references/ViewModel.md`](../ViewModel/SKILL.md)).

### 3.3 UImage (`Image.h`)

| API | 메모 |
|-----|------|
| `void SetBrush(const FSlateBrush&)` | 전체 브러시 교체 |
| `void SetBrushFromTexture(UTexture2D*, bool bMatchSize=false)` | 텍스처 |
| `void SetBrushFromMaterial(UMaterialInterface*)` | 머티리얼 |
| `void SetBrushFromAtlasInterface(TScriptInterface<ISlateTextureAtlasInterface>, bool bMatchSize=false)` | 아틀라스 |
| `void SetBrushFromSoftTexture(TSoftObjectPtr<UTexture2D>, bool bMatchSize=false)` | 소프트 참조 — 비동기 로드 |
| `void SetBrushFromSoftMaterial(TSoftObjectPtr<UMaterialInterface>)` | 소프트 머티리얼 |
| `void SetColorAndOpacity(FLinearColor)` | 틴트 (sRGB) |
| `UMaterialInstanceDynamic* GetDynamicMaterial()` | MID 생성/획득 — Render 카테고리 통합점 |

**함정**: `SetBrushFromTexture(true)` 의 `bMatchSize` 는 **텍스처 픽셀 크기로 위젯 사이즈 강제** — 디자이너 의도와 충돌하면 false 권장.

### 3.4 UTextBlock (`TextBlock.h`)

| API | 메모 |
|-----|------|
| `FText GetText()` / `void SetText(FText)` | **`FText` 사용 의무** — `FString` 금지 (지역화) |
| `void SetColorAndOpacity(FSlateColor)` | |
| `void SetFont(FSlateFontInfo)` | 폰트 통째 교체 |
| `void SetMinDesiredWidth(float)` | 최소 폭 |
| `void SetShadowColorAndOpacity(FLinearColor)` / `SetShadowOffset(FVector2D)` | 그림자 |
| `void SetJustification(ETextJustify::Type)` | Left/Center/Right |
| `void SetAutoWrapText(bool)` | 자동 줄바꿈 |

**함정**:
- `SetText` 매 프레임 호출 → STextBlock 자동 인밸리데이션 → DrawCall 증가. **변경 시에만** 호출.
- `FText::FromString(TEXT("..."))` 는 지역화 우회 — 런타임 동적 문자열에만 사용. **상수 텍스트는 `LOCTEXT`/`NSLOCTEXT`**.

### 3.5 URichTextBlock (`RichTextBlock.h`)

| API | 메모 |
|-----|------|
| `void SetText(FText)` | 마크업 포함 (`<RichTextStyle Color="...">` 등) |
| `void SetTextStyleSet(const TObjectPtr<UDataTable>&)` | `RichTextStyleRow` 행 구조 데이터 테이블 (스타일셋) |
| `void SetDecorators(const TArray<TSubclassOf<URichTextBlockDecorator>>&)` | 디코레이터 (이미지·인라인 위젯 등) |

**🚨 RichText 인밸리데이션 다발 함정** (자세한 [`06_InvalidationHotspots.md §2.2`](../../../references/06_InvalidationHotspots.md)):
- `SetText` 1회마다 마크업 파싱 → **여러 STextBlock 재생성** → Invalidate(All) → 부모 InvalidationBox 캐시 무효
- 동적 갱신이 잦으면 **다음 단계 회피**:
  1. 변경된 부분만 갱신할 수 있다면 별도 STextBlock 분리
  2. `UInvalidationBox` 로 감싸지 않기 (어차피 매번 무효화)
  3. 변경 빈도가 매우 높으면 (채팅 윈도우 등) `UScrollBox + UVerticalBox` 에 짧은 `UTextBlock` 들을 쌓는 패턴 고려

### 3.6 UProgressBar (`ProgressBar.h`)

| API | 메모 |
|-----|------|
| `void SetPercent(float)` | 0~1 |
| `void SetFillColorAndOpacity(FLinearColor)` | |
| `void SetWidgetStyle(const FProgressBarStyle&)` | |
| `bool bIsMarquee` | true → 무한 스크롤 (Indeterminate) — **자동 휘발성** |
| `void SetBarFillType(EProgressBarFillType::Type)` | LeftToRight/RightToLeft/FillFromCenter 등 |

**함정**: `bIsMarquee=true` 시 SProgressBar 가 매 프레임 페인트 → DrawCall 증가. 진행률 표시는 가능하면 **마퀴 사용 금지** + 명확한 0~100% 모드 사용.

### 3.7 UThrobber / UCircularThrobber (`Throbber.h` / `CircularThrobber.h`)

| API | 메모 |
|-----|------|
| `void SetNumberOfPieces(int32)` | 회전 점 수 |
| `void SetAnimateHorizontally/Vertically/Opacity(bool)` (UThrobber) | 어떤 축으로 애니 |
| `void SetPeriod(float)` (UCircularThrobber) | 회전 주기 |

**🚨 인밸리데이션 함정**: 두 Throbber 모두 **자동 휘발성** (`bIsVolatile=true`) — 부모 `UInvalidationBox` 안에 넣어도 캐시 효과 X. 자세히 [`06_InvalidationHotspots.md §2.4`](../../../references/06_InvalidationHotspots.md).

### 3.8 USlider (`Slider.h`)

| API | 메모 |
|-----|------|
| `float GetValue()` / `SetValue(float)` | 0~1 (정규화) — `MinValue`/`MaxValue` 따로 있음 |
| `SetStepSize(float)` | 키보드/내비 stepping |
| `SetSliderHandleColor(FLinearColor)` | |
| 이벤트 | `OnValueChanged` · `OnMouseCaptureBegin` · `OnMouseCaptureEnd` · `OnControllerCaptureBegin` · `OnControllerCaptureEnd` |

### 3.9 USpinBox (`SpinBox.h`)

| API | 메모 |
|-----|------|
| `float GetValue()` / `SetValue(float)` | |
| `SetMinValue/MaxValue/MinSliderValue/MaxSliderValue(float)` | 클램프 + 슬라이드 범위 |
| `SetDelta(float)` | 한 step 증가량 |
| `SetSliderExponent(float)` | log scale |
| 이벤트 | `OnValueChanged` · `OnValueCommitted(float, ETextCommit::Type)` · `OnBeginSliderMovement` · `OnEndSliderMovement` |

### 3.10 UEditableText / UEditableTextBox (`EditableText.h` / `EditableTextBox.h`)

| API | 메모 |
|-----|------|
| `FText GetText()` / `SetText(FText)` | |
| `void SetHintText(FText)` | placeholder |
| `void SetIsPassword(bool)` | 비밀번호 마스킹 |
| `void SetClearKeyboardFocusOnCommit(bool)` | Enter → 포커스 해제 |
| 이벤트 | `OnTextChanged(FText)` · `OnTextCommitted(FText, ETextCommit::Type)` |

**🚨 함정** (자세한 [`06_InvalidationHotspots.md §2.3`](../../../references/06_InvalidationHotspots.md)): IME 입력 중 매 키 입력마다 `OnTextChanged` → SEditableText 자동 인밸리데이션. 입력 중 외부 검증/네트워크 호출 금지. **`OnTextCommitted` 사용** 권장.

### 3.11 UComboBoxString / UComboBoxKey

| API | 메모 |
|-----|------|
| `void AddOption(const FString&)` | (String 버전) |
| `void RemoveOption(const FString&)` | |
| `void ClearOptions()` | |
| `void SetSelectedOption(FString)` / `GetSelectedOption()` | |
| 이벤트 | `OnSelectionChanged(FString, ESelectInfo::Type)` · `OnOpening` |

---

## 4. 가상 함수 (오버라이드 포인트)

표준 위젯들은 거의 override 안 한다 — **사용**이 목적. 다만 다음 4개는 사용자 정의 시 표준 패턴:

| 시그니처 | Super | 호출 시점 |
|----------|-------|-----------|
| `virtual TSharedRef<SWidget> RebuildWidget() override` | (호출 안 함) | UWidget→SWidget 변환 |
| `virtual void SynchronizeProperties() override` | **FIRST** | 디테일 패널 변경 / 생성 |
| `virtual void ReleaseSlateResources(bool) override` | **FIRST** | 트리 제거 |
| `virtual void OnWidgetRebuilt() override` | **FIRST** | RebuildWidget 직후 |

> **Super 호출 규약 통합 표**: [`04_OverrideIndex.md §6.4`](../../../references/04_OverrideIndex.md).

각 위젯의 헤더에는 추가로 `SetXxx` setter가 다수 정의돼 있고 모두 **자동 Invalidate(reason)** 호출. 사용자 정의 시 동일 패턴 따라야.

---

## 5. 🚨 인밸리데이션 / 갱신 흐름 (의무 섹션)

### 5.1 표준 setter 자동 인밸리데이션

표준 위젯의 `SetXxx` 호출 → 내부 SXxx setter 호출 → **자동 `Invalidate(reason)`**. reason은 위젯·프로퍼티별로 다르다:

| 변경 종류 | reason | 영향 |
|-----------|--------|------|
| 색상·브러시·텍스처 변경 | `Paint` | 페인트만 다시 |
| 가시성·정렬·위치 변경 | `Layout` | 레이아웃 재계산 + 페인트 |
| 자식 추가/제거 | `ChildOrder` | 자식 정렬 + 레이아웃 + 페인트 |
| TSlateAttribute 등록 변경 | `AttributeRegistration` | 속성 평가 시점 변경 |

자세한 8종 reason은 [`SlateCore/references/Drawing.md §3`](../../SlateCore/references/Drawing.md) 참조.

### 5.2 InvalidationBox 결정 트리 (간단)

표준 위젯을 `UInvalidationBox` 안에 넣을지 결정:

```
이 위젯 묶음의 갱신 빈도가 매우 낮은가? (예: 1초에 0~1회)
├─ Yes → InvalidationBox 사용 (DrawCall 절감)
└─ No → 사용 X
   ├─ 휘발성 위젯 포함? (Throbber/Marquee Progress/Animation)
   │   → InvalidationBox 효과 0 → 사용 X
   └─ 매 프레임 setter 호출? (HP 바 매 틱 갱신 등)
       → InvalidationBox 자체가 매번 무효화 → 사용 X
```

자세한 결정 트리는 [`06_InvalidationHotspots.md §3`](../../../references/06_InvalidationHotspots.md).

---

## 6. 예제

### 6.1 표준 위젯 묶음 — 인벤토리 슬롯 (UUserWidget 안에 BindWidget)

```cpp
UCLASS()
class UInventorySlotWidget : public UUserWidget
{
    GENERATED_BODY()
protected:
    virtual void NativeConstruct() override
    {
        Super::NativeConstruct();        // ← FIRST: 입력 델리게이트·Construct BP·UpdateCanTick
        if (UseButton)
        {
            UseButton->OnClicked.AddDynamic(this, &UInventorySlotWidget::HandleUseClicked);
        }
    }
    virtual void NativeDestruct() override
    {
        if (UseButton)
        {
            UseButton->OnClicked.RemoveDynamic(this, &UInventorySlotWidget::HandleUseClicked);
        }
        Super::NativeDestruct();         // ← LAST
    }

    UFUNCTION() void HandleUseClicked();

    UPROPERTY(meta=(BindWidget)) UImage* IconImage = nullptr;
    UPROPERTY(meta=(BindWidget)) UTextBlock* NameText = nullptr;
    UPROPERTY(meta=(BindWidget)) UTextBlock* CountText = nullptr;
    UPROPERTY(meta=(BindWidgetOptional)) UProgressBar* CooldownBar = nullptr;
    UPROPERTY(meta=(BindWidget)) UButton* UseButton = nullptr;
};

// 데이터 갱신 (View 재로드 패턴)
void UInventorySlotWidget::RefreshFromData(const FInventoryItem& Item)
{
    IconImage->SetBrushFromTexture(Item.Icon);
    NameText->SetText(Item.DisplayName);
    CountText->SetText(FText::AsNumber(Item.Count));

    if (CooldownBar && Item.Cooldown > 0.f)
    {
        CooldownBar->SetVisibility(ESlateVisibility::Visible);
        CooldownBar->SetPercent(Item.CooldownPercent);
    }
    else if (CooldownBar)
    {
        CooldownBar->SetVisibility(ESlateVisibility::Collapsed);
    }

    UseButton->SetIsEnabled(Item.bUsable);
}
```

### 6.2 RichText 인라인 디코레이터 (이미지 인라인 표시)

```xml
<!-- Data Table row "RichTextStyleRow" -->
<!-- 텍스트에 마크업 사용 -->
<row Style="Header">제목</row>
<row Style="Body">본문 안에 <img id="GoldIcon"/> 100 골드</row>
```

```cpp
UCLASS() class UMyRichTextWidget : public UUserWidget
{
    UPROPERTY(meta=(BindWidget)) URichTextBlock* StoryText = nullptr;
    
    virtual void NativePreConstruct() override
    {
        Super::NativePreConstruct();      // ← FIRST: DesiredFocus 등
        if (StoryText)
        {
            // 디자이너에서 SetTextStyleSet(...) + SetDecorators({URichTextBlockImageDecorator::StaticClass()})
            // 이미 설정된 경우 다시 호출 X (인밸리데이션 방지)
        }
    }
};
```

---

## 7. 운영 가이드 / 함정

| 함정 | 회피 |
|------|------|
| `UTextBlock::SetText` 매 프레임 호출 | 변경 시에만 호출 (이전값과 비교) |
| `URichTextBlock::SetText` 자주 호출 | 부분 갱신은 별도 STextBlock 분리 / 채팅은 ScrollBox+VerticalBox |
| `UEditableText::OnTextChanged` 에서 외부 검증 | `OnTextCommitted` 사용 |
| `UProgressBar` Marquee 모드 상시 | 진행률 모드 사용 + 명확한 종료 |
| `UThrobber` 항상 표시 | 로딩/대기 상태에서만 + 끝나면 `Visibility=Collapsed` |
| `UButton` 자식 미설정 | TextBlock 또는 Image 자식 추가 |
| `UImage::SetBrushFromTexture(_, true)` 의도하지 않은 사이즈 강제 | `bMatchSize=false` (기본) |
| `FText::FromString` 으로 상수 텍스트 만들기 | 상수는 `LOCTEXT`/`NSLOCTEXT`; 동적만 `FromString` |
| 표준 위젯에 `bIsVolatile=true` 직접 설정 | 휘발성은 자동 — 직접 설정하면 InvalidationBox 무력화 |

---

## 8. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

표준 위젯은 디자이너에서 자주 만지는 카테고리 → **`PostEditChangeProperty` / `SynchronizeProperties` 가 디테일 패널 변경 즉시 반영**. 게임 빌드와 분리되는 부분은 거의 없음. 단:

| 항목 | 가드 |
|------|------|
| `URichTextBlock::CreateDecorators` 디자이너 미리보기 갱신 | `WITH_EDITOR` |
| `UButton`/`UCheckBox` 디자이너 클릭 시뮬레이션 | `WITH_EDITOR` |
| `UImage::SetBrushFromAsset` 디자이너 드래그 앤 드롭 | `WITH_EDITORONLY_DATA` |

자세한 에디터 전용 통합 표는 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md).

---

## 9. 관련 sub-skill

- [`UMG/UWidget`](../UWidget/SKILL.md) — UWidget 베이스 + RebuildWidget + Super 호출 규약
- [`UMG/UUserWidget`](../UUserWidget/SKILL.md) — UUserWidget 베이스 + Native\* + BindWidget
- [`UMG/PanelWidgets`](../PanelWidgets/SKILL.md) — VerticalBox/HorizontalBox/CanvasPanel 등 컨테이너
- [`UMG/Slot`](../Slot/SKILL.md) — UPanelSlot 사슬 (각 패널의 자식 슬롯 프로퍼티)
- [`UMG/ViewModel`](../ViewModel/SKILL.md) — FieldNotify / MVVM 통합 (CheckBox·Image 등 FieldNotify 마킹된 프로퍼티)
- [`SlateCore/Text`](../../SlateCore/references/Text.md) — 폰트·HarfBuzz·FreeType (TextBlock 내부)
- [`SlateCore/Drawing`](../../SlateCore/references/Drawing.md) — 인밸리데이션 reason 8종
- [`06_InvalidationHotspots.md`](../../../references/06_InvalidationHotspots.md) — RichText/EditableText/Throbber/ProgressBar 핫스팟
- [`04_OverrideIndex.md §6`](../../../references/04_OverrideIndex.md) — Super 호출 통합 표
