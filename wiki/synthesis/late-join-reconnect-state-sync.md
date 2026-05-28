---
type: synthesis
title: "Late Join + Reconnect 상태 동기화 — Ragdoll/GameplayCue/PlayerState 합류 시점 복원"
slug: late-join-reconnect-state-sync
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-networking-skill]]"
  - "[[sources/ue-coreuobject-network]]"
  - "[[sources/ue-gameframework-gamemode]]"
  - "[[sources/ue-gameframework-controller]]"
  - "[[sources/ue-gas-skill]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
entities:
  - "[[entities/UNetDriver]]"
  - "[[entities/UNetConnection]]"
  - "[[entities/AGameModeBase]]"
  - "[[entities/AGameStateBase]]"
  - "[[entities/UAbilitySystemComponent]]"
concepts:
  - "[[concepts/Replication]]"
  - "[[concepts/RPC]]"
  - "[[concepts/Authority-NetMode]]"
  - "[[concepts/Match-State]]"
status: living
tags: [synthesis, late-join, reconnect, replication, multiplayer]
---

# Late Join + Reconnect 상태 동기화

## 1. Thesis

Multiplayer 게임에서 *진행 중인 매치에 합류한 클라이언트* (Late Join) 또는 *연결 끊김 후 재연결* (Reconnect) 은 모두 *현재 게임 상태* 를 복원해야 한다. 핵심 — **Replication 만으론 부족**. 기본 Replication 은 *`bNetStartup`/`bNetLoadOnClient` Actor + 진행 중 Replicate Property* 만 동기 — *과거에 발화한 Multicast RPC* / *현재 진행 중 Montage* / *활성 GameplayCue* 는 안 따라옴. 4 가지 누락 카테고리 — **(1) 시간 의존 효과 (진행 중 GameplayEffect duration / Cooldown) / (2) Multicast 단발 효과 (이미 fade out 된 폭발 cue 는 OK, 진행 중 ragdoll 은 NG) / (3) Montage 진행 상태 (위치 / 시간) / (4) Local-only 데이터 (UI 상태)**. 본 synthesis 는 합류 시점 복원의 4 카테고리별 표준 + Initial Replication 시점 활용 + 명시적 Sync RPC.

## 2. 4 카테고리 매트릭스

| 카테고리 | 자동 동기? | 복원 방법 |
| -- | -- | -- |
| Replicated Property (HP / Tag) | ✓ (Initial Replication) | 자동 — `OnRep_*` 발화 |
| 진행 중 GameplayEffect Duration | △ — ASC 가 GE 자체는 replicate, *남은 시간* 은 Server 시간 vs Client 시간 동기 필요 | `FActiveGameplayEffect::StartServerWorldTime` 으로 보정 |
| 진행 중 AnimMontage | △ — Position 은 Replicate (CharacterMovement 의 Compressed Movement) | 자동 (Character Mesh 만) |
| 진행 중 ragdoll | ✗ — 시뮬 상태는 Replicate 안 됨 | bIsRagdoll Property + Multicast 재발화 |
| 활성 GameplayCue (지속) | ✗ — Cue 는 trigger only | `ASC->GetActiveGameplayCues()` 에서 모든 Tag broadcast |
| 과거 Multicast RPC (폭발 등) | ✗ — 일회성 | 무시 OK (이미 fade out) |
| Local-only UI 상태 | ✗ | UI 가 Replicated Property 기반 재구성 |

## 3. 시점별 복원 절차 (Late Join)

```
Client 합류 → AGameMode::PostLogin
                 ↓
             RestartPlayer (Pawn spawn)
                 ↓
             (NetDriver 가 모든 Relevant Actor 의 Initial Replication 시작)
                 ↓
             Pawn::OnRep_PlayerState (PS 도착)
                 ↓
             ASC::InitAbilityActorInfo (PlayerState 모델)
                 ↓
             (Replicated Property 도착 — HP / Stamina / etc.)
                 ↓
             OnRep_*  ← 4 카테고리 #1 복원
                 ↓
             AGameStateBase::OnRep_PlayerArray (다른 플레이어 정보)
                 ↓
             [명시적 SyncRPC 호출] ← 4 카테고리 #2~5 복원
```

## 4. 명시적 Sync RPC 패턴

