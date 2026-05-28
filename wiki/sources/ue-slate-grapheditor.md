---
type: source
title: "UE Slate — GraphEditor sub-skill"
slug: ue-slate-grapheditor
source_path: raw/ue-wiki-llm/skills/Slate/references/GraphEditor.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/UEdGraph]]"
tags: [ue, slate, editor]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE Slate — GraphEditor sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/GraphEditor.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

🛠 SGraphEditor + [[entities/UEdGraph]] + UEdGraphNode + UEdGraphSchema — 노드 그래프 에디터 (BP / AnimGraph / Material / Niagara 등 베이스).

## 2. Deep references

- [[sources/ue-slate-uedgraphapi]] — UEdGraph API 깊이 (50+ virtual override + Custom Node 표준)

## 3. Key claims

- SGraphEditor: Slate 위젯 — 노드 그래프 visualization + 인터랙션.
- UEdGraph (Editor 만): 그래프 데이터. WITH_EDITORONLY_DATA.
- UEdGraphNode: 개별 노드. UEdGraphPin (입출력 핀).
- UEdGraphSchema: 그래프 종류별 규칙 (어떤 노드가 connect 가능 / 시각 스타일).
- SGraphNode / SGraphPin: 노드 / 핀 의 Slate 표현.
- 사용처: BP Editor / AnimGraph / MaterialGraph / NiagaraGraph / 사용자 정의 노드.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
