---
type: source
title: "UE 5.7.4 AI Module — Main SKILL"
slug: ue-ai-skill
source_path: raw/ue-wiki-llm/skills/AI/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/AAIController]]"
  - "[[entities/UBehaviorTree]]"
  - "[[entities/UBlackboardComponent]]"
  - "[[entities/UNavigationSystemV1]]"
  - "[[entities/UAIPerceptionComponent]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, ai, plugin]
---

# UE 5.7.4 AI Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/AI/SKILL.md]]
> Kind: text · Date: 2026-05-09 · Ingested: 2026-05-09

## 1. Summary

게임 AI 의 4 대 축: **Controller / BT / Nav / Perception**. [[entities/AAIController]] (AAIModule 자손 of [[entities/AController]]) + [[entities/UBehaviorTree]] (Task/Service/Decorator) + [[entities/UBlackboardComponent]] (BT 의 메모리) + EQS (UEnvQuery, 환경 쿼리) + Navigation ([[entities/UNavigationSystemV1]] / RecastNavMesh / UCrowdManager) + [[entities/UAIPerceptionComponent]] (Sight/Hearing/Damage). 다수 NPC 5중 최적화 + Significance 통합.

## 2. Key claims

- [[entities/AAIController]] = AAIModule 의 [[entities/AController]] 자손. OnPossess(Pawn) 에서 Super FIRST + BT 시작.
- BehaviorTree = Task (UBTTaskNode 자손, 행동 단위) + Service (UBTService 자손, 주기적 갱신) + Decorator (UBTDecorator 자손, 조건). [[entities/UBlackboardComponent]] 가 BT 의 공유 메모리.
- EQS = `UEnvQuery` + Generator (어디 후보 생성) + Test (각 후보 점수). 시야/거리/노드 가중 평가.
- Navigation = [[entities/UNavigationSystemV1]] (싱글톤) + RecastNavMesh (자동 빌드 또는 명시적) + Crowd (UCrowdManager + RVO). MoveTo / FindPath API.
- Perception = [[entities/UAIPerceptionComponent]] + Sense (UAISenseConfig_Sight / Hearing / Damage / Touch / Team / Prediction). OnTargetPerceptionUpdated delegate.
- 다수 NPC = [[concepts/Asset-Optimization-Policy]] 5중 누적 + Significance 등록.

## 3. Quotations

> "본 sub-skill 은 게임 AI 의 4대 축 (Controller / BT / Nav / Perception). 다수 NPC 환경 최적화는 Animation/Optimization + Significance 페어."

## 4. Open questions / next sources

- [ ] BT vs StateTree 5.x 결정 트리
- [ ] EQS Generator/Test 의 비용 분석
