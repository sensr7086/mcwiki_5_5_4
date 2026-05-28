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
