---
type: synthesis
title: "Ragdoll 멀티플레이 Replication 표준 — cosmetic-only vs Authority 결정 + FastArraySerializer + 멀티 본 누적 피격"
slug: ragdoll-multiplayer-replication
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
  - "[[sources/ue-networking-skill]]"
  - "[[sources/ue-coreuobject-network]]"
  - "[[sources/ue-components-physicscomponents]]"
  - "[[sources/ue-gameframework-pawncharacter]]"
entities:
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/UNetDriver]]"
  - "[[entities/AActor]]"
  - "[[entities/APlayerController]]"
concepts:
  - "[[concepts/Authority-NetMode]]"
  - "[[concepts/Replication]]"
  - "[[concepts/RPC]]"
  - "[[concepts/PushModel]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, ragdoll, networking, replication, multiplayer]
---

# Ragdoll 멀티플레이 Replication 표준

## 1. Thesis

멀티플레이 ragdoll 은 *비용/정확도/대역폭* 의 trade-off — 3 가지 모드에서 결정 — **(A) cosmetic-only** (각 클라가 독립 시뮬, 실제 본 위치 다를 수 있음) / **(B) Multicast trigger** (Server 가 ragdoll 시작/끝 RPC 만 broadcast, 본 위치는 각 클라 시뮬) / **(C) Server-authoritative bone transform** (Server 가 본 위치 매 프레임 replicate, FastArraySerializer 로 N 본 묶음)**. 99% 게임은 (B) 가 정답 — 시뮬은 deterministic 하지 않지만 cosmetic 차이는 인지 불가. (C) 는 hit detection / 죽은 캐릭터 위에서 추가 게임플레이 (예: loot drop) 가 정확한 본 위치를 요구할 때만. 본 synthesis 는 결정 트리 + FastArraySerializer 셋업 + 멀티 본 누적 피격 패턴.

## 2. 3 모드 매트릭스

| 모드 | 본 위치 정확도 | 대역폭 | 구현 비용 | 적합 |
| -- | -- | -- | -- | -- |
| (A) cosmetic-only | 클라마다 다름 | 0 | 저 | 사망 후 재생 안 되는 ragdoll, 가까이 안 봐도 됨 |
| (B) Multicast trigger | 큰 흐름은 동일, 본은 다름 | 작음 (RPC 1개) | 중 | 99% 게임 — 사망 ragdoll, hit reaction |
| (C) Server-authoritative | 정확 | 큼 (본 N 개 × 매 프레임) | 고 | hit detection, looting, 정밀 게임플레이 |

## 3. (B) Multicast Trigger 표준 패턴

```cpp
class AMyChar : public ACharacter
{
    UFUNCTION(NetMulticast, Reliable)
    void MulticastEnableRagdoll(FVector_NetQuantize HitLocation, FVector_NetQuantizeNormal HitDir, float Strength);

    void Server_OnDeath()  // Authority only
    {
        if (HasAuthority()) {
            MulticastEnableRagdoll(HitLoc, HitDir, Strength);
        }
    }

    void MulticastEnableRagdoll_Implementation(FVector_NetQuantize HitLoc, FVector_NetQuantizeNormal HitDir, float Strength)
    {
        // Server + 모든 Client 에서 동일 호출
        if (UMCSoftSkeletalMeshComponent* M = Cast<UMCSoftSkeletalMeshComponent>(GetMesh())) {
            M->OnHitReceived(NAME_None, HitDir, Strength, NAME_None, /*bUseFullRagdoll=*/true);
        }
    }
};
```

핵심:
- `FVector_NetQuantize` / `FVector_NetQuantizeNormal` — 정밀도 줄여 대역폭 감소 ([[sources/ue-coreuobject-network]] §FNetQuantize)
- `Reliable` — ragdoll trigger 는 1번뿐이라 Reliable 안전. 잃으면 캐릭터 안 쓰러짐
- 본 위치 자체는 *각 클라가 시뮬* — 작은 차이 발생하지만 cosmetic OK

## 4. (C) Server-Authoritative — FastArraySerializer

본 N 개 (40~80) × 매 프레임 transform replicate 는 비싸다. *변경된 본만* replicate:

```cpp
USTRUCT() struct FBoneSnapshot : public FFastArraySerializerItem
{
    GENERATED_BODY()
    UPROPERTY() FName BoneName;
    UPROPERTY() FVector_NetQuantize Location;
    UPROPERTY() FQuat Rotation;
    void PostReplicatedAdd(const struct FBoneSnapshotArray& InArr);
    void PostReplicatedChange(const struct FBoneSnapshotArray& InArr);
};

USTRUCT() struct FBoneSnapshotArray : public FFastArraySerializer
{
    GENERATED_BODY()
    UPROPERTY() TArray<FBoneSnapshot> Items;
    bool NetDeltaSerialize(FNetDeltaSerializeInfo& Params)
    { return FFastArraySerializer::FastArrayDeltaSerialize<FBoneSnapshot>(Items, Params, *this); }
};

template<> struct TStructOpsTypeTraits<FBoneSnapshotArray> : public TStructOpsTypeTraitsBase2<FBoneSnapshotArray>
{ enum { WithNetDeltaSerializer = true }; };
```

[[sources/ue-coreuobject-network]] 의 FastArraySerializer §. Server 가 매 프레임 본 위치 변경 detection 후 변경된 본만 replicate. 클라이언트 `PostReplicatedChange` 콜백에서 `SetBoneTransformByName`.

