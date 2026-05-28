---
type: synthesis
title: "Server vs Client RPC 결정 트리 — Authority + NetMode + RPC 종류 (Server/Client/NetMulticast, Reliable/Unreliable)"
slug: server-vs-client-rpc-decision-tree
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-networking-skill]]"
  - "[[sources/ue-coreuobject-network]]"
  - "[[sources/ue-gameframework-pawncharacter]]"
  - "[[sources/ue-gameframework-controller]]"
  - "[[sources/ue-gameframework-gamemode]]"
entities:
  - "[[entities/UNetDriver]]"
  - "[[entities/UNetConnection]]"
  - "[[entities/APlayerController]]"
  - "[[entities/AGameModeBase]]"
  - "[[entities/AActor]]"
concepts:
  - "[[concepts/RPC]]"
  - "[[concepts/Authority-NetMode]]"
  - "[[concepts/Replication]]"
  - "[[concepts/PushModel]]"
status: living
tags: [synthesis, networking, rpc, replication, authority]
---

# Server vs Client RPC 결정 트리

## 1. Thesis

UE 의 멀티플레이 함수 호출 — **Replication (Property)** vs **RPC (Function)** 두 갈래. RPC 는 *어디서 실행되는가* (Server/Client/NetMulticast) × *신뢰성* (Reliable/Unreliable) × *호출자 권한* (Authority/Autonomous/Simulated) 의 3 축. 본 synthesis 는 **"이 액션을 어디서 누가 트리거하고 어디서 실행되어야 하는가"** 한 질문으로 결정 트리를 따라가면 답이 나오도록. [[concepts/RPC]] + [[concepts/Authority-NetMode]] + [[concepts/Replication]] 통합.

## 2. RPC 3 종 매트릭스

| 종류 | 어디서 실행 | 누가 호출 가능 | 흔한 용도 |
| -- | -- | -- | -- |
| `Server` (UFUNCTION(Server, Reliable)) | 서버에서만 | Owning Client (Owner = Player 의 Pawn 등) | 입력 → 서버 사이드 액션 (Fire, Jump, UseItem) |
| `Client` (UFUNCTION(Client, Reliable)) | 특정 클라이언트에서만 | 서버 (Authority) | 그 플레이어에게만 보일 UI 알림, 화면 이펙트 |
| `NetMulticast` | 서버 + 모든 관련 클라이언트 | 서버 (Authority) | 폭발 / 시각 효과 / 사운드 — 모두에게 보여야 |

## 3. 신뢰성 매트릭스

| 옵션 | 보장 | 비용 | 용도 |
| -- | -- | -- | -- |
| `Reliable` | 도착 + 순서 | 큼 — 패킷 재전송, 순서 보장, 체크섬 | 게임 로직 (HP 변경, 죽음, 미션 진행) |
| `Unreliable` | 도착 보장 X, 순서 X | 작음 — fire-and-forget | 시각 / 사운드 (폭발 위치 등 — 1 패킷 잃어도 게임 무결) |

> Tip: Reliable 채널은 한정 — 매 프레임 50개 Reliable RPC 는 패킷 큐 폭발. 게임 로직만 Reliable, 시각은 Unreliable 표준.

## 4. 결정 트리

```
이 액션은 *상태를 바꾸는가* (게임 로직) vs *보여주는 효과인가* (cosmetic)?
├── 게임 로직 (HP 변경, 사망, 점수)
│   └── Server 가 *권한* — 두 가지 패턴:
│       (a) Server RPC: Client 입력 → Server 가 검증 후 실행
│           → UFUNCTION(Server, Reliable, WithValidation)
│           → ServerFire_Validate (cheat 검사) + ServerFire_Implementation (실행)
│       (b) Property Replication: Server 가 변경 → 자동 모든 Client
│           → UPROPERTY(Replicated 또는 ReplicatedUsing=OnRep_HP)
│           → Server SetHP(50) → Client 의 OnRep_HP 자동 호출
│
├── Cosmetic (폭발, 사운드, 파티클)
│   └── 한 명 vs 여러 명?
│       ├── 한 명 (private UI) → Client RPC
│       │   → UFUNCTION(Client, Unreliable)
│       │   → Server 에서 ClientShowDamageNumber(50) 호출 → 그 클라만
│       └── 모두 (폭발 effect)  → NetMulticast
│           → UFUNCTION(NetMulticast, Unreliable)
│           → Server 에서 MulticastExplodeAt(Loc) → 모두에게 broadcast
│
└── 입력 → Cosmetic (예: 사운드만)
    └── Local 만 — RPC 안 씀, 그냥 함수 호출
```

## 5. 시나리오 — 흔한 패턴

