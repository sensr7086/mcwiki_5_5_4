---
name: render-shader
description: Global / Material / Compute Shader 작성 표준. FGlobalShader + IMPLEMENT_GLOBAL_SHADER + SHADER_PARAMETER_STRUCT + FShaderPermutationDomain + ShouldCompilePermutation. USF 파일 위치 등록 + Module StartupModule + AddShaderSourceDirectoryMapping. Cooked Build 컴파일 안전.
---

# Render/Shader — Global / Material / Compute Shader 작성

> **위치**: `Engine/Source/Runtime/RenderCore/Public/Shader.h` + `GlobalShader.h` + `ShaderParameterStruct.h` + `ShaderPermutation.h` + `MaterialShader.h`
> **요지**: GPU 셰이더 작성의 5.x 표준 — Permutation + Parameter Struct + DDC 캐시 + Cooked PSO.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 ShouldCompilePermutation | 의무 — 누락 시 Cooked Build 안 모든 플랫폼 컴파일 (시간 폭증) |
| 🚨 Shader Path 등록 | `AddShaderSourceDirectoryMapping` — Module StartupModule 안 의무 |
| 🚨 Cooked Build | 모든 사용 Permutation 사전 컴파일 의무 |

---

## 1. Shader 종류

| 종류 | 베이스 | 용도 |
|------|--------|------|
| **Global Shader** | `FGlobalShader` | PostProcess / Custom Compute / 일반 풀스크린 |
| **Material Shader** | `FMaterialShader` | UMaterial 어셋 컴파일 결과 |
| **MeshMaterial Shader** | `FMeshMaterialShader` | Mesh + Material (UMaterial × Vertex Factory) |
| **Compute Shader** | `FGlobalShader` (Pixel/Vertex/Compute 통합 베이스) | GPU 시뮬 / 후처리 |

---

## 2. Global Shader 표준 패턴 (가장 흔함)

### 2.1 Shader Class 정의

```cpp
// MyComputeShader.h
#pragma once
#include "GlobalShader.h"
#include "ShaderParameterStruct.h"

class FMyComputeShader : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FMyComputeShader);
    SHADER_USE_PARAMETER_STRUCT(FMyComputeShader, FGlobalShader);

    BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
        SHADER_PARAMETER(int32, OutputSize)
        SHADER_PARAMETER(float, Strength)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutputTexture)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D, InputTexture)
    END_SHADER_PARAMETER_STRUCT()

    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
    {
        return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
    }

    static void ModifyCompilationEnvironment(const FGlobalShaderPermutationParameters& Parameters,
                                              FShaderCompilerEnvironment& OutEnvironment)
    {
        FGlobalShader::ModifyCompilationEnvironment(Parameters, OutEnvironment);
        OutEnvironment.SetDefine(TEXT("THREAD_GROUP_SIZE"), 8);
    }
};

// MyComputeShader.cpp
IMPLEMENT_GLOBAL_SHADER(FMyComputeShader, "/Plugin/MyPlugin/MyShader.usf", "MainCS", SF_Compute);
```

### 2.2 USF 파일 (HLSL)

```hlsl
// /Plugin/MyPlugin/MyShader.usf
#include "/Engine/Public/Platform.ush"

#ifndef THREAD_GROUP_SIZE
#define THREAD_GROUP_SIZE 8
#endif

int OutputSize;
float Strength;
RWTexture2D<float4> OutputTexture;
Texture2D InputTexture;

[numthreads(THREAD_GROUP_SIZE, THREAD_GROUP_SIZE, 1)]
void MainCS(uint3 DispatchThreadId : SV_DispatchThreadID)
{
    if (DispatchThreadId.x >= OutputSize || DispatchThreadId.y >= OutputSize) return;

    float4 InColor = InputTexture.Load(int3(DispatchThreadId.xy, 0));
    OutputTexture[DispatchThreadId.xy] = InColor * Strength;
}
```

---

## 3. Shader Path 등록 (Module StartupModule 의무)

