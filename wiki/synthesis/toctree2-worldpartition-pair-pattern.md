---
type: synthesis
title: "TOctree2 + WorldPartition 페어 표준 패턴 (대규모 월드 + 정밀 반경 쿼리)"
slug: toctree2-worldpartition-pair-pattern
created: 2026-05-13
last_updated: 2026-05-13
sources:
  - "[[sources/ue-spatialpartition-toctree2]]"
  - "[[sources/ue-spatialpartition-worldpartitionruntime]]"
  - "[[sources/ue-spatialpartition-skill]]"
  - "[[sources/ue-spatialpartition-staticspatialindex]]"
  - "[[sources/ue-gameframework-world]]"
  - "[[sources/ue-significance-skill]]"
entities: []
concepts:
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Profiling-Scope-Rule]]"
status: living
tags: [synthesis, spatial-partition, octree, worldpartition, streaming, large-world, pair-pattern]
citation_disclosure: "🟢 18 (SpatialPartition sub-skill source 직접 인용) / 🟡 2 (페어 통합 동작 외삽) / 🔴 0 · Cycle #11 보너스 발견 #2 vault 화"
---

# TOctree2 + WorldPartition 페어 표준 패턴

> 정밀판 sources: [[sources/ue-spatialpartition-toctree2]] · [[sources/ue-spatialpartition-worldpartitionruntime]]
> 카테고리: [[sources/ue-spatialpartition-skill]] (20번째 신규 카테고리, Phase 9)
> 페어 정책: Cycle #11 보너스 발견 #2 (raw `WorldPartitionRuntime.md` §3 직접 명시)

## 1. Thesis

🟢 UE 5.x 의 **대규모 월드 (1km+) 안 정밀 반경 쿼리** 는 *단일 시스템* 으로 못함. 두 시스템 페어 사용 표준:

```
[1] WorldPartition Runtime Spatial Hash → 액터 메모리 cell 로드/언로드 (자동)
                                          ↓
[2] TOctree2 (UWorldSubsystem)          → 로드된 액터 안 정밀 반경 쿼리 O(log N + K)
```

각 시스템의 책임이 *직교* — WorldPartition 은 *메모리 streaming*, TOctree2 는 *공간 인덱스*. 한쪽만 사용 시 한계 명확.

## 2. 왜 페어가 필수인가

### 2.1 WorldPartition 단독의 한계 🟢

WorldPartition Runtime Spatial Hash (raw `WorldPartitionRuntime.md` §2) 는 **cell 단위** 로드/언로드만 — 단위가 보통 25600 cm (256m). 정밀 "내 주변 N미터 적" 쿼리는 X:

| 사용 시도 | 한계 |
|----------|------|
| 반경 N미터 액터 검색 | 직접 API 없음 — cell 안 *모든* 액터 순회 (O(N)) |
| 셀 경계의 액터 처리 | 인접 cell 4-8개 모두 검사 |
| Active 액터 vs Streaming 액터 구분 | 별도 추적 필요 |

### 2.2 TOctree2 단독의 한계 🟢

TOctree2 (raw `TOctree2.md` §1) 는 **모든 액터가 메모리에 있다고 가정**:

| 사용 시도 | 한계 |
|----------|------|
| 1km+ 월드 모든 액터 등록 | 메모리 폭발 (수십만 액터) |
| 멀리 있는 액터까지 추적 | 의미 없음 (쿼리 못함) |
| World Origin Rebasing (LWC) | ApplyOffset Semantics 만으로 cell 동기화 불가 |

### 2.3 페어의 통합 효과 🟡

WorldPartition 이 *플레이어 근처 cell* 만 메모리 로드 → 그 액터들이 *BeginPlay 시 TOctree2 에 자동 등록* → 정밀 쿼리 가능. 액터가 cell 언로드되면 EndPlay → TOctree2 자동 해제. **모든 추적이 액터 라이프사이클에 자동 동기화**.

## 3. 표준 통합 패턴

### 3.1 단계별 통합 🟢

