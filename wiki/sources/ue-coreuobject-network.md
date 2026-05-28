---
type: source
title: "UE CoreUObject — Network sub-skill"
slug: ue-coreuobject-network
source_path: raw/ue-wiki-llm/skills/CoreUObject/references/Network.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UObject]]"
  - "[[entities/UNetDriver]]"
related_concepts:
  - "[[concepts/Replication]]"
  - "[[concepts/RPC]]"
  - "[[concepts/PushModel]]"
tags: [ue, runtime, foundation, coreuobject, networking]
---

# UE CoreUObject — Network sub-skill

> Source: [[raw/ue-wiki-llm/skills/CoreUObject/references/Network.md]]
> Parent: [[sources/ue-coreuobject-skill]]

## 1. Summary

CoreUObject 측 네트워크 primitives — UFUNCTION RPC (Server / Client / NetMulticast) + DOREPLIFETIME + RepNotify (OnRep_*) + NetSerialize + [[concepts/PushModel]] + Owner / Connection / Authority 권한. 게임플레이 측 패턴은 [[sources/ue-networking-skill]].

## 2. Key claims

- UFUNCTION RPC 매크로 매트릭스 — Server / Client / NetMulticast × Reliable / Unreliable.
- DOREPLIFETIME 매크로: GetLifetimeReplicatedProps 안에서 `DOREPLIFETIME(MyClass, MyProp)` — Replicated UPROPERTY 등록.
- RepNotify: `UPROPERTY(ReplicatedUsing=OnRep_Var)` — Client 측 변경 callback.
- NetSerialize override: USTRUCT 의 custom 직렬화 (FFastArraySerializer 의 베이스).
- Push Model: `MARK_PROPERTY_DIRTY_FROM_NAME` 명시 — Pull 모델 대체.
- Owner / Connection / Authority: RPC 가 어느 노드로 가는지 결정 — Actor 의 Owner chain.

## 3. Quotations

> "본 sub-skill 은 CoreUObject 의 네트워크 primitives. 게임플레이 차원의 패턴은 ue-networking-skill 참조."

## 4. Open questions

- [ ] FFastArraySerializer 와 NetSerialize 의 통합 패턴
