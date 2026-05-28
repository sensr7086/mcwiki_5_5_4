---
type: source
title: "UE AssetClasses — Animation sub-skill"
slug: ue-assetclasses-animation
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Animation.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UAnimSequence]]"
  - "[[entities/UAnimMontage]]"
  - "[[entities/UBlendSpace]]"
  - "[[entities/UAnimInstance]]"
tags: [ue, asset, animation]
---

# UE AssetClasses — Animation sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Animation.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

[[entities/UAnimSequence]] (1,001) + [[entities/UAnimMontage]] (996) + [[entities/UBlendSpace]] (966) + UAnimBlueprint (299) + [[entities/UAnimInstance]] (1,776) + USkeleton (1,037). 5.x NativeThreadSafeUpdateAnimation + Curve API + Montage_* + AnimNotify.

## 2. Key claims

- UAnimSequence: 단일 모션 클립. Pose 키 + Curve + Notify + 5.x ACL compression.
- UAnimMontage: AnimSequence 들의 컨테이너 + Slot + Sections + Branch Points + Notify. `Montage_Play` API.
- UBlendSpace / BlendSpace1D: 다차원 파라미터 → 모션 블렌드 (Locomotion 표준).
- UAnimBlueprint: Editor 만의 AnimGraph 그래프. Cooked 빌드는 UAnimInstance 자손 클래스만.
- UAnimInstance (런타임 측): Pose 평가 + Curve + Montage_* + Native* 라이프사이클. → [[sources/ue-animation-animinstance]]
- USkeleton: 본 계층 + Slot 정의 + Curve Mapping + Compatible Skeletons (5.x).
- 5.x ACL (Animation Compression Library): default compression. 메모리 절감.

## 3. Open questions

- [ ] ACL 5.x 압축 비율 비교 (legacy 대비)
- [ ] Montage 의 Multiplayer 동기 표준