```cpp
// [1] WorldPartition 설정 — Map Settings 에서 활성 (디자이너)
// — UWorldPartitionRuntimeSpatialHash 자동 생성
// — UWorldPartitionStreamingSourceComponent 를 플레이어에 부착 (자동 cell 로드)

// [2] TOctree2 Subsystem — UWorldSubsystem 자손
UCLASS()
class UActorTrackerSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Coll) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UActorTrackerSubsystem::Initialize);
        Super::Initialize(Coll);
        // 100km half-extent — WorldPartition 의 cell 영역 충분히 포함
        Octree.Reset(new FActorOctree(FVector::ZeroVector, 100000.f));
    }

    void RegisterActor(AActor* Actor)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UActorTrackerSubsystem::RegisterActor);
        if (!IsValid(Actor) || !Octree) return;
        FActorOctreeElement E{TWeakObjectPtr<AActor>(Actor), GetActorBounds(Actor), {}};
        FOctreeElementId2 Id = Octree->AddElement(E);
        ActorToId.Add(Actor, Id);
    }

    void UnregisterActor(AActor* Actor)
    {
        if (FOctreeElementId2* Id = ActorToId.Find(Actor))
        {
            Octree->RemoveElement(*Id);     // O(1)
            ActorToId.Remove(Actor);
        }
    }
    // GetActorsInRadius / ForEachActorInRadius — [[sources/ue-spatialpartition-toctree2]] §2.5
};

// [3] AActor 측 — BeginPlay/EndPlay 페어
void AMyEnemy::BeginPlay()
{
    Super::BeginPlay();
    // WorldPartition 이 이 cell 을 streaming 로드 → BeginPlay 발화
    if (auto* T = GetWorld()->GetSubsystem<UActorTrackerSubsystem>())
        T->RegisterActor(this);
}
void AMyEnemy::EndPlay(const EEndPlayReason::Type R)
{
    // WorldPartition 이 cell 언로드 시 EndPlay = EEndPlayReason::RemovedFromWorld
    if (UWorld* W = GetWorld())
        if (auto* T = W->GetSubsystem<UActorTrackerSubsystem>())
            T->UnregisterActor(this);
    Super::EndPlay(R);    // Super LAST
}

// [4] 게임 로직 — 페어가 활성됐다는 사실 의식 X
void AMyPlayer::Tick(float DT)
{
    Super::Tick(DT);
    auto* Tracker = GetWorld()->GetSubsystem<UActorTrackerSubsystem>();
    if (!Tracker) return;
    // Player StreamingSource 가 cell 자동 로드 + Tracker 가 정밀 쿼리
    Tracker->ForEachActorInRadius(GetActorLocation(), 2000.f,
        [this](AActor* A) { ProcessEnemyInRange(A); });
}
```

### 3.2 EEndPlayReason 매트릭스 🟢

WorldPartition 의 cell 언로드 시점 = `AActor::EndPlay(EEndPlayReason::RemovedFromWorld)`. TOctree2 가 정상 해제:

| EndPlay Reason | TOctree2 Unregister | WorldPartition 트리거 |
|---------------|---------------------|---------------------|
| `LevelTransition` | ✅ | World transition 시 |
| `Destroyed` | ✅ | `Destroy()` 호출 |
| `RemovedFromWorld` | ✅ | **WorldPartition cell 언로드** ⭐ |
| `Quit` | ✅ | 게임 종료 |
| `EndPlayInEditor` | ✅ | PIE 종료 |

> 🟢 [[sources/ue-gameframework-actor]] §라이프사이클 + 본 페어 패턴 정합.

## 4. 함정

### 4.1 cell 경계 함정 🟡

플레이어가 cell 경계 근처일 때 — *반경 쿼리* 가 인접 cell 의 미로드 액터를 *놓침*. 해결:

- **StreamingSource 의 LoadingRange** 를 *쿼리 최대 반경* 보다 크게 설정 (보통 2× 여유)
- WorldPartition Project Settings → StreamingSource → `bSpatialQuery=true`
- 또는 게임 로직 단에 "관심 반경 N미터" 를 cell 단위로 적응 (UWorldPartitionStreamingSourceComponent 의 Priority 활용)

### 4.2 TOctree2 LWC ApplyOffset 미적용 🟢

대규모 월드 + World Origin Rebasing 활성 시 `Semantics::ApplyOffset` 누락 → cell 좌표 깨짐. ([[sources/ue-spatialpartition-toctree2]] §2.4 의무) — Semantics 6+ 요소 모두 명시.

### 4.3 BeginPlay 이전 등록 시도 🟢

