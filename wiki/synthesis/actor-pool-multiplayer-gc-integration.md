---
type: synthesis
title: "Actor Pool 멀티플레이 + GC 통합 — Replicated Pool + Niagara Pool 결합 + 한도 초과 정책"
slug: actor-pool-multiplayer-gc-integration
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/ue-gameframework-actor]]"
  - "[[sources/ue-networking-skill]]"
  - "[[sources/ue-coreuobject-gc]]"
  - "[[sources/ue-niagara-skill]]"
  - "[[sources/ue-significance-skill]]"
entities:
  - "[[entities/AActor]]"
  - "[[entities/UNiagaraSystem]]"
  - "[[entities/UNetDriver]]"
  - "[[entities/USignificanceManager]]"
concepts:
  - "[[concepts/Replication]]"
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, actor-pool, multiplayer, gc, niagara-pool, overflow]
---

# Actor Pool 멀티플레이 + GC 통합

## 1. Thesis

[[synthesis/actor-pool-reset-pattern]] 의 3 미해결 — **(1) Replicated Pool — NetGUID 매번 새로 → channel destroy/recreate 비효율 / (2) Niagara Pool 와 결합 — Pool actor 안 NiagaraComponent 의 AutoRelease 가 Pool actor Reset 과 동기 / (3) Pool 한도 초과 정책 — 새 SpawnActor (Warning) vs 가장 오래된 Active force reset)**. 본 synthesis 는 3 축의 결정 트리 + 표준 패턴 + 함정. 결론 — **Replicated Pool 은 *Dormancy + Custom NetSerialize* 로 해결, Niagara Pool 는 Reset/OnDeactivate 안 명시 호출, 한도 초과는 *force reset* (LRU) 권장**.

## 2. (1) Replicated Pool 패턴

기본 Pool 은 *같은 AActor 인스턴스 재사용* → Server replicate 시 *NetGUID 동일 유지*. 하지만 Channel 은 destroy 안 되므로 클라가 *옛 상태* 가진 채 새 사용:

```cpp
// 클라가 Bullet1 의 Activate(Loc1) 받음 → 표시
// Bullet1 Deactivate → Channel 유지 (Dormancy)
// Bullet1 Activate(Loc2) → 새 위치 — 클라는 *Loc1 → Loc2 의 부드러운 보간* 시도 (망상)
```

**해결**:
```cpp
// (a) Activate 시 NetDormancy 깨우기 + 즉시 Replicate
virtual void Activate(const FTransform& W) override
{
    Super::Activate(W);
    if (HasAuthority()) {
        SetNetDormancy(DORM_Awake);
        FlushNetDormancy();    // 다음 frame 즉시 Replicate
        ForceNetUpdate();
    }
}

// (b) Deactivate 시 Dormancy
virtual void Deactivate() override
{
    if (HasAuthority()) {
        SetNetDormancy(DORM_DormantAll);
    }
    Super::Deactivate();
}

// (c) Replicated 상태 — bIsPoolActive UPROPERTY
UPROPERTY(ReplicatedUsing=OnRep_PoolActive)
bool bIsPoolActive = false;

void OnRep_PoolActive()
{
    if (bIsPoolActive) {
        SetActorHiddenInGame(false);
        SetActorEnableCollision(true);
        Reset();   // 클라가 자체 Reset
    } else {
        SetActorHiddenInGame(true);
        SetActorEnableCollision(false);
    }
}
```

[[synthesis/replication-graph-bandwidth-management]] 의 Dormancy 와 결합 — Pool deactive = `DORM_DormantAll` 로 bandwidth 0.

## 3. (2) Niagara Pool 결합

Pool Actor 안 `UNiagaraComponent` 가 자체 ENCPoolMethod::AutoRelease — Pool actor reset 시 Niagara 도 *깨끗하게* reset:

```cpp
class AMCBullet : public AMCPooledActor
{
    UPROPERTY() TObjectPtr<UNiagaraComponent> TrailVFX;

    AMCBullet() {
        TrailVFX = CreateDefaultSubobject<UNiagaraComponent>(TEXT("Trail"));
        TrailVFX->SetAutoActivate(false);
        // NCPoolMethod::AutoRelease 자동 — Component 단위 Pool ([[synthesis/vfx-audio-soft-pool-significance]])
    }

    virtual void Reset() override
    {
        TrailVFX->ResetSystem();     // 파티클 큐 비움
        TrailVFX->Activate(/*bReset=*/true);
    }

    virtual void OnDeactivate() override
    {
        TrailVFX->Deactivate();      // Niagara Pool 에 반환
    }
};
```

**중요** — Niagara 의 `bAutoDestroy=false` 강제 (Pool actor 의 자식이므로 actor destroy 와 동기 — Niagara 가 먼저 destroy 되면 안 됨).

## 4. (3) Pool 한도 초과 — LRU force reset

[[synthesis/actor-pool-reset-pattern]] 의 미해결 — *새 SpawnActor (Warning)* vs *가장 오래된 Active 재사용*. 게임 종류 결정:

