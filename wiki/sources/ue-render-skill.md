---
type: source
title: "UE 5.7.4 Render Module — Main SKILL (19번째 카테고리)"
slug: ue-render-skill
source_path: raw/ue-wiki-llm/skills/Render/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-12
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, render, gpu]
---

# UE 5.7.4 Render Module — Main SKILL (19번째)

> Source: [[raw/ue-wiki-llm/skills/Render/SKILL.md]]

## 1. Summary

UE 5.x **GPU 측 코드 작성** 카테고리. RenderCore (RDG/Shader/Material/MaterialExpression) + Renderer (MeshDrawing/PostProcess/Lumen/Nanite) + RHI (Command List/Resources) + Vulkan/Mobile/VR 플랫폼 분기. **12 sub-skill** (Phase 8 + 1 = MaterialExpression 신규). 게임 스레드 (Components/AssetClasses) 와 분리된 별도 영역. **3 축 분리 의무**: 게임 스레드 → Render Thread (Proxy 데이터 복사) → RHI Thread (실제 명령 실행).

## 2. Sub-skills (12)

- [[sources/ue-render-rdg]] — Render Dependency Graph (5.x 표준)
- [[sources/ue-render-shader]] — Global / Material / Compute Shader · FGlobalShader / USF
- [[sources/ue-render-material]] — Material 컴파일 흐름 + Domain×ShadingModel 매트릭스
- ⭐ [[sources/ue-render-materialexpression]] — **Custom Material Expression 깊이** 🛠 (Phase 8 신규) · UMaterialExpression 자손 + FMaterialCompiler 578 + 5.x MIR::FEmitter + Substrate
- [[sources/ue-render-sceneviewextension]] — FSceneViewExtensionBase 7 Hook
- [[sources/ue-render-meshdrawing]] — FMeshBatch + FMeshPassProcessor 파이프라인
- [[sources/ue-render-postprocess]] — PostProcess Pipeline (5.x RDG 통합)
- [[sources/ue-render-lumennanite]] — 5.x Lumen + Nanite + GPU Scene
- [[sources/ue-render-rhi]] — FRHICommandList + Resources + 동기화
- [[sources/ue-render-vulkan]] — RHI 벤더 차이 (DX12/Vulkan/Metal/GLES)
- [[sources/ue-render-mobile]] — Mobile Forward + 5.x Mobile Deferred + Mobile PSO
- [[sources/ue-render-vr]] — Stereo Rendering + OpenXR + Foveated Rendering

## 3. Open questions

- [ ] FPrimitiveSceneProxy 의 Render Thread 데이터 복사 표준 패턴
- [ ] BeginInitResource / BeginReleaseResource 페어 lifetime

## 4. Cross-link

### Cycle 5p reverse-link 보강 (med confidence missing)

- 🚨 [[sources/ue-ref-07-profilingscopeRule]] — 모든 Render 측 콜백 (BeginRenderViewFamily/SetupView/PreRenderView_RenderThread/PostRenderViewFamily_RenderThread 등) 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무. 3 축 분리 (Game/Render/RHI) 의 각 측면에서 적용. §1 의 frontmatter `Profiling-Scope-Rule` 연계.
- [[sources/ue-ref-01-layermap]] — L1~L7 의존 계층. Render 카테고리는 L5~L6 (RHI 위, PostProcess 아래).
