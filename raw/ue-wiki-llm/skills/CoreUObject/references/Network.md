---
name: coreuobject-network
description: UFUNCTION RPC (Server/Client/NetMulticast) + DOREPLIFETIME + RepNotify (OnRep_*) + NetSerialize + Push Model + Owner/Connection/Authority 권한.
---

# CoreUObject / Network

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.7.4
> 다루는 영역: `UPackageMap` (네트워크 직렬화 ID 매핑), 네트워크 복제 virtual, `FLifetimeProperty`, `FNetBitReader/Writer`, Iris 통합 진입점
> 관련 sub-skill: [`UObject/`](../UObject/SKILL.md), [`Property/`](../Property/SKILL.md), [`Reflection/`](../Reflection/SKILL.md)

---

## 1. 개요

CoreUObject가 제공하는 네트워크 영역은 **네트워크-안전 객체/클래스 식별 + 비트 스트림 직렬화 베이스 + 복제용 UObject 가상 함수** 세 가지로 좁다. 실제 복제 정책·NetDriver·Connection은 `Engine` / `Net` / `OnlineSubsystem` 모듈로 빠진다.

핵심:

1. **`UPackageMap`** — 네트워크 GUID(`FNetworkGUID`) ↔ UObject 매핑. RPC·복제 시 객체를 식별.
2. **`FNetBitWriter`/`FNetBitReader`** — `FBitWriter`/`FBitReader` 의 UObject 인지 확장.
3. **복제 virtual** — `GetLifetimeReplicatedProps`, `PreNetReceive` 등 — 복제 활성 객체가 override.
4. **`FFieldNetCache`/`FClassNetCache`** — UFUNCTION/UPROPERTY 의 네트워크 ID 캐시.
5. **`RegisterReplicationFragments`** — 5.x Iris 시스템 통합 hook.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/CoreNet.h` | `UPackageMap` (L190, `: public UObject`), `FFieldNetCache` (L72), `FClassNetCache` (L90), `FClassNetCacheMgr` (L160), `FLifetimeProperty` (L299), `FPacketIdRange` (L258), `FPropertyRetirement` (L274), `TNetDoNotCopyPtr<T>` (L360), `FNetBitWriter : FBitWriter` (L383), `FNetBitReader : FBitReader` (L414), `INetDeltaBaseState` (L475), `INetSerializeCB` (L513) | 네트워크 직렬화 인프라. |
| `Public/UObject/CoreNetTypes.h` | `enum ELifetimeCondition` (L19), `ELifetimeRepNotifyCondition` (L42), `enum class EChannelCloseReason : uint8` (L48) | 복제 조건·채널 종료 사유. |
| `Public/UObject/CoreNetContext.h` | (네트워크 호출 컨텍스트) | RPC 디스패치 시 호출 스택 추적. |
| `Public/UObject/CoreNet.h` | `namespace UE::Net { ... }` | Iris (5.x 신규 복제 시스템) 진입 영역. |

> 실제 RPC 디스패치(`ProcessEvent`/`GetFunctionCallspace`/`CallRemoteFunction`)는 [`UObject/SKILL.md` §4.2](../UObject/SKILL.md) 참조 — 이 sub-skill에서는 그 결과로 사용되는 패키지맵·비트스트림·복제 메타에 집중.

### 2.1 ELifetimeCondition (`CoreNetTypes.h:19`) 자주 쓰는 값

```cpp
COND_None                 // 항상 복제
COND_InitialOnly          // 첫 복제만
COND_OwnerOnly            // 소유 클라이언트에만
COND_SkipOwner            // 소유 클라이언트 제외
COND_SimulatedOnly        // 시뮬레이트 프록시에만
COND_AutonomousOnly       // 오토노머스 프록시에만
COND_SimulatedOrPhysics   // 시뮬레이트 또는 물리 권한
COND_InitialOrOwner
COND_Custom               // 코드로 직접 결정 (DOREPLIFETIME_ACTIVE_OVERRIDE)
COND_ReplayOrOwner / COND_ReplayOnly / COND_SkipReplay
COND_Dynamic              // 런타임에 활성화 토글 가능
```

`DOREPLIFETIME_CONDITION` 매크로의 두 번째 인수가 이 enum.

---

## 3. 자주 쓰는 API

```cpp
// === 복제 프로퍼티 등록 (가장 흔한 진입점) ===
void AMyActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const
{
    Super::GetLifetimeReplicatedProps(Out);
    DOREPLIFETIME(AMyActor, Health);
    DOREPLIFETIME_CONDITION(AMyActor, Mana, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION_NOTIFY(AMyActor, Buffs, COND_None, REPNOTIFY_OnChanged);
}

// === Iris 신규 시스템 등록 (5.x) ===
void AMyActor::RegisterReplicationFragments(UE::Net::FFragmentRegistrationContext& Ctx,
                                            UE::Net::EFragmentRegistrationFlags Flags)
{
    Super::RegisterReplicationFragments(Ctx, Flags);
    // 추가 프래그먼트 등록 (커스텀 직렬화 등)
}

// === 비트 스트림 ===
FNetBitWriter Writer(/*PackageMap=*/Map, /*MaxBits=*/1024);
Writer << SomeUObject;     // PackageMap이 NetGUID로 변환
Writer.WriteBit(1);

FNetBitReader Reader(Map, Writer.GetData(), Writer.GetNumBits());
UObject* Obj = nullptr;
Reader << Obj;             // NetGUID → UObject 역변환

// === 클래스 네트워크 캐시 ===
FClassNetCache* C = ClassMgr->GetClassNetCache(MyClass);     // CoreNet.h L160
const FFieldNetCache* F = C->GetFromField(SomeProperty);
```

### 3.1 ProcessEvent / RPC 디스패치 (UObject 가상)

```cpp
// 호출 측은 보통 BP 노출 또는 매크로로 대체되지만, 이해는 다음과 같이:
void UObject::ProcessEvent(UFunction* Function, void* Parms);                     // Object.h L1499
int32 UObject::GetFunctionCallspace(UFunction* Function, FFrame* Stack);          // L1509  → FunctionCallspace::Local/Remote/Multicast
bool  UObject::CallRemoteFunction(UFunction*, void*, FOutParmRec*, FFrame*);      // L1523  → NetDriver로 전송
```

UFUNCTION 에 `Server`/`Client`/`NetMulticast` 가 붙으면 UHT가 `_Implementation` 분리·런타임 디스패치를 자동 합성한다.

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 UObject 복제 virtual (`Public/UObject/Object.h`)

| 시그니처 | 위치 | 호출 시점 / 용도 |
|----------|------|------------------|
| `virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>&) const` | Object.h L1052 | **복제할 UPROPERTY 등록** — 거의 모든 복제 액터/컴포넌트가 override. |
| `virtual void GetReplicatedCustomConditionState(FCustomPropertyConditionState&) const` | Object.h L1055 | 조건부 복제 상태 노출 (`COND_Custom`/`COND_Dynamic`). |
| `virtual void RegisterReplicationFragments(UE::Net::FFragmentRegistrationContext&, UE::Net::EFragmentRegistrationFlags)` | Object.h L1063 | Iris(5.x 신규 복제 시스템) 프래그먼트 등록. |
| `virtual bool IsNameStableForNetworking() const` | Object.h L1066 | Name 기반 식별이 네트워크에서 안정적인지 (StaticActor 등). |
| `virtual bool IsFullNameStableForNetworking() const` | Object.h L1069 | 전체 경로 안정성. |
| `virtual bool IsSupportedForNetworking() const` | Object.h L1072 | 네트워크 직렬화에 적합한지. |
| `virtual void GetSubobjectsWithStableNamesForNetworking(TArray<UObject*>&)` | Object.h L1076 | Name이 안정한 서브오브젝트 열거. |
| `virtual void PreNetReceive()` / `PostNetReceive()` | Object.h L1079 / L1082 | 복제 패킷 수신 전후. |
| `virtual void PostRepNotifies()` | Object.h L1085 | 모든 RepNotify 콜백 종료 후. |
| `virtual void PreDestroyFromReplication()` | Object.h L1088 | 서버 측 파괴를 클라이언트가 수신했을 때. |

### 4.2 ProcessEvent / Callspace virtual (UObject)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void ProcessEvent(UFunction*, void*)` | Object.h L1499 | UFUNCTION 디스패치. RPC 게이트로 자주 override. |
| `virtual int32 GetFunctionCallspace(UFunction*, FFrame*)` | Object.h L1509 | 로컬/원격 결정. |
| `virtual bool CallRemoteFunction(UFunction*, void*, FOutParmRec*, FFrame*)` | Object.h L1523 | 원격 호출 송신. |

