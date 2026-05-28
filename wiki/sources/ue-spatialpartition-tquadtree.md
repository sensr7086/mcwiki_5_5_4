---
type: source
title: "UE SpatialPartition — TQuadTree (2D 공간 분할)"
slug: ue-spatialpartition-tquadtree
source_path: raw/ue-wiki-llm/skills/SpatialPartition/references/TQuadTree.md
source_kind: text
source_date: 2026-05-12
ingested: 2026-05-13
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Subsystem-5-Types]]"
tags: [ue, spatial-partition, quadtree, 2d, top-down, rts, slim-card]
citation_disclosure: "🟢 9 / 🟡 0 / 🔴 0 · 보너스 발견 0건"
---

# UE SpatialPartition — TQuadTree (2D)

> Source: [[raw/ue-wiki-llm/skills/SpatialPartition/references/TQuadTree.md]] (141L)
> Parent: [[sources/ue-spatialpartition-skill]] · Pair: [[sources/ue-spatialpartition-toctree2]] (3D 표준)
> 위치: `Engine/Public/GenericQuadTree.h:9-50`

## 1. Summary

🟢 2D 평면 충분 시나리오 (탑다운 / RTS / 미니맵 / AOE 2D) 의 공간 분할. `TOctree2` 보다 **메모리 1/4** (3축 → 2축). NodeCapacity 4 디폴트.

## 2. Key claims

### 2.1 API 🟢 [verified] (raw L26-44)

```cpp
template <typename ElementType, int32 NodeCapacity = 4>
class TQuadTree
{
public:
    TQuadTree(const FBox2D& InBox, float InMinimumQuadSize = 100.f);
    void Insert(const ElementType& Element, const FBox2D& Box, const TCHAR* DebugContext = nullptr);
    template <typename Func>
    void GetElements(const FBox2D& Box, Func&& Callback) const;
    bool Remove(const ElementType& Instance, const FBox2D& Box);     // ⚠ 원본 Box 필요
    void Empty();
};
```

### 2.2 AActor 트래커 패턴 🟢 (raw L48-109)

`UActorTrackerQuadSubsystem : UWorldSubsystem`:

- Initialize — `QuadTree.Reset(new TQuadTree<TWeakObjectPtr<AActor>>(WorldBox, MinQuadSize=200.f))` (보통 2km × 2km)
- RegisterActor — Box2D 계산 (50.f 반경) + `QuadTree->Insert(Actor, Box)` + `ActorBoxMap.Add(Actor, Box2D)`
- UnregisterActor — `ActorBoxMap.Find` → `QuadTree->Remove(Actor, *Box)` (⚠ 원본 Box2D 보관 필수)
- GetActorsInRadius — Box prefilter → `GetElements` callback → 2D 거리 정밀 검사

### 2.3 TOctree2 vs TQuadTree 🟢 (raw §3)

| 항목 | TOctree2 | TQuadTree |
|------|----------|-----------|
| 차원 | 3D | 2D |
| 메모리 | 4× (3축) | 1× (2축) |
| 적합 게임 | FPS / 오픈월드 / 3D MOBA | 탑다운 / RTS / 2D / 미니맵 |
| API | `FBoxCenterAndExtent` | `FBox2D` |
| Semantics | 6 요소 의무 | 별도 X (NodeCapacity 만) |
| Element ID | `FOctreeElementId2` O(1) 제거 | Box 보관 O(log N) 제거 |

## 3. 함정 (raw §4)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 높이 차이 무시 — 위층 적이 1층 쿼리에 포함 | 결과 후 Z 거리 검사 |
| 2 | `Remove` 시 원본 `FBox2D` 보관 안 함 | `TMap<Actor, FBox2D>` 으로 보관 |
| 3 | 매 Insert 시 새 Box2D 생성 비용 | 최소 cell size 충분히 크게 |
| 4 | 위치 변경 시 Remove + Insert 누락 | OnActorMoved 콜백 페어 |

## 4. Cross-link

- Parent: [[sources/ue-spatialpartition-skill]]
- Sibling: [[sources/ue-spatialpartition-toctree2]] (3D 표준) · [[sources/ue-spatialpartition-staticspatialindex]] (정적)
- 정책: [[concepts/Profiling-Scope-Rule]] · [[concepts/Component-Policies-6]] §3 · [[concepts/Subsystem-5-Types]]
