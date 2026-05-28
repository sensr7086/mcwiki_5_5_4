---
name: animation-optimization
description: 다수 NPC Animation 최적화 5중 통합 — URO (FAnimUpdateRateParameters) + EVisibilityBasedAnimTickOption 5종 + AnimSharing (UAnimSharingInstance) + AnimationBudgetAllocator (USkeletalMeshComponentBudgeted + IAnimationBudgetAllocator + FAnimationBudgetAllocatorParameters) + Significance (USignificanceManager). 1~10/10~50/50~100/100+ NPC 결정 매트릭스 + Bone LOD 페어 + 60fps 보장.
---

# Animation/Optimization — URO + Visibility + AnimSharing + Budget Allocator + Significance

> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/SkinnedMeshComponent.h` (URO/Visibility 표준) + `Engine/Plugins/Runtime/AnimationBudgetAllocator/` (Plugin) + `Engine/Plugins/Runtime/SignificanceManager/`
> **요지**: 다수 캐릭터 (50~1000+) 에서 60fps 유지의 **핵심 책임**. 5중 통합 (URO / Visibility Tick / Sharing / Budget / Significance) — 환경에 맞춰 누적 적용.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) §1 | **Bone LOD + URO + Visibility + Significance** 4중 의무 (다수 NPC) |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | Significance 콜백 / Tick Function 첫 줄 프로파일링 스코프 |
| 🚨 [`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md) | `TActorIterator<ACharacter>` 금지 → Significance 등록 / BudgetAllocator 자동 등록 |

---

## 1. 5중 통합 매트릭스

| 영역 | 위치 | 적용 환경 |
|------|------|----------|
| **Bone LOD** | USkeletalMeshLODSettings + BonesToRemove 70/50/30/15% | 모든 SkeletalMesh (의무) |
| **URO** | `bEnableUpdateRateOptimizations = true` | 1~10 캐릭터 (기본) |
| **Visibility Tick** | `EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered` | 10~50 NPC |
| **Significance** | USignificanceManager + 거리 기반 Tick Interval | 50~100 NPC |
| **Anim Sharing** | UAnimSharingInstance | 동일 모션 다수 (군중) |
| **Budget Allocator** ⭐⭐ | USkeletalMeshComponentBudgeted + IAnimationBudgetAllocator | 100+ NPC (군중) |

---

## 2. URO (Update Rate Optimization)

### 2.1 활성

```cpp
// SkeletalMeshComponent
SkelMesh->bEnableUpdateRateOptimizations = true;
```

### 2.2 FAnimUpdateRateParameters

| 거리 | UpdateRate | 의미 |
|------|-----------|------|
| 가까움 (< 30m) | 1 (매 프레임) | 60fps |
| 중간 (30~60m) | 2 (격 프레임) | 30fps |
| 멀리 (> 60m) | 5 (5프레임마다) | 12fps |

> **자동 보간** — 사이 프레임은 이전 결과 보간.

### 2.3 LOD 페어

URO 와 LOD 가 자동 페어 — LOD 0 = UpdateRate 1, LOD 4 = UpdateRate 5+ (예).

---

## 3. EVisibilityBasedAnimTickOption (5종)

```cpp
// SkinnedMeshComponent.h:93
enum class EVisibilityBasedAnimTickOption : uint8
{
    AlwaysTickPoseAndRefreshBones,    // 항상 (가장 비용 큼) — 플레이어 캐릭터
    AlwaysTickPose,                    // Pose Tick / Bones Refresh 안 함
    OnlyTickMontagesWhenNotRendered,   // 보이지 않을 때 Montage 만 (RootMotion 보장)
    OnlyTickPoseWhenRendered,          // 보일 때만 ⭐ NPC 표준
    OnlyTickPoseWhenRenderedAndDilation // 보일 때 + Dilation 적용
};

SkelMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
```

### 3.1 결정 매트릭스

| 캐릭터 종류 | Option | 사유 |
|------------|--------|------|
| 플레이어 캐릭터 | AlwaysTickPoseAndRefreshBones | 항상 정확 |
| 중요 NPC (Boss / Quest) | AlwaysTickPose | RootMotion 정확 |
| 일반 NPC (50~) | **OnlyTickPoseWhenRendered** ⭐ | 보일 때만 |
| 군중 NPC (100~) | OnlyTickPoseWhenRendered + URO 5 | 보일 때 + 저주기 |

