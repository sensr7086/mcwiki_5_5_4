---
type: source
title: "UE Render — Mobile sub-skill"
slug: ue-render-mobile
source_path: raw/ue-wiki-llm/skills/Render/references/Mobile.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-12
related_concepts: ["[[concepts/Profiling-Scope-Rule]]", "[[concepts/PSO-Precache]]"]
tags: [ue, render, gpu, mobile, ios, android, quest, pso, vulkan]
---

# UE Render — Mobile

> Source: [[raw/ue-wiki-llm/skills/Render/references/Mobile.md]]
> Parent: [[sources/ue-render-skill]]
> Sibling: [[sources/ue-render-vulkan]] · [[sources/ue-render-vr]] · [[sources/ue-render-material]] · [[sources/ue-render-shader]] · [[sources/ue-render-lumennanite]]
> §13 tier: 본 카드의 모든 본문 주장 = 🟢 VAULT (raw L1-285 직접 매핑). 외삽 / 추론 = §5 / §6 에 별도 표시.

---

## §1. Summary

UE 5.7.4 Mobile 렌더 — iOS / Android / Quest 표준 파이프라인. 두 모드:

- **Mobile Forward** (default) — Tile-based, 단일 패스, 다이내믹 라이트 4개 제한, 메모리 ↓, iOS / Android 표준.
- **Mobile Deferred (5.x 신규)** — Deferred Shading on Mobile, 다이내믹 라이트 + AO + GBuffer, 메모리 +30~50MB, Quest 3+ / 고성능 Android.

핵심 의무 4종: **Lumen / Nanite 비활성 (Lightmap fallback)** · **Material Quality Level 분기 (Low / Medium)** · **PSO Bundled Cache** (런타임 컴파일 = 수백 ms hitch) · **Vulkan ES 표준** (OpenGL ES deprecated 5.x).

60 fps 임계 (raw §8): DrawCalls < 600 · Triangles < 1M · Texture Memory < 200MB · Mesh Memory < 100MB · 4 dynamic lights.

---

## §2. Key claims (9)

1. **Mobile Forward = 5.x 표준** — 단일 패스 Forward Shading, Tile-based light culling, 다이내믹 라이트 ≤ 4. `r.Mobile.ShadingPath=0` (raw §1.1, §5).
2. **Mobile Deferred = 5.x 신규** — `r.Mobile.SupportDeferredShading=1` + `r.Mobile.ShadingPath=1`. GBuffer + AO + 더 많은 동적 라이트. Quest 3+ / 고성능 Android (raw §1.2, §5).
3. **Lumen / Nanite Mobile 비활성 의무** — 두 모드 모두에서 ❌. Lightmap Static Lighting + LOD 0/1/2 Legacy 로 fallback. Mobile + Lumen 활성 = 빌드 실패 / 검은 화면 (raw §2.2, §9-1/2).
4. **Material Quality Level 분기 의무** — `MATERIAL_QUALITY_LEVEL_LOW / MEDIUM / EPIC` 매크로로 HLSL 분기. 누락 시 Low 폰에서 instruction count 초과로 컴파일 실패 또는 FPS 붕괴 (raw §2.1, §9-5).
5. **PSO Bundled Cache 의무** — `r.PSOPrecache=1` + Cooked Build `-BuildPSOCache`. 런타임 PSO 컴파일은 Mobile 에서 수백 ms hitch → 60 fps 불가 (raw §3, §9-3).
6. **Texture Compression = ASTC / ETC2** — iOS = ASTC / Android Vulkan ES 3.1+ = ASTC / 저사양 Android = ETC2 / Quest = ASTC. BC 계열 사용 금지 (raw §4.1, §9-6).
7. **Streaming Pool = 200MB 제한** — `r.Streaming.PoolSize=200` + `r.Streaming.LimitPoolSizeToVRAM=1`. PC 기본 (1GB) 그대로 두면 메모리 폭증 (raw §4.2, §9-7).
8. **Mobile PostProcess 제한** — Bloom / DOF / SSR / SSAO 비활성. Tone Mapper + Color Grading (LUT) + Vignette 만 허용. Mobile Deferred 모드 한정으로 5.x Mobile AO 허용 (raw §6).
9. **Vulkan ES 표준 + OpenGL ES deprecated** — `r.Mobile.AllowGLES=0` + `r.Mobile.UseVulkan=1`. USF 분기 = `PLATFORM_IS_MOBILE` / `FEATURE_LEVEL == FEATURE_LEVEL_ES3_1` (raw §7, §9-10).

---

## §3. 함정 (raw §9 10대 압축)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Mobile + Lumen / Nanite 활성 | 비활성 + Lightmap fallback |
| 2 | PSO Cache 비활성 → 런타임 컴파일 stall | r.PSOPrecache=1 + Bundled Cache 빌드 |
| 3 | Material Quality 분기 누락 | MATERIAL_QUALITY_LEVEL 매크로 의무 |
| 4 | Texture = BC (Mobile X) | ASTC / ETC2 |
| 5 | Streaming Pool 기본값 (1GB) | Mobile = 200MB |
| 6 | Multiple Dynamic Lights > 4 | Forward = 4 제한 (Deferred 만 초과 가능) |
| 7 | Tessellation / 과도한 WPO | Mobile = 비활성 또는 최소 |
| 8 | Custom HLSL = Mobile 비호환 함수 | FEATURE_LEVEL + PLATFORM_IS_MOBILE 분기 |
| 9 | OpenGL ES (5.x deprecated) | Vulkan ES |
| 10 | Bloom Quality 1+ on Mobile | Quality 0 (비활성) |

---

## §4. 코드 / INI 예 (raw 발췌)

