---
type: entity
title: "UAttributeSet"
aliases: [UAttributeSet, AttributeSet, FGameplayAttributeData]
kind: model
sources:
  - "[[sources/ue-gas-skill]]"
tags: [ue, plugin, gas]
last_updated: 2026-05-09
---

# UAttributeSet

## 요약

GAS Plugin 의 속성 베이스. [[entities/UObject]] 자손. [[entities/UAbilitySystemComponent]] 의 SubObject. 게임의 numeric attributes (Health / Mana / Stamina / AttackPower / Defense 등) 정의. FGameplayAttributeData 가 BaseValue / CurrentValue 보유.

## 관계

- 부모: [[entities/UObject]]
- 호스트: [[entities/UAbilitySystemComponent]] (자동 SubObject)
- 협력: [[entities/FGameplayEffect]] (속성 변경)

## 핵심 주장

- BaseValue (영구) vs CurrentValue (임시 + Effect 누적). Effect 가 expire 시 CurrentValue → BaseValue 복귀.
- 매크로 패턴:
  - `ATTRIBUTE_ACCESSORS(UMyAttributeSet, Health)` — Getter/Setter/Initter 자동 생성.
  - `UPROPERTY(BlueprintReadOnly, ReplicatedUsing=OnRep_Health)` — 복제 + BP 노출.
- PreAttributeChange / PreAttributeBaseChange — Clamp 등 적용 시점.
- PostGameplayEffectExecute — Effect 실행 후 후처리 (예: Health 0 이면 Die).
- SetByCaller 모드 (FGameplayEffectModifierMagnitude::ScalableFloat) — 동적 magnitude.
- 6 대 정책의 GC 방어: ASC 의 SubObject — UPROPERTY 자동 보호.

## 열린 질문

- [ ] Init Attribute (GE_InitAttributes) 패턴
- [ ] Aggregator 의 Pre/Post Modifier 흐름
