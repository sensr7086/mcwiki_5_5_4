---
name: gameframework-actor
description: AActor 베이스 (가장 중요) - 라이프사이클 11단계 (PostInitProperties → InitializeComponents → BeginPlay → Tick → EndPlay → BeginDestroy) + Super 호출 규약 + 6대 정책 + SpawnActorDeferred + FinishSpawning.
---

# GameFramework/Actor — AActor 베이스 (가장 중요)

> **위치**: `Engine/Source/Runtime/Engine/Classes/GameFramework/Actor.h` (4,912 lines — 본 위키 가장 큰 헤더 중 하나)
> **베이스**: `AActor : public UObject`
> **요지**: **모든 게임 오브젝트의 베이스** — Pawn / Character / Controller / GameMode / GameState / PlayerState 등 모두 Actor 자손. **컴포넌트 호스트** + **World 안 1급 시민**. 라이프사이클·Tick·Replication·Spawn 의 모든 진입점.

---

## 🚨 공통 정책 (Components 6대 의무 + Actor 특화)

> 모든 Actor 작성 시 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) 의 6대 정책 + Actor 추가 규칙.

| # | 정책 | Actor 적용 |
|---|------|----------|
| 1 | **Mobility (RootComponent)** | RootComponent SceneComponent 자손 — 생성자에서 Mobility 명시. Pawn 의 RootComponent = Capsule (Movable 강제). 환경 정적 Mesh = `Static`. |
| 2 | **NewObject + DuplicateObject** | **Actor = `World->SpawnActor<T>(Class, Transform)` 만 사용** — `NewObject<AActor>` 직접 호출 절대 금지 (Spawn 라이프사이클 우회 — PostSpawnInitialize/OnConstruction/InitializeComponents/BeginPlay 모두 누락). Outer = `UWorld`. Component 는 Constructor 안 `CreateDefaultSubobject` (CDO subobject) 또는 런타임 `NewObject<UComp>(this)` + `RegisterComponent()`. |
| 3 | **GC 방어** | `UPROPERTY()` + `TObjectPtr<AActor>` (멤버) / `TWeakObjectPtr<AActor>` (캐싱·Lifetime 분리 — 다른 Actor 참조 표준) / `TStrongObjectPtr` (비-UCLASS — 드물다). Spawn 한 Actor 는 **World 가 OwnedActors 배열로 강참조** 하므로 자동 GC 보호. **명시적 Destroy 필요 시 `Destroy()` 호출**. |
| 4 | **GetController / GetPawn / GetWorld 캐싱** | `BeginPlay` 에서 1회 캐싱 → `TWeakObjectPtr<AController> CachedController` 보관 + 매 Tick/콜백 재조회 금지. Pawn 의 PossessedBy / OnPossess 콜백에서만 갱신. |
| 5 | **PrimaryActorTick** | 기본 `bCanEverTick = false` + 필요 시 `TickGroup = TG_PrePhysics` (표준) + `TickInterval` (0.05~1s) 우선 + 매 프레임 = 마지막 수단. **Actor Tick 은 Component 들의 컨테이너** — Actor::Tick 안에 매 프레임 로직 작성 시 모든 Component 도 동시 Tick (대량 누적). |
| 6 | **CDO + OnConstruction** | `GetMutableDefault<AActor>()` Set 금지 + `PostInitProperties` 안 `HasAnyFlags(RF_ClassDefaultObject)` 검사 + `CreateDefaultSubobject` 는 Constructor 안만 + **`OnConstruction(Transform)` 매번 멱등** (RerunConstructionScripts 매번 호출 — 누적 작업 금지). |

---

## 1. AActor 라이프사이클 11단계 (가장 중요)

> [`Actor.h`](../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/GameFramework/Actor.h) — 11개 virtual 함수의 호출 순서. **Super 호출 규약** + **각 단계의 안전한 작업** 명확히 이해 필수.

### 1.1 호출 순서 (스폰 → 디스폰)

