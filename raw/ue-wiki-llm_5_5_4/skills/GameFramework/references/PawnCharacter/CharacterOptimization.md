---
name: gameframework-pawncharacter-characteroptimization
description: ACharacter 최적화 10종 깊이 자료 — Tick 회피 / URO+EVisibilityBasedAnimTickOption / Significance / AnimationBudgetAllocator / Network / LOD / Capsule Channel / PostProcess + AI vs Player 9종 매트릭스 + 결정 트리.
---

# GameFramework / PawnCharacter — CharacterOptimization Reference

> 본 문서는 [`SKILL.md §6`](../SKILL.md) 의 깊이 자료. 메인 SKILL.md 는 §1~§5 (의존트리/라이프사이클/APawn/ACharacter/분기) + §7~§9 (함정/체크리스트/관련). 본 reference 는 매 프레임 다수 캐릭터 환경 최적화.
>
> **트리거**: 다수 NPC / AI 캐릭터 / 60fps 유지 / Significance / AnimationBudget / Network 최적화 작업 시 로드.

---

## 1. Tick 회피 (가장 큰 최적화)

> **🚨 핵심 — `ACharacter::Tick` 활성 X 권장**. UCharacterMovementComponent 가 모든 이동·물리·입력 처리. AnimBP 도 SkeletalMeshComponent 의 Tick 안에서.

```cpp
// MyCharacter Constructor
PrimaryActorTick.bCanEverTick = false;          // ⚠️ 권장 — Character 자체 Tick 안 함

// 만약 Tick 필요 시 (예: 카메라 흔들림 매 프레임 갱신) — 인터벌 사용
PrimaryActorTick.bCanEverTick = true;
PrimaryActorTick.TickInterval = 0.1f;            // 100ms
```

| Tick 위치 | 매 프레임 비용 | 회피 방법 |
|----------|------------|---------|
| `ACharacter::Tick` | 자체 비용 + 모든 콜백 누적 | **비활성** (CMC 가 처리) |
| `UCharacterMovementComponent::TickComponent` | 핵심 — 활성 필수 | TickInterval = 0 (매 프레임) — 단 Significance 시 조정 |
| `USkeletalMeshComponent::TickComponent` | Animation 갱신 — 가장 큰 비용 | URO + EVisibilityBasedAnimTickOption + PostProcess LOD |
| `CapsuleComponent::TickComponent` | Update Overlap — 활성 안 함 (자동) | OnComponentBeginOverlap 콜백만 비용 |

---

## 2. Animation Tick 최적화 (가장 큰 비용)

```cpp
// MyCharacter Constructor (또는 BeginPlay)
USkeletalMeshComponent* MeshComp = GetMesh();

// (1) URO (Update Rate Optimization) 활성 — 5.x 권장
MeshComp->bEnableUpdateRateOptimizations = true;
MeshComp->AnimUpdateRateParams->BaseNonRenderedUpdateRate = 4;   // 안 보일 때 4프레임마다
MeshComp->AnimUpdateRateParams->MaxEvalRateForInterpolation = 4;

// (2) Visibility 기반 Tick 옵션 — 가장 강력
MeshComp->VisibilityBasedAnimTickOption =
    EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;   // 안 보이면 Pose 안 함
    // 옵션 5종:
    // AlwaysTickPoseAndRefreshBones    — 항상 (가장 비쌈)
    // AlwaysTickPose                   — 항상 Pose, RefreshBones 필요시만
    // OnlyTickMontagesWhenNotRendered  — 안 보이면 Montage 만
    // OnlyTickPoseWhenRendered         — 안 보이면 Pose 도 X (가장 빠름)
    // AlwaysSkipPostProcess            — PostProcess AnimBP 만 OFF

// (3) bRecentlyRendered 검사 (수동)
if (MeshComp->bRecentlyRendered)
{
    // 비싼 작업
}
```

