---
type: entity
title: "UTexture"
aliases: [UTexture, UTexture2D, UTextureCube, UTextureRenderTarget2D, UVolumeTexture]
kind: model
sources:
  - "[[sources/ue-assetclasses-skill]]"
tags: [ue, asset, rendering]
last_updated: 2026-05-09
---

# UTexture / UTexture2D / UTextureCube / UTextureRenderTarget2D / UVolumeTexture

## 요약

UTexture (2,228 lines) 베이스 + UTexture2D (397, 가장 흔함) + UTextureCube + UTextureRenderTarget2D (RT) + UVolumeTexture. CompressionSettings 10 종 + TextureGroup 11 종 + MipGenSettings 8 종 + Streaming + 5.x VirtualTexture / RVT (Runtime Virtual Texture).

## 관계

- 부모: [[entities/UObject]]
- 자손: UTexture2D / UTextureCube / UTextureRenderTarget2D / UVolumeTexture / UTexture2DArray / UTextureLightProfile
- 페어: [[entities/UMaterial]] (Material 의 Texture parameter), [[entities/UPrimitiveComponent]] 의 Custom Primitive Data

## 핵심 주장

- CompressionSettings 10 종: Default (BC1/BC3) / NormalMap (BC5) / Masks / Grayscale / HDR (BC6H) / UI / etc.
- TextureGroup 11 종: World / WorldNormalMap / Character / UI / Lightmap / RenderTarget / Cinematic / etc. — LOD bias 와 streaming priority 결정.
- Streaming: 자동 (Texture Streaming Pool 안에서 우선순위) 또는 수동 (`bForceMiplevelsToBeResident`). 5.x 에서 더 정교한 priority.
- 5.x VirtualTexture: 큰 텍스처 (10K+) 를 tile 단위로 스트림. 메모리 ↓, GPU ↑.
- 5.x Runtime Virtual Texture (RVT): Material 의 결과를 텍스처로 캐싱 — Decal/Foliage 등에서 색조 합성 시 유용.
- BulkData: pixel data 가 [[concepts/BulkData]]. WITH_EDITORONLY_DATA 의 source data (raw pixel) 와 Cooked 의 plat data 가 분리.

## 열린 질문

- [ ] VirtualTexture vs Texture Streaming 의 결정 기준
- [ ] RVT 의 update 빈도 / 메모리 비용
