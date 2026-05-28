---
name: render-postprocess
description: PostProcess Pipeline (5.x RDG 통합) — 내장 PostProcess 흐름 + Custom Pass 등록 + Material Domain MD_PostProcess + UPostProcessVolume + UPostProcessComponent. SceneViewExtension 통한 Custom Pass + RDG 표준.
---

# Render/PostProcess — Pipeline + Custom Pass + Material PP

> **위치**: `Engine/Source/Runtime/Renderer/Public/PostProcess/` + `Engine/Source/Runtime/Engine/Classes/Engine/PostProcessVolume.h`
> **요지**: PostProcess Pass 추가 표준 — Material Domain `MD_PostProcess` (디자이너) vs SceneViewExtension + Shader (프로그래머).

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | 모든 PP 콜백 첫 줄 `RDG_EVENT_SCOPE` |
| 🚨 RDG | 5.x 표준 — Legacy `IPooledRenderTarget` 직접 사용 X |
| 🎯 [`Material/SKILL.md`](../Material/SKILL.md) | MD_PostProcess Material 사용 시 Material 측 정책 |

---

## 1. PostProcess 추가 — 4가지 방법

| 방법 | 누가 | 사용 시점 | 비용 |
|------|------|----------|------|
| **PostProcess Material** (MD_PostProcess) | 디자이너 | 색감 / 블룸 / 비네팅 등 | 저 |
| **UPostProcessVolume** + Material | 디자이너 | 위치 기반 PP (위치 들어가면 활성) | 저 |
| **UPostProcessComponent** + Material | 디자이너 / 프로그래머 | 위치 기반 PP (Actor 첨부) | 저 |
| **SceneViewExtension + Shader** ⭐ | 프로그래머 | Custom GBuffer / Custom Compute | 중 |

---

## 2. PostProcess Pipeline 시점 (5.x)

```
GBuffer Render
  ↓
Lumen / SSAO / SSR
  ↓
PrePostProcessPass_RenderThread ⭐ (SceneViewExtension Hook)
  ↓
ToneMapper / Bloom / Lens Flare
  ↓
PostTonemap (UI 그리기 전)
  ↓
Final Output
```

→ **PrePostProcessPass_RenderThread** = 가장 자주 쓰는 Custom Hook 시점.

---

## 3. PostProcess Material 사용

### 3.1 자산 작성

```
Material Editor:
- Material Domain = Post Process
- Output: Emissive Color (출력 픽셀 색)
- Input: SceneTexture / SceneColor 노드로 GBuffer 샘플링
```

### 3.2 활성

```cpp
// Code 측 — UPostProcessComponent 활용
UPostProcessComponent* PPComp = ...;
PPComp->bEnabled = true;
PPComp->Settings.AddBlendable(MyPostProcessMaterial, /*Weight=*/ 1.0f);
PPComp->Settings.bOverride_AutoExposureMethod = true;
```

### 3.3 PostProcessVolume

```cpp
// Level 안 PostProcessVolume 배치 → 위치 기반 활성
APostProcessVolume* Volume = World->SpawnActor<APostProcessVolume>();
Volume->Settings.AddBlendable(MyPostProcessMaterial, 1.0f);
Volume->bUnbound = true;   // 전역 PP
```

---

## 4. SceneViewExtension Custom Pass (가장 강력)

자세한 = [`SceneViewExtension/SKILL.md`](../SceneViewExtension/SKILL.md)

```cpp
// PrePostProcessPass_RenderThread 안 Custom Pass 추가
void FMySceneViewExt::PrePostProcessPass_RenderThread(
    FRDGBuilder& GraphBuilder,
    const FSceneView& View,
    const FPostProcessingInputs& Inputs)
{
    RDG_EVENT_SCOPE(GraphBuilder, "MyCustomPass");

    FRDGTextureRef SceneColor = (*Inputs.SceneTextures)->GetContents()->SceneColorTexture;
    FRDGTextureRef GBufferA = (*Inputs.SceneTextures)->GetContents()->GBufferATexture;

    // 1. Custom Compute Pass
    AddMyComputePass(GraphBuilder, GBufferA, SceneColor);

    // 2. Custom Pixel Shader Pass
    AddMyPixelPass(GraphBuilder, SceneColor);
}
```

---

## 5. 결정 매트릭스