> **자세한 Animation Tick 최적화 매트릭스 = [`Components/MeshComponents §7`](../../../Components/references/MeshComponents.md)**.

---

## 3. Significance 통합 (다수 NPC 환경 표준)

```cpp
// MyAICharacter Constructor — Significance 등록
void AMyAICharacter::BeginPlay()
{
    Super::BeginPlay();

    if (auto* SigMgr = USignificanceManager::Get<USignificanceManager>(GetWorld()))
    {
        SigMgr->RegisterObject(this, TEXT("AICharacter"),
            [](USignificanceManager::FManagedObjectInfo* Info, const FTransform& Viewer)
            {
                FVector Loc = Cast<AActor>(Info->GetObject())->GetActorLocation();
                return FMath::InvSqrt(FVector::DistSquared(Loc, Viewer.GetLocation()));
            },
            USignificanceManager::EPostSignificanceType::Sequential,
            [](USignificanceManager::FManagedObjectInfo* Info, float OldSig, float NewSig, bool bFinal)
            {
                auto* Char = Cast<AMyAICharacter>(Info->GetObject());
                if (NewSig > 0.5f)        { Char->SetTickInterval(0.f); /* 매 프레임 */ }
                else if (NewSig > 0.1f)   { Char->SetTickInterval(0.1f); /* 100ms */ }
                else                       { Char->SetTickInterval(1.f);  /* 1s */ }
            });
    }
}

void AMyAICharacter::SetTickInterval(float Interval)
{
    SetActorTickInterval(Interval);
    GetCharacterMovement()->SetComponentTickInterval(Interval);
    GetMesh()->VisibilityBasedAnimTickOption = (Interval > 0.5f)
        ? EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered
        : EVisibilityBasedAnimTickOption::AlwaysTickPose;
}
```

> **자세한 Significance 패턴 = [`Significance/SKILL.md`](../../../Significance/SKILL.md)**.

---

## 4. AnimationBudgetAllocator (5.x Plugin — Significance 의 자동화)

```cpp
// 5.x 권장 — 다수 NPC 자동 Animation Budget 할당
USkeletalMeshComponentBudgeted* BudgetedMesh = GetMesh<USkeletalMeshComponentBudgeted>();
BudgetedMesh->SetComponentSignificance(NewSig);   // Significance 가 호출

// 글로벌 Budget 설정 (FAnimationBudgetAllocatorParameters)
// - MaxTickRate: 60Hz 기본
// - WorkUnitSmoothingNumFrames: 평활화 (기본 4)
// - TargetMs: 5ms 기본 — 모든 NPC Anim 합산 목표
// - MinComponentsToShouldAlwaysTick: 4
```

> **자세한 AnimationBudgetAllocator 패턴 = [`MeshComponents §7.6`](../../../Components/references/MeshComponents.md)**.

---

## 5. Network 최적화

```cpp
// Player Character — 매우 자주 (33Hz) + 항상 relevant
SetNetUpdateFrequency(33.f);
SetMinNetUpdateFrequency(2.f);
bAlwaysRelevant = true;
NetCullDistanceSquared = 0.f;        // 컬링 OFF

// AI / NPC — 적게 (5Hz) + 거리 컬링
SetNetUpdateFrequency(5.f);
SetMinNetUpdateFrequency(2.f);
bAlwaysRelevant = false;
NetCullDistanceSquared = 15000.f * 15000.f;   // 150m

// CharacterMovement Replication 모드
CharacterMovement->NetworkSmoothingMode = ENetworkSmoothingMode::Linear;   // 표준
CharacterMovement->bNetworkAlwaysReplicateTransformUpdateTimestamp = false;   // 대역폭 절약
CharacterMovement->NetworkMinTimeBetweenClientAdjustments = 0.1f;            // 보정 빈도 제한
```

---

## 6. Mesh LOD (Modular Character)

