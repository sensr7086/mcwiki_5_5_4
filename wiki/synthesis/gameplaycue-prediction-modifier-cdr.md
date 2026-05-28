---
type: synthesis
title: "GameplayCue Local Prediction + Late Join 복원 + cdr Modifier + Refund Mana 환불 통합"
slug: gameplaycue-prediction-modifier-cdr
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/ue-gas-skill]]"
  - "[[sources/ue-networking-skill]]"
entities:
  - "[[entities/UAbilitySystemComponent]]"
  - "[[entities/UGameplayAbility]]"
  - "[[entities/FGameplayEffect]]"
  - "[[entities/FGameplayTag]]"
  - "[[entities/UAttributeSet]]"
concepts:
  - "[[concepts/RPC]]"
  - "[[concepts/PushModel]]"
  - "[[concepts/Authority-NetMode]]"
status: living
tags: [synthesis, gas, gameplaycue, prediction, cdr, refund]
---

# GameplayCue Local Prediction + Late Join + cdr Modifier + Refund Mana

## 1. Thesis

[[synthesis/gameplaycue-cosmetic-boundary]] 의 4 미해결 — **(1) Cue Local Prediction 과 Server replicate 충돌 — 같은 효과 두 번 / (2) Looping Cue Late Join 미동기 — 새 클라가 진행 중 cue 안 봄 / (3) cdr (Cooldown Reduction) Modifier 와 GE Duration race — cdr 변경 시점 / (4) Refund 시 Mana / Cost 환불**. 본 synthesis 는 4 케이스의 *공통 메커니즘* (`bIsClientPrediction` flag + `ASC->GetOwnedGameplayTags` broadcast + `FGameplayModifierInfo::ModifierMagnitude` AttributeBased + `CancelAbility` callback chain) + 결정 트리.

## 2. (1) Local Prediction vs Server Replicate

GAS Ability `bIsClientPrediction=true` 시 — Client 가 Local Predict trigger → Server 가 동일 Multicast replicate → 같은 Cue 두 번:

```cpp
// 옵션 A — Predict 했으면 Server Multicast 무시 (Client 측 cue 가 더 빠름)
class UMyAbility : public UGameplayAbility
{
    virtual void ActivateAbility(...) override
    {
        // Local Predict
        if (HasAuthority() == false && bIsClientPrediction) {
            ASC->ExecuteGameplayCue(FGameplayTag::RequestGameplayTag("GameplayCue.Fire.Explosion"),
                                    FGameplayCueParameters{});
            // bClientPredicted 마킹 — OnRep_GameplayCue 가 이 flag 보고 skip
            PredictedCueTags.Add("GameplayCue.Fire.Explosion");
        }
        Super::ActivateAbility(...);
    }
};

// ASC 측 — OnRep_GameplayCue
void UMyASC::OnRep_GameplayCueAdded(FGameplayTag CueTag)
{
    if (PredictedCueTags.Contains(CueTag)) {
        PredictedCueTags.Remove(CueTag);
        return;  // Server replicate 무시 — Local 이미 실행
    }
    // 일반 Cue 실행
    ExecuteGameplayCueLocal(CueTag);
}
```

**대안** — Server-only Cue (Client 는 cue 실행 안 함, Server 가 Multicast 만) — 단순하지만 lag 증가.

## 3. (2) Looping Cue Late Join 복원

새 클라 합류 시 진행 중 *Looping* Cue (캐릭터 화염 지속) 안 보임. ASC 의 ActiveCueTags broadcast:

```cpp
// AMyPlayerController::OnRep_PlayerState (Late Join)
void AMyPlayerController::OnRep_PlayerState()
{
    Super::OnRep_PlayerState();
    if (IsLocalController()) {
        ServerRequestActiveCues();
    }
}

UFUNCTION(Server, Reliable)
void AMyPlayerController::ServerRequestActiveCues();

void AMyPlayerController::ServerRequestActiveCues_Implementation()
{
    // Server 가 *모든* Pawn 의 진행 중 Looping Cue 수집 → 그 클라에만 broadcast
    TArray<FActiveCueSnapshot> Snapshots;
    for (TActorIterator<APawn> It(GetWorld()); It; ++It) {   // ❌ 안티 — vault: [[concepts/Global-Iterator-Avoidance]]
        // 대안 — GameState 가 Looping Cue Owner 들 등록부 보유
    }
    ClientApplyActiveCues(Snapshots);
}

UFUNCTION(Client, Reliable)
void ClientApplyActiveCues(const TArray<FActiveCueSnapshot>& Snapshots);

void ClientApplyActiveCues_Implementation(const TArray<FActiveCueSnapshot>& Snapshots)
{
    for (const auto& S : Snapshots) {
        S.OwnerPawn->GetAbilitySystemComponent()
            ->ExecuteGameplayCue(S.CueTag, S.Parameters);
    }
}
```

[[synthesis/late-join-reconnect-state-sync]] §4 의 SyncRPC 패턴과 결합 — Cue 는 그 패턴의 *카테고리 5* (Looping cosmetic).

## 4. (3) cdr Modifier 와 GE Duration

`FGameplayModifierInfo::ModifierMagnitude` 가 *AttributeBased* — Caster 의 `CooldownReduction` Attribute 가 GE Duration 결정:

```cpp
// GE_Cooldown_FireSpell.h
class UGE_Cooldown_FireSpell : public UGameplayEffect
{
    UGE_Cooldown_FireSpell() {
        DurationPolicy = EGameplayEffectDurationType::HasDuration;
        DurationMagnitude = FGameplayEffectModifierMagnitude(
            FAttributeBasedFloat{
                .BackingAttribute = UMyAttrSet::GetCooldownReductionAttribute(),
                .Coefficient = -1.0f,    // 음수 — cdr 가 클수록 Duration 짧음
                .PreMultiplyAdditiveValue = 5.0f,  // 베이스 Duration 5초
            });
        // 결과 Duration = 5 + (-1) × cdr = 5 - cdr
    }
};
```