```cpp
// MyPluginModule.cpp
#include "Modules/ModuleManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Paths.h"
#include "ShaderCore.h"

class FMyPluginModule : public IModuleInterface
{
public:
    virtual void StartupModule() override
    {
        // ⭐ 의무 — Shader 경로 등록 (런타임)
        FString PluginShaderDir = FPaths::Combine(
            IPluginManager::Get().FindPlugin(TEXT("MyPlugin"))->GetBaseDir(),
            TEXT("Shaders")
        );
        AddShaderSourceDirectoryMapping(TEXT("/Plugin/MyPlugin"), PluginShaderDir);
    }

    virtual void ShutdownModule() override {}
};

IMPLEMENT_MODULE(FMyPluginModule, MyPlugin)
```

> **누락 시**: USF 파일 못 찾음 → IMPLEMENT_GLOBAL_SHADER 컴파일 X.

---

## 4. Shader Permutation (FShaderPermutationDomain)

복수 변형 (Quality / Feature / Platform) 시 사용.

### 4.1 정의

```cpp
class FMyShader : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FMyShader);
    SHADER_USE_PARAMETER_STRUCT(FMyShader, FGlobalShader);

    // Permutation 정의
    class FQualityDim : SHADER_PERMUTATION_INT("QUALITY_LEVEL", 4);  // 0~3
    class FUseHDRDim : SHADER_PERMUTATION_BOOL("USE_HDR");

    using FPermutationDomain = TShaderPermutationDomain<FQualityDim, FUseHDRDim>;
};

// 사용 시
FMyShader::FPermutationDomain PermutationVector;
PermutationVector.Set<FMyShader::FQualityDim>(2);
PermutationVector.Set<FMyShader::FUseHDRDim>(true);

TShaderMapRef<FMyShader> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel), PermutationVector);
```

### 4.2 USF 안 분기

```hlsl
#if QUALITY_LEVEL == 0
    // 저사양
#elif QUALITY_LEVEL >= 2
    // 고사양
#endif

#if USE_HDR
    // HDR 분기
#endif
```

---

## 5. SHADER_PARAMETER 종류

```cpp
BEGIN_SHADER_PARAMETER_STRUCT(FMyParams, )
    SHADER_PARAMETER(int32, IntValue)
    SHADER_PARAMETER(float, FloatValue)
    SHADER_PARAMETER(FVector4f, VectorValue)
    SHADER_PARAMETER(FMatrix44f, Matrix)
    SHADER_PARAMETER_TEXTURE(Texture2D, MyTexture)                       // 정적 텍스처
    SHADER_PARAMETER_SAMPLER(SamplerState, MySampler)                    // 샘플러
    SHADER_PARAMETER_RDG_TEXTURE(Texture2D, RDGTex)                      // RDG 텍스처
    SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D, RDGTexSRV)               // SRV
    SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, RDGTexUAV)     // UAV
    SHADER_PARAMETER_RDG_BUFFER_SRV(Buffer<float4>, RDGBufSRV)
    SHADER_PARAMETER_RDG_BUFFER_UAV(RWBuffer<float4>, RDGBufUAV)
    SHADER_PARAMETER_STRUCT_REF(FMyStruct, MyStruct)                     // 구조체 참조
    SHADER_PARAMETER_STRUCT_INCLUDE(FViewUniformShaderParameters, View)  // View 포함
END_SHADER_PARAMETER_STRUCT()
```

---

## 6. Compute Shader Dispatch

```cpp
// FComputeShaderUtils 헬퍼 사용
FComputeShaderUtils::AddPass(
    GraphBuilder,
    RDG_EVENT_NAME("MyComputePass"),
    Shader,
    Parameters,
    FComputeShaderUtils::GetGroupCount(OutputSize, FIntPoint(8, 8))   // 8×8 thread group
);

// 또는 직접 RDG Pass
GraphBuilder.AddPass(
    RDG_EVENT_NAME("MyDispatch"),
    Parameters,
    ERDGPassFlags::Compute,
    [Parameters, Shader, GroupCount](FRDGAsyncTask, FRHIComputeCommandList& RHICmdList)
    {
        FComputeShaderUtils::Dispatch(RHICmdList, Shader, *Parameters, GroupCount);
    }
);
```

