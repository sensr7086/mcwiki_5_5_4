---
type: source
title: "UE Render — Material sub-skill"
slug: ue-render-material
source_path: raw/ue-wiki-llm/skills/Render/references/Material.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-12
related_entities:
  - "[[entities/UMaterial]]"
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, render, gpu, material, slim-card]
citation_disclosure: "Substrate Material 상태 = 🟡 PARTIAL (raw 에서 '실험적' / '5.x 신규' 표기만 — UE 5.7.4 의 정식 Production 여부는 vault 외부 검증 필요). FMaterialCompiler 메소드 수 578 = 🟢 verified ([[sources/ue-render-materialexpression]] §2.3)."
---

# UE Render — Material

> Source: [[raw/ue-wiki-llm/skills/Render/references/Material.md]]
> Parent: [[sources/ue-render-skill]] · 페어: [[sources/ue-render-materialexpression]] (Custom Expression 깊이) · [[sources/ue-render-shader]] (FGlobalShader / USF)

## 1. Summary

`UMaterial` / USF / Custom HLSL Node + Material Domain 7 종 + ShadingModel 12 종 + Material Expression. Material 컴파일 흐름 (HLSL Translator → USF → Cooked PSO) + Custom HLSL Node 작성 + Custom Material Output. AssetClasses/Material ([[entities/UMaterial]]) 의 Render 측 페어. **Custom Material Expression 의 *깊은 작성 가이드* 는 [[sources/ue-render-materialexpression]] 로 분리** (raw L63 `§3 ~ §4 ✂️` 마커).

## 2. Key claims

### 2.1 컴파일 흐름 🟢

Editor 그래프 → HLSL Translator → USF → 플랫폼별 셰이더 binary → DDC 캐싱 → Cooked PSO.

### 2.2 Material Expression 노드 — 분리된 SSoT

- `UMaterialExpressionCustom` — HLSL 직접 작성 노드 (그래프 안). 매 Material 별 *고유 Permutation* → 폭증 위험 ([[sources/ue-render-materialexpression]] §2.4)
- `UMaterialExpressionCustomOutput` — Custom Output 등록 (Velocity / SSS Profile / Substrate Slab BSDF 등)
- **`UMaterialExpression` 자손 269종** ([[sources/ue-render-materialexpression]] §2.7) — 카테고리: 산술 / 벡터 / 텍스처 / 분기 / Substrate 등

### 2.3 5.x Substrate Material 상태 🟡 PARTIAL

- **Substrate Material 자체** (multi-layer BSDF / advanced shading) — UE 5.4 정식 도입, 5.7.4 = Production 추정 (🟡 vault 외부 검증 필요)
- **Material IR / `MIR::FEmitter` Build()** — 5.x **실험적** ([[sources/ue-render-materialexpression]] §2.5) — Compile() 와 *병행* 진행 중인 점진 마이그레이션
- 두 개를 *별개* 로 구분 — Substrate (✅ Production) vs IR Build (🧪 Experimental)

### 2.4 Domain × ShadingModel 매트릭스 🟢

Material Domain 7 (Surface / DeferredDecal / LightFunction / Volume / PostProcess / UI / VirtualTexture) × ShadingModel 12 (Default Lit / Unlit / Subsurface / Cloth / Hair / Eye / SingleLayerWater / ToonShading / Substrate / etc) = 84 조합. **실제 valid 은 일부** — 예: PostProcess Domain 은 Unlit 만, Volume Domain 은 Volumetric 만.

### 2.5 FMaterialCompiler 정합 🟢

`FMaterialCompiler` = **578** `int32` 메소드 ([[sources/ue-render-materialexpression]] §2.3 [verified]). 일부 vault 표기에 "600+" 라운드업이 있었으나 vault 통일 = **578**.

## 3. Cross-link

- 페어: [[sources/ue-render-materialexpression]] ⭐ Custom Expression 자손 작성 / [[sources/ue-render-shader]] FGlobalShader+USF / [[sources/ue-assetclasses-material]] (자산 측)
- 자산: [[entities/UMaterial]]
- 정책: 🚨 [[sources/ue-ref-11-assetloadingpolicy]] §3 (Editor 동기 로드) · 🚨 **PSO Precache 5.x `r.PSOPrecache=1` CVar — 본 source 가 권위 출처** (raw Material.md L93). [[sources/ue-render-shader]] L268 의 "DDC 미스" 와 [[synthesis/pso-streaming-livepatch-tools]] 가 cross-ref. (Cycle #2 보너스 발견 3 fix — 2026-05-12)

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-render-meshdrawing]] (inbound=3, suggest_missing_cross_link high confidence)
- [[sources/ue-render-mobile]] (inbound=3, suggest_missing_cross_link high confidence)