```
[1] Constructor             ── CDO 생성 + 매 인스턴스 — Component CreateDefaultSubobject 만
[2] PostInitProperties()    ── UObject 베이스 — UPROPERTY 기본값 적용 후
[3] PostSpawnInitialize()   ── 트랜스폼·Owner·Instigator 적용 (private — 직접 override X)
[4] OnConstruction(Transform) ── BP Construction Script + 매 RerunConstructionScripts (멱등 의무)
[5] PostActorConstruction
    ↓ PreInitializeComponents()
    ↓ InitializeComponents()  ── 모든 Component->RegisterComponent (Component->BeginPlay 아직 X)
    ↓ PostInitializeComponents()
[6] FinishSpawning()        ── Replication 라우팅 + bHasFinishedSpawning = true
[7] BeginPlay()             ── Component 들의 BeginPlay 도 함께 (UWorld 가 BeginPlayActor 면)
[8] Tick(DeltaSeconds)      ── 매 프레임 (PrimaryActorTick.bCanEverTick == true 일 때만)

[ Destroy() / 종료 ]
[9] EndPlay(Reason)         ── Component 들의 EndPlay 도 함께
[10] Destroyed()            ── 즉시 콜백 (현재 프레임 — UObject 는 살아있음)
[11] BeginDestroy()         ── UObject GC 직전 (다음 GC 사이클 — 멤버 nullptr 가능)
```

### 1.2 각 virtual 의 위치 + Super 호출 규약

| # | virtual | 위치 | Super 위치 | 안전한 작업 | 금지 작업 |
|---|---------|------|-----------|-----------|----------|
| 1 | `AActor()` Constructor | (생성자) | (없음) | `CreateDefaultSubobject<UComp>(TEXT("Name"))` / `PrimaryActorTick.bCanEverTick = false` 등 기본값 | ⚠️ `GetWorld()` / `GetGameInstance()` (둘 다 nullptr) / 다른 Actor 참조 / `bCanEverTick = true` (검토 후만) |
| 2 | `PostInitProperties()` | `Actor.h:2346` | **처음** | `RF_ClassDefaultObject` 검사 후 CDO 만 작업 / 멤버 초기화 (UPROPERTY 적용 후) | `BeginPlay`-시점 데이터 / Replication |
| 3 | `OnConstruction(FTransform)` | `Actor.h:3448` | **처음** | BP Construction Script + 멱등 작업만 (Mesh 정리·재생성 등) | ⚠️ 누적·증분 작업 (이전 상태 의존) / 다른 Actor 참조 / GameMode 접근 |
| 4 | `PreInitializeComponents()` | `Actor.h:3123` | **처음** | Component 등록 직전 — 베이스 데이터 셋업 | Component 간 페어 셋업 (아직 Init 안 끝남) |
| 5 | `PostInitializeComponents()` | `Actor.h:3126` | **처음** | 모든 Component->Init 완료 — Component 간 페어 셋업 / Delegate 바인딩 | BeginPlay-시점 데이터 (아직 BeginPlay 전) |
| 6 | `BeginPlay()` | `Actor.h:2128` | **처음** | 다른 Actor 참조 / GameMode / Controller / Tick 활성화 / 타이머 시작 / Replication 시작 | EndPlay-시점 데이터 |
| 7 | `Tick(DeltaSeconds)` | `Actor.h:3059` | **처음** | 매 프레임 로직 (단 `PrimaryActorTick.bCanEverTick = true` 일 때만) | 무거운 로직 (Component Tick 으로 분리) / Spawn 이 매 프레임 |
| 8 | `EndPlay(EEndPlayReason)` | `Actor.h:2135` | **마지막** | Delegate 해제 / 타이머 정리 / 다른 Actor 참조 정리 (아직 World 살아있음) | UObject 멤버 직접 nullptr 화 (GC 가 처리) |
| 9 | `Destroyed()` | `Actor.h:3568` | **마지막** | 즉시 정리 (현재 프레임 — Owner/OwnedActors 정리 등) | EndPlay 다음 단계인지 확인 (둘 다 호출됨) |
| 10 | `BeginDestroy()` | `Actor.h:2357` | **마지막** | UObject GC 직전 — 비-UObject 리소스 해제 | UObject 멤버 접근 (이미 nullptr 가능) |

### 1.3 표준 라이프사이클 코드 템플릿

