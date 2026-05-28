---
type: concept
title: "Subsystem 5종 비교 매트릭스"
aliases: [Subsystem 5 Types, Engine Subsystem, GameInstance Subsystem, World Subsystem, LocalPlayer Subsystem]
sources:
  - "[[sources/ue-subsystem-skill]]"
related_concepts:
  - "[[concepts/Global-Iterator-Avoidance]]"
tags: [ue, runtime, subsystem]
last_updated: 2026-05-09
---

# Subsystem 5종 비교

## 1. 정의 (한 줄)

[[entities/USubsystem]] 의 5 자손 — 라이프사이클 / scope / 사용처가 모두 다름.

## 2. 자세히

| 종류 | 라이프사이클 | Scope | 표준 사용 |
| -- | -- | -- | -- |
| **UEngineSubsystem** | Engine 시작 ~ 종료 | 모든 World 공유 | 글로벌 매니저 (saving / analytics / matchmaking) |
| **UEditorSubsystem** 🛠 | Editor 시작 ~ 종료 | Editor only | Editor 도구 (Asset Tools 등) |
| **UGameInstanceSubsystem** ⭐ | Game 실행 ~ 종료 (Map 전환 살아남음) | GameInstance | 영속 데이터, 세션 정보, Online Subsystem 통합 |
| **UWorldSubsystem** | Map 마다 새로 | World (Map 단위) | World-bound 매니저 (NPC list, Quest manager) |
| **ULocalPlayerSubsystem** | LocalPlayer 마다 별개 | LocalPlayer | Couch Co-op (Enhanced Input Subsystem 등) |

## 3. 변형 / 사례 / 응용

- 결정 트리 (raw skill 9 시나리오 발췌):
  - "전역 매니저, 게임 종료까지" = UEngineSubsystem
  - "Map 전환 살아남는 데이터" = UGameInstanceSubsystem
  - "이 Map 에만 의미" = UWorldSubsystem
  - "LocalPlayer 마다 별개" = ULocalPlayerSubsystem
  - "Editor 도구" = UEditorSubsystem 🛠
- UTickableWorldSubsystem 변형 = Tick 가능 (UWorldSubsystem 자손).
- UDynamicSubsystem (Engine/Editor 만) = 모듈 로드 시 자동 인스턴싱.
- 전역 이터레이터 회피 ([[concepts/Global-Iterator-Avoidance]]): TActorIterator 대신 Subsystem 안 등록 list.

## 4. 관련 entity

- [[entities/USubsystem]] · [[entities/UEngineSubsystem]] · [[entities/UGameInstance]] · [[entities/UWorld]]

## 5. 열린 질문

- [ ] LocalPlayer 동적 추가/제거 시 Subsystem 동작
- [ ] WorldSubsystem 의 SeamlessTravel 인계 패턴
