---
type: synthesis
title: "GAS 의 Pawn vs PlayerState 모델 결정 — UAbilitySystemComponent 호스트 위치 결정 트리"
slug: gas-pawn-vs-playerstate-decision
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-gas-skill]]"
  - "[[sources/ue-gameframework-pawncharacter]]"
  - "[[sources/ue-gameframework-gamemode]]"
  - "[[sources/ue-gameframework-controller]]"
  - "[[sources/ue-networking-skill]]"
entities:
  - "[[entities/UAbilitySystemComponent]]"
  - "[[entities/UAttributeSet]]"
  - "[[entities/UGameplayAbility]]"
  - "[[entities/APawn]]"
  - "[[entities/ACharacter]]"
  - "[[entities/AGameStateBase]]"
concepts:
  - "[[concepts/Possession]]"
  - "[[concepts/Authority-NetMode]]"
  - "[[concepts/Replication]]"
  - "[[concepts/SeamlessTravel]]"
status: living
tags: [synthesis, gas, abilitysystem, playerstate, pawn]
---

# GAS 의 Pawn vs PlayerState 모델 결정

## 1. Thesis

`UAbilitySystemComponent` (ASC) 의 호스트는 **`APawn` (Pawn 모델, MOBA / FPS / 액션)** 또는 **`APlayerState` (PlayerState 모델, MMORPG / 영구 능력)** 중 하나. 결정은 *능력 / 어트리뷰트가 Pawn 의 죽음 / 변경 (탈것 탑승, 캐릭터 swap) 을 어떻게 살아남는가* 단 하나의 질문으로 좁혀짐. 본 synthesis 는 두 모델의 장단점 + 결정 트리 + 마이그레이션 비용 + 흔한 함정. [[sources/ue-gas-skill]] §결정 트리 + [[sources/ue-gameframework-controller]] (PlayerController + PlayerState) + [[concepts/Possession]] 통합.

## 2. 두 모델 매트릭스

| 항목 | Pawn 모델 | PlayerState 모델 |
| -- | -- | -- |
| ASC 호스트 | `ACharacter` / `APawn` | `APlayerState` |
| 죽음 (Possess 끊김) | ASC 도 Destroy → AttributeSet 사라짐 | ASC 살아남음 — 새 Pawn 으로 transfer |
| 캐릭터 swap | ASC 새로 — 능력 새로 부여 | ASC 유지 — 캐릭터별 효과만 reapply |
| 탈것 탑승 | 탈것 별도 ASC (또는 Possess 변경) | Pawn 만 변경, ASC 유지 |
| 게임 종료 영구 진행 | Save/Load 외부 처리 | Save/Load 외부 처리 (PlayerState 도 Map 전환 시 새로) |
| AI / NPC | 그대로 작동 (PlayerState 없음) | NPC 는 ASC 를 Pawn 에 둬야 |
| 적합 장르 | MOBA (DOTA / LoL — 챔피언 1개) / FPS / 액션 | MMORPG (WoW — 캐릭터 영구 진행) / RPG |

## 3. 결정 트리

```
이 게임에서 *능력 / 어트리뷰트가 Pawn 의 일생을 넘어 지속* 되어야 하나?
├── 아니오 (캐릭터 = 능력 = 한 묶음. 죽으면 다 새로)
│   └── Pawn 모델 → ACharacter 안 ASC
│       장점: 단순, AI / NPC 동일 코드
│       단점: 죽음 / 탈것 / swap 시 ASC 재초기화 비용
│
└── 예 (캐릭터는 변하지만 능력 / 능력치는 유지)
    └── PlayerState 모델 → APlayerState 안 ASC
        장점: 죽어도 능력 살아남음, 캐릭터 swap 부드러움
        단점: AI / NPC 는 Pawn 에 따로 ASC, PlayerState 설정 복잡
        
# 보조 질문:
[Q1] AI / NPC 가 ASC 사용? 
     → 예 → PlayerState 모델이라도 NPC 는 Pawn 에 ASC (이중 표준)
[Q2] 멀티플레이?
     → 예 → 둘 다 OK (RepNotify 셋업만 다름)
[Q3] Possess 자주 변경?
     → 예 → PlayerState 모델 강력 권장
```

## 4. 셋업 차이

### Pawn 모델

```cpp
class AMyChar : public ACharacter, public IAbilitySystemInterface
{
    UPROPERTY(VisibleAnywhere) TObjectPtr<UAbilitySystemComponent> ASC;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UMyAttributeSet> Attributes;

    AMyChar() {
        ASC = CreateDefaultSubobject<UAbilitySystemComponent>(TEXT("ASC"));
        ASC->SetIsReplicated(true);
        ASC->SetReplicationMode(EGameplayEffectReplicationMode::Mixed);
        Attributes = CreateDefaultSubobject<UMyAttributeSet>(TEXT("Attr"));
    }
    virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override { return ASC; }

    virtual void BeginPlay() override {
        Super::BeginPlay();
        ASC->InitAbilityActorInfo(this, this);   // Owner = Avatar = self
    }
};
```

