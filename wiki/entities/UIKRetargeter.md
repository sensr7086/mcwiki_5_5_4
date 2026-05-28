---
type: entity
title: "UIKRetargeter"
aliases: [UIKRetargeter, IKRetargeter]
kind: model
sources:
  - "[[sources/ue-animation-skill]]"
tags: [ue, runtime, animation, ik]
last_updated: 2026-05-09
---

# UIKRetargeter (5.x IK Retargeter)

## 요약

[[entities/UObject]] 자손. **다른 Skeleton 의 모션 재사용 표준** — 5.x. 16 RetargetOps 로 Source Skeleton (예: Mannequin) → Target Skeleton (Custom) 의 변환 graph. FAnimNode_RetargetPoseFromMesh 가 런타임 평가.

## 관계

- 부모: [[entities/UObject]]
- 페어 자산: 2 개 USkeleton (Source / Target)
- 런타임: FAnimNode_RetargetPoseFromMesh
- 협력: [[entities/UIKRigDefinition]] (Source / Target 양쪽에 IK Rig 권장)

## 핵심 주장

- 16 RetargetOps: Pose Copy / Bone Lengths / Root Lock / IK Foot / Limb Adjust / Hip Adjust / 등 — graph 로 Source → Target 변환.
- 표준 사용 사례: Mannequin 모션 → Custom Character (다른 비율). Marketplace 의 모션 자산을 자기 캐릭터에 재사용.
- IK Rig 와의 통합: Source / Target 양쪽이 [[entities/UIKRigDefinition]] 보유 시 더 정확한 retarget. Limb IK / Foot IK 등이 retarget 후 적용.
- vs Compatible Skeleton 5.x: Compatible Skeleton 은 동일 본 구조에서 모션 공유 (간단). IK Retargeter 는 다른 구조에서도 (정교).
- Profiling: FAnimNode_RetargetPoseFromMesh::Evaluate_AnyThread 워커 스레드 — Source mesh 의 pose evaluation 자체 비용도 같이.

## 열린 질문

- [ ] Compatible Skeleton vs IK Retargeter 결정 기준
- [ ] 16 RetargetOps 의 권장 graph 패턴
