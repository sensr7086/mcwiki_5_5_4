---
name: gas-main
description: GameplayAbilities Plugin (MOBA/RPG/Multiplayer 표준) - UAbilitySystemComponent + UAttributeSet + UGameplayAbility + FGameplayEffect + FGameplayTag + Pawn vs PlayerState + 5종 핵심 정책.
---

# GAS — Gameplay Ability System (Plugin)

> **위치**: `Engine/Plugins/Runtime/GameplayAbilities/Source/GameplayAbilities/` (Epic 표준 플러그인)
> **모듈명**: `GameplayAbilities` + 의존: `GameplayTags` + `GameplayTasks`
> **베이스**: `UAbilitySystemComponent : public UGameplayTasksComponent`
> **요지**: **MOBA / RPG / Multiplayer 액션 표준** — 어트리뷰트 (체력/마나) + 어빌리티 (스킬) + 이펙트 (버프/데미지) + 태그 (상태) 의 **결합 시스템**. **5.x 에서 권장되는 게임플레이 시스템 표준**.

---

## 🚨 공통 정책 (Components 6대 의무)

> 모든 컴포넌트는 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) 의 6대 정책 적용.

| # | 정책 | GAS 특화 |
|---|------|---------|
| 1 | **Mobility** | UAbilitySystemComponent = UActorComponent — Mobility 무관 |
| 2 | **NewObject + DuplicateObject** | Ability 인스턴스 = `UAbilitySystemComponent::GiveAbility()` 가 자동 생성 — 직접 `NewObject` 안 함 |
| 3 | **GC 방어** | UAttributeSet 은 ASC 의 SubObject — `UPROPERTY()` 자동 보호 |
| 4 | **GetOwner 캐싱** | ASC 자체가 OwnerActor + AvatarActor 분리 — 자식이 캐싱 |
| 5 | **PrimaryComponentTick** | ASC = `bCanEverTick = true` (기본 ON — Effect 갱신) |
| 6 | **CDO** | UGameplayAbility 의 InstancingPolicy = `InstancedPerActor` 권장 |
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) — **GameplayAbility / GameplayEffect Class** = `TSubclassOf<UGameplayAbility>` Hard (BP 작음) / **Cosmetic GameplayCue (VFX·SFX·Niagara)** = `FGameplayCueTag` + Soft + LoadPrimaryAsset (큰 Niagara/Sound). **GameplayCueManager** 가 `LoadPrimaryAsset` 자동 — Cue 어셋 Bundle 분리 (`Visual` / `Audio`). MOBA 스킬 = Match Start 시 모든 Ability + Cue 사전 PreLoad. |

---

## 1. 핵심 구성 요소 (5종)

| 클래스 | 역할 |
|--------|------|
| `UAbilitySystemComponent` | **GAS 의 중심** — Owner Actor 에 부착, 모든 GAS 기능의 진입점 |
| `UAttributeSet` | 어트리뷰트 (Health/Mana/Stamina/AttackPower 등) 의 정의 + 복제 |
| `UGameplayAbility` | 어빌리티 (스킬·액션) — Ability 의 instance 단위로 실행 |
| `FGameplayEffect` | 이펙트 (데미지·버프·디버프) — 어트리뷰트 변경 + 태그 부여 + 지속 시간 |
| `FGameplayTag` | 태그 (상태·이벤트·키) — Hierarchical FName (`State.Stunned`, `Event.Damaged.Critical`) |

```
Owner Actor (보통 Pawn / PlayerState)
└── UAbilitySystemComponent (ASC)
    ├── TArray<UAttributeSet*> SpawnedAttributes   (Health/Mana/...)
    ├── FActiveGameplayAbilities (GiveAbility 로 등록된 어빌리티)
    ├── FActiveGameplayEffectsContainer (적용 중인 효과)
    └── FGameplayTagCountContainer (현재 보유 태그)
```

---

## 2. UAbilitySystemComponent (ASC)

### 2.1 표준 셋업 — Pawn vs PlayerState 모델

