---
type: entity
title: "UActorComponent"
aliases: [UActorComponent, ActorComponent]
kind: model
sources:
  - "[[sources/ue-components-skill]]"
tags: [ue, runtime, components]
last_updated: 2026-05-09
---

# UActorComponent

## 요약

[[entities/UObject]] 자손 + [[entities/AActor]] 의 부속. **로직 전용** 컴포넌트의 베이스 — 트랜스폼 없음. Tick / Replication / 라이프사이클 (BeginPlay/EndPlay) 진입점. 자손 [[entities/USceneComponent]] 부터 트랜스폼 추가.

## 관계

- 부모: [[entities/UObject]]
- 자손: [[entities/USceneComponent]] (트랜스폼 추가) → [[entities/UPrimitiveComponent]] (콜리전+렌더+물리)
- 호스트: [[entities/AActor]] (Owner)
- 페어 자산: 없음 (로직 전용)

## 핵심 주장

- 라이프사이클 표준 4 단계: OnRegister → InitializeComponent → BeginPlay → EndPlay → UninitializeComponent → OnUnregister. [[concepts/Component-Lifecycle]]
- Super 호출 규약: BeginPlay → Super FIRST, EndPlay → Super LAST. 위반 시 Component 등록 해제가 깨짐. [[raw/ue-wiki-llm/references/04_OverrideIndex.md]]
- 6 대 정책 의무 [[concepts/Component-Policies-6]]: NewObject 표준 / GC 방어 (UPROPERTY + TObjectPtr) / GetOwner 캐싱 / PrimaryComponentTick / CDO. [[raw/ue-wiki-llm/references/10_ComponentPolicies.md]]
- Tick: `PrimaryComponentTick.bCanEverTick = false` 가 기본 (생성자) + 필요 시 `TickInterval` (0.05~1s) 우선 + 매 프레임 = 마지막 수단. [[concepts/Profiling-Scope-Rule]]
- Replication: `SetIsReplicatedByDefault(true)` 또는 owning Actor 의 `bReplicates`. UPROPERTY(Replicated) + GetLifetimeReplicatedProps.

## 열린 질문

- [ ] InitializeComponent vs BeginPlay 호출 순서 — Editor 와 Cooked 차이
- [ ] Component 의 Replication 이 Actor 의 Replication 과 어떻게 상호작용
