---
type: synthesis
title: "Replication Graph 5.x + Bandwidth 관리 — Late Join burst 분산 + Dormancy + 매치 시간 동기"
slug: replication-graph-bandwidth-management
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/ue-networking-skill]]"
  - "[[sources/ue-coreuobject-network]]"
  - "[[sources/ue-gameframework-gamemode]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
entities:
  - "[[entities/UNetDriver]]"
  - "[[entities/UNetConnection]]"
  - "[[entities/AGameStateBase]]"
  - "[[entities/AActor]]"
concepts:
  - "[[concepts/Replication]]"
  - "[[concepts/PushModel]]"
  - "[[concepts/Authority-NetMode]]"
  - "[[concepts/Match-State]]"
status: living
tags: [synthesis, networking, replication-graph, bandwidth, dormancy]
---

# Replication Graph 5.x + Bandwidth 관리

## 1. Thesis

[[synthesis/late-join-reconnect-state-sync]] 의 미해결 — Bandwidth burst (Late Join 시 1~2초간 모든 relevant Actor Initial Replication) — 5.x 의 *Replication Graph* (UReplicationGraph) 가 해결. 핵심 — **NetDriver 의 *모든 Actor × 모든 Connection* O(N×M) 검사를 graph-based 분류 (Spatial / Always Relevant / Frequency Buckets) 로 변환**. Bandwidth 관리는 4 축 — **(1) Replication Graph 노드 분류 (Spatial Grid / Always Relevant / Owner Only / Dynamic) / (2) NetUpdateFrequency × Significance bucket / (3) Dormancy (특정 Actor 의 Replication 임시 정지) / (4) ServerWorldTimeSeconds 매치 시간 동기 (GE Duration 보정)**.

## 2. Replication Graph 노드 4 종

`UReplicationGraph` 의 Actor 분류 — 각 노드가 다른 Frequency 로 처리:

| 노드 | 무엇이 들어가는가 | Frequency / Cost |
| -- | -- | -- |
| `UReplicationGraphNode_GridSpatialization2D` | 위치 기반 — Player 근처 Actor | 거리 따라 NetUpdateFrequency 조정 |
| `UReplicationGraphNode_AlwaysRelevant_ForConnection` | PlayerController / Pawn / PlayerState (자기 자신) | 항상 max frequency |
| `UReplicationGraphNode_ActorList` | 모두에게 relevant (GameState / 보스) | 매 frame 검사 |
| `UReplicationGraphNode_Dormancy` | Dormant 상태 (Replication 임시 정지) | 깨어날 때만 |

```cpp
class UMyReplicationGraph : public UReplicationGraph
{
    virtual void InitGlobalActorClassSettings() override
    {
        Super::InitGlobalActorClassSettings();
        // 클래스별 default node 할당
        SetClassReplicationInfo(AMyEnemy::StaticClass(),  /*Node=*/EClassRepNode::Spatial);
        SetClassReplicationInfo(AMyBoss::StaticClass(),   /*Node=*/EClassRepNode::AlwaysRelevant);
        SetClassReplicationInfo(AMyPickup::StaticClass(), /*Node=*/EClassRepNode::Dormancy);
    }
};

// DefaultEngine.ini
[/Script/OnlineSubsystemUtils.IpNetDriver]
ReplicationDriverClassName="MyReplicationGraph"
```

## 3. NetUpdateFrequency × Significance Bucket

거리 기반 Replication 주기 분할 — Significance bucket 과 같은 결정 트리:

```cpp
// Server tick — Actor 별 NetUpdateFrequency 동적 조정
void AMyEnemy::Tick(float Dt)
{
    Super::Tick(Dt);
    if (HasAuthority()) {
        APawn* ClosestPlayer = FindClosestPlayer();
        const float Dist = GetDistanceTo(ClosestPlayer);
        // 근거리: 60Hz / 중거리: 10Hz / 원거리: 1Hz
        NetUpdateFrequency = (Dist < 500.f) ? 60.f
                           : (Dist < 2000.f) ? 10.f : 1.f;
    }
}
```

[[synthesis/character-many-npc-5-fold-optimization]] 의 5축 최적화와 결합 — Bone LOD / URO / Visibility / NetUpdateFrequency 가 *각 축 직교*.

## 4. Dormancy — Bandwidth 0 으로

특정 Actor 가 잠시 *변화 없음* → Dormancy 로 Replication 완전 정지:

```cpp
// Server — 변화 없을 때 Dormancy 진입
SetNetDormancy(DORM_DormantAll);   // 모든 Connection 에서 잠듦

// 변화 발생 시 깨우기
FlushNetDormancy();   // 다음 frame 부터 다시 Replicate

// DORM 모드:
// DORM_Awake          — 항상 Replicate (디폴트)
// DORM_DormantAll     — 모든 Connection 에서 잠듦
// DORM_DormantPartial — 특정 Connection 만 잠듦 (사용자 정의)
// DORM_Initial        — Initial Replication 만 후 잠듦 (Static prop 표준)
```

