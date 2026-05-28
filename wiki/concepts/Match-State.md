---
type: concept
title: "Match State (AGameMode)"
aliases: [Match State, MatchState, WaitingToStart, InProgress]
sources:
  - "[[sources/ue-gameframework-skill]]"
related_concepts:
  - "[[concepts/SeamlessTravel]]"
tags: [ue, runtime, gameframework, multiplayer]
last_updated: 2026-05-09
---

# Match State (AGameMode)

## 1. 정의 (한 줄)

AGameMode (AGameModeBase 와 별개) 의 5 단계 상태 머신 — WaitingToStart / InProgress / WaitingPostMatch / LeavingMap / Aborted. HandleMatchHasStarted / HandleMatchHasEnded 등의 callback 으로 분기.

## 2. 자세히

| State | 의미 | 진입 callback |
| -- | -- | -- |
| WaitingToStart | 모든 player 입장 대기 | InitGame |
| InProgress | 게임 진행 중 | HandleMatchHasStarted |
| WaitingPostMatch | 게임 종료 후 정리 | HandleMatchHasEnded |
| LeavingMap | 다음 맵으로 [[concepts/SeamlessTravel]] | HandleLeavingMap |
| Aborted | 비정상 종료 | HandleMatchAborted |

`SetMatchState(Name)` 으로 강제 전환. `HasMatchStarted()` / `HasMatchEnded()` 로 분기.

## 3. 변형 / 사례 / 응용

- **AGameModeBase 는 Match State 없음** — 단순 Lobby / Main Menu 등.
- **AGameMode** 만 Match State 보유. 멀티플레이어 라운드 기반 게임 표준.
- **Replication 표준**: AGameStateBase 의 MatchState 가 Replicated → Client 에서도 상태 인지.
- **ReadyToStartMatch / ReadyToEndMatch override**: 라운드 시작/종료 조건 커스터마이징.

## 4. 관련 entity

- [[entities/AGameModeBase]] (자손 AGameMode)

## 5. 열린 질문

- [ ] Match State 와 [[concepts/SeamlessTravel]] 의 통합 — LeavingMap 진입 시점
- [ ] Custom Match State 추가 패턴
