---
type: source
title: "UE Slate — ListsTrees sub-skill"
slug: ue-slate-liststrees
source_path: raw/ue-wiki-llm/skills/Slate/references/ListsTrees.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
tags: [ue, slate, ui]
---

# UE Slate — ListsTrees sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/ListsTrees.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

데이터 기반 리스트 위젯 — SListView + STreeView + STableRow + ITableRow.

## 2. Key claims

- SListView<ItemType>: ListItemsSource 의 each item 마다 OnGenerateRow delegate 로 row 위젯 생성.
- STreeView<ItemType>: 계층 구조. OnGetChildren delegate 로 자식 노드 query.
- STableRow<ItemType>: 단일 row 위젯 베이스. Padding / 콘텐츠 / Selection state 처리.
- ITableRow: row 인터페이스 — Custom row 위젯 작성 시 구현.
- Performance: 가시 영역만 row 생성 (virtualization) — 큰 리스트도 효율적. [[concepts/Slate-Invalidation]] 회피의 모범.
- OnSelectionChanged / OnDoubleClick / OnContextMenuOpening delegate.