---

## 4. AnimSharing — 다수 NPC 1 AnimInstance 공유

### 4.1 정의

100+ 동일 모션 NPC (예: 좀비 군중) — 1 AnimInstance + N SkelMesh 공유. 메모리 / CPU 거대 절약.

### 4.2 사용

```cpp
// 1. UAnimSharingInstance 생성 (1회)
UAnimSharingInstance* SharingInst = ...

// 2. 각 NPC 의 SkelMesh 가 공유
SkelMesh->SetMasterPoseComponent(SharingMesh);
// 또는 Animation Sharing Plugin 활성 → 자동
```

### 4.3 함정

- **다른 모션 / 다른 시각 NPC 가 공유 X** → 동일 군중에만 사용

---

## 5. AnimationBudgetAllocator (100+ NPC ⭐⭐)

### 5.1 정의

**자동 Budget 분배 시스템** — 매 프레임 N ms 예산 안에서 NPC 들의 Anim Tick 분배. 거리 / 가시성 / 중요도 기반 자동.

### 5.2 USkeletalMeshComponentBudgeted

```cpp
// AnimationBudgetAllocator/Public/SkeletalMeshComponentBudgeted.h
UCLASS(MinimalAPI, meta=(BlueprintSpawnableComponent))
class USkeletalMeshComponentBudgeted : public USkeletalMeshComponent
{
    virtual void SetComponentTickEnabled(bool bEnabled) override;
    virtual void BeginPlay() override;       // 자동 등록
    virtual void EndPlay(const EEndPlayReason::Type) override;  // 자동 해제
    virtual void TickComponent(...) override;
    virtual void CompleteParallelAnimationEvaluation(bool bDoPostAnimEvaluation) override;
};
```

> **사용** = ACharacter 의 SkelMesh 컴포넌트를 `USkeletalMeshComponentBudgeted` 로 교체 → 자동 등록.

### 5.3 표준 사용 패턴

```cpp
// 1. Character Constructor
AMyAIChar::AMyAIChar(const FObjectInitializer& OI)
    : Super(OI.SetDefaultSubobjectClass<USkeletalMeshComponentBudgeted>(ACharacter::MeshComponentName))
{
    // 자동 — BeginPlay 시 IAnimationBudgetAllocator 에 등록
}

// 2. World 에서 IAnimationBudgetAllocator 가져오기 (Subsystem)
auto& BudgetAllocator = IAnimationBudgetAllocator::Get(GetWorld());

// 3. 파라미터 설정 (FAnimationBudgetAllocatorParameters)
FAnimationBudgetAllocatorParameters Params;
Params.BudgetInMs = 5.0f;                  // 5ms 예산 / 프레임
Params.MinQuality = 0.0f;                   // 최소 품질
Params.MaxTickRate = 10;                    // 최대 격 프레임
Params.WorkUnitSmoothingNumFrames = 4;
BudgetAllocator.SetParameters(Params);
```

### 5.4 Budget 분배 알고리즘 (개략)

```
1. 등록된 모든 USkeletalMeshComponentBudgeted 수집
2. 각 컴포넌트의 거리 / 가시성 / 마지막 Tick 시간 → Significance 계산
3. Budget (5ms) 안에서 우선순위 분배:
   - 가까움 / 보임 = 매 프레임
   - 멀리 / 안 보임 = 격 / N 프레임마다
4. 자동 Tick Rate 조정
```

---

## 6. Significance Manager 통합

> 자세한 = [`Significance/SKILL.md`](../../Significance/SKILL.md).

### 6.1 패턴

