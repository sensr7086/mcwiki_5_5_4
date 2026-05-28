---
type: synthesis
title: "KMCProject UMCActorSpawnSubsystem — 통합 구현 정밀 사례 (Subsystem + Pool + Interface + TOctree2 + Significance + Bundle + Console + Consumer Library)"
slug: mc-actor-spawn-subsystem-implementation
created: 2026-05-13
last_updated: 2026-05-13
sources:
  - "[[sources/ue-subsystem-skill]]"
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
  - "[[sources/ue-spatialpartition-toctree2]]"
  - "[[sources/ue-significance-skill]]"
  - "[[sources/ue-niagara-skill]]"
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/ue-coreuobject-interface]]"
entities:
  - "[[entities/AActor]]"
  - "[[entities/USubsystem]]"
  - "[[entities/USignificanceManager]]"
concepts:
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Pimpl-TUniquePtr-Destructor]]"
  - "[[concepts/Global-Iterator-Avoidance]]"
status: living
tags: [synthesis, kmcproject, subsystem, actor-spawn, pool, toctree2, significance, bundle-preload, console-commands, consumer-library]
citation_disclosure: "🟢 25 (vault 직접 인용 + KMCProject 빌드 검증) / 🟡 5 (외삽) / 🔴 3 (일반 UE 지식)"
---

# KMCProject UMCActorSpawnSubsystem — 통합 구현 정밀 사례

> **목적**: KMCProject 의 첫 Subsystem 구현 (2026-05-13) 의 *완전한 통합 사례*. 8 개 vault 패턴이 한 클래스 (+ Consumer Library) 에 결합된 모범 사례 — Subsystem (5종 결정) + Pool (Activate/Deactivate) + Interface (Native+BP) + Soft Class Async + TOctree2 (반경 쿼리) + Significance (점수) + Bundle PreLoad + 콘솔 디버그 + ⭐ Consumer Library (UMCSpatialQueryLibrary).
>
> **참고 vault**: [[synthesis/actor-pool-reset-pattern]] §8 (generic pool §1~§7 보강) + [[synthesis/toctree2-worldpartition-pair-pattern]] (TOctree2 + WorldPartition 페어).

## 1. Thesis

KMCProject `UMCActorSpawnSubsystem` 은 **하나의 Subsystem 이 8 개 vault 패턴을 직교 결합**한 모범 사례:

```
┌─ UWorldSubsystem (vault [[sources/ue-subsystem-skill]] §3) — 라이프사이클 호스트
│
├─ Actor Pool (vault [[synthesis/actor-pool-reset-pattern]] §2~§5)
│  ├─ TMap<TSubclassOf<AActor>, FMCPooledActorArray> AvailablePool — 클래스별 풀
│  ├─ TArray<TObjectPtr<AActor>> ActiveActors                       — 활성 액터
│  └─ PoolHardLimitPerClass + Destroy fallback                       — 한도 정책
│
├─ Soft Class Async (vault [[sources/ue-ref-11-assetloadingpolicy]] §2.5/§2.6)
│  ├─ FStreamableManager::RequestAsyncLoad                          — Cooked 4단 회피
│  ├─ SpawnActorDeferred + FinishSpawning                           — 4단 표준
│  └─ TArray<TSharedPtr<FStreamableHandle>> ActiveLoadHandles       — Pin 보관
│
├─ IMCPoolableInterface (vault [[sources/ue-coreuobject-interface]] §6 BP+C++)
│  ├─ OnPoolActivate / OnPoolDeactivate / IsPoolActive             — BlueprintNativeEvent
│  ├─ GetSignificanceTag / OnSignificanceChanged                   — Significance 연동
│  └─ AMCPooledActor 베이스 (BP event hook K2_*)                   — 자손 confort
│
├─ TOctree2 Spatial Index (vault [[sources/ue-spatialpartition-toctree2]])
│  ├─ TPimplPtr<FOctreeData> OctreeData                            — Pimpl C4150 회피
│  ├─ FMCActorOctreeElement + FMCActorOctreeSemantics              — 6 요소
│  └─ GetActorsInRadius — O(log N + K)                              — vault §2.5
│
├─ USignificanceManager (vault [[sources/ue-significance-skill]] §5)
│  ├─ RegisterObject(Actor, Tag, SigFunc, Sequential, PostFunc 4인자) — 시그니처
│  ├─ 거리 기반 0~1 score                                              — 디폴트 함수
│  └─ PostFunc → Execute_OnSignificanceChanged                        — interface 통합
│
├─ Bundle PreLoad (vault [[sources/ue-ref-11-assetloadingpolicy]] §2.7)
│  ├─ PreloadActorClasses(Soft[]) — 묶음 비동기                       — GameMode 시작
│  └─ TArray<TSubclassOf<AActor>> PreloadedClassCache                — Strong ref GC 방어
│
├─ Console Commands (디버그 시각화)
│  ├─ mc.spawn.dump / .octree.draw / .octree.query / .significance.dump
│  └─ TArray<TUniquePtr<FAutoConsoleCommand>> ConsoleCommands       — Subsystem lifetime
│
└─ ⭐ Consumer Library (vault [[sources/mc-asset-validation-policy]] §6 — 2026-05-13 추가)
   ├─ UMCSpatialQueryLibrary — 5 정적 BP API (Radius / Cone / LOS / Cone+Vis / Closest)
   ├─ FMCSpatialQueryFilter USTRUCT — Class / Tag / Self / Interface / Pawn 5 필터
   ├─ IMCSpatialQueryFilterable — 액터 측 CanBeSpatialQueryResult BNE
   └─ §9.5 정리 — Subsystem 의 GetActorsInRadius BP API 의 표준 wrapper
```