### PlayerState 모델

```cpp
class AMyPlayerState : public APlayerState, public IAbilitySystemInterface
{
    UPROPERTY(VisibleAnywhere) TObjectPtr<UAbilitySystemComponent> ASC;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UMyAttributeSet> Attributes;

    AMyPlayerState() {
        ASC = CreateDefaultSubobject<UAbilitySystemComponent>(TEXT("ASC"));
        ASC->SetIsReplicated(true);
        ASC->SetReplicationMode(EGameplayEffectReplicationMode::Mixed);
        Attributes = CreateDefaultSubobject<UMyAttributeSet>(TEXT("Attr"));
        // PlayerState 는 NetUpdateFrequency 100Hz 강제 (replication 누락 회피)
        NetUpdateFrequency = 100.f;
    }
};

class AMyChar : public ACharacter, public IAbilitySystemInterface
{
    virtual UAbilitySystemComponent* GetAbilitySystemComponent() const override
    {
        return Cast<AMyPlayerState>(GetPlayerState())->GetAbilitySystemComponent();
    }

    virtual void PossessedBy(AController* NewController) override {  // Server
        Super::PossessedBy(NewController);
        InitASC();
    }
    virtual void OnRep_PlayerState() override {                       // Client
        Super::OnRep_PlayerState();
        InitASC();
    }
    void InitASC() {
        if (auto* PS = Cast<AMyPlayerState>(GetPlayerState())) {
            UAbilitySystemComponent* ASC = PS->GetAbilitySystemComponent();
            ASC->InitAbilityActorInfo(PS, this);   // Owner = PlayerState, Avatar = Pawn
        }
    }
};
```

핵심 — `InitAbilityActorInfo(Owner, Avatar)` 의 두 인자가 **다름**. Pawn 모델은 둘 다 self, PlayerState 모델은 Owner=PS / Avatar=Pawn.

## 5. 함정 / 열린 질문

- [ ] **PlayerState 모델 + Possess 시점 race** — Server `PossessedBy` vs Client `OnRep_PlayerState` 순서 보장 X. 둘 다에 InitASC 등록 의무 + idempotent
- [ ] **PlayerState 의 NetUpdateFrequency** — 디폴트 1Hz. ASC 의 GameplayEffect / Tag 변경이 누락됨. **100Hz 강제** 의무
- [ ] **AI / NPC 의 일관성** — PlayerState 모델 채택해도 NPC 는 Pawn 에 ASC. 두 패턴 공존 → 헬퍼 함수 (`UAbilitySystemBlueprintLibrary::GetAbilitySystemComponent(Actor)`) 가 chain 검사
- [ ] **SeamlessTravel + PlayerState** ([[concepts/SeamlessTravel]]) — 일부 데이터만 살아남음 (`bIsInactive` 마킹). 능력 / 어트리뷰트 transfer 절차 별도 ([[sources/ue-gameframework-controller]])
- [ ] **Replication mode 선택** — `Full` (모두 모든 GE 봄) / `Mixed` (자기 GE 만 자세히, 남의 건 Tag 만) / `Minimal` (자기 GE 만). 멀티플레이어 밸런스 게임은 Mixed 표준
- [ ] **GameplayCue 적용 위치** — Pawn / PlayerState 어디서 트리거하든 GameplayCueManager 가 처리. Cue 자체는 *visual cosmetic* 으로 NetMulticast (열린)
- [ ] **MOBA 스킬 swap** — Pawn 모델 + 능력만 추가/제거 (`GiveAbility` / `ClearAbility`). PlayerState 모델은 Pawn 변경 시점에 reapply (열린)

## 6. 관련

### Sources

[[sources/ue-gas-skill]] · [[sources/ue-gameframework-pawncharacter]] · [[sources/ue-gameframework-gamemode]] · [[sources/ue-gameframework-controller]] · [[sources/ue-networking-skill]]

### Entities

[[entities/UAbilitySystemComponent]] · [[entities/UAttributeSet]] · [[entities/UGameplayAbility]] · [[entities/APawn]] · [[entities/ACharacter]] · [[entities/AGameStateBase]]

### Concepts

[[concepts/Possession]] · [[concepts/Authority-NetMode]] · [[concepts/Replication]] · [[concepts/SeamlessTravel]]

### Related synthesis

[[synthesis/server-vs-client-rpc-decision-tree]] (GAS RPC / Replication 셋업) · [[synthesis/subsystem-5-types-decision-tree]] (PlayerState vs GameInstance vs LocalPlayer Subsystem 결정과 페어) · [[synthesis/component-vs-actor-lifecycle-table]] (Pawn / PlayerState 의 BeginPlay / Possess 순서) · [[synthesis/gas-advanced-runtime-patterns]] (GameplayCue / 스킬 swap / SeamlessTravel transfer)
