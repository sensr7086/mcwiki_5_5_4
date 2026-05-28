---
type: source
title: "UE AssetClasses — Texture sub-skill"
slug: ue-assetclasses-texture
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Texture.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UTexture]]"
related_concepts:
  - "[[concepts/BulkData]]"
tags: [ue, asset, rendering]
---

# UE AssetClasses — Texture sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Texture.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

UTexture (2,228) + UTexture2D + UTextureCube + UTextureRenderTarget2D + UVolumeTexture. CompressionSettings 10 종 + TextureGroup 11 종 + MipGenSettings 8 종 + 5.x VirtualTexture / RVT.

## 2. Key claims

- CompressionSettings 10 종: Default (BC1/BC3) / NormalMap (BC5) / Masks / Grayscale / HDR (BC6H) / UI / DistanceFieldFont / EditorIcon / Alpha / DisplacementMap.
- TextureGroup 11 종: World / WorldNormalMap / Character / UI / Lightmap / RenderTarget / Cinematic / etc — LOD bias + streaming priority.
- MipGenSettings 8 종: FromTextureGroup / Sharpen0~10 / NoMipmaps / SimpleAverage / etc.
- Streaming: 자동 (Texture Streaming Pool) 또는 bForceMipLevelsToBeResident.
- 5.x VirtualTexture (VT): 큰 텍스처 (10K+) 를 tile 단위 stream. 메모리 ↓ GPU ↑.
- 5.x RuntimeVirtualTexture (RVT): Material 결과를 텍스처로 캐싱 — Decal / Foliage 색조 합성.
- BulkData ([[concepts/BulkData]]): mip pixel data 가 lazy load. WITH_EDITORONLY_DATA source raw.

## 3. Open questions

- [ ] VT vs Texture Streaming 결정 트리
- [ ] RVT update 빈도 / 메모리 비용
