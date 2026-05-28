---
type: synthesis
title: "GameplayCue Cosmetic vs Gameplay 분리 + MOBA Cooldown Reset 정책"
slug: gameplaycue-cosmetic-boundary
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-gas-skill]]"
  - "[[sources/ue-networking-skill]]"
  - "[[sources/mc-asset-validation-policy]]"
entities:
  - "[[entities/UAbilitySystemComponent]]"
  - "[[entities/UGameplayAbility]]"
  - "[[entities/FGameplayEffect]]"
  - "[[entities/FGameplayTag]]"
concepts:
  - "[[concepts/RPC]]"
  - "[[concepts/Authority-NetMode]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, gas, gameplaycue, cosmetic, cooldown, moba]
---

# GameplayCue Cosmetic vs Gameplay 분리 + MOBA Cooldown Reset 정책

## 1. Thesis

GAS 의 *2 가지 자주 침범되는 경계* — **(1) GameplayCue 가 게임 상태를 바꾸면 안 됨** (Cue = cosmetic only, 게임 로직 = GameplayEffect / GameplayAbility) / **(2) MOBA 의 Cooldown Reset 정책** (스킬 swap 시 cooldown 유지 vs 리셋, refund 시점). 본 synthesis 는 Cue 의 합법 / 금기 매트릭스 + Cooldown 의 4 가지 reset 시나리오 (swap / refund / death respawn / Phase change). [[synthesis/gas-advanced-runtime-patterns]] 의 미해결 §6 (Cue cosmetic vs gameplay) + §7 (cooldown reset) 결합.

## 2. (1) GameplayCue Cosmetic Boundary

| 합법 (Cue 가 처리) | 금기 (GE / GA 처리) |
| -- | -- |
| Niagara Spawn (폭발 VFX) | HP 변경 |
| Sound Play (피격음) | Tag 추가 / 제거 |
| 카메라 흔들림 (`PlayWorldCameraShake`) | Damage 적용 |
| 화면 효과 (PostProcess Material 활성) | 능력 cooldown 시작 |
| 짧은 hit pause (게임 일시정지 X — Time Dilation) | Buff / Debuff 부여 |
| UI 알림 (HUD 메시지) | Money / XP 변경 |

**원칙** — Cue Notify 가 *게임 결정에 영향 안 주는* 모든 효과. 다음 함수 호출 시점에 *지금 제거되어도 게임 로직 무결*:

```cpp
// 예시 — Cue Notify (BP 또는 C++ UGameplayCueNotify_Actor 자손)
class AGCN_FireExplosion : public AGameplayCueNotify_Actor
{
    virtual bool OnExecute_Implementation(AActor* Target, const FGameplayCueParameters& Params) override
    {
        // OK — Niagara
        UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, FireVFX,
            Params.Location, Params.Normal.Rotation(), FVector(1), /*bAutoDestroy=*/true,
            /*bAutoActivate=*/true, ENCPoolMethod::AutoRelease);

        // OK — Sound
        UGameplayStatics::PlaySoundAtLocation(this, ExplosionSound, Params.Location);

        // OK — Camera shake
        if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0)) {
            PC->ClientStartCameraShake(ShakeClass);
        }

        // ❌ 금기 — HP 변경
        // if (auto* Char = Cast<AMyChar>(Target)) Char->TakeDamage(50.f);

        // ❌ 금기 — GameplayEffect 부여
        // ASC->ApplyGameplayEffectToSelf(GE_Damage, 1.f, ASC->MakeEffectContext());

        return true;
    }
};
```

## 3. Cue 가 게임 영향을 *간접* 으로 주는 경계 케이스

| 케이스 | 합법 / 금기 |
| -- | -- |
| Cue 가 Time Dilation 적용 (hit pause) | △ — *짧은 hit pause* 는 모든 클라가 동시 — 합법. *긴 게임 동안 dilation* 은 게임 로직 — GE 처리 |
| Cue 가 카메라를 *공격자 방향으로 회전* | △ — Camera 자체는 cosmetic 하지만, *Look-Direction 이 게임 입력에 영향* 주면 금기 |
| Cue 가 Loot Drop VFX 만 — Loot 자체 spawn 은 GA | ✓ 합법 분리 |
| Cue 가 *Tutorial UI 표시* | ✓ — UI 는 cosmetic. 게임 진행에는 무관 |
| Cue 가 *Achievement 진행* | ❌ — Online Subsystem 호출 — gameplay 로 분류 |

## 4. (2) MOBA Cooldown Reset 정책

GAS 의 Cooldown 은 *Duration 기반 GameplayEffect* — `GE_Cooldown_Q` 가 부여되어 있는 동안 Q 스킬 활성 차단. 4 시나리오:

### 4.1 스킬 swap (`ClearAbility` + `GiveAbility`)

```cpp
// 옵션 A — 옛 스킬 cooldown 유지 (RPG 식)
void SwapAbility(TSubclassOf<UGameplayAbility> OldCls, TSubclassOf<UGameplayAbility> NewCls)
{
    // 기존 cooldown GE 도 ClearAbility 와 함께 자동 제거?
    // 정답: ClearAbility 는 *능력만* 제거. GE_Cooldown 은 ASC 에 별도 active.
    //       cooldown 유지하려면 GE 를 그대로 두고 능력만 swap.
    ASC->ClearAbility(OldHandle);
    ASC->GiveAbility(FGameplayAbilitySpec(NewCls));
    // GE_Cooldown_Q 는 그대로 → 새 Q 스킬도 cooldown 동안 활성 안 됨
}

// 옵션 B — swap 시 cooldown 초기화 (MOBA 식 talent 변경)
void SwapAbilityWithReset(...)
{
    ASC->ClearAbility(OldHandle);
    ASC->GiveAbility(FGameplayAbilitySpec(NewCls));
    // 명시적 Cooldown GE 제거
    FGameplayTagContainer CooldownTags;
    CooldownTags.AddTag(FGameplayTag::RequestGameplayTag(TEXT("Cooldown.Ability.Q")));
    ASC->RemoveActiveGameplayEffectsByTag(CooldownTags);
}
```

