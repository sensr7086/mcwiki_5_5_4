---
type: source
title: "UE Editor — IStaticMeshEditor 접근 표준"
slug: ue-editor-staticmesheditor
source_path: raw/ue-wiki-llm/skills/Editor/AssetEditorAPI/references/StaticMeshEditor.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities:
  - "[[entities/IToolkit]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, editor, asseteditorapi, staticmesh, enriched-card, layout-delegate-bypass]
citation_disclosure: "🟢 8 / 🟡 2 / 🔴 0 · raw verified · Cycle 5f #2 enrich"
---

# UE Editor — IStaticMeshEditor 접근 표준 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/AssetEditorAPI/references/StaticMeshEditor.md]]
> Parent: [[sources/ue-editor-asseteditorapi]] · [[sources/ue-editor-skill]]
> Cycle 5f #2 — stub 카드 → enrich 카드 (raw 본문 + layout delegate 우회 cross-link + 3-tier marker)

## 1. Summary

🟢 `IStaticMeshEditor` = StaticMesh asset editor toolkit interface. `Engine/Source/Editor/StaticMeshEditor/Public/IStaticMeshEditor.h`. `GetStaticMeshComponent()` / preview LOD 노출. ⚠ `SetGenericLayoutDetailsDelegate` 우회 강제 (Cycle 5b/5e 검증) — 외부 customization 시도 시 stub.

## 2. 표준 패턴 — 외부 코드에서 Preview Component 접근 (raw §1) 🟢

```cpp
#if WITH_EDITOR
#include "IStaticMeshEditor.h"
#include "Subsystems/AssetEditorSubsystem.h"

void AccessStaticMeshEditor(UStaticMesh* Mesh)
{
    if (!IsValid(Mesh)) return;

    UAssetEditorSubsystem* AES = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
    IAssetEditorInstance* EditorInst = AES->FindEditorForAsset(Mesh, /*bFocusIfOpen=*/ false);
    if (!EditorInst) return;

    // EditorName 검증 의무
    if (EditorInst->GetEditorName() != FName("StaticMeshEditor")) return;

    // 안전 cast
    auto* SME = static_cast<IStaticMeshEditor*>(EditorInst);
    if (UStaticMeshComponent* PreviewComp = SME->GetStaticMeshComponent())
    {
        // Preview Component 사용 (Material 변경 / 시각화 등)
    }
}
#endif
```

## 3. 핵심 API + 매트릭스 🟢

| API | 반환 | 용도 |
|-----|------|------|
| `GetStaticMeshComponent()` | `UStaticMeshComponent*` | Preview viewport 메시 컴포넌트 |
| `RefreshTool()` | `void` | UI 강제 갱신 |
| `RefreshViewport()` | `void` | 3D 뷰포트 갱신 |
| `GetCustomLODSelectedIndex()` | `int32` | 현재 강제 LOD |
| `SetCustomLODSelectedIndex(int32)` | `void` | LOD 강제 |
| `RegisterOnPostUndo(FOnPostUndo::FDelegate)` | `void` | Undo 후 콜백 |

## 4. 활용 시나리오 (raw §2) 🟢

| 시나리오 | 사용 API | 비고 |
|----------|---------|------|
| Material 일괄 변경 도구 | `GetStaticMeshComponent()` + `SetMaterial` | 열려있는 Editor 의 Preview Material 동적 변경 |
| LOD 시각화 디버그 | `SetCustomLODSelectedIndex` | Preview LOD 강제 |
| Custom Thumbnail Capture | `GetStaticMeshComponent()` + RT 캡처 | Preview Component 기반 썸네일 |
| Editor Automation | 위 모두 | 자동 검증 도구 — Preview 상태 추출 |

## 5. ⚠ Layout Delegate 우회 함정 (Cycle 5b/5e 검증) 🟢

StaticMeshEditor 는 자체 layout delegate (`SetGenericLayoutDetailsDelegate`) 강제 사용 → 외부 모듈 `RegisterCustomClassLayout(UStaticMesh::StaticClass(), ...)` 시도 시 **MakeInstance/CustomizeDetails 미발화** (영구 stub).