#### 모델 A: Pawn 에 ASC (단순 게임 — 1인칭/3인칭 액션)

```cpp
UCLASS()
class AMyChar : public ACharacter, public IAbilitySystemInterface
{
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="GAS")
    TObjectPtr<UAbilitySystemComponent> AbilitySystem;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="GAS")
    TObjectPtr<UMyAttributeSet> Attributes;

public:
    AMyChar();
    virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override { return AbilitySystem; }
};

// .cpp
AMyChar::AMyChar()
{
    AbilitySystem = CreateDefaultSubobject<UAbilitySystemComponent>(TEXT("AbilitySystem"));
    AbilitySystem->SetIsReplicated(true);
    AbilitySystem->SetReplicationMode(EGameplayEffectReplicationMode::Mixed);   // §2.3 참조

    Attributes = CreateDefaultSubobject<UMyAttributeSet>(TEXT("Attributes"));   // ASC 가 자동 인식
}

void AMyChar::PossessedBy(AController* NewController)
{
    Super::PossessedBy(NewController);
    AbilitySystem->InitAbilityActorInfo(this, this);   // OwnerActor=this, AvatarActor=this
    GiveDefaultAbilities();   // 서버 권한
}
```

#### 모델 B: PlayerState 에 ASC (MOBA / 멀티플레이어)

```cpp
// AMyPlayerState 에 ASC + Attributes 보유
// AMyChar (Pawn) 는 PlayerState 의 ASC 참조

void AMyChar::PossessedBy(AController* NewController)
{
    Super::PossessedBy(NewController);
    if (AMyPlayerState* PS = GetPlayerState<AMyPlayerState>())
    {
        AbilitySystemComponent = PS->GetAbilitySystemComponent();
        AbilitySystemComponent->InitAbilityActorInfo(PS, this);   // Owner=PS, Avatar=Pawn
    }
}

void AMyChar::OnRep_PlayerState()
{
    Super::OnRep_PlayerState();
    if (AMyPlayerState* PS = GetPlayerState<AMyPlayerState>())
    {
        AbilitySystemComponent = PS->GetAbilitySystemComponent();
        AbilitySystemComponent->InitAbilityActorInfo(PS, this);   // 클라 측
    }
}
```

> **PlayerState 모델의 장점**: 죽고 부활해도 ASC 유지 (Pawn 만 새로 spawn). MOBA / Hero Shooter 표준.

### 2.2 InitAbilityActorInfo — Owner vs Avatar 구분

| Actor | 역할 |
|-------|------|
| **OwnerActor** | ASC 가 부착된 Actor (PlayerState 모델 → PlayerState) |
| **AvatarActor** | 게임 월드 안 시각/물리 Actor (Pawn) |

> **죽음/부활 시** Avatar 만 교체, Owner 유지 → ASC 의 모든 어빌리티/이펙트/태그 보존.

### 2.3 EGameplayEffectReplicationMode — 복제 모드 3종

```cpp
enum class EGameplayEffectReplicationMode : uint8
{
    Full,     // Single Player / Co-op — 모든 GE 가 모든 클라이언트로 복제
    Mixed,    // Multiplayer Player Pawn — GE 가 Owner Client + Server 만, GameplayCue 만 모두에게
    Minimal,  // Multiplayer AI Pawn — GE 자체 복제 안 함, GameplayCue 만 모두에게
};
```

- **Full**: 싱글/Co-op 게임
- **Mixed**: 플레이어 캐릭터 (Owner 가 결과 정확하게 알아야 함 — UI 표시 등)
- **Minimal**: AI / 적 (시각 효과만 보여주고 내부 GE 복제 안 함 — 대역폭 절감)

---

## 3. UAttributeSet — 어트리뷰트

### 3.1 정의 패턴 — 매크로 + Replication

