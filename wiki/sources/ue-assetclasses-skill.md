---
type: source
title: "UE 5.7.4 AssetClasses Module — Main SKILL"
slug: ue-assetclasses-skill
source_path: raw/ue-wiki-llm/skills/AssetClasses/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UStaticMesh]]"
  - "[[entities/USkeletalMesh]]"
  - "[[entities/UMaterial]]"
  - "[[entities/UTexture]]"
  - "[[entities/UAnimSequence]]"
  - "[[entities/UAnimMontage]]"
  - "[[entities/UBlendSpace]]"
  - "[[entities/USoundBase]]"
  - "[[entities/UNiagaraSystem]]"
related_concepts:
  - "[[concepts/Asset-Lifecycle]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/BulkData]]"
tags: [ue, runtime, assets]
---

# UE 5.7.4 AssetClasses Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/SKILL.md]]

## 1. Summary

Components 가 호스트, AssetClasses 가 자산 — 페어 매트릭스. 9 sub-skill 분할.

## 2. Sub-skills (9 — Phase 4D 완료)

- [[sources/ue-assetclasses-mesh]] — StaticMesh + SkeletalMesh + Skeleton + PhysicsAsset (Nanite / Compatible Skeleton)
- [[sources/ue-assetclasses-material]] — Material / MIC / MID + Domain 7 / ShadingModel 12 + 5.x PSO Precache
- [[sources/ue-assetclasses-texture]] — Texture + 5.x VirtualTexture / RVT + CompressionSettings 10 / TextureGroup 11
- [[sources/ue-assetclasses-animation]] — AnimSequence / AnimMontage / BlendSpace / AnimBlueprint / AnimInstance
- [[sources/ue-assetclasses-audio]] — SoundBase / Cue / Wave / Concurrency / Attenuation + 5.x MetaSounds
- [[sources/ue-assetclasses-data]] — DataAsset / PrimaryDataAsset (Bundle) / DataTable / CurveTable
- [[sources/ue-assetclasses-vfx]] — NiagaraSystem (5.x) + ParticleSystem (Cascade legacy) + EffectType
- [[sources/ue-assetclasses-camera]] — UCameraShakeBase + ShakePattern 4 + UCameraAnimationSequence (5.x)
- [[sources/ue-assetclasses-physics]] — PhysicalMaterial + EPhysicalSurface 32 + PhysicsConstraintTemplate

## 3. Open questions

- [ ] BulkData 의 Editor vs Cooked 동작 차이
- [ ] DDC 의 PSO/Shader/Mesh 파이프라인
- [ ] 5.x VT vs Texture Streaming 비교
