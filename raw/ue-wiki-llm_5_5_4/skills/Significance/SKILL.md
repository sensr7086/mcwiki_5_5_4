---
name: significance-main
description: Significance Manager Plugin - USignificanceManager + FManagedObjectInfo + FOrderedBudget - 거리 기반 LOD/Tick 토글 + 다수 NPC 표준.
---

# Significance Module

> **모듈**: `Engine/Plugins/Runtime/SignificanceManager/Source/SignificanceManager/` (런타임 — 게임 빌드)
> **사이즈**: Public 2 헤더 (`SignificanceManager.h` · `OrderedBudget.h`)
> **카테고리**: `[Components]` 게임 시스템 — 거리 기반 LOD / Tick 토글 통합 매니저
>
> **🎯 어셋 최적화 5대 영역의 통합 진입점**: 🚨 [`12_AssetOptimizationPolicy.md §1-§5`](../../references/12_AssetOptimizationPolicy.md) — Significance 가 §1 Bone LOD (LOD 강제) + §4 Audio Culling (Sound 활성/비활성) + §5 Niagara Quality Scaling (`ENiagaraSignificanceHandling::EarliestActorBased` 통합) 의 진입점. **다수 NPC 환경 = Significance Manager 등록 + 콜백 안 5대 영역 동시 토글** 표준 패턴. 자세한 통합 매트릭스 = [`12_AssetOptimizationPolicy.md §6`](../../references/12_AssetOptimizationPolicy.md) (LOD 5단계 9개 항목).

---

## 1. 개요

UE의 **거리/카메라 기반 객체 중요도 평가 시스템**. 게임 시작 시 N개 액터/컴포넌트를 SignificanceManager에 등록 → 매 프레임 모든 ViewPoints 와 비교해 중요도(0~1) 계산 → 기준치에 따라:
- Tick 활성/비활성 토글
- LOD 강제
- AnimUpdateRate 조절
- Cosmetic 컴포넌트 (이펙트·사운드) 비활성

수십~수백 NPC가 있는 게임의 **표준 최적화 시스템**. 단일 캐릭터/주인공 게임에는 불필요.

---

## 2. 핵심 헤더

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `SignificanceManager.h` L32 | `USignificanceManager` (UCLASS) | 글로벌 매니저 (UObject) — `USubsystem` 패턴 |
| `SignificanceManager.h` (struct) | `FManagedObjectInfo` | 관리되는 객체 1개 정보 (Object + Tag + SignificanceFunction + PostFunction) |
| `SignificanceManager.h` enum | `EPostSignificanceType` | None / Concurrent / Sequential |
| `OrderedBudget.h` | `FOrderedBudget` | 거리 순 정렬된 N개에 LOD/Budget 분배 헬퍼 |

---

## 3. 사용 흐름 (Standard 패턴)

```
[Game 시작]
        │
        ▼
USignificanceManager::Get(World)        ← 글로벌 인스턴스 (UObject)
        │
        │ 객체 등록
        ▼
SigMgr->RegisterObject(MyNPC, FName("NPC"),
   /* SignificanceFunc */ [](FManagedObjectInfo* Info, const FTransform& VP) -> float
   {
       AActor* Actor = Cast<AActor>(Info->GetObject());
       return 1.0f - FMath::Clamp(FVector::Dist(Actor->GetActorLocation(), VP.GetLocation()) / 5000.0f, 0.0f, 1.0f);
       // 거리 0 → Significance 1.0, 거리 5000 → 0.0
   },
   EPostSignificanceType::Concurrent,
   /* PostFunc */ [](FManagedObjectInfo* Info, float OldSig, float NewSig, bool bFinal)
   {
       // 중요도 변경 후 처리 (Tick 토글 등)
       AActor* Actor = Cast<AActor>(Info->GetObject());
       if (NewSig < 0.1f) Actor->SetActorTickEnabled(false);
       else if (OldSig < 0.1f) Actor->SetActorTickEnabled(true);
   });
        │
        │ [매 프레임 — GameViewportClient::Tick 등에서]
        ▼
TArray<FTransform> Viewpoints;     // 카메라들 (보통 1개 — 플레이어)
Viewpoints.Add(PlayerCamera->GetComponentTransform());
SigMgr->Update(Viewpoints);
        │
        ▼
[모든 등록 객체에 대해 SignificanceFunction 호출]
        │
        │ EPostSignificanceType:
        │   Concurrent — 병렬 실행 가능
        │   Sequential — 순차 실행
        │   None       — Post 없음
        ▼
[중요도 변경된 객체에만 PostSignificanceFunction 호출]
        │
        │ 게임 종료
        ▼
SigMgr->UnregisterObject(MyNPC);
```

