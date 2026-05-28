---
name: ue-networking
description: UE 5.5.4 네트워킹/멀티플레이 위키. Replication(DOREPLIFETIME, OnRep_, PushModel) + RPC(Server/Client/NetMulticast, Reliable/Unreliable) + Authority/NetMode + RelevantTo/NetCullDistance + FastArraySerializer + 데디 서버 분기. CoreUObject/Network sub-skill의 게임 레벨 컴패니언.
---

# Networking — UE 5.5.4 멀티플레이 / Replication

> **카테고리** — Tier 1 (게임 로직 베이스 — 멀티플레이 시)
> **대표 클래스** — `AActor`(NetRole/NetMode), `UActorComponent`(IsReplicated), `UNetDriver`, `UNetConnection`, `FRepLayout`
> **트리거 키워드** — Replication, DOREPLIFETIME, Server, Client, Multicast, RPC, NetMulticast, GetLifetimeReplicatedProps, OnRep_, HasAuthority, GetNetMode, PushModel, FastArraySerializer

본 sub-skill은 게임플레이 코드에서 자주 쓰는 네트워킹 패턴을 정리. 직렬화 깊은 내부는 [`skills/CoreUObject/references/Network.md`](../CoreUObject/references/Network.md) 참조.

---

## 1. NetMode / Role 식별 표준

```cpp
const ENetMode NM = GetNetMode();
const bool bIsServer  = NM != NM_Client;
const bool bIsClient  = NM == NM_Client;
const bool bIsListen  = NM == NM_ListenServer;
const bool bIsDedi    = NM == NM_DedicatedServer;
const bool bIsStandalone = NM == NM_Standalone;

if (HasAuthority())  // 권위 측 (서버 또는 Standalone)
{
    // 게임 상태 변경
}
```

> 🚨 **`HasAuthority()` vs `GetNetMode() == NM_Client`** 의미 다름 — Authority는 객체 단위, NetMode는 World 단위 [grep-listed].

---

## 2. Replication 표준

### 2.1 변수 복제 (`UPROPERTY(Replicated)` + `DOREPLIFETIME`)

```cpp
UPROPERTY(ReplicatedUsing=OnRep_Health)
float Health = 100.f;

void AMyChar::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const
{
    Super::GetLifetimeReplicatedProps(Out);
    DOREPLIFETIME(AMyChar, Health);
    // 조건 복제
    DOREPLIFETIME_CONDITION(AMyChar, Health, COND_OwnerOnly);
}

UFUNCTION()
void OnRep_Health(float OldHealth)  // 클라이언트 콜백
{
    if (Health <= 0) { /* 사망 처리 */ }
}
```

### 2.2 Component 복제

```cpp
UMyComp::UMyComp()
{
    SetIsReplicatedByDefault(true);  // Component 자체 복제
    PrimaryComponentTick.bCanEverTick = false;
}
```

### 2.3 PushModel 5.x 표준

복제 트래픽 절감 — **변경된 필드만 푸시**:

```cpp
// Build.cs
PrivateDependencyModuleNames.Add("NetCore");

// .h
UPROPERTY(ReplicatedUsing=OnRep_Health)
float Health;

// .cpp — 변경 시
MARK_PROPERTY_DIRTY_FROM_NAME(AMyChar, Health, this);
```

> ⚠ PushModel 등록 의무 — `DOREPLIFETIME_WITH_PARAMS_FAST` + `DefaultEngine.ini`에 `bWithPushModel=true` [grep-listed].

---

## 3. RPC 표준

### 3.1 RPC 종류

| 종류 | 호출자 | 실행 위치 | 사용 |
|------|--------|----------|------|
| `Server` | 클라이언트 | 서버 | 입력 → 권위 처리 |
| `Client` | 서버 | 특정 클라(Owner) | 응답 / 알림 |
| `NetMulticast` | 서버 | 모든 클라 + 서버 | 시각/사운드 효과 |

### 3.2 Reliable vs Unreliable

| 옵션 | 보장 | 사용 |
|------|------|------|
| `Reliable` | 도착 + 순서 | 게임 상태 변경, 점수 |
| `Unreliable` | 손실 가능 | 위치 업데이트, 사운드 |

### 3.3 시그니처

```cpp
UFUNCTION(Server, Reliable, WithValidation)
void Server_Fire(FVector Target);
void Server_Fire_Implementation(FVector Target);  // 본체
bool Server_Fire_Validate(FVector Target) { return Target.SizeSquared() < 100000.f * 100000.f; }
```

> 🚨 `WithValidation` 권장 — 클라 해킹 방지. 실패 시 클라 강제 disconnect [verified].

---

## 4. Relevancy / 컬링

