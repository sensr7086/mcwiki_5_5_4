---
name: editor-scenarios
description: Editor 카테고리 8 시나리오 → sub-skill 묶음 상세 — 인하우스 에셋 에디터 / 디테일 패널 / 메뉴/툴바 / 노드 그래프 / Editor Subsystem / 에셋 검색 / 레벨 에디터 / 실행 중인 에셋 에디터 접근. (parent — Editor/SKILL.md)
---

# Editor — 시나리오별 sub-skill 묶음 상세

> **Parent**: [`../SKILL.md`](../SKILL.md)
> **요지**: 인하우스 에디터 도구 작성 시 시나리오 → 필요 sub-skill 묶음 매핑.

---

## 1. 인하우스 에셋 에디터 (가장 일반적) ⭐

> 새 에셋 타입 + 전용 에디터 윈도우 작성 (예: 행동 트리 에디터, 머티리얼 그래프 등).

**필수 묶음** (5개):
1. **`UnrealEd/AssetEditorToolkit`** — 도킹 + 그래프 에디터 통합
2. **`AssetTools`** — `IAssetTypeActions` 으로 "Create > MyAsset" 등록
3. **`UnrealEd/Factories`** — `UFactory` 자식 (새 에셋 생성)
4. **`PropertyEditor`** — Details 패널 커스터마이징
5. **`ToolMenus`** — 메뉴/툴바 통합

**선택**: `EditorFramework` (Toolkit 베이스 깊이) / `Slate/Docking` (도킹 레이아웃) / `Slate/Commands` (단축키) / `Slate/GraphEditor` (노드 그래프 시) / `EditorSubsystem` (Editor-only 서비스).

---

## 2. 디테일 패널 커스터마이징만

**필수**: `PropertyEditor` (단일).
**선택**: `EditorWidgets` (`SEnumCombo`, `SAssetSearchBox` 등 표준 위젯).

---

## 3. 메뉴/툴바만 추가

**필수**: `ToolMenus` (5.x 모던 표준).
**선택**: `MainFrame` (메인 메뉴 후크) / `LevelEditor` (LevelEditor.MainMenu.*) / `Slate/Commands` (단축키).

---

## 4. 노드 그래프 에디터 (인하우스 비주얼 스크립트)

**필수**: `Slate/GraphEditor` (노드 그래프 작성 패턴) + `UnrealEd/AssetEditorToolkit` (Toolkit 진입).
**선택**: `UnrealEd/Kismet2` (BP 컴파일 패턴 참고).

---

## 5. Editor Subsystem 작성

**필수**: `EditorSubsystem` (베이스) + [`Subsystem/SKILL.md`](../../Subsystem/SKILL.md) (5종 통합 가이드).
**선택**: `UnrealEd/Subsystems` (UEditorActorSubsystem / UEditorAssetSubsystem 표준 패턴).

---

## 6. 에셋 검색 / 의존성 추적

**필수**: `AssetRegistry` + `CoreUObject/ObjectHandles` (FSoftObjectPath / FAssetData).
**선택**: `UnrealEd/Misc` (에디터 헬퍼).

---

## 7. 레벨 에디터 확장

**필수**: `LevelEditor` + `UnrealEd/Layers` (DataLayer 5.x).
**선택**: `UnrealEd/Elements` (5.x Element 선택 시스템) / `MainFrame` (메뉴 통합).

---

## 8. 실행 중인 에셋 에디터 접근 ⭐ (도구 확장 / 자동화)

> 이미 열려있는 StaticMesh / SkeletalMesh / Material 에디터 등에 외부 코드에서 접근.

**필수**: `AssetEditorAPI` — `UAssetEditorSubsystem::FindEditorForAsset` + EditorName 검증 후 `static_cast` (IStaticMeshEditor / ISkeletalMeshEditor / IPersonaToolkit).
**선택**: `EditorSubsystem` (이벤트 바인딩 — OnAssetOpenedInEditor / OnAssetEditorRequestClose) / `EditorFramework` (Toolkit 베이스).
**Build.cs 의무**: `"UnrealEd", "StaticMeshEditor", "SkeletalMeshEditor", "Persona", "AdvancedPreviewScene"`.

---

## 시나리오 결정 트리 요약

| 작업 | 진입 sub-skill | Build.cs 추가 의무 |
|------|---------------|--------------------|
| 새 에셋 타입 + 에디터 | UnrealEd/AssetEditorToolkit + AssetTools + Factories | UnrealEd, AssetTools, PropertyEditor, ToolMenus |
| 디테일 패널만 | PropertyEditor | PropertyEditor |
| 메뉴/툴바만 | ToolMenus | ToolMenus, MainFrame, LevelEditor |
| 노드 그래프 | Slate/GraphEditor + AssetEditorToolkit | GraphEditor, UnrealEd |
| Editor Subsystem | EditorSubsystem | UnrealEd, EditorSubsystem |
| 에셋 검색 | AssetRegistry | AssetRegistry |
| 레벨 에디터 확장 | LevelEditor + Layers | LevelEditor, UnrealEd |
| 실행 중 에디터 접근 | AssetEditorAPI | UnrealEd, StaticMeshEditor, SkeletalMeshEditor, Persona, AdvancedPreviewScene |