```cpp
// MyAttributeSet.h
#define ATTRIBUTE_ACCESSORS(ClassName, PropertyName) \
    GAMEPLAYATTRIBUTE_PROPERTY_GETTER(ClassName, PropertyName) \
    GAMEPLAYATTRIBUTE_VALUE_GETTER(PropertyName) \
    GAMEPLAYATTRIBUTE_VALUE_SETTER(PropertyName) \
    GAMEPLAYATTRIBUTE_VALUE_INITTER(PropertyName)

UCLASS()
class UMyAttributeSet : public UAttributeSet
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintReadOnly, Category="Health", ReplicatedUsing=OnRep_Health)
    FGameplayAttributeData Health;
    ATTRIBUTE_ACCESSORS(UMyAttributeSet, Health);

    UPROPERTY(BlueprintReadOnly, Category="Health", ReplicatedUsing=OnRep_MaxHealth)
    FGameplayAttributeData MaxHealth;
    ATTRIBUTE_ACCESSORS(UMyAttributeSet, MaxHealth);

    UPROPERTY(BlueprintReadOnly, Category="Mana", ReplicatedUsing=OnRep_Mana)
    FGameplayAttributeData Mana;
    ATTRIBUTE_ACCESSORS(UMyAttributeSet, Mana);

    UFUNCTION()
    virtual void OnRep_Health(const FGameplayAttributeData& OldValue);
    UFUNCTION()
    virtual void OnRep_MaxHealth(const FGameplayAttributeData& OldValue);
    UFUNCTION()
    virtual void OnRep_Mana(const FGameplayAttributeData& OldValue);

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    // PreAttributeChange — 변경 직전 (clamp 위치)
    virtual void PreAttributeChange(const FGameplayAttribute& Attribute, float& NewValue) override;

    // PostGameplayEffectExecute — Effect 실행 후 (Health <= 0 검사 등)
    virtual void PostGameplayEffectExecute(const FGameplayEffectModCallbackData& Data) override;
};

// .cpp
void UMyAttributeSet::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION_NOTIFY(UMyAttributeSet, Health, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UMyAttributeSet, MaxHealth, COND_None, REPNOTIFY_Always);
    DOREPLIFETIME_CONDITION_NOTIFY(UMyAttributeSet, Mana, COND_None, REPNOTIFY_Always);
}

void UMyAttributeSet::OnRep_Health(const FGameplayAttributeData& OldValue)
{
    GAMEPLAYATTRIBUTE_REPNOTIFY(UMyAttributeSet, Health, OldValue);
}

void UMyAttributeSet::PreAttributeChange(const FGameplayAttribute& Attribute, float& NewValue)
{
    Super::PreAttributeChange(Attribute, NewValue);
    if (Attribute == GetHealthAttribute())
    {
        NewValue = FMath::Clamp(NewValue, 0.f, GetMaxHealth());
    }
}

void UMyAttributeSet::PostGameplayEffectExecute(const FGameplayEffectModCallbackData& Data)
{
    Super::PostGameplayEffectExecute(Data);

    if (Data.EvaluatedData.Attribute == GetHealthAttribute())
    {
        SetHealth(FMath::Clamp(GetHealth(), 0.f, GetMaxHealth()));
        if (GetHealth() <= 0.f)
        {
            // 죽음 처리 (Tag 추가 / Death GE 적용)
        }
    }
}
```

### 3.2 PreAttributeChange vs PostGameplayEffectExecute

| 콜백 | 시점 | 용도 |
|------|------|------|
| `PreAttributeChange(Attribute, NewValue&)` | 변경 직전 (모든 변경) | **Clamp** — Health 가 [0, MaxHealth] 안으로 |
| `PostAttributeChange(Attribute, OldValue, NewValue)` | 변경 직후 (모든 변경) | UI 업데이트 트리거 |
| `PreGameplayEffectExecute(Data&)` | GE 실행 전 | Damage 면역 검사 (false 반환 시 GE 무시) |
| `PostGameplayEffectExecute(Data)` | GE 실행 후 (GE 만) | 죽음 / 죽이는 자 (Killer) 추적 |

### 3.3 BaseValue vs CurrentValue

```cpp
struct FGameplayAttributeData
{
    float BaseValue;      // 영구 값 (Instant GE 가 영향)
    float CurrentValue;   // 임시 값 (Duration/Infinite GE 가 영향, 매 갱신)
};
```

