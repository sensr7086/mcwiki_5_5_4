---
type: entity
title: "UEdGraph / UEdGraphNode"
aliases: [UEdGraph, UEdGraphNode, EdGraph]
kind: model
sources:
  - "[[sources/ue-blueprint-skill]]"
tags: [ue, blueprint, editor]
last_updated: 2026-05-09
---

# UEdGraph / UEdGraphNode

## 요약

🛠 Editor 만의 노드 그래프 표현. [[entities/UBlueprint]] 가 보유. EventGraph / Construction Script / Function Graphs / Macro Graphs 의 베이스. UEdGraphNode 자손이 개별 노드 (UK2Node_CallFunction / UK2Node_VariableGet 등).

## 관계

- 부모: [[entities/UObject]]
- 페어: [[entities/UBlueprint]] (Editor 만)
- 협력: SGraphEditor (Slate 위젯), FBlueprintCompilerContext (컴파일러)

## 핵심 주장

- Editor 만 — `WITH_EDITORONLY_DATA` 가드. Cooked 빌드 stripped.
- 핵심 자손: UEdGraphSchema (그래프 종류별 규칙) / UEdGraphNode (노드) / UEdGraphPin (핀).
- BP 의 EventGraph / Construction Script / Function Graphs / Macro Graphs 의 베이스 — UBlueprint 가 보유한 UEdGraph 컬렉션.
- 5.x: AnimGraph / MaterialGraph / NiagaraGraph 등 다른 그래프 시스템도 UEdGraph 자손 사용.
- 사용자 정의 노드 자손 (UK2Node 등) — 5.x 표준 패턴.

## 열린 질문

- [ ] Custom UK2Node 작성 표준 패턴
- [ ] 5.x State Tree Graph 의 UEdGraph 통합
