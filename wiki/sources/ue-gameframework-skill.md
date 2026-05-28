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
