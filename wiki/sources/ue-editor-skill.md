---
type: source
title: "UE Editor Module Main SKILL (🛠 인하우스 도구 통합 가이드)"
slug: ue-editor-skill
source_path: raw/ue-wiki-llm/skills/Editor/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-12
related_entities:
  - "[[entities/IToolkit]]"
  - "[[entities/UEdMode]]"
  - "[[entities/UToolMenus]]"
  - "[[entities/IDetailCustomization]]"
  - "[[entities/IAssetTools]]"
  - "[[entities/IAssetRegistry]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, editor, in-house, toolkit, slate, asseteditor, propertyeditor, toolmenus]
---

# UE Editor Module Main SKILL (🛠 인하우스 도구 통합 가이드)

> Source: [[raw/ue-wiki-llm/skills/Editor/SKILL.md]] · 124 lines / 8.6 KB · 11 sub-skill 카테고리 main

## 1. Summary

🛠 모든 *인하우스 에디터 도구* 작성 시 본 카테고리 — 게임 빌드 X, **Editor 빌드만 동작** (`#if WITH_EDITOR` 가드 의무). 11개 모듈 (UnrealEd / EditorFramework / EditorSubsystem / EditorWidgets / AssetTools / PropertyEditor / ToolMenus / MainFrame / LevelEditor / AssetRegistry / AssetEditorAPI) 이 같이 사용되어 *통합 카테고리* 로 묶임. 핵심 원칙: **런타임/에디터 4단 분리** ([[concepts/Editor-Only-4-Tier-Separation]]) — 모듈 분리 / uplugin Type=Editor / Build.cs 분기 / `#if WITH_EDITOR` 가드. 어셋 로드는 Editor 순수 모드에서 *동기* (`TryLoad`) — PIE / Game 의 비동기 의무와 차이 ([[concepts/Asset-Loading-Policy]] §3).

## 2. Key claims

### 2.1. Editor sub-skill 공통 5대 의무 (raw §🚨)

- **모듈 분리**: Runtime (게임 빌드) vs Editor (Editor 빌드만) 두 모듈로 강제. 같은 .cpp 안 혼재 금지
- **uplugin Type=Editor**: Cooked 빌드 시 자동 stripped
- **Build.cs 분기**: Editor 모듈은 `bBuildDeveloperTools=true` + Slate/SlateCore/UnrealEd 의존
- **`#if WITH_EDITOR` 가드**: Runtime 모듈 안 Editor 호출 모두 가드. `WITH_EDITORONLY_DATA` 도 UPROPERTY 에 적용
- **⭐ 어셋 로드 = 동기 (`TryLoad`)**: Editor 순수 모드 ([[sources/ue-ref-11-assetloadingpolicy]] §3) — `IsPureEditorMode` 검증 + `LoadSynchronous`/`TryLoad`. PIE/Game 은 비동기 의무

### 2.2. 11 sub-skill 인덱스 — 핵심 5종 (§1.1)

| sub-skill | 한 줄 | 사용 시점 |
| -- | -- | -- |
| [[sources/ue-editor-unrealed]] ⭐ | Editor 메인 모듈 — AssetEditorToolkit/Subsystems/Kismet2/Factories 등 8 sub | 모든 인하우스 에셋 에디터 진입 |
| [[sources/ue-editor-editorframework]] | 베이스 — `IToolkit` / `IToolkitHost` / `UEdMode` / `UPlacementSubsystem` + 5.x Element System | UnrealEd 베이스 |
| [[sources/ue-editor-assettools]] | `IAssetTools` / `IAssetTypeActions` / `FAssetTypeActions_Base` | 새 에셋 타입 등록 |
| [[sources/ue-editor-propertyeditor]] | `IDetailCustomization` / `IPropertyTypeCustomization` | 디테일 패널 커스터마이징 |
| [[sources/ue-editor-toolmenus]] | 5.x 모던 메뉴 — `UToolMenus` / `UToolMenu` (FMenuBuilder 후속) | 메뉴/툴바 항목 추가 |