| 시나리오 | 권장 방법 | 사유 |
|---------|---------|------|
| 단순 색감 보정 (LUT) | PostProcess Material | 디자이너 작업 가능 |
| 블룸 / 비네팅 / DOF | 내장 PostProcess Setting | 이미 최적화됨 |
| 위치 기반 PP (실내 → 색조 변환) | UPostProcessVolume | 자동 위치 감지 |
| Actor 따라가는 PP (캐릭터 효과) | UPostProcessComponent | Actor 라이프사이클 |
| GBuffer Custom 샘플링 | SceneViewExtension + PS | GBuffer 직접 접근 |
| Custom Compute (GPU 시뮬) | SceneViewExtension + CS | RDG Compute Pass |
| 5.x Lumen 데이터 사용 | SceneViewExtension + Hook 정확 | Lumen 결과 = PP 직전 |

---

## 6. PostProcess Material 함정

```
1. Material Domain = MD_PostProcess 의무 (Material 자산 설정)
2. SceneTexture 샘플링 = MD_PostProcess 만 가능 (다른 Domain 에선 X)
3. 5.x = Lumen / Nanite 와 호환성 검사 (SceneTexture 일부 누락 가능)
4. Cooked Build 안 PostProcess Material = PSO Precache 의무 (첫 Render 히칭 회피)
5. 모바일 = PostProcess Material 비용 큼 — Quality Level 분기
```

---

## 7. UPostProcessComponent 패턴

```cpp
// MyEffectActor.h
class AMyEffectActor : public AActor
{
    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UPostProcessComponent> PPComp;

    UPROPERTY(EditAnywhere)
    TSoftObjectPtr<UMaterialInterface> EffectMaterial;
};

// AMyEffectActor.cpp
AMyEffectActor::AMyEffectActor()
{
    PPComp = CreateDefaultSubobject<UPostProcessComponent>(TEXT("PostProcess"));
    PPComp->bEnabled = false;        // 기본 비활성
    PPComp->bUnbound = false;        // 위치 기반
    PPComp->BlendRadius = 100.f;
}

void AMyEffectActor::ActivateEffect()
{
    if (!EffectMaterial.IsValid())
    {
        // Soft → Sync Load (빠른 활성화 시)
        EffectMaterial.LoadSynchronous();
    }

    PPComp->bEnabled = true;
    PPComp->Settings.AddBlendable(EffectMaterial.Get(), /*Weight=*/ 1.0f);
}
```

---

## 8. 함정 & 안티패턴 (8대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | PostProcess Material Domain 잘못 (MD_Surface 등) | MD_PostProcess 의무 |
| 2 | Custom Pass = `PostRenderViewFamily_RenderThread` (잘못된 hook) | `PrePostProcessPass_RenderThread` 표준 |
| 3 | RDG 외부에서 PostProcess 텍스처 접근 | RDG Pass 안 + RegisterExternalTexture |
| 4 | UPostProcessComponent 활성화 후 Settings 미설정 | bEnabled = true + AddBlendable 페어 |
| 5 | 모바일 = 비용 큰 PostProcess Material 활성 | Quality Level 분기 (Mobile 비활성) |
| 6 | 5.x Lumen 결과 사용 전에 Hook | Lumen = GBuffer 단계 이후 — Hook 시점 정확 |
| 7 | PSO Precache 미사용 → 첫 Render 히칭 | Material PSO Precache 등록 |
| 8 | Multi-View / Stereo PP 미고려 | View 별 분기 |

---

## 9. 체크리스트

- [ ] MD_PostProcess Material Domain (Material 측)
- [ ] UPostProcessComponent / Volume 활성 + AddBlendable
- [ ] Custom Pass = SceneViewExtension::PrePostProcessPass_RenderThread
- [ ] RDG Pass 안 + RDG_EVENT_SCOPE
- [ ] Mobile Quality 분기
- [ ] PSO Precache 활성
- [ ] 5.x Lumen / Nanite 호환 검사
- [ ] Multi-View / Stereo 검증

---

## 10. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- [`Render/references/SceneViewExtension.md`](../SceneViewExtension/SKILL.md) — Custom Pass Hook
- [`Render/references/RDG.md`](../RDG/SKILL.md) — RDG Pass
- [`Render/references/Material.md`](../Material/SKILL.md) — MD_PostProcess Material
- [`Render/references/Shader.md`](../Shader/SKILL.md) — Pixel/Compute Shader
- [`AssetClasses/references/Material.md`](../../AssetClasses/references/Material.md) — Material 자산

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. PostProcess 4 방법 + Pipeline 시점 + PostProcess Material + SceneViewExtension Custom Pass + 결정 매트릭스 + 함정 8대. |