---

## 7. Pixel Shader (PostProcess)

```cpp
// 풀스크린 픽셀 셰이더
class FMyPostProcessPS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FMyPostProcessPS);
    SHADER_USE_PARAMETER_STRUCT(FMyPostProcessPS, FGlobalShader);

    BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D, InputTexture)
        SHADER_PARAMETER_SAMPLER(SamplerState, InputSampler)
        SHADER_PARAMETER(float, Strength)
        RENDER_TARGET_BINDING_SLOTS()
    END_SHADER_PARAMETER_STRUCT()

    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
    {
        return true;
    }
};

IMPLEMENT_GLOBAL_SHADER(FMyPostProcessPS, "/Plugin/MyPlugin/MyPostProcess.usf", "MainPS", SF_Pixel);

// 사용
FPixelShaderUtils::AddFullscreenPass(
    GraphBuilder,
    GlobalShaderMap,
    RDG_EVENT_NAME("MyPostProcess"),
    Shader,
    Parameters,
    Viewport
);
```

---

## 8. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | ShouldCompilePermutation 누락 | `return IsFeatureLevelSupported(...)` 의무 |
| 2 | Shader Path 등록 누락 | Module StartupModule 안 `AddShaderSourceDirectoryMapping` |
| 3 | Permutation 폭증 (× 8 변수 = 256배) | 정말 필요한 변형만 |
| 4 | USF 안 SHADER_PARAMETER 누락 | C++ Parameter Struct 와 USF 변수명 / 타입 정확 일치 |
| 5 | Cooked Build 안 컴파일 (DDC 미스) | DDC 셰어드 스토리지 + ShaderPipelineCache |
| 6 | Mobile 컴파일 누락 | `IsMobilePlatform` 검사 분리 |
| 7 | RDG 외부 Shader Bind | RDG Pass 안에서만 사용 |
| 8 | ENV 변수 충돌 | ModifyCompilationEnvironment 안 SetDefine |
| 9 | Shader Hot Reload (개발 중) | RecompileShaders 콘솔 명령 |
| 10 | SF_Compute / SF_Pixel 잘못 지정 | IMPLEMENT_GLOBAL_SHADER 마지막 인자 정확히 |

---

## 9. 체크리스트

- [ ] DECLARE_GLOBAL_SHADER + IMPLEMENT_GLOBAL_SHADER 페어
- [ ] SHADER_USE_PARAMETER_STRUCT 의무
- [ ] ShouldCompilePermutation 의무 (플랫폼 / FeatureLevel)
- [ ] ModifyCompilationEnvironment (Define 추가)
- [ ] Shader Path 등록 (Module StartupModule)
- [ ] USF 변수명 / 타입 = C++ Parameter Struct 정확 일치
- [ ] Permutation = 정말 필요한 변형만 (폭증 회피)
- [ ] Cooked Build 검증 (Cook 후 DDC 캐시)
- [ ] FComputeShaderUtils / FPixelShaderUtils 헬퍼 우선

---

## 10. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- [`Render/references/RDG.md`](./RDG.md) — Shader Dispatch (RDG Pass 안)
- [`Render/references/Material.md`](./Material.md) — Material 컴파일 결과 (FMaterialShader)
- ⭐ [`Render/references/MaterialExpression.md`](./MaterialExpression.md) — **Custom Material Expression 깊이** (UMaterialExpression + FMaterialCompiler 578 메소드 + Substrate 5.x)
- [`Render/references/RHI.md`](./RHI.md) — RHI Shader Resource
- [`Build/SKILL.md`](../../Build/SKILL.md) — Shader Cooking + DDC

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. Global / Material / Compute Shader + IMPLEMENT_GLOBAL_SHADER + SHADER_PARAMETER 종류 + Permutation Domain + Compute Dispatch + Pixel Shader + 함정 10대. |
