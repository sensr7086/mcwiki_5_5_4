---
type: entity
title: "AGameModeBase"
aliases: [AGameModeBase, AGameMode, GameMode]
kind: model
sources:
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, gameframework, multiplayer]
last_updated: 2026-05-09
---

# AGameModeBase / AGameMode

## 요약

[[entities/AActor]] 자손. **서버 Authority 만 존재** — 게임 규칙 결정자. AGameModeBase (672 lines) + AGameMode (Match State 도입) + AGameStateBase + AGameState + APlayerState. DefaultPawnClass / RestartPlayer / InitGame / PostLogin / Logout 등이 진입점.

## 관계

- 부모: [[entities/AActor]]
- 형제: AGameStateBase (모든 클라이언트에 복제), APlayerState (플레이어별)
- 협력: [[entities/UWorld]] (AuthorityGameMode 멤버), [[entities/AController]] (PostLogin 으로 생성)

## 핵심 주장

- **서버 only**: Listen Server / Dedicated Server 에만 존재. Client 는 본 객체 없음. 게임 규칙 결정은 서버 권한.
- Class slots: `DefaultPawnClass` / `PlayerControllerClass` / `HUDClass` / `GameStateClass` / `PlayerStateClass` / `SpectatorClass`. 모두 TSubclassOf — Soft 로 두면 Cooked Build 에서 lazy load.
- PostLogin(NewPlayer): 새 플레이어 입장 시 호출 → SpawnDefaultPawnFor → RestartPlayer.
- [[concepts/Match-State]] (AGameMode 만): WaitingToStart / InProgress / WaitingPostMatch / LeavingMap. HandleMatchHasStarted 등의 callback.
- [[concepts/SeamlessTravel]]: GameMode 자체는 새 맵에서 새로 생성됨. 이전 GameMode 의 정보는 GameInstance 또는 PlayerState 의 SeamlessTravelTo 데이터로 인계.
- 모든 GameMode 클래스 = Class 슬롯 (TSubclassOf vs TSoftClassPtr) 결정 의무. [[concepts/Asset-Loading-Policy]]

## 열린 질문

- [ ] AGameModeBase vs AGameMode 결정 기준 (Match State 필요 여부)
- [ ] Listen Server 의 GameMode 가 클라이언트 측에서 어떻게 보이는가 (안 보임)
