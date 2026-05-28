---
type: source
title: "UE Editor — UnrealEd / Subsystems sub-skill 🛠 (에디터 서브시스템 12종)"
slug: ue-editor-unrealed-subsystems
source_path: raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Subsystems.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-12
related_entities:
  - "[[entities/USubsystem]]"
  - "[[entities/IToolkit]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Subsystem-5-Types]]"
tags: [ue, editor, unrealed, subsystem, ueditorsubsystem, asseteditorsubsystem]
---

# UE Editor — UnrealEd / Subsystems sub-skill 🛠 (12종)

> Source: [[raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Subsystems.md]] · 12 KB

## 1. Summary

UE 에디터의 **싱글턴 헬퍼 12종** — `UEditorSubsystem` 베이스 (모듈 `EditorSubsystem`) 에서 파생. 에디터 시작 시 자동 Initialize / 종료 Deinitialize. `GEditor->GetEditorSubsystem<T>()` 진입. 일부는 BP/Python 노출 (Editor Utility BP / Editor Scripting). 전체 `WITH_EDITOR` 전용.

## 2. Key claims

### 2.1. 12 서브시스템 매트릭스

| # | 클래스 | 헤더 | 핵심 책임 |
| -- | -- | -- | -- |
| 1 ⭐ | `UAssetEditorSubsystem` | `AssetEditorSubsystem.h` | **에셋 더블클릭/오픈 라우팅** — OpenEditorForAsset / FindEditorForAsset (가장 자주) |
| 2 | `UEditorActorSubsystem` | 같음 | 레벨 액터 일괄 조작 — Spawn / Destroy / Select / SetActorTransform (Editor Scripting) |
| 3 | `UEditorAssetSubsystem` | 같음 | Asset 파일 — Save / Delete / Rename / Duplicate / 메타데이터 |
| 4 | `UImportSubsystem` | 같음 | Asset 임포트 라우팅 — ImportFile + Reimport 콜백 + Interchange |
| 5 | `UPanelExtensionSubsystem` | 같음 | 임의 위젯 패널에 외부 모듈 항목 추가 (확장점) |
| 6 | `UPropertyVisibilityOverrideSubsystem` | 같음 | UPROPERTY 가시성 동적 오버라이드 |
| 7 | `UBrowseToAssetOverrideSubsystem` | 같음 | 컨텐츠 브라우저 "Browse to" 오버라이드 |
| 8 | `UBrushEditingSubsystem` | 같음 | BSP 브러시 편집 |
| 9 | `UCollectionManagerScriptingSubsystem` | 같음 | 컬렉션 (Editor Scripting) |
| 10 | `UActorEditorContextSubsystem` | 같음 | 액터 배치 컨텍스트 (현재 폴더 / 레벨) |
| 11 | `UUnrealEditorSubsystem` | 같음 | 잡다한 에디터 헬퍼 (스크린샷 / 뷰포트) |
| 12 | `UEditorSubsystemBlueprintLibrary` | 같음 | BP 헬퍼 (UEditorSubsystem 자체는 아님) |

### 2.2. UAssetEditorSubsystem 핵심 API (가장 자주, §3.1)

| API | 라인 | 의미 |
| -- | -- | -- |
| `OpenEditorForAsset(UObject*, EAssetTypeActivationOpenedMethod, EAssetEditorToolkitFocusOption)` ⭐ | L138 | 에디터 열기 |
| `OpenEditorForAssets(TArray<UObject*>&)` | L162 | 다중 |
| `CloseAllEditorsForAsset(UObject*)` / `CloseAllAssetEditors()` | — | 닫기 |
| `FindEditorForAsset(UObject*, bool bFocusIfOpen)` | — | 진행 중 인스턴스 |
| `FindEditorsForAsset(UObject*)` | — | 다중 인스턴스 |
| `NotifyAssetClosed(UObject*, IAssetEditorInstance*)` | — | 닫힘 통지 |

### 2.3. UAssetEditorSubsystem 이벤트 5종 (§3.2)

| 델리게이트 | 라인 | 의미 |
| -- | -- | -- |
| `OnAssetEditorRequestClose()` | L176 | 닫기 요청 (2-param, EAssetEditorCloseReason) |
| `OnAssetOpenedInEditor()` ⭐ | L190 | 열림 (2-param, UObject*, IAssetEditorInstance*) |
| `OnEditorOpeningPreWidgets()` | L197 | 열리기 직전 (위젯 생성 전) |
| `OnAssetClosedInEditor()` | L204 | 닫힘 |
| `OnAssetEditorRequestedOpen()` | L214 | 열기 요청 (가로채기 가능) |

자세한 EditorName static_cast 안전 + EAssetEditorCloseReason 8종 → [[sources/ue-editor-asseteditorapi]] (페어).

### 2.4. 표준 사용 패턴

```cpp
#if WITH_EDITOR
if (UAssetEditorSubsystem* Sub = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>())
{
    Sub->OpenEditorForAsset(MyAsset);
    TArray<IAssetEditorInstance*> Editors = Sub->FindEditorsForAsset(MyAsset);
}
#endif
```

### 2.5. UEditorActorSubsystem — 레벨 액터 (BP/Python)

`SpawnActorFromObject` / `SpawnActorFromClass` / `DestroyActor` / `SetSelectedLevelActors` / `GetSelectedLevelActors` / `ConvertActorWith` — Editor Utility BP 의 자동화 진입점.

### 2.6. UEditorAssetSubsystem — Asset 파일 (BP/Python)

`SaveAsset(FString AssetPath)` / `DeleteAsset` / `RenameAsset` / `DuplicateAsset` / `DoesAssetExist` / `GetMetadataTag` / `GetMetadataTagsValues` — Build 자동화 + Asset Migration 도구.

### 2.7. UImportSubsystem — Reimport 콜백

`OnAssetPreImport` / `OnAssetPostImport` / `OnAssetReimport` 멀티캐스트 — 사용자 정의 임포트 후처리 진입.

### 2.8. 함정 (§함정 — 핵심)

- `GEditor` 가 nullptr (Commandlet / -nullrhi 환경) → IsValid 검사
- `OpenEditorForAsset` 직접 호출 시 매번 새 인스턴스 추측 X — 이미 열려있으면 포커스
- BP 노출 함수 (`UFUNCTION(BlueprintCallable, Category="...")`) — Editor Utility BP 에서만 호출 가능 (게임 BP X)
- Initialize / Deinitialize 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` ([[concepts/Profiling-Scope-Rule]])
- 다른 EditorSubsystem 의존 시 Initialize 순서 — `Collection.InitializeDependency<T>()` 명시

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어: [[sources/ue-editor-asseteditorapi]] (`IAssetEditorInstance` static_cast 안전) / [[sources/ue-editor-editorsubsystem]] (UEditorSubsystem 베이스 모듈) / [[sources/ue-subsystem-skill]] (5 Subsystem 통합)
- 횡단: [[sources/ue-ref-05-editoronlyindex]] / [[sources/ue-ref-07-profilingscopeRule]]
