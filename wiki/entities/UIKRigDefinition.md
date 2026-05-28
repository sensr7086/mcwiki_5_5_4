---
type: entity
title: "UIKRigDefinition"
aliases: [UIKRigDefinition, IKRig]
kind: model
sources:
  - "[[sources/ue-animation-skill]]"
tags: [ue, runtime, animation, ik]
last_updated: 2026-05-09
---

# UIKRigDefinition (5.x IK Rig)

## 요약

[[entities/UObject]] 자손. **5.x IK 표준** — 선언적 IK Asset. 7 Solvers (FBIK / Limb / Pole / SetTransform / BodyMover / StretchLimb / 등) 를 graph 로 조합. FBIK = 다중 골 동시 풀이 (전신 IK). FAnimNode_IKRig 가 런타임 평가.

## 관계

- 부모: [[entities/UObject]]
- 페어 자산: USkeleton / [[entities/USkeletalMesh]] (대상)
- 런타임: FAnimNode_IKRig (AnimGraph 노드)
- 후속: [[entities/UIKRetargeter]] (Skeleton 간 모션 재사용)

## 핵심 주장

- 5.x 표준 — Legacy AnimNode IK 8 종 (FAnimNode_TwoBoneIK 등) 보다 우선.
- 7 Solvers: FBIK (전신 IK, 다중 골) / Limb IK (팔다리 단일 chain) / Pole Vector / SetTransform (특정 본 강제) / BodyMover (Hip 따라 전신 이동) / StretchLimb (팔다리 늘림) / 기타.
- 선언적 Asset: Editor 에서 graph 로 Solvers 조합. 런타임 평가는 FAnimNode_IKRig 가 해당 Asset 사용.
- 다중 골 동시 풀이 = FBIK 의 핵심 — 발 + 손 + 시선 등 여러 IK 골을 한 번에 만족하는 Pose 풀이.
- Profiling: FAnimNode_IKRig::Evaluate_AnyThread 가 워커 스레드. 고비용 시 LOD 별 Solver disable 옵션.

## 열린 질문

- [ ] 7 Solvers 각각의 사용처 카탈로그
- [ ] Legacy IK 와의 비교 — 마이그레이션 표준