> **Instant GE** = BaseValue 변경 (영구 데미지). **Duration/Infinite GE** = CurrentValue 변경 (버프 — 종료 시 BaseValue 로 복원).

---

## 4. UGameplayAbility — 어빌리티

### 4.1 정의 패턴

```cpp
UCLASS()
class UMyDashAbility : public UGameplayAbility
{
    GENERATED_BODY()

public:
    UMyDashAbility()
    {
        InstancingPolicy = EGameplayAbilityInstancingPolicy::InstancedPerActor;   // 권장
        NetExecutionPolicy = EGameplayAbilityNetExecutionPolicy::LocalPredicted;   // 클라 예측 + 서버 검증
        AbilityTags.AddTag(FGameplayTag::RequestGameplayTag("Ability.Dash"));
        BlockAbilitiesWithTag.AddTag(FGameplayTag::RequestGameplayTag("State.Stunned"));
    }

    virtual void ActivateAbility(const FGameplayAbilitySpecHandle Handle,
                                  const FGameplayAbilityActorInfo* ActorInfo,
                                  const FGameplayAbilityActivationInfo ActivationInfo,
                                  const FGameplayEventData* TriggerEventData) override;

    virtual void EndAbility(const FGameplayAbilitySpecHandle Handle,
                             const FGameplayAbilityActorInfo* ActorInfo,
                             const FGameplayAbilityActivationInfo ActivationInfo,
                             bool bReplicateEndAbility, bool bWasCancelled) override;

    virtual bool CanActivateAbility(const FGameplayAbilitySpecHandle Handle,
                                     const FGameplayAbilityActorInfo* ActorInfo,
                                     const FGameplayTagContainer* SourceTags,
                                     const FGameplayTagContainer* TargetTags,
                                     OUT FGameplayTagContainer* OptionalRelevantTags) const override;
};

void UMyDashAbility::ActivateAbility(...)
{
    if (!CommitAbility(Handle, ActorInfo, ActivationInfo))   // Cost (Mana) + Cooldown 적용
    {
        EndAbility(Handle, ActorInfo, ActivationInfo, true, true);
        return;
    }

    // 실제 Dash 로직
    ACharacter* Char = Cast<ACharacter>(ActorInfo->AvatarActor.Get());
    Char->LaunchCharacter(Char->GetActorForwardVector() * 5000.f, true, false);

    EndAbility(Handle, ActorInfo, ActivationInfo, true, false);
}
```

### 4.2 EGameplayAbilityInstancingPolicy

| 정책 | 설명 | 사용 |
|------|------|------|
| `NonInstanced` | CDO 만 사용 — 상태 없음 | 가장 가벼움. 단순 어빌리티 (Stateless) |
| `InstancedPerActor` | Actor 마다 1 인스턴스 | **표준** — 대부분의 어빌리티 |
| `InstancedPerExecution` | 실행마다 새 인스턴스 | 거의 사용 안 함 — 비용 ↑ |

### 4.3 EGameplayAbilityNetExecutionPolicy

| 정책 | 어디서 실행 | 사용 |
|------|------------|------|
| `LocalOnly` | 클라이언트만 | UI 어빌리티 |
| `LocalPredicted` | 클라 예측 + 서버 검증 | **표준** — 대부분의 어빌리티 (즉각 반응 + 권위 보정) |
| `ServerInitiated` | 서버 시작 → 클라 알림 | 서버 권위 (Boss AI 어빌리티) |
| `ServerOnly` | 서버만 | 데미지 적용 등 |

### 4.4 CommitAbility = Cost + Cooldown

```cpp
// UMyDashAbility 의 GameplayEffect 자식
UPROPERTY(EditDefaultsOnly, Category="Costs")
TSubclassOf<UGameplayEffect> CostGE;       // Mana -50

UPROPERTY(EditDefaultsOnly, Category="Cooldowns")
TSubclassOf<UGameplayEffect> CooldownGE;   // 5초 동안 "Cooldown.Dash" 태그 추가

// CommitAbility 내부:
// 1. CheckCost (Cost GE 의 Mana >= 50 검사)
// 2. CheckCooldown (Cooldown 태그 없는지 검사)
// 3. ApplyCost (Mana -= 50)
// 4. ApplyCooldown (Cooldown.Dash 태그 추가, 5초 후 자동 제거)
```

