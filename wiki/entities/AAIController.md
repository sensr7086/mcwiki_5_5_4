---
type: entity
title: "AAIController"
aliases: [AAIController, AI Controller]
kind: model
sources:
  - "[[sources/ue-ai-skill]]"
tags: [ue, ai]
last_updated: 2026-05-09
---

# AAIController

## 요약

AAIModule 모듈의 [[entities/AController]] 자손. **AI 의 의지 진입점** — Pawn 소유 + BehaviorTree 시작 + Blackboard 보유. OnPossess(Pawn) 에서 Super FIRST + RunBehaviorTree(BT) 표준 패턴.

## 관계

- 부모: [[entities/AController]] → [[entities/AActor]]
- 모듈: AIModule (cross-link from GameFramework)
- 협력: [[entities/UBehaviorTree]] / [[entities/UBlackboardComponent]] / [[entities/UAIPerceptionComponent]]
- 페어: APawn (소유 대상)

## 핵심 주장

- 표준 셋업: AAIController 자손 + UPROPERTY(EditDefaultsOnly) `TObjectPtr<UBehaviorTree> DefaultBT` + OnPossess 에서 RunBehaviorTree(DefaultBT).
- Super 호출 규약: OnPossess → Super FIRST. [[raw/ue-wiki-llm/references/04_OverrideIndex.md]]
- BlackboardComponent 자동 생성: BT 의 Blackboard 자산이 BB component 자동 인스턴싱.
- AIPerceptionComponent: 별도 생성 (CreateDefaultSubobject) — Sense (Sight / Hearing / Damage) 등록.
- Pawn 의 SpawnDefaultController = GameMode 가 PostLogin / Pawn Spawn 시 자동 호출 → Pawn 의 AIControllerClass 가 정해진 경우 AAIController 자동 Spawn + Possess.
- Multiplayer: Server-side AI 가 표준 (Authority).

## 열린 질문

- [ ] Server-side AI vs Client prediction 분담
- [ ] StateTree 5.x 와 BehaviorTree 의 결정 트리