검증 출처:
- 🟢 외부 에이전트 `StaticMeshNiagaraPreview_Journey.md` Phase 5 (7가지 시도 무위, 2026-05-12)
- 🟢 KMCProject 실측 (UE_LOG 진단, 2026-05-12)

회피 패턴: **Tab Spawner + DataAsset 분리** ([[synthesis/instanced-subobject-customization-bypass]] §4.3-4.4) 또는 **자손 DetailsView 직접 임베드**.

→ Cycle 5e 1차 §3.1 매트릭스 — StaticMeshEditor 만 🟢 우회 확정. SkeletalMeshEditor / AnimationEditor / AnimationBlueprintEditor 도 동일 메커니즘 (Persona `SetGenericLayoutDetailsDelegate` Engine grep 확인 2026-05-15) — Cycle 5f #5 격상 예정.

## 6. 함정 (raw §3 + Cycle 5b/5e 추가) 🟢

| # | 함정 | 정답 |
|---|------|------|
| 1 | EditorName 검증 없이 `static_cast` | UB 위험 — 반드시 `FName("StaticMeshEditor")` 검증 |
| 2 | `GetStaticMeshComponent()` 반환값 nullptr 미체크 | Preview 미초기화 시 가능 |
| 3 | 캐싱한 `IStaticMeshEditor*` 재사용 | 매 호출 `FindEditorForAsset` 재조회 |
| 4 ⭐ | `RegisterCustomClassLayout(UStaticMesh::Class, ...)` 시도 → 영구 stub | Tab Spawner 분리 ([[synthesis/instanced-subobject-customization-bypass]] §4.3) |
| 5 ⭐ | `IStaticMeshEditor.h` include 누락 (forward decl 만) → method 호출 시 incomplete type | full include |
| 6 ⭐ | Editor 외 모듈에서 호출 (Cooked 빌드 깨짐) | `#if WITH_EDITOR` 가드 |

## 7. Build.cs 의존성 🟢

```csharp
PrivateDependencyModuleNames.AddRange(new[] {
    "UnrealEd",                   // UAssetEditorSubsystem
    "StaticMeshEditor",           // IStaticMeshEditor
    "PropertyEditor",             // (옵션) Customization 시
});
```

## 8. Cross-link

- Parent: [[sources/ue-editor-asseteditorapi]] §3.1 EditorName 표 + §3.1 layout delegate 우회 매트릭스
- 카테고리 main: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 자매 sub-skill: [[sources/ue-editor-personatoolkit]] (`SkeletalMeshEditor` 대응) · [[sources/ue-editor-advancedpreviewscene]] · [[sources/ue-editor-eventbinding]]
- ⭐ **layout delegate 우회 deep**: [[synthesis/instanced-subobject-customization-bypass]] (§4.2 차원 2 + §4.3 Tab Spawner 우회)
- 측정: [[sources/ue-measure-instancedsubobject-2026-05-12]] (H1 ⭐⭐ 데이터)
- Citation: [[00_meta/06_VaultCitationRule]]

## 9. 신뢰도 + 변경 이력

| 항목 | tier | 출처 |
|------|------|------|
| 표준 접근 패턴 (`FindEditorForAsset` + EditorName + static_cast) | 🟢 verified | `Subsystems/AssetEditorSubsystem.h` + `IStaticMeshEditor.h` |
| `GetStaticMeshComponent()` 시그니처 | 🟢 verified | Engine source |
| `SetCustomLODSelectedIndex` / `RefreshTool` / `RefreshViewport` | 🟡 grep-listed | 일반 사용 표준 |
| Layout delegate 우회 강제 | 🟢 verified | 외부 에이전트 Journey Phase 5 실측 + KMCProject |
| 함정 6 (3 raw + 3 신규) | 🟢 verified | raw §3 + Cycle 5b/5e |

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | grep-listed stub 카드 작성 |
| 2026-05-15 | Cycle 5f #2 — stub → enrich (API 매트릭스 6 + 시나리오 4 + 함정 6 + layout delegate 우회 cross-link + 3-tier marker) |