### 4.5 GiveAbility / TryActivateAbility (Server)

```cpp
// 서버 측 — 어빌리티 부여
FGameplayAbilitySpec Spec(UMyDashAbility::StaticClass(), 1, INPUT_DASH);
FGameplayAbilitySpecHandle Handle = AbilitySystem->GiveAbility(Spec);

// 활성화 (어디서든)
AbilitySystem->TryActivateAbilityByClass(UMyDashAbility::StaticClass());
// 또는 태그로
AbilitySystem->TryActivateAbilitiesByTag(FGameplayTagContainer(FGameplayTag::RequestGameplayTag("Ability.Dash")));
```

---

## 5. FGameplayEffect — 이펙트 (BP 에셋)

> **GE 는 코드 작성 거의 안 함** — Blueprint 에셋 (`UGameplayEffect` 자식 BP) 으로 정의. C++ 에서는 `TSubclassOf<UGameplayEffect>` 로 참조.

### 5.1 GE 구성 요소

| 항목 | 설명 |
|------|------|
| **Duration Type** | Instant / Duration / Infinite |
| **Modifiers** | 어트리뷰트 변경 (예: `Health -= Magnitude`) |
| **Modifier Op** | Add / Multiply / Divide / Override |
| **Magnitude Calc** | Scalable Float / Attribute Based / Set By Caller / Custom |
| **Stacking** | None / Aggregate by Source / Aggregate by Target |
| **Stack Limit** | 최대 중첩 |
| **Granted Tags** | GE 가 적용된 동안 부여할 태그 |
| **Ongoing Tag Requirements** | 이 태그 있어야 GE 동작 |
| **Removal Tag Requirements** | 이 태그 부여 시 GE 제거 |
| **Period** | Periodic GE (DoT — Damage over Time) — 매 N 초마다 적용 |

### 5.2 ApplyGameplayEffectToSelf / ToTarget

```cpp
// 자신에게 적용 (예: Heal)
FGameplayEffectContextHandle Context = AbilitySystem->MakeEffectContext();
FGameplayEffectSpecHandle Spec = AbilitySystem->MakeOutgoingSpec(HealGE, /*Level=*/1, Context);
AbilitySystem->ApplyGameplayEffectSpecToSelf(*Spec.Data.Get());

// 타겟에게 적용 (예: Damage)
UAbilitySystemComponent* TargetASC = TargetActor->FindComponentByClass<UAbilitySystemComponent>();
AbilitySystem->ApplyGameplayEffectSpecToTarget(*Spec.Data.Get(), TargetASC);

// 또는 SetByCaller (런타임 magnitude 결정)
Spec.Data->SetSetByCallerMagnitude(FGameplayTag::RequestGameplayTag("Data.Damage"), 100.f);
```

### 5.3 GameplayEffectExecutionCalculation — 복잡한 계산

```cpp
UCLASS()
class UDamageExecution : public UGameplayEffectExecutionCalculation
{
    virtual void Execute_Implementation(const FGameplayEffectCustomExecutionParameters& ExecutionParams,
                                         OUT FGameplayEffectCustomExecutionOutput& OutExecutionOutput) const override
    {
        // Source AttackPower vs Target Armor → 최종 Damage 계산
        const FGameplayEffectSpec& Spec = ExecutionParams.GetOwningSpec();

        float SourceAttack = 0.f;
        // ... CaptureAttribute 정의 후 GetCapturedAttributeMagnitude

        float Damage = ComputeFinalDamage(SourceAttack, TargetArmor);

        OutExecutionOutput.AddOutputModifier(
            FGameplayModifierEvaluatedData(UMyAttributeSet::GetHealthAttribute(),
                                           EGameplayModOp::Additive, -Damage));
    }
};
```

