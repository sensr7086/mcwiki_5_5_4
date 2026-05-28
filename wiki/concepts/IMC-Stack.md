---
type: concept
title: "IMC Stack (Priority-based)"
aliases: [IMC Stack, MappingContext Stack, Input Priority]
sources:
  - "[[sources/ue-input-skill]]"
related_concepts:
  - "[[concepts/Enhanced-Input-Standard]]"
tags: [ue, input, plugin]
last_updated: 2026-05-09
---

# IMC Stack

## 1. 정의 (한 줄)

[[entities/UEnhancedInputLocalPlayerSubsystem]] 의 [[entities/UInputMappingContext]] stack — Priority 기반 dynamic switching. AddMappingContext(IMC, Priority) / RemoveMappingContext.

## 2. 자세히

7 단계 priority 권장:
| Priority | 용도 |
| -- | -- |
| 0 | DefaultGame (기본 캐릭터 입력) |
| 1 | Vehicle (탈것 입력 — 캐릭터 입력 차단) |
| 2 | Aim (조준 — 추가 입력) |
| 3 | Menu (메뉴 — 캐릭터 차단) |
| 4 | Cinematic (시네마틱 — 모두 차단) |
| 5 | Debug |
| 6 | Modal (예: 이름 입력 textbox) |

상위 priority 의 IMC 가 같은 Action 을 매핑하면 하위 무시. bConsumeInput 으로 명시적 차단.

## 3. 변형 / 사례 / 응용

- 게임 시작 = AddMappingContext(IMC_DefaultGame, 0).
- 차량 탑승 = AddMappingContext(IMC_Vehicle, 1) — Walk Action 의 W/A/S/D 가 차단됨.
- 메뉴 열기 = AddMappingContext(IMC_Menu, 3) + InputMode UI Only.
- 메뉴 닫기 = RemoveMappingContext(IMC_Menu).

## 4. 관련 entity

- [[entities/UInputMappingContext]] · [[entities/UEnhancedInputLocalPlayerSubsystem]]

## 5. 열린 질문

- [ ] bConsumeInput 의 정확한 차단 동작
- [ ] Cinematic / Modal 의 구현 패턴
