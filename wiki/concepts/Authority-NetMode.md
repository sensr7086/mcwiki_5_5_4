---
type: concept
title: "Authority vs NetMode 분기"
aliases: [HasAuthority, GetNetMode, NetMode, ENetMode]
sources:
  - "[[sources/ue-networking-skill]]"
related_concepts:
  - "[[concepts/Replication]]"
  - "[[concepts/RPC]]"
tags: [ue, networking, multiplayer]
last_updated: 2026-05-09
---

# Authority vs NetMode

## 1. 정의 (한 줄)

HasAuthority() = **객체 단위** Authority (서버 또는 Standalone 의 객체). GetNetMode() = **World 단위** 모드 (Standalone / Client / DedicatedServer / ListenServer). 의미 다름 [grep-listed].

## 2. 자세히

```cpp
const ENetMode NM = GetNetMode();
const bool bIsServer  = NM != NM_Client;          // Listen / Dedicated / Standalone
const bool bIsClient  = NM == NM_Client;
const bool bIsListen  = NM == NM_ListenServer;
const bool bIsDedi    = NM == NM_DedicatedServer;
const bool bIsStandalone = NM == NM_Standalone;

if (HasAuthority())  // 객체 단위 권위
{
    // 게임 상태 변경 (Replication 전파)
}
```

## 3. 변형 / 사례 / 응용

- HasAuthority(): 해당 Actor 가 Server 측 인가? (Client 측 simulated proxy 는 false). Standalone = 항상 true.
- GetNetMode(): World 의 mode. Listen Server 는 NM_ListenServer (Client 도 동시).
- 데디 서버 분기: WITH_SERVER_CODE + IsRunningDedicatedServer(). Cosmetic 코드 (VFX / SFX) skip.
- 표준 패턴: 게임 상태 변경 = HasAuthority() 안. Cosmetic = Server / Client 양쪽 OK.
- 함정: BeginPlay 안 HasAuthority() = OK. Constructor 안 = false (Spawn 후 결정).

## 4. 관련 entity

- [[entities/AActor]] · [[entities/UWorld]]

## 5. 열린 질문

- [ ] Listen Server 의 PlayerController 동작 (Client + Server 동시)
- [ ] HasAuthority 의 Spawn 시점 분기
