---
type: source
title: "UE Components — ParticleComponents sub-skill"
slug: ue-components-particlecomponents
source_path: raw/ue-wiki-llm/skills/Components/references/ParticleComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UNiagaraComponent]]"
  - "[[entities/UNiagaraSystem]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, runtime, components, vfx]
---

# UE Components — ParticleComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/ParticleComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

VFX 호스트 — [[entities/UNiagaraComponent]] (5.x 표준) + UParticleSystemComponent (Cascade legacy) + UVectorFieldComponent. ENCPoolMethod::AutoRelease (Niagara 풀링) + Significance 통합.

## 2. Key claims

- 신규 VFX = 무조건 [[entities/UNiagaraComponent]]. UParticleSystemComponent (Cascade) 는 호환만.
- ENCPoolMethod 4종: None / FreeAllocation / OnlyAutoRelease / AutoRelease (표준). 일회성 VFX (총알 hit / 폭발) 자동 풀링.
- UVectorFieldComponent: Niagara 의 Velocity Field DI — 파편 흐름 / 와류 시뮬.
- SpawnSystemAtLocation / SpawnSystemAttached: UNiagaraFunctionLibrary 의 표준 spawn API.
- SetVariableFloat / SetVariableVec3 / SetVariableObject — 시스템 외부에서 파라미터 주입.
- Significance 통합: NiagaraEffectType 의 Cull 설정 → 거리별 자동 비활성. → [[concepts/Asset-Optimization-Policy]] §5.
- 다수 spawn 환경 (총알 hit, 폭발) = AutoRelease 풀 필수.

## 3. Open questions

- [ ] Cascade → Niagara 마이그레이션 표준 절차
- [ ] DataInterface 9종 의 Component 측 셋업
