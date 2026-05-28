---
type: synthesis
title: "Render RDG Pass 작성 표준 패턴 + SceneViewExtension hook"
slug: render-rdg-pass-standard-pattern
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/ue-render-rdg]]"
  - "[[sources/ue-render-sceneviewextension]]"
  - "[[sources/ue-render-postprocess]]"
  - "[[sources/ue-render-shader]]"
  - "[[sources/ue-render-meshdrawing]]"
  - "[[sources/ue-render-rhi]]"
  - "[[sources/ue-render-skill]]"
  - "[[sources/ue-render-material]]"
  - "[[sources/ue-measure-renderpostprocess-2026-05-08]]"
entities:
  - "[[entities/UMaterial]]"
  - "[[entities/UTexture]]"
concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
status: living
tags: [synthesis, render, rdg, sceneviewextension, postprocess, shader]
---

# Render RDG Pass 작성 표준 패턴 + SceneViewExtension hook

> 작성: 2026-05-11 · status: living

## 1. 정의 / Thesis

UE 5.x 의 *Custom Render Pass* 는 **3 계층 적층** 으로 구현된다: (1) **SceneViewExtension** 이 Engine 측 callback hook (Render Thread), (2) **FRDGBuilder** 가 Frame 의 GPU 작업 컨테이너, (3) **FGlobalShader** + USF 가 실제 GPU 코드. 진입점은 *항상* SceneViewExtension (한 단일 register call) — RDG / Shader 는 그 안에서 호출되는 도구. Material Domain=PostProcess 만으로 충분한 경우는 *코드 0* (Blendable + UPostProcessComponent 만) — 결정 트리의 첫 분기.

## 2. 핵심 매트릭스 — 어떤 도구가 어디서

| 도구 | 어디서 살아있나 | 책임 | 표준 entry |
| -- | -- | -- | -- |
| **FSceneViewExtensionBase** | Engine (Render Thread) | Engine callback hook 7종 (SetupViewFamily / PreRenderViewFamily_RT / PrePostProcessPass_RT 등) | `FSceneViewExtensions::NewExtension<MyExt>()` |
| **FRDGBuilder** | Frame 안 일시 (RT) | GPU 작업 컨테이너 + 의존성 그래프 + Resource Lifetime | `Builder.AddPass(...)` + `Builder.CreateTexture(...)` |
| **FRDGTextureRef / FRDGBufferRef** | Frame 내 (RT) | 일시적 GPU 리소스. RHI 직접 X | `Builder.CreateTexture(Desc, Name)` |
| **FGlobalShader** | Module load 부터 | Shader 정의 + permutation | `IMPLEMENT_GLOBAL_SHADER(Class, Path, Entry, Frequency)` |
| **USF 파일** | `Engine/Shaders/Public/` 또는 `Plugin/Shaders/` | HLSL-like GPU 코드 | `AddShaderSourceDirectoryMapping("/Plugin/MyMod", Dir)` |
| **Material Domain=PostProcess** | Editor 시점 컴파일됨 | Blendable on UPostProcessComponent — *코드 없이* PostProcess | UPostProcessComponent.Settings.AddBlendable |

## 2.1. 결정 트리

```
질문: PostProcess 효과 추가 필요?
  ├─ Material 로 충분? (color grading / tone curve / 화면 효과 단순)
  │   └─ Yes → Material Domain=PostProcess + UPostProcessComponent.Blendable.
  │           (코드 0, 가장 가벼움. [[sources/ue-render-material]] §Domain)
  │
  ├─ Custom Compute Pass 필요?
  │   └─ FSceneViewExtensionBase → PrePostProcessPass_RT → 
  │       FRDGBuilder.AddPass(Compute) + FGlobalShader.
  │       (주된 standard route)
  │
  └─ Custom Mesh Pass / G-Buffer 단계 진입?
      └─ FMeshPassProcessor + MeshDrawCommand (별도 sub-skill).
        [[sources/ue-render-meshdrawing]]
```

## 3. 표준 4단계 패턴 — Custom PostProcess Compute Pass

