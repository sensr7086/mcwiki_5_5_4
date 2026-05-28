---
type: entity
title: "UInputMappingContext"
aliases: [UInputMappingContext, IMC, MappingContext]
kind: model
sources:
  - "[[sources/ue-input-skill]]"
tags: [ue, input, plugin]
last_updated: 2026-05-09
---

# UInputMappingContext

## 요약

Enhanced Input 의 자산 — [[entities/UInputAction]] 과 실제 Key ([[entities/FKey]]) 의 매핑. IMC stack (Priority 기반) 으로 동적 전환 — 메뉴 모드 / 차량 모드 / 점수 모드 등 컨텍스트 분기. [[entities/UEnhancedInputLocalPlayerSubsystem]] 가 stack 관리.

## 관계

- 부모: [[entities/UObject]]
- 페어 자산: [[entities/UInputAction]] 다수
- 호스트: [[entities/UEnhancedInputLocalPlayerSubsystem]] (stack 의 entry)

## 핵심 주장

- IMC ↔ Action ↔ Key 3 단 매핑: IMC 가 (Action, Key, [Modifiers], [Triggers]) 튜플들의 컬렉션. 한 Action 이 여러 Key 매핑 가능 (예: Move = WASD + LeftStick).
- Stack 전환: AddMappingContext(IMC, Priority) / RemoveMappingContext(IMC). 상위 priority 가 우선.
- 7 단계 priority 권장: 0=DefaultGame, 1=Vehicle, 2=Aim, 3=Menu, 4=Cinematic, 5=Debug, 6=Modal.
- Couch Co-op: LocalPlayer 마다 별개 stack — UEnhancedInputLocalPlayerSubsystem 인스턴스 별.
- 자산 정책: 작은 자산. Hard Reference OK. Constructor 안 BP 지정 표준.

## 열린 질문

- [ ] Modal IMC 패턴 (다른 IMC 입력 차단)
- [ ] MappingContext 의 platform-specific 변형