## 2. 옵션 매트릭스 — 게임 디자인 시나리오

| 시나리오 | bEnableSpatial | bEnableSignificance | Pool | Bundle PreLoad | Consumer Library |
| -- | -- | -- | -- | -- | -- |
| 단일 캐릭터 게임 (1 명) | false | false | 단순 fallback | 불필요 | 불필요 |
| 소수 NPC (5~10 명) | false | false | 32/class | 옵션 | `GetActorsInRadius` 만 |
| 다수 NPC (50+ 명) | **true** | **true** | 64/class | **권장** | **`GetActorsInConeWithVisibility`** (perception) |
| 대규모 월드 + 다수 | true | true + WorldPartition (외부) | 128/class | 의무 | Cone + LOS + Filter (Faction Tag) |
| VFX / Decal / Bullet | false | false | 256/class | 의무 | `GetActorsInRadius` (피해 범위 검사) |

### 2.1 게임 디자인 결정 트리

```
스폰 빈도 / 객체 수에 따른 결정:

├─ 자주 spawn / destroy (총알 / 파편 / VFX)
│  └─ Pool ON + Bundle PreLoad + Consumer (피해 범위 = GetActorsInRadius)
│
├─ 다수 동시 (NPC 50+)
│  └─ Pool ON + Bundle + bEnableSpatialIndex (TOctree2)
│     + bEnableSignificance (LOD/Tick) + Consumer (perception = Cone+Visibility)
│
├─ 가끔 spawn (보스 / 컷씬 액터)
│  └─ Pool OFF + Soft Class 만 (RequestSpawnAsync)
│
└─ 정적 (Player Character)
   └─ Pool/Subsystem 불필요 — 디테일 패널 Hard ref
```

## 3. 신규 / 보강 vault 페이지 활용 매트릭스

본 Subsystem 작성 / 검증 과정에서 발견되어 vault 화 된 함정 / 표준:

