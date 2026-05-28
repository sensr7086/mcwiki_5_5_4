---
name: animation
description: UE 5.7.4 Animation 카테고리 — 런타임 측 (AnimInstance / AnimGraph / AnimNotify / Sync / RootMotion / Optimization / IK / Ragdoll 8 sub-skill). UAnimInstance 라이프사이클 + FAnimInstanceProxy + FAnimNode_Base + UAnimNotify/UAnimNotifyState + FAnimSyncScope + FAnimNode_Inertialization (5.x) + FRootMotionSource + URO/Visibility/Sharing/Budget/Significance 5중 + 5.x IK Rig (UIKRigDefinition + 7 Solvers + FAnimNode_IKRig) + 5.x IK Retargeter (16 Ops) + Legacy AnimNode IK 8종 + Ragdoll (SetSimulatePhysics + UPhysicsAsset + UPhysicalAnimationComponent). AssetClasses/Animation 의 페어. [Animation] prefix.
---

# Animation — 런타임 (AnimInstance + AnimGraph + Notify + Sync + RootMotion + Optimization)

> **위치**: `Engine/Source/Runtime/Engine/Public/Animation/` (75+ 헤더) + `Engine/Source/Runtime/Engine/Classes/Animation/` (자산) + `Engine/Plugins/Runtime/AnimationBudgetAllocator/`
> **베이스**: `UAnimInstance` (1,776 lines) + `FAnimInstanceProxy` (worker 스레드) + `FAnimNode_Base` (AnimGraph 노드) + `UAnimNotify` / `UAnimNotifyState`
> **요지**: SkeletalMesh **런타임** 애니메이션 — 자산 (AssetClasses/Animation) 을 호스트 (Components/MeshComponents) 에 **연결·평가·동기화·최적화**. 매 프레임 다수 캐릭터 60fps 유지의 **핵심 책임**.

---

## 🚨 공통 정책 (자동 적용)

| 정책 | Animation 적용 |
|------|---------------|
| 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) | **NativeUpdateAnimation / NativeThreadSafeUpdateAnimation / FAnimNode_*::Update_AnyThread / Notify::Notify / NotifyBegin/End / Montage_* 콜백** = 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 🚨 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) | AnimInstance 멤버 = `UPROPERTY()` + `TObjectPtr<UAnimInstance>` (자동 GC). 워커 스레드 캐싱 = `TWeakObjectPtr` 또는 값 복사만 |
| 🎯 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) | AnimBP / Montage = **메모리 큼** (1MB~10MB). 자주 쓰면 **Match Start `PreloadPrimaryAssets`** 의무 |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../references/12_AssetOptimizationPolicy.md) §1 | **Bone LOD + URO + EVisibilityBasedAnimTickOption + AnimationBudgetAllocator + Significance** 5중 통합 |
| 🚨 [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) | `TObjectIterator<UAnimInstance>` 금지 → `TActorRange<ACharacter>` 도 금지 → **등록 패턴** (Significance / 자체 등록 매니저) |

---

## 1. sub-skill 인덱스 (8 + 메인)

| sub-skill | 책임 | 라인 | 핵심 |
|-----------|------|------|------|
| [`AnimInstance`](./AnimInstance/SKILL.md) ⭐ | UAnimInstance 라이프사이클 + Proxy + Curve + Montage_* | 1,776 | NativeUpdate/ThreadSafeUpdate 분리 / FAnimInstanceProxy / GetCurveValue |
| [`AnimGraph`](./AnimGraph/SKILL.md) | Custom AnimNode + StateMachine + Transition + Layer | 다수 | FAnimNode_Base / Initialize_AnyThread / Update_AnyThread / Evaluate_AnyThread / Layer Interface |
| [`AnimNotify`](./AnimNotify/SKILL.md) | UAnimNotify + NotifyState + Branch Point + Notify Queue | - | Notify (점) vs NotifyState (구간) / FAnimNotifyEvent / BranchingPoint |
| [`Sync`](./Sync/SKILL.md) | SyncGroup + Mirror + Inertialization (5.x) | - | FAnimSyncScope / MirrorSyncScope / FAnimNode_Inertialization (블렌드 0ms) |
| [`RootMotion`](./RootMotion/SKILL.md) | RootMotionSource + AnimRootMotionProvider (5.x) + CMC 통합 | - | FRootMotionSource_* 7종 / IAnimRootMotionProvider / bEnableRootMotionMontagesOnly |
| [`Optimization`](./Optimization/SKILL.md) ⭐⭐ | URO + Visibility Tick + AnimSharing + BudgetAllocator + Significance | - | EVisibilityBasedAnimTickOption 5종 / FAnimUpdateRateParameters / USkeletalMeshComponentBudgeted / FOrderedBudget |
| [`IK`](./IK/SKILL.md) ⭐ | Legacy AnimNode IK 8종 + 5.x IK Rig + 5.x IK Retargeter | - | UIKRigDefinition + 7 Solvers (FBIK/Limb/Pole/SetTransform/BodyMover/StretchLimb) + UIKRetargeter + 16 RetargetOps + FAnimNode_IKRig / RetargetPoseFromMesh |
| [`Ragdoll`](./Ragdoll/SKILL.md) ⭐ | Skeletal 물리 시뮬 + 죽음/히트 전환 | - | SetSimulatePhysics + SetAllBodiesBelowSimulatePhysics + SetPhysicsBlendWeight + BreakConstraint + UPhysicsAsset + UPhysicalAnimationComponent |

