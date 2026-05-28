---
type: source
title: "UE CoreUObject — GC sub-skill"
slug: ue-coreuobject-gc
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/GC.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UObject]]"
related_concepts:
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/Object-Handles]]"
tags: [ue, runtime, foundation, coreuobject, gc]
---

# UE CoreUObject — GC sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/GC.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

[[concepts/Garbage-Collection]] 의 풀 디테일 — CollectGarbage / IncrementalGC / MarkAsGarbage / IsValid / AddReferencedObject / FGCObject / FReferenceCollector / FReferenceChainSearch.

## 2. Key claims

- CollectGarbage(RF_NoFlags, bPerformFullPurge) — 명시적 GC 호출. 보통 자동 호출이 표준 (gc.TimeBetweenPurgingPendingKillObjects).
- IncrementalGC (5.x): 한 번에 모든 객체 mark 하지 않고 frame budget 안에서 분할.
- MarkAsGarbage / IsValid: Legacy MarkPendingKill 의 5.x 대체. WeakPtr 가 자동 NULL.
- FGCObject: 비-UCLASS 객체가 UObject 강참조 보유 — AddReferencedObjects override + GCObjectReferencer 등록.
- FReferenceCollector::AddReferencedObject(Obj) — FGCObject 의 override 안에서 GC 에 알림.
- FReferenceChainSearch — 디버깅: 왜 객체가 GC 안 되는지 reference chain 추적.
- AddToRoot / RemoveFromRoot — RootSet 명시 등록 (남용 금지).

## 3. Quotations

> "MarkAsGarbage 는 5.x 표준. Legacy MarkPendingKill 은 호환만."

## 4. Open questions

- [ ] FReferenceChainSearch 의 Editor 디버그 사용
- [ ] Cluster GC (UCLASS WithinClass=) 패턴
