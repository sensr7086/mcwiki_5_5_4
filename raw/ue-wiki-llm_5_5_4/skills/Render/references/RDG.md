---
name: render-rdg
description: Render Dependency Graph (5.x 표준) — FRDGBuilder + FRDGTexture + FRDGBufferRef + FRDGPass + FRDGBlackboard. 자동 의존성 / Resource Lifetime / Pass Culling / Async Compute. Custom PostProcess / Compute Shader / Custom Pass 작성 표준.
---

# Render/RDG — Render Dependency Graph (5.x 표준)

> **위치**: `Engine/Source/Runtime/RenderCore/Public/RenderGraph*.h` (10+ 헤더)
> **핵심**: `FRDGBuilder` (47:`RenderGraphBuilder.h`) — 모든 5.x Render 코드의 진입점.
> **요지**: 5.x 의 Pass 등록 + 자동 의존성 분석 + Resource Lifetime 자동 관리 + Async Compute 표준.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | 모든 RDG Pass 첫 줄 `RDG_EVENT_SCOPE` 의무 |
| 🚨 의존성 명시 | Resource Read/Write 명확 — 누락 시 GPU race / 비결정 |
| 🚨 Lifetime | RDG Resource = 자동 (외부 등록 = `RegisterExternalTexture`) |

---

## 1. 5 핵심 클래스

| 클래스 | 책임 | 헤더 |
|--------|------|------|
| `FRDGBuilder` | 그래프 빌더 (모든 Pass 등록) | `RenderGraphBuilder.h:47` |
| `FRDGTextureRef` | 텍스처 핸들 | `RenderGraphResources.h` |
| `FRDGBufferRef` | 버퍼 핸들 | `RenderGraphResources.h` |
| `FRDGPass` | Pass 추상 | `RenderGraphPass.h` |
| `FRDGBlackboard` | Pass 간 데이터 교환 (5.x) | `RenderGraphBlackboard.h` |

---

## 2. 표준 사용 패턴 — Custom Compute Pass

```cpp
// 1. Shader Parameter Struct 정의
BEGIN_SHADER_PARAMETER_STRUCT(FMyComputeParameters, )
    SHADER_PARAMETER(int32, OutputSize)
    SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutputTexture)
    SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D, InputTexture)
END_SHADER_PARAMETER_STRUCT()

// 2. Compute Shader 클래스
class FMyComputeShader : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FMyComputeShader);
    SHADER_USE_PARAMETER_STRUCT(FMyComputeShader, FGlobalShader);
    using FParameters = FMyComputeParameters;

    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
    {
        return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
    }
};

IMPLEMENT_GLOBAL_SHADER(FMyComputeShader, "/Engine/Private/MyShader.usf", "MainCS", SF_Compute);

// 3. RDG 사용 (Render Thread)
void AddMyComputePass(FRDGBuilder& GraphBuilder, FRDGTextureRef InputTex, FRDGTextureRef OutputTex)
{
    RDG_EVENT_SCOPE(GraphBuilder, "MyComputePass");

    // Shader 파라미터 채움
    FMyComputeParameters* Parameters = GraphBuilder.AllocParameters<FMyComputeParameters>();
    Parameters->OutputSize = OutputTex->Desc.Extent.X;
    Parameters->InputTexture = GraphBuilder.CreateSRV(FRDGTextureSRVDesc(InputTex));
    Parameters->OutputTexture = GraphBuilder.CreateUAV(OutputTex);

    // Compute Shader 가져오기
    TShaderMapRef<FMyComputeShader> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));

    // Dispatch
    FComputeShaderUtils::AddPass(
        GraphBuilder,
        RDG_EVENT_NAME("MyComputeDispatch"),
        Shader,
        Parameters,
        FComputeShaderUtils::GetGroupCount(OutputTex->Desc.Extent, FIntPoint(8, 8))
    );
}
```

---

## 3. RDG Resource 종류

### 3.1 Transient Resource (RDG 자체 관리)

```cpp
// Texture 생성 (1 Frame 만 유지)
FRDGTextureDesc Desc = FRDGTextureDesc::Create2D(
    FIntPoint(1920, 1080),
    PF_FloatRGBA,
    FClearValueBinding::Black,
    TexCreate_RenderTargetable | TexCreate_ShaderResource | TexCreate_UAV
);
FRDGTextureRef MyTex = GraphBuilder.CreateTexture(Desc, TEXT("MyTexture"));

// Buffer 생성
FRDGBufferRef MyBuf = GraphBuilder.CreateBuffer(
    FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f), 1024),
    TEXT("MyBuffer")
);
```

### 3.2 External Resource (외부 등록)

```cpp
// 기존 RHI Texture 를 RDG 에 등록
FRDGTextureRef ExternalTex = GraphBuilder.RegisterExternalTexture(
    PooledRenderTarget,   // 외부 IPooledRenderTarget
    TEXT("ExternalTexture")
);
```

### 3.3 SRV / UAV 생성

```cpp
// SRV (Read-only)
FRDGTextureSRVRef SRV = GraphBuilder.CreateSRV(FRDGTextureSRVDesc(Tex));

// UAV (Read/Write)
FRDGTextureUAVRef UAV = GraphBuilder.CreateUAV(FRDGTextureUAVDesc(Tex));
```

