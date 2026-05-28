---
type: concept
title: "Asset Optimization Policy (5대 영역)"
aliases: [Asset Optimization, Bone LOD, Actor Merging]
sources:
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-assetclasses-skill]]"
  - "[[sources/ue-animation-skill]]"
related_concepts:
  - "[[concepts/Bone-LOD]]"
  - "[[concepts/URO]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, runtime, asset, optimization, policy]
last_updated: 2026-05-09
---

# Asset Optimization Policy — 5대 영역

## 1. 정의 (한 줄)

60 fps 유지 + 메모리 한계 + GPU 한계 회피의 90% 책임을 지는 5 영역 — SkeletalMesh Bone LOD / StaticMesh LOD / Actor Merging (HISM/HLOD/WorldPartition) / Audio Culling / Niagara Quality Scaling. 자세한 코드는 [[raw/ue-wiki-llm/references/12_AssetOptimizationPolicy.md]].

## 2. 자세히

| # | 영역 | 핵심 |
| -- | -- | -- |
| 1 | **SkeletalMesh** | [[concepts/Bone-LOD]] (USkeletalMeshLODSettings + BonesToRemove/Prioritize) + [[concepts/URO]] + [[concepts/EVisibilityBasedAnimTickOption]] (5종) + AnimationBudgetAllocator Plugin + Significance 5 중 누적 |
| 2 | **StaticMesh** | LOD ScreenSize threshold (표준) + 5.x Nanite (LOD chain 무관, virtualized geo) + LODGroup |
| 3 | **Actor Merging** | UInstancedStaticMeshComponent (HISM = Hierarchical) + Mesh Merge (UStaticMesh 합성) + HLOD (HierarchicalLOD) + WorldPartition cell 단위 자동 |
| 4 | **Audio** | USoundAttenuation (거리 감쇠) + USoundConcurrency (동시 재생 제한 5종 ResolutionRule) + Significance (거리 culling) |
| 5 | **Niagara** | UNiagaraEffectType (EffectType Significance / Cull) + 품질 레벨 5종 매트릭스 + GPU vs CPU SimTarget |

## 3. 변형 / 사례 / 응용

- **다수 NPC (50+) 환경**: SkeletalMesh 5 중 누적 (URO + Visibility + Significance + Sharing + Budget) + Audio Concurrency + Niagara Significance + HISM/HLOD 통합.
- **모바일 Profile**: StaticMesh LOD bias + Texture LODGroup ↑ + Niagara Quality Scaling 의 Low setting + Bone LOD 더 공격적.
- **VR Profile**: 90+ fps 의무 — 모든 5 영역 적극 적용. Forward Rendering + Mobile MultiView.

## 4. 관련 entity

- [[entities/USkeletalMeshComponent]] · [[entities/UStaticMeshComponent]] · [[entities/UNiagaraSystem]] · [[entities/USoundBase]]

## 5. 열린 질문

- [ ] 5중 최적화의 누적 비용 비교 — 각 단계별 ms 절감
- [ ] WorldPartition + HLOD 의 통합 동작
