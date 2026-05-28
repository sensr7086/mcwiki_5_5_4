---
type: synthesis
title: "Actor Pool + Reset 패턴 — BeginPlay/EndPlay 우회 + 캐싱 weak ptr 무효화 + Tick 토글"
slug: actor-pool-reset-pattern
created: 2026-05-10
last_updated: 2026-05-13
sources:
  - "[[sources/ue-gameframework-actor]]"
  - "[[sources/ue-components-actorcomponent]]"
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/ue-niagara-skill]]"
  - "[[sources/ue-significance-skill]]"
  - "[[sources/ue-subsystem-skill]]"
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
entities:
  - "[[entities/AActor]]"
  - "[[entities/UActorComponent]]"
  - "[[entities/USignificanceManager]]"
concepts:
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
status: living
tags: [synthesis, actor-pool, reset, performance, lifecycle, kmcproject]
---

# Actor Pool + Reset 패턴

## 1. Thesis

자주 spawn / destroy 되는 Actor (총알 / 파편 / 효과 트리거) 는 **Object Pool** 로 재사용해야 한다. UE 의 `AActor::BeginPlay/EndPlay` 는 *한 Actor 인스턴스당 1번만* 호출됨이 보장되지 않으므로, Pool 패턴은 **`SpawnActor + Destroy` 를 우회하고 `Activate/Deactivate` 로 대체**. 본 synthesis 는 Pool 의 4 핵심 — **(1) Spawn 시점 BeginPlay 1번 / Reuse 시점 BeginPlay X / (2) `bIsActive` UPROPERTY 로 풀 상태 표시 / (3) `Reset()` 가상 함수 의무 — 캐싱 weak ptr 무효화 + Tick 토글 + 시뮬 정지 / (4) 풀 한도 초과 시 fallback 정책**. UE 의 NiagaraComponent Pool ([[concepts/Asset-Optimization-Policy]] §VFX) 가 모범. 같은 패턴을 게임 Actor 로 일반화. **2026-05-13 KMCProject 적용 사례 추가 (§8)** + **정밀판 → [[synthesis/mc-actor-spawn-subsystem-implementation]]** + **측정 → [[synthesis/mc-actor-spawn-subsystem-h1-measurement]]**.

## 2. Pool 라이프사이클 매트릭스

| 단계 | SpawnActor (한번) | Activate (재사용) | Deactivate (반환) | Destroy (마지막) |
| -- | -- | -- | -- | -- |
| `BeginPlay` | ✓ 호출 | ✗ | ✗ | ✗ |
| `Reset()` (사용자 정의) | ✗ | ✓ — 상태 초기화 | ✓ — 정리 | ✗ |
| `SetActorEnableCollision` | ✓ | true | false | — |
| `SetActorHiddenInGame` | ✓ false | false | true | — |
| `SetActorTickEnabled` | ✓ | true | false | — |
| Tick | ✓ | ✓ | ✗ | ✗ |
| `EndPlay` | ✗ | ✗ | ✗ | ✓ 호출 |

## 3. 골격 — `AMCPooledActor` 베이스

```cpp
UCLASS(Abstract)
class AMCPooledActor : public AActor
{
public:
    AMCPooledActor() {
        PrimaryActorTick.bCanEverTick = false;
        // 풀 첫 SpawnActor 시 비활성 상태로 시작 — 활성 시점에만 보이게
        SetActorHiddenInGame(true);
        SetActorEnableCollision(false);
    }

    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly)
    bool bIsPoolActive = false;

    /** Pool 에서 가져올 때 호출 — Reset + 활성화 */
    virtual void Activate(const FTransform& WorldXfm)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMCPooledActor::Activate);
        MC_LOGRET_IF_FALSE(!bIsPoolActive, "Already active — pool corruption?");

        SetActorTransform(WorldXfm, /*bSweep=*/false, nullptr, ETeleportType::TeleportPhysics);
        Reset();   // 자손이 override
        SetActorHiddenInGame(false);
        SetActorEnableCollision(true);
        SetActorTickEnabled(true);
        bIsPoolActive = true;
    }

    /** Pool 로 반환 — Cleanup + 비활성 */
    virtual void Deactivate()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(AMCPooledActor::Deactivate);
        if (!bIsPoolActive) return;   // idempotent — vault: [[synthesis/actor-lifecycle-edge-cases]]

        SetActorTickEnabled(false);
        SetActorHiddenInGame(true);
        SetActorEnableCollision(false);
        // 캐싱 weak ptr 무효화 — 재사용 시 stale 안 되게
        OnDeactivate();    // 자손이 override
        bIsPoolActive = false;
    }

protected:
    /** 자손 override — 활성 시점 상태 초기화 */
    virtual void Reset() {}

    /** 자손 override — 비활성 시점 cleanup */
    virtual void OnDeactivate() {}
};
```

