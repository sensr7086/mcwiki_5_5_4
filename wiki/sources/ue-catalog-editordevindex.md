---
type: source
title: "UE catalog — EditorDevIndex"
slug: ue-catalog-editordevindex
source_path: raw/ue-wiki-llm/catalog/EditorDevIndex.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, catalog, editor]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE catalog — EditorDevIndex

> Source: [[raw/ue-wiki-llm/catalog/EditorDevIndex.md]]

## 1. Summary

`Engine/Source/Editor/` + `Engine/Source/Developer/` 모듈 카탈로그 — 인하우스 도구 / 에셋 에디터 / 디버그 도구 작성 시 진입점.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에만): 0
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `> **ToolMenus 위치 주의**: UE 5.7에서 `Engine/Source/Developer/ToolMenus/` (Editor가 아님 → > **ToolMenus 위치 주의**: UE 5.5에서 `Engine/Source/Developer/ToolMenus/` (Editor가 아님`

**5.5.4 에만 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/catalog/EditorDevIndex.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/catalog/EditorDevIndex.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
