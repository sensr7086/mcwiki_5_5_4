---
name: animation-animgraph
description: AnimGraph 노드 (FAnimNode_Base 자손) Initialize_AnyThread / Update_AnyThread / Evaluate_AnyThread / GatherDebugData 4단계 + StateMachine + Transition + Layer Interface (5.x). Custom AnimNode 작성 표준 + 워커 스레드 안전성 + AnimGraph 컴파일 의존.
---

# Animation/AnimGraph — Custom AnimNode + StateMachine + Layer (5.x)

> **위치**: `Engine/Source/Runtime/AnimGraphRuntime/` + `Engine/Source/Runtime/Engine/Public/Animation/AnimNode_*.h`
> **베이스**: `FAnimNode_Base` (struct — Editor: `UAnimGraphNode_*` 페어로 노드화)
> **요지**: AnimGraph 노드 = **워커 스레드 (`AnyThread`)** 에서 실행 → 게임 스레드 객체 직접 접근 X. 4단계 lifecycle + AnimGraph 컴파일 → AnimInstance 의 워커 평가에 자동 연결.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | `Initialize_AnyThread` / `Update_AnyThread` / `Evaluate_AnyThread` 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 🚨 워커 스레드 | Owner / Component / World 직접 접근 X — Proxy 또는 캐싱된 값만 |
| 🚨 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | `UAnimGraphNode_*` 클래스 = Editor 모듈 (4단 분리) |

---

## 1. FAnimNode_Base — 4단계 라이프사이클

```cpp
// Engine/Public/Animation/AnimNodeBase.h
struct FAnimNode_Base
{
    // 1. Initialize_AnyThread — 1회 (그래프 활성화)
    virtual void Initialize_AnyThread(const FAnimationInitializeContext& Context);

    // 2. CacheBones_AnyThread — Bone Container 변경 시
    virtual void CacheBones_AnyThread(const FAnimationCacheBonesContext& Context);

    // 3. Update_AnyThread — 매 프레임 (시간 흐름 / 누적)
    virtual void Update_AnyThread(const FAnimationUpdateContext& Context);

    // 4. Evaluate_AnyThread — 매 프레임 (Pose 출력)
    virtual void Evaluate_AnyThread(FPoseContext& Output);

    // Debug — Editor / 시각화
    virtual void GatherDebugData(FNodeDebugData& DebugData);
};
```

| 단계 | 호출 시점 | 책임 |
|------|----------|------|
| `Initialize_AnyThread` | 그래프 활성화 시 (1회) | 멤버 초기화, 캐싱 |
| `CacheBones_AnyThread` | Bone Container (LOD) 변경 | Bone Index 캐싱 (FBoneReference::Initialize) |
| `Update_AnyThread` | 매 프레임 (시간 흐름) | 누적 시간, Sync, 자식 노드 Update 호출 |
| `Evaluate_AnyThread` | 매 프레임 (Pose 평가) | 자식의 Pose 받아 변환, FPoseContext 출력 |

> **Update_AnyThread + Evaluate_AnyThread 분리** — Update 는 시간 진행 / Evaluate 는 실제 본 변환. 그래프 가지치기 (Pose 가 사용 안 되면 Evaluate skip 가능).

---

## 2. Custom AnimNode 표준 패턴

### 2.1 FAnimNode_* (Runtime — 워커 스레드)