## 4. 자손 예 — `AMCBullet`

```cpp
UCLASS()
class AMCBullet : public AMCPooledActor
{
    UPROPERTY() TObjectPtr<UStaticMeshComponent> MeshComp;
    UPROPERTY() TObjectPtr<UNiagaraComponent>    TrailVFX;

    TWeakObjectPtr<AActor> Shooter;   // 캐싱 — 재사용 시 무효화 필요
    float Lifetime = 0.f;

    AMCBullet() {
        MeshComp = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
        TrailVFX = CreateDefaultSubobject<UNiagaraComponent>(TEXT("Trail"));
        TrailVFX->SetAutoActivate(false);   // 풀 첫 SpawnActor 에선 비활성
    }

    virtual void Reset() override
    {
        // 캐싱 무효화 (이전 Shooter 가 GC 되었을 수 있음)
        Shooter.Reset();
        Lifetime = 0.f;
        // VFX activate
        TrailVFX->Activate(/*bReset=*/true);
    }

    virtual void OnDeactivate() override
    {
        // VFX deactivate (Niagara Pool 에 반환)
        TrailVFX->Deactivate();
        // 본 mesh 가 콜리전 hit list 안 stale 안 되게
        MeshComp->ClearMoveIgnoreActors();
    }

    virtual void Tick(float Dt) override
    {
        Super::Tick(Dt);
        Lifetime += Dt;
        if (Lifetime > 5.f) {
            // 5초 후 자동 Pool 반환
            if (auto* Pool = GetWorld()->GetSubsystem<UMCBulletPool>()) {
                Pool->Return(this);
            }
        }
    }
};
```

## 5. Pool Subsystem (WorldSubsystem) — generic 골격

```cpp
UCLASS()
class UMCBulletPool : public UWorldSubsystem
{
    UPROPERTY() TArray<TObjectPtr<AMCPooledActor>> Available;
    UPROPERTY() TArray<TObjectPtr<AMCPooledActor>> Active;

    UPROPERTY(EditDefaultsOnly) int32 PoolSize = 32;
    UPROPERTY(EditDefaultsOnly) TSoftClassPtr<AMCPooledActor> PooledClass;

    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Super::Initialize(Collection);
        // 게임 시작 시 N개 미리 SpawnActor (히칭 분산)
        // [[synthesis/cooked-first-frame-stability]] 와 결합
    }

    AMCPooledActor* Acquire(const FTransform& W)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMCBulletPool::Acquire);
        AMCPooledActor* Actor = nullptr;
        if (Available.Num() > 0) {
            Actor = Available.Pop();
        } else {
            // 풀 부족 — 새 SpawnActor (느림)
            UE_LOG(LogMCAsset, Warning, TEXT("[Pool] Capacity exceeded — new spawn"));
            UClass* Cls = PooledClass.LoadSynchronous();
            MC_LOGRET_VAL_IF_NULL(Cls, nullptr, "PooledClass not loaded");
            Actor = GetWorld()->SpawnActor<AMCPooledActor>(Cls, W);
        }
        Actor->Activate(W);
        Active.Add(Actor);
        return Actor;
    }

    void Return(AMCPooledActor* Actor)
    {
        MC_LOGRET_IF_NULL(Actor, "Return null actor");
        Actor->Deactivate();
        Active.Remove(Actor);
        Available.Add(Actor);
    }
};
```

## 6. 함정 / 열린 질문

