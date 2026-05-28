---
type: concept
title: "UE Garbage Collection (GC)"
aliases: [GC, Garbage Collection, CollectGarbage]
sources:
  - "[[sources/ue-coreuobject-skill]]"
related_concepts:
  - "[[concepts/Reflection-System]]"
  - "[[concepts/Object-Handles]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, foundation]
last_updated: 2026-05-09
---

# UE Garbage Collection

## 1. 정의 (한 줄)

[[entities/UObject]] 자손의 reachability 기반 자동 메모리 관리 — UPROPERTY 표시된 멤버가 edge, RootSet 이 시작점, 도달 가능한 객체는 살리고 나머지는 destroy.

## 2. 자세히

- 시작점: RootSet (`AddToRoot()` / Engine 자체 보유 / GameInstance / World 등).
- Edge: UPROPERTY 로 표시된 [[entities/UObject]] 자손 멤버. `TObjectPtr<>` / `TArray<TObjectPtr<>>` / `TMap<*, TObjectPtr<>>` 등.
- Mark-Sweep: 도달 가능한 객체에 mark, 끝나면 unmark 객체 destroy (BeginDestroy → FinishDestroy 라이프사이클).
- 호출: 자동 (주기적, GC.TimeBetweenPurgingPendingKillObjects) + 수동 (`CollectGarbage(RF_NoFlags, true)`).

## 3. 변형 / 사례 / 응용

- **UPROPERTY 누락 함정**: `UMyComp* Mesh;` (UPROPERTY 없음) → GC 가 Mesh 객체를 reachable 로 안 봄 → 다음 GC 에서 Mesh destroy → dangling pointer crash. → [[concepts/Component-Policies-6]] 의 GC 방어 의무.
- **TWeakObjectPtr**: lifetime 분리 캐싱. 대상 객체 destroy 되면 자동 NULL — GC 와 race condition 회피.
- **TStrongObjectPtr**: 비-UCLASS 컨텍스트에서 UObject 강참조 (드물게 사용).
- **AddToRoot / RemoveFromRoot**: 명시적 RootSet 등록. 너무 자주 사용하면 메모리 leak — 필요 시점에만.

## 4. 관련 entity

- [[entities/UObject]]
- [[entities/UClass]]

## 5. 열린 질문

- [ ] Incremental GC (5.x) 의 frame budget 분할
- [ ] Cluster GC — `UCLASS(WithinClass=)` 와의 통합
