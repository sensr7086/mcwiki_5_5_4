---
type: source
title: "UE AssetClasses — VFX sub-skill"
slug: ue-assetclasses-vfx
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/VFX.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UNiagaraSystem]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, asset, vfx]
---

# UE AssetClasses — VFX sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/VFX.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

[[entities/UNiagaraSystem]] (5.x Plugin 표준) + UParticleSystem (Cascade legacy) + UVectorField + UNiagaraEffectType (Significance / Cull).

## 2. Key claims

- UNiagaraSystem: 5.x VFX 표준. System (컨테이너) → Emitter (Particle 그룹) → Module (스크립트). 자세한 구조는 [[sources/ue-niagara-skill]].
- UParticleSystem (Cascade legacy): 4.x. 호환 목적만. 신규 = Niagara.
- UVectorField: Niagara 의 Velocity Field DI — 와류 / 흐름 / 충격파.
- UNiagaraEffectType: Significance / Cull 정책 자산. ENiagaraSignificanceHandling 4 종 (EarliestCullDistance / EarliestActorBased / EarliestKill / EarliestKeepActive).
- 품질 레벨 5 종 매트릭스: Cinematic 1.0 / High 1.0 / Medium 0.7 / Low 0.4 / Mobile 0.2 — SpawnCountScale / UpdateRateScale / MaxDistance / MaxSystemInstances.
- UAssetManager Bundle 분리: `Visual` (Niagara) / `Audio` (Sound) — Match Start PreLoad.
- [[concepts/Asset-Optimization-Policy]] §5 의 핵심.

## 3. Open questions

- [ ] Cascade → Niagara 마이그레이션 자동화 도구