**적합 케이스**:
- Static prop (의자 / 책상) — `DORM_Initial`
- Pickup (집기 전엔 변화 없음) — `DORM_DormantAll`
- 멀리 있는 NPC — 거리 멀어지면 Dormancy, 가까이 오면 Flush

## 5. ServerWorldTimeSeconds — GE Duration 보정

[[synthesis/late-join-reconnect-state-sync]] §6 의 미해결 — Server 시간 vs Client 시간:

```cpp
// Server: GE Duration 5.0 적용 시점 = ServerWorldTime 100.0
// Client: Initial Replication 도착 시 ServerWorldTime 105.0 → 이미 5초 경과
//         → 남은 시간 = 5.0 - (105.0 - 100.0) = 0.0 → 즉시 expire 정상

// 자동 동기 — FActiveGameplayEffect::StartServerWorldTime
struct FActiveGameplayEffect
{
    float StartServerWorldTime;  // Server 가 GE 부여한 시점
    // Client 의 남은 시간 = Duration - (GetServerWorldTimeSeconds() - StartServerWorldTime)
};

// 클라가 시간 동기 가져옴
const float ServerTime = GetWorld()->GetGameState()->GetServerWorldTimeSeconds();
```

GameStateBase 가 매 N 초 ServerWorldTime 을 클라에 broadcast — GE Duration 의 정확한 잔여 시간 계산 가능.

## 6. Late Join Bandwidth 분산 — 4 전략

| 전략 | 메커니즘 | 효과 |
| -- | -- | -- |
| Replication Graph + Spatial | 멀리 있는 Actor 는 노드 우선순위 낮음 → Initial Rep 도 분산 | 즉시 효과 |
| Dormancy | Static prop = `DORM_Initial` → 1회만 replicate 후 정지 | 대규모 효과 |
| NetUpdateFrequency Dynamic | 거리 따라 1~60Hz — 멀리 = 1Hz | 효과 큼 |
| Initial Burst Throttle | `MaxClientBandwidth` Server 설정 — 클라 별 패킷 비율 제한 | 안전망 |

```ini
; DefaultEngine.ini
[/Script/OnlineSubsystemUtils.IpNetDriver]
MaxClientBandwidth=15000  ; 15 KB/s 클라 별 제한 (디폴트 ~100KB/s)
MaxInternetClientRate=15000
```

## 7. 함정 / 열린 질문

- [ ] **Replication Graph 셋업 비용** — `InitGlobalActorClassSettings` 안 모든 Actor 클래스 분류 — 첫 게임 시작 시 약간 stall. Editor PIE 안 검증
- [ ] **Spatial Grid Cell Size** — 너무 작 (~50 cm) → cell traversal 비용. 너무 큼 (~10000 cm) → 같은 cell 안 너무 많은 Actor. 게임 별 튜닝 (보통 1000~2000)
- [ ] **Dormancy + GameplayEffect 충돌** — Dormancy 진입 후 Server 가 GE 적용 → Client 에 도착 안 됨 (잠들었음). GAS 의무 — ASC 보유 Actor 는 `DORM_Awake` 강제
- [ ] **PushModel 와 NetUpdateFrequency** — PushModel ([[concepts/PushModel]]) 은 *변경 시점에만* Replicate — NetUpdateFrequency 와 직교. 둘 다 켜면 더 효율적
- [ ] **Replication Driver 변경 시 *Mid-game switch* 안 됨** — DefaultEngine.ini 의 ReplicationDriverClassName 은 서버 시작 시점 고정
- [ ] **FastArraySerializer + Spatial** — FastArray 의 변경 항목만 replicate 가 Spatial Grid 와 결합 — `GetMaxNetUpdateFrequency` 가 array entry 별로 동작 (열린)
- [ ] **Replication Graph 의 *디버그 시각화*** — `r.RepGraph.PrintAllActorClassSettings 1` / `gdt.PrintGraph` 콘솔. Editor 에서 Replication Graph 의 노드 트리 ASCII 출력 (열린)

## 8. 관련

### Sources

[[sources/ue-networking-skill]] · [[sources/ue-coreuobject-network]] · [[sources/ue-gameframework-gamemode]] · [[sources/mc-soft-skeletalmesh-ragdoll]]

### Entities

[[entities/UNetDriver]] · [[entities/UNetConnection]] · [[entities/AGameStateBase]] · [[entities/AActor]]

### Concepts

[[concepts/Replication]] · [[concepts/PushModel]] · [[concepts/Authority-NetMode]] · [[concepts/Match-State]]

### Related synthesis

[[synthesis/late-join-reconnect-state-sync]] (Bandwidth burst 해결) · [[synthesis/server-vs-client-rpc-decision-tree]] (Reliable / Unreliable + NetUpdateFreq) · [[synthesis/character-many-npc-5-fold-optimization]] (Significance bucket 결합)