```cpp
// MyActor.h
UCLASS()
class AMyActor : public AActor
{
    GENERATED_BODY()
public:
    AMyActor();

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void PreInitializeComponents() override;
    virtual void PostInitializeComponents() override;
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Destroyed() override;
    virtual void BeginDestroy() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UStaticMeshComponent> Mesh;

    // 캐싱 — BeginPlay 에서 채움
    TWeakObjectPtr<AActor> CachedTarget;

    UPROPERTY(Replicated)
    int32 ReplicatedHealth = 100;
};

// MyActor.cpp
AMyActor::AMyActor()
{
    PrimaryActorTick.bCanEverTick = false;       // 기본 OFF
    PrimaryActorTick.TickGroup = TG_PrePhysics;
    PrimaryActorTick.TickInterval = 0.f;          // 매 프레임 (활성 시)
    bReplicates = false;                          // 필요 시만 활성

    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    RootComponent = Root;

    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
    Mesh->SetupAttachment(Root);
    Mesh->SetMobility(EComponentMobility::Movable);
}

void AMyActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);   // ⚠️ 처음

    // 멱등 — 매번 호출 가능. 이전 상태 의존 X
    // 정답: 기존 Component 정리 후 다시 생성
}

void AMyActor::PreInitializeComponents()
{
    Super::PreInitializeComponents();   // ⚠️ 처음
    // Component Init 직전 — 베이스 셋업
}

void AMyActor::PostInitializeComponents()
{
    Super::PostInitializeComponents();  // ⚠️ 처음
    // 모든 Component Init 완료 — 페어 셋업 가능
}

void AMyActor::BeginPlay()
{
    Super::BeginPlay();                 // ⚠️ 처음
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyActor::BeginPlay);

    // 다른 Actor 참조 안전 — 모두 BeginPlay 시점
    CachedTarget = Cast<AActor>(UGameplayStatics::GetPlayerPawn(this, 0));
    GetWorld()->GetTimerManager().SetTimer(MyTimer, this, &AMyActor::OnTick, 1.f, true);
}

void AMyActor::Tick(float DeltaSeconds)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyActor::Tick);
    Super::Tick(DeltaSeconds);          // ⚠️ 처음

    if (CachedTarget.IsValid())
    {
        // 매 프레임 로직 — 캐싱 사용
    }
}

void AMyActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    GetWorld()->GetTimerManager().ClearAllTimersForObject(this);
    // ... 정리 작업 먼저
    Super::EndPlay(EndPlayReason);      // ⚠️ 마지막
}

void AMyActor::Destroyed()
{
    // 즉시 정리 (현재 프레임)
    Super::Destroyed();                 // ⚠️ 마지막
}

void AMyActor::BeginDestroy()
{
    // 비-UObject 리소스 해제
    Super::BeginDestroy();              // ⚠️ 마지막
}

void AMyActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AMyActor, ReplicatedHealth);
}
```

> **Super 호출 통합 표는 [`04_OverrideIndex.md §6`](../../../references/04_OverrideIndex.md)** — Actor + Component + Widget 모든 라이프사이클 통합.

---

## 2. Spawn 시스템 (UWorld::SpawnActor)

### 2.1 표준 Spawn (즉시 BeginPlay)

```cpp
FActorSpawnParameters Params;
Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
Params.Owner = this;
Params.Instigator = GetInstigator();
Params.Name = TEXT("MyActor_1");        // 안정적 이름 (Replication 안전)

AMyActor* NewActor = GetWorld()->SpawnActor<AMyActor>(
    AMyActor::StaticClass(),
    SpawnLocation,
    SpawnRotation,
    Params
);
// NewActor 는 이미 BeginPlay 호출 완료 상태
```

### 2.2 Deferred Spawn (Spawn → 초기화 → FinishSpawning)

> Spawn 후 Property 초기화 + Component 셋업 후 **BeginPlay 활성** — UPROPERTY 의 초기값을 BeginPlay 가 보게 하려면 필수.

```cpp
AMyActor* NewActor = GetWorld()->SpawnActorDeferred<AMyActor>(
    AMyActor::StaticClass(),
    SpawnTransform,
    /*Owner=*/ this,
    /*Instigator=*/ GetInstigator(),
    ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn
);
// 이 시점 — Constructor + PostInitProperties 만 호출됨. BeginPlay 아직.

if (NewActor)
{
    NewActor->Damage = 50.f;            // BeginPlay 가 보게 됨
    NewActor->bIsExplosive = true;
    NewActor->FinishSpawning(SpawnTransform);   // 이때 BeginPlay 호출
}
```

### 2.3 ESpawnActorCollisionHandlingMethod (콜리전 처리)