```cpp
// MyAnimNode_Lean.h (Runtime 모듈)
USTRUCT(BlueprintInternalUseOnly)
struct FAnimNode_Lean : public FAnimNode_Base
{
    GENERATED_BODY()

    // 입력 Pose (그래프 와이어)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Links")
    FPoseLink BasePose;

    // Lean Angle (외부 — AnimInstance 변수에서 받음)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lean", meta=(PinShownByDefault))
    float LeanAngle = 0.f;

    // 적용할 본
    UPROPERTY(EditAnywhere, Category="Bone")
    FBoneReference SpineBone;

    // 라이프사이클
    virtual void Initialize_AnyThread(const FAnimationInitializeContext& Ctx) override;
    virtual void CacheBones_AnyThread(const FAnimationCacheBonesContext& Ctx) override;
    virtual void Update_AnyThread(const FAnimationUpdateContext& Ctx) override;
    virtual void Evaluate_AnyThread(FPoseContext& Output) override;
};

// MyAnimNode_Lean.cpp
void FAnimNode_Lean::Initialize_AnyThread(const FAnimationInitializeContext& Ctx)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(FAnimNode_Lean::Initialize);
    FAnimNode_Base::Initialize_AnyThread(Ctx);
    BasePose.Initialize(Ctx);
}

void FAnimNode_Lean::CacheBones_AnyThread(const FAnimationCacheBonesContext& Ctx)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(FAnimNode_Lean::CacheBones);
    FAnimNode_Base::CacheBones_AnyThread(Ctx);
    BasePose.CacheBones(Ctx);
    SpineBone.Initialize(Ctx.AnimInstanceProxy->GetRequiredBones());  // BoneIndex 캐싱
}

void FAnimNode_Lean::Update_AnyThread(const FAnimationUpdateContext& Ctx)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(FAnimNode_Lean::Update);
    FAnimNode_Base::Update_AnyThread(Ctx);
    BasePose.Update(Ctx);   // 자식 Update
}

void FAnimNode_Lean::Evaluate_AnyThread(FPoseContext& Output)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(FAnimNode_Lean::Evaluate);
    BasePose.Evaluate(Output);  // 베이스 Pose 가져오기

    if (SpineBone.IsValidToEvaluate(Output.AnimInstanceProxy->GetRequiredBones()))
    {
        const FCompactPoseBoneIndex BoneIdx = SpineBone.GetCompactPoseIndex(Output.AnimInstanceProxy->GetRequiredBones());
        FTransform BoneTM = Output.Pose[BoneIdx];

        // Lean 회전 적용
        FQuat LeanQuat(FVector::ForwardVector, FMath::DegreesToRadians(LeanAngle));
        BoneTM.SetRotation(BoneTM.GetRotation() * LeanQuat);

        Output.Pose[BoneIdx] = BoneTM;
    }
}
```

### 2.2 UAnimGraphNode_* (Editor — 노드 시각화) 🛠

```cpp
// MyAnimGraphNode_Lean.h (Editor 모듈 — 4단 분리 의무)
#if WITH_EDITOR
UCLASS(MinimalAPI)
class UAnimGraphNode_Lean : public UAnimGraphNode_Base
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, Category="Settings")
    FAnimNode_Lean Node;

    // Editor 메타
    virtual FText GetNodeTitle(ENodeTitleType::Type Type) const override
    {
        return NSLOCTEXT("AnimGraph", "Lean", "Lean Spine");
    }

    virtual FText GetTooltipText() const override { return NSLOCTEXT("AnimGraph", "Lean_Tip", "Apply lean rotation to spine bone."); }
    virtual FString GetNodeCategory() const override { return TEXT("Custom"); }

    virtual const FAnimNode_Base* GetAnimNode() const override { return &Node; }
};
#endif
```

> 🛠 **에디터 전용** — Build.cs `bBuildDeveloperTools=true` + `AnimGraph` / `BlueprintGraph` 의존 + 별도 Editor 모듈.

---

## 3. StateMachine (UAnimStateMachineGraph)

### 3.1 구성
- **State** = AnimGraph (BlendSpacePlayer / SequencePlayer / Custom AnimNode)
- **Transition** = State ↔ State 전환 규칙 (Bool 변수 / Curve / 시간)
- **Conduit** = 다중 분기 (1 → 다중 State)

### 3.2 Transition Rule 패턴

```cpp
// AnimBP — Transition Rule 그래프 (Bool 출력)
// 워커 스레드 — bThreadSafe = true (안전 변수만)

bool TransitionRule_IdleToWalk()
{
    // BlueprintReadOnly UPROPERTY 만 접근 (워커 스레드)
    return Speed > 10.f && !bIsFalling;
}
```

### 3.3 5.x 신규 — Inertialization (0ms 블렌드)

> 자세한 = [`Sync/SKILL.md`](../Sync/SKILL.md) §3 Inertialization

State 전환 시 일반 Blend 대신 **FAnimNode_Inertialization** 사용 → 첫 프레임에 모든 본의 가속도 / 속도 캐싱 → 자연스러운 0ms 블렌드.

---

## 4. Animation Layer Interface (5.x)

### 4.1 정의 — 다른 AnimBP 의 Layer 공유

```cpp
// 1. Animation Layer Interface (Asset) 작성 — Editor 에서
// 예: WeaponLayerInterface (UpperBody Slot 정의)

// 2. Base AnimBP 가 Interface 구현
// 3. Weapon AnimBP 가 Interface 구현 (다른 모션)
// 4. 런타임 — Layer 동적 교체
```