---

## 6. FGameplayTag — 태그 시스템

### 6.1 정의

```cpp
// DefaultGameplayTags.ini 또는 GameplayTagsManager 코드 등록
"Ability.Dash"
"Ability.Combat.Attack.Light"
"State.Stunned"
"State.Dead"
"Event.Damage.Critical"
"Cooldown.Dash"
```

### 6.2 사용 패턴

```cpp
// 태그 가져오기
static const FGameplayTag StunTag = FGameplayTag::RequestGameplayTag("State.Stunned");

// 태그 추가/제거
AbilitySystem->AddLooseGameplayTag(StunTag);    // GE 없이 직접 추가 (복제 안 됨)
AbilitySystem->RemoveLooseGameplayTag(StunTag);

// 검사
if (AbilitySystem->HasMatchingGameplayTag(StunTag)) { /* 스턴 상태 */ }

// 컨테이너
FGameplayTagContainer DamageTags;
DamageTags.AddTag(FGameplayTag::RequestGameplayTag("Event.Damage"));
DamageTags.AddTag(FGameplayTag::RequestGameplayTag("Event.Damage.Critical"));
```

### 6.3 GameplayCue — 시각/사운드 효과 트리거

```cpp
// 클라이언트에서 자동 재생되는 효과 (서버 → 클라 복제)
AbilitySystem->ExecuteGameplayCue(FGameplayTag::RequestGameplayTag("GameplayCue.Damage.Hit"),
                                   ContextHandle);

// AGameplayCueNotify_Static 또는 AGameplayCueNotify_Actor BP 가 자동 응답
```

> **GameplayCue = Cosmetic 전용** — Mixed/Minimal Replication 모드에서도 항상 복제. Cue Manager 가 자동 라우팅.

---

## 7. 표준 흐름 — 데미지 적용

```
[Pawn A: Player] Input → ActivateAbility(AttackAbility)
  ↓ AttackAbility 가 Hit 검출 (Trace)
  ↓ Hit Actor (Pawn B) 의 ASC 가져오기
  ↓ FGameplayEffectSpec 생성 (DamageGE, Level)
  ↓ Spec->SetSetByCallerMagnitude("Data.Damage", 100.f)
  ↓ AttackerASC->ApplyGameplayEffectSpecToTarget(Spec, TargetASC)
[ASC Target] ApplyGameplayEffectSpec
  ↓ DamageExecution (Calc) — Source AttackPower vs Target Armor
  ↓ PreGameplayEffectExecute (자식 override — 면역 검사)
  ↓ Health 변경
    ↓ PreAttributeChange (Clamp [0, MaxHealth])
    ↓ Health.SetCurrentValue(NewValue)
  ↓ PostGameplayEffectExecute (자식 override — 죽음 검사)
    ↓ if (Health <= 0) → AbilitySystem->AddLooseGameplayTag("State.Dead")
  ↓ GameplayCue 재생 (모든 클라 — 피격 이펙트/사운드)
```

---

## 8. ASC 활성화 위치 — 표준 패턴

| 위치 | 사용 |
|------|------|
| **PossessedBy** (Server) | Server 측 ASC 초기화 |
| **OnRep_PlayerState** (Client) | Client 측 ASC 초기화 (PlayerState 모델) |
| **PostInitializeComponents** (Both) | 단순 (Pawn 모델, 비복제) |

### 8.1 표준 ASC 초기화

```cpp
// AMyChar — Pawn 모델
void AMyChar::PossessedBy(AController* NewController)
{
    Super::PossessedBy(NewController);
    AbilitySystem->InitAbilityActorInfo(this, this);

    if (HasAuthority())   // Server only
    {
        // 기본 어빌리티 부여
        for (TSubclassOf<UGameplayAbility> Ab : DefaultAbilities)
        {
            AbilitySystem->GiveAbility(FGameplayAbilitySpec(Ab, 1, INDEX_NONE, this));
        }
        // 시작 GE (Health/Mana 초기화)
        FGameplayEffectContextHandle Ctx = AbilitySystem->MakeEffectContext();
        FGameplayEffectSpecHandle Spec = AbilitySystem->MakeOutgoingSpec(StartupGE, 1, Ctx);
        AbilitySystem->ApplyGameplayEffectSpecToSelf(*Spec.Data.Get());
    }
}
```

