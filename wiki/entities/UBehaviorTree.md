---
type: entity
title: "UBehaviorTree / UBTTaskNode / UBTService / UBTDecorator"
aliases: [UBehaviorTree, BehaviorTree, BT, UBTTaskNode, UBTService, UBTDecorator]
kind: model
sources:
  - "[[sources/ue-ai-skill]]"
tags: [ue, ai, asset]
last_updated: 2026-05-09
---

# UBehaviorTree

## 요약

[[entities/UObject]] 자손 (자산). AI 의사결정 트리. Task (UBTTaskNode 자손, 행동 단위) + Service (UBTService 자손, 주기적 갱신) + Decorator (UBTDecorator 자손, 조건 분기). [[entities/UBlackboardComponent]] 가 BT 의 공유 메모리.

## 관계

- 부모: [[entities/UObject]]
- 호스트: [[entities/AAIController]]
- 페어: [[entities/UBlackboardComponent]] (자체 Blackboard 자산 보유)

## 핵심 주장

- Task 자손: BTT_MoveTo / BTT_Wait / BTT_PlayAnimation / Custom Task. Tick 기반 (각 frame 진행).
- Service 자손: BTS_DefaultFocus / Custom — 주기적 (TickInterval) Blackboard 갱신.
- Decorator 자손: BTD_Blackboard / BTD_Loop / BTD_Cooldown / Custom — 조건 평가 (실행 / 차단).
- Selector / Sequence / Composite — 트리 흐름 제어.
- 라이프사이클: RunBehaviorTree(BT) → BT::OnInitialize → Tick (Task 진행) → Task 종료 → 다음 Task.
- 5.x StateTree: BT 의 후속 — 더 일반화된 상태 머신 + 비동기 / 위계적. BT 의 사용처에 따라 결정.

## 열린 질문

- [ ] Custom Task 작성 시 EBTNodeResult 결과 처리 패턴
- [ ] StateTree vs BT 결정 트리