### 2.3. 보조 6종 (§1.2)

| sub-skill | 한 줄 | 사용 시점 |
| -- | -- | -- |
| [[sources/ue-editor-editorsubsystem]] | `UEditorSubsystem` 베이스 | 사용자 정의 에디터 서브시스템 |
| [[sources/ue-editor-editorwidgets]] | `SAssetSearchBox` / `SAssetDropTarget` / `SEnumCombo` 등 공통 위젯 | 표준 Editor 위젯 사용 |
| [[sources/ue-editor-mainframe]] | `IMainFrameModule` + `OnMainFrameCreationFinished` | 메인 윈도우 후크 |
| [[sources/ue-editor-leveleditor]] | `FLevelEditorModule` / `SLevelViewport` / `ULevelEditorSubsystem` | 레벨 에디터 확장 |
| [[sources/ue-editor-assetregistry]] | `IAssetRegistry::GetChecked()` / `FAssetData` / `FARFilter` | 에셋 검색 / 의존성 추적 |
| [[sources/ue-editor-asseteditorapi]] ⭐ | `UAssetEditorSubsystem` + EditorName `static_cast` 안전 + `IStaticMeshEditor` / `IPersonaToolkit` | 도구 확장 / 자동화 |

### 2.4. 시나리오 → sub-skill 묶음 (§2 결정 트리)

| 작업 | 진입 sub-skill | Build.cs |
| -- | -- | -- |
| 새 에셋 타입 + 에디터 ⭐ | UnrealEd/AssetEditorToolkit + AssetTools + Factories + PropertyEditor + ToolMenus | UnrealEd, AssetTools, PropertyEditor, ToolMenus |
| 디테일 패널만 | PropertyEditor | PropertyEditor |
| 메뉴/툴바만 | ToolMenus (5.x 모던) | ToolMenus, MainFrame, LevelEditor |
| 노드 그래프 | Slate/GraphEditor + UnrealEd/AssetEditorToolkit | GraphEditor, UnrealEd |
| Editor Subsystem | EditorSubsystem + Subsystem/SKILL.md | UnrealEd, EditorSubsystem |
| 에셋 검색 | AssetRegistry + CoreUObject/ObjectHandles | AssetRegistry |
| 레벨 에디터 확장 | LevelEditor + UnrealEd/Layers | LevelEditor, UnrealEd |
| 실행 중 에디터 접근 ⭐ | AssetEditorAPI | UnrealEd, StaticMeshEditor, SkeletalMeshEditor, Persona, AdvancedPreviewScene |

### 2.5. 모듈 의존성 (§3)

```
EditorFramework (베이스)
  → UnrealEd (메인)
    → AssetTools / PropertyEditor / ToolMenus / LevelEditor / MainFrame /
      EditorWidgets / EditorSubsystem / AssetRegistry / AssetEditorAPI
```

상세 의존성 트리 + 표준 Build.cs + uplugin Type + 모듈 분리 구조 → [[sources/ue-editor-dependencies]].

### 2.6. 함정 10종 (§4)

1. Runtime 모듈에 Editor 모듈 의존 추가 → Cooked 빌드 실패. **별도 모듈 + Type=Editor**
2. `#if WITH_EDITOR` 가드 누락 → Cooked 컴파일 에러. **모든 Editor 호출 가드**
3. `WITH_EDITORONLY_DATA` 가드 누락 (UPROPERTY) → Cooked 안 정의 안 됨
4. `FMenuBuilder` 사용 (legacy) → 5.x = `UToolMenus` 표준
5. `IDetailCustomization::CustomizeDetails` 안 `Modify()` 누락 → Undo/Redo 안 됨
6. `IAssetTypeActions::GetSupportedClass` nullptr → 에셋 등록 실패
7. `FAssetEditorToolkit::InitAssetEditor` 안 LayoutVersion 누락 → 도킹 레이아웃 깨짐
8. `FEdGraphUtilities::RegisterVisualNodeFactory` 후 `Unregister` 누락 → hot-reload dangling
9. `UEditorSubsystem` 안 Tick 시도 → `UTickableEditorSubsystem` 베이스 잘못 선택
10. 🚨 `Initialize`/`Deinitialize` 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 누락 ([[concepts/Profiling-Scope-Rule]])

