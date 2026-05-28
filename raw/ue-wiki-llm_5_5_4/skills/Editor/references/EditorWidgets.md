---
name: editorwidgets-main
description: 🛠 EditorWidgets 모듈 - SAssetSearchBox + SAssetDropTarget + SDropTarget + SEnumCombo + SAssetFilterBar + ITransportControl + SInputChord.
---

# EditorWidgets Module 🛠

> **모듈**: `Engine/Source/Editor/EditorWidgets/` (Editor 전용)
> **사이즈**: Public 19 헤더
> **카테고리**: `[Slate]` 인하우스 툴 (🛠 에디터 전용)

---

## 1. 개요

UE 에디터에서 **여러 곳에서 재사용되는 공통 위젯** 들을 모은 모듈. 컨텐츠 브라우저·디테일 패널·인하우스 에디터 어디서나 등장하는 검색 박스·드롭 타겟·필터 바·트랜스포트 컨트롤 등.

자주 사용하는 위젯:
- **`SAssetSearchBox`** — 에셋 검색 (자동완성)
- **`SAssetDropTarget`** / **`SDropTarget`** — 드래그앤드롭 영역
- **`SEnumCombo`** — UENUM 콤보박스
- **`SAssetFilterBar`** / **`SFilterBar`** — 필터 바 (컨텐츠 브라우저 등)
- **`ITransportControl`** — 재생/일시정지/스킵 (시퀀서 등)
- **`IObjectNameEditableTextBox`** — 객체 이름 편집
- **`SAssetDiscoveryIndicator`** — Asset 검색 진행 인디케이터
- **`SInputChord`** — 단축키 입력
- **`SMetaDataView`** — Metadata 표시
- **`STextPropertyEditableTextBox`** — FText 편집
- **`STemplateStringEditableTextBox`** — 템플릿 문자열 편집

---

