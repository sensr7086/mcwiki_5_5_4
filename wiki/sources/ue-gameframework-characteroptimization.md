---
type: source
title: "UE GameFramework — Character Optimization Deep"
slug: ue-gameframework-characteroptimization
source_path: raw/ue-wiki-llm/skills/GameFramework/references/PawnCharacter/CharacterOptimization.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/ACharacter]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/URO]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
tags: [ue, gameframework, optimization, deep]
---

# UE GameFramework — Character Optimization Deep

> Source: [[raw/ue-wiki-llm/skills/GameFramework/PawnCharacter/references/CharacterOptimization.md]]
> Parent: [[sources/ue-gameframework-pawncharacter]]

## 1. Summary

[[entities/ACharacter]] 최적화 **10 종** 깊이 자료 — Tick 회피 / [[concepts/URO]] + [[concepts/EVisibilityBasedAnimTickOption]] / Significance / AnimationBudgetAllocator / Network / LOD / Capsule Channel / PostProcess + AI vs Player **9 종 매트릭스** + 결정 트리.

## 2. Key claims

- 10 종 최적화 누적:
  1. PrimaryActorTick 비활성 (`bCanEverTick = false`).
  2. Component Tick 분산 (per-component tick interval).
  3. URO Bucket (FAnimUpdateRateParameters).
  4. EVisibilityBasedAnimTickOption (5종).
  5. SkeletalMesh Bone LOD.
  6. USignificanceManager 등록.
  7. AnimationBudgetAllocator (Plugin).
  8. AnimSharing (UAnimSharingInstance).
  9. Network Update Frequency.
  10. AI vs Player 분기 매트릭스 (cosmetic 풀).
- AI vs Player 9 매트릭스: Tick / Anim / Net / VFX / Audio / Capsule / Mesh LOD / Light / Shadow.
- 결정 트리: 거리 가까움 (풀 Tick) → 중간 (URO) → 멀리 (URO + Visibility Off) → 매우 멀리 (Cull).
- 50+ NPC 환경 = 모든 10 종 누적.