| vault 페이지 | 본 Subsystem 활용 | 등록 시점 |
| -- | -- | -- |
| [[sources/ue-subsystem-skill]] | UWorldSubsystem 3 virtual | 사전 |
| [[sources/ue-ref-11-assetloadingpolicy]] §2.6 | SpawnActorDeferred + FinishSpawning 4단 | 사전 |
| [[sources/ue-spatialpartition-toctree2]] §2.3 | Element + Semantics 6 요소 | 사전 |
| [[sources/ue-significance-skill]] §5 typedef + §6 함정 | PostFunc 4 인자 시그니처 | 2026-05-13 (본 fix) |
| [[sources/ue-coreuobject-interface]] §5 함정 11종 | UINTERFACE Blueprintable + BlueprintPure 금지 | 2026-05-13 (본 fix) |
| ⭐ [[concepts/Pimpl-TUniquePtr-Destructor]] | TPimplPtr<FOctreeData> + MakePimpl | 2026-05-13 (본 fix) |
| [[concepts/MC-Asset-Validation-Policy]] | MC_LOGRET_IF_* 매크로 | 사전 |
| [[concepts/Global-Iterator-Avoidance]] | TOctree2 쿼리가 TActorIterator 대체 | 사전 |
| ⭐ [[sources/mc-asset-validation-policy]] §6 | **static-friendly 매크로 부재 함정** (BPLibrary 작성 시) | 2026-05-13 (본 §9.5) |
| ⭐ [[sources/ue-coreuobject-interface]] §5 #1 ⭐⭐ | **2회 재현 확인** (`MCPoolableInterface` + `MCSpatialQueryFilterable`) | 2026-05-13 (본 §9.5) |

→ **8 함정이 본 Subsystem 빌드 사이클에서 발견** + vault 등록. 다음 작업자는 같은 실수 회피.

## 4. 통합 라이프사이클 흐름

### 4.1 GameMode 시작 시점 (LoadingScreen 안)

```cpp
void AMyGameMode::BeginPlay()
{
    Super::BeginPlay();

    auto* Spawner = GetWorld()->GetSubsystem<UMCActorSpawnSubsystem>();
    if (!Spawner) return;

    // 1. Bundle PreLoad — 자주 spawn 되는 클래스 묶음 비동기 로드
    TArray<TSoftClassPtr<AActor>> ToLoad = {
        BulletClass, ExplosionClass, ImpactClass, EnemyAClass, EnemyBClass
    };
    FMCOnActorClassesPreloadedDelegate OnReady;
    OnReady.BindUFunction(this, FName("OnPreloadComplete"));
    Spawner->PreloadActorClasses(ToLoad, OnReady);

    // 2. Pool WarmUp — 사전 spawn 으로 첫 SpawnActor 히칭 분산
    Spawner->WarmUpPool(BulletClass, 64);
    Spawner->WarmUpPool(ExplosionClass, 16);
}
```

### 4.2 게임 중 spawn

```cpp
// Soft Class 비동기 spawn (이미 PreLoad 됐다면 즉시 spawn)
FMCOnActorSpawnedDelegate OnSpawned;
OnSpawned.BindLambda([](AActor* A) { /* 콜백 처리 */ });
Spawner->RequestSpawnAsync(EnemyClass, SpawnTransform, OnSpawned, /*OnFailed=*/{});

// 다수 NPC 시나리오 — 반경 쿼리 (Subsystem 직접 호출 — 1차 후보만)
TArray<AActor*> Nearby;
Spawner->GetActorsInRadius(Player->GetActorLocation(), 1500.f, Nearby);

// ⭐ 또는 Consumer Library — 고급 필터 (§9.5)
FMCSpatialQueryFilter Filter;
Filter.ClassFilter = AMCEnemyCharacter::StaticClass();
Filter.RequiredTag = FGameplayTag::RequestGameplayTag("Faction.Hostile");
UMCSpatialQueryLibrary::GetActorsInRadius(this, Player->GetActorLocation(), 1500.f, Filter, Nearby);
```

### 4.3 NPC 측 — AMCPooledActor 자손 (BP)

```
BP_MyEnemy : AMCPooledActor

Event Graph:
├─ Event On Pool Reset (Transform) — 캐싱 reset / 체력 100 / VFX activate
├─ Event On Pool Cleanup            — 진행 중 핸들 cancel / 외부 콜백 unbind / VFX deactivate
└─ Event On Significance Changed    — score < 0.1 → SetActorTickInterval(0.5) / score >= 0.5 → 0.0
```

### 4.4 spawn 종료 시 — Pool 반환

```cpp
void AMyEnemy::OnDeath()
{
    if (auto* Spawner = GetWorld()->GetSubsystem<UMCActorSpawnSubsystem>())
    {
        Spawner->ReleaseToPool(this);   // Destroy 대신 풀로
    }
}
```

## 5. ActivateActor / DeactivateActor 통합 흐름

5 단계 순서가 의도적 — 각 시스템이 직교:

### 5.1 Activate 순서

```
ActivateActor(Actor, Transform)
├─ [1] Engine 토글 — Transform / Hidden / Collision / Tick
├─ [2] IMCPoolableInterface::Execute_OnPoolActivate
│      └─ AMCPooledActor::OnPoolActivate_Implementation
│         ├─ bIsPoolActive = 1
│         └─ K2_OnPoolReset (BP event)
├─ [3] Significance 등록 (옵션 ON)
│      └─ Mgr->RegisterObject(Actor, Tag, SigFunc, Sequential, PostFunc 4인자)
└─ [4] TOctree2 등록 (옵션 ON)
       └─ Octree.AddElement(Element with bounds)
```

### 5.2 Deactivate 순서 — 역순

```
DeactivateActor(Actor)
├─ [1] TOctree2 해제 (옵션 ON) — *먼저* (쿼리 결과에서 즉시 제외)
├─ [2] Significance 해제 (옵션 ON) — *interface hook 보다 먼저*
│      (PostFunc 가 더 이상 발화 안 하도록 보장)
├─ [3] IMCPoolableInterface::Execute_OnPoolDeactivate — *Engine 토글 전*
│      └─ AMCPooledActor::OnPoolDeactivate_Implementation
│         ├─ K2_OnPoolCleanup (BP event)
│         └─ bIsPoolActive = 0
└─ [4] Engine 토글 — Tick / Collision / Hidden 비활성
```

직교 책임 + 역순 cleanup → race / stale state 회피.

## 6. 콘솔 디버그 명령 4종

| 명령 | 인자 | 동작 |
| -- | -- | -- |
| `mc.spawn.dump` | (없음) | Active / LoadHandle / Pool / Spatial / Preload 카운트 + Active actor 위치 list |
| `mc.spawn.octree.draw` | `[Duration=5]` | 모든 active actor bounds **cyan box** + actor name (5초) |
| `mc.spawn.octree.query` | `<X> <Y> <Z> <R> [Duration=5]` | **yellow sphere** (쿼리) + **green hit box** + "HIT 이름" |
| `mc.spawn.significance.dump` | (없음) | 각 active actor 의 `QuerySignificance` score |

### 6.1 PIE 측정 흐름 예시

```
PIE 시작 → 50+ NPC spawn → 콘솔:
1. mc.spawn.dump          → "Active=52 SpatialIdx=52 Preloaded=5" 확인
2. mc.spawn.octree.draw 10 → 10초 동안 모든 액터 bounds 시각화
3. mc.spawn.octree.query 0 0 100 2000 → 2km 반경 hit 액터 sphere/box 시각화
4. mc.spawn.significance.dump → 거리별 score 분포 확인 (예: 가까운 NPC = 0.8, 먼 NPC = 0.1)
```

## 7. 함정 / 안티패턴 (본 사례 누적)

본 Subsystem 작성 / 디버깅 사이클에서 마주친 / vault 화 된 함정:

### 7.1 빌드 함정 (🟢 검증)

| # | 함정 | vault 위치 | 재현 횟수 |
| -- | -- | -- | -- |
| 1 | UINTERFACE `Blueprintable` 누락 — BlueprintNativeEvent UHT 거부 | [[sources/ue-coreuobject-interface]] §5 #3 | 1회 (`MCPoolableInterface`) |
| 2 | Interface `BlueprintPure` 사용 — UHT 거부 | [[sources/ue-coreuobject-interface]] §5 #2 | 1회 |
| 3 ⭐⭐ | `meta=(CannotImplementInterfaceInBlueprint=false)` 반대 처리 | [[sources/ue-coreuobject-interface]] §5 #1 | **2회** (`MCPoolableInterface` + `MCSpatialQueryFilterable`) — ⭐⭐ vault 카탈로그 가치 입증 |
| 4 | `FManagedObjectPostSignificanceFunction` 2 인자 추측 (실제 4 인자) | [[sources/ue-significance-skill]] §6 #1 | 1회 |
| 5 | Pimpl + `TUniquePtr<Incomplete>` C4150 | [[concepts/Pimpl-TUniquePtr-Destructor]] §2 | 1회 |
| 6 | Stage 5 + destructor 명시만으로 부족 — TPimplPtr 가 정답 | concept §2 Stage 3 | 1회 |
| 7 ⭐ | **MC_LOGRET_* 매크로 static 함수 비호환** (`this` 참조) | [[sources/mc-asset-validation-policy]] §6 (신규 2026-05-13) | 1회 (`UMCSpatialQueryLibrary`) |