- [ ] **`bIsPoolActive` 와 `IsValidLowLevel()`** — Pool 비활성 actor 도 *valid UObject*. `IsValid(Actor)` 로는 풀 상태 식별 불가. `bIsPoolActive` 명시 검사
- [ ] **캐싱 weak ptr 무효화 누락** — `Reset()` 안에서 *모든 캐싱 reset*. 한 캐싱 빠뜨리면 옛 hit 콜백이 다른 frame 에 발화 (silent 버그)
- [ ] **GC 안 됨 — Pool 이 hard ref** — Pool 의 `TArray<TObjectPtr<>>` 가 hard. 게임 종료 시 Pool 의 EndPlay 후 actors GC. Map 전환 시 World Subsystem 자동 destroy
- [ ] **Replication 의 Pool 패턴** — Replicated Actor 를 Pool 에 넣으면 *NetGUID 가 매번 새로*. Reuse 시 Channel destroy/recreate — 비효율. 멀티플레이는 별도 패턴
- [ ] **`Activate(WorldXfm)` 에서 Replication** — Server 가 Activate → Multicast `Activate` RPC. Client 가 Pool 에서 가져옴 — 양쪽 idempotent
- [ ] **Niagara Pool 와 결합** — Pool actor 안 NiagaraComponent 는 ENCPoolMethod::AutoRelease 가 자동. Pool actor 의 Reset/OnDeactivate 가 Niagara Activate/Deactivate 트리거 ([[synthesis/vfx-audio-soft-pool-significance]])
- [ ] **`SetActorTickEnabled(false)` 해도 Component Tick 은?** — `PrimaryComponentTick` 별도. 모든 Component 의 `bCanEverTick=false` 또는 `SetComponentTickEnabled(false)` 의무 (열린)
- [ ] **풀 한도 초과 시 정책** — 본 synthesis 는 "새 SpawnActor + Warning 로그". 다른 옵션 — *가장 오래된 Active actor 재활용* (force reset). 게임 디자인 결정 (열린)

## 7. 관련

### Sources

[[sources/ue-gameframework-actor]] · [[sources/ue-components-actorcomponent]] · [[sources/mc-asset-validation-policy]] · [[sources/ue-niagara-skill]] · [[sources/ue-significance-skill]] · [[sources/ue-subsystem-skill]] · [[sources/ue-ref-11-assetloadingpolicy]]

### Entities

[[entities/AActor]] · [[entities/UActorComponent]] · [[entities/USignificanceManager]]

### Concepts

[[concepts/Actor-Lifecycle]] · [[concepts/Component-Lifecycle]] · [[concepts/Component-Policies-6]] · [[concepts/MC-Asset-Validation-Policy]] · [[concepts/Soft-Reference-vs-Hard]]

### Related synthesis

[[synthesis/actor-lifecycle-edge-cases]] (idempotent 가드) · [[synthesis/vfx-audio-soft-pool-significance]] (Niagara Pool 베이스) · [[synthesis/cooked-first-frame-stability]] (Pool 사전 spawn 으로 첫 프레임 분산) · [[synthesis/actor-pool-multiplayer-gc-integration]] (Replicated Pool + Niagara 결합 + 한도 정책) · [[synthesis/character-many-npc-5-fold-optimization]] (Significance 누적 5축) · ⭐ [[synthesis/mc-actor-spawn-subsystem-implementation]] (**KMCProject 통합 정밀 사례 — 7 패턴 결합 + 함정 12종 + 콘솔 4 명령 + Bundle PreLoad**) · ⭐ [[synthesis/mc-actor-spawn-subsystem-h1-measurement]] (**측정 H1 가설 검증 — Iterator vs Octree + WarmUp + Bundle + Significance 4축 매트릭스 + 예상값 + 실측 후 갱신 예정**)

---

## 8. KMCProject 적용 사례 (2026-05-13 신규)

§3~§5 의 generic 패턴을 **KMCProject 가 실제 게임 코드로 일반화** — Subsystem + Interface + 베이스 + Significance 통합. 본 섹션은 vault [[00_meta/06_VaultCitationRule]] 3-tier 마커 엄격 적용.

> **정밀판**: [[synthesis/mc-actor-spawn-subsystem-implementation]] (14.6 KB, 11 섹션) — 7 패턴 결합 + 함정 12종 + Bundle PreLoad + 콘솔 4 명령 + 측정 H1 가설.
> **측정**: [[synthesis/mc-actor-spawn-subsystem-h1-measurement]] (10 KB, draft) — H1 검증 측정 4 축 매트릭스 + 예상값 + 실측 후 갱신.