```cpp
enum class ESpawnActorCollisionHandlingMethod : uint8
{
    Undefined,                          // 기본
    AlwaysSpawn,                        // 콜리전 무시 — 항상 Spawn
    AdjustIfPossibleButAlwaysSpawn,     // 가까운 빈 위치 찾기 — 실패 시 그대로 Spawn (가장 안전)
    AdjustIfPossibleButDontSpawnIfColliding,
    DontSpawnIfColliding                // 콜리전 시 nullptr 반환
};
```

### 2.4 Owner / Instigator (네트워크 + 데미지 추적)

| 필드 | 의미 | 결정 시점 |
|------|------|----------|
| `Owner` | **Replication 라우팅** + `bOnlyRelevantToOwner` 시 클라이언트 결정 + `bOwnerNoSee/bOnlyOwnerSee` (Mesh 가시성) | Spawn Params + `SetOwner()` |
| `Instigator` | **데미지 추적** — 누가 트리거했나 (예: 발사한 Pawn) | Spawn Params + 자동 (Owner 가 Pawn 이면 Instigator = Owner) |

```cpp
// 발사체 Spawn — Owner = 무기 Actor / Instigator = 발사한 Pawn
ABullet* Bullet = World->SpawnActor<ABullet>(BulletClass, MuzzleLoc, MuzzleRot, Params);
Bullet->SetOwner(this);                 // 무기 Actor
Bullet->SetInstigator(GetOwner<APawn>());   // 발사한 Pawn
```

### 2.5 Destroy

```cpp
// 명시적 Destroy
GetWorld()->DestroyActor(MyActor);       // 또는 MyActor->Destroy()

// 라이프타임 자동 — World 종료 시 모든 Actor->EndPlay → Destroyed → BeginDestroy
// Streaming Level Unload 시 그 Level 의 Actor 들 Destroy
```

> **함정**: `delete MyActor` 절대 금지 — UObject 는 GC 만 해제. `Destroy()` 호출 후 다음 GC 사이클에 BeginDestroy.

---

## 3. Tick 시스템 (PrimaryActorTick + FActorTickFunction)

### 3.1 PrimaryActorTick 핵심 필드

```cpp
struct FActorTickFunction : public FTickFunction
{
    bool bCanEverTick;                   // 베이스 — Tick 활성화 가능 여부 (false = 영구 OFF)
    bool bStartWithTickEnabled;          // BeginPlay 시 자동 활성
    bool bAllowTickOnDedicatedServer;    // Dedicated Server 에서도 Tick
    ETickingGroup TickGroup;             // TG_PrePhysics / DuringPhysics / PostPhysics 등
    float TickInterval;                  // 0 = 매 프레임 / >0 = N초 간격 (Significance 통합)
    TArray<FTickPrerequisite> Prerequisites; // 다른 TickFunction 종속
};
```

### 3.2 ETickingGroup (Tick 순서)

| 그룹 | 의미 | 표준 사용 |
|------|------|----------|
| `TG_PrePhysics` | 물리 시뮬 전 (가장 먼저) | 일반 Actor·Component (기본값) |
| `TG_StartPhysics` | 물리 시뮬 시작 | (드물게) |
| `TG_DuringPhysics` | 물리 시뮬 중 | 물리 객체 보조 |
| `TG_EndPhysics` | 물리 시뮬 끝 | 물리 결과 후처리 |
| `TG_PostPhysics` | 물리 후 | Skeletal Mesh Anim 적용 후 |
| `TG_PostUpdateWork` | 가장 마지막 | 카메라 (모든 위치 결정 후) |

```cpp
PrimaryActorTick.TickGroup = TG_PostUpdateWork;   // 카메라 — 모든 Pawn 위치 후
```

### 3.3 TickInterval — 매 프레임 회피 (표준)

```cpp
PrimaryActorTick.TickInterval = 0.1f;    // 100ms 간격 — 매 프레임 1/6 비용
PrimaryActorTick.TickInterval = 1.f;     // 1초 — Status 갱신 등
```

> **5.x Significance 통합**: `USignificanceManager` 가 거리에 따라 자동 TickInterval 조정 — [`Significance/SKILL.md`](../../Significance/SKILL.md).

### 3.4 SetActorTickEnabled (런타임 토글)

```cpp
// BeginPlay 후 활성
SetActorTickEnabled(true);

// Idle 상태 — Tick 끄기 (성능)
SetActorTickEnabled(false);

// 인터벌만 변경
SetActorTickInterval(0.5f);
```

