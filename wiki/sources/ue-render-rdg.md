---
type: source
title: "UE Render — RDG sub-skill (5.x 표준)"
slug: ue-render-rdg
source_path: raw/ue-wiki-llm/skills/Render/references/RDG.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-12
citation_disclosure: "🟢 9 / 🟡 1 / 🔴 0 · 보너스 발견 2건"
tags: [ue, render, gpu, rdg, rdg-builder, async-compute, blackboard, slim-card]
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
---

# UE Render — RDG (Render Dependency Graph)

> Source: [[raw/ue-wiki-llm/skills/Render/references/RDG.md]]
> Parent: [[sources/ue-render-skill]] · 페어: [[sources/ue-render-shader]] · [[sources/ue-render-sceneviewextension]] · [[sources/ue-render-rhi]]
> 5.x 표준 — Custom PostProcess / Compute Shader / Custom Pass 의 진입점.

## 1. Summary

UE 5.x Render Dependency Graph (RDG) 는 모든 GPU 작업의 5.x 표준 컨테이너 — `FRDGBuilder` 가 Frame 의 모든 Pass 등록, Resource Lifetime 자동, Pass Culling, Async Compute 명세 지원 🟢 (raw L6-10). 5 핵심 클래스 = `FRDGBuilder` + `FRDGTextureRef` + `FRDGBufferRef` + `FRDGPass` + `FRDGBlackboard` 🟢 (raw L26-32). Legacy `IPooledRenderTarget` 직접 패턴은 5.x 에서 deprecated 흐름 — RDG 안 `RegisterExternalTexture` 로 통합 🟢 (raw L113-117, L216, L227).

## 2. Key claims

- 🟢 `FRDGBuilder` 는 Frame 의 GPU 작업 컨테이너이며 모든 Pass 등록 진입점 — `RenderGraphBuilder.h:47` (raw L9, L28).
- 🟢 RDG Pass 의 첫 줄 `RDG_EVENT_SCOPE(GraphBuilder, "Name")` 는 의무 — Insights / RenderDoc 명명된 hierarchy 표시 (raw L18, L188-206, L217, L229).
- 🟢 5.x 권장 = "모두 RDG 안 통합" — RDG 안 Pass + 외부 Pass 혼용 금지 (raw L216 함정 #3).
- 🟢 Shader Parameter Struct 는 `BEGIN_SHADER_PARAMETER_STRUCT` + `SHADER_PARAMETER_RDG_TEXTURE_SRV/UAV` 매크로로 Resource Read/Write 명시 — 누락 시 GPU race / 비결정 (raw L19, L40-44, L214).
- 🟢 Pass Type 4종 = Compute (`FComputeShaderUtils::AddPass`) / Raster (`FPixelShaderUtils::AddFullscreenPass`) / Custom (`GraphBuilder.AddPass`) / Async Compute (`ERDGPassFlags::AsyncCompute`) (raw L133-138).
- 🟢 Transient Resource = `GraphBuilder.CreateTexture(Desc, Name)` / `GraphBuilder.CreateBuffer(Desc, Name)` — 1 Frame 자동 lifetime (raw L92-107).
- 🟢 External Resource = `GraphBuilder.RegisterExternalTexture(PooledRenderTarget, Name)` — 기존 RHI 텍스처 RDG 통합 (raw L112-117).
- 🟢 `FRDGBlackboard` 는 Pass 간 데이터 교환 (5.x) — `Create<T>()` 저장 / `GetChecked<T>()` 조회. PassParameters 외 frame-wide 공유 (raw L166-184).
- 🟢 `ERDGPassFlags` 종류 = None / Raster / Compute / AsyncCompute / Copy / NeverCull — Queue 명시 의무 (raw L156-162).
- 🟡 Async Compute 의존성 = "Resource Read 끝난 후 Async Pass 시작" — 함정 #7 단문만 raw 명시 (L220), 정확한 fence 메커니즘은 외삽 (vault 근거: raw L220 · RHI fence semantics 외삽).

## 3. 함정 (raw §8 발췌 — 5대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Resource Read/Write 누락 → GPU race | `SHADER_PARAMETER_RDG_TEXTURE_SRV/UAV` 정확히 |
| 2 | 외부 텍스처 직접 변경 | `RegisterExternalTexture` 후 RDG Pass 안 |
| 3 | RDG_EVENT_SCOPE 누락 → 디버깅 불가 | 모든 함수 첫 줄 의무 |
| 4 | Lambda 안 `ENQUEUE_RENDER_COMMAND` 큐잉 | RDG Pass 콜백 안에서 직접 RHI 호출 |
| 5 | 5.x Lumen / Nanite + Custom Pass 충돌 | `ShouldExtendBoundary` 검사 + Hook 시점 정확 |

(raw L210-221 함정 8대 전체 참조)

## 4. 코드 예 (minimal Custom Compute Pass)

```cpp
BEGIN_SHADER_PARAMETER_STRUCT(FMyComputeParameters, )
    SHADER_PARAMETER(int32, OutputSize)
    SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutputTexture)
    SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D, InputTexture)
END_SHADER_PARAMETER_STRUCT()

void AddMyComputePass(FRDGBuilder& GraphBuilder, FRDGTextureRef In, FRDGTextureRef Out)
{
    RDG_EVENT_SCOPE(GraphBuilder, "MyComputePass");

    FMyComputeParameters* P = GraphBuilder.AllocParameters<FMyComputeParameters>();
    P->OutputSize    = Out->Desc.Extent.X;
    P->InputTexture  = GraphBuilder.CreateSRV(FRDGTextureSRVDesc(In));
    P->OutputTexture = GraphBuilder.CreateUAV(Out);

    TShaderMapRef<FMyComputeShader> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));
    FComputeShaderUtils::AddPass(GraphBuilder, RDG_EVENT_NAME("Dispatch"),
        Shader, P, FComputeShaderUtils::GetGroupCount(Out->Desc.Extent, FIntPoint(8, 8)));
}
```

## 5. Cross-link

- Parent: [[sources/ue-render-skill]]
- Sibling: [[sources/ue-render-shader]] (FGlobalShader / SHADER_PARAMETER) · [[sources/ue-render-sceneviewextension]] (RDG Hook 시점) · [[sources/ue-render-rhi]] (Pass 콜백 안 RHI 명령)
- 정책: [[sources/ue-ref-07-profilingscopeRule]] — `RDG_EVENT_SCOPE` Render 영역 변형
- Synthesis: [[synthesis/render-rdg-pass-standard-pattern]]

## 6. 신뢰도 매트릭스

| Claim | Tier | 근거 |
|-------|------|------|
| FRDGBuilder = Frame GPU 작업 컨테이너 | 🟢 | raw L9, L28 |
| RDG_EVENT_SCOPE 의무 | 🟢 | raw L18, L188-206 |
| 5.x = 모두 RDG 통합 | 🟢 | raw L216 |
| Pass Type 4종 | 🟢 | raw L133-138 |
| Transient / External Resource API | 🟢 | raw L92-117 |
| FRDGBlackboard frame-wide 공유 | 🟢 | raw L166-184 |
| ERDGPassFlags 6종 | 🟢 | raw L156-162 |
| Shader Parameter 매크로 = Read/Write 명시 | 🟢 | raw L40-44, L214 |
| 함정 8대 표 | 🟢 | raw L210-221 |
| Async Compute fence 정확 메커니즘 | 🟡 | raw L220 단문 + RHI fence 외삽 |
