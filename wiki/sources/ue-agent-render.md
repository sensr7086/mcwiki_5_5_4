---
type: source
title: "UE Render Specialist 🎨 — 11 sub-skill + 3축 스레드 분리 + 5.x Lumen/Nanite"
slug: ue-agent-render
source_path: raw/ue-wiki-llm/agents/ue-render-specialist.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_entities: []
related_concepts:
  - "[[concepts/RDG-Pass]]"
  - "[[concepts/PSO-Precache]]"
  - "[[concepts/Render-Thread-Safety]]"
  - "[[concepts/Motion-To-Photon-Latency]]"
tags: [ue, agent, specialist, render, rdg, 3-thread-axis, lumen-nanite, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 2 enrich"
---

# UE Render Specialist 🎨

> Source: [[raw/ue-wiki-llm/agents/ue-render-specialist.md]]
> Parent: [[sources/ue-agent-orchestrator]] — `[Render]` prefix 호출
> Cycle 5n Round 2 — stub → 정밀 enrich

## 1. Summary

🟢 UE 5.7.4 Render 카테고리 전문가 — RenderCore + Renderer + RHI + 5.x 통합. **11 sub-skill** (RDG / Shader / Material / SceneViewExtension / MeshDrawing / PostProcess / LumenNanite / RHI / Vulkan / Mobile / VR). `FRDGBuilder` + `FGlobalShader` + `FSceneViewExtensionBase` + `FMeshBatch` + 5.x Lumen/Nanite/GPU Scene + `FRHICommandList` + OpenXR + Mobile Forward/Deferred + Foveated. **3축 스레드 분리** (Game / Render / RHI) 의무. PSO Precache 5.x. Cross-Platform (DX12/Vulkan/Metal). Mobile/VR 90fps.

## 2. 자동 로드 (7 파일)

1. `skills/Render/SKILL.md` (메인 — 11 sub-skill + 3축 스레드 분리)
2. 사용자 요청 매칭 sub-skill
3. [[sources/ue-ref-07-profilingscopeRule]] (의무 — 모든 Render 콜백)
4. [[sources/ue-ref-12-assetoptimizationpolicy]] (Mesh LOD + Material Quality)
5. (5.x) [[sources/ue-render-lumennanite]]
6. (자산) [[sources/ue-assetclasses-material]] · [[sources/ue-assetclasses-mesh]]
7. (호스트) [[sources/ue-components-meshcomponents]]

## 3. 11 시나리오 매핑

| 시나리오 | 필수 sub-skill |
|---------|---------------|
| Custom PostProcess (블러 / 색감) ⭐ | SceneViewExtension + RDG + Shader |
| Custom Compute Shader (GPU 시뮬) | RDG + Shader (Compute) + RHI |
| Custom Material Expression | Material (Editor 4단 분리) |
| Custom Mesh Renderer | MeshDrawing + Shader + RDG |
| GBuffer Custom Sample | SceneViewExtension + Shader + Material |
| 5.x Lumen / Nanite ⭐⭐ | LumenNanite |
| RHI 직접 명령 | RHI + RDG |
| Material PSO 캐시 (Cooked 히칭) | Material §5 + AssetClasses/Material |
| Cross-Platform (DX12/Vulkan/Metal) ⭐ | Vulkan + Shader (Permutation) |
| Mobile 60fps (iOS/Android) ⭐ | Mobile + Material (Quality) |
| VR 90/120fps ⭐⭐ | VR + Mobile (Quest) |

## 4. 🚨 3축 스레드 분리 의무 ⭐ (Render 의 핵심)

```cpp
// 게임 스레드 → Render Thread 큐잉
ENQUEUE_RENDER_COMMAND(MyCmd)(
    [SceneProxy = SceneProxy, Data](FRHICommandList& RHICmdList) {
        if (SceneProxy) SceneProxy->UpdateData_RenderThread(Data);
    });

// Render Thread (FPrimitiveSceneProxy + RDG)
void FMyProxy::AddRenderPass(FRDGBuilder& Builder) {
    RDG_EVENT_SCOPE(Builder, "MyPass");
    Builder.AddPass(RDG_EVENT_NAME("Compute"), Params, ERDGPassFlags::Compute,
        [](FRDGAsyncTask, FRHIComputeCommandList& RHICmdList) {
            // RHI Thread — 실제 GPU 명령
            RHICmdList.DispatchComputeShader(...);
        });
}
```

**3축 절대 규칙**: 게임 스레드 ↔ Render Thread ↔ RHI Thread = 별도 컨텍스트.
- Render Thread 안 UObject 직접 접근 X
- RHI Lambda 안 Render Thread 객체 직접 접근 X (값 복사 또는 TRefCountPtr)

## 5. 5.x 표준 의무 (5종 자동)

1. **RDG 우선** (Legacy `IPooledRenderTarget` X) — `FRDGBuilder` + `CreateTexture`
2. **Shader = Permutation + ShouldCompilePermutation** — `IMPLEMENT_GLOBAL_SHADER`
3. **Shader Path 등록** (Module StartupModule 의무) — `AddShaderSourceDirectoryMapping`
4. **PSO Precache** (Cooked 첫 Render 히칭 회피) — `r.PSOPrecache=1`
5. **Lumen / Nanite 호환 검사** — Material Domain / Vertex Factory GPU Scene / Mobile = Lightmap fallback

## 6. SceneViewExtension Hook 표준 (Custom PostProcess)

```cpp
class FMySceneViewExt : public FSceneViewExtensionBase {
    virtual void SetupView(FSceneViewFamily&, FSceneView&) override;
    virtual void PrePostProcessPass_RenderThread(  // ⭐ 표준 Hook
        FRDGBuilder& Builder, const FSceneView& View, const FPostProcessingInputs& Inputs) override {
        RDG_EVENT_SCOPE(Builder, "MyPostProcess");
    }
    virtual bool IsActiveThisFrame_Internal(const FSceneViewExtensionContext& Ctx) const override {
        return Ctx.GetWorld() == TargetWorld;   // World 분기 의무
    }
};
```

## 7. Build.cs 의존성

```csharp
PrivateDependencyModuleNames.AddRange(new[] {
    "Core", "CoreUObject", "Engine",
    "RenderCore", "Renderer", "RHI",
    "Projects",  // FShaderType IMPLEMENT
});
```

## 8. 함정 자동 회피 (10대)

- Render Thread 안 UObject 접근 → ENQUEUE_RENDER_COMMAND + Proxy 캐싱
- Legacy IPooledRenderTarget → RDG
- Shader Permutation 폭증 (×8=256배) → 정말 필요한 변형만
- ShouldCompilePermutation 누락 → 컴파일 시간 폭증
- RDG_EVENT_SCOPE 누락 → 디버그 불가
- 5.x Nanite + Custom Vertex Factory → GPU Scene 호환 또는 비활성
- Mobile + Lumen → Lightmap fallback 의무
- Cooked PSO Precache 누락 → 첫 Render 100~500ms 히칭
- RHI Resource Init/Release 페어 누락 → GPU 메모리 누수
- SceneViewExtension `IsActiveThisFrame` 누락 → 모든 World 적용

## 9. Baseline Grep 의무

함정 키워드: `RDG` / `FRDGBuilder` / `Lumen` / `Nanite` / `PSO` / `PSO-Precache` / `FRHICommandList` / `FGlobalShader` / `FSceneViewExtensionBase` / `FMeshBatch` / `Motion-To-Photon`.

## 10. 거부 조건

- UMG / Slate — `ue-slate-umg-specialist`
- Editor 도구 — `ue-editor-specialist`
- 일반 Component — `ue-components-specialist`

## 11. Cross-link

- 메타 agent: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-asset]] (Material / Mesh) · [[sources/ue-agent-components]] (MeshComponents 호스트)
- sub-skill 11: [[sources/ue-render-rdg]] · [[sources/ue-render-shader]] · [[sources/ue-render-material]] · [[sources/ue-render-sceneviewextension]] · [[sources/ue-render-meshdrawing]] · [[sources/ue-render-postprocess]] · [[sources/ue-render-lumennanite]] · [[sources/ue-render-rhi]] · [[sources/ue-render-vulkan]] · [[sources/ue-render-mobile]] · [[sources/ue-render-vr]]
- 정책: [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-12-assetoptimizationpolicy]]
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 12. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | stub 카드 |
| 2026-05-15 (Cycle 5n Round 2) | ⭐⭐⭐ stub → 정밀 12 절. 11 시나리오 + 3축 스레드 분리 + 5.x 5종 + 함정 10대 |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
