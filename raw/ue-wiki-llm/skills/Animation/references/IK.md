---
name: animation-ik
description: UE 5.7.4 IK 시스템 통합 — Legacy AnimNode IK 8종 (FAnimNode_TwoBoneIK / Fabrik / LegIK / CCDIK / SplineIK / LookAt / HandIKRetargeting / ApplyLimits) + 5.x IK Rig Plugin (UIKRigDefinition + 7 Solvers FullBody/Limb/Pole/SetTransform/BodyMover/StretchLimb + FAnimNode_IKRig + UIKRigComponent) + 5.x IK Retargeter (UIKRetargeter + Retarget Ops 16종 + FAnimNode_RetargetPoseFromMesh) + Control Rig 비교. 결정 매트릭스 + 발 IK / 손 IK / 무기 IK / 캐릭터 모션 리타깃 표준.
---

# Animation/IK — Legacy IK + 5.x IK Rig + IK Retargeter

> **위치**:
> - **Legacy** (AnimGraphRuntime 모듈) — `Engine/Source/Runtime/AnimGraphRuntime/Public/BoneControllers/AnimNode_*IK.h`
> - **5.x IK Rig Plugin** — `Engine/Plugins/Animation/IKRig/Source/IKRig/Public/`
> - **5.x IK Retargeter Plugin** — 동일 (`Retargeter/IKRetargeter.h` + Solvers)
>
> **요지**: UE 5.7.4 IK 시스템은 **3축 + 1보조** — Legacy (AnimNode 8종, 단순) / **5.x IKRig** (선언적 Asset 기반, ⭐ 표준) / **5.x IKRetargeter** (Skeleton 간 모션 리타깃) / Control Rig (런타임 리깅 — 별도). 5.x 신규 게임은 **IK Rig 우선**.

---

## 🚨 공통 정책 (자동 적용)

| 정책 | IK 적용 |
|------|---------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | IK Solver `Update_AnyThread` / `Evaluate_AnyThread` 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| 🚨 워커 스레드 | 모든 IK AnimNode = `_AnyThread` — Owner / Component 직접 접근 X |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) §1 | 다수 NPC = LOD Threshold + URO 페어 (먼 NPC IK skip) |
| 🚨 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | UIKRig**Editor**Controller 등 = Editor 모듈 (4단 분리) |

---

## 1. 4 IK 시스템 결정 매트릭스 ⭐

```
사용자 작업 → 어느 IK 시스템?
├── 단순 한 노드 IK (손 잡기, 발 위치, 시선)
│   └── Legacy AnimNode IK (TwoBoneIK / Fabrik / LookAt / ApplyLimits)
│
├── 캐릭터 전체 (다중 IK 동시 — 발 + 손 + 시선)
│   └── 5.x IK Rig (Plugin) ⭐ 표준
│
├── 다른 Skeleton 의 모션 재사용 (예: Mannequin → Custom Char)
│   └── 5.x IK Retargeter (Plugin) ⭐
│
├── 런타임 리깅 / 본 변환 / Sequencer 통합
│   └── Control Rig (Plugin — 별도, [Plugin] 카테고리)
│
└── Tongue / 옷 / 머리카락 (단순 물리)
    └── AnimNode_AnimDynamics / AnimNode_SpringBone (별도)
```

| 시스템 | 위치 | 사용 시점 | 비용 |
|--------|------|----------|------|
| Legacy AnimNode IK | AnimGraph 노드 (단일) | 단순 IK, 마이그레이션 | 저 |
| **5.x IK Rig** ⭐ | Plugin Asset + AnimNode_IKRig | 캐릭터 다중 IK | 중 |
| **5.x IK Retargeter** | Plugin Asset + AnimNode_RetargetPoseFromMesh | Skeleton 간 모션 재사용 | 중 |
| Control Rig | Plugin (별도) | 런타임 리깅, 시네마틱 | 고 |

---

## 2. Legacy AnimNode IK 8종 (단순 케이스)

### 2.1 위치
`Engine/Source/Runtime/AnimGraphRuntime/Public/BoneControllers/AnimNode_*.h`