### 3.5 Tick Prerequisite (의존 Tick)

```cpp
// MyActor 가 OtherActor 의 Tick 후에만 Tick
AddTickPrerequisiteActor(OtherActor);

// MyComponent 가 다른 Component 후에만 Tick
MyComp->AddTickPrerequisiteComponent(OtherComp);
```

> **함정**: Prerequisite 가 nullptr 또는 Destroyed 시 자동 정리되지 않음 — `RemoveTickPrerequisiteActor` 필요.

---

## 4. Component 등록 시스템

### 4.1 OwnedComponents — Actor 가 소유한 Component 집합

```cpp
// Actor.h:1073~ — TSet<UActorComponent*> OwnedComponents

// 검색 — 가장 흔한 패턴
UHealthComponent* HealthComp = FindComponentByClass<UHealthComponent>();

// 다중 검색
TArray<UStaticMeshComponent*> MeshComps;
GetComponents<UStaticMeshComponent>(MeshComps);
GetComponents<UStaticMeshComponent>(MeshComps, /*bIncludeFromChildActors=*/ true);

// Tag 기반 검색
TArray<UActorComponent*> Tagged = GetComponentsByTag(UActorComponent::StaticClass(), TEXT("MyTag"));

// Interface 기반 검색
TArray<UActorComponent*> Interfaced = GetComponentsByInterface(UDamageableInterface::StaticClass());
```

### 4.2 RegisterAllComponents 흐름

```cpp
// Actor::PostActorConstruction 안 자동 호출
RegisterAllComponents()
  ↓ PreRegisterAllComponents()      (Actor.h:3231)
  ↓ for each Component: Component->RegisterComponent()
  ↓ PostRegisterAllComponents()     (Actor.h:3237)
```

### 4.3 런타임 Component 추가 (`NewObject` + `RegisterComponent`)

```cpp
// 런타임 Component 추가 — 매 프레임 비용 있음
USphereComponent* NewSphere = NewObject<USphereComponent>(this, TEXT("DynamicSphere"));
NewSphere->SetupAttachment(RootComponent);
NewSphere->SetSphereRadius(100.f);
NewSphere->RegisterComponent();          // ⚠️ 의무 — 등록 안 하면 Tick / Render 안 됨
AddInstanceComponent(NewSphere);         // 에디터 노출 (선택)
```

> **함정**: `NewObject<UComp>(Outer)` 의 Outer = `this` (Actor) — 다른 Actor 의 Component 가 되면 Owner 잘못됨.

### 4.4 BeginPlay 시점의 Component

```cpp
void AMyActor::BeginPlay()
{
    Super::BeginPlay();
    // 이 시점 — 모든 Component->BeginPlay 도 함께 호출됨 (UWorld 가 Actor BeginPlay 활성 시)
    // FindComponentByClass / GetComponents 안전
}
```

---

## 5. Replication / Network

### 5.1 핵심 필드 + Setter (5.5+)

```cpp
// 기본 활성
bReplicates = true;                       // (Actor.h:556)

// Replication 빈도 — 5.5 부터 Setter 의무
SetNetUpdateFrequency(10.f);              // 10Hz — 일반 Actor (기본 100)
SetMinNetUpdateFrequency(2.f);            // 최소 2Hz — 거리 멀어질수록 감소
SetNetCullDistanceSquared(15000.f * 15000.f);   // 150m 밖 컬링

// Relevancy
bAlwaysRelevant = true;                   // (Actor.h:300) — 모든 클라 항상 Replication
bOnlyRelevantToOwner = true;              // (Actor.h:296) — Owner 클라만
bNetUseOwnerRelevancy = true;             // Owner 가 Relevant 면 본인도

NetPriority = 1.f;                        // 우선순위 (1.0 기본)
```

### 5.2 권한 (Authority) 검사 패턴