---

## 4. Pass Type

| Pass Type | 용도 | API |
|-----------|------|-----|
| **Compute** | GPU 시뮬레이션 | `FComputeShaderUtils::AddPass` |
| **Raster** | 픽셀 셰이더 (PostProcess 등) | `FPixelShaderUtils::AddFullscreenPass` |
| **Custom** | 직접 RHI 명령 | `GraphBuilder.AddPass(...)` |
| **Async Compute** | 병렬 Compute (Graphics 와 동시) | `ERDGPassFlags::AsyncCompute` |

---

## 5. ERDGPassFlags 표준

```cpp
GraphBuilder.AddPass(
    RDG_EVENT_NAME("MyPass"),
    Parameters,
    ERDGPassFlags::Compute,                  // Compute Queue
    [Parameters](FRDGAsyncTask, FRHIComputeCommandList& RHICmdList)
    {
        // RHI 직접 명령
    }
);

// Flag 종류
ERDGPassFlags::None
ERDGPassFlags::Raster                        // 그래픽스 큐
ERDGPassFlags::Compute                       // 컴퓨트 큐
ERDGPassFlags::AsyncCompute                  // 비동기 컴퓨트 (Graphics 병렬)
ERDGPassFlags::Copy                          // 복사 큐
ERDGPassFlags::NeverCull                     // 항상 실행 (debug)
```

---

## 6. FRDGBlackboard — Pass 간 데이터 교환 (5.x)

```cpp
// 데이터 구조 정의
struct FMyData
{
    FRDGTextureRef SharedTexture;
    int32 SomeValue;
};

// Pass A — 데이터 저장
FMyData& Data = GraphBuilder.Blackboard.Create<FMyData>();
Data.SharedTexture = MyTex;
Data.SomeValue = 42;

// Pass B — 다른 위치에서 데이터 읽기
const FMyData& Data = GraphBuilder.Blackboard.GetChecked<FMyData>();
FRDGTextureRef Tex = Data.SharedTexture;
```

---

## 7. RDG_EVENT_SCOPE (프로파일링 의무)

```cpp
void MyRenderFunction(FRDGBuilder& GraphBuilder)
{
    RDG_EVENT_SCOPE(GraphBuilder, "MyRenderFunction");        // ⭐ 의무

    {
        RDG_EVENT_SCOPE(GraphBuilder, "Sub-Pass-1");
        AddMyPass1(GraphBuilder);
    }
    {
        RDG_EVENT_SCOPE(GraphBuilder, "Sub-Pass-2");
        AddMyPass2(GraphBuilder);
    }
}
```

→ Insights / RenderDoc 에서 명명된 hierarchy 로 표시.

---

## 8. 함정 & 안티패턴 (8대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Resource Read/Write 누락 → GPU race | `SHADER_PARAMETER_RDG_TEXTURE_SRV/UAV` 정확히 |
| 2 | RDG 외부에서 텍스처 직접 변경 | `RegisterExternalTexture` 후 RDG Pass 안 |
| 3 | RDG 안 Pass + 외부 Pass 혼용 | 모두 RDG 안 통합 (5.x 권장) |
| 4 | RDG_EVENT_SCOPE 누락 → 디버깅 불가 | 모든 함수 첫 줄 의무 |
| 5 | Compute Pass + Raster Pass 의존성 명시 X | `ERDGPassFlags` 정확 |
| 6 | Lambda 안 ENQUEUE_RENDER_COMMAND 큐잉 | RDG Pass 콜백 안에서 직접 RHI 호출 |
| 7 | Async Compute + Resource race | Resource Read 끝난 후 Async Pass 시작 |
| 8 | 5.x Lumen / Nanite 와 Custom Pass 충돌 | `ShouldExtendBoundary` 검사 + Hook 시점 정확 |

---

## 9. 체크리스트

- [ ] FRDGBuilder 사용 (Legacy IPooledRenderTarget 만 X)
- [ ] Resource Read/Write = SHADER_PARAMETER_RDG_TEXTURE_SRV/UAV 정확
- [ ] RDG_EVENT_SCOPE 첫 줄 의무
- [ ] ERDGPassFlags 정확 (Compute / AsyncCompute 명시)
- [ ] External Resource = RegisterExternalTexture 의무
- [ ] FRDGBlackboard 활용 (Pass 간 데이터 교환)
- [ ] Async Compute 의존성 검사
- [ ] FComputeShaderUtils / FPixelShaderUtils 우선 사용

---

## 10. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- [`Render/references/Shader.md`](../Shader/SKILL.md) — IMPLEMENT_GLOBAL_SHADER + Permutation
- [`Render/references/SceneViewExtension.md`](../SceneViewExtension/SKILL.md) — RDG Hook 시점
- [`Render/references/RHI.md`](../RHI/SKILL.md) — Pass 콜백 안 RHI 명령

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. FRDGBuilder + Texture/Buffer/SRV/UAV + 5 Pass Type + ERDGPassFlags + Blackboard + RDG_EVENT_SCOPE + 함정 8대. |
