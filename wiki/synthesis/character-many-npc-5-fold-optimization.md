---
type: synthesis
title: "다수 NPC (50+) 환경의 5중 최적화 누적 매트릭스 — URO + Visibility + Significance + AnimSharing + Budget"
slug: character-many-npc-5-fold-optimization
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-animation-optimization]]"
  - "[[sources/ue-significance-skill]]"
  - "[[sources/ue-gameframework-characteroptimization]]"
  - "[[sources/ue-components-meshcomponents]]"
  - "[[sources/ue-ref-12-assetoptimizationpolicy]]"
  - "[[sources/ue-animation-skill]]"
  - "[[sources/ue-ai-skill]]"
entities:
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/USignificanceManager]]"
  - "[[entities/UAnimInstance]]"
  - "[[entities/ACharacter]]"
  - "[[entities/AAIController]]"
concepts:
  - "[[concepts/URO]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Bone-LOD]]"
  - "[[concepts/Tick-Group]]"
status: living
tags: [synthesis, npc, optimization, animation, performance]
---

# 다수 NPC (50+) 환경의 5중 최적화 누적 매트릭스

## 1. Thesis

50명 이상 NPC 가 동시에 보이는 환경 (RTS / 호드모드 / MMO 인스턴스) 에서 SkeletalMesh 캐릭터 비용은 *Pose 평가 (CPU) + Skinning (GPU) + AnimGraph (CPU) + Tick (CPU) + Update Rate (CPU)* 의 5축. 한 축만 끄면 다른 축이 폭발 — **누적 적용** 이 표준. 5 중 = **(1) URO 거리 기반 Tick 분할 + (2) EVisibilityBasedAnimTickOption 화면 밖 컷 + (3) Significance 우선순위 budget + (4) AnimSharing 동일 본 트리 공유 + (5) AnimationBudgetAllocator 프레임 budget**. [[sources/ue-ref-12-assetoptimizationpolicy]] §6 의 통합 매트릭스를 *결정 트리 + 누적 적용 순서* 로 재정리.

## 2. 5 축 매트릭스

| # | 최적화 | 무엇을 끄는가 | 트리거 | 비용 절감 (대략) |
| -- | -- | -- | -- | -- |
| 1 | **URO** ([[concepts/URO]]) | AnimGraph Tick 주기 — 매 프레임 → 2/4/8/16 frame skip | 거리 / Significance | Pose 평가 50~93% 감소 |
| 2 | **Visibility** ([[concepts/EVisibilityBasedAnimTickOption]]) | Pose Tick 자체 / RefreshBoneTransforms | 화면 밖 (`!bRecentlyRendered`) | Tick 거의 0 (Skinning 도 자동 skip) |
| 3 | **Significance** ([[entities/USignificanceManager]]) | 기능 자체 (Tick / AnimGraph / Niagara / Audio) | USignificanceManager 의 Tag 별 Significance score | 각 컴포넌트가 자체 결정 |
| 4 | **AnimSharing** Plugin | 같은 본 트리 / 같은 Animation 의 NPC 들이 한 *Master Pose* 공유 | 보통 같은 Skeleton + 같은 AnimSequence 군집 | Pose 평가가 N → 1 |
| 5 | **AnimationBudgetAllocator** Plugin | 프레임당 Tick 가능한 SkeletalMesh 수 제한 | budget 안 우선순위 큰 N개만 Tick | 가장 강력 (overflow 자동 차단) |

각 옵션의 자세한 셋업 — [[sources/ue-animation-optimization]] §3 (URO) / §5 (Visibility) / §7 (AnimSharing) / §9 (Budget) + [[sources/ue-significance-skill]] §3 (Tag 별 score) + [[sources/ue-gameframework-characteroptimization]] §4.

## 3. 누적 적용 순서 (결정 트리)

**(1) 먼저 Visibility** — 무조건 켜기:

```cpp
SkelMeshComp->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
```

화면 밖 캐릭터의 Pose Tick + RefreshBoneTransforms 를 자동 skip. 비용 0, 효과 큼. [[concepts/EVisibilityBasedAnimTickOption]].

**(2) URO 추가** — 보일 때도 거리 기반 분할:

```cpp
SkelMeshComp->bEnableUpdateRateOptimizations = true;
// Project Settings 의 AnimUpdateRateShiftBucket 조정 또는
// FAnimUpdateRateParameters::SetTrailMode 로 거리 별 Tick 주기
```

**(3) Significance 묶기** — 거리 + 게임플레이 우선순위 = 본 컴포넌트 + Niagara + Audio + Tick 모두 한 score 로:

```cpp
USignificanceManager* Mgr = USignificanceManager::Get(World);
Mgr->RegisterObject(this, FName("NPC"), [](USignificanceManager::FManagedObjectInfo* Info, const FTransform& Viewer) {
    return CalcMyScore(Info, Viewer);   // 거리 + bIsBoss + bRecentlyRendered + ...
});
// 각 컴포넌트가 PostSignificanceUpdate 콜백에서 Tick / 컴포넌트 활성 결정
```

**(4) AnimSharing** — 같은 군집 NPC 가 5 마리 이상이면 활성:

```
Project Settings → Plugins → Animation Sharing
- AnimSharing Group 정의 (같은 Skeleton + 같은 BlendSpace 사용 NPC)
- 한 Master Pose Component 가 N 마리에 broadcast
```

**(5) Budget 마지막 안전망** — 100명 넘는 환경에서 overflow 차단:

```cpp
// Plugin: AnimationBudgetAllocator
USkeletalMeshComponentBudgeted* Budgeted = ...   // 자동 변환
// 프레임 budget 안 우선순위 큰 N개만 Tick — 나머지는 자동 skip
```

## 4. 비용 비교 시나리오 (50 NPC)

| 시나리오 | URO | Visibility | Significance | Sharing | Budget | 결과 |
| -- | -- | -- | -- | -- | -- | -- |
| naive | × | × | × | × | × | 전부 60Hz Pose — 16ms+ |
| Visibility 만 | × | ✓ | × | × | × | 보이는 N 마리만 Pose — 카메라 의존 큼 |
| 표준 | ✓ | ✓ | ✓ | × | × | 30 마리 보임 + 5 미터 안 0~10 만 매프레임, 10~20 미터 4프레임, 20+ 8프레임 — 50~70% 감소 |
| 고밀도 | ✓ | ✓ | ✓ | ✓ | ✓ | 같은 군집 1 Master + 우선순위 큰 N 만 Tick — 200 NPC 도 안정 |

## 5. 함정 / 열린 질문

- [ ] **URO + RootMotion 호환** — URO 가 4프레임 skip 시 RootMotion 누락 → 캐릭터가 안 움직임. RootMotion 활성 NPC 는 URO bucket 1 (매프레임) 강제 ([[concepts/RootMotion]])
- [ ] **AnimSharing 의 AnimMontage 비호환** — 군집 공유는 BlendSpace / AnimSequence 만. 개별 Hit reaction Montage 가 필요한 NPC 는 Sharing 제외
- [ ] **Significance score 계산 비용** — 매 프레임 50명 score 계산이 새로운 비용. score 함수는 `FORCEINLINE` + 단순 거리만 ([[sources/ue-significance-skill]] §6)
- [ ] **Bone LOD 와 누적** — [[concepts/Bone-LOD]] (USkeletalMeshLODSettings) 는 GPU Skinning 비용 절감 — CPU URO 와 *직교*. 둘 다 켜야 종합 효과
- [ ] **Niagara / VFX 도 Significance 묶음** — ENCPoolMethod::AutoRelease + Significance 콜백 ([[sources/ue-niagara-skill]]) 로 거리 멀면 system deactivate (열린, 세부 가이드 필요)
- [ ] **Cooked Build PSO 캐시 미스** — 첫 NPC Spawn 시 Material PSO 미컴파일 → render thread stall. PSO Precache 5.x 결합 ([[sources/ue-render-skill]] — 열린)

## 6. 관련

### Sources

[[sources/ue-animation-optimization]] · [[sources/ue-significance-skill]] · [[sources/ue-gameframework-characteroptimization]] · [[sources/ue-components-meshcomponents]] · [[sources/ue-ref-12-assetoptimizationpolicy]] · [[sources/ue-animation-skill]] · [[sources/ue-ai-skill]]

### Entities

[[entities/USkeletalMeshComponent]] · [[entities/USignificanceManager]] · [[entities/UAnimInstance]] · [[entities/ACharacter]] · [[entities/AAIController]]

### Concepts

[[concepts/URO]] · [[concepts/EVisibilityBasedAnimTickOption]] · [[concepts/Asset-Optimization-Policy]] · [[concepts/Bone-LOD]] · [[concepts/Tick-Group]]

### Related synthesis

[[synthesis/mc-character-hit-reaction-pipeline]] (NPC 피격/사망 시퀀스) · [[synthesis/spawnactor-hitching-4-step-pattern]] (NPC 첫 Spawn 비용) · [[synthesis/component-vs-actor-lifecycle-table]] (Tick 그룹 / 프레임 budget)

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[synthesis/mc-actor-spawn-subsystem-h1-measurement]] (inbound=3, suggest_missing_cross_link high confidence)
