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
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 5
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 1

**주요 시그니처 변경**:
- `| 6 | [`Data`](./Data/SKILL.md) | `skills/AssetClasses/references/Data.md` | **U → | 1 | [`Mesh`](./Mesh/SKILL.md) | `skills/AssetClasses/references/Mesh.md` | **U`

**5.5.4 표현 (5.7.4 에 없음)**:
- `| 2 | [`Material`](./Material/SKILL.md) | `skills/AssetClasses/references/Material.md` | **UMaterial 2,083 + UMaterialIn`
- `| 3 | [`Texture`](./Texture/SKILL.md) | `skills/AssetClasses/references/Texture.md` | **UTexture 2,174 + UTexture2D 388 `
- `| 4 | [`Animation`](./Animation/SKILL.md) | `skills/AssetClasses/references/Animation.md` | **UAnimSequence 973 + UAnimM`
- `| 5 | [`Audio`](./Audio/SKILL.md) | `skills/AssetClasses/references/Audio.md` | **USoundBase 358 + USoundCue 367 + USoun`
- `| 6 | [`Data`](./Data/SKILL.md) | `skills/AssetClasses/references/Data.md` | **UDataAsset 71 + UPrimaryDataAsset + UData`

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/SKILL.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/SKILL.md]]

### Body Reconciliation (2026-05-28)

- 자동 substitution 적용: **0 변경** (SKILL 표 재정렬)
- 정합 후 tier: **pass-body-no-direct-cite**
