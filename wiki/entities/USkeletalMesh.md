---
type: entity
title: "USkeletalMesh"
aliases: [USkeletalMesh, SkeletalMesh]
kind: model
sources:
  - "[[sources/ue-assetclasses-skill]]"
tags: [ue, asset, mesh, animation]
last_updated: 2026-05-09
---

# USkeletalMesh

## 요약

[[entities/UObject]] 자손 (자산 클래스). 본 (Bone) 기반 deformable mesh — 3,248 lines. USkeleton (참조 Skeleton) + RenderData (LODRenderData chain) + Material slots + UPhysicsAsset (Ragdoll) + Compatible Skeletons (5.x) + Virtual Bones (5.x). [[entities/USkeletalMeshComponent]] 가 호스트.

## 관계

- 부모: [[entities/UObject]]
- 페어 호스트: [[entities/USkeletalMeshComponent]]
- 강제 협력: USkeleton (Skeleton 자산)
- 협력: UPhysicsAsset (Ragdoll), [[entities/UMaterial]] (다중 슬롯), UAnimBlueprint (간접)

## 핵심 주장

- Skeleton: 본 계층 (FReferenceSkeleton). Compatible Skeletons (5.x) 로 다른 Skeleton 의 모션 재사용 가능. Virtual Bones (5.x) — 런타임에만 존재하는 가상 본.
- LOD chain: USkeletalMeshLODSettings 의 BonesToRemove / Prioritize 로 LOD 별 본 수 감소. → [[concepts/Bone-LOD]]
- LODRenderData: 각 LOD 별 vertex / index / skin weights. Bulk Data — lazy load.
- UPhysicsAsset: Ragdoll 표현 — 본별 SimplePrimitive (Capsule/Box/Sphere) + Constraint.
- Material slots: 자산의 default + Component override.
- 페어 자산 (Animation): UAnimBlueprint / [[entities/UAnimSequence]] / [[entities/UAnimMontage]] / [[entities/UBlendSpace]] — Skeleton 단위로 호환.

## 열린 질문

- [ ] Compatible Skeleton 5.x 의 retarget 동작 — IK Retargeter 와 비교
- [ ] Virtual Bones 의 Animation Curve 통합
