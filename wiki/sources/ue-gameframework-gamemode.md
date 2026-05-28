---
type: source
title: "UE GameFramework — GameMode sub-skill"
slug: ue-gameframework-gamemode
source_path: raw/ue-wiki-llm/skills/GameFramework/references/GameMode.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/AGameModeBase]]"
  - "[[entities/AGameStateBase]]"
related_concepts:
  - "[[concepts/Match-State]]"
  - "[[concepts/SeamlessTravel]]"
tags: [ue, runtime, gameframework, multiplayer]
---

# UE GameFramework — GameMode sub-skill

> Source: [[raw/ue-wiki-llm/skills/GameFramework/references/GameMode.md]]
> Parent: [[sources/ue-gameframework-skill]]

## 1. Summary

[[entities/AGameModeBase]] (672) + AGameMode ([[concepts/Match-State]] 5 종) + [[entities/AGameStateBase]] (모든 client 복제) + AGameState + APlayerState (플레이어별). Multiplayer 게임 흐름의 Server Authority.

## 2. Key claims

- AGameModeBase = 서버 only. Class slots: DefaultPawnClass / PlayerControllerClass / HUDClass / GameStateClass / PlayerStateClass / SpectatorClass.
- AGameMode = AGameModeBase 자손 + [[concepts/Match-State]] (WaitingToStart / InProgress / WaitingPostMatch / LeavingMap / Aborted).
- PostLogin(NewPlayer) — 새 플레이어 입장 → SpawnDefaultPawnFor → RestartPlayer.
- HandleMatchHasStarted / HandleMatchHasEnded / ReadyToStartMatch / ReadyToEndMatch — Match State callback.
- AGameStateBase = 모든 client 복제. PlayerArray (모든 PlayerState) + ServerWorldTimeSeconds.
- APlayerState = 플레이어별 1 인스턴스. 점수 / 닉네임 / 팀 / 캐릭터 클래스.
- [[concepts/SeamlessTravel]] = 맵 전환 살아남는 PlayerState 일부 + GameInstance 영속.

## 3. Open questions

- [ ] AGameModeBase vs AGameMode 결정 (Match State 필요 여부)
- [ ] PlayerState 의 SeamlessTravel 인계 정확한 데이터
