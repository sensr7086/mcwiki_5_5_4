---
type: entity
title: "UBlackboardComponent / UBlackboardData"
aliases: [UBlackboardComponent, Blackboard, BB]
kind: model
sources:
  - "[[sources/ue-ai-skill]]"
tags: [ue, ai, components]
last_updated: 2026-05-09
---

# UBlackboardComponent

## 요약

[[entities/UActorComponent]] 자손. **BehaviorTree 의 공유 메모리** — Key / Value 쌍으로 AI 의 인지 상태 저장. UBlackboardData (자산) 가 key 정의. BT 의 Decorator / Service / Task 가 모두 BB key 로 통신.

## 관계

- 부모: [[entities/UActorComponent]]
- 페어 자산: UBlackboardData
- 호스트: [[entities/AAIController]]

## 핵심 주장

- BB Key 타입: Bool / Int / Float / String / Name / Vector / Rotator / Object (UObject) / Class / Enum.
- API: `BB->SetValueAsObject("TargetActor", Actor)` / `BB->GetValueAsObject("TargetActor")`. C++ + BP 양쪽.
- Decorator BTD_Blackboard: BB key 의 값 비교 → 조건 분기.
- 자동 생성: AAIController->RunBehaviorTree(BT) 시 BT 의 Blackboard 자산이 BB component 자동 인스턴싱.
- Multiplayer: Server-side AI — BB 도 server only. 복제 안 됨 (PerceptionComponent 가 client 측 sense 결과 복제).

## 열린 질문

- [ ] BB Key Set 알림 (OnValueChanged delegate) 패턴
- [ ] Blackboard 의 dynamic key 추가
