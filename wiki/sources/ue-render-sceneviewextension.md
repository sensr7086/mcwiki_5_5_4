---
type: source
title: "UE Render — SceneViewExtension sub-skill"
slug: ue-render-sceneviewextension
source_path: raw/ue-wiki-llm/skills/Render/references/SceneViewExtension.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-12
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Render-Thread-Safety]]"
  - "[[concepts/RDG-Pass]]"
related_sources:
  - "[[sources/ue-render-skill]]"
  - "[[sources/ue-render-rdg]]"
  - "[[sources/ue-render-postprocess]]"
  - "[[sources/ue-render-shader]]"
citation_disclosure:
  green: 9   # raw 직접 확인 (Hook 표 / 등록 API / 함정 / 코드 패턴)
  yellow: 1  # raw 근거 + 일반 UE 지식 외삽 (SubscribeToPostProcessingPass 시점 보강)
  red: 0
tags: [ue, render, gpu, sceneviewextension, render-thread, hook]
---

# UE Render — SceneViewExtension

> Source: [[raw/ue-wiki-llm/skills/Render/references/SceneViewExtension.md]]
> Parent: [[sources/ue-render-skill]] · Pair: [[sources/ue-render-rdg]] · [[sources/ue-render-postprocess]] · [[sources/ue-render-shader]]
> Synthesis: [[synthesis/render-rdg-pass-standard-pattern]] §SVE hook

## §1. Summary

🟢 `FSceneViewExtensionBase` (Engine 모듈, `Engine/Public/SceneViewExtension.h`) 자손이 엔진 코드 수정 없이 **Render Pipeline 안 7 가상 후크** 를 override 하는 5.x 표준 시스템. Custom PostProcess / GBuffer 샘플링 / Custom Pass 추가의 진입점. `_RenderThread` 접미사 후크는 Render Thread 컨텍스트 — 게임 스레드 멤버 직접 접근 금지, `SetupView` 에서 캐싱 후 cached 값만 사용. RDG 5.x 와 직접 통합 (`FRDGBuilder&` 인자).

## §2. Key claims (🟢 9 · 🟡 1)

- 🟢 **자손 + 등록 API**: `FSceneViewExtensionBase(const FAutoRegister&)` 생성자 + `FSceneViewExtensions::NewExtension<MyExt>()` (TSharedPtr) — Raw pointer 등록 금지.
- 🟢 **7 Hook 라이프사이클 순서**:
  1. `SetupView` (게임 스레드 — Render Thread 진입 전 데이터 전달)
  2. `BeginRenderViewFamily` (Render Thread 진입 직후 셋업)
  3. `PreRenderView_RenderThread` (View 렌더 직전 Per-View 셋업)
  4. `PreRenderViewFamily_RenderThread` (View Family 렌더 직전 전체 셋업)
  5. `PrePostProcessPass_RenderThread` ⭐ (PostProcess 직전 — Custom PP 표준 진입점)
  6. `PostRenderViewFamily_RenderThread` (View Family 렌더 직후 정리)
  7. `PostRenderView_RenderThread` (View 렌더 직후 Per-View 정리)
- 🟢 **`PrePostProcessPass_RenderThread` 가 Custom PostProcess 표준 hook** — 인자 `FRDGBuilder& GraphBuilder` + `FSceneView&` + `FPostProcessingInputs&` 직접 수령, RDG Pass 추가 가능.
- 🟢 **PostProcessing Inputs → SceneTextures 접근**: `(*Inputs.SceneTextures)->GetContents()->{SceneColorTexture / SceneDepthTexture / GBufferA~B / VelocityTexture}` — 모두 `FRDGTextureRef`.
- 🟢 **`IsActiveThisFrame_Internal(FSceneViewExtensionContext&)` 의무 override** — `Context.GetWorld()` 검사 없으면 모든 World 적용 (PIE/Editor preview 포함 함정).
- 🟢 **Render Thread 안전성 의무**: `_RenderThread` 메소드 안 UObject / 게임 스레드 멤버 직접 접근 X. `SetupView` 가 게임 스레드 → Render Thread 캐싱 다리.
- 🟢 **Lifetime = host Subsystem**: `UGameInstanceSubsystem::Initialize` 에서 `NewExtension`, `Deinitialize` 에서 `Reset` 페어 — 미등록/누수 차단.
- 🟢 **RDG_EVENT_SCOPE 의무**: 모든 `_RenderThread` 후크 첫 줄 (raw §1 + `07_ProfilingScopeRule.md` 연계).
- 🟡 **`SubscribeToPostProcessingPass` (raw에 명시 없음, 일반 UE 5.x 지식)**: 5.x 신 API — `EPostProcessingPass` enum 별 callback subscribe 방식. 본 raw 는 `PrePostProcessPass_RenderThread` 만 다룸 (vault 근거 부분 + 외삽).

## §3. 함정 (5)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 🟢 `_RenderThread` 안 게임 스레드 객체 직접 접근 | `SetupView` 에서 캐싱 → cached 값만 사용 (race 차단) |
| 2 | 🟢 `IsActiveThisFrame_Internal` 누락 → 모든 World/PIE/Editor preview 적용 | `Context.GetWorld() == TargetWorld` 의무 검사 |
| 3 | 🟢 Raw pointer 등록 (수동 GEngine->ViewExtensions push) | `FSceneViewExtensions::NewExtension<>()` 만 사용 — TSharedPtr 자동 |
| 4 | 🟢 등록 / 해제 페어 누락 (Subsystem Deinitialize 에서 Reset 안 함) | GameInstanceSubsystem Init/Deinit 페어 의무 — Reset 으로 자동 해제 |
| 5 | 🟢 잘못된 Hook 시점 선택 (예: PostProcess 추가에 PreRenderView 사용) | Custom PostProcess = `PrePostProcessPass_RenderThread` 1 곳만 표준 |

