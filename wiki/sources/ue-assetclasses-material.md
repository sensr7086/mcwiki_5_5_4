---
type: source
title: "UE AssetClasses — Material sub-skill"
slug: ue-assetclasses-material
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Material.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UMaterial]]"
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, asset, rendering]
---

# UE AssetClasses — Material sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Material.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

UMaterial (2,166) + UMaterialInstanceConstant (MIC, 디스크) + UMaterialInstanceDynamic (MID, 런타임) + UMaterialInterface (1,385). Domain 7 종 + BlendMode 7 종 + ShadingModel 12 종 + 5.x PSO Precache.

## 2. Key claims

- Domain 7 종: Surface (3D) / DeferredDecal / Light Function / Post Process / UI / Volume / Subsurface — 호스트 컴포넌트 결정자.
- ShadingModel 12 종: DefaultLit / Unlit / Subsurface / PreintegratedSkin / ClearCoat / Hair / Cloth / Eye / TwoSidedFoliage / Volumetric / ThinTranslucent / SingleLayerWater.
- BlendMode 7 종: Opaque / Masked / Translucent / Additive / Modulate / AlphaComposite / AlphaHoldout. Translucent = sort 영향 + 추가 비용.
- MIC vs MID:
  - MIC = `.uasset`, 빌드 시 결정.
  - MID = `UMaterialInstanceDynamic::Create(Parent, Outer)` 런타임 생성. Component 마다 별개 → 동적 파라미터.
- 5.x PSO Precache: 첫 프레임 hitch 회피 — Pipeline State Object 사전 컴파일. Project Settings → Rendering → PSO Precaching.
- MaterialParameterCollection: 글로벌 파라미터 (시간 / 기상).
- MaterialFunction: 노드 그래프의 재사용 단위.

## 3. Open questions

- [ ] PSO Precache 의 Cook 단계 통합
- [ ] Translucent OIT 5.x 통합
