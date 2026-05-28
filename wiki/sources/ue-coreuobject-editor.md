---
type: source
title: "UE CoreUObject — Editor sub-skill"
slug: ue-coreuobject-editor
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/Editor.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UObject]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
tags: [ue, editor, foundation, coreuobject]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE CoreUObject — Editor sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/Editor.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

🛠 [[entities/UObject]] 의 Editor 전용 callback — PostEditChangeProperty + Modify (Undo/Redo) + PostEditUndo + IsDataValid + GetAssetRegistryTags + WITH_EDITOR / WITH_EDITORONLY_DATA 가드.

## 2. Key claims

- PostEditChangeProperty(FPropertyChangedEvent&) — Editor 패널 변경 콜백. 변경된 Property 식별 + 의존 갱신.
- Modify(): Undo/Redo 시스템에 변경 등록. 모든 Property 수정 전 호출 표준.
- PostEditUndo() — Undo / Redo 후 콜백. 의존 데이터 재생성.
- IsDataValid (5.x): 자산이 Editor 에 표시될 때 검증. Validation Errors / Warnings 반환.
- GetAssetRegistryTags(TArray<FAssetRegistryTag>&): 자산이 AssetRegistry 에 노출할 메타.
- 모든 callback `#if WITH_EDITOR` 가드 의무. → [[concepts/Editor-Only-4-Tier-Separation]]
- WITH_EDITORONLY_DATA: Editor 데이터 (raw source / DDC source) 만 — Cooked 빌드 stripped. → [[concepts/Cooked-vs-Uncooked]]

## 3. Quotations

> "Editor callback 모두 #if WITH_EDITOR 가드 의무. Cooked 빌드 stripped."

## 4. Open questions

- [ ] IsDataValid 의 5.x 표준 패턴 (자동 Editor 알림)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
