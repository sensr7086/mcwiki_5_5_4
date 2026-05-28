---
type: source
title: "UE Render — PostProcess sub-skill"
slug: ue-render-postprocess
source_path: raw/ue-wiki-llm/skills/Render/references/PostProcess.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-12
related_entities:
  - "[[entities/UMaterial]]"
related_concepts: []
tags: [ue, render, gpu, postprocess, rdg, sceneviewextension]
citation_tiers: { green: 14, yellow: 2, red: 4 }
---

# UE Render — PostProcess

> Source: [[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]]
> Parent: [[sources/ue-render-skill]] · Pair: [[sources/ue-render-sceneviewextension]] · [[sources/ue-render-rdg]] · [[sources/ue-render-shader]]
> Synthesis: [[synthesis/render-rdg-pass-standard-pattern]] · [[synthesis/pso-streaming-livepatch-tools]]
> Cycle: #5 slim enrich (boundary §5.4)

---

## §1. Summary

UE 5.x PostProcess 파이프라인은 **RDG 통합**. 모든 PP Pass = `FRDGPass`. 추가 방법은 4축: (a) `MD_PostProcess` Material + `UPostProcessVolume` / `UPostProcessComponent` 의 Blendable (디자이너) — (b) `FSceneViewExtensionBase::PrePostProcessPass_RenderThread` 의 RDG Hook (프로그래머). Lumen / Nanite / Tonemap / Bloom / AutoExposure 모두 RDG Pass 그래프. Material Domain `MD_PostProcess` 만 `SceneTexture` (GBuffer) 노드 샘플링 가능. Cooked Build = PSO Precache 등록 의무, Mobile = Quality Level 분기.

## §2. Key claims (🟢 vault)

1. **5.x RDG 통합** — Legacy `IPooledRenderTarget` 직접 사용 금지, PP Pass 는 RDG `FRDGPass` 그래프. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §공통 정책 + L18)
2. **Pipeline 순서** — GBuffer → Lumen/SSAO/SSR → `PrePostProcessPass_RenderThread` → Tonemap/Bloom/LensFlare → PostTonemap (UI 직전) → Final Output. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §2 L36-48)
3. **PrePostProcessPass_RenderThread = 표준 Hook** — 가장 자주 쓰는 Custom Hook 시점. Lumen 결과는 이 단계 직전까지 완료. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] L50, L184)
4. **4 추가 방법** — (a) `MD_PostProcess` Material, (b) `UPostProcessVolume` + Material, (c) `UPostProcessComponent` + Material (Actor 첨부), (d) `SceneViewExtension` + Shader. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §1 표 L25-30)
5. **`MD_PostProcess` Material Domain 의무** — `SceneTexture` / `SceneColor` 노드는 `MD_PostProcess` 에서만 샘플링 가능 (`MD_Surface` 등 다른 Domain X). Output = Emissive Color. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §3.1 + §6 함정 1·2)
6. **`UPostProcessComponent` vs `UPostProcessVolume`** — Volume = 위치 기반 (BlendRadius 보간) / Component = Actor 첨부 (캐릭터 라이프사이클). 둘 다 `Settings.AddBlendable(Material, Weight)` 로 활성. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §3.2-3.3 + §7)
7. **`bUnbound = true` = 전역 PP** — Volume 진입 무관, 항상 활성. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §3.3 L81)
8. **Custom Pass 표준 — RDG_EVENT_SCOPE 첫 줄** — `PrePostProcessPass_RenderThread(FRDGBuilder&, const FSceneView&, const FPostProcessingInputs&)` 안에서 `RDG_EVENT_SCOPE` → `(*Inputs.SceneTextures)->GetContents()->SceneColorTexture` / `GBufferATexture` 접근 → Custom Compute / Pixel Pass 추가. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §4 L91-108)
9. **결정 매트릭스** — 색감 LUT → MD_PostProcess Material / 블룸/DOF/Vignette → 내장 Setting / 위치 PP → Volume / Actor PP → Component / GBuffer 샘플 → SVE+PS / Compute 시뮬 → SVE+CS / Lumen 데이터 → SVE + Hook 시점 정확. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §5 L114-122)
10. **PSO Precache 의무 (Cooked Build)** — 첫 Render 히칭 회피. Material 등록 PSO Precache. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §6 L132 + §8 #7)
11. **Mobile 분기 의무** — PostProcess Material 비용 큼 → Quality Level 로 비활성. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §6 L133 + §8 #5)
12. **5.x Lumen / Nanite 호환 검사** — `SceneTexture` 일부 누락 가능 (Nanite GBuffer 구조 변화). ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §6 L131 + §8 #6)
13. **Multi-View / Stereo 분기** — VR 환경 View 별 PP 분기 의무. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §8 #8 L186)
14. **체크리스트 8항** — Domain / 활성 / Hook / RDG Scope / Mobile Quality / PSO / Lumen 호환 / Stereo. ([[raw/ue-wiki-llm/skills/Render/references/PostProcess.md]] §9 L192-199)

