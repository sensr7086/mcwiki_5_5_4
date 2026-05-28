---
title: "UMaterialGraph"
kind: entity
status: stub
parent: editor
tags: [editor, material, graph, edgraph, ue-574]
module: UnrealEd
header: "Public/MaterialGraph/MaterialGraph.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# UMaterialGraph

[[UEdGraph]] 의 specialization — Material Editor 에서 사용되는 그래프 모델. `UMaterial::MaterialGraph` 필드가 가리키며 UMaterialExpression 들의 visual representation (UMaterialGraphNode) 을 보관. **Editor-only** — runtime 셰이더 codegen 에는 사용되지 않음.

## 핵심 특성

- **Lazy rebuild**: Material 의 expression 배열 변경 시 `RebuildGraph()` 호출 의무 — 호출 안 하면 UI stale
- **Notify channel**: `NotifyGraphChanged()` 가 SGraphPanel 에 invalidation broadcast
- **이중 책임**: UMaterialExpression (data) ↔ UMaterialGraphNode (visual) 의 동기화 담당

## 주요 API

| API | 설명 |
|---|---|
| `RebuildGraph()` | Material 의 expression 배열을 읽어 graph node 재생성 |
| `NotifyGraphChanged()` | SGraphPanel invalidation broadcast |
| `AddExpression(UMaterialExpression*, bool bSelect)` | 그래프에 expression 추가 + node 생성 |
| `RemoveExpression(UMaterialExpression*)` | 노드 + expression 제거 |
| `LinkGraphNodesFromMaterial()` | input pin connection 복원 |

## 관련 함정

- [[concepts/Material-Editor-External-Change-Reopen]] — `RebuildGraph + NotifyGraphChanged` 만으로는 **Preview / Details panel 갱신 안됨** — 3-Layer 의무

## 관련 entity

- [[UEdGraph]] · [[UMaterial]] · [[UMaterialExpression]] · [[UMaterialEditingLibrary]] · [[UAssetEditorSubsystem]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| Editor-only — runtime 무관 | 🟢 VAULT |
| RebuildGraph + NotifyGraphChanged 동작 | 🟢 VAULT (UE 5.7 `MaterialGraph.cpp`) |
| Preview/Details panel 미갱신 | 🟡 PARTIAL (실측 — 정확한 cache mechanism 미특정) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-33+34 filing-back cross-link)