---

## 2. 시나리오 결정 트리

```
사용자 작업 → Animation 측면?
├── 캐릭터에 AnimBP 연결, NativeUpdate 작성              → AnimInstance
├── 새 AnimNode (Custom Skeletal 등) 작성                → AnimGraph
├── 발자국 / 콤보 윈도우 / 히트 박스 트리거               → AnimNotify
├── 다른 BP 와 같은 박자 (Sync Group)                    → Sync
├── 0ms 블렌드 (점프 → 착지 즉시)                        → Sync (Inertialization)
├── 어택 모션이 캐릭터 이동 (RootMotion)                 → RootMotion
├── 다수 NPC (50+ Char) 60fps 유지                       → Optimization ⭐⭐
├── 발 IK / 손 IK / 무기 IK / 시선 추적                  → IK ⭐ (5.x IK Rig 우선)
├── 다른 Skeleton 모션 재사용 (Mannequin → Custom)       → IK (5.x IK Retargeter)
├── 캐릭터 죽음 / 다운 / 폭발 반응                       → Ragdoll ⭐
├── 부분 Ragdoll (히트 반응만, 상체)                     → Ragdoll (SetAllBodiesBelowSimulatePhysics)
├── Animation + Physics 보강 (외력 반응)                → Ragdoll (UPhysicalAnimationComponent)
├── AnimSequence / AnimMontage / BlendSpace 자산        → AssetClasses/Animation (페어)
└── SkeletalMeshComponent 호스트                         → Components/MeshComponents (페어)
```

---

## 3. 페어 매트릭스 (자산 ↔ 런타임 ↔ 호스트)

| 작업 | 자산 (AssetClasses) | 런타임 (Animation) | 호스트 (Components) |
|------|---------------------|--------------------|--------------------|
| 캐릭터 애니 셋업 | UAnimBlueprint | AnimInstance/SKILL.md | MeshComponents §SkeletalMeshComponent |
| 어택 모션 + Section | UAnimMontage | AnimInstance §Montage_* | MeshComponents (Owner) |
| 본 IK / 발 IK / 무기 IK ⭐ | UIKRigDefinition (Plugin) | IK (5.x IK Rig) | MeshComponents |
| Skeleton 간 모션 재사용 ⭐ | UIKRetargeter (Plugin) | IK (5.x IK Retargeter) | MeshComponents |
| Custom AnimNode (Lean / Custom Pose) | - | AnimGraph (FAnimNode_*) | MeshComponents |
| 발자국 / 사운드 트리거 | UAnimSequence Notify | AnimNotify | AudioComponent |
| 0ms 점프-착지 블렌드 | UAnimSequence | Sync (Inertialization) | MeshComponents |
| 어택이 이동 (Roll) | UAnimMontage RootMotion | RootMotion | MovementComponents §5.12 |
| 50+ NPC 다수 환경 | LODSettings (Bone LOD) | Optimization ⭐ | MeshComponents §7 + Significance |

---

## 4. UAnimInstance 라이프사이클 (10단계)