---

## 4. 핵심 API

### 4.1 등록 / 해제

| API | 라인 | 의미 |
|-----|------|------|
| `static USignificanceManager* Get(const UWorld*)` | (헤더) | 인스턴스 (World당 1개) |
| `template<class T> static T* Get(const UWorld*)` | | 캐스팅 헬퍼 |
| `virtual void RegisterObject(UObject*, FName Tag, FManagedObjectSignificanceFunction, EPostSignificanceType=None, FManagedObjectPostSignificanceFunction=nullptr)` | L123 | 객체 등록 |
| `virtual void UnregisterObject(UObject*)` | L126 | 해제 |
| `void UnregisterAll(FName Tag)` | (헤더) | 태그별 일괄 해제 |

### 4.2 매 프레임 갱신

| API | 의미 |
|-----|------|
| `virtual void Update(TArrayView<const FTransform> Viewpoints)` (L120) | 매 프레임 호출 — 모든 객체의 SignificanceFunction 호출 |
| `const TArray<FTransform>& GetViewpoints() const` | 현재 ViewPoints |

> **Update 호출 위치**: `UGameViewportClient::Tick` 또는 `APlayerController::PlayerTick` — 보통 게임당 1회 / 프레임.

### 4.3 조회

| API | 의미 |
|-----|------|
| `float GetSignificance(const UObject*) const` | 객체 중요도 (0~1) |
| `bool QuerySignificance(const UObject*, float& Out) const` | 등록 여부 + 값 |
| `FManagedObjectInfo* GetManagedObject(UObject*)` | 정보 |
| `const TArray<FManagedObjectInfo*>& GetManagedObjects(FName Tag)` | 태그별 |
| `void GetManagedObjects(TArray<FManagedObjectInfo*>& Out, bool bInSignificanceOrder=false) const` | 모든 / 정렬 |

### 4.4 EPostSignificanceType 3종

| 종류 | 의미 | 사용처 |
|------|------|--------|
| `None` | Post 함수 없음 — 단순 조회만 | LOD 직접 변경 (Tick에서 GetSignificance 호출) |
| `Concurrent` | 병렬 가능 | 가벼운 작업 (Tick 토글·매트리얼 파라미터) |
| `Sequential` | 순차만 | 무거운 작업 (서브시스템 호출·UI 갱신) |

---

## 5. SignificanceFunction 작성

### 5.1 기본 — 거리 기반

```cpp
auto DistanceSigFunc = [](FManagedObjectInfo* Info, const FTransform& VP) -> float
{
    if (UActorComponent* Comp = Cast<UActorComponent>(Info->GetObject()))
    {
        if (AActor* Actor = Comp->GetOwner())
        {
            const float Dist = FVector::Dist(Actor->GetActorLocation(), VP.GetLocation());
            return FMath::Clamp(1.0f - (Dist / 5000.0f), 0.0f, 1.0f);
        }
    }
    return 0.0f;
};
```

### 5.2 거리 + 시야각 (Cone)

```cpp
auto FrustumSigFunc = [](FManagedObjectInfo* Info, const FTransform& VP) -> float
{
    AActor* Actor = Cast<AActor>(Info->GetObject());
    const FVector ToActor = (Actor->GetActorLocation() - VP.GetLocation()).GetSafeNormal();
    const FVector Forward = VP.GetRotation().GetForwardVector();
    const float DotProduct = FVector::DotProduct(ToActor, Forward);

    // 시야 안 (Dot > 0.5) + 거리 fall-off
    const float Distance = FVector::Dist(Actor->GetActorLocation(), VP.GetLocation());
    const float DistFactor = 1.0f - FMath::Clamp(Distance / 5000.0f, 0.0f, 1.0f);

    return DistFactor * FMath::Max(0.0f, (DotProduct - 0.3f) / 0.7f);   // 0~1
};
```

### 5.3 다중 ViewPoints 처리

`Update(Viewpoints)` 가 여러 카메라를 받으면 **각 ViewPoint 별로 SigFunc 호출 후 최댓값** 자동 사용:

