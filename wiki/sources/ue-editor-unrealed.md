---
type: source
title: "UE Editor — UnrealEd Module Main SKILL 🛠"
slug: ue-editor-unrealed
source_path: raw/ue-wiki-llm/skills/Editor/references/UnrealEd.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-12
related_entities:
  - "[[entities/IToolkit]]"
  - "[[entities/UEdGraph]]"
  - "[[entities/UBlueprintGeneratedClass]]"
  - "[[entities/IAssetTools]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
tags: [ue, editor, unrealed, toolkit, factories, kismet, materialeditor]
---

# UE Editor — UnrealEd Module Main SKILL 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/UnrealEd.md]] · 13.8 KB · UE 의 가장 큰 Editor 모듈 (717 헤더)

## 1. Summary

UE 에디터의 **본체 모듈** (`Engine/Source/Editor/UnrealEd/`). 거의 모든 인하우스 에셋 에디터 / 레벨 도구 / BP 컴파일 / 임포트 파이프라인의 베이스. 분량이 거대 (Public 329 + Classes 388 = **717 헤더**) → vault 에서는 **8개 sub-skill 로 분할**. 빌드 보호: `Build.cs` 첫 줄 `if(!Target.bCompileAgainstEditor) throw` — 에디터 빌드 전용. 게임 모듈에서 *직접 의존 금지* ([[concepts/Editor-Only-4-Tier-Separation]] 4단 방어 의무).

## 2. Key claims

### 2.1. 빌드 / 의존성 (§2)

- **PublicDependencyModuleNames 50+** — Core / Slate / AssetTools / 5.x Element System / Interchange / BlueprintGraph 등
- **PrivateIncludePathModuleNames 20+** — StructViewer / MainFrame / GraphEditor / SourceControl 등
- **PCH**: PrivatePCH + SharedPCH 분리. `bEnableExceptions = !Target.bUseAutoRTFMCompiler`

### 2.2. 디렉토리 구조 (§3)

**Public/** (24 1차 디렉토리):
- 핵심 (✅ sub-skill 분할): `Toolkits/` `Subsystems/` `Kismet2/` `Elements/` `Layers/` `Bookmarks/` `WorkflowOrientedApp/` `WorldPartition/`
- 기타 16: EditorState / DragAndDrop / Settings / ImportUtils / ViewportToolbar / AutoReimport / Commandlets / Dialogs / Editor / Features / Instances / Serialization / Tests / Text / Tools 등 (sub-skill: Misc / Factories)

**Classes/** (17 1차 디렉토리):
- `ActorFactories/` `Exporters/` `Factories/` (가장 큼) → Factories sub-skill
- `MaterialEditor/` `MaterialGraph/` → MaterialEditor sub-skill
- 기타: Animation / Builders / Commandlets / CookOnTheSide / Preferences / Settings / ThumbnailRendering / UserDefinedStructure

### 2.3. 8 Sub-skill 인덱스 (§4)

각 sub-skill 은 *개요 → 핵심 헤더/클래스 → 자주 쓰는 API → virtual → 예제 → 에디터 전용 → 함정 → 관련 sub-skill* 8섹션 구조.

| # | Sub-skill | 영역 | 주요 심볼 |
| -- | -- | -- | -- |
| 1 | [[sources/ue-editor-unrealed-asseteditortoolkit]] 🛠 | **인하우스 에셋 에디터 작성 표준** | `FAssetEditorToolkit` / `BaseToolkit` / `SimpleAssetEditor` / `FWorkflowCentricApplication` / `IToolkitHost` / `FExtensibilityManager` |
| 2 | [[sources/ue-editor-unrealed-subsystems]] 🛠 | 에디터 서브시스템 12개 | `UAssetEditorSubsystem` / `UEditorActorSubsystem` / `UEditorAssetSubsystem` / `UImportSubsystem` 등 |
| 3 | [[sources/ue-editor-unrealed-kismet2]] 🛠 | 블루프린트 통합 | `FBlueprintEditorUtils` / `FKismetEditorUtilities` / `FCompilerResultsLog` / `FDebuggerCommands` |
| 4 | [[sources/ue-editor-unrealed-factories]] 🛠 | Asset 임포트 파이프라인 | `UFactory` / `UActorFactory` / `UExporter` / Reimport / Interchange 통합 |
| 5 | [[sources/ue-editor-unrealed-elements]] 🛠 | 5.x Element Selection System | `FTypedElementSelectionSet` / `ITypedElementWorldInterface` / `FTypedElementHandle` |
| 6 | [[sources/ue-editor-unrealed-layers]] 🛠 | Layers · Bookmarks · WorldPartition 통합 | `FLayers` / `UWorldBookmark` |
| 7 | [[sources/ue-editor-unrealed-materialeditor]] 🛠 | Material 에디터 통합 | `UMaterialGraph` / `UMaterialGraphNode` / `UMaterialEditingLibrary` |
| 8 | [[sources/ue-editor-unrealed-misc]] 🛠 | Settings / Preferences / ImportUtils / Tools / ViewportToolbar / Dialogs / Animation / Builders / Cook / Thumbnail 등 | `Public/Settings/` / `Tools/` / `Dialogs/` / `Classes/Settings/` 등 |

## 3. Quotations

> "에디터 빌드에서만 사용 가능 — `Build.cs` 첫 줄 `if(!Target.bCompileAgainstEditor) throw new BuildException` — 게임 모듈에서 직접 의존 금지" — §0 위치 / §1 빌드 보호

> "분량이 거대하므로 본 위키에서는 8개 sub-skill 로 분할" — §1 개요

> "각 sub-skill 은 개요 → 핵심 헤더/클래스 → 자주 쓰는 API → virtual → 예제 → 에디터 전용 → 함정 → 관련 sub-skill 의 8섹션 구조" — §4 표준 구조

## 4. Cross-link

- 카테고리 main: [[sources/ue-editor-skill]] (11 sub-skill 통합)
- 자매 sub-skill (UnrealEd 외): [[sources/ue-editor-asseteditorapi]] / [[sources/ue-editor-editorframework]] / [[sources/ue-editor-assettools]] / [[sources/ue-editor-propertyeditor]] / [[sources/ue-editor-toolmenus]]
- 횡단 정책: [[sources/ue-ref-05-editoronlyindex]] (4단 분리) · [[sources/ue-ref-07-profilingscopeRule]]
- 페어 카테고리: [[sources/ue-slate-skill]] (인하우스 툴 진입) · [[sources/ue-coreuobject-editor]] (PostEditChangeProperty / Modify)

## 5. Open questions

- [ ] 5.x Interchange (`InterchangeCore` / `InterchangeEngine`) — 레거시 Factories 와의 마이그레이션 전략
- [ ] `InteractiveToolsFramework` (Modeling Mode 통합) — Editor Mode 베이스 vs UEdMode 결정 트리
- [ ] `TypedElementFramework` 5.x — 기존 Actor 선택 (Selection / Browse) 과 호환 패턴
- [ ] WorldPartition + Layers 통합 — Large World 에서 Layers 정의 시점
