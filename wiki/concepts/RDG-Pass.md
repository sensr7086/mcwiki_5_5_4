---
type: concept
title: "RDG Pass (Render Dependency Graph Pass 패턴)"
aliases: ["RDG Pass", "FRDGPass", "AddPass lambda"]
sources:
  - "[[sources/ue-render-rdg]]"
  - "[[sources/ue-render-shader]]"
  - "[[sources/ue-render-sceneviewextension]]"
  - "[[synthesis/render-rdg-pass-standard-pattern]]"
related_concepts:
  - "[[concepts/Render-Thread-Safety]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [render, gpu, rdg, pass, lambda]
last_updated: 2026-05-13
---

# RDG Pass

## 정의

UE 5.x Render Dependency Graph 의 **단일 GPU 작업 단위**. `FRDGBuilder::AddPass` (또는 헬퍼) 로 등록되며, *Parameter Struct* (`SHADER_PARAMETER_RDG_*` 매크로) 가 Read/Write Resource 명시. RDG 가 의존성 그래프 자동 빌드 → Pass Culling + 동시 실행 + Resource Lifetime 자동.

## Pass Type 4종

| Type | API | 용도 |
|------|-----|------|
| Compute | `FComputeShaderUtils::AddPass(...)` | Compute Shader Dispatch |
| Raster (Fullscreen) | `FPixelShaderUtils::AddFullscreenPass(...)` | PostProcess 풀스크린 |
| Custom | `GraphBuilder.AddPass(..., ERDGPassFlags::Raster\|Compute, lambda)` | 자유 lambda |
| Async Compute | `GraphBuilder.AddPass(..., ERDGPassFlags::AsyncCompute, lambda)` | Async Queue |

## Lambda 캡처 규약

```cpp
// ✅ 안전 — Pass parameters 는 GraphBuilder 가 lifetime 보장
FMyParameters* P = GraphBuilder.AllocParameters<FMyParameters>();
P->Input = GraphBuilder.CreateSRV(...);

GraphBuilder.AddPass(
    RDG_EVENT_NAME("MyPass"),
    P,                                       // 자동 Resource 추적
    ERDGPassFlags::Compute,
    [P, ShaderRef](FRHIComputeCommandList& RHICmdList)
    {
        // lambda 안에서 RHI 직접 호출 (RHI Thread 동기)
        FComputeShaderUtils::Dispatch(RHICmdList, ShaderRef, *P, GroupCount);
    });
```

### 캡처 금지 항목

- UObject* / TWeakObjectPtr (GT 만)
- TArray<T>& by ref (lifetime 위험) — 값 복사만
- FString (refcount race) — FName 또는 stack literal
- Outer state 가변 → 캡처 시점 snapshot 만

[[concepts/Render-Thread-Safety]] §캡처 규약 참조.

## Resource 명시 의무

Pass parameters 안 모든 RDG resource 는 *접근 패턴* 명시:

```cpp
BEGIN_SHADER_PARAMETER_STRUCT(FMyParameters, )
    SHADER_PARAMETER(int32, Size)
    SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D, InTex)        // 읽기
    SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, Out) // 쓰기
END_SHADER_PARAMETER_STRUCT()
```

누락 시 RDG 가 의존성 파악 못함 → GPU race 비결정 ([[sources/ue-render-rdg]] §3 함정 #1).

## 표준 패턴 — SVE Hook + Pass

```cpp
void FMySVE::PrePostProcessPass_RenderThread(
    FRDGBuilder& GraphBuilder, const FSceneView& View,
    const FPostProcessingInputs& Inputs)
{
    RDG_EVENT_SCOPE(GraphBuilder, "MyCustomPP");   // 의무

    FRDGTextureRef SceneColor =
        (*Inputs.SceneTextures)->GetContents()->SceneColorTexture;

    AddMyComputePass(GraphBuilder, SceneColor);    // 본 concept 적용
}
```

[[synthesis/render-rdg-pass-standard-pattern]] = SVE Hook + RDG Pass + FGlobalShader 3계층 통합 가이드.

## 함정

- ❌ Pass parameters 외 RDG resource 접근 = GPU race
- ❌ Legacy `IPooledRenderTarget` 직접 변경 — `RegisterExternalTexture` 후 Pass 안에서만
- ❌ `RDG_EVENT_SCOPE` 누락 → Insights / RenderDoc hierarchy 깨짐
- ❌ Lambda 안 `ENQUEUE_RENDER_COMMAND` 중첩 큐잉 → RDG Pass 콜백 안에서 직접 RHI

## Cross-link

- 권위 source: [[sources/ue-render-rdg]]
- 페어: [[sources/ue-render-shader]] (Parameter Struct 매크로) · [[sources/ue-render-sceneviewextension]] (Hook 시점)
- 통합 synthesis: [[synthesis/render-rdg-pass-standard-pattern]]
- 정책: [[concepts/Render-Thread-Safety]] (캡처 규약) · [[concepts/Profiling-Scope-Rule]] (`RDG_EVENT_SCOPE`)