⭐⭐ **#3 의 2회 재현** 이 본 cycle 의 핵심 vault 신뢰도 데이터:
- 1차 (`MCPoolableInterface`) → vault 카탈로그
- 2차 (`MCSpatialQueryFilterable`) → vault 신뢰도 ⭐⭐ 승격 + *vault 즉시 인지 → 1 시도 해결* 사례 (H1 데이터)

### 7.2 라이프사이클 함정 (🟡 일반 UE 지식)

| # | 함정 | 정답 |
| -- | -- | -- |
| 8 | Activate 시 Significance / Octree 등록 *전* interface hook | Engine 토글 → interface → Significance → Octree 순서 |
| 9 | Deactivate 시 interface hook 호출 *후* Octree 해제 | 역순 — Octree → Significance → interface → 토글 |
| 10 | NotifyActorMoved 미호출 — 액터 위치 변경 시 Octree stale | 자손이 큰 이동 시 명시 호출 (자동 갱신 비용 큼 — 옵션 후속) |
| 11 | Pool 한도 초과 시 destroy fallback — 게임 디자인 따라 LRU eviction 필요 | PoolHardLimitPerClass 옵션 + 후속 LRU |

### 7.3 검증 함정 (🟡)

| # | 함정 | 정답 |
| -- | -- | -- |
| 12 | `TActorIterator` 사용 — vault [[concepts/Global-Iterator-Avoidance]] 금지 | TOctree2 GetActorsInRadius 대체 (O(log N + K) vs O(N)) |
| 13 | 콘솔 명령 `FAutoConsoleCommand` 전역 등록 — 멀티 PIE / 다중 World 충돌 | Subsystem 멤버 `TArray<TUniquePtr<FAutoConsoleCommand>>` Lifetime 묶음 |

## 8. 정책 매핑 — UE 횡단 6 정책

| 정책 | 적용 위치 |
| -- | -- |
| 🚨 [[concepts/Profiling-Scope-Rule]] | 모든 진입점 + lambda 안 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| 🚨 [[concepts/Global-Iterator-Avoidance]] | TOctree2 가 TActorIterator 대체 |
| 🚨 [[concepts/Component-Policies-6]] §3 | UPROPERTY GC — TObjectPtr / TWeakObjectPtr |
| 🚨 [[concepts/Asset-Loading-Policy]] §2.5/2.6/2.7 | Soft Class + StreamableManager + Pin + Bundle PreLoad |
| 🎯 [[concepts/Asset-Optimization-Policy]] | Pool + Significance + URO (자손 ActorClass) |
| 🟢 [[concepts/MC-Asset-Validation-Policy]] | `MC_LOGRET_IF_*` 매크로 모든 가드 + ⭐ §6 static-friendly 변형 부재 함정 (§9.5) |

## 9. 후속 작업 후보

### 9.1 코드 보강

- [ ] **LRU eviction** — 풀 한도 초과 시 가장 오래된 Active actor 재활용 (현재 Destroy fallback)
- [ ] **자동 NotifyActorMoved** — bAutoUpdateOctreeOnTick 옵션 + Tick 안 자동 갱신
- [ ] **Replication 분기** — 멀티플레이 확장 ([[synthesis/actor-pool-multiplayer-gc-integration]] 패턴)
- [ ] **WorldPartition 통합** — 대규모 월드 streaming ([[synthesis/toctree2-worldpartition-pair-pattern]] 페어)

### 9.2 측정

[[sources/ue-measure-readme]] 패턴:
- [ ] `TActorIterator` (O(N)) vs `GetActorsInRadius` (O(log N + K)) — 100/500/2000 NPC 측정
- [ ] WarmUpPool 5 vs no warm — 첫 RequestSpawnAsync ms
- [ ] Bundle PreLoad 활성 vs 비활성 — 매 spawn 비용
- [ ] Significance ON / OFF — 50 NPC frame 비용
- [ ] ⭐ Consumer Library (§9.5) — `GetActorsInRadius` vs `GetActorsInConeWithVisibility` 비용 차이 (50/200 NPC, LineTrace 차폐 검사 비용)

