---
type: entity
title: "UEngineSubsystem / UEditorSubsystem"
aliases: [UEngineSubsystem, UEditorSubsystem, UGameInstanceSubsystem, UWorldSubsystem, ULocalPlayerSubsystem, UTickableWorldSubsystem]
kind: model
sources:
  - "[[sources/ue-subsystem-skill]]"
tags: [ue, runtime, subsystem]
last_updated: 2026-05-09
---

# 5종 Subsystem 자손

## 요약

[[entities/USubsystem]] 의 5 종 자손 — 라이프사이클이 다름. UEngineSubsystem (Engine) / UEditorSubsystem 🛠 (Editor) / UGameInstanceSubsystem (GameInstance) / UWorldSubsystem (World) / ULocalPlayerSubsystem (LocalPlayer).

## 관계

- 부모: [[entities/USubsystem]] (또는 UDynamicSubsystem 자손)
- 호스트:
  - UEngineSubsystem → UEngine
  - UEditorSubsystem → UEditorEngine 🛠
  - UGameInstanceSubsystem → [[entities/UGameInstance]]
  - UWorldSubsystem → [[entities/UWorld]] (Map 마다)
  - ULocalPlayerSubsystem → ULocalPlayer

## 핵심 주장

- **UEngineSubsystem** — Engine 라이프사이클 (게임 실행 ~ 종료, 모든 World 공유). UDynamicSubsystem 자손 — 모듈 로드 시 자동.
- **UEditorSubsystem 🛠** — Editor 라이프사이클. Editor 빌드만 (`#if WITH_EDITOR`). 표준 Editor 도구 (Asset Tools 등) 이 사용.
- **UGameInstanceSubsystem** ⭐ — Map 전환을 살아남음. SeamlessTravel 동안 유지. 영속 데이터 / 세션 정보 표준 위치.
- **UWorldSubsystem** — Map 마다 새로 생성. World-bound 데이터 (현재 Map 의 NPC list 등). UTickableWorldSubsystem 변형 = Tick 가능.
- **ULocalPlayerSubsystem** — Couch Co-op (LocalPlayer 마다 별개 인스턴스). UEnhancedInputLocalPlayerSubsystem 등.

## 열린 질문

- [ ] 결정 트리 9 시나리오 (자세한 raw skill)
- [ ] UDynamicSubsystem vs 일반 Subsystem 차이