```cpp
// 멀티플레이어 — 4명 플레이어 카메라
TArray<FTransform> AllCameras;
for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
{
    if (APlayerController* PC = It->Get())
    {
        FVector Loc; FRotator Rot;
        PC->GetPlayerViewPoint(Loc, Rot);
        AllCameras.Add(FTransform(Rot, Loc));
    }
}
SigMgr->Update(AllCameras);
// 각 객체는 가장 가까운/시야 안 카메라 기준
```

---

## 6. PostSignificanceFunction (변경 처리)

```cpp
auto PostFunc = [](FManagedObjectInfo* Info, float OldSig, float NewSig, bool bFinal)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyGame_SigPostFunc);    // ← 람다 스코프 의무

    AMyNPC* NPC = Cast<AMyNPC>(Info->GetObject());
    if (!NPC) return;

    // 중요도 임계값에 따른 LOD 단계
    const int32 OldLOD = OldSig > 0.7f ? 0 : (OldSig > 0.3f ? 1 : (OldSig > 0.1f ? 2 : 3));
    const int32 NewLOD = NewSig > 0.7f ? 0 : (NewSig > 0.3f ? 1 : (NewSig > 0.1f ? 2 : 3));

    if (OldLOD != NewLOD)
    {
        // LOD 변경
        if (USkeletalMeshComponent* Mesh = NPC->GetMesh())
        {
            switch (NewLOD)
            {
            case 0:   // 가까이
                Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPose;
                Mesh->bEnableUpdateRateOptimizations = false;
                break;
            case 1:   // 중간
                Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickMontagesWhenNotRendered;
                Mesh->bEnableUpdateRateOptimizations = true;
                break;
            case 2:   // 멀리
                Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
                Mesh->bEnableUpdateRateOptimizations = true;
                break;
            case 3:   // 매우 멀리 — 정지
                NPC->SetActorTickEnabled(false);
                Mesh->bDisableClothSimulation = true;
                break;
            }
        }
    }
};
```

---

## 7. Budget 시스템 통합 — UE의 4가지 Budget 메커니즘

UE에서 "Budget" 이라는 단어는 **여러 시스템**에서 다르게 사용됨. 본 sub-skill은 그것들을 통합 정리.

### 7.0 4가지 Budget 시스템 비교

| 시스템 | 위치 | 단위 | 용도 |
|--------|------|------|------|
| **`FOrderedBudget`** | `SignificanceManager/OrderedBudget.h` | 거리 정렬된 N번째 → LOD 레벨 | LOD 분배 (Significance 통합) |
| **`AnimationBudgetAllocator`** | `Plugins/Runtime/AnimationBudgetAllocator/` | **시간 (ms)** 글로벌 예산 | SkeletalMesh URO 자동 분배 |
| **`FActorComponentTickFunction::TickInterval`** | `Engine/EngineTypes.h` | 초 단위 — Tick 빈도 제한 | 컴포넌트 단위 Tick 빈도 |
| **CVar 기반 Budget** (예: `r.Streaming.PoolSize`) | 각 시스템별 | 메모리·시간 | 시스템 단위 자원 한도 |

### 7.1 FOrderedBudget (`OrderedBudget.h`) — 거리 정렬 LOD 분배

거리 순 정렬된 N개 객체에 **LOD 단계 분배**. `BudgetSpec` 문자열 → 인덱스→레벨 룩업 테이블:

```cpp
FOrderedBudget Budget;
Budget.RecreateBudget(TEXT("0,2,3,5"));
// 의미:
//   Level 0 (가장 가까운 N개) → LOD 0
//   Level 1 (그 다음 2개) → LOD 1  → 인덱스 1~2
//   Level 2 (그 다음 3개) → LOD 2  → 인덱스 3~5
//   Level 3 (그 다음 5개) → LOD 3  → 인덱스 6~10
//   나머지 → ValueForOutOfBounds (기본 0)

// 사용
TArray<FManagedObjectInfo*> Sorted;
SigMgr->GetManagedObjects(Sorted, /*bInSignificanceOrder=*/true);
for (int32 i = 0; i < Sorted.Num(); i++)
{
    const int32 LODLevel = Budget.GetBudgetForIndex(i);
    // ApplyLOD(Sorted[i]->GetObject(), LODLevel);
}
```

→ "**가장 가까운 1명만 풀 디테일, 그 다음 2명은 LOD1, 그 다음 3명은 LOD2 ...**" 분배 패턴.