### 8.1 4 컴포넌트 구조

| 파일 | 역할 |
| -- | -- |
| `MCActorSpawnSubsystem.h/.cpp` | `UWorldSubsystem` — Soft Class 비동기 spawn + 풀 + Significance + TOctree2 + Bundle |
| `MCPoolableInterface.h` | `IMCPoolableInterface` — OnPoolActivate / Deactivate / GetSignificanceTag / OnSignificanceChanged |
| `MCPooledActor.h/.cpp` | `AMCPooledActor` 베이스 — interface 구현 + 기본 토글 + BP event hook |
| `MCActorSpawnSubsystem.{h,cpp}` Subsystem 자체에 통합 | Significance Manager + TOctree2 + Bundle PreLoad 등록 / Unregister |

### 8.2 vault §5 generic 골격 vs KMCProject 구현 비교

| 항목 | vault §5 generic | KMCProject 구현 |
| -- | -- | -- |
| Subsystem 베이스 | `UWorldSubsystem` | `UWorldSubsystem` ✅ |
| 풀 단위 | 단일 클래스 (UMCBulletPool — class 마다 Subsystem 1개) | **클래스별 TMap 풀** (`TMap<TSubclassOf, FMCPooledActorArray>`) — 한 Subsystem 이 N 클래스 |
| Acquire 시 새 spawn | `SpawnActor<>` 직접 호출 | `SpawnActorDeferred + FinishSpawning` 4단 ([[sources/ue-ref-11-assetloadingpolicy]] §2.6) |
| Soft Class 비동기 로드 | `LoadSynchronous` (동기) | `FStreamableManager::RequestAsyncLoad` + Handle Pin ([[concepts/Asset-Loading-Policy]] §2.5) |
| Activate 자손 hook | virtual `Reset()` | `IMCPoolableInterface::OnPoolActivate_Implementation` + `K2_OnPoolReset` BP event |
| Deactivate 자손 hook | virtual `OnDeactivate()` | `IMCPoolableInterface::OnPoolDeactivate_Implementation` + `K2_OnPoolCleanup` BP event |
| Significance 통합 | 미언급 (자손이 자체 등록) | Subsystem 옵션 (`bEnableSignificanceManagement`) — 자동 Register / Unregister |
| Spatial Index | 미언급 | `bEnableSpatialIndex` + TPimplPtr<FOctreeData> + GetActorsInRadius |
| Bundle PreLoad | 미언급 | `PreloadActorClasses(SoftClass[])` BP API + Strong ref 캐시 |
| 디버그 시각화 | 미언급 | 콘솔 4 명령 + DrawDebug |
| 한도 초과 정책 | "새 SpawnActor + Warning" | `Destroy` fallback + Verbose log (게임 디자인 결정 가능) |

### 8.3 Significance 통합 흐름 (§8.1)

```
ActivateActor(Actor, Transform)
├─ Engine 토글 (Transform / Hidden / Collision / Tick)
├─ IMCPoolableInterface::Execute_OnPoolActivate
│  └─ AMCPooledActor::OnPoolActivate_Implementation
│     ├─ bIsPoolActive = 1
│     └─ K2_OnPoolReset (BP)
└─ if (bEnableSignificanceManagement)
   └─ RegisterActorToSignificance
      └─ USignificanceManager::RegisterObject(Actor, Tag, ScoreFunc, Sequential, PostFunc)
         (Score 함수 = 거리 기반 0~1 선형 / PostFunc = OnSignificanceChanged 액터 hook)
```

Significance score 변화 → `PostFunc` → `IMCPoolableInterface::Execute_OnSignificanceChanged` → 자손 BP `Event On Significance Changed`. 디폴트 동작은 score < 0.1 → Tick OFF, 임계 이상 → Tick ON.

### 8.4 vault §6 함정 매트릭스 적용 검증