| AnimNode | 책임 | 일반 사용 |
|----------|------|----------|
| `AnimNode_TwoBoneIK` | 2 본 IK (어깨-팔꿈치-손) | 손 잡기 (무기 IK) |
| `AnimNode_Fabrik` | FABRIK (긴 체인) | 척추, 꼬리 |
| `AnimNode_LegIK` | 다리 IK (고급) | 발 IK (지면 적응) |
| `AnimNode_CCDIK` | CCD IK (반복) | 매우 긴 체인 |
| `AnimNode_HandIKRetargeting` | 손 IK 리타깃 | Skeleton 간 손 위치 |
| `AnimNode_SplineIK` | Spline 따라 본 배치 | 꼬리, 촉수 |
| `AnimNode_LookAt` | 본 시선 추적 | 머리/눈 추적 |
| `AnimNode_ApplyLimits` | 본 회전 제한 | Joint Limit |

### 2.2 FAnimNode_TwoBoneIK 표준 사용

```cpp
// AnimGraph 안 노드 (Editor)
//   Input Pose → [TwoBoneIK Node] → Output
//
// 핵심 파라미터:
// - IKBone (FBoneReference) — 끝 본 (예: hand_r)
// - EffectorLocation (FVector) — 목표 위치
// - JointTargetLocation (FVector) — 무릎 / 팔꿈치 방향
// - EffectorLocationSpace (EBoneControlSpace) — World / Component / Parent / Bone
// - StretchLimits (FFloatRange) — 늘어나는 한계
// - AllowStretching (bool)
```

### 2.3 BoneControlSpace 5종

| Space | 의미 | 사용 |
|-------|------|------|
| `BCS_WorldSpace` | World 좌표 | 절대 위치 |
| `BCS_ComponentSpace` | Mesh Component | 캐릭터 기준 |
| `BCS_ParentBoneSpace` | 부모 본 | 회전 중심 |
| `BCS_BoneSpace` | 본 자체 | 본 로컬 |

### 2.4 표준 발 IK 패턴 (Legacy)

```cpp
// AnimGraph 안:
// 1. Locomotion BlendSpace → Output
// 2. → LegIK (왼발, 오른발) — 지면 Trace 기반
// 3. → ApplyLimits (무릎 회전 제한)
// 4. → Final

// 게임 스레드 — Trace 결과 캐싱
void UMyAnimInstance::NativeUpdateAnimation(float DT)
{
    Super::NativeUpdateAnimation(DT);

    if (auto* C = CachedOwner.Get())
    {
        FootIK_L_Loc = TraceFoot(C, TEXT("foot_l"));
        FootIK_R_Loc = TraceFoot(C, TEXT("foot_r"));
    }
}

// 워커 스레드 — IK 적용
void UMyAnimInstance::NativeThreadSafeUpdateAnimation(float DT)
{
    Super::NativeThreadSafeUpdateAnimation(DT);
    // BlueprintReadOnly UPROPERTY = AnimGraph LegIK 노드가 읽음
    EffectorLocL = FootIK_L_Loc;
    EffectorLocR = FootIK_R_Loc;
}
```

---

## 3. 5.x IK Rig (Plugin) ⭐ 표준

### 3.1 핵심 6 클래스

```cpp
// Engine/Plugins/Animation/IKRig/Source/IKRig/Public/

// 1. UIKRigDefinition — Asset (본 계층 + 골 + Solver Stack)
class UIKRigDefinition : public UObject
{
    USkeletalMesh* PreviewMesh;
    TArray<FIKRigSkeleton> Skeleton;
    TArray<FIKRigGoal> Goals;             // 골 (목표 위치 / 회전)
    TArray<UIKRigSolver*> SolverStack;    // 7종 솔버 스택
};

// 2. UIKRigSolver (베이스) — 7종 자손
class UIKRigSolver : public UObject
{
    virtual void Initialize(...);
    virtual void Solve(FIKRigSkeleton& Skel, const FIKRigGoalContainer& Goals);
};

// 3. UIKRigProcessor — 런타임 처리기
class UIKRigProcessor : public UObject
{
    void Initialize(UIKRigDefinition* Rig, USkeleton* Skel);
    void Solve(FTransform RootTransform);
};

// 4. UIKRigComponent — Actor Component (게임에서 사용)
class UIKRigComponent : public UActorComponent
{
    UIKRigDefinition* RigDefinition;
};

// 5. FAnimNode_IKRig — AnimGraph 노드
struct FAnimNode_IKRig : public FAnimNode_Base
{
    UIKRigDefinition* RigDefinitionAsset;
    TArray<FIKRigGoal> Goals;
};

// 6. UIKRigController — Editor 컨트롤러 (Editor 모듈)
```

