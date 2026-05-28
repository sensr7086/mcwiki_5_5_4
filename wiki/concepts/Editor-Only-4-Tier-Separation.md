---
type: concept
title: "Editor-only 4단 분리 원칙"
aliases: [WITH_EDITOR, Editor Only, 4단 분리]
sources:
  - "[[sources/ue-editor-skill]]"
  - "[[sources/ue-build-skill]]"
related_concepts:
  - "[[concepts/Cooked-vs-Uncooked]]"
tags: [ue, editor, build, policy]
last_updated: 2026-05-09
---

# Editor-only 4단 분리 원칙

## 1. 정의 (한 줄)

Editor 전용 코드를 게임 출시 빌드에서 제외하는 4 단 방어 — 모듈 분리 + uplugin Type=Editor + Build.cs 분기 + `#if WITH_EDITOR` 가드. 위반 시 Cooked 빌드 실패 또는 보안/사이즈 문제. 자세한 코드 = [[raw/ue-wiki-llm/references/05_EditorOnlyIndex.md]].

## 2. 자세히

| 단 | 의무 | 위반 결과 |
| -- | -- | -- |
| 1. 모듈 분리 | Runtime 모듈 (게임) vs Editor 모듈 (Editor 만) — 두 모듈로 강제 | 게임 모듈에서 Editor API 호출 시 빌드 에러 |
| 2. uplugin Type | `Type=Editor` 명시 | Cooked 빌드 시 모듈 stripped |
| 3. Build.cs | `bBuildDeveloperTools=true` 필요. `if (Target.bBuildEditor) { ... }` 분기 | Editor 의존이 게임 빌드에 leak |
| 4. `#if WITH_EDITOR` 가드 | Runtime 모듈 안 Editor API 호출 시 가드 + `WITH_EDITORONLY_DATA` 도 동일 | Cooked 컴파일 에러 |

## 2.1. Editor 모듈 작성 시 *명시 의무* (LNK2019 회피)

> **vault verified**: [[sources/ue-editor-dependencies]] §3 시나리오별 Build.cs 추가 의존 표 + [[sources/ue-editor-staticmesheditor]] / [[sources/ue-editor-personatoolkit]] / [[sources/ue-editor-eventbinding]] 의 Build.cs 의존 명시.

UE 의 Editor 인프라가 다수 모듈로 분리돼 있어 헤더 include 만으로는 부족 — 링크 단계에서 unresolved external 발생. **베이스 클래스의 dllimport 심볼이 위치한 모듈을 Build.cs 에 명시** 해야 한다.

| 베이스 / 인터페이스 | 필요 모듈 | 메모 |
| -- | -- | -- |
| `UEditorSubsystem` 자손 | **`"EditorSubsystem"`** | `UnrealEd` 의존만으로는 LNK2019 — UE 5.x 에서 별도 분리. 헤더는 transitive 통과 (2026-05-11 log 참조) |
| `IStaticMeshEditor` 캐스트 | `"StaticMeshEditor"` | preview mesh 컴포넌트 접근 시 |
| `ISkeletalMeshEditor` 캐스트 | `"SkeletalMeshEditor"` | Persona 토킷 |
| `IPersonaToolkit::GetPreviewMeshComponent` | `"Persona"` | SkeletalMesh preview |
| `IPropertyTypeCustomization` / `IDetailCustomization` | `"PropertyEditor"` | 디테일 패널 커스터마이즈 |
| `UAssetEditorSubsystem::OnAssetOpenedInEditor` | `"UnrealEd"` 의존 (subsystem 자체) + **`"EditorSubsystem"`** (베이스) | 단 `UEditorSubsystem` 의 베이스는 별도 모듈 |
| `FAssetToolsModule` | `"AssetTools"` | 자산 등록 |
| `FToolMenuOwnerScoped` | `"ToolMenus"` | 메뉴 확장 |

**증상**: 헤더 컴파일은 OK, 링크 단계에서 `__imp_?Z_Construct_UClass_*` / `__imp_??0*::ClassName` 등 `__declspec(dllimport)` 심볼이 unresolved → `LNK1120`.

**진단 패턴**: 에러 메시지에서 `Z_Construct_UClass_<ClassName>` 또는 `<ClassName>::<ClassName>` 의 클래스 이름을 보고 그 클래스가 정의된 모듈을 찾아 Build.cs 에 추가.

## 3. 변형 / 사례 / 응용

- IDetailCustomization / IPropertyTypeCustomization 등 PropertyEditor 의존 = 모두 Editor 모듈.
- UPROPERTY(EditAnywhere) 자체는 Runtime 에 남음 — Editor 메타만 strip.
- WITH_EDITORONLY_DATA: Texture 의 raw pixel / Mesh 의 source tri / DDC source — Cooked 에 안 남음.
- 5.x WORLD Type 분기: PIE (`World->IsPlayInEditor()`) vs Cooked (`#if WITH_EDITOR`) 의미 다름.

## 4. 관련 entity

- [[entities/IToolkit]] / [[entities/UEdMode]] / [[entities/UToolMenus]] / [[entities/IDetailCustomization]] / [[entities/IAssetTools]] (모두 Editor 빌드만)

## 5. 열린 질문

- [ ] WITH_EDITOR vs WITH_EDITORONLY_DATA 의 정확한 차이
- [ ] PIE 와 Standalone 의 동작 차이 매트릭스
