---
type: concept
title: "Bone LOD (USkeletalMeshLODSettings)"
aliases: [Bone LOD, BonesToRemove, USkeletalMeshLODSettings]
sources:
  - "[[sources/ue-animation-skill]]"
  - "[[sources/ue-assetclasses-skill]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/URO]]"
tags: [ue, runtime, animation, optimization]
last_updated: 2026-05-09
---

# Bone LOD

## 1. 정의 (한 줄)

[[entities/USkeletalMesh]] 의 LOD 별로 *본 수* 를 감소시키는 메커니즘 — `USkeletalMeshLODSettings` 의 `BonesToRemove` (LOD 별 제거할 본) + `BonesToPrioritize` (강제 보존). [[concepts/Asset-Optimization-Policy]] 의 1번 영역.

## 2. 자세히

```
LOD 0:  full skeleton (예: 80 본)         가까운 거리 / 화면 큼
LOD 1:  finger bone 제거                  중간 (~70 본)
LOD 2:  finger + toe + clavicle 제거      먼 거리 (~50 본)
LOD 3:  spine 단순화                      매우 먼 거리 (~30 본)
```

- **BonesToRemove (LOD 별)**: 해당 LOD 에서 제거할 본 — Editor 에서 LOD 별로 설정.
- **BonesToPrioritize**: 강제 유지할 본 (예: weapon socket bone).
- **자동 적용**: Mesh LOD 결정 (ScreenSize / 거리) → 해당 LOD 의 본만 평가 + GPU skinning.

## 3. 변형 / 사례 / 응용

- **다수 NPC 환경**: LOD 3 의 본 수를 30 개 이하로 → SkeletalMesh skinning GPU 비용 ↓.
- **Mesh build 시점에 결정**: Editor 에서 LOD 별 BonesToRemove 설정 → DDC 에 build 결과 캐싱.
- **5.x 와의 호환**: Compatible Skeleton 5.x 가 다른 본 구조 사용 시 BonesToRemove 의 의미 보존.
- **AnimSequence Compression** 과 별개: Compression 은 키 데이터 압축, Bone LOD 는 평가 본 수 감소.

## 4. 관련 entity

- [[entities/USkeletalMesh]] · [[entities/USkeletalMeshComponent]]

## 5. 열린 질문

- [ ] LOD 별 BonesToRemove 의 자동 추천 (Editor 도구)
- [ ] BonesToPrioritize 와 weapon socket 의 정확한 통합
