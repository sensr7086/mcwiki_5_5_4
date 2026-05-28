---
type: entity
title: "AGameStateBase / AGameState / APlayerState"
aliases: [AGameStateBase, AGameState, APlayerState, GameState]
kind: model
sources:
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, gameframework, multiplayer]
last_updated: 2026-05-09
---

# AGameStateBase / AGameState / APlayerState

## 요약

[[entities/AActor]] 자손. **모든 클라이언트에 복제** — 게임의 *공유 상태* 표현. AGameStateBase (베이스) + AGameState (Match State 추가) + APlayerState (플레이어별, [[entities/AGameModeBase]] 의 PostLogin 으로 생성).

## 관계

- 부모: [[entities/AActor]]
- 형제: [[entities/AGameModeBase]] (서버 only) — GameState 는 Server 가 관리하고 모든 Client 에 복제
- PlayerState: 각 플레이어마다 하나 (점수 / 팀 / 상태)

## 핵심 주장

- **AGameStateBase**: 베이스 — 모든 클라이언트 복제. PlayerArray (모든 플레이어의 PlayerState) 보유. ServerWorldTimeSeconds 동기화.
- **AGameState** (자손): [[concepts/Match-State]] 5단계 추가. HasMatchStarted / HasMatchEnded.
- **APlayerState**: 플레이어 1명 = 1 인스턴스. SeamlessTravel 시 일부 데이터 인계 (`bIsInactive` flag 로 transition 동안 유지).
- **표준 사용**: 점수판 / 팀 정보 / 라운드 진행 / 글로벌 상태 = AGameState. 개인 점수 / 닉네임 / 캐릭터 클래스 = APlayerState.
- Class slot: `AGameModeBase::GameStateClass` / `PlayerStateClass` 로 결정. TSubclassOf — Hard 또는 Soft.

## 열린 질문

- [ ] PlayerState 의 SeamlessTravel 인계 표준 패턴
- [ ] AGameStateBase vs AGameState 결정 (Match State 필요 여부)
