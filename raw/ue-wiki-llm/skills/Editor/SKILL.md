---
name: editor
description: 🛠 Editor 모듈 통합 가이드 — UnrealEd / EditorFramework / EditorSubsystem / EditorWidgets / AssetTools / PropertyEditor / ToolMenus / MainFrame / LevelEditor / AssetRegistry / AssetEditorAPI 11개 모듈. 인하우스 에셋 에디터 / 디테일 패널 / 메뉴/툴바 / 단축키 / 노드 그래프 / 실행 중인 에셋 에디터 접근 진입점. 시나리오/의존성 detail = references/.
---

# 🛠 Editor — 인하우스 에디터 도구 통합 가이드

> **위치**: `Engine/Source/Editor/{UnrealEd,EditorFramework,EditorSubsystem,EditorWidgets,PropertyEditor,MainFrame,LevelEditor}/` + `Engine/Source/Developer/{AssetTools,ToolMenus}/` + `Engine/Source/Runtime/AssetRegistry/`
> **요지**: **모든 인하우스 에디터 도구 작성 시 본 카테고리** — 게임 빌드 X, Editor 빌드만 동작 (`#if WITH_EDITOR` 가드 의무). 11개 모듈이 같이 사용되어 통합 카테고리로 묶음.

---

## 🚨 모든 Editor sub-skill 공통 의무

> [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) 의 **런타임/에디터 4단 분리 원칙** 의무.

| # | 정책 | 핵심 룰 |
|---|------|---------|
| 1 | **모듈 분리** | Runtime 모듈 (게임 빌드) vs Editor 모듈 (Editor 빌드만) 두 모듈로 강제 분리 |
| 2 | **uplugin Type 명시** | `Type=Editor` 명시 — Cooked 빌드 시 자동 stripped |
| 3 | **Build.cs 분기** | Editor 모듈은 `bBuildDeveloperTools=true` 만 + Slate/SlateCore/UnrealEd 등 의존 |
| 4 | **`#if WITH_EDITOR` 가드** | Runtime 모듈 안 Editor 호출은 모두 가드 |
| 5 | ⭐ **어셋 로드 = 동기 (`TryLoad`)** | Editor 순수 모드 ([`11_AssetLoadingPolicy.md §3`](../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-)) = 동기 로드 표준 — `IsPureEditorMode` 검증 + `LoadSynchronous` / `TryLoad`. PIE / Game 은 §5 비동기 의무 |

