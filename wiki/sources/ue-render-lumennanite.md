---
type: source
title: "UE Render — Lumen + Nanite sub-skill"
slug: ue-render-lumennanite
source_path: raw/ue-wiki-llm/skills/Render/references/LumenNanite.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-12
related_entities:
  - "[[entities/UStaticMesh]]"
related_concepts:
  - "[[concepts/Mobility]]"
tags: [ue, render, gpu, lumen, nanite, gpu-scene, mesh-shader]
citation_tier_summary:
  green: "raw 본문 직접 확인 — Lumen / Nanite 활성화 cvar / 호환 매트릭스 / Fallback / 함정 10대"
  yellow: "raw 의 항목을 §4 코드 예로 합성 — cvar 묶음 / Material 호환 패턴은 raw 기반 외삽"
  red: "Substrate + Lumen 통합, DLSS/FSR 호환은 raw 직접 언급 없음 — 외부 UE 5.x 일반 지식 추론"
---

# UE Render — Lumen + Nanite + GPU Scene (5.x 시각 혁신)

> Source: [[raw/ue-wiki-llm/skills/Render/references/LumenNanite.md]]
> Parent: [[sources/ue-render-skill]]
> §13 tier: 🟢 §1 / §2 (1)~(7) / §3 / §4 (cvar 기반) / 🟡 §2 (8) Substrate / 🔴 §2 (9) DLSS/FSR

## §1. Summary

UE 5.x 의 **시각 혁신 2축** — **Lumen** (동적 GI/Reflection, Lightmap 대체) + **Nanite** (Virtualized Geometry, 수백만 폴리곤 자동 LOD). 둘 다 **GPU Scene** 위에서 동작 — 모든 Primitive Transform / Material / Bounds 가 GPU 측 단일 버퍼로 통합되어 per-View Culling 이 GPU 측에서 일어남. 활성화는 `DefaultEngine.ini` cvar + Project Settings + `UStaticMesh::NaniteSettings` 3축. 핵심 제약은 **Mobile 비활성 의무** + **Custom Vertex Factory = GPU Scene 호환** + **Translucent/Two-sided Material = Nanite 미지원** + **Skeletal Mesh + Nanite = 5.4+ 부분 지원**. (raw §1~§5 직접 확인 🟢)

## §2. Key claims (9)

