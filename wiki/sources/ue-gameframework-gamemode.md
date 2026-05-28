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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 3 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/GameFramework/references/GameMode.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/GameFramework/references/GameMode.md`