**race** — GE 적용 *시점* 에 cdr Attribute 가 N → 0.5 초 후 cdr 가 M 으로 변경. GE Duration 은 *적용 시점 N* 으로 고정. 의도된 design — *시전 시점 cdr 적용*.

만약 *실시간 cdr 반영* 원하면 — GE 의 `Period` 사용 + 매 tick 재계산 (드물게 권장).

## 5. (4) Refund Mana — Ability Cost 환불

`CancelAbility` 시 cooldown + cost 둘 다 환불:

```cpp
class UMyAbility : public UGameplayAbility
{
    UPROPERTY() FActiveGameplayEffectHandle CooldownHandle;
    UPROPERTY() FActiveGameplayEffectHandle CostHandle;

    virtual void ActivateAbility(...) override
    {
        Super::ActivateAbility(...);
        // Cost 적용 (Mana -10) — 핸들 보관
        if (UGameplayEffect* CostGE = GetCostGameplayEffect()) {
            CostHandle = ASC->ApplyGameplayEffectToSelf(CostGE, /*Level=*/1.0f, ...);
        }
        // Cooldown 적용 — 핸들 보관
        if (UGameplayEffect* CooldownGE = GetCooldownGameplayEffect()) {
            CooldownHandle = ASC->ApplyGameplayEffectToSelf(CooldownGE, ...);
        }
    }

    UFUNCTION(BlueprintCallable)
    void CancelAndRefund()
    {
        CancelAbility(GetCurrentAbilitySpecHandle(), GetCurrentActorInfo(), GetCurrentActivationInfo(), false);

        // 환불 — GE 둘 다 즉시 제거
        if (CostHandle.IsValid())     ASC->RemoveActiveGameplayEffect(CostHandle);
        if (CooldownHandle.IsValid()) ASC->RemoveActiveGameplayEffect(CooldownHandle);
    }
};
```

**시점** — Ability 진행 중 *중단 조건* 발화 (예: 시전 중 hit 받음 — interrupt) → CancelAndRefund 호출.

## 6. 결정 트리

```
Cue 가 게임 동작에 영향?
├── 없음 (시각만) → §2 Local Prediction OK
├── 있음 (HP 변경 등) → ❌ Cue 가 아님 — GameplayEffect 로 처리

Cue 가 *지속* (looping)?
├── Yes → §3 ASC->ActiveCueTags broadcast 의무 (Late Join)
└── No  → §2 Prediction 만

cdr 가 적용되는 시점?
├── 시전 시 한 번 (대부분) → §4 AttributeBasedFloat 디폴트
└── 실시간 (희귀) → GE Period + 매 tick 재계산

Ability 취소 시 Refund?
├── Cost + Cooldown 모두 → §5 두 핸들 모두 RemoveActiveGameplayEffect
└── Cost 만 (cooldown 페널티 유지) → CostHandle 만 Remove
```

## 7. 함정 / 열린 질문

- [ ] **Predict + Server replicate 의 *순서 비결정성*** — Client Predict 발화 vs Server Multicast 도착 — frame 단위로 race. 두 군데 모두 fingerprint (PredictionKey) 비교 의무
- [ ] **Looping Cue Late Join + Listen Server** — 호스트 클라는 Server + Client 동시 — ServerRequestActiveCues 가 *자기 자신에* 도 적용 시도. `IsLocalController()` 검사
- [ ] **cdr 의 *최대치 한도*** — cdr 100% 되면 Duration = 0 → instant ready. 게임 디자인 — Clamp (예: 80%) UPROPERTY
- [ ] **Refund 의 *부분 환불*** — Ability 가 단계적 (channel) 으로 진행 — 50% 진행 후 cancel → cost 50% 환불? 게임 디자인 결정 (열린)
- [ ] **Cue 의 *cosmetic 의도 위반 검출*** — Cue 안 HP 변경 / Damage 적용 등 — code review 또는 정적 분석 ([[synthesis/validation-static-analysis-ide-integration]]) 으로 감지
- [ ] **`OnRemoval` Cue 가 *Late Join 합류 시 발화*** — 진행 중 cue Snapshot broadcast → 매치 종료 시 OnRemoval 가 합류 클라에 *적용 안 됐던 OnExecute* 후 발화 → 시각 부조화
- [ ] **GAS 의 *Server-only Ability* (NotReplicated) 와 Cue** — Ability 자체는 Server only — Cue 는 Multicast — Client 는 ability 정보 없이 Cue 만 봄. 정상 동작 검증 (열린)
- [ ] **cdr Modifier 의 *음수 결과*** — cdr > 5 (Duration 5초 베이스 초과) → 결과 Duration 음수 → 즉시 expire 또는 무한 = 정의 안 됨. Clamp 의무 (열린)

## 8. 관련

### Sources

[[sources/ue-gas-skill]] · [[sources/ue-networking-skill]]

### Entities

[[entities/UAbilitySystemComponent]] · [[entities/UGameplayAbility]] · [[entities/FGameplayEffect]] · [[entities/FGameplayTag]] · [[entities/UAttributeSet]]

### Concepts

[[concepts/RPC]] · [[concepts/PushModel]] · [[concepts/Authority-NetMode]]

### Related synthesis

[[synthesis/gameplaycue-cosmetic-boundary]] (베이스 — Cue 경계 + Cooldown reset) · [[synthesis/gas-advanced-runtime-patterns]] (GameplayCue NetMulticast + 스킬 swap) · [[synthesis/late-join-reconnect-state-sync]] (Cue Late Join SyncRPC)
