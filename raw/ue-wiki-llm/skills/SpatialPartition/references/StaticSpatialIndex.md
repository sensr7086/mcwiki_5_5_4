---
name: spatial-staticspatialindex
description: TStaticSpatialIndex (R-Tree) — 정적 데이터 공간 인덱스. WorldPartition/RuntimeHashSet/StaticSpatialIndex.h. TRTreeImpl (MaxNumElementsPerNode=16) + TListImpl. 한 번 빌드 후 변경 X 시 TOctree2 보다 빠름.
---

# SpatialPartition/StaticSpatialIndex — 정적 R-Tree 인덱스

> **위치 (verified)**: `Engine/Public/WorldPartition/RuntimeHashSet/StaticSpatialIndex.h:14-650`
> **요지**: **정적** 데이터 (BeginPlay 후 변경 X) 의 공간 인덱스. R-Tree (Rectangle Tree) 구현 — Tree 가 element 분포에 균등 적응 (Octree 보다 unbalanced 데이터 우수). 한 번 빌드 후 query 만 시 `TOctree2` 보다 메모리 / cache 효율.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 정적 데이터 한정 | BeginPlay 후 변경 X — 동적 변경 = TOctree2 |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | Query 함수 첫 줄 스코프 |

---

## 1. API [verified]

```cpp
// Engine/Public/WorldPartition/RuntimeHashSet/StaticSpatialIndex.h:14-23
namespace FStaticSpatialIndex
{
    struct FSpatialIndexProfile2D    // 2D variant
    {
        enum { Is3D = 0 };
        using FReal     = FVector2D::FReal;
        using FVector   = FVector2D;
        using FIntPoint = FIntVector2;
        using FBox      = FBox2D;
    };

    struct FSpatialIndexProfile3D    // 3D variant
    {
        enum { Is3D = 1 };
        using FReal     = FVector::FReal;
        using FVector   = FVector;
        using FIntPoint = FIntVector;
        using FBox      = FBox;
    };
}

// 베이스 인터페이스 (라인 172-227)
template <typename ValueType, typename Profile,
          class SpatialIndexType, class ElementsSorter>
class TStaticSpatialIndex : public TStaticSpatialIndexDataInterface<Profile>
{
    template <class Func> /* ForEachIntersectingElement */
    template <class Func> /* ForEachElement */
};

// R-Tree 구현 (라인 396-)
template <typename Profile, int32 MaxNumElementsPerNode = 16,
          int32 MaxNumElementsPerLeaf = 64>
class TRTreeImpl;

// List 구현 (작은 데이터셋)
template <typename Profile>
class TListImpl;
```

---

## 2. 사용 시점

| 시나리오 | 적합 |
|---------|:----:|
| **레벨 안 정적 픽업 아이템** (변경 X) | ✅ |
| **고정 적 spawn point** (BeginPlay 후 불변) | ✅ |
| **Tower Defense 적 경로 안 정적 타워** (배치 후 불변) | ✅ |
| **NavMesh poly 검색** | ✅ |
| **동적 Spawn/Destroy 액터** | ❌ TOctree2 사용 |
| **자주 이동하는 캐릭터** | ❌ TOctree2 사용 |

---

## 3. 핵심 차이 — TOctree2 vs StaticSpatialIndex

| 항목 | TOctree2 | StaticSpatialIndex (R-Tree) |
|------|----------|------------------------------|
| 동적 변경 | ✅ Add/Remove O(log N) | ❌ 한 번 빌드 후 immutable |
| 빌드 비용 | 증분 (per Add) | 일괄 (모든 element 한 번에) |
| Unbalanced 데이터 | ⚠ 빈 octant 메모리 낭비 | ✅ Tree 가 분포 적응 |
| Cache 효율 | 중간 | ✅ 더 높음 (정적 layout) |
| 메모리 (1만 element) | ~80 bytes / element | ~50 bytes / element |
| API 복잡도 | Semantics 6 요소 | Profile + Sorter (간단) |

---

## 4. 함정

| # | 함정 | 정답 |
|---|------|------|
| 1 | 동적 변경 시 사용 | TOctree2 로 전환 |
| 2 | 빌드 비용 미고려 — BeginPlay 안 지연 | 비동기 빌드 또는 Cook 시점 사전 빌드 |
| 3 | 2D / 3D Profile 선택 잘못 | FSpatialIndexProfile2D vs 3D 명시 |
| 4 | List 구현 (TListImpl) 큰 데이터셋 사용 | 100+ element = R-Tree 사용 |

---

## 5. 관련

- [`../SKILL.md`](../SKILL.md)
- [`./TOctree2.md`](./TOctree2.md) — 동적 데이터 표준
- [`./WorldPartitionRuntime.md`](./WorldPartitionRuntime.md) — 대규모 월드 스트리밍 (StaticSpatialIndex 가 내부 사용)