```cpp
// 메인 Mesh
GetMesh()->SetForcedLOD(0);   // 0 = 자동
GetMesh()->LODBias = 0;
GetMesh()->MinLodModel = 0;
GetMesh()->bOverrideMinLod = false;

// Modular Character (Body / Cape / Hair) LOD 동기화
auto* LODSync = CreateDefaultSubobject<ULODSyncComponent>(TEXT("LODSync"));
LODSync->ComponentsToSync = {
    {TEXT("Mesh"), ESyncOption::Drive},      // 메인 Body 가 LOD 결정
    {TEXT("Cape"), ESyncOption::Passive},
    {TEXT("Hair"), ESyncOption::Passive},
};
```

> **자세한 LODSync 패턴 = [`Components/SystemComponents §9`](../../../Components/references/SystemComponents.md)**.

---

## 7. Capsule Collision Channel (오버랩 비용)

```cpp
// 표준 Pawn 프로파일 — 다른 Pawn 과 Block + WorldStatic Block + Trigger 만 Overlap
GetCapsuleComponent()->SetCollisionProfileName(UCollisionProfile::Pawn_ProfileName);

// 더미 NPC (충돌 안 중요) — Overlap 없는 Channel
GetCapsuleComponent()->SetCollisionProfileName(TEXT("CharacterMesh"));   // Block only — Overlap 비용 0
```

> **자세한 Overlap 핫스팟 = [`08_OverlapHotspots.md`](../../../../references/08_OverlapHotspots.md)**.

---

## 8. PostProcess AnimBP — 분리 LOD

```cpp
// PostProcess AnimBP (IK / Foot Lock 등 — 매우 비쌈)
GetMesh()->SetPostProcessAnimBPLODThreshold(2);   // LOD 2 이하만 적용 (가까울 때만)

// 또는 OFF
GetMesh()->bDisablePostProcessBlueprint = true;
```

---

## 9. AI vs Player 분리 표준 매트릭스

| 항목 | Player | AI (Significance 1) | AI (Significance 0.5) | AI (Significance 0.1) |
|------|--------|---------------------|----------------------|----------------------|
| Tick Interval | 0 (매 프레임) | 0 (매 프레임) | 0.1s | 1s |
| AnimTickOption | AlwaysTickPoseAndRefreshBones | OnlyTickPoseWhenRendered | OnlyTickPoseWhenRendered | OnlyTickMontagesWhenNotRendered |
| URO | OFF | ON (BaseNonRenderedUpdateRate=4) | ON (=8) | ON (=15) |
| NetUpdateFrequency | 33 | 5 | 2 | 1 |
| NetCullDistance | 0 (없음) | 30000 cm² | 15000 cm² | 5000 cm² |
| PostProcess AnimBP | ON | LOD 2 이하만 | OFF | OFF |
| Mesh LOD | 자동 | 자동 | LOD 1 강제 | LOD 2 강제 |
| Capsule | Pawn (Block + Overlap) | Pawn | CharacterMesh (Block only) | CharacterMesh |
| CapsuleComponent Overlap 콜백 | 활성 | 활성 | 비활성 | 비활성 |

---

## 10. 표준 최적화 결정 트리

```
다수 캐릭터 환경?
├── No → Player Character 표준 (모든 활성)
└── Yes →
    ├── 캐릭터 수 < 10 → Significance 등록 (수동)
    ├── 캐릭터 수 10~50 → Significance + URO + AnimTickOption
    ├── 캐릭터 수 50~200 → AnimationBudgetAllocator Plugin 활성
    └── 캐릭터 수 > 200 → 위 + Pooling + InstancedSkeletalMesh 검토 + Mass Entity (5.x)
```

> **자세한 Budget 시스템 비교 = [`Significance/SKILL.md §7`](../../../Significance/SKILL.md)** (FOrderedBudget vs AnimationBudgetAllocator vs TickInterval vs CVar).

---

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-06 | PawnCharacter/SKILL.md §6 에서 분리. 메인 34KB → ~17KB / reference ~13KB. |