| 메서드 / 변수 | 역할 |
|--------------|------|
| `bAlwaysRelevant` | 항상 모두에게 복제 (GameMode 등) |
| `bOnlyRelevantToOwner` | Owner만 |
| `NetCullDistanceSquared` | 거리 컬링 (제곱) |
| `IsNetRelevantFor()` | 커스텀 Relevancy override |
| `GetNetPriority()` | 우선순위 — 멀리 있어도 자주 |

```cpp
NetCullDistanceSquared = 30000.f * 30000.f;  // 30000 cm = 300m
```

---

## 5. FastArraySerializer (배열 효율 복제)

대량 인벤토리 / 버프 등은 `FFastArraySerializer` + `FFastArraySerializerItem` 사용:

```cpp
USTRUCT()
struct FInventoryItem : public FFastArraySerializerItem
{
    GENERATED_BODY()
    UPROPERTY() int32 ItemID = 0;
    UPROPERTY() int32 Quantity = 0;
};

USTRUCT()
struct FInventoryArray : public FFastArraySerializer
{
    GENERATED_BODY()
    UPROPERTY() TArray<FInventoryItem> Items;
    bool NetDeltaSerialize(FNetDeltaSerializeInfo& P)
    { return FFastArraySerializer::FastArrayDeltaSerialize<FInventoryItem, FInventoryArray>(Items, P, *this); }
};

template<> struct TStructOpsTypeTraits<FInventoryArray>
    : TStructOpsTypeTraitsBase2<FInventoryArray> { enum { WithNetDeltaSerializer = true }; };
```

---

## 6. 함정 / 정책 의무

| 함정 | 원인 | 해결 |
|------|------|------|
| `OnRep_` 안 호출 | `GetLifetimeReplicatedProps` 누락 | DOREPLIFETIME 등록 |
| 클라에서 변수 변경 | Authority 미체크 | `if (HasAuthority())` 가드 |
| RPC 폭주 | 매 Tick 호출 | Throttle / Bunching |
| Component 복제 안 됨 | `SetIsReplicatedByDefault` 누락 | Constructor 호출 |
| Multicast 안 보임 | NetCullDistance / Relevancy 컷 | bAlwaysRelevant or 거리 늘림 |

### 6.1 정책 인용

- 🚨 `04_OverrideIndex` — `GetLifetimeReplicatedProps` Super 호출 의무
- 🚨 `07_ProfilingScopeRule` — RPC 호출에 `TRACE_CPUPROFILER_EVENT_SCOPE`
- 🚨 `10_ComponentPolicies` — Component 복제 시 GC 보호

---

## 7. 데디 서버 분기 (Cooked 차이)

```cpp
#if UE_SERVER
    // 서버 전용 코드 (Cooked DediServer 빌드만)
#endif

if (IsRunningDedicatedServer())  // 런타임 분기
{
    // 시각/사운드 스킵
}
```

> 🚨 `BlueprintCosmetic` 매크로 — BP 함수가 데디 서버에서 자동 NOP. 서버 CPU 절약 [verified].

---

## 8. 검증 절차

1. Editor PIE — Net Mode = Listen Server, NumberOfClients = 2
2. Standalone — Server 별도 + Client 별도 프로세스
3. Cooked Development DediServer 빌드 + Cooked Client
4. Net Profiler — `stat Net` / `Net.PktLag=200` 등 콘솔 명령

---

## 9. 더 깊이 / 외부 검증

- Replication 깊은 내부 → [`skills/CoreUObject/references/Network.md`](../CoreUObject/references/Network.md)
- GAS Replication Mode 3종 → [`skills/GAS/SKILL.md`](../GAS/SKILL.md)
- 위키 외부 — `references/19_ExternalSourcesGuide.md`로 docs.unrealengine.com Networking 섹션
- Iris(5.x 신규 Replication 시스템)는 위키에 없음 — `[inferred]`로 표시
  - 5.5.4 위치: `Engine/Source/Runtime/Experimental/Iris/Core/` (Public/Iris/{ReplicationSystem, ReplicationState, Serialization, DataStream, PacketControl, Metrics, IrisConfig.h, IrisConstants.h}). 5.5 = Experimental 단계.

---

## 관련

- [`skills/CoreUObject/references/Network.md`](../CoreUObject/references/Network.md) — 직렬화 + RepLayout 깊이
- [`skills/GameFramework/references/Controller.md`](../GameFramework/references/Controller.md) — PlayerController 복제
- [`skills/GAS/SKILL.md`](../GAS/SKILL.md) — Ability Replication
- [`references/04_OverrideIndex.md`](../../references/04_OverrideIndex.md)
- [`references/07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md)
