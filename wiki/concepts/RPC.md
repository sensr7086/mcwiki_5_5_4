---
type: concept
title: "RPC (Server / Client / NetMulticast)"
aliases: [RPC, Server RPC, Client RPC, NetMulticast, Reliable, Unreliable]
sources:
  - "[[sources/ue-networking-skill]]"
related_concepts:
  - "[[concepts/Replication]]"
  - "[[concepts/Authority-NetMode]]"
tags: [ue, networking, multiplayer]
last_updated: 2026-05-09
---

# RPC (Remote Procedure Call)

## 1. 정의 (한 줄)

UFUNCTION(Server / Client / NetMulticast, Reliable / Unreliable) 매크로로 다른 노드에서 함수 실행. Server (Client → Server), Client (Server → 특정 Client), NetMulticast (Server → 모든 Client).

## 2. 자세히

| RPC 종류 | 발화 → 실행 | 사용처 |
| -- | -- | -- |
| Server | Client → Server | 게임 상태 변경 요청 (입력 / 액션) |
| Client | Server → 특정 Client (NetOwner) | UI 알림 / Cosmetic feedback |
| NetMulticast | Server → 모든 Client | 폭발 / Cosmetic 이벤트 |

매크로 표준:
```cpp
UFUNCTION(Server, Reliable, WithValidation)
void Server_RequestJump();
void Server_RequestJump_Implementation();
bool Server_RequestJump_Validate();  // 보안 검증

UFUNCTION(Client, Reliable)
void Client_ShowKillFeed();

UFUNCTION(NetMulticast, Unreliable)
void NetMulticast_PlayExplosion(FVector Location);
```

## 3. 변형 / 사례 / 응용

- Reliable: 보장 (TCP 같은). Unreliable: 드롭 가능 (UDP). 자주 호출 (Tick 마다) = Unreliable.
- WithValidation: Server RPC 의 보안 검증 — `_Validate()` 가 false 시 NMT_GameSpecific kick.
- Owner 결정: RPC 가 어느 PlayerController NetOwner 의 Connection 으로 가는지 — Actor 의 Owner chain.
- 함정: 자주 호출되는 Reliable RPC = 네트워크 saturation. 누적 큐 → 패킷 drop.

## 4. 관련 entity

- [[entities/AActor]] · [[entities/APlayerController]] · [[entities/UNetConnection]]

## 5. 열린 질문

- [ ] WithValidation 의 보안 검증 표준 패턴
- [ ] Reliable RPC saturation 디버깅