## 5. 멀티 본 누적 피격

[[synthesis/mc-character-hit-reaction-pipeline]] §4 의 미해결 — `OnHitReceived` 가 한 본 가정. 동시 다발 (양쪽 어깨 + 가슴):

```cpp
USTRUCT() struct FHitImpact
{
    UPROPERTY() FName BoneName;
    UPROPERTY() FVector_NetQuantizeNormal Direction;
    UPROPERTY() float Strength;
};

UFUNCTION(NetMulticast, Unreliable)  // cosmetic — Unreliable OK
void MulticastApplyHits(const TArray<FHitImpact>& Hits);

void MulticastApplyHits_Implementation(const TArray<FHitImpact>& Hits)
{
    auto* M = Cast<UMCSoftSkeletalMeshComponent>(GetMesh());
    for (const FHitImpact& H : Hits) {
        // 한 번에 여러 본 시뮬 활성 + 임펄스
        M->EnablePartialRagdoll(H.BoneName, true);
        M->ApplyHitImpulse(H.BoneName, H.Direction * H.Strength);
    }
    // Motor profile 은 가장 강한 1번만 적용 (성능)
    if (Hits.Num() > 0) {
        const FHitImpact& Strongest = ...;  // max Strength
        M->ApplyMotorProfileBelow(Strongest.BoneName, M->HitProfileName, true);
    }
}
```

## 6. 결정 트리

```
이 ragdoll 의 *클라간 차이* 가 게임에 영향?
├── 아니오 (시각만) → (A) 또는 (B)
│   ├── 1번뿐 (사망) → (A) cosmetic-only — 각 클라가 자체 트리거
│   └── 트리거 자체가 게임 이벤트 (HP 0) → (B) Multicast — Server 가 동시성 보장
└── 예 (looting / hit detection)
    └── (C) Server-authoritative + FastArraySerializer
        + 추가: 클라이언트 *예측 (prediction)* — Server replicate 도착 전 자체 시뮬,
                 도착 후 reconcile (ACharacter 의 movement prediction 패턴 참고)
```

## 7. 함정 / 열린 질문

- [ ] **(A) cosmetic-only 의 *상태 동기*** — 한 클라는 ragdoll, 다른 클라는 살아있는 상태. `bIsDead` UPROPERTY(Replicated) 로 *상태만* 동기 + 시뮬은 클라마다
- [ ] **(B) Multicast 의 Owner 부재** — Multicast RPC 는 Owner 의 RelevancyChannel 에 의존. 죽은 캐릭터의 Owner = nullptr 면 RPC drop. `SetOwner(GameMode)` 또는 `bOnlyRelevantToOwner=false` 
- [ ] **(C) FastArraySerializer 대역폭** — 80 본 × 매 60Hz = 4.8K 메시지/초/캐릭터. NetUpdateFrequency 5Hz 로 낮추기 + 본 수 LOD ([[concepts/Bone-LOD]])
- [ ] **Late join (게임 중간 합류)** — 합류 시 이미 ragdoll 인 캐릭터의 본 위치 어떻게 동기? (B) 면 RPC 도 못 받음. AActor::OnRep 또는 Replicated UPROPERTY 로 *현재 ragdoll 상태* 만 → 클라가 자체 시뮬 시작
- [ ] **CharacterMovement 와 충돌** — Client 가 ragdoll 인 동안 CharacterMovement Tick 끄기 — 안 그러면 Capsule 이 본과 다른 위치로 ([[sources/ue-components-charactermovementdeep]])
- [ ] **Listen Server 호스트의 호스트 클라** — Server + Client 동시. Multicast RPC 가 Server 코드 + Client 코드 둘 다 실행 → cosmetic 효과 두 번? `IsLocallyControlled()` 가드 ([[synthesis/server-vs-client-rpc-decision-tree]] 함정 #2)
- [ ] **Anti-cheat (해킹)** — (B) 에서 클라가 자체 ragdoll 토글하면 시각만 — 게임 무영향. (C) 는 Server 가 권한 — 클라 조작 불가 (열린)
- [ ] **GAS 와 결합** — Server 가 `GameplayEffect` 로 사망 처리 → `OnDeathTagAdded` 콜백 → Multicast Ragdoll. [[synthesis/gas-pawn-vs-playerstate-decision]] 의 Replication mode = Mixed 가 호환 (열린)

## 8. 관련

### Sources

[[sources/mc-soft-skeletalmesh-ragdoll]] · [[sources/ue-networking-skill]] · [[sources/ue-coreuobject-network]] · [[sources/ue-components-physicscomponents]] · [[sources/ue-gameframework-pawncharacter]]

### Entities

[[entities/USkeletalMeshComponent]] · [[entities/UNetDriver]] · [[entities/AActor]] · [[entities/APlayerController]]

### Concepts

[[concepts/Authority-NetMode]] · [[concepts/Replication]] · [[concepts/RPC]] · [[concepts/PushModel]] · [[concepts/MC-Asset-Validation-Policy]]

### Related synthesis

[[synthesis/server-vs-client-rpc-decision-tree]] (Multicast Reliable/Unreliable 결정) · [[synthesis/mc-character-hit-reaction-pipeline]] (Multicast 진입점) · [[synthesis/ragdoll-getup-anim-recovery]] (GetUp 도 Multicast)

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[synthesis/ai-npc-ragdoll-coordination]] (inbound=3, suggest_missing_cross_link high confidence)
