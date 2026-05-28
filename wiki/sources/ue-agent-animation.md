---
type: source
title: "UE Animation Specialist — 런타임 8 sub-skill + 자산 페어 + 다수 NPC 5중 최적화"
slug: ue-agent-animation
source_path: raw/ue-wiki-llm/agents/ue-animation-specialist.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_entities:
  - "[[entities/UAnimInstance]]"
  - "[[entities/FAnimNode-Base]]"
related_concepts:
  - "[[concepts/URO]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
tags: [ue, agent, specialist, animation, multi-npc-optimization, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 2 enrich (stub → 정밀)"
---

# UE Animation Specialist 🎬

> Source: [[raw/ue-wiki-llm/agents/ue-animation-specialist.md]]
> Parent: [[sources/ue-agent-orchestrator]] — `[Animation]` prefix 호출
> Cycle 5n Round 2 — stub → 정밀 enrich (raw 본문 통합)

## 1. Summary

🟢 UE 5.7.4 Animation 카테고리 전문가 — 런타임 측 **8 sub-skill** (AnimInstance / AnimGraph / AnimNotify / Sync / RootMotion / Optimization / IK / Ragdoll) + AssetClasses/Animation 페어. UAnimInstance `Native*` 5단 + Custom AnimNode 4단 `_AnyThread` + Inertialization 5.x + RootMotion CMC 페어 + 다수 NPC **5중 최적화** + 5.x IK Rig (`UIKRigDefinition` + 7 Solvers) + IK Retargeter (16 Ops) + Ragdoll (`SetSimulatePhysics` + UPhysicsAsset + UPhysicalAnimationComponent + 죽음 5단 표준) 자동 적용.

**도구**: Read, Edit, Write, Grep, Glob, Bash. **모델**: opus.

## 2. 자동 로드 (6 파일)

1. `skills/Animation/SKILL.md` (메인 — 8 sub-skill 인덱스)
2. 사용자 요청 매칭 sub-skill (AnimInstance / AnimGraph / AnimNotify / Sync / RootMotion / Optimization / IK / Ragdoll)
3. [[sources/ue-assetclasses-animation]] (자산 페어)
4. [[sources/ue-components-meshcomponents]] §7 (호스트 페어 + URO 깊이)
5. [[sources/ue-ref-07-profilingscopeRule]] (의무)
6. [[sources/ue-ref-12-assetoptimizationpolicy]] §1 (다수 NPC)

## 3. 14 시나리오 매핑 (요약)

| 시나리오 | 필수 sub-skill |
|---------|---------------|
| 캐릭터 + AnimBP 셋업 | AnimInstance ⭐ |
| Custom AnimNode | AnimGraph |
| 발자국 / 콤보 / 히트박스 | AnimNotify |
| BlendSpace 동기 / 0ms 블렌드 | Sync |
| 어택 이동 (Roll / Grapple) | RootMotion |
| **50+ NPC 60fps ⭐⭐** | Optimization (URO + Visibility + Significance + Budget + Sharing) |
| 발 IK / 무기 IK / 시선 추적 ⭐ | IK Rig (5.x) |
| Skeleton 간 모션 재사용 ⭐ | IK Retargeter (5.x, 16 Ops) |
| 죽음 / 다운 / 폭발 ⭐ | Ragdoll + UPhysicsAsset + CMC DisableMovement |
| 부분 Ragdoll (히트 반응) | Ragdoll + SetAllBodiesBelowSimulatePhysics |
| 방향성 Ragdoll (히트 / 폭발) ⭐ | Ragdoll §6 + AddImpulseAtLocation / AddRadialImpulse |

## 4. UAnimInstance 라이프사이클 의무 (5단 + Super)

```cpp
NativeInitializeAnimation()    → Super FIRST
NativeBeginPlay()               → Super FIRST
NativeUpdateAnimation(DT)       → Super FIRST   (게임 스레드)
NativeThreadSafeUpdateAnim(DT)  → Super FIRST   (워커 스레드)
NativeUninitializeAnimation()   → Super LAST
```

> 모두 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무.

## 5. NativeUpdate vs NativeThreadSafe 분리 의무

- **NativeUpdate** (게임 스레드): Owner / Component 접근 OK + 캐싱
- **NativeThreadSafe** (워커 스레드): 캐싱 값만 사용 (Owner 직접 접근 X)

## 6. Custom AnimNode (FAnimNode_Base 4단 `_AnyThread`)

```cpp
Initialize_AnyThread     → 1회 + 자식 FPoseLink::Initialize
CacheBones_AnyThread     → LOD 변경 시 + FBoneReference::Initialize
Update_AnyThread         → 매 프레임 (시간) + 자식 Update
Evaluate_AnyThread       → 매 프레임 (Pose 평가) + 자식 Evaluate
```

> `UAnimGraphNode_*` = Editor 모듈 (4단 분리).

## 7. RootMotion 페어 의무

```cpp
Montage->bEnableRootMotionTranslation = true;
GetCharacterMovement()->bEnableRootMotionMontagesOnly = true;
```

## 8. IK 결정 매트릭스 (5.x 표준)

```
캐릭터 다중 IK (발 + 손 + 시선)  → 5.x IK Rig (UIKRigDefinition + FBIK Solver) ⭐
Skeleton 간 모션 재사용           → 5.x IK Retargeter (UIKRetargeter)
단순 한 노드 IK                   → Legacy AnimNode (FAnimNode_TwoBoneIK)
런타임 리깅 / 시네마틱             → Control Rig (ue-plugin-specialist 위임)
```

## 9. 다수 NPC 5중 최적화 자동

1. URO (`bEnableUpdateRateOptimizations`)
2. Visibility Tick (`OnlyTickPoseWhenRendered`)
3. Significance Manager 등록
4. (100+) `USkeletalMeshComponentBudgeted`
5. (군중 동일 모션) `UAnimSharingInstance` (`SetMasterPoseComponent`)

## 10. Baseline Grep 의무 (Cycle 5h #4)

함정 키워드: `UAnimInstance` / `FAnimNode_` / `AnimNotify` / `URO` / `IKRig` / `Inertialization` / `RootMotion`. Pre-write 3단 + Post-write 3단 ([[sources/ue-meta-baseline-grep-system]] §4).

## 11. 거부 조건

- 자산 (AnimSequence / Skeleton 등) — `ue-asset-specialist`
- Components 작성 — `ue-components-specialist`
- Plugin (GAS / Control Rig) — `ue-plugin-specialist`

## 12. Cross-link

- 메타 agent: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-wiki-maintainer]] · [[sources/ue-agent-audit]]
- 페어 specialist: [[sources/ue-agent-asset]] (자산) · [[sources/ue-agent-components]] (MeshComponents 호스트)
- 자동 로드 (raw): [[sources/ue-assetclasses-animation]] · [[sources/ue-components-meshcomponents]] · [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-12-assetoptimizationpolicy]]
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7 (agent prompt patch)

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | grep-listed stub 카드 |
| 2026-05-15 (Cycle 5n Round 2) | ⭐⭐⭐ stub → 정밀 13 절. 14 시나리오 매핑 + 5단 + 4단 _AnyThread + IK 결정 매트릭스 + 5중 최적화 |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
