---
name: spatial-partition
description: UE 5.5.4 공간 분할 카테고리 — 런타임 AActor 대규모 관리 + 반경 쿼리 (Octree / Quadtree / WorldPartition Runtime Spatial Hash / Static Spatial Index R-Tree). TOctree2 기반 AActor 트래커 표준 패턴 (가장 일반). 4 sub-skill 인덱스 + 결정 트리 + Semantics 작성 규약 + 함정. [SpatialPartition] prefix 호출.
---

# SpatialPartition — 런타임 AActor 공간 분할 통합 가이드

> **위치**: `Core/Public/Math/GenericOctree.h` (TOctree2 베이스) + `Engine/Public/GenericQuadTree.h` (TQuadTree) + `Engine/Public/WorldPartition/` (WorldPartition Runtime Spatial Hash + Static Spatial Index)
> **요지**: 다수 AActor 의 **공간 인덱싱** + **반경/박스 쿼리** + **거리 기반 LOD/Tick 토글**. 매 프레임 수백~수천 쿼리 가능. Engine 의 Renderer (FScenePrimitiveOctree) 가 검증된 동일 패턴.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) | Register / Unregister / Query 모든 함수 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| 🚨 [`10_ComponentPolicies.md §3 GC 방어`](../../references/10_ComponentPolicies.md) | Element 안 `AActor*` 직접 X — `TWeakObjectPtr<AActor>` + 콜백 안 `IsValid` 의무 |
| 🚨 [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) | `TActorIterator` 전체 순회 금지 — 공간 분할 인덱스 사용 |
| 🚨 Octree 정적 bounds | Element 위치 변경 = Remove + Add 페어 (Octree 는 mutable bounds 미지원) |
| 🚨 Lifetime | Subsystem 의무 등록/해제 + EndPlay 시 명시적 Unregister |

---

## 1. 4 sub-skill 인덱스

| sub-skill | 책임 | 핵심 클래스 | 추천도 |
|-----------|------|------------|--------|
| [`TOctree2`](./references/TOctree2.md) ⭐⭐⭐ | **AActor 트래커 (가장 일반)** — 3D 범용 Octree + Semantics + Subsystem 통합 | `TOctree2<T, Semantics>` / `FOctreeElementId2` / `FBoxCenterAndExtent` | 가장 권장 |
| [`TQuadTree`](./references/TQuadTree.md) | 2D Quadtree (탑다운/RTS 전용) | `TQuadTree<T, NodeCapacity=4>` | 2D 한정 |
| [`WorldPartitionRuntime`](./references/WorldPartitionRuntime.md) | 5.x 대규모 월드 스트리밍 (cell 단위) | `UWorldPartitionRuntimeSpatialHash` / `FSquare2DGridHelper` | 1km+ 월드 |
| [`StaticSpatialIndex`](./references/StaticSpatialIndex.md) | 정적 R-Tree (변경 X 시 가장 빠름) | `FStaticSpatialIndex::TRTreeImpl` / `TListImpl` | 정적 데이터 |

---

## 2. 시나리오 결정 트리

```
런타임 AActor 공간 쿼리?
├── 변경 빈번 (Spawn/Destroy/Move) + 반경 쿼리
│   ├── 3D 범용 (FPS / 오픈월드 일부 / 3D AOE)  → TOctree2 ⭐⭐⭐
│   └── 2D 평면 충분 (탑다운 / RTS / 미니맵)     → TQuadTree
│
├── 정적 (BeginPlay 후 변경 X)                  → StaticSpatialIndex (R-Tree)
│
├── 대규모 월드 액터 스트리밍 (1km+)            → WorldPartition Runtime Spatial Hash
│
├── 거리 기반 LOD/Tick 토글 (NPC 100+)         → USignificanceManager ([`Significance/SKILL.md`](../Significance/SKILL.md))
│
└── 단발 Overlap/Sweep (이미 충돌 활성)         → UWorld::OverlapMultiByChannel (TOctree 보다 비쌈)
```

---

## 3. 핵심 시나리오 매핑