### 4.3 INetDeltaBaseState (`CoreNet.h:475`) — 델타 복제 베이스 상태

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual bool IsStateEqual(INetDeltaBaseState*) = 0` | CoreNet.h L487 | 두 베이스 상태가 같은지 — 델타 직렬화 결정. |

### 4.4 INetSerializeCB (`CoreNet.h:513`) — 커스텀 NetSerialize 콜백

USTRUCT의 `NetSerialize` 가 호출하는 콜백 인터페이스. 일반 코드에서 직접 구현 안 함.

---

## 5. 예제

### 5.1 RepNotify 패턴 (가장 흔함)

```cpp
UCLASS()
class MYGAME_API AMyChar : public ACharacter
{
    GENERATED_BODY()
public:
    UPROPERTY(ReplicatedUsing=OnRep_Health, BlueprintReadOnly)
    float Health = 100.f;

    UPROPERTY(Replicated)
    int32 Score = 0;

    UFUNCTION()
    void OnRep_Health(float OldHealth);    // 5.x 시그니처: 옛 값 인자 가능

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const override;
};

void AMyChar::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& Out) const
{
    Super::GetLifetimeReplicatedProps(Out);
    DOREPLIFETIME(AMyChar, Health);
    DOREPLIFETIME_CONDITION(AMyChar, Score, COND_OwnerOnly);
}

