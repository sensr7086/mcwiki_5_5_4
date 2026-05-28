---
type: source
title: "UE SpatialPartition — WorldPartitionRuntime (5.x 대규모 월드 스트리밍)"
slug: ue-spatialpartition-worldpartitionruntime
source_path: raw/ue-wiki-llm/skills/SpatialPartition/references/WorldPartitionRuntime.md
source_kind: text
source_date: 2026-05-12
ingested: 2026-05-13
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, spatial-partition, worldpartition, streaming, large-world, slim-card]
citation_disclosure: "🟢 9 / 🟡 0 / 🔴 0 · 보너스 발견 1건 (TOctree2 + WorldPartition 페어 패턴 = synthesis 후보)"
---

# UE SpatialPartition — WorldPartitionRuntime (5.x)

> Source: [[raw/ue-wiki-llm/skills/SpatialPartition/references/WorldPartitionRuntime.md]] (124L)
> Parent: [[sources/ue-spatialpartition-skill]] · Pair: [[sources/ue-spatialpartition-toctree2]] (정밀 쿼리 페어)
> 위치: `Engine/Public/WorldPartition/WorldPartitionRuntimeSpatialHash.h:14-100` + `RuntimeSpatialHashGridHelper.h:27`

## 1. Summary

🟢 UE 5.x 표준 — **대규모 월드** (1km+) 안 액터의 **자동 스트리밍** (메모리 cell 단위 로드/언로드). 단순 "내 주변 N미터 액터" 정밀 쿼리는 X — `TOctree2` 페어 사용 권장. WorldPartition Runtime Spatial Hash 가 cell-level streaming, TOctree2 가 element-level query.

## 2. Key claims

### 2.1 핵심 클래스 🟢 [verified] (raw L29-62)

```cpp
typedef FInt64Vector3 FGridCellCoord;     // 대규모 월드 좌표 (3D cell)
typedef FInt64Vector2 FGridCellCoord2;    // 2D cell

struct FSquare2DGridHelper                 // RuntimeSpatialHashGridHelper.h:27
{
    struct FGrid2D
    {
        FVector2D Origin;  int64 CellSize;  int64 GridSize;
        bool IsValidCoords(const FGridCellCoord2&) const;
        bool GetCellBounds(int64 Index, FBox2D& OutBounds) const;
        bool GetCellBounds(const FGridCellCoord2& Coords, FBox2D& OutBounds, bool bCheckValid = true) const;
        // GetIntersectingCells / ForEachIntersectingCells
    };
};

UCLASS()
class UWorldPartitionRuntimeSpatialHash : public UWorldPartitionRuntimeHash
{ /* World 액터 자동 스트리밍 */ };
```

### 2.2 사용 시점 🟢 (raw §2)

| 시나리오 | 적합 |
|----------|:----:|
| 오픈 월드 (1km+) 액터 스트리밍 | ✅ |
| 고정 데이터 cell 단위 검색 (HLOD) | ✅ |
| GridLayer 기반 World 분할 | ✅ |
| 반경 N미터 액터 쿼리 | ❌ → TOctree2 |
| 작은 레벨 (200m 이하) | ❌ 오버킬 |

### 2.3 WorldPartition + TOctree2 페어 표준 🟢 ⭐ (raw §3)

대규모 월드 = **두 시스템 협업**:

```
[1] WorldPartition Runtime Spatial Hash → 액터 메모리 cell 로드/언로드 (자동)
                                          ↓
[2] TOctree2 (UWorldSubsystem)          → 로드된 액터 안 정밀 반경 쿼리
```

```cpp
void AMyPlayer::Tick(float DT)
{
    // [1] WorldPartition 자동 — 플레이어 StreamingSource 가 cell 로드/언로드
    // [2] TOctree2 = 로드된 액터 안 반경 쿼리
    if (auto* T = GetWorld()->GetSubsystem<UActorTrackerSubsystem>())
        T->ForEachActorInRadius(GetActorLocation(), 2000.f, [](AActor* A) { /* ... */ });
}
```

## 3. 함정 (raw §4)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 정밀 반경 쿼리 시 WorldPartition 사용 | TOctree2 페어 |
| 2 | WorldPartition 비활성 World 사용 | Map Settings 에서 활성 |
| 3 | StreamingSource 등록 누락 | `UWorldPartitionStreamingSourceComponent` 추가 |
| 4 | Cell Size 너무 크게 → 메모리 폭발 | 보통 25600 cm (256m) 시작 |
| 5 | HLOD Layer 미고려 | `DefaultEngine.ini` HLODLayer 설정 |

## 4. Cross-link

- Parent: [[sources/ue-spatialpartition-skill]]
- Pair (정밀 쿼리): [[sources/ue-spatialpartition-toctree2]]
- 내부 사용: [[sources/ue-spatialpartition-staticspatialindex]] (R-Tree 가 WorldPartition 내부)
- World 측: [[sources/ue-gameframework-world]] (WorldPartition Streaming)
- 정책: 🚨 [[sources/ue-ref-11-assetloadingpolicy]] §3 (Editor Pure Sync)