```cpp
class UMCBulletPool : public UWorldSubsystem
{
    UPROPERTY() TArray<TObjectPtr<AMCPooledActor>> Available;
    UPROPERTY() TArray<TObjectPtr<AMCPooledActor>> Active;
    TMap<AMCPooledActor*, double> ActivationTime;   // LRU 추적

    AMCPooledActor* Acquire(const FTransform& W)
    {
        if (Available.Num() > 0) {
            AMCPooledActor* A = Available.Pop();
            Active.Add(A); ActivationTime.Add(A, FPlatformTime::Seconds());
            A->Activate(W);
            return A;
        }

        // === 한도 초과 정책 ===
        // 옵션 A: 새 SpawnActor (느림 — Warning)
        // UE_LOG(LogMCAsset, Warning, TEXT("Pool capacity exceeded — new spawn (slow)"));
        // UClass* Cls = PooledClass.LoadSynchronous();
        // AActor* New = GetWorld()->SpawnActor<AActor>(Cls, W);

        // 옵션 B: LRU force reset (즉시 — 추천)
        AMCPooledActor* Oldest = nullptr;
        double OldestTime = DBL_MAX;
        for (auto& Pair : ActivationTime) {
            if (Pair.Value < OldestTime) { OldestTime = Pair.Value; Oldest = Pair.Key; }
        }
        if (Oldest) {
            Oldest->Deactivate();
            Oldest->Activate(W);   // 즉시 재사용
            ActivationTime[Oldest] = FPlatformTime::Seconds();
            UE_LOG(LogMCAsset, Verbose, TEXT("Pool LRU force reset — oldest bullet recycled"));
            return Oldest;
        }
        return nullptr;
    }
};
```

**결정 트리**:
| 게임 유형 | 정책 |
| -- | -- |
| 시각적 필요한 wave / 폭발 효과 | LRU force reset (Visibility 우선) |
| 정확한 hit detection 필요 (총알이 사라지면 안 됨) | 새 SpawnActor (Warning + 풀 크기 조정 권장) |
| 모바일 / 저사양 | LRU force reset 의무 (메모리 제한) |

## 5. GC 통합

Pool 의 `TArray<TObjectPtr<>>` 가 hard ref → Pool 살아있는 동안 actor 들 GC 안 됨. 게임 종료 시:

```cpp
// World destroy → World Subsystem (Pool) Deinitialize → 자동 cleanup
virtual void Deinitialize() override
{
    for (AMCPooledActor* A : Available) {
        if (A) A->Destroy();
    }
    for (AMCPooledActor* A : Active) {
        if (A) A->Destroy();
    }
    Available.Empty();
    Active.Empty();
    Super::Deinitialize();
}
```

**Streaming Map 전환 시** — World Subsystem 새로 → Pool 도 새로 spawn — 옛 actor 들 정상 GC. SeamlessTravel 시는 PlayerState 만 살아남으므로 Pool 도 새로.

## 6. 함정 / 열린 질문

- [ ] **NetGUID 재사용의 *Late Join 부작용*** — 새 클라가 합류 시 Bullet1 이 *Initial Replication* 으로 옛 Dormant 상태 전송 → 합류 클라는 사라진 총알 본다 가정. `bIsPoolActive=false` 면 Initial Rep 도 skip (`bRelevantForNetworkReplays=false`)
- [ ] **LRU force reset 시 *예측 불가능* 사라짐** — 플레이어가 보던 총알이 갑자기 fade — 시각적 부자연스러움. 거리 가까운 actor 는 force reset 제외 (Significance score 검사)
- [ ] **Niagara `bAutoDestroy=false` 강제** — UPROPERTY meta 또는 Constructor 명시 — 위배 시 Pool 첫 사용 후 Component 사라짐
- [ ] **Replicated Pool + GAS** — Pool actor 가 ASC 보유 (GAS NPC) — Dormancy + ASC Replicate Mode = Mixed 충돌 가능. ASC 보유 actor 는 Pool 제외 또는 명시 검증
- [ ] **GC 타이밍 — *Deinitialize* 호출 시점 vs Streaming Sub-level Unload** — Sub-level 의 actor 는 Sub-level Unload 와 함께 destroy. Pool 이 sub-level reference 가지면 Unload 차단
- [ ] **Pool actor 의 *Component Tick 동기*** — `SetActorTickEnabled(false)` 해도 NiagaraComponent / CharacterMovementComponent 등은 별도 Tick. `PrimaryComponentTick.bCanEverTick=false` 또는 SetComponentTickEnabled(false) 명시
- [ ] **Pool 크기 *동적 조정*** — 게임 시작 시 32 → 진행 중 100 필요. 동적 확장 vs 미리 큰 풀 (메모리). 게임 디자인 결정 (열린)
- [ ] **Niagara Pool overflow 시 fallback** — `UNiagaraComponentPool::SetWorldParticleSystemPoolSettings` 의 한도 초과 → spawn 거절 → Pool actor 의 VFX 없음 (시각 누락). 별도 fallback 로깅 (열린)

## 7. 관련

### Sources

[[sources/ue-gameframework-actor]] · [[sources/ue-networking-skill]] · [[sources/ue-coreuobject-gc]] · [[sources/ue-niagara-skill]] · [[sources/ue-significance-skill]]

### Entities

[[entities/AActor]] · [[entities/UNiagaraSystem]] · [[entities/UNetDriver]] · [[entities/USignificanceManager]]

### Concepts

[[concepts/Replication]] · [[concepts/Garbage-Collection]] · [[concepts/Component-Policies-6]] · [[concepts/MC-Asset-Validation-Policy]]

### Related synthesis

[[synthesis/actor-pool-reset-pattern]] (베이스 — Pool 골격) · [[synthesis/vfx-audio-soft-pool-significance]] (Niagara Pool) · [[synthesis/replication-graph-bandwidth-management]] (Dormancy + Pool 결합)