```cpp
// HasAuthority() — Server/StandaloneGame 인지
if (HasAuthority())
{
    // 서버 only 로직 — Replication 변경 / 다른 Actor Spawn / Destroy
    Health -= Damage;
    OnRep_Health(OldHealth);              // 서버는 직접 호출 (RepNotify 자동 X)
}

// GetLocalRole() / GetRemoteRole()
ENetRole MyRole = GetLocalRole();         // ROLE_Authority (서버) / ROLE_AutonomousProxy (소유 클라) / ROLE_SimulatedProxy (다른 클라)
ENetRole RemoteRole = GetRemoteRole();    // 반대편

// GetNetMode()
switch (GetNetMode())
{
    case NM_Standalone:    /* 싱글 */ break;
    case NM_DedicatedServer: /* 데디케이트 */ break;
    case NM_ListenServer:  /* 리슨 */ break;
    case NM_Client:        /* 클라 */ break;
}
```

### 5.3 GetLifetimeReplicatedProps + DOREPLIFETIME

```cpp
// MyActor.h
UPROPERTY(Replicated)
int32 SimpleHealth;

UPROPERTY(ReplicatedUsing=OnRep_Health)
int32 NotifiedHealth;

UPROPERTY(Replicated, EditAnywhere, meta=(ClampMin=0, ClampMax=100))
TArray<int32> ReplicatedArray;

// MyActor.cpp
void AMyActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    // 표준
    DOREPLIFETIME(AMyActor, SimpleHealth);
    DOREPLIFETIME(AMyActor, NotifiedHealth);

    // 조건부 — 자세한 옵션
    DOREPLIFETIME_CONDITION(AMyActor, ReplicatedArray, COND_OwnerOnly);   // Owner 만
    DOREPLIFETIME_CONDITION_NOTIFY(AMyActor, NotifiedHealth, COND_None, REPNOTIFY_Always);
}

UFUNCTION()
void AMyActor::OnRep_Health(int32 OldHealth)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyActor::OnRep_Health);
    UpdateHealthBar();
}
```

### 5.4 RPC (Server / Client / NetMulticast)

```cpp
// 서버에 호출 (클라 → 서버)
UFUNCTION(Server, Reliable, WithValidation)
void Server_Fire(FVector Direction);

// 모든 클라에 호출 (서버 → 모든 클라)
UFUNCTION(NetMulticast, Reliable)
void Multicast_Explode();

// 특정 Owner 클라에 호출 (서버 → Owner 클라)
UFUNCTION(Client, Reliable)
void Client_PlayHitEffect();

// 검증 함수 (Server RPC 의무)
bool AMyActor::Server_Fire_Validate(FVector Direction) { return Direction.IsNormalized(); }
void AMyActor::Server_Fire_Implementation(FVector Direction)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyActor::Server_Fire);
    // 서버에서 실행
}
```

> **자세한 Replication 패턴은 [`CoreUObject/Network`](../../CoreUObject/references/Network.md)**.

---

## 6. Owner / Instigator / Children

| API | 반환 |
|-----|------|
| `GetOwner()` | 부모 Actor (Spawn 시 설정 — 무기 Actor 의 Owner = Pawn 등) |
| `GetInstigator()` | 데미지 추적용 Pawn (발사한 Pawn) |
| `GetInstigatorController()` | Pawn 의 Controller |
| `GetParentActor()` | ChildActorComponent 호스트 |
| `Children` | 자식 Actor 배열 (Children = 다른 Actor 의 Owner == this) |

```cpp
// 무기 데미지 — Instigator 추적
void ABullet::ApplyDamage(AActor* HitActor, float Damage)
{
    UGameplayStatics::ApplyDamage(
        HitActor,
        Damage,
        GetInstigatorController(),       // 발사한 Pawn 의 Controller
        this,                              // 발사체 자체
        UDamageType::StaticClass()
    );
}
```

---