가장 흔한 케이스 — Frame buffer 받아 Compute Shader 로 변형해 Frame buffer 에 합성:

### 3.1. Shader 정의 (USF + C++ class)

```cpp
// MyEffectShader.h
class FMyEffectCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FMyEffectCS);
    SHADER_USE_PARAMETER_STRUCT(FMyEffectCS, FGlobalShader);

    BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
        SHADER_PARAMETER_RDG_TEXTURE(Texture2D, InputTex)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutputUAV)
        SHADER_PARAMETER(FIntPoint, ViewSize)
        SHADER_PARAMETER(float, Intensity)
    END_SHADER_PARAMETER_STRUCT()
};

IMPLEMENT_GLOBAL_SHADER(FMyEffectCS, "/Plugin/MyMod/Private/MyEffect.usf", "MainCS", SF_Compute);
```

USF 파일 (`Plugin/MyMod/Shaders/Private/MyEffect.usf`):

```hlsl
#include "/Engine/Public/Platform.ush"

[numthreads(8, 8, 1)]
void MainCS(uint3 DTid : SV_DispatchThreadID)
{
    if (any(DTid.xy >= ViewSize)) return;
    float4 Col = InputTex.Load(int3(DTid.xy, 0));
    OutputUAV[DTid.xy] = Col * Intensity;
}
```

### 3.2. SceneViewExtension 작성

```cpp
class FMyEffectSVE : public FSceneViewExtensionBase
{
public:
    using FSceneViewExtensionBase::FSceneViewExtensionBase;

    virtual void SubscribeToPostProcessingPass(EPostProcessingPass Pass, 
        FAfterPassCallbackDelegateArray& InOutPassCallbacks, bool bIsPassEnabled) override
    {
        if (Pass == EPostProcessingPass::Tonemap && bIsPassEnabled)
        {
            InOutPassCallbacks.Add(FAfterPassCallbackDelegate::CreateRaw(
                this, &FMyEffectSVE::AfterTonemap_RT));
        }
    }
    
    FScreenPassTexture AfterTonemap_RT(FRDGBuilder& Builder, 
        const FSceneView& View, const FPostProcessMaterialInputs& Inputs);
};
```

### 3.3. AfterTonemap_RT — RDG Pass 등록

```cpp
FScreenPassTexture FMyEffectSVE::AfterTonemap_RT(FRDGBuilder& Builder,
    const FSceneView& View, const FPostProcessMaterialInputs& Inputs)
{
    RDG_EVENT_SCOPE(Builder, "MyEffect");          // 🚨 Profiling 의무 ([[concepts/Profiling-Scope-Rule]])
    
    FRDGTextureRef Input = Inputs.GetInput(EPostProcessMaterialInput::SceneColor).Texture;
    FRDGTextureRef Output = Builder.CreateTexture(Input->Desc, TEXT("MyEffect.Output"));

    auto* Parameters = Builder.AllocParameters<FMyEffectCS::FParameters>();
    Parameters->InputTex = Input;
    Parameters->OutputUAV = Builder.CreateUAV(Output);
    Parameters->ViewSize = View.UnconstrainedViewRect.Size();
    Parameters->Intensity = 1.2f;

    TShaderMapRef<FMyEffectCS> Shader(GetGlobalShaderMap(View.GetFeatureLevel()));
    FComputeShaderUtils::AddPass(Builder, RDG_EVENT_NAME("MyEffectCS"),
        Shader, Parameters, FComputeShaderUtils::GetGroupCount(View.UnconstrainedViewRect.Size(), FIntPoint(8, 8)));

    return FScreenPassTexture(Output);
}
```

### 3.4. Module Startup 등록

```cpp
void FMyModModule::StartupModule()
{
    AddShaderSourceDirectoryMapping(TEXT("/Plugin/MyMod"),
        FPaths::Combine(IPluginManager::Get().FindPlugin(TEXT("MyMod"))->GetBaseDir(), TEXT("Shaders")));
    
    SceneViewExtension = FSceneViewExtensions::NewExtension<FMyEffectSVE>();
}
```