```
1. UAnimBlueprint 컴파일 → UAnimInstance 자식 생성 (BPGC_*_C)
2. SkeletalMeshComponent::SetAnimInstanceClass(BPClass)
3. AnimInstance 생성 (NewObject) — Outer = SkelMeshComp
4. NativeInitializeAnimation()              — Owner 캐싱 등 1회
5. NativeBeginPlay()                         — Owner BeginPlay 후
6. (게임 스레드)  NativeUpdateAnimation(DT)  — 매 프레임 → 워커 데이터 캐싱
7. (워커 스레드)  NativeThreadSafeUpdateAnimation(DT)  — 매 프레임 (병렬) ⭐ 권장
8. (워커 스레드)  FAnimNode_*::Update_AnyThread → Evaluate_AnyThread
9. CompleteParallelAnimationEvaluation       — 게임 스레드 합쳐기
10. NativeUninitializeAnimation()            — 종료
```

> **핵심 분리**: 게임 스레드 (`NativeUpdate`) = Owner 접근 / 워커 (`NativeThreadSafeUpdate`) = 캐싱된 값 만 / AnimGraph 노드 (`Update_AnyThread`/`Evaluate_AnyThread`) = Read-only.

---

## 5. 표준 작업 패턴 (4단계)

### 5.1 캐릭터 + AnimInstance 표준

```cpp
// 1. AnimBP 클래스 어셋 — UAnimBlueprint::TargetSkeleton 호환
// 2. SkeletalMeshComponent 의 AnimClass 지정 (BP / Constructor)
USkeletalMeshComponent* SkelMesh = GetMesh();
SkelMesh->SetAnimInstanceClass(MyAnimBP);

// 3. UAnimInstance 자식 — 데이터 캐싱
UCLASS()
class UMyAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    virtual void NativeInitializeAnimation() override;
    virtual void NativeUpdateAnimation(float DT) override;
    virtual void NativeThreadSafeUpdateAnimation(float DT) override;

    UPROPERTY(BlueprintReadOnly, Category="Anim")
    float Speed;

    UPROPERTY(BlueprintReadOnly, Category="Anim")
    bool bIsCrouched;

private:
    TWeakObjectPtr<ACharacter> CachedOwner;
    float CachedSpeed = 0.f;
    bool bCachedCrouched = false;
};

// 4. NativeUpdate — 게임 스레드 데이터 캐싱
void UMyAnimInstance::NativeUpdateAnimation(float DT)
{
    Super::NativeUpdateAnimation(DT);
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyAnimInstance::NativeUpdate);
    if (auto* C = CachedOwner.Get())
    {
        CachedSpeed = C->GetVelocity().Size();
        bCachedCrouched = C->bIsCrouched;
    }
}

// 5. NativeThreadSafe — 워커 스레드 (병렬, 빠름)
void UMyAnimInstance::NativeThreadSafeUpdateAnimation(float DT)
{
    Super::NativeThreadSafeUpdateAnimation(DT);
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyAnimInstance::NativeThreadSafe);
    Speed = CachedSpeed;          // 캐싱된 값만 (Owner 접근 X)
    bIsCrouched = bCachedCrouched;
}
```

---

