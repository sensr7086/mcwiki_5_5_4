---
title: "Material Editor 외부 변경 미감지 → 강제 재오픈 패턴"
kind: concept
status: stable
severity: "★★★"
tags: [editor, material, refresh, MMA-33, MMA-34, hazard, ue-574]
created: 2026-05-22
last_updated: 2026-05-27
audit_5_5_4: partial-internal-differs  # 2026-05-27 Phase 2 engine grep 완료
---

# Material Editor 외부 변경 미감지 → 강제 재오픈 패턴

## 정의

`UMaterial` 객체를 **에디터 외부**(C++ 코드 / MCP 서버 / 스크립트)에서 수정한 뒤, 이미 열려 있는 Material Editor 창의 UI(노드 그래프 + Preview viewport + Details panel)가 **자동으로 갱신되지 않는 현상**과 이를 해결하는 3-단계 강제 재오픈 패턴.

**단일 호출로는 부족** — `Material->PostEditChange()` 만 호출하면 셰이더는 재컴파일되지만 그래프 노드는 stale UI 로 남는다. `UMaterialGraph::RebuildGraph()` + `NotifyGraphChanged()` 까지 호출해야 그래프 노드 가시성이 일치하지만, **Preview viewport 와 Details panel 은 여전히 stale**. 완전한 동기화에는 `AssetEditorSubsystem` 의 **close + reopen** 이 필요.

## 자세히 (3-Layer Refresh)

### Layer 1 — `Material->PostEditChange()` (불충분)

🟢 **VAULT** — `entities/UMaterial` § PostEditChange:
- 셰이더 재컴파일 트리거 (FMaterialUpdateContext 내부 실행)
- 머티리얼 인스턴스 invalidation 전파
- **하지만**: Material Editor 의 SGraphPanel 은 `UEdGraph` 의 변경 broadcast 를 별도 subscribe — `UMaterial::PostEditChange` 만으로는 graph 가 reissue 되지 않음

### Layer 2 — `UMaterialGraph::RebuildGraph()` + `NotifyGraphChanged()` (여전히 불충분)

🟡 **PARTIAL** — UE 5.7 소스 (`Engine/Source/Editor/UnrealEd/Private/MaterialGraph/`) 검토:
```cpp
if (UMaterialGraph* MaterialGraph = Cast<UMaterialGraph>(Material->MaterialGraph))
{
    MaterialGraph->RebuildGraph();         // expression → node 재생성
    MaterialGraph->NotifyGraphChanged();   // SGraphPanel 에 invalidation broadcast
}
```
이 단계까지 호출하면:
- ✅ 그래프 노드 가시성 일치 (새 노드 보임, 삭제된 노드 사라짐)
- ✅ 연결선(wire) 갱신
- ❌ **Preview viewport** 의 머티리얼 미리보기는 stale (이전 셰이더 표시)
- ❌ **Details panel** 에서 선택 중이던 expression 이 사라져도 panel 은 stale

🔴 **INFERRED** — Material Editor toolkit 의 Preview viewport 는 자체 `UMaterialInstanceDynamic` 또는 cached resource 를 들고 있고, graph change broadcast 로는 이 cache 가 invalidate 되지 않는 것으로 보임.

### Layer 3 — `AssetEditorSubsystem` close + reopen (확실한 해결)

🟢 **VAULT** — `entities/UAssetEditorSubsystem`:
```cpp
UAssetEditorSubsystem* AES = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
if (AES && AES->FindEditorForAsset(Material, /*bFocusIfOpen*/false))
{
    AES->CloseAllEditorsForAsset(Material);
    AES->OpenEditorForAsset(Material);
}
```
- ✅ 전체 toolkit 재생성 → Preview / Details / Graph 모두 fresh
- ⚠️ **side effect**: 사용자가 선택했던 노드 / viewport 카메라 위치 / details scroll position 모두 reset
- ⚠️ **race**: close 직후 reopen 사이에 짧은 깜빡임 — 사용자 인지 가능

## 회피 패턴 (Production-Ready Helper)

MCMaterialAuto v0.14.13 채택:

```cpp
void RefreshMaterialEditor(UMaterial* Material)
{
    if (!Material) return;
    Material->PostEditChange();
    if (UMaterialGraph* G = Cast<UMaterialGraph>(Material->MaterialGraph))
    {
        G->RebuildGraph();
        G->NotifyGraphChanged();
    }
}

void ForceReopenMaterialEditor(UMaterial* Material)
{
    if (!Material) return;
    if (GEditor)
    {
        UAssetEditorSubsystem* AES = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
        if (AES)
        {
            AES->CloseAllEditorsForAsset(Material);
            AES->OpenEditorForAsset(Material);
        }
    }
}
```

**전략**:
- 가벼운 변경 (Connection / property change) → `RefreshMaterialEditor()` 만
- 구조적 변경 (add/delete expression, recompile, MIC 부모 교체) → 둘 다 호출 (`RefreshMaterialEditor()` 후 `ForceReopenMaterialEditor()`)

