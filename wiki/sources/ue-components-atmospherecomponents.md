---
type: source
title: "UE Components — AtmosphereComponents sub-skill"
slug: ue-components-atmospherecomponents
source_path: raw/ue-wiki-llm/skills/Components/references/AtmosphereComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components, rendering]
---

# UE Components — AtmosphereComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/AtmosphereComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

대기 / 날씨 / 환경 — USkyAtmosphereComponent (5.x sky) + UExponentialHeightFogComponent (안개) + UVolumetricCloudComponent (5.x volumetric cloud) + UWindDirectionalSourceComponent (바람).

## 2. Key claims

- USkyAtmosphereComponent: 5.x 의 물리 기반 sky. Rayleigh / Mie scattering. 시간/계절 변경 동적 (Stationary / Movable).
- UExponentialHeightFogComponent: 거리 + 높이 기반 안개. FogInscatteringColor + FogDensity + FogHeightFalloff. Volumetric Fog 옵션 (5.x).
- UVolumetricCloudComponent (5.x): GPU 시뮬 cloud. CloudComponent + CloudMaterial. 매 프레임 비싼 — Mobile 권장 X.
- UWindDirectionalSourceComponent: 바람 방향 + 강도 — Foliage / Cloth / Niagara DI 영향.
- Map 당 보통 1개씩 (Atmosphere / Fog / Cloud) — Lighting 시스템과 통합.
- 5.x Lumen 활성 시 Atmosphere 반응 자동.

## 3. Open questions

- [ ] VolumetricCloud 의 모바일 / 저사양 platform 대안
- [ ] Wind 의 Foliage 반응 셋업