### 3.2 7 Solver 종류 (Stack 순서대로 적용)

| Solver | 위치 | 책임 |
|--------|------|------|
| `UIKRigFullBodyIK` (FBIK) ⭐ | `Solvers/IKRigFullBodyIK.h` | **전신 IK — 가장 강력** (다중 골 동시) |
| `UIKRigLimbSolver` | `Solvers/IKRigLimbSolver.h` | 사지 IK (다리/팔 — 무릎/팔꿈치 굽힘) |
| `UIKRigPoleSolver` | `Solvers/IKRigPoleSolver.h` | Pole 방향 제어 (무릎/팔꿈치 어디로?) |
| `UIKRigSetTransform` | `Solvers/IKRigSetTransform.h` | 직접 본 변환 설정 (덮어쓰기) |
| `UIKRigBodyMoverSolver` | `Solvers/IKRigBodyMoverSolver.h` | 몸통 / Pelvis 이동 (베이스) |
| `UIKRigStretchLimb` | `Solvers/IKRigStretchLimb.h` | 사지 늘리기 (도달 거리 ↑) |
| `UIKRigSolverBase` | `Solvers/IKRigSolverBase.h` | (베이스 — Custom Solver 작성용) |

### 3.3 표준 사용 흐름 (5단계)

```
1. UIKRigDefinition 자산 작성 (Editor)
   - PreviewMesh 지정 (USkeletalMesh)
   - 본 계층 구성 (자동 — Skeleton 에서)
   - Goals 추가 (예: "hand_r_goal", "foot_l_goal")
   - Solver Stack 구성 (예: BodyMover → FBIK)

2. UIKRigController 로 골 / 솔버 편집 (Editor)

3. AnimBP 안 FAnimNode_IKRig 노드 추가
   - RigDefinitionAsset 지정
   - Goals 의 EffectorLocation/Rotation 외부에서 받음

4. 게임 스레드 (NativeUpdateAnimation):
   - 골 위치 / 회전 캐싱

5. 워커 스레드 (NativeThreadSafeUpdate / AnimGraph):
   - BlueprintReadOnly UPROPERTY 가 IKRig 노드의 Goal 입력으로 연결
```

### 3.4 표준 패턴 — 무기 IK + 발 IK 동시 (FBIK)

```cpp
// 1. UIKRigDefinition: "Char_FBIK"
//    Goals:
//      - "hand_r_goal" (오른손 — 무기 잡기)
//      - "hand_l_goal" (왼손 — 무기 보조)
//      - "foot_l_goal" (왼발)
//      - "foot_r_goal" (오른발)
//    Solver Stack:
//      - UIKRigBodyMoverSolver (Pelvis 이동)
//      - UIKRigFullBodyIK (4 골 동시 풀이)

// 2. AnimBP — AnimGraph
//    Input → [FAnimNode_IKRig (Char_FBIK)] → Output

// 3. UMyAnimInstance.h
UPROPERTY(BlueprintReadOnly, Category="IK")
FVector HandRGoalLoc;

UPROPERTY(BlueprintReadOnly, Category="IK")
FVector FootLGoalLoc;

UPROPERTY(BlueprintReadOnly, Category="IK")
FVector FootRGoalLoc;

// 4. NativeUpdate — 게임 스레드 캐싱
void UMyAnimInstance::NativeUpdateAnimation(float DT)
{
    Super::NativeUpdateAnimation(DT);
    TRACE_CPUPROFILER_EVENT_SCOPE(NativeUpdate);

    if (auto* C = CachedOwner.Get())
    {
        // 무기 잡기
        if (auto* Weapon = C->GetWeaponActor())
        {
            CachedHandRGoal = Weapon->GetGripLocation();
        }

        // 발 IK — 지면 Trace
        CachedFootLGoal = TraceFoot(C, TEXT("foot_l"));
        CachedFootRGoal = TraceFoot(C, TEXT("foot_r"));
    }
}

// 5. NativeThreadSafe — 워커 스레드 (AnimGraph 가 읽음)
void UMyAnimInstance::NativeThreadSafeUpdateAnimation(float DT)
{
    Super::NativeThreadSafeUpdateAnimation(DT);
    HandRGoalLoc = CachedHandRGoal;
    FootLGoalLoc = CachedFootLGoal;
    FootRGoalLoc = CachedFootRGoal;
}
```