## 7. 함정 & 안티패턴 (12종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | Constructor 안 `GetWorld()` 호출 | nullptr — Constructor 안에서는 World 안 만들어짐. `BeginPlay` 에서 호출 |
| 2 | OnConstruction 안 누적 작업 (Mesh 추가 → 다음 호출에 또 추가) | 멱등 의무 — 기존 정리 후 재생성 (또는 변경 없으면 작업 안 함) |
| 3 | `NewObject<AActor>(Outer)` 직접 호출 | ⚠️ Spawn 라이프사이클 우회 — 항상 `World->SpawnActor<T>` |
| 4 | BeginPlay 에서 Component 검색 안 캐싱 | TWeakObjectPtr 캐싱 — Tick 안 매번 FindComponentByClass 비용 |
| 5 | `SetActorLocation` 매 프레임 호출 (Sweep=false) | Sweep=true 또는 SetActorLocationAndRotation — 콜리전·이동 동기 안전 |
| 6 | `Destroy()` 후 즉시 멤버 접근 | EndPlay → Destroyed 후 BeginDestroy 까지 살아있지만, Tick 함수는 자동 비활성. 다음 프레임은 안전 |
| 7 | Replication 변경 후 OnRep_ 직접 호출 안 함 (서버) | 서버는 RepNotify 자동 X — 직접 호출하거나 `MARK_PROPERTY_DIRTY` |
| 8 | bReplicates 활성 안 한 Actor 의 RPC 호출 | Replication 안 됨 — `bReplicates = true` 필수 |
| 9 | Server RPC 에 `WithValidation` 누락 | UE 5+ 컴파일 오류 — 모든 Server RPC 는 Validation 의무 |
| 10 | `PrimaryActorTick.bCanEverTick = true` 기본값 | 기본 false — Tick 필요한 Actor 만 활성 (성능) |
| 11 | 🚨 Tick / 콜백 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |
| 12 | 🚨 BeginPlay 안 `TActorIterator<T>` 사용 | 매 호출 N개 순회 — Subsystem 등록 패턴 사용 ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |

---

## 8. 체크리스트 (Actor 자식 작성 시)

- [ ] Constructor: `PrimaryActorTick.bCanEverTick = false` 기본
- [ ] Constructor: `bReplicates` 명시 (필요 시만 true)
- [ ] Constructor: `CreateDefaultSubobject` 만 사용 — `NewObject` 금지
- [ ] Constructor: `RootComponent` 명시 + Mobility 명시
- [ ] PostInitProperties: `RF_ClassDefaultObject` 검사 (CDO 만 작업)
- [ ] OnConstruction: 멱등 (이전 상태 의존 X) + Super 처음
- [ ] PreInit/Init/PostInit: Super 처음
- [ ] BeginPlay: Super 처음 + 캐싱 (TWeakObjectPtr) + Tick 활성화 (필요 시)
- [ ] Tick: Super 처음 + 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] EndPlay/Destroyed/BeginDestroy: Super 마지막
- [ ] GetLifetimeReplicatedProps: Super 처음 + DOREPLIFETIME
- [ ] Server RPC: WithValidation + _Validate 의무
- [ ] HasAuthority() 검사 — Replication 변경 / Spawn / Destroy
- [ ] 🚨 6대 정책 모두 만족 ([`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md))
- [ ] 🚨 전역 이터레이터 사용 안 했는가 ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md))

---

## 9. 관련 sub-skill

- [`GameFramework/PawnCharacter`](../PawnCharacter/SKILL.md) — Actor 자식 (입력·이동)
- [`GameFramework/Controller`](../Controller/SKILL.md) — Actor 자식 (Pawn 소유)
- [`GameFramework/GameMode`](../GameMode/SKILL.md) — Actor 자식 (서버 only)
- [`Components/ActorComponent`](../../Components/references/ActorComponent.md) — Actor 안 부속
- [`Components/SceneComponent`](../../Components/references/SceneComponent.md) — Actor 의 RootComponent 표준
- [`CoreUObject/UObject`](../../CoreUObject/references/UObject.md) — UObject 베이스 (PostInitProperties / BeginDestroy)
- [`CoreUObject/Network`](../../CoreUObject/references/Network.md) — DOREPLIFETIME / RPC
- 교차: [`04_OverrideIndex.md`](../../../references/04_OverrideIndex.md) (라이프사이클 통합) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) · [`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md) · [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md)

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. AActor 4,912 lines 분석. 라이프사이클 11단계 (Constructor/PostInitProperties/PostSpawnInitialize/OnConstruction/PreInit/Init/PostInit/FinishSpawning/BeginPlay/Tick/EndPlay/Destroyed/BeginDestroy) + Super 호출 규약 + 표준 코드 템플릿. Spawn 4종 (즉시·Deferred·CollisionHandling·Owner/Instigator) + Tick (PrimaryActorTick + ETickingGroup 6종 + TickInterval + Prerequisite) + Component 등록 (OwnedComponents/FindComponentByClass/GetComponents/RegisterComponent) + Replication (bReplicates/SetNetUpdateFrequency 5.5/HasAuthority/GetLocalRole/GetNetMode/DOREPLIFETIME/RPC). 함정 12종 + 14단 체크리스트. |
