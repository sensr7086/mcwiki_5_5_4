---
type: source
title: "UE Render — Shader sub-skill (Global / Material / Compute Shader)"
slug: ue-render-shader
source_path: raw/ue-wiki-llm/skills/Render/references/Shader.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-28
audit_5_5_4: pass-minor-numeric  # 2026-05-28 Phase 2-B priority audit
related_entities: []
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, render, gpu, shader, slim-card]
citation_disclosure: "🟢 18 / 🟡 4 / 🔴 2 · 보너스 발견 3건 (PermutationDomain 매크로 정밀화 / SHADER_PARAMETER_STRUCT_INCLUDE 누락 / PSO Precache 근거 출처 sibling 이전)"
---

# UE Render — Shader (Global / Material / Compute)

> Source: [[raw/ue-wiki-llm/skills/Render/references/Shader.md]] (304L)
> Parent: [[sources/ue-render-skill]] · 페어: [[sources/ue-render-material]] · [[sources/ue-render-materialexpression]] · [[sources/ue-render-rdg]]
> Synthesis: [[synthesis/render-rdg-pass-standard-pattern]] (SVE + RDG + FGlobalShader 3계층 통합)

## 1. Summary

🟢 GPU 셰이더 작성의 **5.x 표준** — `FGlobalShader` 자손 + `DECLARE_GLOBAL_SHADER` / `IMPLEMENT_GLOBAL_SHADER` 페어 + `SHADER_USE_PARAMETER_STRUCT` + `BEGIN/END_SHADER_PARAMETER_STRUCT` + `TShaderPermutationDomain<>` + `ShouldCompilePermutation` 의무. USF 파일 (`.usf`, HLSL-like) 은 Module `StartupModule` 안 `AddShaderSourceDirectoryMapping("/Plugin/X", Dir)` 로 가상 경로 등록 후 `IMPLEMENT_GLOBAL_SHADER` 의 3번째 인자로 참조 (raw L70, L119). 🟡 5.x PSO Precache (`r.PSOPrecache=1`) 는 Material / MeshDraw 측 cooked-build 표준 — Shader.md 본문은 §8 L268 에서 "Cooked Build 안 컴파일 (DDC 미스)" 로만 표현 ([[sources/ue-render-material]] L93 가 권위 출처).

## 2. Key claims

