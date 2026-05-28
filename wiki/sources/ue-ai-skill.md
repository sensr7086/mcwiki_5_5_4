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
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-content-shift** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 작은 의미 변경 + 큰 cosmetic. 시그니처 0 / 추가 3 / 제거 0 / 수치 0 / 기타 1.

**주요 변경 sample**:
- `---`
- ``
- `# AI — UE 5.5.4 AI 시스템 / Behavior Tree / Navigation`

**결정**: 🟡 본질 안정, 일부 표현 갱신 필요 가능. 후속 본문 정합 확인 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/AI/SKILL.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/AI/SKILL.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
