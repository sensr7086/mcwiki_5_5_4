---
type: source
title: "UE Components — LightComponents sub-skill"
slug: ue-components-lightcomponents
source_path: raw/ue-wiki-llm/skills/Components/references/LightComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UPrimitiveComponent]]"
related_concepts:
  - "[[concepts/Mobility]]"
tags: [ue, runtime, components, rendering]
---

# UE Components — LightComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/LightComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

UE 의 라이트 컴포넌트 — UPointLight / USpotLight / URectLight / UDirectionalLight / USkyLight + ULocalLight (베이스) + Mobility 매트릭스. [[concepts/Mobility]] 와 직결 — Light Baking 호환성 결정자.

## 2. Key claims

- 베이스 트리: ULightComponentBase → ULocalLightComponent → UPointLight / USpotLight / URectLight + UDirectionalLightComponent (별도) + USkyLightComponent (별도) + USkyAtmosphereComponent.
- UPointLight: 모든 방향 (전구). Attenuation Radius. SourceRadius / SoftSourceRadius.
- USpotLight: Cone 방향 (가로등). InnerCone / OuterCone Angle.
- URectLight: 사각형 면광 (5.x). Width / Height.
- UDirectionalLight: 평행광 (해/달). Map 당 1개 표준.
- USkyLight: 환경광 + reflection capture. Movable 시 동적, Static/Stationary 시 baked.
- Mobility × Light Baking 매트릭스: Static Light + Static Mesh = 완전 baked. Movable Light + Movable Mesh = 동적 only.
- 5.x Lumen 활성 시 Movable Light 비용 ↓.

## 3. Open questions

- [ ] 5.x Lumen / Hardware Lumen 환경에서 Mobility 의미 변화
- [ ] Light Function (Material Domain=LightFunction) 통합