> **위반 시**: Cooked 빌드 시 컴파일 에러 / 게임 출시 빌드에 Editor 코드 포함. 4단 방어 상세 = [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

---

## 1. 11개 sub-skill 인덱스

### 1.1 핵심 5종 — 인하우스 에셋 에디터 골격 ⭐

| sub-skill | 한 줄 요약 | 사용 시점 |
|-----------|-----------|----------|
| [`UnrealEd/`](./UnrealEd/SKILL.md) ⭐ | **Editor 메인 모듈** — AssetEditorToolkit / Subsystems / Kismet2 / Factories / Elements / Layers / MaterialEditor / Misc 8 sub | 모든 인하우스 에셋 에디터 진입점 |
| [`EditorFramework/`](./EditorFramework/SKILL.md) | **베이스** — `IToolkit` / `IToolkitHost` / `UEdMode` / `UPlacementSubsystem` + 5.x Element System | UnrealEd 베이스 — Toolkit 작성 |
| [`AssetTools/`](./AssetTools/SKILL.md) | **에셋 타입별 동작** — `IAssetTools` / `IAssetTypeActions` / `FAssetTypeActions_Base` | 새 에셋 타입 등록 시 |
| [`PropertyEditor/`](./PropertyEditor/SKILL.md) | **디테일 패널 커스터마이징** — `IDetailCustomization` / `IPropertyTypeCustomization` | 디테일 패널에 사용자 위젯 추가 |
| [`ToolMenus/`](./ToolMenus/SKILL.md) | **5.x 모던 메뉴** — `UToolMenus` / `UToolMenu` (FMenuBuilder 후속) | 메뉴/툴바 항목 추가 |

### 1.2 보조 6종

| sub-skill | 한 줄 요약 | 사용 시점 |
|-----------|-----------|----------|
| [`EditorSubsystem/`](./EditorSubsystem/SKILL.md) | **UEditorSubsystem 베이스 모듈** | 사용자 정의 에디터 서브시스템 |
| [`EditorWidgets/`](./EditorWidgets/SKILL.md) | **공통 위젯** — `SAssetSearchBox` / `SAssetDropTarget` / `SEnumCombo` / `SAssetFilterBar` 등 | 표준 Editor 위젯 사용 |
| [`MainFrame/`](./MainFrame/SKILL.md) | **메인 윈도우** — `IMainFrameModule` + `OnMainFrameCreationFinished` | 메인 윈도우 / 메뉴 후크 |
| [`LevelEditor/`](./LevelEditor/SKILL.md) | **레벨 에디터 본체** — `FLevelEditorModule` / `SLevelViewport` / `ULevelEditorSubsystem` | 레벨 에디터 확장 |
| [`AssetRegistry/`](./AssetRegistry/SKILL.md) | **에셋 메타 캐시** — `IAssetRegistry::GetChecked()` / `FAssetData` / `FARFilter` | 에셋 검색 / 의존성 추적 |
| [`AssetEditorAPI/`](./AssetEditorAPI/SKILL.md) ⭐ | **실행 중 에디터 접근** — `UAssetEditorSubsystem` + EditorName `static_cast` 안전 + `IStaticMeshEditor` / `IPersonaToolkit` | 도구 확장 / 자동화 |

---

## 2. 시나리오 → sub-skill 묶음 (결정 트리)

상세 시나리오별 필수/선택 묶음 + Build.cs = [`references/Scenarios.md`](./references/Scenarios.md).

| 작업 | 진입 sub-skill | Build.cs 추가 |
|------|---------------|---------------|
| 새 에셋 타입 + 에디터 ⭐ | UnrealEd/AssetEditorToolkit + AssetTools + Factories + PropertyEditor + ToolMenus | UnrealEd, AssetTools, PropertyEditor, ToolMenus |
| 디테일 패널만 | PropertyEditor | PropertyEditor |
| 메뉴/툴바만 | ToolMenus (5.x 모던) | ToolMenus, MainFrame, LevelEditor |
| 노드 그래프 | Slate/GraphEditor + UnrealEd/AssetEditorToolkit | GraphEditor, UnrealEd |
| Editor Subsystem | EditorSubsystem + Subsystem/SKILL.md | UnrealEd, EditorSubsystem |
| 에셋 검색 | AssetRegistry + CoreUObject/ObjectHandles | AssetRegistry |
| 레벨 에디터 확장 | LevelEditor + UnrealEd/Layers | LevelEditor, UnrealEd |
| 실행 중 에디터 접근 ⭐ | AssetEditorAPI | UnrealEd, StaticMeshEditor, SkeletalMeshEditor, Persona, AdvancedPreviewScene |

---

## 3. 모듈 의존성 + 표준 Build.cs

의존성 트리 + 표준 Build.cs + uplugin Type + 모듈 분리 구조 detail = [`references/Dependencies.md`](./references/Dependencies.md).

```
EditorFramework (베이스)
  → UnrealEd (메인)
    → AssetTools / PropertyEditor / ToolMenus / LevelEditor / MainFrame / EditorWidgets / EditorSubsystem / AssetRegistry / AssetEditorAPI
```

---

## 4. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | Runtime 모듈에 Editor 모듈 의존 추가 | Cooked 빌드 실패 — Editor 모듈은 별도 모듈 + `Type=Editor` |
| 2 | `#if WITH_EDITOR` 가드 누락 | Cooked 빌드 안 컴파일 에러 — 모든 Editor 호출 가드 |
| 3 | `WITH_EDITORONLY_DATA` 가드 누락 (UPROPERTY) | Cooked 빌드 안 정의 안 됨 — UPROPERTY 도 가드 |
| 4 | `FMenuBuilder` 사용 (legacy) | 5.x = `UToolMenus` 표준 ([`ToolMenus/SKILL.md`](./ToolMenus/SKILL.md)) |
| 5 | `IDetailCustomization::CustomizeDetails` 안 `Modify()` 호출 누락 | Undo/Redo 안 됨 — `CoreUObject/Editor §3` |
| 6 | `IAssetTypeActions::GetSupportedClass` nullptr 반환 | 에셋 등록 실패 — `AssetTools/SKILL.md §3` |
| 7 | `FAssetEditorToolkit::InitAssetEditor` 안 LayoutVersion 누락 | 도킹 레이아웃 깨짐 — `UnrealEd/AssetEditorToolkit §6` |
| 8 | `FEdGraphUtilities::RegisterVisualNodeFactory` 후 `Unregister` 누락 | hot-reload 시 댕글링 — `Slate/GraphEditor §6` |
| 9 | `UEditorSubsystem` 안 Tick 시도 (UTickableEditorSubsystem 대신) | Tick 안 됨 — 베이스 잘못 선택 |
| 10 | 🚨 `Initialize` / `Deinitialize` 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md)) |

---

## 5. 관련 문서

### 카테고리 외부 cross-link

- [`Slate/`](../Slate/SKILL.md) — 인하우스 툴 묶음 (Docking / Menu / Commands / GraphEditor 5개 sub-skill)
- [`SlateCore/`](../SlateCore/SKILL.md) — 위젯 베이스 (SWidget / Layout / Drawing)
- [`Subsystem/`](../Subsystem/SKILL.md) — UEditorSubsystem 통합 가이드 (5종 비교)
- [`CoreUObject/Editor`](../CoreUObject/references/Editor.md) — `PostEditChangeProperty` / `Modify` (Undo/Redo)
- [`CoreUObject/Cooking`](../CoreUObject/references/Cooking.md) — Cooked Build 빌드 시 Editor 데이터 처리

### 횡단 정책

- 🚨 [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) — **런타임/에디터 4단 분리 원칙** (모든 Editor sub-skill 의무)
- [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — 콜백 첫 줄 스코프 의무
- [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) — TActorIterator / TObjectIterator 사용 금지

### 본 카테고리 references/ (deep)

- [`references/Scenarios.md`](./references/Scenarios.md) — 8 시나리오별 sub-skill 묶음 상세
- [`references/Dependencies.md`](./references/Dependencies.md) — 모듈 의존성 트리 + 표준 Build.cs + 모듈 분리 구조

---

## 6. 변경 이력

| 날짜 | 변경 |