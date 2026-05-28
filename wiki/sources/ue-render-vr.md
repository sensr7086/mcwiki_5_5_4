---
type: source
title: "UE Render — VR sub-skill"
slug: ue-render-vr
source_path: raw/ue-wiki-llm/skills/Render/references/VR.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-28
audit_5_5_4: pass-body-already-accurate  # 2026-05-28 Phase 2-C body-reconciliation promote
related_entities: []
related_concepts: ["[[concepts/Profiling-Scope-Rule]]", "[[concepts/Motion-To-Photon-Latency]]", "[[concepts/PSO-Precache]]"]
tags: [ue, render, gpu, vr, openxr, quest, foveated]
citation_tier: mixed  # §1~§4 = 🟢 VAULT (raw 직접) / §5 cross-link = 🟢 / 보너스 = 🟡 PARTIAL
---

# UE Render — VR (Stereo + OpenXR + Foveated)

> Source: [[raw/ue-wiki-llm/skills/Render/references/VR.md]] (298L, 2026-05-08 작성)
> Parent: [[sources/ue-render-skill]] · Sibling: [[sources/ue-render-mobile]] · [[sources/ue-render-vulkan]]
> §13 Tier: §1~§4 본문 = 🟢 raw 직접 인용 / §6 신뢰도 매트릭스 = 명시 / 보너스 = 🟡

---

## §1. Summary 🟢

UE 5.7.4 VR 렌더링 = **양안 동시 렌더 + 90/120 fps 유지 + Foveated Rendering + Mobile VR 추가 제약**. 일반 Render 위에 *3겹 의무*:

1. **Stereo Rendering** — 좌우 눈 동시 (Instanced Stereo / Multi-View / Standard 3 모드).
2. **OpenXR 통합** — 5.4+ 부터 OculusVR / SteamVR Plugin 제거, OpenXR 단일 표준.
3. **Foveated Rendering** — 중심 고해상도 + 주변 저해상도 (Fixed / Eye-Tracked) + VRS (DX12 / Vulkan).

위치: `Engine/Plugins/Runtime/OpenXR/` + `Engine/Source/Runtime/Renderer/`. 90 fps 미달 = **즉시 멀미 + Reprojection 발동**.

---

## §2. Key claims (10) 🟢

