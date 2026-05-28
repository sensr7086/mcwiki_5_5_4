---
type: source
title: "UE Editor — EditorWidgets sub-skill 🛠 (공통 위젯 라이브러리)"
slug: ue-editor-editorwidgets
source_path: raw/ue-wiki-llm/skills/Editor/references/EditorWidgets.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-minor-numeric  # 2026-05-28 Phase 2-B remaining audit
related_entities:
  - "[[entities/SWidget]]"
  - "[[entities/FSlateBrush]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, editor, editorwidgets, slate, common-widgets, filter-bar, transport-control]
---

# UE Editor — EditorWidgets sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/EditorWidgets.md]] · 10 KB raw · `Editor/EditorWidgets/` 19 헤더

## 1. Summary

UE 에디터에서 *여러 곳 재사용되는 **공통 위젯***. 컨텐츠 브라우저 / 디테일 패널 / 인하우스 에디터 어디서나 등장하는 검색 박스 / 드롭 타겟 / 필터 바 / 트랜스포트 컨트롤. 자주 쓰는 11 위젯 묶음.

## 2. Key claims

### 2.1. 핵심 위젯 11

| 위젯 | 용도 |
| -- | -- |
| **`SAssetSearchBox`** | 에셋 검색 (자동완성) |
| **`SAssetDropTarget`** / `SDropTarget` | 드래그앤드롭 영역 |
| **`SEnumCombo`** | UENUM 콤보박스 |
| **`SAssetFilterBar`** / `SFilterBar` | 필터 바 (컨텐츠 브라우저 등) |
| **`ITransportControl`** | 재생/일시정지/스킵 (시퀀서) |
| `IObjectNameEditableTextBox` | 객체 이름 편집 |
| `SAssetDiscoveryIndicator` | Asset 검색 진행 |
| `SInputChord` | 단축키 입력 |
| `SMetaDataView` | Metadata 표시 |
| `STextPropertyEditableTextBox` | FText (지역화 통합) |
| `STemplateStringEditableTextBox` | 템플릿 문자열 |

### 2.2. 핵심 헤더

- `EditorWidgetsModule.h` (L34) — `FEditorWidgetsModule` + `IObjectNameEditableTextBox` (L27)
- `SAssetSearchBox.h` (L72) / `SAssetDropTarget.h` / `SDropTarget.h` / `SEnumCombo.h` / `SInputChord.h` / `SMetaDataView.h` / `STextPropertyEditableTextBox.h` / `STemplateStringEditableTextBox.h`
- `AssetDiscoveryIndicator.h` — `SAssetDiscoveryIndicator`
- `ITransportControl.h` (L106) + `ETransportControlWidgetType` — 재생 컨트롤 인터페이스
- `IObjectNameEditSink.h` / `ObjectNameEditSinkRegistry.h` — `FObjectNameEditSinkRegistry`
- **Filters/**: `AssetFilter.h` (`FAssetFilter`) / `CustomClassFilterData.h` / `FilterBarConfig.h` / `SAssetFilterBar.h` / `SFilterBar.h`

### 2.3. FEditorWidgetsModule API (§3.1)

| API | 라인 | 의미 |
| -- | -- | -- |
| `CreateObjectNameEditableTextBox(TArray<TWeakObjectPtr<UObject>>&)` | L54 | 객체 이름 편집 위젯 |
| `CreateAssetDiscoveryIndicator(EAssetDiscoveryIndicatorScaleMode, FMargin, bool bFadeIn)` | L63 | Asset 검색 진행 |
| `CreateTransportControl(FTransportControlArgs&)` | L71 | 재생 컨트롤 |
| `GetObjectNameEditSinkRegistry() const` | L78 | Sink 레지스트리 |

### 2.4. 표준 사용 — Transport Control

```cpp
#if WITH_EDITOR
FEditorWidgetsModule& Module = FModuleManager::LoadModuleChecked<FEditorWidgetsModule>("EditorWidgets");

FTransportControlArgs Args;
Args.OnForwardPlay.BindLambda([]() -> FReply { /* 재생 */ return FReply::Handled(); });
Args.OnBackwardPlay.BindLambda([]() -> FReply { /* 역재생 */ return FReply::Handled(); });
Args.OnStop.BindLambda([]() -> FReply { /* 정지 */ return FReply::Handled(); });

TSharedRef<ITransportControl> TC = Module.CreateTransportControl(Args);
// SBox 등에 wrap 해서 위젯 트리에 삽입
#endif
```

### 2.5. SAssetSearchBox — 자동완성

```cpp
SNew(SAssetSearchBox)
    .OnTextCommitted_Lambda([this](const FText& T, ETextCommit::Type) { /* 검색 */ })
    .PossibleSuggestions_Lambda([] { return GetSuggestions(); })
    .DelayChangeNotificationsWhileTyping(true);
```

### 2.6. SFilterBar / SAssetFilterBar — 컨텐츠 브라우저 패턴

`FCustomClassFilterData` 로 클래스 필터 정의 + `FFilterBarConfig` 로 영구 저장. 컨텐츠 브라우저 의 필터 UI 가 본 위젯 기반.

### 2.7. IObjectNameEditSink + Registry — 객체 이름 편집 확장

특정 UClass 의 *Display Name* 결정 로직을 외부 모듈에서 등록. `FObjectNameEditSinkRegistry::Register(UClass*, IObjectNameEditSink*)`.

### 2.8. 함정

- `SAssetSearchBox` 의 `PossibleSuggestions` 매 호출 비용 — 캐싱 의무
- `ITransportControl` 의 OnForward/Backward 람다에 `TWeakObjectPtr<this>` + IsValid 검사 (Slate 람다 dangling 회피)
- `SFilterBar` 의 `FFilterBarConfig` 영구 저장 — `SaveConfig()` 시점 명시
- `SEnumCombo` 의 UENUM `meta=(Hidden)` 항목 — 자동 필터 안 됨, 수동 옵션 cull 필요

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어: [[sources/ue-editor-propertyeditor]] (디테일 패널 안 위젯) / [[sources/ue-editor-leveleditor]] (Sequencer Transport Control) / [[sources/ue-editor-assetregistry]] (SAssetSearchBox 베이스)
- Slate 베이스: [[sources/ue-slatecore-swidget]] / [[sources/ue-slate-commonwidgets]]
- 횡단: [[sources/ue-ref-05-editoronlyindex]]
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 0 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Editor/references/EditorWidgets.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Editor/references/EditorWidgets.md`
