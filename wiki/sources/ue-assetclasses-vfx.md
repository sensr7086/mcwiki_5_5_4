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
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 0
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 0

**주요 시그니처 변경**:
- `> **위치**: Plugin (Niagara) `Engine/Plugins/FX/Niagara/Source/Niagara/Public/Niag → > **위치**: Plugin (Niagara) `Engine/Plugins/FX/Niagara/Source/Niagara/Classes/Nia`

**5.5.4 표현 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/AssetClasses/references/VFX.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/AssetClasses/references/VFX.md]]

### Body Reconciliation (2026-05-28)

- 자동 substitution 적용: **0 변경** (Niagara 경로 미세)
- 정합 후 tier: **pass-body-no-direct-cite**
