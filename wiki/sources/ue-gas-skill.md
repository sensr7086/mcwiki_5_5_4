---
type: source
title: "UE 5.7.4 GAS (GameplayAbilities) Plugin — Main SKILL"
slug: ue-gas-skill
source_path: raw/ue-wiki-llm/skills/GAS/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UAbilitySystemComponent]]"
  - "[[entities/UAttributeSet]]"
  - "[[entities/UGameplayAbility]]"
  - "[[entities/FGameplayEffect]]"
  - "[[entities/FGameplayTag]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, plugin, gas, multiplayer]
---

# UE 5.7.4 GAS (GameplayAbilities) Plugin — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/GAS/SKILL.md]]
> Kind: text · Date: 2026-05-09 · Ingested: 2026-05-09

## 1. Summary

**MOBA / RPG / Multiplayer 액션 표준** (Plugin: `Engine/Plugins/Runtime/GameplayAbilities/`). 어트리뷰트 (체력/마나) + 어빌리티 (스킬) + 이펙트 (버프/데미지) + 태그 (상태) 의 결합 시스템. 5 개 핵심: [[entities/UAbilitySystemComponent]] (ASC, 진입점) + [[entities/UAttributeSet]] (속성) + [[entities/UGameplayAbility]] (스킬) + [[entities/FGameplayEffect]] (효과) + [[entities/FGameplayTag]] (태그).

## 2. Key claims

- ASC = UGameplayTasksComponent 자손 = UActorComponent. Owner Actor 에 부착. `bCanEverTick = true` (Effect 갱신).
- Pawn vs PlayerState 모델: PlayerState 가 ASC owner 권장 (multiplayer respawn 시 유지). InitAbilityActorInfo(Owner=PlayerState, Avatar=Pawn).
- EGameplayEffectReplicationMode 3종: Full (모든 client) / Mixed (자기 + others 부분) / Minimal (자기만 + Cosmetic GameplayCue).
- InstancingPolicy 3종 (UGameplayAbility): NonInstanced (CDO 호출, GE 만) / InstancedPerActor (가장 흔함) / InstancedPerExecution (다중 호출).
- NetExecutionPolicy 4종: LocalPredicted / LocalOnly / ServerInitiated / ServerOnly.
- CommitAbility = Cost (Mana/Stamina 차감) + Cooldown (재사용 제한). 어빌리티 발동 시점.
- GameplayCue = Cosmetic (VFX/SFX/Niagara). FGameplayCueTag + 별도 Manager (UGameplayCueManager).
- 자산 정책: GameplayAbility / Effect Class = Hard (BP 작음). Cosmetic Cue = Soft + Bundle (Visual / Audio 분리). Match Start 사전 PreLoad.

## 3. Quotations

> "MOBA / RPG / Multiplayer 액션 표준 — 5.x 권장 게임플레이 시스템 표준."

## 4. Open questions / next sources

- [ ] GAS 의 Server-Authoritative + Client Prediction 패턴 (LocalPredicted)
- [ ] GameplayCueManager 의 Bundle 분리 표준 패턴
