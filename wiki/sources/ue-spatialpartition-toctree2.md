---
type: source
title: "UE SpatialPartition — TOctree2 (AActor 트래커 표준 ⭐⭐⭐)"
slug: ue-spatialpartition-toctree2
source_path: raw/ue-wiki-llm/skills/SpatialPartition/references/TOctree2.md
source_kind: text
source_date: 2026-05-12
ingested: 2026-05-13
last_updated: 2026-05-28
audit_5_5_4: pass-body-reconciled  # 2026-05-28 Phase 2-C body-reconciliation
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Global-Iterator-Avoidance]]"
  - "[[concepts/Subsystem-5-Types]]"
tags: [ue, spatial-partition, octree, toctree2, actor-tracker, slim-card, verified]
citation_disclosure: "🟢 14 / 🟡 0 / 🔴 0 · 보너스 발견 1건 (UWorldOriginRebasing ApplyOffset LWC 5.x — vault 미카탈로그)"
---

# UE SpatialPartition — TOctree2 ⭐⭐⭐

> Source: [[raw/ue-wiki-llm/skills/SpatialPartition/references/TOctree2.md]] (655L)
> Parent: [[sources/ue-spatialpartition-skill]] · Engine 검증: `PrimitiveSceneInfo.h` 사용 (`FScenePrimitiveOctree`)
> **가장 권장** — 다수 NPC 매 프레임 "내 주변 N미터 적" 조회 등 가장 흔한 시나리오.

## 1. Summary

🟢 `TOctree2<ElementType, OctreeSemantics>` — `Core/Public/Math/GenericOctree.h` 의 3D 범용 Octree. Renderer 의 `FScenePrimitiveOctree` 와 *동일 패턴*. AddElement O(log N) / RemoveElement O(1) (FOctreeElementId2 보관 시) / FindElementsWithBoundsTest O(log N + K). 메모리 ~80 bytes/element. 수만 액터 매 프레임 쿼리 OK.

## 2. Key claims

### 2.1 API 핵심 🟢 [verified] (raw L36-66)

```cpp
template<typename ElementType, typename OctreeSemantics>
class TOctree2
{
public:
    TOctree2(const FVector& InOrigin, FVector::FReal InExtent);   // 월드 중심 + 반경
    FOctreeElementId2 AddElement(const ElementType& Element);
    void RemoveElement(FOctreeElementId2 ElementId);              // O(1) — SetElementId 의무
    template <typename Func>
    void FindElementsWithBoundsTest(const FBoxCenterAndExtent& Box, const Func& F) const;
    template <typename Func>
    void FindAllElements(const Func& F) const;
};
```

### 2.2 Semantics 6 요소 🟢 [verified — FPrimitiveOctreeSemantics 모사] (raw L78-114, `PrimitiveSceneInfo.h:808-840`)

| 요소 | 필수 | 설명 |
|------|------|------|
| `MaxElementsPerLeaf` | ✅ | 리프당 element 한계 (Renderer 256, 일반 16) |
| `MinInclusiveElementsPerNode` | ✅ | 노드 병합 임계 (보통 7) |
| `MaxNodeDepth` | ✅ | 트리 최대 깊이 (보통 12) |
| `ElementAllocator` | ✅ | `FDefaultAllocator` 또는 `TInlineAllocator` |
| `GetBoundingBox` | ✅ | Octree 가 분류용으로 호출 |
| `AreElementsEqual` | ✅ | Remove 시 동등성 비교 |
| `SetElementId` | ⭐ 필수 | **O(1) 제거 의무** — Id 보관 안 하면 RemoveElement 시 O(N) |
| `ApplyOffset` | ✅ 5.x | LWC (Large World Coordinates) — World Origin Rebasing 시 호출 |

### 2.3 표준 Semantics 패턴 🟢 (raw L78-114)

```cpp
struct FActorOctreeSemantics
{
    enum { MaxElementsPerLeaf      = 16 };
    enum { MinInclusiveElementsPerNode = 7 };
    enum { MaxNodeDepth            = 12 };
    using ElementAllocator = FDefaultAllocator;

    FORCEINLINE static FBoxCenterAndExtent GetBoundingBox(const FActorOctreeElement& E)
    { return FBoxCenterAndExtent(E.Bounds.Origin, E.Bounds.BoxExtent); }

    FORCEINLINE static bool AreElementsEqual(const FActorOctreeElement& A, const FActorOctreeElement& B)
    { return A.Actor == B.Actor; }

    FORCEINLINE static void SetElementId(const FActorOctreeElement& Element, FOctreeElementId2 Id)
    { const_cast<FActorOctreeElement&>(Element).OctreeId = Id; }    // Renderer 표준 패턴

    FORCEINLINE static void ApplyOffset(FActorOctreeElement& Element, FVector Offset)
    { Element.Bounds.Origin += Offset; }
};
```

### 2.4 UWorldSubsystem 통합 표준 패턴 🟢 (raw §4)

`UActorTrackerSubsystem : public UWorldSubsystem` 안:

- `Initialize` — `Octree = MakeUnique<TOctree2<...>>(FVector::ZeroVector, 100000.f)` (100km extent)
- `Deinitialize` — `Octree.Reset()`
- `RegisterActor(AActor*)` — Element 생성 + `Octree->AddElement(E)` → `ActorToId.Add(Actor, E.OctreeId)`
- `UnregisterActor(AActor*)` — `ActorToId.Find` → `Octree->RemoveElement(Id)` (O(1))
- `UpdateActor(AActor*)` — 위치 변경 시 Remove + Add (immutable bounds)

