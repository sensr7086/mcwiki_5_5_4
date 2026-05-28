---
type: source
title: "UE Slate — UEdGraph API Deep"
slug: ue-slate-uedgraphapi
source_path: raw/ue-wiki-llm/skills/Slate/references/GraphEditor/UEdGraphAPI.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/UEdGraph]]"
tags: [ue, slate, editor, deep]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE Slate — UEdGraph API Deep

> Source: [[raw/ue-wiki-llm/skills/Slate/GraphEditor/references/UEdGraphAPI.md]]
> Parent: [[sources/ue-slate-grapheditor]]

## 1. Summary

[[entities/UEdGraph]] + UEdGraphNode + UEdGraphSchema + SGraphNode + FConnectionDrawingPolicy 깊이 자료 — 자주 쓰는 API 5 종 + 가상 함수 50+ 오버라이드 포인트.

## 2. Key claims

- UEdGraph API:
  - GetGraphNodes / AddNode / RemoveNode / GetSchema.
  - GetSelectedNodes (Editor session).
- UEdGraphNode 가상 카탈로그 50+:
  - AllocateDefaultPins / ReconstructNode / GetNodeTitle / GetTooltipText / NodeConnectionListChanged / PinDefaultValueChanged / etc.
- UEdGraphSchema 가상:
  - CanCreateConnection (pin 연결 검증) / TryCreateConnection / GetGraphContextActions.
- SGraphNode (Slate 위젯):
  - CreatePinWidgets / CreateBelowPinControls / GetTitleColor / GetNodeBodyBrush.
- FConnectionDrawingPolicy: wire 그리기 (color / thickness / arrow style).
- Custom Node 작성 표준: UEdGraphNode 자손 + UEdGraphSchema 자손 + SGraphNode 자손 + FConnectionDrawingPolicy 자손 (필요 시).
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 3
- 추가 (5.5.4 에만): 31
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `| `virtual TSharedPtr<SWidget> CreateNodeImage() const` 🛠 | L967 | 노드 미니맵 이미지. | → | `virtual void AllocateDefaultPins()` | EdGraphNode.h L694 | **핵심** — 노드 생성 시 핀`
- `| `virtual const FPinConnectionResponse CanCreateConnection(const UEdGraphPin* A → | `virtual const FPinConnectionResponse CanCreateConnection(const UEdGraphPin* A`
- `| `virtual void CreateDefaultNodesForGraph(UEdGraph&) const` | L1091 | 새 그래프 생성  → | `virtual const FPinConnectionResponse CanMergeNodes(const UEdGraphNode* A, con`

**5.5.4 에만 (5.7.4 에 없음)**:
- `| `virtual void ReconstructNode()` | L702 | 리프레시 시 핀 재구성 (옛 데이터 마이그레이션). |`
- `| `virtual void PinDefaultValueChanged(UEdGraphPin*)` | L812 | 핀 기본값 변경 시 — 의존 노드 갱신. |`
- `| `virtual void PinConnectionListChanged(UEdGraphPin*)` | L815 | 핀 연결/해제 시. |`
- `| `virtual void PinTypeChanged(UEdGraphPin*)` | L818 | 핀 타입 변경 시 (Wildcard 등). |`

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Slate/references/GraphEditor/UEdGraphAPI.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Slate/references/GraphEditor/UEdGraphAPI.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
