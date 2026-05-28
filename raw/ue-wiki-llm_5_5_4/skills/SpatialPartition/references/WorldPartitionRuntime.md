---
name: spatial-worldpartitionruntime
description: WorldPartition Runtime Spatial Hash — 5.x 대규모 월드 액터 스트리밍 (cell 단위 로드/언로드). UWorldPartitionRuntimeSpatialHash + FSquare2DGridHelper + FGridCellCoord. 1km+ 월드 표준. 정밀 반경 쿼리 X — TOctree2 와 페어 사용.
---

# SpatialPartition/WorldPartitionRuntime — 5.x 대규모 월드 스트리밍

> **위치 (verified)**:
> - `Engine/Public/WorldPartition/WorldPartitionRuntimeSpatialHash.h` (라인 14-100)
> - `Engine/Public/WorldPartition/RuntimeSpatialHash/RuntimeSpatialHashGridHelper.h:27` — `FSquare2DGridHelper`
> - `FGridCellCoord` = `FInt64Vector3`, `FGridCellCoord2` = `FInt64Vector2` (대규모 월드 좌표)
>
> **요지**: 5.x 표준 — **대규모 월드** (1km+) 안 액터의 **자동 스트리밍** (메모리 로드/언로드). 단순 "내 주변 N미터 액터" 쿼리는 X — `TOctree2` 와 페어 사용 권장.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 Streaming Cell 단위 | 정밀 반경 쿼리 X — 단위 = cell (보통 25600cm = 256m) |
| 🚨 Editor 설정 의무 | WorldPartition 활성 World 만 동작 — Map Settings 에서 활성 |
| 🚨 [`11_AssetLoadingPolicy §3`](../../../references/11_AssetLoadingPolicy.md) | Editor Pure 모드 = Sync Load |

---

## 1. 핵심 클래스 [verified]

```cpp
// WorldPartitionRuntimeSpatialHash.h:14-20
typedef FInt64Vector3 FGridCellCoord;
typedef FInt64Vector2 FGridCellCoord2;

// RuntimeSpatialHashGridHelper.h:27
struct FSquare2DGridHelper
{
    struct FGrid2D
    {
        FVector2D Origin;
        int64 CellSize;
        int64 GridSize;

        bool IsValidCoords(const FGridCellCoord2& InCoords) const;
        bool GetCellBounds(int64 InIndex, FBox2D& OutBounds) const;
        bool GetCellBounds(const FGridCellCoord2& InCoords, FBox2D& OutBounds, bool bCheckIsValidCoord = true) const;
        // ... GetIntersectingCells / ForEachIntersectingCells 등
    };
};

// WorldPartitionRuntimeSpatialHash.h:90-100
USTRUCT()
struct FSpatialHashStreamingGridLevel
{
    // 그리드 레벨 (계층 LOD)
};

UCLASS()
class UWorldPartitionRuntimeSpatialHash : public UWorldPartitionRuntimeHash
{
    // 메인 — World 의 액터 자동 스트리밍
};
```

---

## 2. 사용 시점

| 시나리오 | 적합 |
|----------|:----:|
| **오픈 월드 (1km+)** 액터 스트리밍 | ✅ |
| **고정 데이터 cell 단위 검색** (HLOD) | ✅ |
| **GridLayer 기반 World 분할** (Editor 설정) | ✅ |
| **반경 N미터 액터 쿼리** | ❌ — TOctree2 사용 |
| **빈번한 동적 Spawn/Destroy** | ❌ — TOctree2 사용 |
| **작은 레벨 (200m 이하)** | ❌ — 오버킬 |

---

## 3. WorldPartition vs TOctree2 결합 표준

대규모 월드 = **두 시스템 페어 사용**:

```
WorldPartition Runtime Spatial Hash → 액터 메모리 로드/언로드 (cell 단위)
                                       ↓
TOctree2 (UWorldSubsystem)            → 로드된 액터 안 정밀 반경 쿼리
```

```cpp
// 의사 코드 — 두 시스템 협업
void AMyPlayer::Tick(float DT)
{
    // [1] WorldPartition = 자동 — 플레이어 위치 기반 cell 로드/언로드
    //    (StreamingSource 가 자동 등록됨)

    // [2] TOctree2 = 로드된 액터 안 반경 쿼리
    auto* Tracker = GetWorld()->GetSubsystem<UActorTrackerSubsystem>();
    if (Tracker)
    {
        Tracker->ForEachActorInRadius(GetActorLocation(), 2000.f, [](AActor* A) { /* ... */ });
    }
}
```

---

## 4. 함정

| # | 함정 | 정답 |
|---|------|------|
| 1 | 정밀 반경 쿼리 시 WorldPartition 사용 | TOctree2 페어 사용 |
| 2 | WorldPartition 비활성 World 에서 사용 | Map Settings 에서 활성 확인 |
| 3 | StreamingSource 등록 누락 | `UWorldPartitionStreamingSourceComponent` 추가 |
| 4 | Cell Size 너무 크게 → 메모리 폭발 | 보통 25600cm (256m) 시작, 적응 |
| 5 | HLOD Layer 미고려 | DefaultEngine.ini HLODLayer 설정 |

---

## 5. 관련

- [`../SKILL.md`](../SKILL.md)
- [`./TOctree2.md`](./TOctree2.md) — 정밀 반경 쿼리 (페어 사용)
- [`./StaticSpatialIndex.md`](./StaticSpatialIndex.md) — WorldPartition 내부 사용 R-Tree
- [`GameFramework/World.md`](../../GameFramework/references/World.md) — WorldPartition Streaming
