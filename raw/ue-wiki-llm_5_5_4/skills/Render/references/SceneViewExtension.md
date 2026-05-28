---
name: render-sceneviewextension
description: FSceneViewExtensionBase + 7 Hook (PreRenderView_RenderThread / PostRenderViewFamily_RenderThread / PrePostProcessPass_RenderThread / etc) — Custom PostProcess / GBuffer Sample / Custom Pass 추가의 표준 진입점. 5.x RDG 통합. 게임 스레드 → Render Thread 데이터 전달.
---

# Render/SceneViewExtension — Custom Render Hook 표준

> **위치**: `Engine/Public/SceneViewExtension.h` (Engine 모듈)
> **요지**: 엔진 코드 수정 없이 **Render Pipeline 안 Hook** 가능한 5.x 표준 시스템. Custom PostProcess / GBuffer 샘플링 / Custom Pass 추가의 진입점.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | 모든 _RenderThread 콜백 첫 줄 `RDG_EVENT_SCOPE` 의무 |
| 🚨 스레드 안전성 | _RenderThread 메소드 = Render Thread / 게임 스레드 멤버 직접 접근 X |
| 🚨 Lifetime | Subsystem / GameInstance 에서 등록 / 해제 페어 의무 |

---

## 1. 7 Hook 시점 (라이프사이클 순서)

| 콜백 | 시점 | 용도 |
|------|------|------|
| `SetupView` | Render Thread 진입 전 (게임 스레드) | 게임 데이터 → Render Thread 전달 |
| `BeginRenderViewFamily` | Render Thread 진입 직후 | Render Thread 셋업 |
| `PreRenderView_RenderThread` | View 렌더 직전 | Per-View 셋업 |
| `PreRenderViewFamily_RenderThread` | View Family 렌더 직전 | 전체 셋업 |
| `PrePostProcessPass_RenderThread` ⭐ | PostProcess 직전 (Custom PP 표준) | Custom PostProcess Pass 추가 |
| `PostRenderViewFamily_RenderThread` | View Family 렌더 직후 | 정리 / 최종 처리 |
| `PostRenderView_RenderThread` | View 렌더 직후 | Per-View 정리 |

---

## 2. 표준 사용 패턴

### 2.1 SceneViewExtension 클래스 정의

```cpp
// MySceneViewExtension.h
#pragma once
#include "SceneViewExtension.h"

class FMySceneViewExtension : public FSceneViewExtensionBase
{
public:
    FMySceneViewExtension(const FAutoRegister& AutoRegister);

    // 게임 스레드 → Render Thread 데이터 전달
    void SetEffectStrength(float NewStrength) { EffectStrength = NewStrength; }

    // ─── FSceneViewExtensionBase 인터페이스 ───
    virtual void SetupView(FSceneViewFamily& InViewFamily, FSceneView& InView) override;
    virtual void PrePostProcessPass_RenderThread(FRDGBuilder& GraphBuilder,
                                                   const FSceneView& View,
                                                   const FPostProcessingInputs& Inputs) override;

private:
    // 게임 스레드 → Render Thread 페어 (volatile or atomic)
    float EffectStrength = 1.0f;
    float CachedEffectStrength_RenderThread = 1.0f;
};
```

### 2.2 구현

```cpp
// MySceneViewExtension.cpp
FMySceneViewExtension::FMySceneViewExtension(const FAutoRegister& AutoRegister)
    : FSceneViewExtensionBase(AutoRegister)
{
}

void FMySceneViewExtension::SetupView(FSceneViewFamily& InViewFamily, FSceneView& InView)
{
    // 게임 스레드 — 데이터 캐싱 (Render Thread 사용 위해)
    CachedEffectStrength_RenderThread = EffectStrength;
}

void FMySceneViewExtension::PrePostProcessPass_RenderThread(
    FRDGBuilder& GraphBuilder,
    const FSceneView& View,
    const FPostProcessingInputs& Inputs)
{
    RDG_EVENT_SCOPE(GraphBuilder, "MyPostProcessExtension");

    // PostProcess Input 가져오기
    FRDGTextureRef SceneColor = (*Inputs.SceneTextures)->GetContents()->SceneColorTexture;
    if (!SceneColor)
    {
        return;
    }

    // Custom PostProcess Pass 추가 (RDG)
    AddMyCustomPass(GraphBuilder, SceneColor, CachedEffectStrength_RenderThread);
}
```

### 2.3 등록 (GameInstanceSubsystem 또는 PlayerController)

```cpp
// MyGameInstanceSubsystem.h
UCLASS()
class UMyRenderSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    // 게임 측 → Render 측 데이터
    UFUNCTION(BlueprintCallable)
    void SetEffectStrength(float NewStrength);

private:
    TSharedPtr<class FMySceneViewExtension, ESPMode::ThreadSafe> ViewExtension;
};

// MyGameInstanceSubsystem.cpp
void UMyRenderSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    // FAutoRegister — 자동 등록
    ViewExtension = FSceneViewExtensions::NewExtension<FMySceneViewExtension>();
}

void UMyRenderSubsystem::Deinitialize()
{
    ViewExtension.Reset();   // 자동 해제
    Super::Deinitialize();
}

void UMyRenderSubsystem::SetEffectStrength(float NewStrength)
{
    if (ViewExtension.IsValid())
    {
        ViewExtension->SetEffectStrength(NewStrength);   // 게임 스레드 데이터
    }
}
```

---

## 3. PrePostProcessPass_RenderThread — Custom PostProcess 표준

### 3.1 PostProcessing Inputs 구조

