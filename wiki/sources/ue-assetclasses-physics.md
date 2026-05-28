---
type: source
title: "UE AssetClasses — Physics sub-skill"
slug: ue-assetclasses-physics
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Physics.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, asset, physics]
---

# UE AssetClasses — Physics sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Physics.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

UPhysicalMaterial + EPhysicalSurface 32 종 + UPhysicalMaterialMask (5.x) + UPhysicsConstraintTemplate (6DoF Profile).

## 2. Key claims

- UPhysicalMaterial: Friction / Restitution / Density / Damping. Mesh / Mesh Section / Body Setup 에 적용.
- EPhysicalSurface 32 종: SurfaceType_Default + SurfaceType1 ~ SurfaceType31 (Project Settings 에서 명명 — Concrete / Metal / Wood / Flesh 등).
- UPhysicalMaterialMask (5.x): 텍스처 기반 surface 분리 — 한 mesh 의 여러 surface (예: 갑옷 = Metal, 살갗 = Flesh).
- UPhysicsConstraintTemplate: 6DoF (X / Y / Z / Twist / Swing1 / Swing2) Profile 자산 — 캐릭터 관절 / 로봇 / 차량 suspension.
- 사용처: HitResult.PhysMaterial — 발자국 / 피격 사운드 / VFX 결정.
- Anim Physics 통합: UPhysicalAnimationComponent 의 Profile 셋업.

## 3. Open questions

- [ ] PhysicalMaterialMask 의 5.x 표준 사용 패턴
