---
type: source
title: "UE SpatialPartition — StaticSpatialIndex (정적 R-Tree)"
slug: ue-spatialpartition-staticspatialindex
source_path: raw/ue-wiki-llm/skills/SpatialPartition/references/StaticSpatialIndex.md
source_kind: text
source_date: 2026-05-12
ingested: 2026-05-13
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, spatial-partition, rtree, static, slim-card]
citation_disclosure: "🟢 8 / 🟡 1 / 🔴 0 · 보너스 발견 0건"
---

# UE SpatialPartition — StaticSpatialIndex (R-Tree)

> Source: [[raw/ue-wiki-llm/skills/SpatialPartition/references/StaticSpatialIndex.md]] (109L)
> Parent: [[sources/ue-spatialpartition-skill]] · Pair: [[sources/ue-spatialpartition-toctree2]] (동적 대안)
> 위치: `Engine/Public/WorldPartition/RuntimeHashSet/StaticSpatialIndex.h:14-650`

## 1. Summary

🟢 정적 데이터 (BeginPlay 후 변경 X) 의 공간 인덱스. **R-Tree** 구현 — Tree 가 element 분포에 균등 적응 (Octree 보다 unbalanced 데이터 우수). 한 번 빌드 후 query 만 시 `TOctree2` 보다 메모리 ↓ + cache 효율 ↑. 2D / 3D Profile 분리.

## 2. Key claims

### 2.1 API 🟢 [verified] (raw L24-64)

```cpp
namespace FStaticSpatialIndex
{
    struct FSpatialIndexProfile2D { /* FVector2D / FBox2D */ };
    struct FSpatialIndexProfile3D { /* FVector / FBox */ };
}

template <typename ValueType, typename Profile, class SpatialIndexType, class ElementsSorter>
class TStaticSpatialIndex : public TStaticSpatialIndexDataInterface<Profile>
{
    template <class Func> /* ForEachIntersectingElement */
    template <class Func> /* ForEachElement */
};

template <typename Profile, int32 MaxNumElementsPerNode = 16, int32 MaxNumElementsPerLeaf = 64>
class TRTreeImpl;             // R-Tree (대용량)

template <typename Profile>
class TListImpl;              // List (작은 데이터)
```

### 2.2 사용 시점 🟢 (raw §2)

| 시나리오 | 적합 |
|---------|:----:|
| 레벨 안 정적 픽업 아이템 (변경 X) | ✅ |
| 고정 적 spawn point (BeginPlay 후 불변) | ✅ |
| Tower Defense 정적 타워 | ✅ |
| NavMesh poly 검색 | ✅ |
| 동적 Spawn/Destroy 액터 | ❌ → TOctree2 |

### 2.3 TOctree2 vs StaticSpatialIndex 🟢 (raw §3)

| 항목 | TOctree2 | StaticSpatialIndex |
|------|----------|---------------------|
| 동적 변경 | ✅ Add/Remove O(log N) | ❌ immutable 빌드 후 |
| 빌드 비용 | 증분 (per Add) | 일괄 (한 번에) |
| Unbalanced 데이터 | ⚠ 빈 octant 낭비 | ✅ Tree 가 분포 적응 |
| Cache 효율 | 중간 | ✅ 더 높음 (정적 layout) |
| 메모리 (1만 element) | ~80 bytes / element | ~50 bytes / element |
| API 복잡도 | Semantics 6 요소 | Profile + Sorter 간단 |

### 2.4 R-Tree 파라미터 🟡

`TRTreeImpl<Profile, 16, 64>` 의 16 / 64 = MaxNumElementsPerNode / PerLeaf. 작은 데이터셋 (< 100 element) 은 `TListImpl` 사용 권장 — vault 외 일반 데이터 구조 지식 외삽.

## 3. 함정 (raw §4)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 동적 변경 시 사용 | TOctree2 로 전환 |
| 2 | 빌드 비용 미고려 — BeginPlay 안 지연 | 비동기 빌드 또는 Cook 시점 사전 빌드 |
| 3 | 2D / 3D Profile 잘못 선택 | `FSpatialIndexProfile2D` vs `3D` 명시 |
| 4 | `TListImpl` 큰 데이터셋 사용 | 100+ element = `TRTreeImpl` |

## 4. Cross-link

- Parent: [[sources/ue-spatialpartition-skill]]
- Sibling: [[sources/ue-spatialpartition-toctree2]] (동적 표준) · [[sources/ue-spatialpartition-worldpartitionruntime]] (StaticSpatialIndex 내부 사용)
- 정책: [[concepts/Profiling-Scope-Rule]]
