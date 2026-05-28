---
type: source
title: "UE SpatialPartition — Main SKILL (20번째 카테고리)"
slug: ue-spatialpartition-skill
source_path: raw/ue-wiki-llm/skills/SpatialPartition/SKILL.md
source_kind: text
source_date: 2026-05-12
ingested: 2026-05-13
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Global-Iterator-Avoidance]]"
tags: [ue, spatial-partition, octree, quadtree, worldpartition, slim-card, category-main]
citation_disclosure: "🟢 12 / 🟡 0 / 🔴 0 · 보너스 발견 0건 (raw 정밀 카테고리 main hub)"
---

# UE SpatialPartition — Main SKILL (20번째 카테고리)

> Source: [[raw/ue-wiki-llm/skills/SpatialPartition/SKILL.md]] (140L)
> 위치: `Core/Public/Math/GenericOctree.h` + `Engine/Public/GenericQuadTree.h` + `Engine/Public/WorldPartition/`
> 4 sub-skill 인덱스 + 결정 트리 + Semantics 작성 규약 + 함정 5대.

## 1. Summary

🟢 UE 5.x 의 **런타임 AActor 공간 인덱싱** 카테고리 — 반경/박스 쿼리 + 거리 기반 LOD/Tick 토글. Renderer 의 `FScenePrimitiveOctree` (`PrimitiveSceneInfo.h:239`) 가 검증된 동일 패턴. 4 sub-skill: TOctree2 (⭐⭐⭐ 가장 일반) / TQuadTree (2D 한정) / WorldPartitionRuntime (1km+) / StaticSpatialIndex (정적 R-Tree).

## 2. Key claims

- 🟢 **4 sub-skill 인덱스** (raw L25-32):
  - [[sources/ue-spatialpartition-toctree2]] ⭐⭐⭐ — `TOctree2<T, Semantics>` 3D 범용 (변경 빈번 + 반경 쿼리)
  - [[sources/ue-spatialpartition-tquadtree]] — `TQuadTree<T, NodeCapacity=4>` 2D (탑다운/RTS)
  - [[sources/ue-spatialpartition-worldpartitionruntime]] — `UWorldPartitionRuntimeSpatialHash` 5.x (대규모 월드)
  - [[sources/ue-spatialpartition-staticspatialindex]] — `FStaticSpatialIndex::TRTreeImpl` (정적 + 가장 빠름)
- 🟢 **시나리오 결정 트리** (raw L39-50) — 변경 빈번 3D → TOctree2 / 변경 빈번 2D → TQuadTree / 정적 → StaticSpatialIndex / 1km+ 월드 → WorldPartitionRuntime / 거리 LOD → [[sources/ue-significance-skill]] (공간 분할 X)
- 🟢 **TOctree2 4단 표준 패턴** (raw L72-77): (1) Element struct 정의 + `TWeakObjectPtr<AActor>` + Bounds + `FOctreeElementId2` → (2) Semantics 정의 (6 요소: MaxElementsPerLeaf / MinInclusiveElementsPerNode / MaxNodeDepth / GetBoundingBox / AreElementsEqual / SetElementId + ApplyOffset LWC 5.x) → (3) UWorldSubsystem 등록/해제/Update → (4) Query API (GetActorsNearby) O(log N + K)
- 🟢 **성능 매트릭스** (raw L85-90) — AddElement O(log N), RemoveElement O(1) (FOctreeElementId2 보관 시), FindElementsWithBoundsTest O(log N + K), 메모리 ~80 bytes/element. 수만 액터 OK.
- 🟢 **Engine 검증 사례** (raw L92-94) — `FScenePrimitiveOctree` 가 Renderer 의 frustum culling 베이스. 본 패턴은 *Engine 자체 사용* 검증.

## 3. 🚨 공통 정책 (5건 — raw §🚨)

| 정책 | 적용 |
|------|------|
| 🟢 [[concepts/Profiling-Scope-Rule]] | Register / Unregister / Query 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| 🟢 [[concepts/Component-Policies-6]] §3 GC 방어 | Element 안 `AActor*` 직접 X — `TWeakObjectPtr<AActor>` + `IsValid` 의무 |
| 🟢 [[concepts/Global-Iterator-Avoidance]] | `TActorIterator` 전체 순회 금지 → 공간 분할 인덱스 사용 |
| 🟢 Octree 정적 bounds | Element 위치 변경 = Remove + Add 페어 (Octree 는 mutable bounds 미지원) |
| 🟢 Lifetime | Subsystem 의무 등록/해제 + EndPlay 시 명시적 Unregister |

## 4. 함정 (raw L114-120 — 5대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Element 에 `AActor*` 직접 보관 | `TWeakObjectPtr<AActor>` + `.Get()` IsValid 검사 |
| 2 | 위치 변경 시 Octree 갱신 누락 | `OnActorMoved` 시 Remove + Add 페어 (immutable bounds) |
| 3 | `FOctreeElementId2` 미보관 → 제거 O(N) | `SetElementId` Semantics override 의무 |
| 4 | World Extent 너무 작음 → 액터 outside | 충분히 크게 (10~100km) 초기화 |
| 5 | 매 Tick `RegisterActor` 중복 호출 | BeginPlay/EndPlay 페어 + `TMap` 중복 검사 |

## 5. Cross-link

- ⭐ Sub-skills: [[sources/ue-spatialpartition-toctree2]] · [[sources/ue-spatialpartition-tquadtree]] · [[sources/ue-spatialpartition-worldpartitionruntime]] · [[sources/ue-spatialpartition-staticspatialindex]]
- Agent: [[sources/ue-agent-spatial-partition]] (14번째 agent — plugin 미등록, raw 만)
- 연관: [[sources/ue-significance-skill]] (거리 LOD/Tick 토글) · [[sources/ue-components-skill]] (Subsystem 안 등록 패턴) · [[sources/ue-gameframework-actor]] (BeginPlay/EndPlay 페어) · [[sources/ue-ai-skill]] (Perception Sight 통합)
- 정책: 🚨 [[sources/ue-ref-07-profilingscopeRule]] · 🚨 [[sources/ue-ref-09-globaliteratorpolicy]] · 🚨 [[sources/ue-ref-10-componentpolicies]] §3

## 6. Build.cs 의존

```csharp
// MyGameModule.Build.cs
PrivateDependencyModuleNames.AddRange(new[] {
    "Core", "CoreUObject", "Engine"   // TOctree2 / TQuadTree = Core/Engine 포함
});
```

WorldPartition 사용 시 `"Engine"` + WorldPartition 헤더 include.