### 3.5 UIKRigComponent (Actor Component — 직접 사용)

> **AnimGraph 통합 X** — Actor 가 직접 IKRig 처리 (드물지만 가능).

```cpp
// 캐릭터에 컴포넌트 추가
UPROPERTY(VisibleAnywhere)
TObjectPtr<UIKRigComponent> IKRigComp;

// Constructor
IKRigComp = CreateDefaultSubobject<UIKRigComponent>(TEXT("IKRig"));
```

> **일반적으론 FAnimNode_IKRig (AnimGraph) 사용 — 위 패턴 권장**.

---

## 4. 5.x IK Retargeter (Plugin) ⭐

### 4.1 정의

**다른 Skeleton 의 애니메이션을 우리 Skeleton 으로 변환** — Mannequin 모션을 Custom Char 에 적용. 5.x 표준 (Animation Retargeting Manager 후속).

### 4.2 핵심 4 클래스

```cpp
// 1. UIKRetargeter — Asset (Source ↔ Target 매핑)
class UIKRetargeter : public UObject
{
    UIKRigDefinition* SourceIKRig;   // 원본 (예: Mannequin)
    UIKRigDefinition* TargetIKRig;   // 타깃 (예: Custom Char)
    TArray<FIKRetargetChainMapping> ChainMappings;
    TArray<URetargetOpBase*> RetargetOps;  // 16종 Op
};

// 2. UIKRetargetProcessor — 런타임 처리기
class UIKRetargetProcessor
{
    void Initialize(UIKRetargeter* Asset);
    void RunRetargeter(...);
};

// 3. FAnimNode_RetargetPoseFromMesh — AnimGraph 노드
struct FAnimNode_RetargetPoseFromMesh : public FAnimNode_Base
{
    UIKRetargeter* IKRetargeterAsset;
    USkeletalMeshComponent* SourceMeshComponent;  // 원본 메시
};

// 4. FIKRetargetChainMapping — 본 체인 매핑
```

### 4.3 16 Retarget Ops

```
RetargetOps/RunIKRigOp.h            ⭐ — IKRig 적용 (가장 흔함)
RetargetOps/IKChainsOp.h            — IK 체인 처리
RetargetOps/FKChainsOp.h            — FK 체인 처리
RetargetOps/PelvisMotionOp.h        — Pelvis 이동
RetargetOps/RootMotionGeneratorOp.h — RootMotion 생성
RetargetOps/CopyBasePoseOp.h        — Base Pose 복사
RetargetOps/CurveRemapOp.h          — Curve 매핑
RetargetOps/PinBoneOp.h             — 본 고정
RetargetOps/FilterBoneOp.h          — 본 필터
RetargetOps/AlignPoleVectorOp.h     — Pole 정렬
RetargetOps/FloorConstraintOp.h     — 바닥 제약
RetargetOps/StretchChainOp.h        — 체인 스트레치
RetargetOps/ScaleSourceOp.h         — Source 스케일
RetargetOps/StrideWarpingOp.h       — 보폭 와핑
RetargetOps/SpeedPlantingOp.h       — 발 고정 (Speed Planting)
RetargetOps/RetargetPoseOp.h        — Retarget Pose
```