## 2. 핵심 헤더

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `EditorWidgetsModule.h` | `FEditorWidgetsModule` (L34) + `IObjectNameEditableTextBox` (L27) | 모듈 진입 |
| `SAssetSearchBox.h` | `SAssetSearchBox` (L72) | 검색 박스 |
| `SAssetDropTarget.h` | `SAssetDropTarget` | 에셋 드롭 영역 |
| `SDropTarget.h` | `SDropTarget` | 일반 드롭 영역 |
| `SEnumCombo.h` | `SEnumCombo` | UENUM 콤보 |
| `SInputChord.h` | `SInputChord` | 단축키 캡처 — ⚠ **5.5 에는 없음 (5.7+ 추가)** |
| `SMetaDataView.h` | `SMetaDataView` | Metadata 표시 |
| `STextPropertyEditableTextBox.h` | `STextPropertyEditableTextBox` | FText 편집 (지역화 통합) |
| `STemplateStringEditableTextBox.h` | `STemplateStringEditableTextBox` | 템플릿 문자열 |
| `AssetDiscoveryIndicator.h` | (`SAssetDiscoveryIndicator`) | Asset 검색 진행 |
| `ITransportControl.h` | `ITransportControl` (L106) + `ETransportControlWidgetType` | 재생 컨트롤 |
| `IObjectNameEditSink.h` | `IObjectNameEditSink` 인터페이스 | 객체 이름 편집 sink |
| `ObjectNameEditSinkRegistry.h` | `FObjectNameEditSinkRegistry` | sink 등록 |
| **Filters/** | (서브 디렉토리) | |
| `Filters/AssetFilter.h` | `FAssetFilter` | 에셋 필터 |
| `Filters/CustomClassFilterData.h` | `FCustomClassFilterData` | 클래스 필터 |
| `Filters/FilterBarConfig.h` | `FFilterBarConfig` | 필터 바 설정 |
| `Filters/SAssetFilterBar.h` | `SAssetFilterBar` | 에셋 필터 바 |
| `Filters/SFilterBar.h` | `SFilterBar` (베이스) | 필터 바 베이스 |

---

## 3. FEditorWidgetsModule (모듈 진입)

### 3.1 핵심 API (EditorWidgetsModule.h L34)

| API | 라인 | 의미 |
|-----|------|------|
| `TSharedRef<IObjectNameEditableTextBox> CreateObjectNameEditableTextBox(const TArray<TWeakObjectPtr<UObject>>& Objects)` | L54 | 객체 이름 편집 위젯 |
| `TSharedRef<SWidget> CreateAssetDiscoveryIndicator(EAssetDiscoveryIndicatorScaleMode::Type, FMargin, bool bFadeIn=true)` | L63 | Asset 검색 진행 |
| `TSharedRef<ITransportControl> CreateTransportControl(const FTransportControlArgs&)` | L71 | 재생 컨트롤 |
| `TSharedRef<UE::EditorWidgets::FObjectNameEditSinkRegistry> GetObjectNameEditSinkRegistry() const` | L78 | Sink 레지스트리 |

### 3.2 사용

```cpp
#if WITH_EDITOR
FEditorWidgetsModule& Module = FModuleManager::LoadModuleChecked<FEditorWidgetsModule>("EditorWidgets");

// Transport Control (재생/일시정지/뒤로/앞으로)
FTransportControlArgs Args;
Args.OnForwardPlay.BindLambda([]() -> FReply { /* 재생 */ return FReply::Handled(); });
Args.OnBackwardPlay.BindLambda([]() -> FReply { /* 역재생 */ return FReply::Handled(); });
Args.OnStop.BindLambda([]() -> FReply { /* 정지 */ return FReply::Handled(); });
TSharedRef<ITransportControl> Transport = Module.CreateTransportControl(Args);
#endif
```

---

## 4. SAssetSearchBox — 자동완성 검색

### 4.1 SLATE_BEGIN_ARGS (SAssetSearchBox.h L75)

| 인자 | 의미 |
|------|------|
| `SLATE_EVENT(FOnTextChanged, OnTextChanged)` | 텍스트 변경 |
| `SLATE_EVENT(FOnTextCommitted, OnTextCommitted)` | 엔터/포커스 이탈 시 |
| `SLATE_EVENT(FOnAssetSearchBoxSuggestionFilter, OnAssetSearchBoxSuggestionFilter)` | 자동완성 필터 콜백 |
| `SLATE_EVENT(FOnAssetSearchBoxSuggestionChosen, OnAssetSearchBoxSuggestionChosen)` | 선택 콜백 |
| `SLATE_EVENT(FOnKeyDown, OnKeyDownHandler)` | 키 입력 |
| `SLATE_EVENT(SFilterSearchBox::FOnSaveSearchClicked, OnSaveSearchClicked)` | 저장 버튼 |

### 4.2 사용

```cpp
SNew(SAssetSearchBox)
.OnTextChanged_Lambda([](const FText& NewText)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_SearchTextChanged);
    // 검색 처리
})
.OnAssetSearchBoxSuggestionChosen_Lambda([](const FString& SelectedSuggestion, ESelectInfo::Type)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_SuggestionChosen);
    // ...
});
```

---

## 5. SAssetDropTarget / SDropTarget

### 5.1 SAssetDropTarget — 에셋 드롭

```cpp
SNew(SAssetDropTarget)
.bSupportsMultiDrop(true)
.OnAssetsDropped_Lambda([this](const FDragDropEvent&, TArrayView<FAssetData> Assets)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_OnAssetsDropped);
    for (const FAssetData& Asset : Assets) { /* 처리 */ }
})
.OnAreAssetsAcceptableForDrop_Lambda([](TArrayView<FAssetData> Assets)
{
    return Assets.Num() > 0 && Assets[0].IsInstanceOf<UMyAsset>();
})
[
    // 드롭 영역 안의 콘텐츠
    SNew(SBorder)[ SNew(STextBlock).Text(LOCTEXT("DropHere", "Drop My Assets Here")) ]
];
```

### 5.2 SDropTarget — 일반 드롭

`SAssetDropTarget` 보다 일반적 — 임의 `FDragDropOperation` 처리.

---

## 6. SEnumCombo — UENUM 콤보박스

```cpp
SNew(SEnumCombo, StaticEnum<EMyEnum>())
.CurrentValue_Lambda([this]() -> int32 { return (int32)CurrentEnum; })
.OnEnumSelectionChanged_Lambda([this](int32 NewValue, ESelectInfo::Type)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_EnumChanged);
    CurrentEnum = (EMyEnum)NewValue;
});
```

`StaticEnum<T>()` 가 UENUM 메타데이터 가져옴 — 자동으로 항목 표시 이름·툴팁·hide 메타키 처리.

---

## 7. SAssetFilterBar — 컨텐츠 브라우저 스타일 필터 바

```cpp
SNew(SAssetFilterBar<FAssetData>)
.UseDefaultAssetFilters(true)
.OnFilterChanged_Lambda([](){ TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_FilterChanged); })
.FilterBarLayout(EFilterBarLayout::Horizontal);
```

---

## 8. ITransportControl — 재생 컨트롤

`ITransportControl.h` L106 — `SCompoundWidget` 자손 인터페이스. 시퀀서·애니메이션 에디터 등이 사용.

```cpp
enum class ETransportControlWidgetType : int32
{
    BackwardEnd, BackwardStep, Backward, Stop, ForwardPlay, ForwardStep, ForwardEnd, Loop, Record
};
```

`FEditorWidgetsModule::CreateTransportControl(Args)` 로 생성 — 표준 재생 버튼 묶음.

---

## 9. STextPropertyEditableTextBox — FText 편집

`FText` 의 지역화 키와 source string 까지 편집 가능한 텍스트 박스. 보통 디테일 패널에서 자동 사용 — 직접 사용 시:

```cpp
SNew(STextPropertyEditableTextBox, MakeShared<FMyTextEditableImpl>(...));
```

`IEditableTextProperty` 인터페이스 구현체를 받음.

---

## 10. SInputChord — 단축키 캡처

```cpp
SNew(SInputChord)
.OnInputChordChanged_Lambda([](const FInputChord& NewChord)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_ChordChanged);
    // 사용자가 단축키 변경
});
```

`Edit > Editor Preferences > Keyboard Shortcuts` 같은 UI에서 사용.

---

## 11. IObjectNameEditSink (객체 이름 편집 — 가상)

특정 UObject 타입의 이름을 편집 가능하게 만드는 sink 인터페이스. `FObjectNameEditSinkRegistry::RegisterObjectNameEditSink` 로 등록 — 이후 `IObjectNameEditableTextBox` 가 자동으로 사용.

거의 사용 안 함 — 자세한 구조는 `EditorWidgetsModule.h` 참조.

---

## 12. 가상 함수 / Super 호출

대부분 SCompoundWidget — `Construct` 안에서 `ChildSlot` 채우기. virtual override 거의 안 함.

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `SCompoundWidget::Construct` | (자체) | 위젯 빌드 |
| `IObjectNameEditSink::*` | (override 시 자체 처리) | sink 인터페이스 |
| `IModuleInterface::StartupModule` (자손) | (override 시 등록) | sink/필터 등록 |

---

## 13. 함정

| 함정 | 회피 |
|------|------|
| `OnAssetSearchBoxSuggestionFilter` 람다 안에서 무거운 작업 | 자동완성 호출 빈도 — 캐싱 + 스코프 |
| `SEnumCombo` 의 enum 값이 hidden — `Hidden` 메타키 무시 | 5.x는 자동 처리 — 4.x는 수동 |
| `OnAssetsDropped` 람다 캡처 강 참조 | TWeakPtr / TWeakObjectPtr |
| `STextPropertyEditableTextBox` 직접 인스턴스화 | 보통 디테일 패널이 자동 — 직접은 비권장 |
| `ITransportControl` 콜백 스코프 누락 | 매 클릭마다 호출 — [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) |
| `SAssetFilterBar` 필터 변경 빈도 | 변경 시에만 처리 |

---

## 14. 에디터 전용 🛠

전체 모듈 에디터 빌드 전용. 4단 분리 — [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

---

## 15. 관련 sub-skill

- [`Slate/EditorApplication`](../Slate/references/EditorApplication.md) — FSlateApplication
- [`SlateCore/Input`](../SlateCore/references/Input.md) — FReply / Drag-Drop / FKeyEvent
- [`UnrealEd/AssetEditorToolkit`](../UnrealEd/AssetEditorToolkit/SKILL.md) — 인하우스 에디터 안에서 사용
- [`PropertyEditor`](../PropertyEditor/SKILL.md) — STextPropertyEditableTextBox 가 디테일 패널에서 자동 사용
- [`AssetTools`](../AssetTools/SKILL.md) — SAssetSearchBox 의 자동완성과 통합
- [`AssetRegistry`](../AssetRegistry/SKILL.md) — 검색 결과 에셋 메타데이터 베이스
- 교차: [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) (자동완성 / 드롭 / 단축키 콜백 람다 스코프)