### 7.2 AnimationBudgetAllocator (Plugin — 글로벌 시간 예산)

**시간 기반 자동 Budget** — `BudgetInMs` (예: 1ms / 프레임) 안에서 모든 등록된 SkeletalMesh의 UpdateRate 자동 조정. NPC 수십~수백 명 환경에서 **프레임당 SkeletalMesh 비용 상한 보장**.

자세한 사용 — [`Components/MeshComponents §7.6`](../Components/references/MeshComponents.md):

```cpp
#include "IAnimationBudgetAllocatorModule.h"

if (IAnimationBudgetAllocator* Allocator = IAnimationBudgetAllocatorModule::Get().GetAllocator(World))
{
    Allocator->RegisterComponent(BudgetedMesh);
    // SetComponentSignificance 으로 매 프레임 중요도 갱신
    Allocator->SetComponentSignificance(BudgetedMesh, NewSig,
        /*bNeverSkip=*/(Mesh == PlayerMesh),     // 주인공만 NeverSkip
        /*bTickEvenIfNotRendered=*/false,
        /*bAllowReducedWork=*/true);
}
```

**Significance ↔ AnimationBudgetAllocator 통합**: Significance Manager의 PostFunc 안에서 `Allocator->SetComponentSignificance` 호출 — Significance가 "*어떤 NPC가 더 중요한가*", Allocator가 "*Budget 안에서 어떻게 분배*". 두 시스템이 직교적 — 함께 사용 권장.

### 7.3 FActorComponentTickFunction::TickInterval (컴포넌트 단위 Tick 빈도)

`UActorComponent::SetComponentTickInterval(float Seconds)` — 매 N초마다 1번만 Tick:

```cpp
// 매 0.5초마다 1번 (가벼운 폴링용)
MyComponent->SetComponentTickInterval(0.5f);

// 매 프레임 (기본)
MyComponent->SetComponentTickInterval(0.0f);
```

용도:
- AI 의사결정 (매 프레임 불필요)
- 통계 갱신
- 멀리 있는 NPC의 Tick 빈도 ↓ (Significance 보다 단순)

**Significance vs TickInterval**: Significance는 동적 거리 계산 + 다양한 컴포넌트 일괄 제어, TickInterval은 컴포넌트 1개의 정적 빈도 설정. 가벼운 NPC는 TickInterval로 충분.

### 7.4 CVar 기반 Budget — 자원 한도

| CVar | 의미 |
|------|------|
| `r.Streaming.PoolSize` | 텍스처 스트리밍 풀 (MB) |
| `Slate.NumThrottle` | Slate 스로틀 |
| `s.AsyncLoadingThreadEnabled` | 비동기 로딩 |
| `r.Shadow.MaxResolution` | 그림자 해상도 한도 |
| `a.Budget.Enabled` | AnimationBudgetAllocator 활성 |
| `physx.SimMaxRigidBodies` | 물리 강체 수 한도 |

자세한 — Render·Physics·Memory 카테고리 (별도 sub-skill, 향후).

### 7.5 통합 의사결정 트리

```
N개 컴포넌트의 Tick 비용 제어가 필요하다 →
│
├─ N < 30 ?
│   └─ TickInterval 또는 Significance 단순 사용
│
├─ N >= 30 + SkeletalMesh 위주 ?
│   └─ AnimationBudgetAllocator + Significance (조합)
│       (Significance가 중요도 계산 / Allocator가 Budget 분배)
│
└─ N >= 30 + 다양한 컴포넌트 ?
    └─ Significance + FOrderedBudget (LOD 분배) + TickInterval (보조)
```

---

## 8. 게임 통합 패턴

### 8.1 GameMode / GameInstance 등록

```cpp
void AMyGameMode::BeginPlay()
{
    Super::BeginPlay();
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyGameMode_BeginPlay);

    // 1. 모든 NPC 등록
    TArray<AActor*> NPCs;
    UGameplayStatics::GetAllActorsOfClass(GetWorld(), AMyNPC::StaticClass(), NPCs);

    USignificanceManager* SigMgr = USignificanceManager::Get(GetWorld());
    for (AActor* NPC : NPCs)
    {
        SigMgr->RegisterObject(NPC, FName("NPC"),
            DistanceSigFunc, EPostSignificanceType::Concurrent, PostFunc);
    }
}
```

### 8.2 매 프레임 Update — GameViewportClient 또는 PlayerController

```cpp
void AMy