### 4.2 LinkAnimClassLayers / UnlinkAnimClassLayers

```cpp
// SkeletalMeshComponent 에 Layer 연결
SkelMeshComp->LinkAnimClassLayers(WeaponAnimBPClass);

// 다른 Layer 로 교체
SkelMeshComp->UnlinkAnimClassLayers(WeaponAnimBPClass);
SkelMeshComp->LinkAnimClassLayers(SwordAnimBPClass);
```

---

## 5. Sync Group (음악 박자)

> 다중 BlendSpace / Sequence 가 같은 박자로 재생 — 동기화. 자세한 = [`Sync/SKILL.md`](../Sync/SKILL.md).

```cpp
// AnimBP 안 BlendSpace 노드 → SyncGroupName = "Locomotion"
// → Walk / Run / Sprint 모두 같은 박자 (발 위치 동기화)
```

---

## 6. AnimAttributes (5.x — 노드 간 사용자 정의 속성)

```cpp
// FAnimAttributes — 노드 간 임의 속성 전달 (Bone Mask 등)
// AnimAttributes.h:6 — TAttribute<T>

// 사용 예 — IK Trace 결과를 다른 노드로 전달
void FAnimNode_FootIK::Evaluate_AnyThread(FPoseContext& Output)
{
    // Foot 위치 계산
    FVector FootTrace = ComputeFootTrace();

    // 노드 간 전달 (Custom Attribute)
    Output.CustomAttributes.AddAttribute<FVectorAttribute>(TEXT("FootTrace_L"), FootTrace);
}
```

---

## 7. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | `Update_AnyThread` 안 Owner / Component 직접 접근 | Proxy 의 캐싱 데이터 만 |
| 2 | `Evaluate_AnyThread` 안 무거운 계산 (매 프레임) | Update 에서 캐싱 → Evaluate 는 적용만 |
| 3 | `CacheBones_AnyThread` 누락 (LOD 변경 시 본 인덱스 stale) | 의무 — `FBoneReference::Initialize` |
| 4 | `Initialize_AnyThread` 안 자식 Pose Initialize 누락 | 모든 `FPoseLink::Initialize(Ctx)` 호출 |
| 5 | UAnimGraphNode_* 가 Runtime 모듈 | Editor 모듈 (4단 분리) |
| 6 | Transition Rule 그래프 안 게임 스레드 객체 접근 | bThreadSafe = true 보장 → 안전 변수만 |
| 7 | StateMachine 일반 Blend (느림) | 5.x Inertialization (0ms) |
| 8 | Layer 미사용 — 무기 마다 다른 AnimBP 클래스 | Animation Layer Interface (1 베이스 + N Layer) |
| 9 | 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 10 | Sync 안 함 — 다중 BlendSpace 박자 어긋남 | SyncGroupName 지정 |

---

## 8. 체크리스트

- [ ] FAnimNode_* 4단계 (Initialize / CacheBones / Update / Evaluate) Super 호출
- [ ] 모든 _AnyThread 첫 줄 프로파일링 스코프
- [ ] 자식 FPoseLink::Initialize / CacheBones / Update / Evaluate 의무
- [ ] Bone 인덱스 캐싱 (CacheBones_AnyThread)
- [ ] Update vs Evaluate 분리 (시간 vs 적용)
- [ ] UAnimGraphNode_* = Editor 모듈 (4단 분리)
- [ ] Transition Rule = bThreadSafe (안전 변수만)
- [ ] Layer Interface 활용 (다중 BP 공유)
- [ ] StateMachine 전이 = Inertialization (5.x)
- [ ] 워커 스레드 — Owner / Component 직접 접근 X

---

## 9. 관련

- [`Animation/SKILL.md`](../SKILL.md) — 메인
- [`Animation/references/AnimInstance.md`](../AnimInstance/SKILL.md) — Proxy + NativeUpdate (워커 데이터 캐싱)
- [`Animation/references/Sync.md`](../Sync/SKILL.md) — Sync Group + Inertialization
- [`Editor/references/UnrealEd.md`](../../Editor/references/UnrealEd.md) — UAnimGraphNode_* 4단 분리

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. 4단계 라이프사이클 + Custom AnimNode 패턴 + StateMachine + Layer Interface + AnimAttributes + 함정 10대. |