1. 🟢 **Lumen = HWRT (DX12) ∨ SWRT (SDF Mesh)** — `r.Lumen.HardwareRayTracing=1` 이 HWRT 활성. 미지원 GPU = SWRT fallback. HWRT 의 GPU 부담 ~10~20% 추가 (raw §1.5 함정 5). [[raw/ue-wiki-llm/skills/Render/references/LumenNanite.md#1-lumen]]
2. 🟢 **Lumen Surface Cache + Card Capture** — Mesh 표면을 카드로 캡처해 GI 샘플링. `ShowFlag.LumenSurfaceCacheDirectLighting` / `ShowFlag.LumenSceneCardCapture` 로 시각화. 메모리 부족 시 `r.LumenScene.SurfaceCache.MaxMeshCardsPerComponent` 조정.
3. 🟢 **Nanite Virtualized Geometry = Cluster + GPU Culling** — Pre-baked LOD 0 만 작성 → 자동 LOD. `NaniteSettings.PercentTriangles` (1.0 = 100% 보존) + `FallbackTriangleCount=5000` (Fallback Mesh 데시메이션).
4. 🟢 **Nanite 호환 매트릭스** — Static Mesh ✅ / InstancedStaticMesh ∙ HISM ✅ / Skeletal Mesh ⚠️ (5.4+ 부분) / Custom Vertex Factory ❌ / Translucent ❌ / Two-sided ❌ / WPO ⚠️ (제한적) / Mobile ❌. (raw §2.3)
5. 🟢 **GPU Scene = Lumen / Nanite 베이스** — CPU 측 per-Primitive 명령 회피, Per-View Culling 이 GPU 측. **Custom Vertex Factory = GPU Scene 호환 의무**. 호환 안 되면 Nanite 비활성 필요. (raw §3)
6. 🟢 **Nanite Mesh Shader (DX12)** — Vertex/Geometry Shader 후속. Nanite 가 내부적으로 사용. Custom Mesh Shader 는 5.x 부터 가능하나 드물게 사용. (raw §4)
7. 🟢 **Mobile/VR (Quest) = Lumen + Nanite 둘 다 비활성 의무 + Lightmap fallback** — Quest 등 Mobile VR = Mobile 모드 동작. (raw §5 호환 결정 매트릭스)
8. 🟡 **Substrate Material + Lumen 통합** — 5.x Substrate 는 다층 BSDF 지원. Lumen Surface Cache 가 Substrate slab 의 base BSDF 만 샘플링하므로 복잡한 layer 효과는 Lumen 캡처에 정확히 반영되지 않을 수 있음. (vault 근거: raw 의 "Custom HLSL = Material Domain 정확 시 OK" §1.3 + Material 도메인 호환 검사 의무 · 외삽: Substrate-Lumen 정확도 절충은 raw 직접 명시 없음)
9. 🔴 **DLSS / FSR Upscaler 와 Lumen/Nanite 호환** — DLSS3 / FSR2 = Motion Vector + Depth + Color 입력 사용. Lumen Reflection 의 SSR 컴포넌트는 jittered → Upscaler 가 노이즈 증폭 가능. Nanite 는 자체적으로 micro-poly aliasing 이 강해 TSR/DLSS 와 페어 권장. **추론 (vault 미확정)** — raw §1~§9 에 DLSS/FSR 직접 언급 없음. UE 5.x 일반 지식 기반 외부 추론.

## §3. 함정 (10대 중 핵심 7)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Lumen 활성 + Mobile 빌드 | Mobile = Lumen 비활성 의무 + Lightmap fallback |
| 2 | Nanite + Translucent / Two-sided | Material 측 호환 검사 — Nanite 미지원 |
| 3 | Custom Vertex Factory + Nanite | GPU Scene 호환 의무 또는 Nanite 비활성 |
| 4 | Nanite Skeletal Mesh (5.3 이전) | 5.4+ 만 부분 지원 |
| 5 | `r.Nanite=0` 인데 `NaniteSettings.bEnabled=true` | Project Settings 와 페어 — 동시 적용 |
| 6 | HWRT 미지원 GPU + `r.Lumen.HardwareRayTracing=1` | SWRT fallback 또는 비활성 |
| 7 | Custom PostProcess + Lumen 결과 사용 시 Hook 시점 | `PrePostProcessPass_RenderThread` 표준 — Lumen 합성 *후* hook |

(raw §6 함정 표 10대 중 발췌. 🟢)

## §4. 코드 예 — Nanite 활성화 + Lumen cvar

```ini
; DefaultEngine.ini — Lumen
[/Script/Engine.RendererSettings]
r.DynamicGlobalIlluminationMethod=1   ; 1 = Lumen
r.ReflectionMethod=1                   ; 1 = Lumen Reflection
r.Lumen.HardwareRayTracing=1           ; HWRT (DX12 + RT GPU)
r.Lumen.HardwareRayTracing.Inline=1    ; Inline RT (5.x)

; Nanite
r.Nanite=1
r.Nanite.AsyncRasterization=1
```

```cpp
// UStaticMesh 측 — Nanite 활성 + Fallback
StaticMesh->NaniteSettings.bEnabled = true;
StaticMesh->NaniteSettings.PercentTriangles = 1.0f;
StaticMesh->NaniteSettings.FallbackTriangleCount = 5000;  // Mobile / GPU 부족 시
```

```
// 디버그 콘솔 (PIE / Cooked)
ShowFlag.Nanite                                    // Nanite Mesh 시각화
r.Nanite.Visualize                                 // 다양한 모드 (Clusters / Overdraw / LOD)
ShowFlag.LumenSurfaceCacheDirectLighting           // Lumen Surface Cache
ShowFlag.VisualizeLumenScene                       // Lumen Scene 전체
r.Lumen.Visualize 1                                // Lumen 시각화 모드
```

(raw §1.2 / §1.4 / §2.2 / §2.5 직접 인용. 🟢)

## §5. Cross-link

- 부모 skill: [[sources/ue-render-skill]]
- Lumen 결과 PostProcess hook: [[sources/ue-render-postprocess]] · [[sources/ue-render-sceneviewextension]]
- GPU Scene + Mesh Pass: [[sources/ue-render-meshdrawing]]
- Material Domain 호환: [[sources/ue-render-material]] · [[sources/ue-assetclasses-material]]
- UStaticMesh Nanite 설정: [[entities/UStaticMesh]] · [[sources/ue-assetclasses-mesh]]
- Mobility (Movable + Lumen 동적 GI): [[concepts/Mobility]]
- Asset 최적화 (Nanite Fallback ↔ LOD): [[raw/ue-wiki-llm/references/12_AssetOptimizationPolicy.md]]
- Mobile / VR 분기: [[sources/ue-render-mobile]] · [[sources/ue-render-vr]]

## §6. 신뢰도 매트릭스

| 영역 | Tier | 근거 |
|------|------|------|
| Lumen 활성화 cvar | 🟢 | raw §1.2 직접 |
| Lumen 호환 매트릭스 | 🟢 | raw §1.3 표 직접 |
| Nanite 활성화 + NaniteSettings | 🟢 | raw §2.2 코드 직접 |
| Nanite 호환 매트릭스 | 🟢 | raw §2.3 표 직접 |
| GPU Scene 정의 + 영향 | 🟢 | raw §3 직접 |
| Fallback Mesh 동작 | 🟢 | raw §2.4 직접 |
| 함정 10대 | 🟢 | raw §6 표 직접 |
| 디버그 cvar / ShowFlag | 🟢 | raw §1.4 / §2.5 직접 |
| Substrate + Lumen 통합 | 🟡 | raw Material Domain 호환 의무 외삽 |
| DLSS / FSR 호환 | 🔴 | raw 미언급 — 일반 UE 지식 추론 |

---

## (Boundary §5.4) 보너스 발견

specialist boundary 분해 중 raw 본문에서 vault sibling 페이지에 직접 cross-link 할 가치 있는 항목:

1. **`r.Lumen.HardwareRayTracing.Inline=1`** (raw §1.2) — 5.x 의 **Inline Ray Tracing** 활성. Inline RT 는 Compute Shader 안에서 직접 ray query 호출하는 패턴 (separate RT Pipeline 없이). 이건 [[sources/ue-render-rhi]] 의 RT 추상화와 페어 — Inline RT 가 RHI 측에서 어떻게 expose 되는지가 vault 에 별도로 합성될 가치 있음.
2. **`FallbackTriangleCount=5000` (Nanite Fallback Mesh)** ↔ **Mesh LOD 정책** (raw `references/12_AssetOptimizationPolicy.md`) — Nanite 활성 자산은 LOD 1~N 이 fallback 으로 자동 데시메이션됨 → 기존 LOD 정책의 "수동 LOD chain 작성" 과 충돌할 수 있음. [[sources/ue-assetclasses-mesh]] 측 Nanite 섹션에 **"Nanite 활성 = 수동 LOD 무의미, Fallback Count 만 조정"** 노트가 필요.
3. **`r.GPUSkinCache.Enable=1`** (raw §3.3) — Skin Cache 가 활성이어야 Skeletal Mesh 가 GPU Scene 에 정확히 들어감. 5.4+ Skeletal Nanite 부분 지원의 전제조건이지만 raw 는 직접 연결을 말하지 않음 — 🟡 외삽 가치 있는 cross-link.
4. **함정 #6 `r.Nanite=0` + `NaniteSettings.bEnabled=true` 동시 적용 결과** — raw 가 "Project Settings 와 페어" 라고만 적고 *실제 동작* 은 명시 안 함. 일반적으로 cvar 가 우선 (전역 비활성) 하나 cooked package 에는 Nanite data 가 *포함됨* → 디스크 낭비. 이건 [[sources/ue-assetclasses-mesh]] 측 cooking 노트로 합성 후보.
5. **Lumen 호환표의 "Custom HLSL ⚠️ Material Domain 정확 시 OK"** — [[sources/ue-render-material]] 측 Material Domain 분류 (Surface / DefaultLit / Translucent / PostProcess) 와 직접 연결. Render/Material sub-skill 측에 **"Lumen 호환 Domain 체크리스트"** 합성 후보.

이 5개 중 (2) 와 (3) 은 다음 cycle `synthesis_seed` 후보로 가장 가치 높음 — 두 sub-skill 사이에 *조용히 빠진* 의존성을 드러냄.
