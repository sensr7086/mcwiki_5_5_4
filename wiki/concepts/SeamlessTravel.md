---
type: concept
title: "Seamless Travel"
aliases: [SeamlessTravel, ServerTravel]
sources:
  - "[[sources/ue-gameframework-skill]]"
related_concepts:
  - "[[concepts/Match-State]]"
  - "[[concepts/Possession]]"
tags: [ue, runtime, gameframework, multiplayer]
last_updated: 2026-05-09
---

# Seamless Travel

## 1. 정의 (한 줄)

맵 전환 (UWorld 교체) 의 *플레이어 연결 유지* 모드 — `UWorld->ServerTravel(Map, true /* bAbsolute */, false /* bShouldSkipGameNotify */)` 또는 `bUseSeamlessTravel = true` 로 활성. UGameInstance / PlayerState 의 일부 데이터 인계 가능.

## 2. 자세히

흐름:
```
ServerTravel("Map2", true, true)  /* bSeamless */
  ├─▶ TransitionMap 으로 1차 이동 (네트워크 연결 유지)
  ├─▶ AGameMode->StartTravelling
  ├─▶ PreparePlayerForSeamlessTravel — PlayerState / PlayerController 인계 준비
  ├─▶ Map2 로 2차 이동
  ├─▶ AGameMode (Map2) 새로 생성
  ├─▶ PostSeamlessTravel — 새 GameMode + 인계된 PlayerState
  └─▶ PlayerController 새로 생성 + Possess 재실행
```

## 3. 변형 / 사례 / 응용

- **GameInstance 는 살아남음** — [[entities/UGameInstance]] / GameInstanceSubsystem 은 모든 맵 전환을 살아남는 유일한 World-bound 외 객체. SeamlessTravel 데이터 인계의 자연스러운 위치.
- **PlayerState 인계**: GetSeamlessTravelActorList 로 인계 대상 등록.
- **WorldSubsystem 은 새로 생성** — Map 마다 다른 Subsystem 인스턴스.
- **Listen Server vs Dedicated**: 둘 다 SeamlessTravel 지원. 비-Seamless travel 은 클라이언트 disconnect → reconnect.

## 4. 관련 entity

- [[entities/UWorld]] · [[entities/UGameInstance]] · [[entities/AGameModeBase]] · [[entities/APlayerController]]

## 5. 열린 질문

- [ ] TransitionMap 의 standard 셋업
- [ ] SeamlessTravel 시 PlayerState 의 정확한 인계 데이터 (스코어 / 팀 등)
