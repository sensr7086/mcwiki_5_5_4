---
type: entity
title: "UEnhancedInputLocalPlayerSubsystem"
aliases: [UEnhancedInputLocalPlayerSubsystem, EnhancedInputSubsystem]
kind: model
sources:
  - "[[sources/ue-input-skill]]"
  - "[[sources/ue-subsystem-skill]]"
tags: [ue, input, plugin, subsystem]
last_updated: 2026-05-09
---

# UEnhancedInputLocalPlayerSubsystem

## 요약

ULocalPlayerSubsystem 자손 — LocalPlayer 마다 1 인스턴스. Enhanced Input 의 stack 관리 + UEnhancedPlayerInput (이전 처리기) + UEnhancedInputComponent 등록.

## 관계

- 부모: ULocalPlayerSubsystem → [[entities/USubsystem]]
- 페어: ULocalPlayer (Owner)
- 협력: [[entities/UInputMappingContext]] (stack), [[entities/UEnhancedInputComponent]]

## 핵심 주장

- IMC stack API: AddMappingContext(IMC, Priority, Options) / RemoveMappingContext / ClearAllMappings.
- Couch Co-op: 각 LocalPlayer 마다 별개 인스턴스 → 별개 IMC stack → 별개 입력 분기. PIE 다중 클라이언트도 동일.
- 라이프사이클: LocalPlayer 생성 시 자동 Initialize (PlayerController possess 시 또는 그 이전).
- ShouldCreateSubsystem(Outer) override: EnhancedInput Plugin 활성 시만.

## 열린 질문

- [ ] LocalPlayer 의 동적 추가/제거 (Couch Co-op 새 플레이어 입장)
- [ ] PlayerController possession 변경 시 Subsystem 의 동작
