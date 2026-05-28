---
type: synthesis
title: "GAS 고급 런타임 패턴 — GameplayCue NetMulticast + MOBA 스킬 swap (GiveAbility/ClearAbility) + SeamlessTravel PlayerState transfer"
slug: gas-advanced-runtime-patterns
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-gas-skill]]"
  - "[[sources/ue-gameframework-controller]]"
  - "[[sources/ue-gameframework-gamemode]]"
  - "[[sources/ue-networking-skill]]"
entities:
  - "[[entities/UAbilitySystemComponent]]"
  - "[[entities/UGameplayAbility]]"
  - "[[entities/FGameplayEffect]]"
  - "[[entities/FGameplayTag]]"
  - "[[entities/AGameStateBase]]"
concepts:
  - "[[concepts/SeamlessTravel]]"
  - "[[concepts/Match-State]]"
  - "[[concepts/RPC]]"
  - "[[concepts/Possession]]"
status: living
tags: [synthesis, gas, gameplay-cue, ability-swap, seamless-travel]
---

# GAS 고급 런타임 패턴

## 1. Thesis

[[synthesis/gas-pawn-vs-playerstate-decision]] 의 호스트 결정 후 *실제 게임플레이 운영* 에서 부딪히는 3 가지 — **(1) GameplayCue 의 NetMulticast 시각 효과 (Cue Tag → Niagara/Sound 자동 broadcast) / (2) MOBA 의 동적 스킬 swap (`GiveAbility` / `ClearAbility`) — Pawn 모델 vs PlayerState 모델 차이 / (3) SeamlessTravel 시 PlayerState 의 능력 / 어트리뷰트 transfer (일부만 살아남음, 명시적 transfer 의무)**. 본 synthesis 는 각 케이스의 표준 패턴 + 함정 + 두 모델 매트릭스.

## 2. (1) GameplayCue NetMulticast

GameplayCue = Tag 기반 cosmetic 효과 — Server 에서 `ASC->ExecuteGameplayCue(Tag, Param)` → 자동으로 모든 클라이언트에서 *등록된 GameplayCueNotify_Static / Actor* 가 trigger.

```cpp
// GameplayEffect 안에 Cue Tag 등록 (BP 또는 C++)
GE_FireballHit.GameplayCues.Add(FGameplayCueTag{TEXT("GameplayCue.Fire.Explosion")});

// Server 가 Effect 적용
ASC_Source->ApplyGameplayEffectToTarget(GE_FireballHit, ASC_Target);

// 자동: GameplayCueManager 가 모든 클라이언트에서
//   "/Game/GameplayCues/GCN_FireExplosion" (Tag 매칭) 찾아 spawn — Niagara + Audio
```

**Replication mode 별 동작**:
- `Mixed` (표준) — 자기 효과는 자세히, 남의 건 Cue 만 broadcast → 대역폭 절감
- `Full` — 모든 효과 broadcast → 디버그 / 단일 캐릭터
- `Minimal` — 자기 효과만 → AI / NPC

## 3. (2) MOBA 스킬 swap — Pawn 모델 vs PlayerState 모델

[[synthesis/gas-pawn-vs-playerstate-decision]] 의 두 모델 차이:

### Pawn 모델 (LoL 챔피언 = 캐릭터 = 능력 한 묶음)

스킬 swap 은 *드물거나 없음* — 죽으면 ASC 새로. 동적 swap 은 talent / rune 시스템 정도:

```cpp
void AMyChar::ApplyTalentTree(UTalentDataAsset* Talent)
{
    if (!HasAuthority()) return;

    // 기존 ability 제거
    for (FGameplayAbilitySpec& Spec : ASC->GetActivatableAbilities()) {
        if (Spec.SourceObject == OldTalent) {
            ASC->ClearAbility(Spec.Handle);
        }
    }
    // 새 ability 부여
    for (TSubclassOf<UGameplayAbility> AbilityClass : Talent->Abilities) {
        FGameplayAbilitySpec Spec(AbilityClass, /*Level=*/1, /*InputID=*/-1, /*SourceObject=*/Talent);
        ASC->GiveAbility(Spec);
    }
}
```

### PlayerState 모델 (WoW 캐릭터 = 영구, Spec 변경)

스킬 swap 은 *자주 발생* — Spec 변경 (전사 → 보호 / 정복). Pawn 변경 없이 ASC 유지:

```cpp
void AMyPlayerState::SwapSpec(EClassSpec NewSpec)
{
    if (!HasAuthority()) return;

    // 모든 Spec 능력 일괄 제거
    TArray<FGameplayAbilitySpecHandle> ToRemove;
    for (FGameplayAbilitySpec& Spec : ASC->GetActivatableAbilities()) {
        if (Spec.SourceObject->IsA<UClassSpecDataAsset>()) {
            ToRemove.Add(Spec.Handle);
        }
    }
    for (FGameplayAbilitySpecHandle H : ToRemove) ASC->ClearAbility(H);

    // 새 Spec 능력 부여
    UClassSpecDataAsset* NewData = LoadSpec(NewSpec);
    for (TSubclassOf<UGameplayAbility> Cls : NewData->Abilities) {
        ASC->GiveAbility(FGameplayAbilitySpec(Cls, 1, -1, NewData));
    }
}
```

