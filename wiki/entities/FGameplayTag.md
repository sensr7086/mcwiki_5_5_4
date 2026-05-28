---
type: entity
title: "FGameplayTag / UGameplayTagsManager"
aliases: [FGameplayTag, GameplayTag, FGameplayTagContainer, UGameplayTagsManager]
kind: model
sources:
  - "[[sources/ue-gas-skill]]"
tags: [ue, plugin, gas]
last_updated: 2026-05-09
---

# FGameplayTag

## 요약

GameplayTags Plugin (GAS 의존). 계층적 태그 시스템 — `Damage.Fire.Burn`, `State.Stunned`, `Ability.Active` 등. UGameplayTagsManager 가 등록 + lookup. FGameplayTagContainer = Tag 집합. GAS 의 조건 / 차단 / 부여 의 핵심.

## 관계

- 자체 Plugin: GameplayTags (GAS 의존)
- 협력: [[entities/UAbilitySystemComponent]] / [[entities/FGameplayEffect]] / [[entities/UGameplayAbility]]

## 핵심 주장

- 계층 매칭: `Damage.Fire.Burn` 은 `Damage`, `Damage.Fire` 의 자손. HasMatchingTag(Damage) → Burn / Fire / Lightning 모두 매칭.
- 등록: Project Settings → GameplayTags → Add Tag (또는 .ini / DataTable).
- API: `Container.HasTag(Tag)` / `Container.HasAny(OtherContainer)` / `Container.HasAll(OtherContainer)`.
- GAS 통합:
  - Activation Required Tags — 어빌리티 발동 조건.
  - Activation Blocked Tags — 어빌리티 차단.
  - Granted Tags — 효과 적용 동안 부여.
  - Cancel Tags — 다른 어빌리티 취소.
- 5.x: GameplayTagContainer 의 native 직렬화 (FGameplayTagNetIndex) — 네트워크 효율적.

## 열린 질문

- [ ] Tag 등록의 .ini vs DataTable 결정
- [ ] FGameplayTagQuery 의 복잡한 조건 작성