| 함정 # | KMCProject 적용 | 검증 |
| -- | -- | -- |
| #1 `bIsPoolActive` 와 `IsValid` 분리 | `AMCPooledActor::bIsPoolActive` UPROPERTY 명시 | ✅ |
| #2 캐싱 weak ptr 무효화 | OnPoolDeactivate 안 K2_OnPoolCleanup → 자손 BP 의무 | 🟡 자손 책임 (interface doc 에 명시) |
| #3 Pool hard ref → GC | `TObjectPtr` UPROPERTY 사용, Deinitialize 시 ClearAllPools | ✅ |
| #4 Replication Pool | 본 버전은 **싱글플레이 결정** — 멀티 분기 후속 | 🔴 미구현 (vault [[synthesis/actor-pool-multiplayer-gc-integration]] 후속) |
| #5 Activate Replication | 동일 — 후속 | 🔴 |
| #6 Niagara Pool 결합 | 자손 BP `K2_OnPoolReset` 안 NiagaraComponent::Activate(true) 호출 권장 | 🟡 자손 책임 |
| #7 Component Tick | 자손이 K2_OnPoolReset 안 `SetComponentTickEnabled` 호출 권장 | 🟡 자손 책임 |
| #8 풀 한도 초과 정책 | `PoolHardLimitPerClass = 32` 디폴트, 초과 시 Destroy fallback | ✅ (LRU eviction 은 후속) |

### 8.5 디자이너 워크플로

**기본 사용** (싱글플레이 / 단일 캐릭터):

```
1. BP — AMCPooledActor 자손 클래스 (예: BP_MyEffect) 생성
2. 컴포넌트 / 변수 추가
3. Event Graph — Event On Pool Reset 노드 / Event On Pool Cleanup 노드 추가
4. 게임 로직 — UMCActorSpawnSubsystem 의 RequestSpawnAsync 호출 (SoftClass 지정)
5. 종료 시 ReleaseToPool 호출
```

**다수 NPC 시나리오** (Significance ON):

```
1. Subsystem 디테일 패널 — bEnableSignificanceManagement = true + bEnableSpatialIndex = true
2. 적절한 SignificanceNearDistance / FarDistance / SpatialIndexExtent 설정
3. GameMode::BeginPlay 안 — PreloadActorClasses + WarmUpPool 호출
4. NPC AMCPooledActor 자손 BP — Event On Significance Changed 노드
5. score 변화에 따라 VFX Quality / AnimUpdateRate / Audio Cull 결정
6. 디버그 — 콘솔 mc.spawn.dump / mc.spawn.octree.query
```

### 8.6 후속 작업 (이번 사례 외)

- [x] **Bundle PreloadPrimaryAssets** — GameMode 시작 시 자주 쓰는 SoftClass 사전 로드 — 2026-05-13 완료 (`PreloadActorClasses` BP API + Strong ref 캐시)
- [x] **TOctree2 + Significance 통합** — 2026-05-13 완료 ([[sources/ue-spatialpartition-toctree2]] 페어)
- [x] **디버그 시각화** — 2026-05-13 완료 (콘솔 4 명령)
- [x] **측정 계획 작성** — 2026-05-13 완료 [[synthesis/mc-actor-spawn-subsystem-h1-measurement]] (4 축 매트릭스 + 예상값)
- [ ] **측정 실측** — 사용자 PIE / Cooked 빌드 측정 → 위 measurement synthesis 갱신
- [ ] **Replication 분기** — 멀티플레이 확장, vault [[synthesis/actor-pool-multiplayer-gc-integration]] 패턴
- [ ] **LRU eviction** — 풀 한도 초과 시 가장 오래된 Active actor 재활용 (현재는 Destroy fallback)
- [ ] **자손 정밀 예** — AMCBullet / AMCEffectDecal / AMCSpawnedNPC 등 vault §4 의 KMCProject 실제 자손 작성

### 8.7 3-tier 검증

- 🟢 VAULT — Subsystem 5 종 결정 / SpawnActor 4단 회피 / Pool 라이프사이클 §2 / Significance API §2 / TOctree2 §2.3 / Bundle §2.7 — 모두 vault 직접 인용
- 🟡 PARTIAL — `EPostSignificanceType::Sequential` 채택 근거 (vault §2 는 종류 나열만, PostFunc 가 BP execution 호출하므로 Sequential 필수는 외삽) / `FManagedObjectInfo::GetSignificance()` API 존재 (UE 5.x 일반 지식)
- 🔴 INFERRED — Significance Score 함수의 viewer transform 활용 정밀 (단일 viewer vs 모든 ViewPoints) / 자동 release 안 함 디자인 결정 (vault 미정책, 디자인 판단)
