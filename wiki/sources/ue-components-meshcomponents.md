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
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
