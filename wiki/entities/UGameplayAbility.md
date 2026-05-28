---
type: entity
title: "UGameplayAbility"
aliases: [UGameplayAbility, GameplayAbility, GA, Ability]
kind: model
sources:
  - "[[sources/ue-gas-skill]]"
tags: [ue, plugin, gas]
last_updated: 2026-05-09
---

# UGameplayAbility

## 요약

GAS Plugin 의 스킬 / 액티브 능력 베이스. [[entities/UObject]] 자손. [[entities/UAbilitySystemComponent]]::GiveAbility 로 등록 → TryActivateAbility 로 발동. InstancingPolicy / NetExecutionPolicy 로 라이프사이클 / 멀티플레이 분기.

## 관계

- 부모: [[entities/UObject]]
- 호스트: [[entities/UAbilitySystemComponent]] (등록 / 발동)
- 협력: [[entities/FGameplayEffect]] (효과 적용), [[entities/FGameplayTag]] (조건 / 차단)

## 핵심 주장

- InstancingPolicy 3종: NonInstanced (CDO 호출, GameplayEffect 만 사용) / InstancedPerActor (기본 권장) / InstancedPerExecution (다중 호출 동시).
- NetExecutionPolicy 4종: LocalPredicted (Client 즉시 실행 + Server 검증) / LocalOnly / ServerInitiated (Server 가 시작) / ServerOnly.
- API:
  - `ActivateAbility(Handle, ActorInfo, ActivationInfo, TriggerEventData)` — 발동 진입점.
  - `CommitAbility` = `CheckCost + CheckCooldown + ApplyCost + ApplyCooldown`. 보통 ActivateAbility 시작에 호출.
  - `EndAbility` — 어빌리티 종료. CleanUp.
- Ability Tags / Cancel Tags / Block Tags / Activation Required Tags / Activation Blocked Tags — Tag 기반 조건.
- AbilityTask: 비동기 단계 (Wait / Trace / Montage Play 등). UAbilityTask 자손 인스턴스로 chained.

## 열린 질문

- [ ] LocalPredicted 의 정확한 reconciliation 흐름
- [ ] Custom AbilityTask 작성 패턴