## §4. 코드 예 (최소 SVE — Custom PostProcess)

```cpp
class FMySVE : public FSceneViewExtensionBase
{
public:
    FMySVE(const FAutoRegister& AR) : FSceneViewExtensionBase(AR) {}

    void SetStrength(float S) { Strength = S; }   // 게임 스레드

    virtual void SetupView(FSceneViewFamily&, FSceneView&) override
    {
        CachedStrength = Strength;                // GT → RT 캐싱 다리
    }

    virtual void PrePostProcessPass_RenderThread(
        FRDGBuilder& GraphBuilder, const FSceneView& View,
        const FPostProcessingInputs& Inputs) override
    {
        RDG_EVENT_SCOPE(GraphBuilder, "MySVE_PP");     // §3 의무
        FRDGTextureRef SceneColor =
            (*Inputs.SceneTextures)->GetContents()->SceneColorTexture;
        if (SceneColor) AddMyPass(GraphBuilder, SceneColor, CachedStrength);
    }

    virtual bool IsActiveThisFrame_Internal(
        const FSceneViewExtensionContext& Ctx) const override
    {
        return Ctx.GetWorld() == TargetWorld && bEnabled;   // World 분기
    }

private:
    float Strength = 1.f, CachedStrength = 1.f;
    TWeakObjectPtr<UWorld> TargetWorld; bool bEnabled = true;
};

// 등록 (UGameInstanceSubsystem::Initialize)
ViewExtension = FSceneViewExtensions::NewExtension<FMySVE>();
// 해제 (Deinitialize) — ViewExtension.Reset();
```

## §5. Cross-link

- Parent: [[sources/ue-render-skill]]
- Sibling: [[sources/ue-render-rdg]] (FRDGBuilder Pass 추가) · [[sources/ue-render-postprocess]] (PP Material Domain · UPostProcessVolume 보완) · [[sources/ue-render-shader]] (Pixel/Compute Shader 호출)
- Concept: [[concepts/Render-Thread-Safety]] (GT↔RT 캐싱 다리) · [[concepts/RDG-Pass]] (Pass Lambda 캡처)
- Synthesis: [[synthesis/render-rdg-pass-standard-pattern]] §SVE hook 절
- Host: [[raw/ue-wiki-llm/skills/Subsystem/SKILL.md]] (UGameInstanceSubsystem 등록 호스트)
- Policy: [[raw/ue-wiki-llm/references/07_ProfilingScopeRule.md]] (RDG_EVENT_SCOPE 의무)

## §6. 신뢰도 매트릭스

| Claim | Tier | 근거 |
|-------|------|------|
| FSceneViewExtensionBase 자손 + FAutoRegister | 🟢 | raw §2.1-§2.2 |
| 7 Hook 순서 + 시점 | 🟢 | raw §1 표 |
| PrePostProcessPass_RenderThread = Custom PP 표준 | 🟢 | raw §1 ⭐ + §3 |
| FPostProcessingInputs → SceneTextures 접근 | 🟢 | raw §3.1 |
| IsActiveThisFrame_Internal World 분기 | 🟢 | raw §4 + §5 함정 #8 |
| RDG_EVENT_SCOPE 의무 | 🟢 | raw §공통 + §3.2 |
| TSharedPtr NewExtension API | 🟢 | raw §2.3 + §5 함정 #4 |
| GameInstanceSubsystem Init/Deinit 페어 | 🟢 | raw §2.3 |
| Render Thread 캐싱 다리 (SetupView) | 🟢 | raw §2.2 + §5 함정 #1 |
| SubscribeToPostProcessingPass (5.x 신 API) | 🟡 | raw 미언급 — 일반 UE 5.x 지식 외삽 |

---

### (Boundary) 보너스 발견

1. **raw §5 함정 #6 Multi-View / Stereo 미고려** — 본 카드 5 함정 압축 시 제외. VR ([[sources/ue-render-vr]]) 페어에서 다룰 가치. **synthesis 후보**: "SVE × Stereo Rendering 함정 매트릭스".
2. **raw §5 함정 #7 Lumen / Nanite PostProcess 와 Hook 시점 충돌** — [[sources/ue-render-lumennanite]] (예정) 와 cross-link 필요. 5.x 특화 — 별도 short synthesis 후보 ("Lumen Hook 시점 안전 매트릭스").
3. **`SubscribeToPostProcessingPass` (🟡)** — vault 미확정. UE 5.4+ 신 API 로 알려진 (per-pass callback) 패턴. raw 보강 시 vault green 으로 전환 필요. **filing-back 후보**: raw 갱신 요청 → 사용자 결정.
4. **호스트 페어 [[sources/ue-subsystem-skill]] 미존재 가능성** — Subsystem skill stub 검증 필요 (Cycle #5+ 대상).
5. **`FSceneViewExtensions::NewExtension` 정확한 namespace** — raw 는 이 정확한 API 형태를 보여줌. 5.x 코드 기반 일치 (engine 헤더 검증 시 green 유지).
