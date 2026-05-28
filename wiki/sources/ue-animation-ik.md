---
type: source
title: "UE Animation — IK sub-skill"
slug: ue-animation-ik
source_path: raw/ue-wiki-llm/skills/Animation/references/IK.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UIKRigDefinition]]"
  - "[[entities/UIKRetargeter]]"
tags: [ue, runtime, animation, ik]
---

# UE Animation — IK sub-skill ⭐

> Source: [[raw/ue-wiki-llm/skills/Animation/references/IK.md]]
> Parent: [[sources/ue-animation-skill]]

## 1. Summary

UE 5.7.4 IK 통합 — Legacy AnimNode IK 8 종 + 5.x [[entities/UIKRigDefinition]] (선언적 Asset + 7 Solvers) + 5.x [[entities/UIKRetargeter]] (Skeleton 간 모션 재사용 + 16 RetargetOps).

## 2. Key claims

- Legacy AnimNode IK 8 종 (4.x 호환): FAnimNode_TwoBoneIK / Fabrik / LegIK / CCDIK / SplineIK / LookAt / HandIKRetargeting / ApplyLimits.
- 5.x [[entities/UIKRigDefinition]] 7 Solvers: FullBodyIK (FBIK, 다중 골 동시) / Limb IK / Pole Vector / SetTransform / BodyMover (Hip 따라 전신) / StretchLimb (팔다리 늘림) / 기타.
- FAnimNode_IKRig: AnimGraph 의 IK Rig 자산 평가.
- 5.x [[entities/UIKRetargeter]]: Source Skeleton (예: Mannequin) → Target Skeleton (Custom) 변환. 16 RetargetOps (Pose Copy / Bone Lengths / Root Lock / IK Foot / Limb Adjust / Hip Adjust / etc.).
- FAnimNode_RetargetPoseFromMesh: 다른 Skeleton 의 mesh 의 pose 를 자기 mesh 로 retarget.
- 결정 트리: 단순 IK (발 IK 1개 / 손 IK 1개) = Legacy LegIK / Fabrik. 다중 골 동시 (전신 IK) = 5.x FBIK. 다른 Skeleton 모션 재사용 = 5.x IK Retargeter.
- 표준 사용처: 발 IK (지면 적응) / 손 IK (무기 / 사다리) / 시선 추적 (LookAt) / 처형 모션 (FBIK 다중 골).

## 3. Open questions

- [ ] IK Rig 7 Solvers 사용처 카탈로그
- [ ] Legacy → IK Rig 마이그레이션 표준
