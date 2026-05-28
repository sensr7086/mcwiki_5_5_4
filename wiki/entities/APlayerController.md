---
type: entity
title: "APlayerController"
aliases: [APlayerController, PlayerController, PC]
kind: model
sources:
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, gameframework, input]
last_updated: 2026-05-09
---

# APlayerController

## 요약

[[entities/AController]] 자손. **인간 플레이어의 입력 + 카메라 + 네트워크 진입점**. 2,377 lines. PlayerCameraManager 보유 + InputMode (UI/Game) + RPC 발화점 + ULocalPlayer 와 페어.

## 관계

- 부모: [[entities/AController]] → [[entities/AActor]]
- 페어: ULocalPlayer (LocalPlayer 의 LocalPlayerController), APlayerCameraManager
- Subsystem: ULocalPlayerSubsystem (PlayerController 가 아니라 LocalPlayer 에 attached)

## 핵심 주장

- 클라이언트와 서버 양쪽에 존재 (NetOwner). RPC 의 표준 발화점 — Server RPC / Client RPC / NetMulticast.
- 입력 처리: SetupInputComponent → BindAction (Legacy) 또는 EnhancedInputComponent + IMC stack (5.x 표준).
- InputMode 전환: SetInputModeGameOnly / SetInputModeUIOnly / SetInputModeGameAndUI. 마우스 cursor / focus 결정.
- PlayerCameraManager: 카메라 효과 / View 결정. ClientSetCameraFade / ClientSetCameraMode.
- HUD / Widget 진입점: ClientSetHUD / Possess 시 자동 HUD 생성.
- SeamlessTravel: 맵 전환 시 PlayerController 도 새로 생성됨 ([[concepts/SeamlessTravel]] §4 참조).

## 열린 질문

- [ ] EnhancedInputComponent 5.x 와 Legacy InputComponent 의 마이그레이션 경로
- [ ] Listen Server 의 PlayerController 동작 (Client + Server 동시)