## §2.5. Key claims (🟡 PARTIAL — vault + 외삽)

15. **PrePostProcessPass = Tonemap 직전 단계** — vault 의 Pipeline 다이어그램(§2) 으로부터 위치는 명확하나, 정확한 Hook signature 의 RHI/RDG 표면(`FPostProcessingInputs` 멤버 명세)은 §4 코드 발췌 외 자세히 노출되지 않음. (vault 근거: §2 + §4 · 외삽: `Inputs.SceneTextures` IPooledRenderTarget→RDG promote 경계)
16. **Blendable Weight 보간** — Volume `BlendRadius` (`L157` `= 100.f`) 로 페어들 weight blending. vault 는 값 하나 (100) 만 보임, 보간 곡선/공식은 외삽. (vault 근거: §7 코드 · 외삽: 거리 기반 선형 fall-off 가정)

## §3. 함정 (vault §8 8대 — 🟢)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Material Domain 잘못 (MD_Surface 등) | `MD_PostProcess` 의무 |
| 2 | Custom Pass = `PostRenderViewFamily_RenderThread` 사용 | `PrePostProcessPass_RenderThread` 표준 |
| 3 | RDG 외부에서 PP 텍스처 접근 | RDG Pass 안 + `RegisterExternalTexture` |
| 4 | UPostProcessComponent 활성화 후 Settings 미설정 | `bEnabled=true` + `AddBlendable` 페어 |
| 5 | Mobile 에서 비용 큰 PP Material 활성 | Quality Level 분기 |
| 6 | Lumen 결과 사용 전 시점 Hook | Lumen = GBuffer 단계 이후, Hook 시점 정확 |
| 7 | PSO Precache 미사용 → 첫 Render 히칭 | Material PSO Precache 등록 |
| 8 | Multi-View / Stereo PP 미고려 | View 별 분기 |

## §4. Code — Custom PP Pass 최소 (vault §4 + §7 압축)

```cpp
// SceneViewExtension Custom Pass (가장 강력)
void FMySceneViewExt::PrePostProcessPass_RenderThread(
    FRDGBuilder& GraphBuilder,
    const FSceneView& View,
    const FPostProcessingInputs& Inputs)
{
    RDG_EVENT_SCOPE(GraphBuilder, "MyCustomPass");
    FRDGTextureRef SceneColor = (*Inputs.SceneTextures)->GetContents()->SceneColorTexture;
    FRDGTextureRef GBufferA   = (*Inputs.SceneTextures)->GetContents()->GBufferATexture;
    AddMyComputePass(GraphBuilder, GBufferA, SceneColor);
}

// UPostProcessComponent 활성 패턴 (Actor 첨부)
PPComp = CreateDefaultSubobject<UPostProcessComponent>(TEXT("PostProcess"));
PPComp->bEnabled = false;          // 기본 비활성
PPComp->bUnbound = false;          // 위치 기반
PPComp->BlendRadius = 100.f;
// 활성 시
PPComp->bEnabled = true;
PPComp->Settings.AddBlendable(EffectMaterial.Get(), /*Weight=*/ 1.0f);
```

## §5. Cross-link

