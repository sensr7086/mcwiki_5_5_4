---
type: concept
title: "Possession (Controller ↔ Pawn)"
aliases: [Possess, UnPossess, PossessedBy]
sources:
  - "[[sources/ue-gameframework-skill]]"
related_concepts:
  - "[[concepts/SeamlessTravel]]"
tags: [ue, runtime, gameframework]
last_updated: 2026-05-09
---

# Possession (Controller ↔ Pawn)

## 1. 정의 (한 줄)

[[entities/AController]] 가 [[entities/APawn]] 을 *소유* 하는 흐름 — Controller->Possess(Pawn) → Pawn->PossessedBy(Controller) → ReceiveControllerChanged. 입력 + 카메라 + AI 의지의 진입점.

## 2. 자세히

```
Controller->Possess(Pawn)
    │
    ├─▶ Pawn->PossessedBy(Controller)         (Pawn 측 callback)
    ├─▶ Pawn->SetOwner(Controller)
    ├─▶ Pawn->ReceiveControllerChanged        (BP event)
    ├─▶ Controller->OnPossess(Pawn)           (Controller 측 BP event)
    ├─▶ APlayerController 의 경우 SetupInputComponent → BindAction
    └─▶ ControlRotation 갱신 시작

Controller->UnPossess()
    │
    ├─▶ Pawn->UnPossessed
    ├─▶ Pawn->SetOwner(nullptr)
    ├─▶ Controller->OnUnPossess
    └─▶ InputComponent 해제
```

## 3. 변형 / 사례 / 응용

- **Listen Server**: 서버 측 Player 의 Possess 는 Server Authoritative. Client 측 Possess 는 Server 의 Replication 결과.
- **AI Controller**: AAIController 의 Possess 는 SpawnDefaultController 또는 명시적 Possess. BehaviorTree / Blackboard 시작.
- **Possess 시점에 Pawn 의 InputComponent 자동 SetupPlayerInputComponent** — 입력 바인딩 초기화의 표준 위치.
- **bIsPlayerControlled / bIsLocallyControlled** 분기 — Possess 후 사용 가능.

## 4. 관련 entity

- [[entities/AController]] · [[entities/APlayerController]]
- [[entities/APawn]] · [[entities/ACharacter]]

## 5. 열린 질문

- [ ] OnPossess vs PossessedBy 호출 순서 (Pawn 이 먼저? Controller 가 먼저?)
- [ ] Multiplayer 의 SeamlessTravel 시 Possess 재실행 흐름