## 6. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | `NativeUpdateAnimation` 안 무거운 계산 | `NativeThreadSafeUpdateAnimation` 분리 (워커 병렬) |
| 2 | `NativeThreadSafeUpdateAnimation` 안 Owner / Component 직접 접근 | NativeUpdate 에 캐싱, 워커는 캐싱된 값만 |
| 3 | AnimMontage_Play 후 EndedDelegate 누락 | `Montage_SetEndDelegate` 의무 (완료 처리 필요 시) |
| 4 | RootMotion 활성 + CMC `bEnableRootMotionMontagesOnly = false` | CMC 측 `true` 설정 의무 |
| 5 | Notify 안 무거운 SpawnEmitter / SpawnSound | Pool / AutoRelease + `IsValid(MeshComp->GetOwner())` |
| 6 | 50+ NPC 다수 환경 — URO 비활성 | `bEnableUpdateRateOptimizations = true` + `EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered` |
| 7 | 50+ NPC — Significance 미사용 | USignificanceManager + 거리 기반 Tick Interval |
| 8 | 100+ NPC 환경 (군중) — 일반 SkelMeshComp | **USkeletalMeshComponentBudgeted** + `IAnimationBudgetAllocator` |
| 9 | Custom AnimNode `Update_AnyThread` 안 게임 스레드 객체 접근 | Read-only 캐싱 데이터만 (`bool bThreadSafe = true` 보장) |
| 10 | 🚨 `TObjectIterator<UAnimInstance>` (다수 NPC 일괄 처리) | Significance 등록 + 콜백 패턴 ([`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md)) |

---

## 7. 최적화 결정 매트릭스 (Optimization sub-skill 미리보기)

| 환경 | 표준 솔루션 | 비고 |
|------|------------|------|
| 1~10 캐릭터 (플레이어 중심) | URO + Visibility Tick | 기본 |
| 10~50 NPC | URO + Significance + Tick Interval | 거리 기반 |
| 50~100 NPC | + EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones X (= OnlyTickPoseWhenRendered) | 가장 약한 LOD |
| 100+ NPC (군중) ⭐ | **USkeletalMeshComponentBudgeted + IAnimationBudgetAllocator** | 자동 Budget 분배 |
| 군중 + 동일 모션 | + Anim Sharing (UAnimSharingInstance) | 1 AnimInstance 다수 공유 |

> **자세한 패턴**: [`Optimization/SKILL.md`](./Optimization/SKILL.md) + [`Components/MeshComponents §7`](../Components/references/MeshComponents.md) + [`Significance/SKILL.md`](../Significance/SKILL.md).

---

## 8. 5.x 신규 / Deprecated

### 5.x 신규
- `NativeThreadSafeUpdateAnimation` — 워커 스레드 (게임 스레드 부하 분산)
- `FAnimNode_Inertialization` — 0ms 블렌드 (전이)
- `IAnimRootMotionProvider` — RootMotion 인터페이스 추상
- `FAnimAttributes` — 노드 간 사용자 정의 속성 (Bone Mask 등)
- `IAnimationDataController` (Editor) — Raw 데이터 접근 표준
- `UAnimSharingInstance` — 다수 NPC 공유 AnimInstance

### Deprecated
- `SequenceLength` 직접 접근 → `GetPlayLength()`
- `RawAnimationData` 직접 접근 → `IAnimationDataController`
- `EMeshComponentUpdateFlag` (4.21~) → `EVisibilityBasedAnimTickOption`

---

## 9. 체크리스트 (모든 Animation 작업)

- [ ] AnimBP TargetSkeleton 호환 검사
- [ ] AnimInstance = NativeUpdate (캐싱) + NativeThreadSafe (계산) 분리
- [ ] 모든 Native* + FAnimNode_*::Update_AnyThread / Notify::Notify 첫 줄 프로파일링 스코프
- [ ] Montage_Play 시 EndedDelegate 바인딩 (완료 처리 시)
- [ ] RootMotion = Montage 측 + CMC 측 페어 활성
- [ ] AnimNotify Owner 검증 (`IsValid`) + Pool / AutoRelease
- [ ] 다수 NPC = URO + Significance + Tick Interval 의무
- [ ] 100+ NPC = USkeletalMeshComponentBudgeted (Budget Allocator)
- [ ] AnimBP / Montage 자주 쓰면 Match Start PreLoad
- [ ] 🚨 `TObjectIterator<UAnimInstance>` / `TActorIterator<ACharacter>` 금지

---

## 10. 관련 sub-skill / cross-link

- **자산 페어**: [`AssetClasses/references/Animation.md`](../AssetClasses/references/Animation.md) — UAnimSequence / UAnimMontage / UBlendSpace / UAnimBlueprint
- **호스트 페어**: [`Components/references/MeshComponents.md`](../Components/references/MeshComponents.md) §7 — SkeletalMeshComponent + URO 의 깊이
- **이동**: [`Components/references/MovementComponents.md`](../Components/references/MovementComponents.md) §5.12 — RootMotion + CMC
- **다수 NPC**: [`Significance/SKILL.md`](../Significance/SKILL.md) — 거리 기반 Tick / LOD 토글
- **캐릭터 베이스**: [`GameFramework/references/PawnCharacter.md`](../GameFramework/references/PawnCharacter.md) §6 — 최적화 10종

---

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. 카테고리 메인 + 6 sub-skill 인덱스 + 라이프사이클 10단계 + 페어 매트릭스 + 함정 10대 + 5.x 신규/Deprecated. |
