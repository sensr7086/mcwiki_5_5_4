---
type: source
title: "UE Components — RenderingComponents sub-skill"
slug: ue-components-renderingcomponents
source_path: raw/ue-wiki-llm/skills/Components/references/RenderingComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UMaterial]]"
  - "[[entities/UTexture]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components, rendering]
---

# UE Components — RenderingComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/RenderingComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

특수 렌더링 컴포넌트 — UDecalComponent + UTextRenderComponent + USceneCaptureComponent2D / Cube + UPostProcessComponent + UReflectionCaptureComponent + URuntimeVirtualTextureComponent (5.x). 모두 [[entities/UMaterial]] 페어 (특정 Domain 사용).

## 2. Key claims

- UDecalComponent: 표면에 투영되는 이미지 (총알 자국 / 핏자국). [[entities/UMaterial]] Domain=DeferredDecal.
- UTextRenderComponent: 3D 공간의 텍스트 (간판 / 숫자). UFont + UMaterial.
- USceneCaptureComponent2D: 2D RenderTarget 으로 scene 캡처. UTextureRenderTarget2D 자산. 미니맵 / 거울 / CCTV.
- USceneCaptureComponentCube: Cubemap 캡처. 동적 reflection capture.
- UPostProcessComponent: PostProcess 효과 영역 (Blendable). Material Domain=PostProcess + Volume vs Unbound.
- UReflectionCaptureComponent: 정적 reflection probe (Build 시 cube map 베이크).
- URuntimeVirtualTextureComponent (5.x): RVT — 큰 영역의 material 결과 캐싱.

## 3. Open questions

- [ ] SceneCapture 의 매 frame 캡처 비용
- [ ] RVT 의 update 빈도 / 메모리 비용
