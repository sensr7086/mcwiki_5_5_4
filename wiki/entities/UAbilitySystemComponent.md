---
type: entity
title: "UAbilitySystemComponent (ASC)"
aliases: [UAbilitySystemComponent, ASC, GAS Component]
kind: model
sources:
  - "[[sources/ue-gas-skill]]"
tags: [ue, plugin, gas, multiplayer]
last_updated: 2026-05-09
---

# UAbilitySystemComponent (ASC)

## 요약

GAS Plugin 의 중심 — UGameplayTasksComponent → [[entities/UActorComponent]] 자손. Owner Actor 에 부착. 모든 GAS 기능 (어빌리티 / 어트리뷰트 / 효과 / 태그) 의 진입점.

## 관계

- 부모: UGameplayTasksComponent → [[entities/UActorComponent]]
- 호스트: [[entities/APawn]] / [[entities/APlayerController]] / APlayerState
- 협력: [[entities/UAttributeSet]], [[entities/UGameplayAbility]], [[entities/FGameplayEffect]], [[entities/FGameplayTag]]

## 핵심 주장

- Pawn vs PlayerState 모델: PlayerState 가 ASC owner 권장 (multiplayer respawn 시 유지). InitAbilityActorInfo(OwnerActor=PlayerState, AvatarActor=Pawn).
- bCanEverTick = true (기본 ON — Effect 갱신).
- API:
  - `GiveAbility(Spec)` — Ability 등록 (자동 NewObject).
  - `TryActivateAbility(Spec)` — 어빌리티 발동 시도.
  - `ApplyGameplayEffectToTarget(Effect, Target)` — Effect 적용.
  - `HasMatchingGameplayTag(Tag)` — Tag 검사.
- EGameplayEffectReplicationMode 3종: Full (모든 client) / Mixed (자기+others 부분) / Minimal (자기 + Cosmetic Cue).
- 6 대 정책 ([[concepts/Component-Policies-6]]): 자동 적용. CDO 변경 금지.
- 자산 정책: GameplayAbility / Effect Class = Hard. Cosmetic Cue (VFX/SFX/Niagara) = Soft + Bundle.

## 열린 질문

- [ ] InitAbilityActorInfo 호출 시점 — Server 와 Client 차이
- [ ] Replication Mode 결정 트리 (어떤 게임에 어느 모드)