### 9.3 BP 자손 사례

KMCProject 안 실제 자손 BP 작성:
- [ ] `BP_MCBullet` — Bullet pool 자손 (Niagara trail + lifetime)
- [ ] `BP_MCExplosion` — Decal + Niagara + Audio 일회성
- [ ] `BP_MCSpawnedNPC` — AMCPooledActor + ACharacter 다중 inherit + IMCPoolableInterface 명시
- [ ] ⭐ `BP_MCEnemy_Faction` — IMCSpatialQueryFilterable 구현 (Faction Tag 보유 + CanBeSpatialQueryResult override)

### 9.4 측정 가치 — H1 가설 (vault summary)

본 Subsystem 의 vault 적용 사례가 *다음 작업자* 의 시도 횟수를 측정:

```
시도 횟수 단축 가설 (H1):
├─ vault 없을 때 (단순 추측) — 6+ 시도 (본 세션 측정)
└─ vault 있을 때 (search "C4150" / "TPimplPtr" / "Blueprintable") — 1~2 시도 (예상)
```

**§7.1 #3 의 2회 재현 사례 (2026-05-13)**:
- `MCPoolableInterface` 1차 발견 → vault 카탈로그 (3+ 시도 추정 — UHT 메시지로 추적 어려움)
- `MCSpatialQueryFilterable` 2차 재현 → **vault 즉시 인지 → 1 시도 해결** (실증 데이터)

→ vault [[sources/ue-measure-summary]] H1 추적 — 후속 측정 진행 + ⭐⭐ 신뢰도 데이터 1건 누적.

### 9.5 ⭐ Consumer Library 사례 (2026-05-13 신규)

Subsystem 의 `GetActorsInRadius` BP API 를 *고급 필터와 함께* 사용하는 표준 wrapper. 본 §은 Consumer 측 라이브러리 작성 시 vault 모범 사례.

#### 9.5.1 파일 구조

```
Source/KMCProject/MCPlayModule/BlueprintLib/
├── MCSpatialQueryFilterable.h     ← UMCSpatialQueryFilterable + IMCSpatialQueryFilterable (BNE)
├── MCSpatialQueryLibrary.h        ← FMCSpatialQueryFilter USTRUCT + 5 정적 BP API
└── MCSpatialQueryLibrary.cpp      ← 구현 + file-local static-friendly 매크로
```

#### 9.5.2 5 정적 BP API 매트릭스

| 함수 | Subsystem 호출 | 추가 필터 / 기하 |
| -- | -- | -- |
| `GetActorsInRadius` | 1차 | FMCSpatialQueryFilter (5 필터) |
| `GetActorsInCone` | 1차 + Cone | + axial dot product (HalfAngle 도 cosine) |
| `GetActorsInLineOfSight` | 1차 + LineTrace | + LineTraceSingleByChannel (벽 차폐 검사) |
| **`GetActorsInConeWithVisibility`** ⭐ | 1차 + Cone + LOS | NPC perception 표준 (5.x AI 베이스) |
| `GetClosestActorInConeWithVisibility` | 위 + 거리 정렬 [0] | 단일 결과 편의 |

#### 9.5.3 FMCSpatialQueryFilter 5 필터

```cpp
USTRUCT(BlueprintType)
struct FMCSpatialQueryFilter
{
    TSubclassOf<AActor> ClassFilter = nullptr;           // IsA(Class) 만
    FGameplayTag RequiredTag;                            // IGameplayTagAssetInterface 보유 + HasTag
    TObjectPtr<AActor> IgnoredActor = nullptr;           // Self 제외
    bool bRequireFilterableInterface = false;            // IMCSpatialQueryFilterable + CanBeSpatialQueryResult
    bool bRequirePawn = false;                           // APawn 자손만
};
```

#### 9.5.4 직교 패턴 — Subsystem vs Library 책임