이 4단계로 — **GameThread 코드 0 / 단 1 hook subscribe / Frame 별 자동 Pass culling**. RDG 가 의존성 그래프로 lifetime 처리.

## 4. 함정 / 열린 질문

### 4.1. 함정 (실전 6건)

1. **_RenderThread hook 에서 UObject 접근** — GC 안전성 위반. RT 진입 시 *GameThread 측에서 미리 복사한 POD struct* 만. ([[concepts/Editor-Only-4-Tier-Separation]] 의 thread 분리 원칙 동일 적용)
2. **PassParameters 의 `BEGIN_SHADER_PARAMETER_STRUCT` 누락** — 컴파일 자체 안 됨. UAV / SRV / sampler / uniform 모두 매크로로 명시.
3. **ShouldCompilePermutation 분기 안 함** — 모든 셰이더 변형 컴파일 → DDC 빌드 시간 폭증. 플랫폼/featurelevel 별 cull 의무.
4. **`AddShaderSourceDirectoryMapping` 누락** — `IMPLEMENT_GLOBAL_SHADER` 의 USF 경로 못 찾음 → Module startup 에서 register 의무.
5. **`RDG_EVENT_SCOPE` 누락** — RenderDoc / Insights 에서 Pass 식별 불가 ([[concepts/Profiling-Scope-Rule]] 위반). RDG 자체 의무는 아니지만 *디버깅 가시성* 위해 의무화.
6. **PSO Precache 5.x 미고려** — 첫 frame 에 Shader 컴파일 hitching. `bIsPSOPrecache` warm-up 의무 (Cooked Build 출시 시).

### 4.2. 열린 질문

- [ ] Vulkan / Mobile 의 RDG 차이 — `RHI_RAYTRACING` 제외 / GroupSize 한계 / Tile-based 최적화 ([[sources/ue-render-vulkan]] / [[sources/ue-render-mobile]] cross-check 필요)
- [ ] VR Stereo (Multi-View Instanced) 와 SVE hook 의 결합 — Eye 별 RDG Pass 가 자동 복제되나? ([[sources/ue-render-vr]])
- [ ] Lumen / Nanite Pass 와의 hook 순서 — `PrePostProcessPass_RT` 가 Lumen output 후인가 전인가? ([[sources/ue-render-lumennanite]])
- [ ] [[entities/UMaterial]] Domain=PostProcess vs FGlobalShader 의 성능 trade-off — Blendable 의 비용
- [ ] AsyncCompute 경로 — `FRDGPass::Type::AsyncCompute` 사용 시 dependency barrier 자동 정합?

## 5. 관련

### 핵심 sources (필수)

- [[sources/ue-render-rdg]] — RDG (FRDGBuilder + FRDGPass + 의존성 그래프)
- [[sources/ue-render-sceneviewextension]] — 7 Hook + Register 패턴
- [[sources/ue-render-postprocess]] — PostProcess Pipeline + Custom Pass 진입점
- [[sources/ue-render-shader]] — FGlobalShader + USF + Permutation
- [[sources/ue-render-skill]] — Render 카테고리 main

### 보조 sources

- [[sources/ue-render-meshdrawing]] — Mesh Pass 별도 경로
- [[sources/ue-render-rhi]] — 직접 RHI (RDG 미사용 시)
- [[sources/ue-render-material]] — Material Domain=PostProcess 의 Blendable 경로
- [[sources/ue-measure-renderpostprocess-2026-05-08]] — vault 효과 측정 (RenderPostProcess with vs no wiki A/B)

### 관련 concept

- [[concepts/Profiling-Scope-Rule]] — RDG_EVENT_SCOPE 의무
- [[concepts/Editor-Only-4-Tier-Separation]] — Thread 분리 원칙 (GT / RT)
- [[concepts/Cooked-vs-Uncooked]] — PSO Precache 5.x 시점

### 평가 호환

- [[sources/ue-agent-evaluator]] — 본 패턴 적용 시 Performance 35% / Memory 25% 채점
- [[sources/ue-ref-07-profilingscopeRule]] — RDG_EVENT_SCOPE 의 정밀판
