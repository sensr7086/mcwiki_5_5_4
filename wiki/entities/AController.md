---
type: entity
title: "AController"
aliases: [AController, Controller]
kind: model
sources:
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, gameframework]
last_updated: 2026-05-09
---

# AController

## 요약

[[entities/AActor]] 자손. **[[entities/APawn]] 을 소유하는 비-시각 Actor** — 입력/AI 의 의지 표현. 420 lines. 자손 [[entities/APlayerController]] (인간 입력) + AAIController (AI 모듈) 양분.

## 관계

- 부모: [[entities/AActor]]
- 자손: [[entities/APlayerController]] / AAIController (AIModule cross-link)
- 소유 대상: [[entities/APawn]] / [[entities/ACharacter]]

## 핵심 주장

- [[concepts/Possession]] 진입점: Possess(Pawn) → Pawn 의 PossessedBy 호출 + Controller 의 ControlRotation 갱신. UnPossess 로 해제.
- ControlRotation: Pawn 의 시점 (마우스 / AI 의 LookAt). Pawn 의 GetControlRotation() 으로 접근.
- bPossessNonPlayerOnly / bAttachToPawn / bAutoManageActiveCameraTarget 등의 옵션.
- Multiplayer: Controller 자체는 Server 와 그 OwningPlayer Client 에만 존재 (다른 Client 에는 X). PlayerController = NetOwner.
- AAIController 는 BehaviorTree / Blackboard / EQS 와 통합 — AIModule 의존 (cross-link).

## 열린 질문

- [ ] Server-side AI 와 Client-side prediction 의 책임 분담
- [ ] OnPossess/OnUnPossess 이벤트의 호출 순서 (Pawn 측 PossessedBy 와 비교)