## 변형 사례

1. **Material Instance Constant (MIC)**:
   - 부모 머티리얼 변경 시 MIC 의 Details panel 갱신도 동일 문제
   - `MIC->PostEditChange()` 만으로는 부모 expression 변경이 MIC override slot 에 반영 안됨
   - → `ForceReopenMaterialEditor(MIC)` 또는 부모 머티리얼 reopen 시 MIC 도 함께 reopen

2. **MaterialFunction 편집**:
   - 함수 본체 변경 후 함수를 사용하는 머티리얼들의 stale 발생
   - `UMaterialEditingLibrary::UpdateMaterialFunction()` 가 부모 머티리얼 재컴파일 처리 — 별도 reopen 불요한 것으로 보임 (🔴 INFERRED, MMA-37 후속 검증 필요)

3. **Recompile flag fallback**:
   - `MarkPackageDirty()` 단독 호출은 효과 없음 — dirty flag 는 save 만 영향, UI refresh 와 무관

## 관련 entity

- [[UMaterial]]
- [[UMaterialGraph]]
- [[UAssetEditorSubsystem]]
- [[UMaterialEditingLibrary]]
- [[FMaterialUpdateContext]] (PostEditChange 내부)
- [[FAssetEditorToolkit]] (Material Editor toolkit base)

## 열린 질문

1. ❓ Material Editor toolkit 의 Preview viewport 가 어떤 cached resource 를 들고 있는지 — UE 5.7 소스 정확한 위치 미특정. `Engine/Plugins/MaterialAnalyzer` 와 `MaterialEditor` 모듈에서 추가 조사 필요.
2. ❓ Close+Reopen 의 깜빡임을 완화할 수 있는 다른 API 존재 여부 — `FMaterialEditor::RefreshExpressionPreviews()` 또는 `RefreshPreviewViewport()` 가 toolkit private 인터페이스에 있을 가능성. 5.7 소스 grep 필요.
3. ❓ MaterialFunction 편집 시 부모 머티리얼들의 자동 refresh 가 어디까지 동작하는지 — Phase C 검증 미완.

## Cross-link

- `concepts/Python-Stdio-MCP-Buffering-Hazard` (같은 v0.14 작업 중 발견)
- `concepts/UE-HttpServer-Body-NullTerm-Hazard` (같은 v0.14 작업 중 발견)
- `synthesis/UE-Editor-External-Modification-Patterns` (TODO — 다른 외부 변경 패턴들 합성 필요)
- `00_meta/03_EvaluatorRecipe` § Stage 5 (UI-Layer Refresh 검증)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| `PostEditChange` 셰이더 재컴파일 트리거 | 🟢 VAULT | `entities/UMaterial` |
| `RebuildGraph` + `NotifyGraphChanged` 가 그래프만 갱신 | 🟡 PARTIAL | UE 5.7 소스 직접 검토, vault 미기록 |
| Preview viewport 가 자체 cache 보유 | 🔴 INFERRED | 행동 관찰 — 소스 위치 미확인 |
| `CloseAllEditorsForAsset` + `OpenEditorForAsset` 동작 | 🟢 VAULT | `entities/UAssetEditorSubsystem` |
| MaterialFunction 자동 propagation | 🔴 INFERRED | Phase C 검증 미완 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-33/34 fix 직후, MCMaterialAuto v0.14.13 채택본 기반)
## §X. 5.5.4 Audit Status (2026-05-27) — engine grep 완료

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3·§5 · **결정**: partial-internal-differs

**검증 결과 (engine source dual-grep, 2026-05-27)**:

- `MaterialGraph.cpp` 라인: **5.5.4 = 1020 / 5.7.4 = 827** (5.5.4 가 193 라인 더 많음 — 5.7 에서 코드 단순화/리팩토)
- `UMaterialGraph::RebuildGraph`: 5.5.4 line 55 / 5.7.4 line 54 (양쪽 존재)
- `UMaterialGraph::NotifyGraphChanged`: 5.5.4 line 955 / 5.7.4 line 762 (양쪽 존재)
- 호출 패턴 (`RebuildGraph + NotifyGraphChanged` 가 그래프만 갱신) — 함수 존재만 확인, 내부 구현 193 라인 delta 가 cache 동작에 어떻게 영향하는지 미확인
- **결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론 (CloseAllEditorsForAsset + OpenEditorForAsset reopen 패턴) 은 5.5.4 에서도 작동 가능성 高 (UAssetEditorSubsystem API stable). 단 MaterialGraph 내부 cache 동작이 5.5.4 ↔ 5.7.4 사이 변동했으므로 RebuildGraph fallback 시도가 5.5.4 에서는 다른 결과 낼 수 있음.

> 본 audit 는 5.5.4 + 5.7.4 engine source 직접 grep 으로 수행 (2026-05-27). `[[raw/ue-wiki-llm/...]]` 인용은 5.7.4 vintage 자료 보존, 새 검증은 engine source 본가 기반.
