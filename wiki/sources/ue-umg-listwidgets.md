---
type: source
title: "UE UMG — ListWidgets sub-skill"
slug: ue-umg-listwidgets
source_path: raw/ue-wiki-llm/skills/UMG/references/ListWidgets.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, umg, ui]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE UMG — ListWidgets sub-skill

> Source: [[raw/ue-wiki-llm/skills/UMG/references/ListWidgets.md]]
> Parent: [[sources/ue-umg-skill]]

## 1. Summary

데이터 기반 리스트 — UListView + UTileView + UTreeView + UDynamicEntryBox.

## 2. Key claims

- UListView: 1D 가상화 리스트. SetListItems(TArray<UObject*>) + EntryWidgetClass.
- UTileView: 2D grid 가상화 (인벤토리 표준). SetListItems + TileSize.
- UTreeView: 계층 (3D 가상화). OnGetItemChildrenForUserNode delegate.
- UDynamicEntryBox: 작은 컬렉션 (가상화 없음 — 모든 entry 매번 생성).
- 가상화: 가시 영역만 entry 위젯 생성 — 큰 리스트도 효율적.
- IUserObjectListEntry 인터페이스: entry 위젯이 구현 — OnListItemObjectSet(UObject* ListItemObject) callback.
- 5.x CommonUI Plugin 의 CommonListView 와 통합 권장 (게임 패드 navigation).
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