### 2.5 ⭐ 핵심 쿼리 API — 반경 N미터 액터 🟢 (raw L317-381)

```cpp
void UActorTrackerSubsystem::GetActorsInRadius(const FVector& Center, float Radius, TArray<AActor*>& Out) const
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UActorTrackerSubsystem::GetActorsInRadius);
    if (!Octree) return;
    Out.Reset();
    const FBoxCenterAndExtent Query(Center, FVector(Radius));
    const float RadSq = Radius * Radius;
    Octree->FindElementsWithBoundsTest(Query, [&Out, Center, RadSq](const FActorOctreeElement& E)
    {
        AActor* A = E.Actor.Get();                       // TWeakObjectPtr lifetime 검사
        if (!IsValid(A)) return;
        if (FVector::DistSquared(A->GetActorLocation(), Center) <= RadSq)   // 박스 prefilter → 정밀 거리
        { Out.Add(A); }
    });
}
```

추가 패턴 — `ForEachActorInRadius` (alloc 회피 — 결과 배열 없이 lambda 직접 처리).

### 2.6 AActor 측 통합 🟢 (raw L389-411)

```cpp
void AMyEnemy::BeginPlay()
{
    Super::BeginPlay();
    if (auto* T = GetWorld()->GetSubsystem<UActorTrackerSubsystem>()) { T->RegisterActor(this); }
}
void AMyEnemy::EndPlay(const EEndPlayReason::Type R)
{
    if (UWorld* W = GetWorld())
        if (auto* T = W->GetSubsystem<UActorTrackerSubsystem>()) { T->UnregisterActor(this); }
    Super::EndPlay(R);   // ⭐ 정리 후 Super
}
```

## 3. 함정 (raw §3.1 + §함정 종합 — 5대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Element 안 `AActor*` 직접 | `TWeakObjectPtr<AActor>` + `IsValid` |
| 2 | `SetElementId` 누락 → 제거 O(N) | Semantics 안 const_cast 패턴 의무 |
| 3 | Element 위치 변경 시 Octree 갱신 누락 | Remove + Add 페어 (immutable bounds) |
| 4 | LWC `ApplyOffset` 누락 → World Origin Rebasing 시 좌표 깨짐 | Semantics 안 명시 |
| 5 | World Extent 너무 작음 → 액터 outside | 100km 초기화 권장 |

## 4. 신뢰도 매트릭스

| 영역 | Tier | 근거 |
|------|------|------|
| TOctree2 API 시그니처 | 🟢 [verified] | raw L36-66 + Engine `GenericOctree.h` |
| Semantics 6 요소 | 🟢 [verified] | raw L78-114 + `PrimitiveSceneInfo.h:808-840` |
| O(log N) / O(1) / O(log N + K) 복잡도 | 🟢 [verified] | Engine `FScenePrimitiveOctree` 실 사용 |
| UWorldSubsystem 통합 4단계 | 🟢 [verified] | raw §4 (Subsystem-5-Types 페어) |
| GetActorsInRadius 박스 prefilter 패턴 | 🟢 [verified] | raw L317-381 |
| BeginPlay/EndPlay Super 호출 순서 | 🟢 [verified] | raw L398-411 + `04_OverrideIndex` |

## 5. Cross-link

- Parent: [[sources/ue-spatialpartition-skill]]
- Sibling: [[sources/ue-spatialpartition-tquadtree]] (2D 대안) · [[sources/ue-spatialpartition-staticspatialindex]] (정적) · [[sources/ue-spatialpartition-worldpartitionruntime]] (1km+)
- 페어: [[sources/ue-significance-skill]] (거리 LOD 결합)
- Engine 검증: [[sources/ue-render-meshdrawing]] §FScenePrimitiveOctree
- 정책: [[concepts/Profiling-Scope-Rule]] · [[concepts/Component-Policies-6]] §3 · [[concepts/Subsystem-5-Types]]
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 4
- 추가 (5.5.4 에만): 1
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `description: TOctree2<T, Semantics> 기반 AActor 트래커 deep 표준 — Semantics 정의 + UWorl → description: TOctree2<T, Semantics> 기반 AActor 트래커 deep 표준 — Semantics 정의 + UWorl`
- `>   - Renderer/Public/PrimitiveSceneInfo.h:46, 239, 808 — FScenePrimitiveOctr → >   - Renderer/Public/PrimitiveSceneInfo.h:259, 828 — FScenePrimitiveOctree `
- `FPrimitiveOctreeSemantics ([PrimitiveSceneInfo.h:808-840](../../Render/refer → FPrimitiveOctreeSemantics ([PrimitiveSceneInfo.h:828-852](../../Render/refer`
- `| FOctreeElementId2 SetElementId 패턴 | **[verified]** ✅ | Renderer/Public/Primit → | FOctreeElementId2 SetElementId 패턴 | **[verified]** ✅ | Renderer/Public/Primit`

**5.5.4 에만 (5.7.4 에 없음)**:
- `| FPrimitiveOctreeSemantics 6 요소 패턴 | **[verified]** ✅ | Renderer/Public/PrimitiveSceneInfo.h:828-852 (5.5) |`

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/SpatialPartition/references/TOctree2.md · 5.7.4 vintage 비교: raw/ue-wiki-llm/skills/SpatialPartition/references/TOctree2.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **1 변경**
- 정합 후 tier: **🟢 pass-body-reconciled**