```cpp
struct FPostProcessingInputs
{
    const FSceneTexturesUniformBuffer* SceneTextures;   // GBuffer / Depth / SceneColor 등
    // ... 기타 입력
};

// 핵심 Texture 접근
FRDGTextureRef SceneColor    = (*Inputs.SceneTextures)->GetContents()->SceneColorTexture;
FRDGTextureRef SceneDepth    = (*Inputs.SceneTextures)->GetContents()->SceneDepthTexture;
FRDGTextureRef GBufferA      = (*Inputs.SceneTextures)->GetContents()->GBufferATexture;
FRDGTextureRef GBufferB      = (*Inputs.SceneTextures)->GetContents()->GBufferBTexture;
FRDGTextureRef Velocity      = (*Inputs.SceneTextures)->GetContents()->VelocityTexture;
```

### 3.2 표준 PostProcess Pass 작성

```cpp
void AddMyCustomPostProcess(
    FRDGBuilder& GraphBuilder,
    FRDGTextureRef SceneColor,
    float Strength)
{
    RDG_EVENT_SCOPE(GraphBuilder, "MyPostProcess");

    // 출력 텍스처 (SceneColor 와 같은 크기)
    FRDGTextureDesc OutputDesc = SceneColor->Desc;
    FRDGTextureRef OutputTex = GraphBuilder.CreateTexture(OutputDesc, TEXT("MyPostProcessOutput"));

    // Pixel Shader 사용
    FMyPostProcessPS::FParameters* Parameters = GraphBuilder.AllocParameters<FMyPostProcessPS::FParameters>();
    Parameters->InputTexture = GraphBuilder.CreateSRV(FRDGTextureSRVDesc(SceneColor));
    Parameters->InputSampler = TStaticSamplerState<SF_Bilinear>::GetRHI();
    Parameters->Strength = Strength;
    Parameters->RenderTargets[0] = FRenderTargetBinding(OutputTex, ERenderTargetLoadAction::EClear);

    TShaderMapRef<FMyPostProcessPS> Shader(GetGlobalShaderMap(GMaxRHIFeatureLevel));

    FPixelShaderUtils::AddFullscreenPass(
        GraphBuilder,
        GetGlobalShaderMap(GMaxRHIFeatureLevel),
        RDG_EVENT_NAME("MyPostProcess"),
        Shader,
        Parameters,
        FIntRect(0, 0, OutputTex->Desc.Extent.X, OutputTex->Desc.Extent.Y)
    );

    // (선택) OutputTex → SceneColor 복사 (다음 Pass 가 SceneColor 사용 시)
    AddCopyTexturePass(GraphBuilder, OutputTex, SceneColor);
}
```

---

## 4. IsActiveThisFrame_Internal (활성 분기)

```cpp
class FMySceneViewExtension : public FSceneViewExtensionBase
{
    virtual bool IsActiveThisFrame_Internal(const FSceneViewExtensionContext& Context) const override
    {
        // 특정 World / 특정 PlayerController 만 활성
        if (Context.GetWorld() != TargetWorld)
        {
            return false;
        }
        return bEnabled;
    }
};
```

---

## 5. 함정 & 안티패턴 (8대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | _RenderThread 메소드 안 게임 스레드 객체 접근 | SetupView 에서 캐싱 → _RenderThread 가 캐싱 값만 |
| 2 | RDG_EVENT_SCOPE 누락 | 모든 _RenderThread 첫 줄 의무 |
| 3 | 등록 / 해제 누락 (메모리 누수) | GameInstanceSubsystem Initialize/Deinitialize 페어 |
| 4 | TSharedPtr 가 아닌 Raw pointer 등록 | `FSceneViewExtensions::NewExtension<>` 만 사용 |
| 5 | 잘못된 Hook 시점 (Pre vs Post) | PostProcess 추가 = `PrePostProcessPass_RenderThread` 표준 |
| 6 | Multi-View / Stereo 미고려 | View 별 분기 (FSceneView 인자 활용) |
| 7 | 5.x Lumen / Nanite 의 PostProcess 와 충돌 | Hook 시점 정확 + IsActiveThisFrame_Internal 검사 |
| 8 | IsActiveThisFrame_Internal 누락 → 모든 World 적용 | 의무 — Context.GetWorld() 검사 |

---

## 6. 체크리스트

- [ ] FSceneViewExtensionBase 자손 + FAutoRegister
- [ ] _RenderThread 메소드 안 캐싱 값만 사용
- [ ] SetupView 에서 게임 스레드 데이터 → 캐싱
- [ ] RDG_EVENT_SCOPE 모든 _RenderThread 첫 줄
- [ ] FSceneViewExtensions::NewExtension<> 등록
- [ ] GameInstanceSubsystem Initialize/Deinitialize 페어
- [ ] IsActiveThisFrame_Internal 의무 (World 분기)
- [ ] PrePostProcessPass_RenderThread (Custom PP) 표준 hook

---

## 7. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- [`Render/references/RDG.md`](../RDG/SKILL.md) — RDG Pass 안 사용
- [`Render/references/PostProcess.md`](../PostProcess/SKILL.md) — PostProcess 깊이
- [`Render/references/Shader.md`](../Shader/SKILL.md) — Pixel/Compute Shader
- [`Subsystem/SKILL.md`](../../Subsystem/SKILL.md) — UGameInstanceSubsystem (등록 호스트)

## 8. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. FSceneViewExtensionBase + 7 Hook + Custom PostProcess 표준 + GameInstanceSubsystem 등록 + IsActiveThisFrame_Internal + 함정 8대. |