```ini
; DefaultEngine.ini — Mobile 표준 셋업
[/Script/Engine.RendererSettings]
r.Mobile.ShadingPath=0              ; 0 = Forward (표준) / 1 = Deferred (5.x)
r.Mobile.SupportDeferredShading=0   ; Quest 3+ 만 1
r.Mobile.UseVulkan=1                ; Vulkan ES 표준
r.Mobile.AllowGLES=0                ; OpenGL ES deprecated
r.PSOPrecache=1                     ; Bundled PSO Cache
r.PSOPrecache.GlobalShaders=1
r.Streaming.PoolSize=200            ; Mobile 200MB 제한
r.Streaming.LimitPoolSizeToVRAM=1
r.Mobile.BloomQuality=0
r.Mobile.DepthOfField=0
r.Mobile.SSR=0
```

```hlsl
// Material Editor — Material Quality Level 분기
#if (MATERIAL_QUALITY_LEVEL == MATERIAL_QUALITY_LEVEL_LOW)
    return BaseColor;                              // Mobile Low
#elif (MATERIAL_QUALITY_LEVEL == MATERIAL_QUALITY_LEVEL_MEDIUM)
    return BaseColor + Detail * 0.5;               // Mobile Medium
#else
    return BaseColor + Detail + Reflection;        // PC Epic
#endif

// USF — Mobile 플랫폼 분기
#if PLATFORM_IS_MOBILE
    // Vulkan ES / OpenGL ES 호환 — 일부 함수 제한
#endif
#if FEATURE_LEVEL == FEATURE_LEVEL_ES3_1
    // Mobile 전용
#endif
```

```bash
# Cooked Build + PSO Cache 자동 생성
RunUAT.bat BuildCookRun -project=<.uproject> -platform=Android \
  -clientconfig=Shipping -build -cook -package -stage -BuildPSOCache
```

---

## §5. Cross-link

- 부모: [[sources/ue-render-skill]] — Render 11 sub-skill 인덱스
- 형제: [[sources/ue-render-vulkan]] (Mobile RHI 백엔드) · [[sources/ue-render-vr]] (Quest = Mobile VR) · [[sources/ue-render-material]] (Quality Level 정밀판) · [[sources/ue-render-shader]] (Permutation Mobile) · [[sources/ue-render-lumennanite]] (Mobile 비활성 매트릭스)
- 정책: [[raw/ue-wiki-llm/references/12_AssetOptimizationPolicy.md|AssetOptimization]] (LOD + Streaming + Audio Concurrency) · [[raw/ue-wiki-llm/references/07_ProfilingScopeRule.md|ProfilingScope]] (Mobile Tick 첫 줄)
- 에셋: [[sources/ue-assetclasses-texture]] — Mobile Compression Settings · [[sources/ue-assetclasses-mesh]] — LOD Group `NAME_LandscapeMobile`

---

## §6. 신뢰도 매트릭스

| 주장 | Tier | 근거 |
|------|------|------|
| Mobile Forward 4 lights 제한 | 🟢 | raw §1.1, §9-9 |
| Mobile Deferred = 5.x 신규 + Quest 3+ | 🟢 | raw §1.2, §5 |
| Lumen / Nanite Mobile 비활성 | 🟢 | raw §2.2 매트릭스 |
| PSO Bundled Cache 의무 | 🟢 | raw §3, §9-3 |
| ASTC / ETC2 권장 | 🟢 | raw §4.1 |
| Streaming Pool 200MB | 🟢 | raw §4.2 |
| Vulkan ES + OpenGL ES deprecated 5.x | 🟡 | raw §7 (deprecated 시점 = 외삽, 5.0~5.4 사이 추정) |
| 60 fps DrawCalls < 600 | 🟢 | raw §8 매트릭스 |
| Quest 3+ Mobile Deferred 권장 | 🟡 | raw §1.2 "Quest 3+ / 일부 안드로이드" — Quest 3 SoC 사양 검증 = vault 미확인 |

---

## §7. (Boundary) 보너스 발견

specialist (`ue-render-mobile`) raw 를 §5.4 POST-RECEIVE 분해하며 vault 가 따로 캡처하면 좋은 *교차 패턴* 3건:

1. **Quest = Mobile VR 합성 zone** — Quest 1/2 = Vulkan ES + Mobile Forward + Stereo Instancing + Foveated Rendering. Render/Mobile + Render/VR + Render/Vulkan 3 sub-skill 이 *동일 디바이스* 에서 합쳐지는 유일 케이스. → `quest-render-stack` synthesis 후보 (vault 미생성) (Mobile Forward + Multi-View + FFR + Vulkan ES + PSO Bundled = 5단 의무).
2. **PSO Precache 의존성 사슬 (Mobile + VR + Cooked Build)** — Mobile.md §3 / Vulkan.md / VR.md 가 모두 `r.PSOPrecache=1` + `-BuildPSOCache` 를 *독립적으로* 요구. Cycle #8 Vulkan 카드의 PSO Precache claim, 본 Cycle #9 의 Bundled PSO Cache, 향후 Cycle (VR) 의 90/120 fps 시작 hitch 회피가 동일 메커니즘 → [[concepts/PSO-Precache]] 단일 SSoT (현재 3개 source 가 중복 기술).
3. **Mobile Material Quality 매크로의 4단 분리 페어** — `MATERIAL_QUALITY_LEVEL_LOW/MEDIUM/HIGH/EPIC` 은 [[sources/ue-render-material]] §3 의 Material Quality Switch 노드와 동일 의미론. raw 양쪽이 *서로 cross-link 안 함*. wiki/sources 측에서 양방향 wikilink 추가 = silent gap 메우기.

🟢 ALL — raw 직접 매핑 또는 sibling source 카드 비교로 확인된 발견. § 13 위반 없음.