### 4.4 표준 사용 흐름

```
1. Source IKRig 작성 (예: SK_Mannequin_IKRig)
2. Target IKRig 작성 (예: SK_MyChar_IKRig)
3. UIKRetargeter 자산 작성:
   - Source/Target IKRig 지정
   - ChainMappings 자동 매칭 (또는 수동)
   - RetargetOps 추가 (보통 RunIKRigOp 1개로 충분)

4. AnimBP — FAnimNode_RetargetPoseFromMesh 노드:
   - SourceMeshComponent: Mannequin SkelMesh (런타임 임시)
   - IKRetargeterAsset 지정
   - Output Pose → Final
```

### 4.5 표준 패턴 — Mannequin 모션 사용 (Custom Char)

```cpp
// AMyChar 안 Source Mesh + IK Retarget

UPROPERTY(VisibleAnywhere)
TObjectPtr<USkeletalMeshComponent> SourceMesh;  // Hidden, Mannequin 메시

void AMyChar::BeginPlay()
{
    Super::BeginPlay();

    // Source Mesh — Hidden, Mannequin AnimBP 만 평가
    SourceMesh->SetVisibility(false);
    SourceMesh->SetAnimInstanceClass(MannequinAnimBP);

    // 우리 Mesh = Custom Char + Retarget AnimBP (FAnimNode_RetargetPoseFromMesh 가 SourceMesh 참조)
}
```

---

## 5. AnimGraph 통합 — IK 노드 흐름

```
AnimGraph:
  Input Pose
    ↓
  [Locomotion BlendSpace]
    ↓
  [FAnimNode_RetargetPoseFromMesh]   ← IK Retargeter (Mannequin → Custom)
    ↓
  [FAnimNode_IKRig (Char_FBIK)]      ← 발 / 손 / 시선 IK 동시
    ↓
  [LegIK / TwoBoneIK ApplyLimits]    ← (Legacy) 추가 보정
    ↓
  Output Pose
```

---

## 6. 성능 고려 (다수 NPC + IK)

### 6.1 LOD Threshold

```cpp
// AnimGraph IK 노드 = LOD Threshold 설정
// LOD 0 = 모든 IK / LOD 2+ = IK skip

// FAnimNode_IKRig 안:
LODThreshold = 2;  // LOD 0,1 만 IK 적용
```

### 6.2 다수 NPC IK skip 매트릭스

| 환경 | IK 적용 | 사유 |
|------|---------|------|
| 1~10 캐릭터 | 모든 IK 활성 | 60fps 충분 |
| 10~50 NPC | LOD 0,1 만 IK | 멀리 NPC IK skip |
| 50~100 NPC | LOD 0 만 IK | 가장 가까운 NPC만 |
| 100+ NPC | IK 비활성 (BudgetAllocator) | 비용 너무 큼 |

### 6.3 Bone LOD + IK 페어

```cpp
// USkeletalMeshLODSettings
// LOD 0 — 모든 본 (IK 가능)
// LOD 2 — 30% 본 제거 (IK 본 누락 = 작동 X) → IK skip 의무
// LOD 4 — 15% 본 (skin only)
```

---

## 7. 함정 & 안티패턴 (12대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 다중 IK (발 + 손 + 시선) — 각자 별도 AnimNode | **5.x IK Rig** 으로 통합 (FBIK) |
| 2 | Skeleton 다른 모션 = 직접 사용 (본 어긋남) | **5.x IK Retargeter** (UIKRetargeter) 사용 |
| 3 | EffectorLocation 게임 스레드 객체 직접 접근 (워커 스레드 안) | NativeUpdate 캐싱 → NativeThreadSafe / AnimGraph |
| 4 | LOD 멀리도 IK 활성 (성능 낭비) | LODThreshold 설정 (의무) |
| 5 | Legacy CCDIK 매우 긴 체인 — 비용 큼 | FABRIK 또는 IK Rig FBIK |
| 6 | TwoBoneIK 의 JointTarget 누락 (무릎 방향 무작위) | JointTargetLocation 의무 |
| 7 | LegIK 발 Trace 결과 stale (1프레임 지연) | 매 프레임 NativeUpdate Trace |
| 8 | 100+ NPC IK 활성 | IK skip + BudgetAllocator |
| 9 | 5.x 신규 게임 — Legacy AnimNode IK 만 사용 | IK Rig 우선 (확장성 ↑) |
| 10 | UIKRigDefinition Editor 모듈 의존 누락 | Build.cs `IKRig` + `IKRigDeveloper` 의존 |
| 11 | IK Retargeter — Source Mesh 가시성 활성 (이중 렌더) | `SetVisibility(false)` |
| 12 | Custom Solver 작성 시 워커 스레드 안전성 누락 | UIKRigSolverBase + ThreadSafe 보장 |