---

## 9. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | ASC 의 `InitAbilityActorInfo` 안 호출 | `PossessedBy` (서버) + `OnRep_PlayerState` (클라) 둘 다 호출 의무 |
| 2 | AttributeSet 의 `OnRep_*` 함수 시그니처 잘못 | `(const FGameplayAttributeData& OldValue)` 정확히 |
| 3 | `GAMEPLAYATTRIBUTE_REPNOTIFY` 호출 누락 | `OnRep_*` 안 첫 줄 의무 — UI 갱신 트리거 |
| 4 | Health 변경을 `SetHealth` 직접 사용 (BP) | 표준은 GameplayEffect — 직접 set 은 PreAttributeChange/Post 콜백 우회 |
| 5 | `LocalPredicted` 어빌리티에서 서버 권위 데이터 사용 | 클라 예측 안 가능한 데이터 (ServerOnly 어빌리티로) |
| 6 | InstancingPolicy = `NonInstanced` 인데 멤버 변수 사용 | NonInstanced = CDO 만 — 멤버 = 모든 Actor 공유 (race) |
| 7 | GameplayTag string literal 매번 `RequestGameplayTag` | `static const FGameplayTag X = ...` 캐시 |
| 8 | Mixed Replication + AI 캐릭터 | AI 는 Minimal — 대역폭 절감 |
| 9 | GameplayCue 를 데미지 계산에 사용 | Cue = Cosmetic 만. 데미지는 GameplayEffect Modifier |
| 10 | 🚨 Ability `ActivateAbility` 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` ([`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md)) |
| 11 | 🚨 Ability 안 `TActorIterator` 로 타겟 검색 | `OverlapMulti` 또는 Subsystem ([`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md)) |

---

## 10. 체크리스트

- [ ] Build.cs 에 `GameplayAbilities` + `GameplayTags` + `GameplayTasks` 추가
- [ ] `IAbilitySystemInterface` 구현 (Owner Actor)
- [ ] `InitAbilityActorInfo` 서버/클라 둘 다 호출
- [ ] AttributeSet: `OnRep_*` + `GAMEPLAYATTRIBUTE_REPNOTIFY` + `GetLifetimeReplicatedProps`
- [ ] AttributeSet: `PreAttributeChange` (Clamp) + `PostGameplayEffectExecute` (죽음 등)
- [ ] Ability: `InstancingPolicy = InstancedPerActor`
- [ ] Ability: `NetExecutionPolicy = LocalPredicted` (대부분)
- [ ] Ability: `CommitAbility` 호출 (Cost + Cooldown)
- [ ] GameplayEffect: BP 에셋으로 정의 (Damage/Heal/Buff)
- [ ] GameplayTag: `static const FGameplayTag` 캐시
- [ ] GameplayCue: 시각/사운드 효과만 (데미지 계산 X)
- [ ] Replication Mode: Player = Mixed, AI = Minimal, SinglePlayer = Full
- [ ] 🚨 Ability ActivateAbility 첫 줄 프로파일링 스코프
- [ ] 🚨 Ability 안 TActorIterator 안 씀

---

## 11. 관련 문서

- [`Components/SKILL.md`](../Components/SKILL.md) — UAbilitySystemComponent 도 UActorComponent 자손
- [`skills/CoreUObject/Network`](../CoreUObject/references/Network.md) — DOREPLIFETIME / OnRep 패턴
- [`skills/CoreUObject/Reflection`](../CoreUObject/references/Reflection.md) — UCLASS / UPROPERTY
- [`references/07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — Ability 콜백 스코프
- [`references/10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) — 6대 정책 (ASC = UActorComponent)

---

## 12. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. UAbilitySystemComponent (Pawn vs Playe