| 책임 | Subsystem | Consumer Library |
| -- | -- | -- |
| TOctree2 등록 / 해제 | ✅ `RegisterActorToOctree` / `UnregisterActorFromOctree` | X |
| 박스 prefilter + 정밀 거리 | ✅ `GetActorsInRadius` (1차) | X (사용만) |
| Class / Tag / Self 필터 | X | ✅ `ApplyFilter` |
| Cone (axial) 검사 | X | ✅ `IsInCone` |
| LineTrace (LOS) | X | ✅ `HasLineOfSight` |
| Interface dispatch | X | ✅ `Execute_CanBeSpatialQueryResult` |
| Profiling Scope | ✅ Subsystem 측 | ✅ 5 BP API 첫 줄 |
| Validation 매크로 | `MC_LOGRET_*` (멤버 함수) | **file-local `MCSP_LOGRET_*`** (§7.1 #7 함정) |

→ Subsystem 은 *공간 인덱스 + 라이프사이클*. Library 는 *고급 필터 + 기하*.

#### 9.5.5 BP / C++ 사용 패턴

```cpp
// C++ — NPC perception
FMCSpatialQueryFilter Filter;
Filter.ClassFilter = AMCEnemyCharacter::StaticClass();
Filter.bRequirePawn = true;
Filter.RequiredTag = FGameplayTag::RequestGameplayTag("Faction.Hostile");

TArray<AActor*> Visible;
UMCSpatialQueryLibrary::GetActorsInConeWithVisibility(
    this, /*Observer=*/this,
    GetActorForwardVector(), /*Radius=*/2000.f, /*HalfAngle=*/60.f,
    ECC_Visibility, Filter, Visible);

if (Visible.Num() > 0)
{
    AActor* Closest = Visible[0];   // 또는 GetClosestActorInConeWithVisibility 단일
}
```

```
// BP — Player ability "주변 적 5명에 데미지"
1. MakeStruct FMCSpatialQueryFilter (ClassFilter=BP_Enemy / IgnoredActor=Self)
2. GetActorsInRadius(Self, GetActorLocation, 800, Filter, OutActors)
3. ForEachLoop → ApplyDamage
```

#### 9.5.6 페어 vault 인용 (8 종)

| vault | 적용 |
| -- | -- |
| [[sources/ue-spatialpartition-toctree2]] §2.5 | Subsystem 박스 prefilter 패턴 (1차 후보) |
| [[sources/ue-ref-09-globaliteratorpolicy]] §4.1 / §4.7 | TActorIterator 금지 — Consumer 측 대안 진입점 |
| [[sources/ue-coreuobject-interface]] §5 #1·#3 + §6 | UINTERFACE 함정 + BP/C++ 결정 트리 |
| [[sources/ue-coreuobject-interface]] §5 #1 ⭐⭐ | **2회 재현** (`MCPoolableInterface` + `MCSpatialQueryFilterable`) |
| [[sources/ue-ref-07-profilingscopeRule]] §2.1 | 모든 BP API 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| [[sources/mc-asset-validation-policy]] §6 ⭐ | **static-friendly 매크로 부재 함정** (BPLibrary 작성 시) |
| [[sources/ue-significance-skill]] §4 | 페어 (Library 는 retrieve 만, score 결합은 자손) |
| [[synthesis/mc-actor-spawn-subsystem-implementation]] §4.2 (본 페이지) | 게임 중 spawn — 다수 NPC 시나리오 반경 쿼리 — 본 Library 가 표준 wrapper |

## 10. Cross-link

### Sources

- [[sources/ue-subsystem-skill]] (Subsystem 5종 결정)
- [[sources/ue-ref-11-assetloadingpolicy]] (SoftClass + Bundle + 4단)
- [[sources/ue-spatialpartition-toctree2]] (TOctree2 표준 ⭐⭐⭐)
- [[sources/ue-significance-skill]] (Significance 5대 영역 + 함정)
- [[sources/ue-coreuobject-interface]] (UINTERFACE 11 함정 ⭐⭐ §5 #1 2회 재현)
- [[sources/ue-niagara-skill]] (Pool 자손 VFX 결합)
- [[sources/mc-asset-validation-policy]] (KMCProject 매크로 + ⭐ §6 static-friendly 부재 함정)

### Concepts

- [[concepts/Subsystem-5-Types]] · [[concepts/Component-Policies-6]] · [[concepts/Profiling-Scope-Rule]]
- [[concepts/Asset-Loading-Policy]] · [[concepts/Soft-Reference-vs-Hard]]
- [[concepts/MC-Asset-Validation-Policy]]
- ⭐ [[concepts/Pimpl-TUniquePtr-Destructor]] (본 Subsystem 첫 검증 사례)
- [[concepts/Global-Iterator-Avoidance]]

### Related synthesis

- [[synthesis/actor-pool-reset-pattern]] §8 (KMCProject 적용 사례 — 4 컴포넌트 비교)
- [[synthesis/toctree2-worldpartition-pair-pattern]] (TOctree2 페어 — WorldPartition 통합 후속)
- [[synthesis/spawnactor-hitching-4-step-pattern]] (4단 회피 — Bundle PreLoad 결합)
- [[synthesis/character-many-npc-5-fold-optimization]] (Significance 5축 — 다수 NPC)
- [[synthesis/mc-soft-asset-component-pattern]] (KMCProject Soft 컴포넌트 자매 사례)

### log entries (2026-05-13 본 세션)

- `feature | UMCActorSpawnSubsystem — 런타임 액터 스폰/풀 관리 Subsystem 골격`
- `feature | IMCPoolableInterface + AMCPooledActor + Subsystem hook 통합`
- `feature | UMCActorSpawnSubsystem — Significance Manager 통합 (옵션)`
- `feature | UMCActorSpawnSubsystem — TOctree2 통합 + 콘솔 명령 4종 + 디버그 시각화` ⭐ (Subsystem GetActorsInRadius BP API 추가)
- `feature | UMCActorSpawnSubsystem — Bundle PreLoad (PreloadActorClasses) BP API`
- ⭐ `feature | UMCSpatialQueryLibrary — UMCActorSpawnSubsystem Octree 쿼리 소비자 (BPFunctionLibrary + 4 필터 + IMCSpatialQueryFilterable)` (2026-05-13 본 §9.5)
- `fix | UMCSpatialQueryFilterable — UINTERFACE meta=... 함정 재현` (§7.1 #3 2차 재현 — ⭐⭐ 신뢰도 데이터)
- 6 fix entries (Stage 1·2·3 + PostFunc + UHT + 그 외)
- 3 doc entries (Interface §5 / Significance §6 / Pimpl concept)
- 1 verify (Subsystem 빌드)

## 11. 신뢰도 매트릭스 (3-tier)

| 영역 | tier | 근거 |
| -- | -- | -- |
| §1 8 패턴 결합 구조 | 🟢 | 모든 패턴 vault 직접 인용 + KMCProject 빌드 검증 |
| §2 옵션 매트릭스 | 🟡 | 게임 시나리오별 결정 — 일반 UE 5.x 패턴 |
| §4 라이프사이클 흐름 | 🟢 | 코드 직접 검증 |
| §5 Activate/Deactivate 순서 | 🟢 | 코드 검증 + vault 직교 원칙 |
| §6 콘솔 명령 PIE 흐름 | 🟡 | 실제 PIE 측정 미완료 (후속) |
| §7 함정 13종 | 🟢 (1~7 빌드 검증) / 🟡 (8~13 일반 UE) | |
| §7.1 #3 2회 재현 ⭐⭐ | 🟢 | `MCPoolableInterface` + `MCSpatialQueryFilterable` 빌드 에러 직접 |
| §8 정책 매핑 6종 | 🟢 | vault 정책 페이지 직접 인용 |
| ⭐ §9.5 Consumer Library | 🟢 | `UMCSpatialQueryLibrary` 빌드 통과 + 5 BP API 검증 |
| §9.5.6 페어 vault 인용 8종 | 🟢 | 모두 vault 직접 인용 |
| §9.4 H1 가설 | 🔴 (이전) → 🟡 (2026-05-13 갱신) | §7.1 #3 2차 재현 = 1 시도 해결 실증 |

본 페이지가 KMCProject 의 가장 정밀한 Subsystem 사례 — 향후 다른 Subsystem 작성 시 *참조 모범 사례*. ⭐ Consumer Library 추가 (§9.5) — Subsystem 작성 + Consumer 작성 양쪽 패턴 정리.