- Parent: [[sources/ue-render-skill]]
- Hook 메커니즘: [[sources/ue-render-sceneviewextension]] (PrePostProcessPass_RenderThread 의 SVE 단)
- RDG Pass 표준: [[sources/ue-render-rdg]] · [[synthesis/render-rdg-pass-standard-pattern]]
- Shader (PS/CS): [[sources/ue-render-shader]]
- Material 정책 (MD_PostProcess): [[sources/ue-render-material]] · [[sources/ue-assetclasses-material]]
- PSO 히칭 회피: [[synthesis/pso-streaming-livepatch-tools]]
- 의무 정책: [[raw/ue-wiki-llm/references/07_ProfilingScopeRule.md]] (RDG_EVENT_SCOPE)

## §6. 신뢰도 매트릭스

| Tier | Count | 의미 |
|------|-------|------|
| 🟢 VAULT | 14 (§2 #1-14) | raw L18-216 직접 인용 |
| 🟡 PARTIAL | 2 (§2.5 #15-16) | vault 근거 + 외삽 |
| 🔴 INFERRED | 4 (§7 보너스) | vault 미확인 — 일반 UE 지식 |

---

## §7. Boundary 보너스 발견 (🔴 INFERRED — vault 미확인)

> 사용자 요청 메시지의 "SubscribeToPostProcessingPass + EPostProcessingPass enum 27+ / FPostProcessMaterialInputs / 5.x AutoExposure·Bloom·TonemapPass / Material Domain=PostProcess 의 SVE 통합 경로" 항목 — vault `raw/ue-wiki-llm/` 에서 `EPostProcessingPass` / `SubscribeToPostProcessingPass` / `FPostProcessMaterialInputs` grep 0 hits. 내 일반 UE 5.x 지식으로 외삽한 부분이며 vault 자산으로 인용 불가.

### vault 검색했지만 결과 없음 — 추론에 의존

- **`ISceneViewExtension::SubscribeToPostProcessingPass(EPostProcessingPass PassId, FAfterPassCallbackDelegateArray& InOutCallbacks, bool bIsPassEnabled)`** — UE 5.x 가 도입한 *세분화된* PP Hook API. `PrePostProcessPass_RenderThread` 보다 정밀. — *vault 미확인.*
- **`EPostProcessingPass` enum** — `MotionBlur` / `Tonemap` / `FXAA` / `VisualizeDepth` / `VisualizeHDR` 등 다단계. 정확한 enum 멤버 수("27+") = 내가 부풀린 추측 — vault 미확인. 실제 멤버는 `PostProcessing.h` 헤더 직접 확인 필요.
- **`FPostProcessMaterialInputs`** — Material 기반 PP 입력 구조체 (SceneTexture 핸들 묶음). vault PostProcess.md §4 는 `FPostProcessingInputs` (다른 타입) 만 노출. 둘의 관계 = vault 미확정.
- **AutoExposure / Bloom / TonemapPass 의 RDG Pass 명세** — `FRDGTextureRef` 입출력 명세, 5.x AutoExposure 의 EyeAdaptation buffer 구조 — vault 미확인.
- **Material Domain=PostProcess 의 SVE 통합 경로** — `UMaterialExpressionCustomOutput` 파생 / `MaterialInputType` 의 PostProcess pin 등 — vault `Material.md` 와 `PostProcess.md` 둘 다 노출 안 함. SVE 가 내부적으로 Blendable Material 을 어느 시점에 RDG Pass 로 변환하는지의 정확한 경로 = 추론.

→ **filing-back 후보**: 이 §7 항목 중 사용자가 검증 sourcing 을 제공하면 (예: Epic 의 5.4 release notes / `SceneViewExtension.h` 헤더 발췌) → 🔴→🟢 승격 cycle. 별도 source 페이지 `ue-render-postprocessing-pass-api` 로 분리 검토.

---

## §8. 변경 이력

| 날짜 | 변경 | Tier 변동 |
|------|------|---------|
| 2026-05-10 | 최초 stub (29L, 6 claims) | — |
| 2026-05-12 | Cycle #5 slim enrich. §2 14 claims (🟢) + §2.5 2 (🟡) + §7 5 추론 (🔴) + 함정 8대 표 + 코드 + Cross-link 8. | 0/0/0 → 14/2/4 |
