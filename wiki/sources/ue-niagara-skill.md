---
type: source
title: "UE 5.7.4 Niagara Plugin — Main SKILL"
slug: ue-niagara-skill
source_path: raw/ue-wiki-llm/skills/Niagara/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UNiagaraComponent]]"
  - "[[entities/UNiagaraSystem]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, plugin, vfx]
---

# UE 5.7.4 Niagara Plugin — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Niagara/SKILL.md]]
> Kind: text · Date: 2026-05-09 · Ingested: 2026-05-09

## 1. Summary

Cascade 의 후속 — **5.x VFX 표준**. Plugin (`Engine/Plugins/FX/Niagara/`). [[entities/UNiagaraComponent]] (UFXSystemComponent → USceneComponent) + [[entities/UNiagaraSystem]] (자산) + Stack 모듈 (System / Emitter / Particle Spawn / Update) + Data Interface 9종 + GPU vs CPU SimTarget + ENCPoolMethod (AutoRelease 표준) + USignificanceManager 통합. **신규 VFX = 무조건 Niagara** (Cascade 는 호환만).

## 2. Key claims

- 자세한 정의는 [[entities/UNiagaraSystem]] / [[entities/UNiagaraComponent]] 참조.
- NiagaraSystem 자산이 매우 큼 (Module Stack + DI + GPU 시뮬). `TSoftObjectPtr<UNiagaraSystem>` + UAssetManager `PreloadPrimaryAssets(bLoadRecursive=true)` Match Start 사전 로드 의무. [[concepts/Asset-Loading-Policy]]
- Pool 활성 (`ENCPoolMethod::AutoRelease`) + 메모리 상주 — 자주 Spawn = 풀이 사전 인스턴스. SpawnSystemAtLocation 첫 호출 히칭 = NiagaraSystem CDO 로드 + Shader PSO 컴파일.
- Quality Scaling (모든 NiagaraSystem 의무): UNiagaraEffectType 지정 + 5 품질 레벨 (Cinematic 1.0 / High 1.0 / Medium 0.7 / Low 0.4 / Mobile 0.2) + ENiagaraSignificanceHandling 4종. → [[concepts/Asset-Optimization-Policy]]
- Stack 구조: System (컨테이너) → Emitter (Particle 그룹) → Module (스크립트 동작).
- Data Interface 9 종: SkeletalMesh / StaticMesh / PhysicsAsset / Curve / VolumeTexture / RenderTarget2D / CollisionQuery / Audio / ParticleRead.

## 3. Quotations

> "신규 VFX 자산은 무조건 Niagara. Cascade (UParticleSystem) 는 마이그레이션 / 호환 목적만."

## 4. Open questions / next sources

- [ ] GPU Sim 의 Compute Shader 디버깅 (RenderDoc 통합)
- [ ] Niagara DI 9종 의 사용처 카탈로그