---

## 8. 체크리스트

- [ ] IK 시스템 결정 (Legacy / IK Rig / IK Retargeter / Control Rig)
- [ ] 5.x 신규 게임 = IK Rig 우선
- [ ] Skeleton 간 모션 재사용 = IK Retargeter
- [ ] AnimGraph IK 노드 = LODThreshold 설정 의무
- [ ] EffectorLocation = NativeUpdate (캐싱) → NativeThreadSafe (전달)
- [ ] TwoBoneIK = JointTargetLocation 의무
- [ ] LegIK = NativeUpdate 안 매 프레임 Trace
- [ ] 다수 NPC = LOD Threshold + Bone LOD 페어 + BudgetAllocator
- [ ] IK Retargeter Source Mesh = `SetVisibility(false)`
- [ ] Build.cs = `IKRig` 의존 (Plugin)
- [ ] 첫 줄 프로파일링 스코프

---

## 9. 5.x 신규 / Deprecated

### 5.x 신규
- **`UIKRigDefinition`** ⭐ — Asset 기반 IK 시스템
- `UIKRigFullBodyIK` (FBIK) — 전신 IK Solver
- `FAnimNode_IKRig` — AnimGraph 노드
- `UIKRetargeter` ⭐ — Skeleton 간 리타깃 표준
- `FAnimNode_RetargetPoseFromMesh` — AnimGraph 노드
- 16 Retarget Ops (RunIKRigOp / IKChainsOp / SpeedPlantingOp / StrideWarpingOp 등)
- `UIKRigComponent` — Actor Component
- Control Rig (별도 시스템)

### Deprecated / 마이그레이션 권장
- Animation Retargeting Manager (4.x) → **5.x IK Retargeter**
- 단일 AnimNode IK 만 사용 → 5.x IK Rig 통합

---

## 10. 모듈 의존성 (Build.cs)

```csharp
// Plugin 의존 (Animation/IKRig)
PrivateDependencyModuleNames.AddRange(new[] {
    "Engine", "AnimGraphRuntime",
    "IKRig",                    // Runtime
    // Editor 작업 시
    // "IKRigEditor",
    // "IKRigDeveloper",
});

// .uplugin 안:
// "Plugins": [
//   { "Name": "IKRig", "Enabled": true }
// ]
```

---

## 11. 관련

- [`Animation/SKILL.md`](../SKILL.md) — 메인 (7 sub-skill)
- [`Animation/references/AnimGraph.md`](../AnimGraph/SKILL.md) — Custom AnimNode 작성 (Custom Solver 시)
- [`Animation/references/AnimInstance.md`](../AnimInstance/SKILL.md) — NativeUpdate / ThreadSafe 분리 (IK Goal 캐싱)
- [`Animation/references/Optimization.md`](../Optimization/SKILL.md) — LOD Threshold + 다수 NPC
- [`AssetClasses/references/Animation.md`](../../AssetClasses/references/Animation.md) — Skeleton (Compatible Skeleton)
- [`Components/references/MeshComponents.md`](../../Components/references/MeshComponents.md) §7 — SkeletalMeshComponent

## 12. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. **Legacy AnimNode IK 8종 + 5.x IK Rig 7 Solver + 5.x IK Retargeter 16 Ops + AnimGraph 통합 흐름 + 성능 매트릭스 + 함정 12대**. |