## 3. Quotations

> "모든 인하우스 에디터 도구 작성 시 본 카테고리 — 게임 빌드 X, Editor 빌드만 동작 (`#if WITH_EDITOR` 가드 의무). 11개 모듈이 같이 사용되어 통합 카테고리로 묶음." — §0 요지

> "Editor 순수 모드 = 동기 로드 표준 — `IsPureEditorMode` 검증 + `LoadSynchronous`/`TryLoad`. PIE/Game 은 §5 비동기 의무" — 5대 의무 #5

> "Cooked 빌드 시 컴파일 에러 / 게임 출시 빌드에 Editor 코드 포함 — 본 정책 위반의 가장 흔한 증상. 4단 방어 상세 = `05_EditorOnlyIndex.md`" — §🚨

## 4. Cross-link

### 카테고리 외부

- [[sources/ue-slate-skill]] — 인하우스 툴 묶음 (Docking / Menu / Commands / GraphEditor)
- [[sources/ue-slatecore-skill]] — 위젯 베이스 (SWidget / Layout / Drawing)
- [[sources/ue-subsystem-skill]] — UEditorSubsystem 5종 비교
- [[sources/ue-coreuobject-editor]] — `PostEditChangeProperty` / `Modify` (Undo/Redo)
- [[sources/ue-coreuobject-cooking]] — Cooked Build 시 Editor 데이터 처리

### 횡단 정책

- 🚨 [[sources/ue-ref-05-editoronlyindex]] — 4단 분리 원칙 (모든 Editor sub-skill 의무)
- 🚨 [[sources/ue-ref-07-profilingscopeRule]] — 콜백 첫 줄 스코프
- 🚨 [[sources/ue-ref-09-globaliteratorpolicy]] — TActorIterator/TObjectIterator 금지
- 🚨 [[sources/ue-ref-11-assetloadingpolicy]] §3 — 환경 모드별 로드 (Editor Pure 분기)

### 본 카테고리 deep

- [[sources/ue-editor-scenarios]] — 8 시나리오별 sub-skill 묶음 상세
- [[sources/ue-editor-dependencies]] — 모듈 의존성 + 표준 Build.cs + uplugin 구조

### Cycle 5p reverse-link 보강 (med confidence missing)

- [[sources/ue-editor-staticmesheditor]] — `IStaticMeshEditor` + `FStaticMeshEditorModule` + 5.x AdvancedPreviewScene 통합. AssetEditorAPI sub-skill 의 도구 확장 예시 (§2.3 EditorName `static_cast` 안전).
- [[sources/ue-editor-personatoolkit]] — `IPersonaToolkit` + Persona 모드 1·5종 + AnimationEditor 통합. AssetEditorAPI sub-skill 의 도구 확장 예시.
- [[sources/ue-editor-unrealed-asseteditortoolkit]] — `FAssetEditorToolkit::InitAssetEditor` + 표준 8 슬롯 + 도킹 레이아웃. UnrealEd ⭐ sub-skill 의 22KB 핵심 deep dive (§2.6 함정 #7 LayoutVersion 검증 소스).

## 5. Open questions

- [ ] `UTickableEditorSubsystem` vs `UEditorSubsystem` — Tick 필요 시 베이스 선택 트리
- [ ] 5.x `UToolMenus` 의 정적 vs 동적 메뉴 등록 — `RegisterMenu` 시점 (Module Startup vs Lazy)
- [ ] Custom Asset Factory + Importer 통합 — Reimport delegate 의 stale handle 처리
- [ ] EditorUtility Widget (UMG) 와 SlateEditor Widget 의 결정 트리