```cpp
void AMyAIChar::BeginPlay()
{
    Super::BeginPlay();

    if (auto* SigMgr = USignificanceManager::Get<USignificanceManager>(GetWorld()))
    {
        SigMgr->RegisterObject(this, TEXT("AIChar"),
            // Significance = 거리 기반
            [](FManagedObjectInfo* Info, const FTransform& Viewer) {
                FVector Loc = Cast<AActor>(Info->GetObject())->GetActorLocation();
                return FMath::InvSqrt(FVector::DistSquared(Loc, Viewer.GetLocation()));
            },
            EPostSignificanceType::Sequential,
            // 변화 시 — Tick Interval 조정
            [](FManagedObjectInfo* Info, float Old, float New, bool bFinal) {
                auto* C = Cast<AMyAIChar>(Info->GetObject());
                auto* SkelMesh = C->GetMesh();
                if (New > 0.5f)
                {
                    SkelMesh->SetComponentTickInterval(0.f);
                    SkelMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPose;
                }
                else if (New > 0.1f)
                {
                    SkelMesh->SetComponentTickInterval(0.1f);
                    SkelMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
                }
                else
                {
                    SkelMesh->SetComponentTickInterval(1.f);
                    SkelMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
                }
            });
    }
}
```

---

## 7. 환경별 결정 매트릭스 (누적 적용)

| 환경 | URO | Visibility Tick | Significance | AnimSharing | Budget Allocator |
|------|-----|----------------|--------------|------------|-----------------|
| 1~10 캐릭터 | ✅ | AlwaysTickPose | - | - | - |
| 10~50 NPC | ✅ | OnlyTickPoseWhenRendered | ✅ | - | - |
| 50~100 NPC | ✅ | OnlyTickPoseWhenRendered | ✅ | - | ⚠ 검토 |
| 100~500 NPC | ✅ | OnlyTickPoseWhenRendered | ✅ | ⚠ 동일 모션 시 | ✅ ⭐ |
| 500+ 군중 | ✅ | OnlyTickPoseWhenRendered | ✅ | ✅ ⭐ | ✅ ⭐ |

---

## 8. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 다수 NPC + URO 비활성 | `bEnableUpdateRateOptimizations = true` 의무 |
| 2 | NPC + AlwaysTickPoseAndRefreshBones | `OnlyTickPoseWhenRendered` |
| 3 | 100+ NPC + 일반 SkelMesh | `USkeletalMeshComponentBudgeted` |
| 4 | Significance 등록 누락 | 모든 NPC = Register 의무 |
| 5 | Significance 콜백 안 무거운 작업 | Tick Interval / Option 변경만 (가벼움) |
| 6 | AnimSharing 사용 — 다른 모션 NPC 도 공유 | 동일 모션만 |
| 7 | BudgetAllocator BudgetInMs 너무 작음 (대부분 NPC 안 보임) | 5~10ms 적정 |
| 8 | 🚨 `TActorIterator<ACharacter>` 일괄 처리 | Significance 등록 + 콜백 |
| 9 | LOD 미설정 — 멀어도 본 모두 평가 | LODSettings + BonesToRemove 의무 |
| 10 | Bone LOD 와 URO 페어 미스매치 | LOD 0 = URO 1, LOD 4 = URO 5+ 자동 |

---

## 9. 체크리스트

- [ ] 모든 SkeletalMesh = `bEnableUpdateRateOptimizations = true`
- [ ] NPC = `EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered`
- [ ] 50+ NPC = USignificanceManager 등록 의무
- [ ] 100+ NPC = USkeletalMeshComponentBudgeted (Plugin)
- [ ] 군중 동일 모션 = UAnimSharingInstance
- [ ] Bone LOD + URO 페어
- [ ] Significance 콜백 = 가벼운 작업만 (Tick Interval / Option)
- [ ] BudgetAllocator BudgetInMs = 5~10ms
- [ ] 🚨 TActorIterator 금지 — 등록 패턴 의무

---

## 10. 관련

- [`Animation/SKILL.md`](../SKILL.md) — 메인
- [`Components/references/MeshComponents.md`](../../Components/references/MeshComponents.md) §7 — SkeletalMesh URO 깊이
- [`Significance/SKILL.md`](../../Significance/SKILL.md) — USignificanceManager
- [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) §1 — Bone LOD 페어
- [`GameFramework/references/PawnCharacter.md`](../../GameFramework/references/PawnCharacter.md) §6 — 최적화 10종
- [`AssetClasses/references/Mesh.md`](../../AssetClasses/references/Mesh.md) — USkeletalMesh + LODSettings

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. 5중 통합 (URO / Visibility / Sharing / Budget / Significance) + USkeletalMeshComponentBudgeted + 환경별 결정 매트릭스 + 함정 10대. |
