---
type: source
title: "UE Components — UActorComponent sub-skill"
slug: ue-components-actorcomponent
source_path: raw/ue-wiki-llm/skills/Components/references/ActorComponent.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UActorComponent]]"
related_concepts:
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components]
---

# UE Components — UActorComponent sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/ActorComponent.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

[[entities/UActorComponent]] 로직 전용 컴포넌트 베이스 — BeginPlay / EndPlay / TickComponent / GetOwner / Replication / Subobject 등록 + 6대 정책 의무.

## 2. Key claims

- 라이프사이클 6단계 ([[concepts/Component-Lifecycle]]): OnRegister → InitializeComponent → BeginPlay → Tick → EndPlay → UninitializeComponent → OnUnregister.
- Super 호출 규약: BeginPlay → Super FIRST, EndPlay → Super LAST.
- GetOwner: BeginPlay 에서 1회 캐싱 + TWeakObjectPtr 보관. Tick / 콜백 재조회 금지. → [[concepts/Component-Policies-6]] §4.
- TickComponent: PrimaryComponentTick.bCanEverTick = false 가 기본. 활성 시 TickInterval 우선.
- Replication: SetIsReplicatedByDefault(true) 또는 owning Actor 의 bReplicates. UPROPERTY(Replicated) + GetLifetimeReplicatedProps.
- Subobject 등록: CreateDefaultSubobject (Constructor 안만) 또는 NewObject<>(Outer=Actor) (런타임).

## 3. Open questions

- [ ] InitializeComponent vs BeginPlay 호출 순서 — Editor PIE vs Cooked