WorldPartition cell 로드 *비동기* — 액터 spawn 직후 BeginPlay 발화까지 1-2 frame gap. 그 사이 다른 시스템이 Tracker 쿼리 시 *누락* 가능. 해결: 쿼리 측이 *최대 1 frame stale 허용* 또는 EndOfFrame 단위 일괄 처리.

### 4.4 EndPlay 중복 처리 🟡

cell 언로드 시 `EEndPlayReason::RemovedFromWorld` + 게임 종료 시 `Quit` 둘 다 발화 가능. TOctree2 Unregister 가 *중복 호출 안전* 인지 검증 — `ActorToId.Find` nullptr 검사로 자동 안전 (방어 패턴 권장).

### 4.5 Significance Manager 와 3중 스택 🟢

대규모 월드 + 정밀 쿼리 + LOD/Tick 토글 = **3중 시스템 스택**:

```
[1] WorldPartition         → cell 단위 메모리 streaming
[2] TOctree2 Tracker       → 정밀 반경 쿼리
[3] USignificanceManager   → 거리 기반 LOD/Tick priority
```

각 시스템이 *직교 책임* — 한 시스템이 다른 책임을 흉내내면 비효율. ([[sources/ue-significance-skill]] 페어)

## 5. 성능 매트릭스

| 시나리오 | WorldPartition 단독 | TOctree2 단독 | 페어 |
|----------|--------------------|--------------------|------|
| 1km+ 월드 메모리 | ✅ cell streaming | ❌ 전 액터 로드 | ✅ |
| 반경 N미터 쿼리 | ❌ O(N) cell scan | ✅ O(log N + K) | ✅ |
| 매 프레임 수백 쿼리 | ❌ 비용 폭발 | ✅ 빠름 | ✅ |
| 동적 spawn/destroy | ⚠ cell 가산 비용 | ✅ O(log N) | ✅ |
| LWC (Large World) | ✅ 자동 | ✅ ApplyOffset 의무 | ✅ |

## 6. Cross-link

### Sources

- [[sources/ue-spatialpartition-toctree2]] (정밀 쿼리 권위)
- [[sources/ue-spatialpartition-worldpartitionruntime]] (streaming 권위)
- [[sources/ue-spatialpartition-skill]] (카테고리 main)
- [[sources/ue-spatialpartition-staticspatialindex]] (WorldPartition 내부 R-Tree)
- [[sources/ue-gameframework-world]] (WorldPartition Streaming)
- [[sources/ue-significance-skill]] (3중 스택의 LOD 축)

### Concepts

- [[concepts/Subsystem-5-Types]] (UWorldSubsystem 등록 호스트)
- [[concepts/Component-Policies-6]] §3 (TWeakObjectPtr GC 방어)
- [[concepts/Asset-Loading-Policy]] (Editor Pure Sync)
- [[concepts/Profiling-Scope-Rule]] (콜백 첫 줄 스코프)

### Related synthesis

- [[synthesis/character-many-npc-5-fold-optimization]] (다수 NPC 5중 최적화 — 공간 분할 축 페어 활용)
- [[synthesis/ai-npc-squad-coordination-tick-budget]] (squad coordination — TOctree2 페어)


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[synthesis/mc-actor-spawn-subsystem-implementation]] (inbound=3, suggest_missing_cross_link high confidence)
## 7. 신뢰도 매트릭스

| Claim | Tier | 근거 |
|-------|------|------|
| WorldPartition cell streaming 자동 | 🟢 | [[sources/ue-spatialpartition-worldpartitionruntime]] §2 (raw L66-76) |
| TOctree2 O(log N + K) | 🟢 | [[sources/ue-spatialpartition-toctree2]] §2.4 (raw L317-381) |
| 페어 통합 표준 — BeginPlay/EndPlay 자동 동기 | 🟢 | raw `WorldPartitionRuntime.md` §3 (L83-103) |
| EEndPlayReason::RemovedFromWorld 매트릭스 | 🟢 | [[sources/ue-gameframework-actor]] §라이프사이클 |
| cell 경계 LoadingRange × 2 권장 | 🟡 | 일반 spatial partition 패턴 외삽 — raw 명시 없음 |
| BeginPlay 1-2 frame gap | 🟡 | 일반 streaming 동작 — raw 명시 없음 |
| Significance Manager 3중 스택 | 🟢 | [[sources/ue-spatialpartition-skill]] §2 (Significance 페어 명시) |
