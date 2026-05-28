---
type: entity
title: "AActor"
aliases: [AActor, Actor]
kind: model
sources:
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, gameframework, foundation]
last_updated: 2026-05-09
---

# AActor

## 요약

[[entities/UObject]] 자손. **모든 게임 객체의 컴포넌트 호스트** + [[entities/UWorld]] 에 Spawn 되는 단위. 5,074 lines (UE 5.7.4). 자체는 거의 비어있고 부착된 [[entities/UActorComponent]] 들이 실제 동작 담당. [[concepts/Actor-Lifecycle]] 11 단계 + Replication 진입점 + Tick 루트.

## 관계

- 부모: [[entities/UObject]]
- 자손: [[entities/APawn]] / [[entities/AController]] / [[entities/AGameModeBase]] / [[entities/AGameStateBase]] / APlayerState / 일반 AActor
- 컴포넌트 호스트: RootComponent ([[entities/USceneComponent]]) + 다수 [[entities/UActorComponent]]
- 컨테이너: [[entities/UWorld]] (PersistentLevel / StreamingLevels / OwnedActors)

## 핵심 주장

- [[concepts/Actor-Lifecycle]] 11 단계: PostActorCreated → PostInitProperties → PostInitializeComponents → BeginPlay → Tick → EndPlay → BeginDestroy → FinishDestroy + (생성자 / OnConstruction). Editor 와 Cooked 가 미묘하게 다름 — `RerunConstructionScripts` 매번 호출되어 멱등 의무. [[raw/ue-wiki-llm/skills/GameFramework/SKILL]]
- Spawn: `World->SpawnActor<T>(Class, Transform)` 표준. `SpawnActorDeferred + FinishSpawning` 으로 Property 셋업 후 BeginPlay 분리. **`NewObject<AActor>` 직접 호출 금지** (라이프사이클 우회). [[concepts/Asset-Loading-Policy]]
- Super 호출 규약: BeginPlay → Super FIRST, EndPlay → Super LAST. [[raw/ue-wiki-llm/references/04_OverrideIndex.md]]
- Tick: `PrimaryActorTick.bCanEverTick = false` 가 기본. TickGroup (TG_PrePhysics 표준) + TickInterval. **Actor Tick 안에 매 프레임 로직 작성 금지** — Component Tick 으로 분산. [[concepts/Component-Policies-6]]
- Replication: `bReplicates = true` → DOREPLIFETIME 매크로 + GetLifetimeReplicatedProps + OnRep_*. RPC 3 종 (Server/Client/NetMulticast).
- OnConstruction 은 Editor 의 Construction Script 와 런타임 Spawn 양쪽에서 호출 — 멱등 (idempotent) 이어야 함.
- Owner 체인: GetOwner() / SetOwner() — Replication relevancy + GetActorEyesViewPoint 등에 사용.

## 열린 질문

- [ ] Actor 라이프사이클 11 단계 의 Editor PIE vs Cooked vs Dedicated Server 차이
- [ ] NetCullDistanceSquared / NetUpdateFrequency / bAlwaysRelevant 의 실제 동작 매트릭스
