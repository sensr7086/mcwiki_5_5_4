---
type: source
title: "UE 5.7.4 GameFramework Module — Main SKILL"
slug: ue-gameframework-skill
source_path: raw/ue-wiki-llm/skills/GameFramework/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/AActor]]"
  - "[[entities/APawn]]"
  - "[[entities/ACharacter]]"
  - "[[entities/AController]]"
  - "[[entities/APlayerController]]"
  - "[[entities/AGameModeBase]]"
  - "[[entities/UGameInstance]]"
  - "[[entities/UWorld]]"
related_concepts:
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/Possession]]"
  - "[[concepts/Match-State]]"
  - "[[concepts/SeamlessTravel]]"
  - "[[concepts/Tick-Group]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, gameframework]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE 5.7.4 GameFramework Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/GameFramework/SKILL.md]]

## 1. Summary

Actor 게임 흐름의 베이스 — Actor / Pawn / Character / Controller / GameMode / GameInstance / World. SpawnActor 히칭 회피 + Cooked 검증 의무.

## 2. Sub-skills (6 — Phase 4C 완료)

- [[sources/ue-gameframework-actor]] — AActor 라이프사이클 11 단계 + 6 대 정책 + SpawnActorDeferred
- [[sources/ue-gameframework-pawncharacter]] — APawn + ACharacter + 최적화 10 종 + AI vs Player 매트릭스
- [[sources/ue-gameframework-controller]] — AController + APlayerController + AAIController + Possession + Camera
- [[sources/ue-gameframework-gamemode]] — AGameModeBase + Match State + AGameStateBase + APlayerState + SeamlessTravel
- [[sources/ue-gameframework-gameinstance]] — UGameInstance 영속 세션 + Subsystem + AssetManager 진입점
- [[sources/ue-gameframework-world]] — UWorld + ULevel + Tick Group 8 종 + Streaming + WorldSubsystem

## 3. Open questions

- [ ] [[concepts/SeamlessTravel]] 의 GameInstance / PlayerController / GameMode 인계 정확한 절차
- [ ] AAIController 와 AIModule 의 cross-link
- [ ] WorldPartition 5.x 가 ULevel 라이프사이클에 미치는 영향
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에만): 5
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `| 6 | [`World`](./World/SKILL.md) | `skills/GameFramework/references/World.md` | → | 1 | [`Actor`](./Actor/SKILL.md) | `skills/GameFramework/references/Actor.md` |`

**5.5.4 에만 (5.7.4 에 없음)**:
- `| 2 | [`PawnCharacter`](./PawnCharacter/SKILL.md) | `skills/GameFramework/references/PawnCharacter.md` | APawn 588 + ACh`
- `| 3 | [`Controller`](./Controller/SKILL.md) | `skills/GameFramework/references/Controller.md` | AController 420 + APlaye`
- `| 4 | [`GameMode`](./GameMode/SKILL.md) | `skills/GameFramework/references/GameMode.md` | AGameModeBase 671 + AGameMode `
- `| 5 | [`GameInstance`](./GameInstance/SKILL.md) | `skills/GameFramework/references/GameInstance.md` | UGameInstance 676 `

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/GameFramework/SKILL.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/GameFramework/SKILL.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
