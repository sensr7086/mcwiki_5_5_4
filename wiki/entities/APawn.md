---
type: entity
title: "APawn"
aliases: [APawn, Pawn]
kind: model
sources:
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, gameframework]
last_updated: 2026-05-09
---

# APawn

## 요약

[[entities/AActor]] 자손. **[[entities/AController]] 가 소유 (Possess) 가능한 Actor**. 입력 받기 + 카메라 시점 제공. 598 lines. 자손 [[entities/ACharacter]] 가 흔한 사용 (Capsule + Mesh + CharacterMovement).

## 관계

- 부모: [[entities/AActor]]
- 자손: [[entities/ACharacter]] (Capsule + SkeletalMesh + [[entities/UCharacterMovementComponent]] 페어), ASpectatorPawn, ADefaultPawn
- Possessor: [[entities/AController]] / [[entities/APlayerController]] / AAIController

## 핵심 주장

- [[concepts/Possession]]: Controller 가 `Possess(Pawn)` → Pawn 의 `PossessedBy(Controller)` 호출 → ReceiveControllerChanged 이벤트. UnPossess 로 해제. [[raw/ue-wiki-llm/skills/GameFramework/SKILL]]
- InputComponent 는 Possess 시점에 자동 SetupPlayerInputComponent 호출 → 입력 바인딩.
- bIsPlayerControlled / bIsLocallyControlled 로 player vs AI / local vs remote 분기.
- Multiplayer: Pawn 자체는 Replicated. Server 가 Authority, Client 가 Predicted. PlayerController 가 Pawn 을 Possess 한 상태가 Replicated.
- AddMovementInput / AddControllerYawInput 등은 Pawn 의 표준 입력 진입점.

## 열린 질문

- [ ] Possess 흐름 — local Player 와 dedicated server 의 차이
- [ ] ASpectatorPawn vs ADefaultPawn 사용처