- 🟢 **Shader 종류 3** — `FGlobalShader` (Global / Compute / Pixel / Vertex 통합 베이스) · `FMaterialShader` (UMaterial 컴파일 결과) · `FMeshMaterialShader` (Material × Vertex Factory) (raw L26-30).
- 🟢 **Global Shader 매크로 페어** — `DECLARE_GLOBAL_SHADER(Class)` (헤더) + `IMPLEMENT_GLOBAL_SHADER(Class, "/VirtualPath/File.usf", "EntryFunc", SF_Compute|SF_Pixel|SF_Vertex)` (cpp, raw L46, L70). 마지막 인자 잘못 = 컴파일 X (raw L273 함정 #10).
- 🟢 **Parameter Struct 매크로** — `SHADER_USE_PARAMETER_STRUCT(FMyShader, FGlobalShader)` 의무 + `BEGIN_SHADER_PARAMETER_STRUCT(FParameters, ) ... END_SHADER_PARAMETER_STRUCT()` 안에서 `SHADER_PARAMETER(int32, ...)` / `SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, ...)` / `SHADER_PARAMETER_RDG_TEXTURE_SRV` / `SHADER_PARAMETER_TEXTURE` / `SHADER_PARAMETER_SAMPLER` / `SHADER_PARAMETER_RDG_BUFFER_SRV|UAV` / `SHADER_PARAMETER_STRUCT_REF` / `SHADER_PARAMETER_STRUCT_INCLUDE(FViewUniformShaderParameters, View)` 사용 (raw L47-54, L178-192). USF 변수명 / 타입 = C++ 정확 일치 (raw L267 함정 #4).
- 🟢 **USF 파일 경로** — `/Engine/Shaders/Public/` 또는 Plugin 가상 경로 (`/Plugin/MyPlugin/...`). HLSL 안 `#include "/Engine/Public/Platform.ush"` 첫 줄 (raw L77).
- 🟢 **Shader Path 등록 의무** — Module `StartupModule()` 안 `FString Dir = FPaths::Combine(IPluginManager::Get().FindPlugin("MyPlugin")->GetBaseDir(), TEXT("Shaders")); AddShaderSourceDirectoryMapping(TEXT("/Plugin/MyPlugin"), Dir);` (raw L112-120). 누락 시 USF 못 찾아 `IMPLEMENT_GLOBAL_SHADER` 자체 실패 (raw L128).
- 🟢 **Permutation Domain — 2 레벨 매크로** — ① `class FQualityDim : SHADER_PERMUTATION_INT("QUALITY_LEVEL", 4);` (0~3) / `SHADER_PERMUTATION_BOOL("USE_HDR")` 매크로로 *dim 클래스* 정의 → ② `using FPermutationDomain = TShaderPermutationDomain<FQualityDim, FUseHDRDim>;` 템플릿 결합. 사용 시 `PermutationVector.Set<FMyShader::FQualityDim>(2);` 후 `TShaderMapRef<FMyShader>(GlobalShaderMap, PermutationVector)` (raw L145-156). USF 안 `#if QUALITY_LEVEL >= 2` 로 분기 (raw L162-170).
- 🟢 **`ShouldCompilePermutation` 의무** — `static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P) { return IsFeatureLevelSupported(P.Platform, ERHIFeatureLevel::SM5); }` (raw L56-59). 누락 시 모든 플랫폼 × 모든 permutation 컴파일 → Cooked 시간 폭증 (raw L264 함정 #1). Permutation 변수 8개 = 2^8 = 256배 증가 (raw L266 함정 #3).
- 🟢 **`ModifyCompilationEnvironment`** — `OutEnvironment.SetDefine(TEXT("THREAD_GROUP_SIZE"), 8);` 로 USF `#define` 주입 (raw L61-66). ENV 변수 충돌 회피 (raw L271 함정 #8).
- 🟢 **Compute Dispatch 헬퍼** — `FComputeShaderUtils::AddPass(GraphBuilder, RDG_EVENT_NAME("X"), Shader, Parameters, FComputeShaderUtils::GetGroupCount(Size, FIntPoint(8,8)))` 우선 (raw L201-207). 또는 `GraphBuilder.AddPass(..., ERDGPassFlags::Compute, [...](FRDGAsyncTask, FRHIComputeCommandList& RHICmdList){ FComputeShaderUtils::Dispatch(...); })` 직접 RDG (raw L210-218).
- 🟢 **Pixel Shader 풀스크린** — `RENDER_TARGET_BINDING_SLOTS()` Parameter Struct 안 의무 + `FPixelShaderUtils::AddFullscreenPass(GraphBuilder, GlobalShaderMap, RDG_EVENT_NAME("X"), Shader, Parameters, Viewport)` 사용 (raw L236, L248-255).
- 🟡 **5.x PSO Precache** — raw Shader.md 본문은 §8 L268 함정 #5 에서 "Cooked Build 안 컴파일 (DDC 미스) → DDC 셰어드 스토리지 + ShaderPipelineCache" 로만 언급. `r.PSOPrecache=1` CVar 자체는 sibling [[sources/ue-render-material]] §5 (raw Material.md L93) 와 [[synthesis/pso-streaming-livepatch-tools]] 가 권위. Shader 차원에서는 ShaderPipelineCache + DDC 캐시 메커니즘.
- 🟡 **Mobile 컴파일 분리** — `IsMobilePlatform(P.Platform)` 검사로 `ShouldCompilePermutation` 안 분기 (raw L269 함정 #6). 정확한 헬퍼명은 일반 UE 지식 — raw 는 함정 표 한 줄.

## 3. 함정 (raw 10대 중 핵심 5)

- 🟢 **#1 `ShouldCompilePermutation` 누락** — `return IsFeatureLevelSupported(...)` 의무. 없으면 Cooked 모든 플랫폼 × 모든 permutation 컴파일 (raw L264).
- 🟢 **#2 Shader Path 등록 누락** — Module `StartupModule` 안 `AddShaderSourceDirectoryMapping`. 없으면 `IMPLEMENT_GLOBAL_SHADER` 가 USF 못 찾음 (raw L265, L128).
- 🟢 **#3 Permutation 폭증** — `× 8 변수 = 256배` cooked-build 시간. 정말 필요한 변형만 dim 추가 (raw L266).
- 🟢 **#4 USF ↔ C++ Parameter 불일치** — `BEGIN_SHADER_PARAMETER_STRUCT` 안 변수명 / 타입 = `.usf` 안 declaration 정확 일치 (raw L267).
- 🟢 **#7 RDG 외부 Shader Bind** — `RDG_TEXTURE_*` / `RDG_BUFFER_*` 매크로 사용 시 RDG Pass lambda 안에서만 dispatch 의무 (raw L270).

## 4. 코드 예 (slim — Global Compute Shader 최소)

```cpp
// MyShader.h
class FMyCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FMyCS);
    SHADER_USE_PARAMETER_STRUCT(FMyCS, FGlobalShader);
    BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
        SHADER_PARAMETER(float, Strength)
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D, InTex)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutTex)
    END_SHADER_PARAMETER_STRUCT()
    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& P)
    { return IsFeatureLevelSupported(P.Platform, ERHIFeatureLevel::SM5); }
};
// MyShader.cpp
IMPLEMENT_GLOBAL_SHADER(FMyCS, "/Plugin/MyMod/MyShader.usf", "MainCS", SF_Compute);
```

(raw L38-71 발췌 / 축약)

## 5. Cross-link

- **페어** — [[sources/ue-render-material]] (Material 측 FMaterialShader / Translator · ⭐ **PSO Precache `r.PSOPrecache` CVar 권위 출처**) · [[sources/ue-render-materialexpression]] (Custom Expression Compile() 페어) · [[sources/ue-render-rdg]] (Pass Parameter Struct 출처)
- **자산 페어** — [[sources/ue-assetclasses-material]] (UMaterial / MIC / MID)
- **통합 가이드** — [[synthesis/render-rdg-pass-standard-pattern]] §34 (SVE hook + FRDGBuilder + FGlobalShader 3계층 표준)
- **PSO** — [[synthesis/pso-streaming-livepatch-tools]] (`r.PSOPrecache` 권위 출처)
- **정책** — [[concepts/Profiling-Scope-Rule]] (Render 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` + `RDG_EVENT_SCOPE` 의무)


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-render-meshdrawing]] (inbound=4, suggest_missing_cross_link high confidence)
- [[sources/ue-render-sceneviewextension]] (inbound=3, suggest_missing_cross_link high confidence)
## 6. 신뢰도 매트릭스

| 영역 | Tier | 근거 |
|------|------|------|
| Shader 종류 3분 / 베이스 클래스 | 🟢 | raw L26-30 표 |
| `DECLARE_GLOBAL_SHADER` / `IMPLEMENT_GLOBAL_SHADER` 시그니처 | 🟢 | raw L46, L70 |
| Parameter Struct 매크로 11종 + `STRUCT_INCLUDE` | 🟢 | raw L178-192 |
| `SHADER_PERMUTATION_INT/BOOL` + `TShaderPermutationDomain<>` | 🟢 | raw L145-148 |
| `ShouldCompilePermutation` 시그니처 / 의무 | 🟢 | raw L56-59 |
| `AddShaderSourceDirectoryMapping` StartupModule 패턴 | 🟢 | raw L112-120 |
| `FComputeShaderUtils::AddPass` / `Dispatch` | 🟢 | raw L201-218 |
| `FPixelShaderUtils::AddFullscreenPass` + `RENDER_TARGET_BINDING_SLOTS()` | 🟢 | raw L236, L248-255 |
| 5.x `r.PSOPrecache` Shader 차원 적용 | 🟡 | raw L268 (DDC 표현) + sibling Material.md L93 (CVar 출처) |
| Mobile 컴파일 분기 헬퍼 `IsMobilePlatform` | 🟡 | raw L269 함정만 / 헬퍼명은 외삽 |
| Shader Hot Reload (`RecompileShaders` 콘솔) | 🟡 | raw L272 함정만 / 정확 명령어 syntax 는 외삽 |
| ShaderPipelineCache 메커니즘 동작 | 🔴 | raw 키워드만 / 일반 UE 지식 |
| DDC 셰어드 스토리지 셋업 | 🔴 | raw 키워드만 / Build sub-skill 권위 |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 변경 0 / 추가 0 / 제거 0 — 단순 수치 또는 미세 변경만. 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/Render/references/Shader.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/Render/references/Shader.md]]