```cpp
class APlayerController : public APlayerController
{
    UFUNCTION(Server, Reliable)
    void ServerRequestStateSync();

    UFUNCTION(Client, Reliable)
    void ClientReceiveStateSync(const FStateSyncData& Data);

    virtual void OnRep_PlayerState() override
    {
        Super::OnRep_PlayerState();
        if (PlayerState && IsLocalController()) {
            // 합류 직후 — Server 에 명시적 sync 요청
            ServerRequestStateSync();
        }
    }
};

void APlayerController::ServerRequestStateSync_Implementation()
{
    // Server 가 현재 상태 수집 + 그 클라에만 broadcast
    FStateSyncData Data;

    // (a) 활성 GameplayCue
    if (auto* ASC = GetAbilitySystemComponent()) {
        ASC->GetOwnedGameplayTags(Data.ActiveCueTags);
    }
    // (b) 진행 중 ragdoll 캐릭터들
    for (TActorIterator<AMyChar> It(GetWorld()); It; ++It) {
        if (It->GetMesh()->IsRagdollActive()) {
            Data.RagdollCharacters.Add({*It, It->GetMesh()->GetSocketTransform(TEXT("pelvis"))});
        }
    }
    // (c) 매치 진행 시간
    Data.MatchStartTime = GetWorld()->GetGameState()->GetServerWorldTimeSeconds();

    ClientReceiveStateSync(Data);
}

void APlayerController::ClientReceiveStateSync_Implementation(const FStateSyncData& Data)
{
    // 클라가 자체 시뮬 트리거
    for (const FGameplayTag& T : Data.ActiveCueTags) {
        ASC->ExecuteGameplayCue(T, FGameplayCueParameters{});  // local trigger
    }
    for (const FRagdollSnapshot& Snap : Data.RagdollCharacters) {
        if (auto* M = Cast<UMCSoftSkeletalMeshComponent>(Snap.Char->GetMesh())) {
            M->EnableFullRagdoll();
            M->GetMesh()->SetSocketLocation(TEXT("pelvis"), Snap.PelvisW.GetLocation());
            // 본 위치 정확 X — 시각만, Server-authoritative 는 [[synthesis/ragdoll-multiplayer-replication]] (C)
        }
    }
}
```

## 5. Reconnect 의 추가 처리

연결 끊김 → 재연결 — Late Join 과 다른 점은 *서버에 PlayerState 가 살아있음*:

```cpp
// AGameMode 측
virtual APlayerController* SpawnPlayerController(...) override
{
    APlayerController* PC = Super::SpawnPlayerController(...);
    // Reconnect 검사 — 같은 UniqueId 의 inactive PS 가 있는가?
    for (APlayerState* InactivePS : GetGameState<AGameStateBase>()->PlayerArray) {
        if (InactivePS->bIsInactive && InactivePS->GetUniqueId() == PC->PlayerState->GetUniqueId()) {
            // 옛 PS 의 데이터를 새 PS 에 복사 (능력 / 스코어 / 인벤토리)
            PC->PlayerState->CopyProperties(InactivePS);
            InactivePS->Destroy();
            break;
        }
    }
    return PC;
}
```

## 6. 함정 / 열린 질문

- [ ] **Initial Replication 의 순서 비결정성** — Pawn 도착 vs PlayerState 도착 — 뭐가 먼저? `OnRep_PlayerState` 또는 `OnRep_Pawn` 둘 다에서 idempotent init ([[synthesis/actor-lifecycle-edge-cases]])
- [ ] **Replicate 안 되는 Editor only Actor** — `bNetStartup=false + bAlwaysRelevant=false + Replicates=false` Actor — Late Join 시 안 보임. 의도라면 OK
- [ ] **GameplayCue 의 Late Join 미동기** — 진행 중인 *Looping cue* (예: 캐릭터의 화염 효과 지속) — Server 가 새 클라에 Multicast 재발화 의무. 자동 X — `ServerRequestStateSync` 안에 포함
- [ ] **Server 시간 vs Client 시간** — `GameplayEffect.Duration` 의 `StartServerWorldTime` — 클라이언트의 World time 과 다름. `GetServerWorldTimeSeconds` 로 정확 복원
- [ ] **Reconnect 의 Inactive PS 만료** — `AGameMode::InactivePlayerStateLifeSpan` (디폴트 5초). 5초 넘으면 데이터 잃음. 게임에 따라 30~300초 늘림
- [ ] **Bandwidth 폭발** — Late Join 첫 1~2초 — Initial Replication 으로 모든 relevant Actor (수십~수백) 동기. NetUpdateFrequency / DormancySettings 로 분산
- [ ] **Save 게임 vs Reconnect** — Reconnect 는 PS 데이터만 — Save 는 World 데이터까지. Save Game subsystem ([[synthesis/subsystem-5-types-decision-tree]]) 가 별도 (열린)
- [ ] **Replication Graph 5.x** — UE 5.x 의 새 Replication Graph 가 Late Join Initial Replication 비용을 분산. 적용 결정 (열린, [[sources/ue-networking-skill]])

## 7. 관련

### Sources

[[sources/ue-networking-skill]] · [[sources/ue-coreuobject-network]] · [[sources/ue-gameframework-gamemode]] · [[sources/ue-gameframework-controller]] · [[sources/ue-gas-skill]] · [[sources/mc-soft-skeletalmesh-ragdoll]]

### Entities

[[entities/UNetDriver]] · [[entities/UNetConnection]] · [[entities/AGameModeBase]] · [[entities/AGameStateBase]] · [[entities/UAbilitySystemComponent]]

### Concepts

[[concepts/Replication]] · [[concepts/RPC]] · [[concepts/Authority-NetMode]] · [[concepts/Match-State]]

### Related synthesis

[[synthesis/server-vs-client-rpc-decision-tree]] (Sync RPC Reliable/Unreliable) · [[synthesis/ragdoll-multiplayer-replication]] (Late Join ragdoll 동기) · [[synthesis/gas-advanced-runtime-patterns]] (GameplayCue Late Join 동기) · [[synthesis/replication-graph-bandwidth-management]] (Replication Graph + Dormancy — Late Join burst 분산)