| # | 액션 | RPC 패턴 |
| -- | -- | -- |
| 1 | Player Fire 발사 | (1) Client 입력 → ServerFire (Reliable, WithValidation) → (2) Server 가 NetMulticast PlayMuzzleFlash (Unreliable) |
| 2 | HP 변경 | UPROPERTY(ReplicatedUsing=OnRep_HP) — RPC 아님. Server 가 직접 수정 |
| 3 | 사망 ragdoll | (1) Server 가 Property bIsDead 갱신 (Replicated) → (2) Server 가 NetMulticast PlayDeathAnim (Reliable — 모두 ragdoll 봐야) |
| 4 | "당신만 받은 데미지" UI 알림 | Server → ClientShowHitMarker (Unreliable) — 그 한 명에게만 |
| 5 | Match 시작 / 종료 | GameMode 가 NetMulticast OnMatchStart (Reliable) — 모두 동시에 |
| 6 | Bot AI 결정 | RPC 안 씀 — Server only Tick. AI 는 서버에서만 동작 |
| 7 | Voice Chat | Plugin (Voice) — Server 가 relay |

## 6. Authority + NetMode 매트릭스

```cpp
// 어디서 실행 중인지 판단
const ENetMode Mode = GetNetMode();
// NM_Standalone (싱글) / NM_DedicatedServer / NM_ListenServer / NM_Client

const bool bHasAuth = HasAuthority();
// Server / Standalone = true, Client = false (Owning Pawn 도 false)

// 함수 시작에서 가드:
void AMyChar::DoServerThing()
{
    if (!HasAuthority()) {                  // Client 면 (또는 Listen client)
        ServerDoThing();                    // RPC 호출
        return;
    }
    // 서버 코드
    InternalDoThing();
    MulticastNotifyAll();                   // cosmetic 은 broadcast
}
```

[[concepts/Authority-NetMode]] — `HasAuthority()` 가 가장 자주 쓰이는 분기. `IsLocallyControlled()` 는 Pawn 의 *그 클라이언트가 조작 중* 검사 (UI / Input 게이팅).

## 7. 함정 / 열린 질문

- [ ] **모든 RPC 를 Reliable** — 채널 폭발. cosmetic 은 Unreliable
- [ ] **NetMulticast 를 Owning Client 검증 없이** — Listen Server 의 호스트 클라이언트도 본인 효과 두 번 받음 (Server tick + Multicast). `IsLocallyControlled()` 분기로 회피
- [ ] **Replication frequency** ([[entities/AActor]]::NetUpdateFrequency) — 디폴트 100Hz. 멀리 있는 NPC 는 1~5Hz 로 (Replication 비용 감소)
- [ ] **`PushModel`** ([[concepts/PushModel]]) — Property 변경 시 명시적 dirty 플래그. 자동 비교 비용 절감 — 5.1+ 표준
- [ ] **Server RPC 의 `WithValidation`** — cheat 검사 함수. `_Validate` returns false → Client kick 가능. 보안 critical RPC 는 의무
- [ ] **`UFUNCTION(Server, Reliable)` 의 `Owner`** — Owner 가 PlayerController / Owner 의 Owner chain 안에 그 클라이언트 있어야 함. 안 그러면 RPC drop
- [ ] **Ragdoll Replication** — Server 가 본 위치를 매 프레임 replicate? Cosmetic-only 처리 (각 클라가 시뮬레이션)? — [[sources/mc-soft-skeletalmesh-ragdoll]] 의 열린 질문 (열린)
- [ ] **FastArraySerializer** — TArray<T> 의 *변경 항목만* replicate. 인벤토리 / 스코어보드 등 큰 배열에 필수 (열린, [[sources/ue-coreuobject-network]] 참고)

## 8. 관련

### Sources

[[sources/ue-networking-skill]] · [[sources/ue-coreuobject-network]] · [[sources/ue-gameframework-pawncharacter]] · [[sources/ue-gameframework-controller]] · [[sources/ue-gameframework-gamemode]]

### Entities

[[entities/UNetDriver]] · [[entities/UNetConnection]] · [[entities/APlayerController]] · [[entities/AGameModeBase]] · [[entities/AActor]]

### Concepts

[[concepts/RPC]] · [[concepts/Authority-NetMode]] · [[concepts/Replication]] · [[concepts/PushModel]]

### Related synthesis

[[synthesis/gas-pawn-vs-playerstate-decision]] (GAS 의 RPC + Replication 통합) · [[synthesis/mc-character-hit-reaction-pipeline]] (Ragdoll Multicast vs cosmetic-only) · [[synthesis/subsystem-5-types-decision-tree]] (Server vs Client Subsystem 결정)
