---
type: source
title: "UE CoreUObject — ObjectHandles sub-skill"
slug: ue-coreuobject-objecthandles
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/ObjectHandles.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UObject]]"
related_concepts:
  - "[[concepts/Object-Handles]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
tags: [ue, runtime, foundation, coreuobject]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE CoreUObject — ObjectHandles sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/ObjectHandles.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

[[concepts/Object-Handles]] 의 풀 디테일 — TObjectPtr + TWeakObjectPtr + TSoftObjectPtr + FSoftObjectPath + FPrimaryAssetId + FObjectKey + Lazy Load 패턴 (5.x).

## 2. Key claims

- TObjectPtr<T> (5.x 표준): UPROPERTY 멤버의 raw pointer 안전 wrapper. Editor lazy resolve, Cooked raw pointer.
- TWeakObjectPtr<T>: GC 무시 + 자동 NULL on destroy. TWeakObjectPtr::IsValid().
- TSoftObjectPtr<T>: path 만 보유 + 명시적 LoadSynchronous() 또는 비동기. → [[concepts/Soft-Reference-vs-Hard]]
- FSoftObjectPath: Soft path 의 raw 형태 (FString wrapper). TSoftObjectPtr 가 wrapping.
- FPrimaryAssetId (UAssetManager 통합): Type:Name 식별자.
- FObjectKey: dictionary key 로 사용 안전 (UObject 가 destroy 돼도 key 는 유효).
- TStrongObjectPtr<T>: 비-UCLASS 컨텍스트의 RAII 강참조.
- Lazy Load: TObjectPtr 의 Editor 측 unresolved → 사용 시점에 resolve.

## 3. Quotations

> "TObjectPtr 5.x = Editor lazy resolve, Cooked raw pointer. UPROPERTY 안에서 raw T* 보다 권장."

## 4. Open questions

- [ ] FObjectKey 의 dictionary key 사용처
- [ ] Lazy Load 의 5.x Editor 동작 디테일
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
