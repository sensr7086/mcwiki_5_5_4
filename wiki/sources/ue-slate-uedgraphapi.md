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
