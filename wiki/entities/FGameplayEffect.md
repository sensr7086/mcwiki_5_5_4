---
type: entity
title: "FGameplayEffect / UGameplayEffect"
aliases: [FGameplayEffect, UGameplayEffect, GameplayEffect, GE]
kind: model
sources:
  - "[[sources/ue-gas-skill]]"
tags: [ue, plugin, gas]
last_updated: 2026-05-09
---

# UGameplayEffect

## 요약

GAS Plugin 의 효과 (버프 / 디버프 / 데미지) 베이스. [[entities/UObject]] 자손. [[entities/UAttributeSet]] 의 속성 변경 + Tag 부여 + GameplayCue 발화. Duration 3 종 (Instant / HasDuration / Infinite).

## 관계

- 부모: [[entities/UObject]]
- 협력: [[entities/UAbilitySystemComponent]] (적용), [[entities/UAttributeSet]] (속성 변경), [[entities/FGameplayTag]] (부여), GameplayCueManager (Cosmetic 발화)

## 핵심 주장

- Duration 3종: Instant (즉시 적용 후 사라짐 — 데미지) / HasDuration (시간 지속 — 버프) / Infinite (수동 제거 — 토글).
- Modifiers: Attribute 변경 — Add / Multiply / Divide / Override. Magnitude = ScalableFloat (시간 / 레벨 곡선) / SetByCaller (동적) / AttributeBased (다른 속성 기반) / CustomCalculation.
- Periodic: HasDuration 효과의 주기적 발동 (예: Damage over Time = 매 1초 데미지).
- Granted Tags / Granted Abilities — 효과 적용 동안 Tag 부여 / 어빌리티 부여.
- Removal Tags — 다른 효과로 제거 가능 표시.
- GameplayCue 통합: 효과 적용 시점에 Cosmetic (VFX/SFX) 발화.
- Stacking: StackingType + StackLimitCount + StackDurationRefreshPolicy.

## 열린 질문

- [ ] SetByCaller 의 표준 패턴 (어빌리티가 동적 magnitude 결정)
- [ ] Stack 의 Refresh Policy 결정 트리
