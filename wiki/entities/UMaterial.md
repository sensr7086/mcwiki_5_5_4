---
type: entity
title: "UMaterial"
aliases: [UMaterial, UMaterialInterface, UMaterialInstance, UMaterialInstanceDynamic, MID, MIC]
kind: model
sources:
  - "[[sources/ue-assetclasses-skill]]"
tags: [ue, asset, rendering]
last_updated: 2026-05-09
---

# UMaterial / UMaterialInterface / UMaterialInstance

## 요약

UMaterialInterface (1,385 lines) 베이스 + UMaterial (2,166, 노드 그래프) + UMaterialInstance (1,256, 파라미터 override) + UMaterialInstanceConstant (MIC, 디스크 자산) + UMaterialInstanceDynamic (MID, 런타임). Domain 7 종 (Surface/PostProcess/Decal/Volume/UI/...) + ShadingModel 12 종 + BlendMode 7 종 + 5.x PSO Precache.

## 관계

- 부모: [[entities/UObject]]
- 베이스: UMaterialInterface
- 자손: UMaterial (root), UMaterialInstance / UMaterialInstanceConstant (MIC) / UMaterialInstanceDynamic (MID)
- 페어 호스트: [[entities/UPrimitiveComponent]] 자손 모두 (Material slots)
- 협력 자산: [[entities/UTexture]], MaterialParameterCollection

## 핵심 주장

- Domain 7 종 결정자: Surface (3D mesh) / DeferredDecal / Light Function / Post Process / UI / Volume / Subsurface. → 호스트 컴포넌트 결정.
- ShadingModel 12 종: DefaultLit / Unlit / Subsurface / PreintegratedSkin / ClearCoat / Hair / Cloth / Eye / TwoSidedFoliage / Volumetric / ThinTranslucent / SingleLayerWater.
- BlendMode 7 종: Opaque / Masked / Translucent / Additive / Modulate / AlphaComposite / AlphaHoldout. Translucent 는 Sort 영향 + 추가 비용.
- MIC vs MID:
  - MIC = 디스크 자산 (`.uasset`), 빌드 시 결정.
  - MID = 런타임 생성 (`UMaterialInstanceDynamic::Create(Parent, Outer)`), Component 마다 별도 인스턴스. 동적 파라미터 변경 가능.
- 5.x PSO Precache: 첫 프레임 hitch 회피 — Material 의 Pipeline State Object 를 미리 컴파일. Project Settings → Rendering 에서 활성.
- MaterialParameterCollection: 글로벌 파라미터 (월드 전체에서 공유). 시간 / 기상 / 글로벌 색조 등.

## 열린 질문

- [ ] PSO Precache 의 Cooking 단계 동작 — DDC 와 통합
- [ ] Translucent BlendMode 의 Sort priority 와 OIT 5.x
