---
name: components-actorcomponent
description: UActorComponent 로직 전용 - BeginPlay + EndPlay + TickComponent + GetOwner + Replication + Subobject 등록 + 6대 정책.
---

# Components · ActorComponent sub-skill

> **모듈**: Engine (Tier 1)
> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/ActorComponent.h`
> **다루는 범위**: `UActorComponent` 베이스 — 라이프사이클 / Tick / Activation / Replication / Subobject — 모든 컴포넌트의 **공통 부모**.

---

## 🚨 공통 정책 (Components 6대 의무)

> 모든 컴포넌트는 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) 의 5대 정책 적용.

| # | 정책 | 핵심 규칙 |
|---|------|-----------|
| 1 | **Mobility** | 생성자에서 `Static`/`Stationary`/`Movable` 명시. 런타임 `SetMobility` 금지 ([§1](../../../references/10_ComponentPolicies.md#1-mobility-정책-ecomponentmobilitystatic-stationary-movable)) |
| 2 | **NewObject + DuplicateObject** | Constructor=`CreateDefaultSubobject` / 런타임=`NewObject<T>(this)` / Deep copy=`DuplicateObject<T>(Source, Outer)` ([§2](../../../references/10_ComponentPolicies.md#2-newobject--duplicateobject-정책)) |
| 3 | **GC 방어** | UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>`. 비-UCLASS = `TStrongObjectPtr<T>` ([§3](../../../references/10_ComponentPolicies.md#3-gc-방어-전략)) |
| 4 | **GetOwner 캐싱** | `BeginPlay` 에서 `TWeakObjectPtr<AOwner>` 1회 캐싱. Tick/콜백 안 매번 Cast 금지 ([§4](../../../references/10_ComponentPolicies.md#4-getowner-캐싱-정책)) |
| 5 | **PrimaryComponentTick** | 기본 `bCanEverTick = false`. 필요 시 `TickInterval` 우선 (0.1~1s). 매 프레임 = 마지막 수단 ([§5](../../../references/10_ComponentPolicies.md#5-primarycomponenttick-정책)) |
| 6 | **CDO** | `GetMutableDefault` 로 CDO 변경 금지. `PostInitProperties` 안 `HasAnyFlags(RF_ClassDefaultObject)` 검사. `CreateDefaultSubobject` 는 Constructor 안만 ([§6](../../../references/10_ComponentPolicies.md#6-cdo-class-default-object-정책)) |

---

## 1. 개요

UE 의 **모든 컴포넌트의 베이스**. 트랜스폼이 없는 순수 로직 전용 컴포넌트(스탯·인벤토리·게임 로직 등)는 `UActorComponent` 직접 상속, 트랜스폼이 필요하면 `USceneComponent` ([`Components/SceneComponent`](../SceneComponent/SKILL.md))부터 자손 상속.

`UActorComponent` 가 정의하는 핵심 시스템:
- **라이프사이클** (`OnRegister`/`InitializeComponent`/`BeginPlay`/`Tick`/`EndPlay`/`UninitializeComponent`/`OnUnregister`)
- **Tick** (`PrimaryComponentTick` + ETickingGroup)
- **Activation** (Activate/Deactivate/SetActive/AutoActivate)
- **Replication** (`bReplicates`/`ReplicateSubobjects` + Iris)
- **Subobject** (UObject 계층 — Actor의 InstancedSubobject)

---

## 2. 핵심 헤더

| 클래스 | 위치 | 라인 | 의미 |
|--------|------|------|------|
| `UActorComponent` | `ActorComponent.h` | (헤더 전체) | 베이스 |
| `FActorComponentTickFunction` | (Engine/TickableObjectBase) | — | Tick 함수 구조 |
| `EComponentRegisterMethod` | (Component lifecycle) | — | 등록 방식 |
| `ELifetimeCondition` | `Engine/CoreNet.h` | — | 복제 조건 |

---

## 3. 라이프사이클 — 가장 중요

### 3.1 8단계 사이클 (Actor 생성 → 파괴)

```
[Actor 생성 (NewObject<AMyActor>)]
        │
        │ 컴포넌트 자동 생성 (생성자에서 CreateDefaultSubobject)
        ▼
[UActorComponent 인스턴스 — UPROPERTY 기본값 적용]
        │
        ▼
PostInitProperties()                    ← UObject (CoreUObject/UObject §4.1)
        │
        │ Actor::PostInitializeComponents 가 컴포넌트 등록 시작
        ▼
OnRegister()                            ← 컴포넌트 World에 등록 (CDO X — 인스턴스만)
   ├─ 자식 컴포넌트도 재귀 등록
   └─ Super::OnRegister() FIRST 의무
        │
        ▼
InitializeComponent() (bWantsInitializeComponent=true 일 때만)
   └─ Super::InitializeComponent() FIRST
        │
        │ AActor::BeginPlay 가 컴포넌트 BeginPlay 호출
        ▼
BeginPlay()                             ← 게임 시작 / 액터 스폰 / 등록 후
   └─ Super::BeginPlay() FIRST
        │
        ▼
Tick(DeltaTime) [매 프레임]              ← bCanEverTick=true 일 때만
   ├─ Super::Tick(DeltaTime) FIRST
   └─ 🚨 프로파일링 스코프 의무
        │
        │ Actor 파괴 시작
        ▼
EndPlay(EEndPlayReason::Type)
   └─ Super::EndPlay(...) LAST
        │
        ▼
UninitializeComponent()
   └─ Super::UninitializeComponent() LAST
        │
        ▼
OnUnregister()
   └─ Super::OnUnregister() LAST
        │
        ▼
BeginDestroy() → FinishDestroy()        ← UObject (Super LAST)
```

### 3.2 단계별 의미

| 단계 | 호출 횟수 | 용도 |
|------|----------|------|
| 생성자 | 인스턴스당 1회 | UPROPERTY 기본값 / `CreateDefaultSubobject` / `PrimaryComponentTick.bCanEverTick` 설정 |
| `PostInitProperties` | 1회 | UObject 베이스 — 거의 override 안 함 |
| `OnRegister` | 등록 시 (편집중·런타임) | 위젯/리소스 셋업 — 단, `IsTemplate()` 검사로 CDO 제외 |
| `InitializeComponent` | 1회 (런타임만) | **외부 시스템 구독·캐시 초기화** |
| `BeginPlay` | 1회 (런타임만) | **델리게이트 바인딩·초기 액션** |
| `Tick` | 매 프레임 | (가능하면 회피) |
| `EndPlay` | 1회 | **델리게이트 언바인딩·외부 참조 해제** |
| `UninitializeComponent` | 1회 | InitializeComponent의 짝 |
| `OnUnregister` | 1회 | OnRegister 의 짝 |

> **주의**: `OnRegister` 는 **에디터에서도 호출**됨 (CDO 제외). `InitializeComponent` / `BeginPlay` 는 **런타임 PIE/게임에서만**.

### 3.3 Super 호출 표 ([`04_OverrideIndex.md §6.1`](../../../references/04_OverrideIndex.md))

| virtual | Super | 위반 시 |
|---------|-------|---------|
| `OnRegister()` | **FIRST** | 자식 컴포넌트 미등록 |
| `OnUnregister()` | **LAST** (사용자 cleanup 후) | 정리 중 컴포넌트 무효 참조 |
| `InitializeComponent()` | **FIRST** | 베이스 초기화 누락 |
| `UninitializeComponent()` | **LAST** | 정리 중 베이스 호출 X |
| `BeginPlay()` | **FIRST** | bHasBegunPlay 미설정 / 자식 누락 |
| `Tick(DeltaTime)` | **FIRST + 프로파일링 스코프** | 베이스 무시 + 프로파일러 식별 X |
| `EndPlay(EEndPlayReason)` | **LAST** | bHasBegunPlay 가 false 인 채로 cleanup |
| `BeginDestroy()` | **LAST** | UObject 베이스 — 객체 무효 후 작업 X |

### 3.4 표준 작성 템플릿

```cpp
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class MYGAME_API UMyHealthComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UMyHealthComponent()
    {
        PrimaryComponentTick.bCanEverTick = false;     // 매 프레임 X
        SetIsReplicatedByDefault(true);                 // 복제 활성
        bWantsInitializeComponent = true;               // InitializeComponent 호출 받기
    }

    UPROPERTY(BlueprintAssignable)
    FOnHealthChanged OnHealthChanged;

    UFUNCTION(BlueprintCallable, Category="Health")
    void ApplyDamage(float Amount, AActor* Instigator);

protected:
    virtual void InitializeComponent() override
    {
        Super::InitializeComponent();    // ← FIRST
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyHealthComponent_InitializeComponent);
        // 외부 시스템 구독·캐시 초기화
    }

    virtual void BeginPlay() override
    {
        Super::BeginPlay();              // ← FIRST
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyHealthComponent_BeginPlay);
        // 델리게이트 바인딩·게임 로직 시작
    }

    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override
    {
        // 사용자 cleanup
        Super::EndPlay(EndPlayReason);   // ← LAST
    }

    virtual void Tick(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override
    {
        Super::Tick(DeltaTime, TickType, ThisTickFunction);
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyHealthComponent_Tick);
        // (가능하면 회피)
    }

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutProps) const override
    {
        Super::GetLifetimeReplicatedProps(OutProps);
        DOREPLIFETIME(UMyHealthComponent, CurrentHealth);
    }

    UPROPERTY(EditDefaultsOnly, Category="Health")
    float MaxHealth = 100.f;

    UPROPERTY(ReplicatedUsing=OnRep_CurrentHealth)
    float CurrentHealth = 100.f;

    UFUNCTION()
    void OnRep_CurrentHealth(float OldValue);
};
```

---

## 4. 자주 쓰는 API

### 4.1 등록 / 라이프사이클

| API | 의미 |
|-----|------|
| `bool IsRegistered() const` | 등록됨? |
| `void RegisterComponent()` | 명시 등록 |
| `void UnregisterComponent()` | 해제 |
| `bool HasBegunPlay() const` | BeginPlay 호출됨? |
| `bool IsBeingDestroyed() const` (L397) | 파괴 중? |
| `void DestroyComponent(bool bPromoteChildren=false)` | 파괴 요청 |

### 4.2 Activation (활성/비활성)

| API | 라인 | 의미 |
|-----|------|------|
| `void Activate(bool bReset=false)` | L457 | 활성 — 자식 자동 활성 |
| `void Deactivate()` | L463 | 비활성 |
| `void SetActive(bool bNewActive, bool bReset=false)` | L471 | 토글 |
| `void ToggleActive()` | L477 | |
| `bool IsActive() const` | (인라인) | |
| `void SetAutoActivate(bool)` | L491 | AutoActivate UPROPERTY 변경 |

### 4.3 소유자 / World

| API | 의미 |
|-----|------|
| `AActor* GetOwner() const` (L415) | 부모 액터 |
| `UWorld* GetWorld() const override final` (L425) | World 캐시 (성능) |
| `template<class T> T* GetOwner() const` | 템플릿 캐스팅 |
| `ENetRole GetOwnerRole() const` | 권한 (Authority/Autonomous/Simulated) |

### 4.4 Tick 제어

| API | 의미 |
|-----|------|
| `FActorComponentTickFunction PrimaryComponentTick` (UPROPERTY) | Tick 함수 |
| `void SetComponentTickEnabled(bool)` | 토글 |
| `void SetComponentTickInterval(float)` | 매 N초마다 (0=매 프레임) |
| `bool IsComponentTickEnabled() const` | |
| `bool ShouldTickIfViewportsOnly() const` | 에디터 뷰포트에서도 틱? |

### 4.5 Replication

| API | 라인 | 의미 |
|-----|------|------|
| `void SetIsReplicated(bool)` | (헤더) | 복제 토글 |
| `void SetIsReplicatedByDefault(bool)` | (헤더) | 디폴트 (생성자) |
| `bool GetIsReplicated() const` | | |
| `virtual bool ReplicateSubobjects(UActorChannel*, FOutBunch*, FReplicationFlags*)` | L525 | 서브오브젝트 복제 (수동) |
| `virtual ELifetimeCondition GetReplicationCondition() const` | L534 | 복제 조건 |
| `virtual void PreReplication(IRepChangedPropertyTracker&)` | L537 | 복제 직전 |
| `virtual bool GetComponentClassCanReplicate() const` | L540 | 클래스 자체 복제 가능? |

#### Iris (5.x 신규 복제 시스템) — 5.5.4 기준

| API | 라인 | 의미 |
|-----|------|------|
| `virtual void RegisterReplicationFragments(...)` | L643 | Iris 등록 |
| `virtual void BeginReplication()` | L646 | |
| `virtual void EndReplication()` | L649 | |

> ⚠ `OnReplicationStartedForIris` / `OnStopReplicationForIris` 콜백은 5.5.4 ActorComponent.h 에 존재하지 않음 (이후 버전 추가 추정).

### 4.6 에디터 콜백 🛠

| API | 의미 |
|-----|------|
| `virtual bool IsEditorOnly() const` (L585) | 에디터 빌드만? |
| `virtual void MarkAsEditorOnlySubobject()` (L588) | 에디터 전용 마킹 |

---

## 5. 가상 함수 / Super 호출 통합

### 5.1 라이프사이클 7종 (가장 자주 override)

§3.3 표 참조.

### 5.2 콜백 / 알림

| 시그니처 | 의미 |
|----------|------|
| `virtual void OnComponentCreated()` | 컴포넌트 생성 직후 (코드/디자이너) |
| `virtual void OnComponentDestroyed(bool bDestroyingHierarchy)` | 파괴 직전 |
| `virtual void OnRep_IsActive()` (L407) | IsActive 복제 변경 |
| `virtual void OnEndOfFrameUpdateDuringTick()` (L636) | 프레임 끝 갱신 |
| `virtual void OnPreEndOfFrameSync()` (L639) | 프레임 끝 동기 직전 |

### 5.3 활성화 정책

| 시그니처 | 의미 |
|----------|------|
| `virtual bool ShouldActivate() const` (L670) | 활성 가능? |

---

## 6. ETickingGroup (Tick 순서)

| 그룹 | 시점 |
|------|------|
| `TG_PrePhysics` | 물리 전 (기본) |
| `TG_StartPhysics` | 물리 시작 |
| `TG_DuringPhysics` | 물리 중 |
| `TG_EndPhysics` | 물리 끝 |
| `TG_PostPhysics` | 물리 후 (애니·이펙트) |
| `TG_PostUpdateWork` | 갱신 후 |
| `TG_LastDemotable` | 마지막 |

```cpp
PrimaryComponentTick.TickGroup = TG_PostPhysics;
```

Tick 의존성:

```cpp
PrimaryComponentTick.AddPrerequisite(OtherComponent, OtherComponent->PrimaryComponentTick);
```

---

## 7. Replication 패턴

### 7.1 단순 변수 복제

```cpp
UPROPERTY(Replicated)
float CurrentHealth;

virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutProps) const override
{
    Super::GetLifetimeReplicatedProps(OutProps);
    DOREPLIFETIME(UMyHealthComponent, CurrentHealth);
}
```

### 7.2 RepNotify

```cpp
UPROPERTY(ReplicatedUsing=OnRep_CurrentHealth)
float CurrentHealth;

UFUNCTION()
void OnRep_CurrentHealth(float OldValue)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyHealthComponent_OnRep_CurrentHealth);    // ← OnRep_* 의무
    OnHealthChanged.Broadcast(CurrentHealth);
}
```

### 7.3 조건부 복제

```cpp
DOREPLIFETIME_CONDITION(UMyHealthComponent, SecretValue, COND_OwnerOnly);
```

조건들: `COND_None`, `COND_InitialOnly`, `COND_OwnerOnly`, `COND_SkipOwner`, `COND_SimulatedOnly`, `COND_AutonomousOnly`, `COND_SimulatedOrPhysics`, `COND_Custom`.

### 7.4 RPC

```cpp
UFUNCTION(Server, Reliable, WithValidation)
void Server_ApplyDamage(float Amount);
void Server_ApplyDamage_Implementation(float Amount) { /* 서버 실행 */ }
bool Server_ApplyDamage_Validate(float Amount) { return Amount >= 0; }

UFUNCTION(NetMulticast, Unreliable)
void Multicast_PlayHitEffect();
void Multicast_PlayHitEffect_Implementation() { /* 모두 실행 */ }
```

자세한 — [`CoreUObject/Network`](../../CoreUObject/references/Network.md).

---

## 8. 함정 / 안티패턴

| 함정 | 회피 |
|------|------|
| 생성자에서 외부 World/Owner 접근 | World 미초기화 — `BeginPlay` 에서 |
| `OnRegister` 에서 게임 로직 | 에디터 호출 — `IsTemplate()` 검사 또는 `BeginPlay` 사용 |
| `Tick` 활성 후 무거운 작업 — 매 프레임 | `SetComponentTickInterval(0.1f)` 또는 이벤트 기반 |
| `BeginPlay` Super 누락 | bHasBegunPlay 미설정 → 분기 오작동 |
| `EndPlay` Super 먼저 호출 | 사용자 cleanup 시 베이스가 이미 정리됨 |
| `Tick` Super 누락 | 베이스 timer / TSlateAttribute 평가 누락 |
| 🚨 `Tick` 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) — 매 프레임 의무 |
| `OnRep_*` 스코프 누락 | 임의 시점 호출 — 의무 |
| `bWantsInitializeComponent=false` 에서 `InitializeComponent` 호출 기대 | true로 설정 의무 |
| 다른 컴포넌트 캐싱 안 함 — 매 호출마다 `FindComponentByClass` | `BeginPlay` 에서 1회 + `TWeakObjectPtr` 보관 |
| 직접 참조 (강 캡처) | `TWeakObjectPtr<UComponentX>` |
| `DestroyComponent` 호출 후 사용 | `IsValid` 검사 |
| `SetIsReplicated(true)` 만 — `GetLifetimeReplicatedProps` 누락 | 둘 다 의무 |
| 멀티플레이 권한 무시 | `HasAuthority()` 검사 — 서버에서만 변경 |

---

## 9. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 가드 | 의미 |
|------|------|------|
| `OnRegister()` (에디터에서도 호출) | (`IsTemplate()` 검사) | CDO 제외 |
| `IsEditorOnly()` (L585) | `WITH_EDITORONLY_DATA` | |
| `MarkAsEditorOnlySubobject()` 🛠 | `WITH_EDITOR` | |
| `PostEditChangeProperty(FPropertyChangedEvent&)` 🛠 | `WITH_EDITOR` | 디테일 패널 변경 |

자세한 — [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md).

---

## 10. 관련 sub-skill

- [`Components/SceneComponent`](../SceneComponent/SKILL.md) — 트랜스폼 + 계층 (UActorComponent 자손)
- [`Components/PrimitiveComponent`](../PrimitiveComponent/SKILL.md) — 콜리전 + 렌더 (USceneComponent 자손)
- [`CoreUObject/UObject`](../../CoreUObject/references/UObject.md) — UObject 라이프사이클 베이스
- [`CoreUObject/Reflection`](../../CoreUObject/references/Reflection.md) — UCLASS/UPROPERTY/UFUNCTION
- [`CoreUObject/Network`](../../CoreUObject/references/Network.md) — DOREPLIFETIME / RPC / Iris
- [`CoreUObject/GC`](../../CoreUObject/references/GC.md) — TObjectPtr / TWeakObjectPtr
- [`CoreUObject/Editor`](../../CoreUObject/references/Editor.md) — PostEditChangeProperty
- 교차: [`04_OverrideIndex.md §6.1`](../../../references/04_OverrideIndex.md) (라이프사이클 Super) · [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (Tick / OnRep_\* 스코프)