핵심 — `SourceObject` 로 *어느 시스템이 부여한 ability 인지* 식별 → 일괄 제거 가능.

## 4. (3) SeamlessTravel + PlayerState transfer

[[concepts/SeamlessTravel]] 시 World 는 새로 — World Subsystem 도, World 안 Actor 도 destroy. *PlayerState* 만 살아남음 (`bIsInactive=true` 마킹 후 새 World 로 복사). 그러나 *기본적으로 능력/어트리뷰트는 transfer 안 됨* — 명시적 transfer 절차:

```cpp
// AGameMode 측 (서버)
class AMyGameMode : public AGameModeBase
{
    virtual void InitSeamlessTravelPlayer(AController* NewController) override
    {
        Super::InitSeamlessTravelPlayer(NewController);

        // 새 World 의 Pawn spawn 후 ASC InitAbilityActorInfo 다시
        if (AMyChar* NewPawn = Cast<AMyChar>(NewController->GetPawn())) {
            if (AMyPlayerState* PS = Cast<AMyPlayerState>(NewController->PlayerState)) {
                UAbilitySystemComponent* ASC = PS->GetAbilitySystemComponent();
                ASC->InitAbilityActorInfo(PS, NewPawn);  // Avatar = 새 Pawn
                // 능력은 PS 에 유지된 채로 살아남음
            }
        }
    }

    virtual void HandleSeamlessTravelPlayer(AController*& C) override
    {
        Super::HandleSeamlessTravelPlayer(C);
        // 새 GameMode 가 PS 의 데이터로 새 캐릭터 생성
    }
};
```

**기본 transfer 되는 것** (PlayerState 모델):
- ASC 자체 (PS 안 호스트)
- 모든 GameplayAbility (`GetActivatableAbilities`)
- AttributeSet (PS 안 멤버)
- 영구 GameplayEffect (Duration=Infinite)

**기본 transfer 안 되는 것**:
- Avatar (Pawn) — 새 World 의 새 Pawn 으로 InitAbilityActorInfo 재호출 의무
- World subsystem 데이터 (몹 처치 카운트 등) — GameInstance 로 옮겨야
- 활성화 중인 GameplayAbility — `EndAbility` 자동
- Duration 효과 (TimeRemaining 1초 남았던 버프) — 정확히 transfer 됨, 단 새 World 에서 GameplayCue 다시 trigger 필요

## 5. 함정 / 열린 질문

- [ ] **GameplayCue 의 *Late Join*** — 새로 합류한 클라이언트는 이미 진행 중인 Cue (지속 효과의 cosmetic) 안 받음. ASC 의 Replicated Cue Tag 컨테이너로 *현재 활성 cue* 동기 + Local 트리거
- [ ] **`GiveAbility` 후 즉시 `TryActivateAbility`** — 부여 직후 활성화는 race. `OnGiveAbility` 콜백 이후만 안전
- [ ] **`ClearAbility` 의 Replication 도착 지연** — Server `ClearAbility` 직후 Server 는 즉시 사라짐. Client 는 다음 Replication 패킷까지 살아있음 — 그 사이 Activate 가능 (race). `bIsActive` 검사 + Server validation
- [ ] **AttributeSet 의 SeamlessTravel 도착 race** — 새 World 의 BeginPlay 시 PS 의 AttributeSet 이 *아직 Replicate 안 됨* 가능. `OnRep_*` 또는 `ASC->InitAbilityActorInfo` 시점에 보장
- [ ] **PlayerState 의 `bIsInactive`** — SeamlessTravel 시 자동 마킹 후 새 World 로 복사. 사용자 코드에서 `bIsInactive=true` 인 PS 를 게임 로직에 포함하면 버그
- [ ] **Pawn 모델 + SeamlessTravel** — Pawn 안 ASC 는 destroy → 능력 유실. 영구 능력 필요하면 GameInstance Subsystem 으로 백업 / 복원 (열린)
- [ ] **GameplayCue 의 cosmetic vs gameplay 분리** — Cue 가 게임 상태를 변경하면 (HP 회복 등) 안티패턴. Cue = 시각 only, 게임 로직 = GameplayEffect. 명확 분리 (열린)
- [ ] **MOBA 의 ability charge / cooldown** — 스킬 swap 후 cooldown 어떻게? swap 후 reset vs 유지. 게임 디자인 결정 (열린)

## 6. 관련

### Sources

[[sources/ue-gas-skill]] · [[sources/ue-gameframework-controller]] · [[sources/ue-gameframework-gamemode]] · [[sources/ue-networking-skill]]

### Entities

[[entities/UAbilitySystemComponent]] · [[entities/UGameplayAbility]] · [[entities/FGameplayEffect]] · [[entities/FGameplayTag]] · [[entities/AGameStateBase]]

### Concepts

[[concepts/SeamlessTravel]] · [[concepts/Match-State]] · [[concepts/RPC]] · [[concepts/Possession]]

### Related synthesis

[[synthesis/gas-pawn-vs-playerstate-decision]] (호스트 결정 베이스) · [[synthesis/server-vs-client-rpc-decision-tree]] (Cue NetMulticast 결정) · [[synthesis/subsystem-advanced-patterns]] (PlayerState vs GameInstance Subsystem 데이터 옮김) · [[synthesis/gameplaycue-cosmetic-boundary]] (Cue cosmetic 경계 + cooldown reset 정책)
