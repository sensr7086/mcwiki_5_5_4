---
name: spatial-tquadtree
description: TQuadTree<ElementType, NodeCapacity=4> — 2D 평면 한정 공간 분할 (탑다운/RTS/미니맵). GenericQuadTree.h. Insert/Remove/GetElements 표준 API + 함정. TOctree2 보다 메모리 효율 (2D 한정).
---

# SpatialPartition/TQuadTree — 2D 공간 분할

> **위치 (verified)**: `Engine/Public/GenericQuadTree.h:9-50`
> **요지**: 2D 평면 충분한 시나리오 (탑다운 / RTS / 미니맵 / AOE 스킬 2D) 의 공간 분할. `TOctree2` 보다 **메모리 1/4** (3축 → 2축).

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | 모든 콜백 첫 줄 스코프 |
| 🚨 [`10_ComponentPolicies §3`](../../../references/10_ComponentPolicies.md) | Element 안 `TWeakObjectPtr<AActor>` 의무 |
| 🚨 2D 한정 | Z 축 무시 — 높이 다른 액터도 동일 cell |

---

## 1. API [verified]

```cpp
// Engine/Public/GenericQuadTree.h:9-50
template <typename ElementType, int32 NodeCapacity = 4>
class TQuadTree
{
public:
    TQuadTree(const FBox2D& InBox, float InMinimumQuadSize = 100.f);

    void Insert(const ElementType& Element, const FBox2D& Box, const TCHAR* DebugContext = nullptr);

    template<typename ElementAllocatorType>
    void GetElements(const FBox2D& Box, TArray<ElementType, ElementAllocatorType>& ElementsOut) const;

    template<typename CallbackType>
    void GetElements(const FBox2D& Box, CallbackType&& Callback) const;

    bool Remove(const ElementType& Instance, const FBox2D& Box);
    void Empty();
};
```

---

## 2. AActor 트래커 (2D 버전)

```cpp
UCLASS()
class UActorTrackerQuadSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

    virtual void Initialize(FSubsystemCollectionBase& Coll) override
    {
        Super::Initialize(Coll);
        const FBox2D WorldBox(FVector2D(-100000.0, -100000.0), FVector2D(100000.0, 100000.0));   // 2km × 2km
        QuadTree.Reset(new TQuadTree<TWeakObjectPtr<AActor>>(WorldBox, /*MinQuadSize=*/ 200.f));
    }

    void RegisterActor(AActor* Actor)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UActorTrackerQuadSubsystem::RegisterActor);
        if (!IsValid(Actor) || !QuadTree) return;

        const FVector Loc = Actor->GetActorLocation();
        const FBox2D Box2D(FVector2D(Loc.X - 50.f, Loc.Y - 50.f),
                           FVector2D(Loc.X + 50.f, Loc.Y + 50.f));
        QuadTree->Insert(Actor, Box2D);
        ActorBoxMap.Add(Actor, Box2D);
    }

    void UnregisterActor(AActor* Actor)
    {
        if (FBox2D* Box = ActorBoxMap.Find(Actor))
        {
            QuadTree->Remove(Actor, *Box);
            ActorBoxMap.Remove(Actor);
        }
    }

    void GetActorsInRadius(const FVector2D& Center, float Radius, TArray<AActor*>& Out) const
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UActorTrackerQuadSubsystem::GetActorsInRadius);
        if (!QuadTree) return;

        const FBox2D Query(Center - FVector2D(Radius), Center + FVector2D(Radius));
        const float RadSq = Radius * Radius;

        QuadTree->GetElements(Query, [&Out, Center, RadSq](const TWeakObjectPtr<AActor>& Weak)
        {
            if (AActor* A = Weak.Get())
            {
                const FVector2D Loc2D(A->GetActorLocation().X, A->GetActorLocation().Y);
                if (FVector2D::DistSquared(Loc2D, Center) <= RadSq)
                {
                    Out.Add(A);
                }
            }
        });
    }

private:
    TUniquePtr<TQuadTree<TWeakObjectPtr<AActor>>> QuadTree;
    TMap<TWeakObjectPtr<AActor>, FBox2D> ActorBoxMap;
};
```

---

## 3. TOctree2 vs TQuadTree

| 항목 | TOctree2 | TQuadTree |
|------|----------|-----------|
| 차원 | 3D | 2D |
| 메모리 | 4x (3축) | 1x (2축) |
| 적합 게임 | FPS / 오픈월드 / 3D MOBA | 탑다운 / RTS / 2D / 미니맵 |
| API | `FBoxCenterAndExtent` | `FBox2D` |
| Semantics | 6 요소 의무 | 별도 X (NodeCapacity 만) |
| Element ID | `FOctreeElementId2` (O(1) 제거) | Box 보관 (O(log N) 제거) |

---

## 4. 함정

| # | 함정 | 정답 |
|---|------|------|
| 1 | 높이 차이 무시 — 위층 적이 1층 쿼리에 포함 | 결과 후 Z 거리 검사 |
| 2 | `Remove` 시 원본 `FBox2D` 보관 안 함 | Map 으로 Actor → Box 보관 |
| 3 | 매 Insert 시 새 Box2D 생성 비용 | 최소 cell size (`InMinimumQuadSize`) 충분히 크게 |
| 4 | 위치 변경 시 Remove + Insert 누락 | OnActorMoved 콜백 페어 |

---

## 5. 관련

- [`../SKILL.md`](../SKILL.md) — SpatialPartition 메인
- [`./TOctree2.md`](./TOctree2.md) — 3D 버전 (가장 일반)
- 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)