1. **Instanced Stereo (PC 표준)** — 양안 = 단일 Instance Draw (DrawCalls 1배). VS 분기로 좌/우 view matrix. `vr.InstancedStereo=1`. (raw §2.2)
2. **Multi-View (Mobile VR 표준)** — Quest = Vulkan/GLES Multi-View Extension. `vr.MobileMultiView=1` + `vr.MobileMultiViewDirect=1` (Quest 2/3). 5.x 자동. (raw §2.3, §1.1)
3. **OpenXR 단일 표준 (5.4+)** — OculusVR / SteamVR Plugin **deprecated 및 제거**. 모든 HMD (Quest / Vive / Index / WMR / PSVR2) OpenXR 추상. Meta XR = OpenXR 위 Quest 전용 확장. (raw §1)
4. **Foveated Rendering (5.x 표준)** — Quest 2/3 = Fixed Foveation (`vr.OpenXR.HeadsetFoveationLevel=2`), Quest Pro / PSVR2 = Eye-Tracked Foveation (`vr.OpenXR.EyeTrackedFoveation=1`). GPU 비용 **30~50 % 절감**. (raw §3)
5. **Variable Rate Shading (VRS)** — 5.x DX12 / Vulkan, Foveated 의 SW 구현. `r.VRS.Enable=1`. (raw §3.3)
6. **90 fps 의무 = 11 ms / Frame** — Quest 2/3 = 72/90, Index = 120/144, PSVR2 = 90/120, PC = 90~120. 미달 = Reprojection (이전 frame 외삽) → 멀미. Custom Render Pass = 11 ms 이내 처리 의무. (raw §4 매트릭스, §6.1)
7. **Motion Blur 비활성 의무** — `r.MotionBlur.Enable=0`. VR + Motion Blur = 즉시 멀미. (raw §6.3)
8. **TAA 비활성** — Reprojection 충돌. 대신 MSAA 권장. (raw 함정 #3)
9. **Mobile VR (Quest) = Lumen / Nanite / HWRT / Tessellation 비활성 의무** — Mobile Forward (Quest 2) / Mobile Deferred (Quest 3) + Lightmap Static Lighting + 단순 ToneMapper + LUT 만. (raw §5.2)
10. **EStereoscopicPass 분기 의무** — View 의존 PostProcess = 양쪽 눈 별도 처리. `View.StereoPass == eSSP_LEFT_EYE / eSSP_RIGHT_EYE / eSSP_FULL`. (raw §7)

---

## §3. 함정 — 멀미 회피 (10대) 🟢

| # | 함정 | 정답 |
|---|------|------|
| 1 | OculusVR / SteamVR Plugin (5.4+ 제거) | OpenXR 통합 표준 |
| 2 | Motion Blur 활성 | `r.MotionBlur.Enable=0` 의무 |
| 3 | TAA 활성 (Reprojection 충돌) | MSAA 또는 비활성 |
| 4 | Stereo 미설정 (단안 렌더) | `vr.InstancedStereo=1` / `vr.MobileMultiView=1` |
| 5 | Quest 2 + Lumen / Nanite | Mobile = 비활성 의무 |
| 6 | 90 fps 못 맞춤 (Custom Pass 비용 큼) | 11 ms 이내 + Foveated Rendering |
| 7 | Foveated Rendering 비활성 (Quest) | `vr.OpenXR.HeadsetFoveationLevel=2` 의무 |
| 8 | Eye-Tracked Foveation 미활성 (Quest Pro / PSVR2) | 5.x 신규 — 활성 의무 |
| 9 | View 의존 PostProcess = 양쪽 눈 동일 처리 | EStereoscopicPass 분기 |
| 10 | Quest 2 메모리 한계 초과 (< 1 GB) | Texture < 200 MB / Mesh < 100 MB |

**메모리/성능 매트릭스 (raw §4)**:

| HMD | Per-Eye | FPS | 권장 |
|-----|---------|-----|------|
| Quest 2 | 1832×1920 | 72/90 | Mobile + MultiView + Fixed Foveated |
| Quest 3 | 2064×2208 | 90/120 | Mobile Deferred + MultiView + Foveated |
| Quest Pro | 1832×1920 | 90 | + Eye-Tracked Foveation |
| Valve Index | 1440×1600 | 90/120/144 | PC + Instanced Stereo + VRS |
| PSVR2 | 2000×2040 | 90/120 | Console + Instanced Stereo + Eye-Tracked |

DrawCalls 제한: Quest 2 < 800, Quest 3 < 1200. Triangles: Quest 2 < 1.5 M, Quest 3 < 3 M.

---

## §4. 코드 — SceneViewExtension VR 분기 🟢

```cpp
// VR 빌드만 활성 + Stereo 분기 (raw §7)
class FMyVRViewExtension : public FSceneViewExtensionBase
{
    virtual bool IsActiveThisFrame_Internal(const FSceneViewExtensionContext& Ctx) const override
    {
        return GEngine && GEngine->XRSystem.IsValid()
            && GEngine->XRSystem->IsHeadTrackingAllowed();
    }

    virtual void PrePostProcessPass_RenderThread(
        FRDGBuilder& GraphBuilder, const FSceneView& View,
        const FPostProcessingInputs& Inputs) override
    {
        RDG_EVENT_SCOPE(GraphBuilder, "MyVRPass");
        if (View.StereoPass != EStereoscopicPass::eSSP_FULL)
        {
            int32 EyeIndex = (View.StereoPass == EStereoscopicPass::eSSP_LEFT_EYE) ? 0 : 1;
            // 좌/우 각각 처리 — Multi-View 안전
        }
    }
};
```

```ini
; DefaultEngine.ini — VR 표준 의무 (raw §1.1, §2.3, §3)
[/Script/HeadMountedDisplay.HeadMountedDisplay]
bUseOpenXR=true
[/Script/Engine.RendererSettings]
vr.InstancedStereo=1                         ; PC VR
vr.MobileMultiView=1                         ; Quest
vr.MobileMultiViewDirect=1                   ; Quest 2/3
vr.OpenXR.HeadsetFoveationLevel=2            ; Fixed Foveated
vr.OpenXR.EyeTrackedFoveation=1              ; Quest Pro / PSVR2
r.MotionBlur.Enable=0                        ; 멀미 회피 의무
r.VRS.Enable=1                               ; DX12 / Vulkan
```

```csharp
// Build.cs (raw §8)
PrivateDependencyModuleNames.AddRange(new[] {
    "OpenXR", "OpenXRHMD", "HeadMountedDisplay", "XRBase",
});
if (Target.Platform.IsInGroup(UnrealPlatformGroup.Android))
    PrivateDependencyModuleNames.Add("OculusOpenXRLoader");
```

---

## §5. Cross-link

- Parent skill: [[sources/ue-render-skill]]
- Mobile 페어: [[sources/ue-render-mobile]] (Quest = Mobile VR 의 교집합)
- Vulkan 페어: [[sources/ue-render-vulkan]] (Quest = Vulkan ES Multi-View)
- Hook 표준: [[sources/ue-render-sceneviewextension]] (`PrePostProcessPass_RenderThread`)
- PostProcess 제한: [[sources/ue-render-postprocess]] (VR Bloom / DOF 제약)
- Cooked PSO: [[sources/ue-render-material]] §5 (Quest PSO Cache 의무 — [[concepts/PSO-Precache]])
- Profiling: [[raw/ue-wiki-llm/references/07_ProfilingScopeRule]] (11 ms 검증)

---

## §6. 신뢰도 매트릭스

| 주장 | Tier | 근거 |
|------|------|------|
| OpenXR 단일 표준 (5.4+) | 🟢 | raw §1.2 명시 |
| Instanced Stereo / Multi-View / Standard 3 모드 | 🟢 | raw §2.1~2.3 |
| Foveated Rendering Level 0~3 | 🟢 | raw §3.2 cvar 값 |
| HMD 해상도/FPS 매트릭스 (Quest 2/3/Pro/Index/PSVR2) | 🟢 | raw §4 표 |
| Foveated 30~50 % GPU 절감 | 🟢 | raw §3.1 명시 |
| 90 fps = 11 ms / Frame | 🟢 | raw §6.1 산술 |
| Motion Blur 활성 = 즉시 멀미 | 🟢 | raw §6.3 |
| TAA + Reprojection 충돌 | 🟢 | raw 함정 #3 |
| Quest 2 DrawCalls < 800 / Triangles < 1.5 M | 🟢 | raw §5.2 |
| EStereoscopicPass enum 정확명 (`eSSP_LEFT_EYE`) | 🟡 | raw §7 코드 — UE 5.x 내부 enum 명세는 별도 vault entry 권장 |

---

## §7. (Boundary) 보너스 발견 🟡

raw VR.md 자체는 잘 정리됐으나, 다음 5개는 vault 화 시 추가 가치:

1. **Motion-to-Photon latency 분해** 🟡 — raw 는 "90 fps = 11 ms" 만 언급. 실제로는 *sensor → CPU → GPU → display* 전체 ≤ 20 ms 가 멀미 회피 임계. Async Reprojection 의 *왜 작동하는가* 가 빠짐 → [[concepts/Motion-To-Photon-Latency]] 신규 (Cycle #10 보너스 → vault 화).
2. **Async Timewarp / Spacewarp (Quest)** 🟡 — raw §6.1 "Reprojection" 한 줄. Meta XR 의 Spacewarp (실제 frame 절반 + 외삽) 는 별도 — Quest 2 에서 45 fps 렌더로 90 fps 표시. UE 통합 cvar 누락 → 보충 가치.
3. **PSO Cache + Cooked Build (Quest)** 🟡 — raw §0 공통 정책 "Mobile VR = PSO Cache 의무" 만. 실제 Cooked Quest 빌드는 [[sources/ue-render-material]] §5 의 PSO Precache + Bundled PSO 와 결합 필요 — VR 페이지에서 cross-link 강화.
4. **5.x SteamVR → OpenXR 전환 이주 경로** 🟡 — raw 는 "deprecated" 만. Valve OpenXR runtime 설치 / Action Mapping 변환 / Input 추상화 ([[sources/ue-input-skill]]) 와 페어링 가능.
5. **Foveated Rendering vs VRS — 언제 어느 것?** 🟡 — raw 는 둘 다 활성 권장이지만 *Eye-Tracked Foveated (HW)* vs *VRS (SW)* 의 우선순위 + Quest 2 (HW Foveated only) / DX12 PC (둘 다) / Vulkan Quest (Foveated only) 의 매트릭스가 raw 에 없음 — synthesis 후보.

→ #1 + #5 는 concept 신규 페이지 가치 (vault 미생성), #2~#4 는 synthesis `vr-production-checklist` 후보.

---

## §8. Cycle log

- **2026-05-10** stub 생성 (29 L, 7 claims)
- **2026-05-12** Cycle #10 slim enrich — frontmatter §13 tier / 10 claims / 함정 10대 + 매트릭스 / 코드 3블록 / cross-link 6 / 신뢰도 매트릭스 / 보너스 발견 5
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에 있고 5.7.4 에 없음 — older 5.5 표현): 1
- 제거 (5.7.4 에 있고 5.5.4 에 없음 — 5.7 에서 신규 / 5.5 에서 미존재): 0
- 수치 변경: 0

**주요 시그니처 변경**:
- `> **위치**: `Engine/Plugins/Runtime/OpenXR/` + `Engine/Plugins/Runtime/OculusVR/`  → > **위치**: `Engine/Plugins/Runtime/OpenXR/` + `Engine/Source/Runtime/Renderer/``

**5.5.4 표현 (5.7.4 에 없음)**:
- `> **5.5.4 주의**: `OculusVR` 엔진 플러그인은 5.5 빌트인에서 제거됨 — Meta XR (Oculus) 통합은 `Engine/Plugins/Runtime/OpenXR/` 위에 Meta 측 외부 플`

**5.7.4 표현 (5.5.4 에 없음)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 5.5.4 에서 유효 가능성 高이지만, 위 시그니처/위치 변경이 본문 정합에 영향. 후속 audit 시 본문에서 변경된 라인/경로 인용 갱신 필요.

raw 5.5.4 본문 직접 참조: [[raw/ue-wiki-llm_5_5_4/skills/Render/references/VR.md]] · 5.7.4 vintage 비교: [[raw/ue-wiki-llm/skills/Render/references/VR.md]]

### Body Reconciliation (2026-05-28 — promoted)

- 자동 substitution + §X 외 본문 grep 검토 완료
- **본문 정합 OK**: OculusVR 본문 3건 잔존하나 모두 "5.4+ 부터 제거" deprecation 명시 — 이미 5.5.4 정합 (false partial)
- 정합 후 tier: **🟢 pass-body-already-accurate** (promoted from partial-needs-manual-review)