void AMyChar::OnRep_Health(float OldHealth)
{
    if (Health < OldHealth) PlayHitFx();
}
```

### 5.2 Server RPC + Client 응답

```cpp
UFUNCTION(Server, Reliable, WithValidation)
void Server_RequestUse(UItem* Item);
// UHT가 자동으로 Server_RequestUse_Implementation 와 Server_RequestUse_Validate 를 분리

UFUNCTION(Client, Reliable)
void Client_NotifyUseResult(bool bOK);
```

```cpp
void AMyChar::Server_RequestUse_Implementation(UItem* Item)
{
    // 권한 검증 후
    Client_NotifyUseResult(true);          // 호출 측에서 자동으로 NetDriver 통해 전송
}

bool AMyChar::Server_RequestUse_Validate(UItem* Item)
{
    return Item != nullptr;
}
```

### 5.3 PreNetReceive/PostNetReceive 활용

```cpp
void AMyChar::PreNetReceive()
{
    Super::PreNetReceive();
    // 복제 적용 전 스냅샷 저장
    SavedTransform = GetActorTransform();
}

void AMyChar::PostNetReceive()
{
    Super::PostNetReceive();
    // 복제로 변경된 트랜스폼과 비교해 보간/보정
    BlendToReplicatedTransform(SavedTransform);
}
```

### 5.4 비트 스트림 직접 사용 (USTRUCT NetSerialize)

```cpp
USTRUCT()
struct FCompactVector
{
    GENERATED_BODY()
    int16 X, Y, Z;

    bool NetSerialize(FArchive& Ar, UPackageMap* Map, bool& bOutSuccess)
    {
        Ar << X; Ar << Y; Ar << Z;
        bOutSuccess = true;
        return true;
    }
};

template<> struct TStructOpsTypeTraits<FCompactVector>
    : public TStructOpsTypeTraitsBase2<FCompactVector>
{ enum { WithNetSerializer = true }; };
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| (없음 — 본 영역은 거의 전부 런타임 전용) | — | — | 네트워크 코드는 게임 빌드에서 동작. |

> 참고: 일부 디버그·통계(예: `FNetTraceCollector` 일부 경로)는 `UE_TRACE_ENABLED` 또는 디버그 빌드 가드. 게임 런타임 자체에는 에디터 전용 가드가 거의 없다.

---

## 7. 관련 sub-skill

- [`UObject/`](../UObject/SKILL.md) — `ProcessEvent`/`GetFunctionCallspace`/`CallRemoteFunction` 본체
- [`Reflection/`](../Reflection/SKILL.md) — UFUNCTION 의 `Server`/`Client`/`NetMulticast` 메타가 RPC 디스패치를 만든다
- [`Property/`](../Property/SKILL.md) — `FProperty`의 네트 직렬화 경로
- [`Serialization/`](../Serialization/SKILL.md) — `FNetBitWriter` 가 `FBitWriter`(Core) 의 확장