| 시나리오 | sub-skill | 비고 |
|----------|-----------|------|
| **다수 NPC 매 프레임 "내 주변 N미터 적" 조회** ⭐ | `TOctree2` | 가장 흔한 케이스 — AOE 스킬 / AI Sight |
| **Influence Map** (1km+ 그리드 가치 계산) | `WorldPartitionRuntime` 또는 `TQuadTree` | 셀 사이즈에 따라 |
| **Static 아이템 픽업** (변경 X) | `StaticSpatialIndex` | 한 번 빌드 후 query 만 |
| **Tower Defense** 적 경로 안 타워 검색 | `TQuadTree` | 2D 충분 |
| **NPC LOD 거리 토글** | `USignificanceManager` | 공간 분할 X — 단순 거리 priority |
| **물리 Overlap** (Capsule/Sphere 충돌) | `UWorld::OverlapMulti*` | Physics Collision 의존 |

---

## 4. 작성 표준 패턴 (TOctree2 베이스)

대부분 시나리오 = `TOctree2` 표준 패턴 4단계:

```
[1] Element struct 정의      — TWeakObjectPtr<AActor> + Bounds + FOctreeElementId2
[2] Semantics 정의           — GetBoundingBox / AreElementsEqual / SetElementId / ApplyOffset
[3] UWorldSubsystem 안 등록  — RegisterActor / UnregisterActor / UpdateActor (이동 시)
[4] Query API 제공           — GetActorsNearby(Center, Radius, Out) — O(log N + K)
```

자세한 코드 = [`references/TOctree2.md`](./references/TOctree2.md) §4.

---

## 5. 성능 기대치 (Engine 검증)

| 작업 | 복잡도 | 비고 |
|------|-------|------|
| `AddElement` | O(log N) | 수만 액터 OK |
| `RemoveElement(Id)` | O(1) | `FOctreeElementId2` 보관 시 |
| `FindElementsWithBoundsTest(Box, Func)` | O(log N + K) | K = 결과 액터 수 |
| 메모리 (element 당) | ~80 bytes | TWeakObjectPtr + Bounds + Id |

**Engine 검증 사례** ([`PrimitiveSceneInfo.h:259`](../../Renderer-source) — `FScenePrimitiveOctree`, UE 5.5):
- 수만 Primitive 매 프레임 frustum culling
- Renderer 의 전 Scene Visibility 시스템 베이스

---

## 6. Build.cs 의존성

```csharp
// MyGameModule.Build.cs
PrivateDependencyModuleNames.AddRange(new[] {
    "Core", "CoreUObject", "Engine"
    // TOctree2 / TQuadTree = Core/Engine 포함 — 추가 의존 X
});
```

> WorldPartition 사용 시: `"Engine"` 만 + WorldPartition 헤더 include.

---

## 7. 함정 & 안티패턴 (5종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | Element 에 `AActor*` 직접 보관 | `TWeakObjectPtr<AActor>` + `.Get()` IsValid 검사 ([`10_ComponentPolicies §3`](../../references/10_ComponentPolicies.md)) |
| 2 | 위치 변경 시 Octree 갱신 누락 | `OnActorMoved` 시 Remove + Add 페어 (Octree 는 immutable bounds) |
| 3 | `FOctreeElementId2` 미보관 → 제거 시 O(N) traverse | `SetElementId` Semantics override 의무 |
| 4 | World Extent 너무 작음 → 액터 outside | 충분히 크게 (10~100km) 초기화 |
| 5 | 매 Tick `RegisterActor` 중복 호출 | BeginPlay/EndPlay 페어 + `TMap` 중복 검사 |

---

## 8. 관련 카테고리 cross-link

- ⭐ [`Significance/SKILL.md`](../Significance/SKILL.md) — 거리 기반 LOD/Tick 토글 (공간 분할 + LOD 결합 시)
- [`Components/SKILL.md`](../Components/SKILL.md) §SystemComponents — Subsystem 안 등록 패턴
- [`GameFramework/Actor.md`](../GameFramework/references/Actor.md) — BeginPlay/EndPlay 시 등록/해제
- [`AI/SKILL.md`](../AI/SKILL.md) — Perception System (Sight) 와 공간 쿼리 통합
- 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — 콜백 첫 줄 스코프
- 🚨 [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) — TActorIterator 금지 → 공간 분할 표준
- 🚨 [`10_ComponentPolicies.md §3 GC 방어`](../../references/10_ComponentPolicies.md) — TWeakObjectPtr 의무

---

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-12 | 카테고리 신설. 4 sub-skill (TOctree2 ⭐⭐⭐ / TQuadTree / WorldPartitionRuntime / StaticSpatialIndex) + 결정 트리 + 시나리오 매핑 6종 + 함정 5대. **TOctree2 ActorTracker deep** (Renderer 의 FScenePrimitiveOctree 동일 패턴 모사). |
