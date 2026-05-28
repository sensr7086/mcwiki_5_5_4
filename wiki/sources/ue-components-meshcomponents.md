---
type: source
title: "UE Components — MeshComponents sub-skill"
slug: ue-components-meshcomponents
source_path: raw/ue-wiki-llm/skills/Components/references/MeshComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UStaticMeshComponent]]"
  - "[[entities/USkeletalMeshComponent]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/URO]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
tags: [ue, runtime, components, mesh]
---

# UE Components — MeshComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/MeshComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

Mesh 호스트 컴포넌트 — [[entities/UStaticMeshComponent]] (5.x Nanite) + [[entities/USkeletalMeshComponent]] (5중 최적화 주 대상) + UInstancedStaticMeshComponent + UHierarchicalISMC. **§7 SkeletalMesh Tick 최적화 5종** ([[concepts/EVisibilityBasedAnimTickOption]] + [[concepts/URO]]) 의 정식 위치.

## 2. Key claims

- UStaticMeshComponent: [[entities/UStaticMesh]] 호스트. ScreenSize LOD + 5.x Nanite (Mesh 자산에 활성).
- UInstancedStaticMeshComponent (ISM) → UHierarchicalISMC (HISM): 다수 인스턴스 batched. 풀밭/돌/숲 표준. [[concepts/Asset-Optimization-Policy]] §3.
- USplineMeshComponent: Spline 따라 변형된 StaticMesh.
- USkeletalMeshComponent: [[entities/USkeletalMesh]] 호스트. AnimClass 또는 [[entities/UAnimInstance]] native.
- §7 EVisibilityBasedAnimTickOption 5종 결정 트리: AlwaysTickPoseAndRefreshBones / AlwaysTickPose / OnlyTickMontagesWhenNotRendered / OnlyTickPoseWhenRendered (표준) / OnlyTickMontagesAndRefreshBonesWhenPlayingMontages (5.x).
- §6 URO Bucket 분배 — 거리/Significance 기반 Animation Tick 주기.
- 다수 NPC (50+) = 5중 최적화 누적.

## 3. Open questions

- [ ] HISM vs ISM vs HLOD 결정 트리
- [ ] Nanite 활성 vs Legacy LOD 메모리/GPU 비용 비교