게임 결정 — *talent 영구 변경* = 옵션 A (cooldown 유지, 페널티), *상점 구매 / 임시 boost* = 옵션 B.

### 4.2 Refund (스킬 사용 직후 취소)

```cpp
void UMyAbility::CancelAndRefund()
{
    // CancelAbility — 진행 중 능력 즉시 종료
    CancelAbility(GetCurrentAbilitySpecHandle(), GetCurrentActorInfo(), GetCurrentActivationInfo(), false);
    // Cooldown 환불 — 부여된 GE 제거
    GetAbilitySystemComponentFromActorInfo()->RemoveActiveGameplayEffect(CooldownEffectHandle);
}
```

### 4.3 Death + Respawn

```cpp
// Pawn 모델 — ASC 도 destroy → cooldown 도 사라짐. respawn 시 fresh
// PlayerState 모델 — ASC 살아남음. 사망 시 cooldown reset 가 디자인 결정:
//   (a) Cooldown 유지 — punishment (사망해도 cooldown 카운트 진행)
//   (b) Cooldown reset — respawn 후 즉시 재사용 가능
void OnRespawn()
{
    if (auto* PS = GetPlayerState<AMyPlayerState>()) {
        UAbilitySystemComponent* ASC = PS->GetAbilitySystemComponent();
        // 옵션 (b) — 모든 cooldown 제거
        FGameplayTagContainer CooldownTags;
        CooldownTags.AddTag(FGameplayTag::RequestGameplayTag(TEXT("Cooldown")));
        ASC->RemoveActiveGameplayEffectsByTag(CooldownTags);
    }
}
```

### 4.4 Phase Change (보스의 페이즈 전환)

```cpp
// 보스 페이즈 1 → 2 — 모든 ability cooldown 즉시 reset (challenge increase)
void EnterPhase2()
{
    UAbilitySystemComponent* ASC = GetAbilitySystemComponent();
    FGameplayTagContainer Tags;
    Tags.AddTag(FGameplayTag::RequestGameplayTag(TEXT("Cooldown")));
    ASC->RemoveActiveGameplayEffectsByTag(Tags);
    // 새 ability 부여 (페이즈 2 전용)
    for (TSubclassOf<UGameplayAbility> Cls : Phase2Abilities) {
        ASC->GiveAbility(FGameplayAbilitySpec(Cls));
    }
}
```

## 5. 함정 / 열린 질문

- [ ] **Cue 가 *Local Predict* 와 충돌** — Server replicate Cue + 동시에 Local Predict trigger → 같은 효과 두 번. `bIsClientPrediction` flag 또는 *Local 이 먼저 트리거 시 Server replicate 무시*
- [ ] **Cue 의 Late Join 동기** — 진행 중 *Looping* Cue (캐릭터의 화염) — 새 클라가 합류해도 안 보임. ASC 의 `GetOwnedGameplayTags` 를 [[synthesis/late-join-reconnect-state-sync]] 의 SyncRPC 안에 broadcast
- [ ] **`GameplayCueParameters` 의 NetSerialize** — Param 이 `FVector_NetQuantize` 등 사용 — 정밀도 절감
- [ ] **Cooldown 의 Modifier (cdr — Cooldown Reduction)** — `GE_Cooldown.Magnitude` 가 `AttributeBased` — Caster 의 `CooldownReduction` Attribute 가 GE Duration 결정 — 실시간 cdr 변경 vs cooldown 적용 시점 결정
- [ ] **Refund 시 Mana 도 환불** — `CancelAndRefund` 가 Cooldown 만 — Mana cost 도 함께 환불해야 자연스러움. `OnAbilityCancelled` 콜백에서 Cost GE 도 제거
- [ ] **Cue 의 `OnRemove`** — Looping Cue (Persistence) 가 GE 제거 시점에 `OnRemove_Implementation` 발화 — VFX deactivate 시점에 누락되면 stuck VFX (예: 죽은 적 위 화염 영구 지속)
- [ ] **Phase Change 의 Server-Client 동기** — 페이즈 전환 시점이 서버/클라 시간 미세 차이. Cooldown reset 도 Multicast Reliable 의무 (열린)
- [ ] **GAS 의 cdr 와 GE Duration race** — cdr 를 매 프레임 갱신 — GE 부여 시점에 *일정 cdr 사용* vs *매 frame 재계산* (열린)

## 6. 관련

### Sources

[[sources/ue-gas-skill]] · [[sources/ue-networking-skill]] · [[sources/mc-asset-validation-policy]]

### Entities

[[entities/UAbilitySystemComponent]] · [[entities/UGameplayAbility]] · [[entities/FGameplayEffect]] · [[entities/FGameplayTag]]

### Concepts

[[concepts/RPC]] · [[concepts/Authority-NetMode]] · [[concepts/MC-Asset-Validation-Policy]]

### Related synthesis

[[synthesis/gas-advanced-runtime-patterns]] (Cue NetMulticast 베이스 + 스킬 swap) · [[synthesis/gas-pawn-vs-playerstate-decision]] (Death respawn cooldown 분기) · [[synthesis/late-join-reconnect-state-sync]] (Cue Late Join) · [[synthesis/gameplaycue-prediction-modifier-cdr]] (Local Predict + Late Join + cdr Modifier + Refund Mana)
