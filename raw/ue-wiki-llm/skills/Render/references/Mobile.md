---
name: render-mobile
description: Mobile 렌더링 — Mobile Forward + 5.x Mobile Deferred + Mobile Material + Vulkan ES + Tile Renderer + Mobile PSO. iOS/Android 60fps 유지 + 메모리 한계 + Lumen/Nanite 비활성 + Lightmap fallback.
---

# Render/Mobile — Mobile Forward + 5.x Mobile Deferred + Vulkan ES

> **위치**: `Engine/Source/Runtime/Renderer/Private/Mobile*` + Mobile Material 확장
> **요지**: Mobile (iOS / Android / Quest) 렌더링 표준 — PC 와 다른 파이프라인 + 메모리 한계 + Tile Renderer + 5.x 신규 Mobile Deferred.

---

## 🚨 공통 정책

| 정책 | Mobile 적용 |
|------|-----------|
| 🚨 Lumen / Nanite | **모두 비활성** (Lightmap fallback 의무) |
| 🚨 Mobile Quality | Material Quality Level = Low / Medium 분기 의무 |
| 🚨 PSO Cache | **Bundled PSO Cache 의무** (런타임 PSO 컴파일 = 60fps 못 맞춤) |
| 🚨 메모리 | Texture < 200MB / Mesh < 100MB / Animation < 50MB |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) | LOD + Texture Streaming + Audio Concurrency |

---

## 1. Mobile 렌더링 두 모드

### 1.1 Mobile Forward (5.x 표준 — 가장 흔함)
- 단일 패스 렌더 (Forward Shading)
- 메모리 ↓ / 다이내믹 라이트 제한 (4개)
- iOS / Android 표준
- Material Domain `MD_Surface` + Mobile Quality

### 1.2 Mobile Deferred (5.x 신규 — Quest 3+ / 고성능 Android)
- Deferred Shading (Mobile)
- 더 많은 다이내믹 라이트
- 메모리 ↑ (G-Buffer)
- 일부 안드로이드 / Quest 3+
- 활성: `r.Mobile.SupportDeferredShading=1`

```ini
; DefaultEngine.ini
[/Script/Engine.RendererSettings]
r.Mobile.ShadingPath=0     ; 0 = Forward (표준), 1 = Deferred (5.x)
r.Mobile.SupportDeferredShading=0   ; 1 = 활성 (Quest 3+ / 일부)
```

---

## 2. Mobile Material 작성

### 2.1 Material Quality Level 분기 (의무)

```hlsl
// Material Editor 안 — Material Quality 노드 사용
#if (MATERIAL_QUALITY_LEVEL == MATERIAL_QUALITY_LEVEL_LOW)
    // Mobile Low (저사양 폰)
    return BaseColor;
#elif (MATERIAL_QUALITY_LEVEL == MATERIAL_QUALITY_LEVEL_MEDIUM)
    // Mobile Medium / 일반
    return BaseColor + Detail * 0.5;
#else
    // PC Epic / Cinematic
    return BaseColor + Detail + Reflection;
#endif
```

### 2.2 Mobile 호환 매트릭스

| 기능 | Mobile Forward | Mobile Deferred (5.x) | PC SM5+ |
|------|:------:|:------:|:------:|
| Lumen | ❌ | ❌ | ✅ |
| Nanite | ❌ | ❌ | ✅ |
| Hardware Ray Tracing | ❌ | ❌ | ✅ |
| Tessellation | ❌ | ❌ | ⚠ |
| Custom HLSL | ⚠ | ⚠ | ✅ |
| Translucent | ✅ | ✅ | ✅ |
| Subsurface Scattering | ⚠ Limited | ✅ | ✅ |
| Multiple Dynamic Lights | ⚠ 4개 | ✅ | ✅ |
| Static Lighting (Lightmap) | ✅ ⭐ | ⚠ | ⚠ |
| World Position Offset | ✅ | ✅ | ✅ |

---

## 3. PSO Cache (Mobile 의무)

### 3.1 정의
- 모든 Material × Vertex Factory × LOD × Pass 조합 = PSO 사전 컴파일
- **런타임 PSO 컴파일 = Mobile 에선 매우 느림 (수백 ms 히칭)**
- 5.x = Bundled PSO Cache 표준

### 3.2 활성

```ini
; DefaultEngine.ini
[/Script/Engine.RendererSettings]
r.PSOPrecache=1
r.PSOPrecaching.LazyLoadShadersWhenPSOPrecacheRequested=0
r.PSOPrecache.GlobalShaders=1
r.PSOPrecache.MaterialPSOPrecacheTextureLogging=1   ; 디버그
```

```ini
; DefaultGame.ini
[/Script/Engine.GameUserSettings]
bUseShaderPipelineCache=true
```

### 3.3 PSO Cache 빌드

```bash
# Cooked Build 후 자동 생성
"<UE>/Engine/Build/BatchFiles/RunUAT.bat" BuildCookRun ^
  -project="<.uproject>" -platform=Android -clientconfig=Shipping ^
  -build -cook -package -stage ^
  -BuildPSOCache
```

---

## 4. Mobile Texture / Mesh 최적화 (의무)

### 4.1 Texture Compression (Mobile)

| 플랫폼 | 권장 Compression |
|--------|----------------|
| iOS | ASTC (가장 효율) |
| Android | ASTC (Vulkan ES 3.1+) / ETC2 (저사양) |
| Quest | ASTC |

```cpp
// UTexture2D 측 (Editor 작업)
Texture->LODGroup = TEXTUREGROUP_World;          // 자동 압축 적용
Texture->CompressionSettings = TC_Default;        // BC1 / ASTC 자동
```

### 4.2 Texture Streaming Pool

```ini
; DefaultEngine.ini
[/Script/Engine.RendererSettings]
r.Streaming.PoolSize=200            ; Mobile = 200MB 제한
r.Streaming.LimitPoolSizeToVRAM=1
```

### 4.3 Mesh LOD (Mobile 강제)

```cpp
// LOD Group = TEXTUREGROUP_World 자동
StaticMesh->LODSettings = MyLODSettings;
StaticMesh->LODGroup = NAME_LandscapeMobile;     // Mobile 전용 LOD 그룹
```

---

## 5. 5.x Mobile Deferred 활성 (Quest 3+ / 고성능 Android)

```ini
[/Script/Engine.RendererSettings]
r.Mobile.SupportDeferredShading=1
r.Mobile.UseHWsRGBEncoding=1
r.Mobile.ShadingPath=1                ; 1 = Deferred
r.Mobile.GTSAOQuality=2               ; SSAO Mobile
r.Mobile.AmbientOcclusion=1
r.Mobile.AmbientOcclusionQuality=2
```

→ 메모리 + 30~50MB / 다이내믹 라이트 + GBuffer + AO 사용 가능.

---

## 6. Mobile PostProcess 제한

### 6.1 비용 큰 PostProcess (Mobile X)
- Bloom (Quality 1+)
- Depth of Field
- Screen Space Reflection (SSR)
- Screen Space Ambient Occlusion (SSAO) — Mobile Quality 1+ 만

### 6.2 Mobile 권장 PostProcess
- Tone Mapper (필수)
- Color Grading (LUT)
- Vignette (선택)
- 5.x Mobile AO (Mobile Deferred 전용)

```ini
; Mobile Quality 분기
[/Script/Engine.RendererSettings]
r.Mobile.BloomQuality=0               ; 0 = 비활성, 1 = Low
r.Mobile.DepthOfField=0
r.Mobile.SSR=0
r.Mobile.AmbientOcclusion=0           ; Forward = 0 / Deferred = 1+
```

---

## 7. Vulkan ES (Mobile 표준)

### 7.1 활성

```ini
[/Script/Engine.RendererSettings]
r.Mobile.AllowGLES=0                  ; 5.x — OpenGL ES deprecated
r.Mobile.UseVulkan=1
```

### 7.2 셰이더 호환

```hlsl
// USF 안 Mobile 분기
#if PLATFORM_IS_MOBILE
    // Vulkan ES / OpenGL ES 호환 — 일부 함수 제한
#endif

#if FEATURE_LEVEL == FEATURE_LEVEL_ES3_1
    // Mobile 전용
#endif
```

---

## 8. Mobile Render 최적화 체크리스트 (60fps 유지)

| 항목 | 권장 | Mobile Low | Mobile Mid (Quest) |
|------|-----|-----------|------------------|
| Resolution | 1280x720 | 960x540 | 1832x1920 (Quest 2) |
| Frame Rate | 60fps | 30fps | 72/90fps (Quest) |
| DrawCalls | < 600 | < 400 | < 800 |
| Triangles | < 1M | < 500K | < 2M |
| Texture Memory | < 200MB | < 100MB | < 300MB |
| Mesh Memory | < 100MB | < 50MB | < 150MB |
| Material Quality | Low / Medium | Low | Medium |
| Shadows | Static Lightmap | Static only | Mobile Dynamic (Quest) |
| PostProcess | ToneMapper + LUT | ToneMapper only | + AO + Vignette |

---

## 9. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Mobile 빌드 + Lumen 활성 | 비활성 의무 (Lightmap fallback) |
| 2 | Mobile + Nanite 활성 | 비활성 의무 (LOD 0/1/2 Legacy) |
| 3 | PSO Cache 비활성 → 런타임 컴파일 stall | r.PSOPrecache=1 + Bundled Cache |
| 4 | Custom Shader = Mobile 비호환 함수 | FEATURE_LEVEL 분기 + PLATFORM_IS_MOBILE |
| 5 | Material Quality 분기 누락 | Mobile Low / Medium 분기 의무 |
| 6 | Texture Compression = BC (Mobile X) | ASTC / ETC2 권장 |
| 7 | Streaming Pool = 1GB (Mobile X) | Mobile = 200MB 제한 |
| 8 | Tessellation / WPO 과도 | Mobile = 비활성 / 단순 사용 |
| 9 | Multiple Dynamic Lights = 4개 초과 | Mobile Forward = 4개 제한 |
| 10 | OpenGL ES 사용 (5.x deprecated) | Vulkan ES 표준 |

---

## 10. 체크리스트

- [ ] r.Mobile.UseVulkan=1 (Vulkan ES 표준)
- [ ] Lumen / Nanite 비활성 (Project Settings)
- [ ] Lightmap Static Lighting 사용
- [ ] PSO Precache 활성 + Bundled PSO Cache 빌드
- [ ] Material Quality Level 분기 (Low / Medium)
- [ ] Texture Compression = ASTC / ETC2
- [ ] Streaming Pool = 200MB 제한
- [ ] DrawCalls < 600 / Triangles < 1M
- [ ] Mobile PostProcess = ToneMapper + LUT 만
- [ ] Multiple Dynamic Lights ≤ 4
- [ ] FEATURE_LEVEL == ES3_1 분기 (USF)

---

## 11. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- [`Render/references/Vulkan.md`](../Vulkan/SKILL.md) — Vulkan ES (Mobile RHI)
- [`Render/references/Material.md`](../Material/SKILL.md) — Material Quality Level
- [`Render/references/Shader.md`](../Shader/SKILL.md) — Permutation (Mobile)
- [`Render/references/LumenNanite.md`](../LumenNanite/SKILL.md) — Mobile = 비활성
- [`AssetClasses/references/Texture.md`](../../AssetClasses/references/Texture.md) — Mobile Compression
- [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) — LOD + Streaming

## 12. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. Mobile Forward / Deferred (5.x) + Material Quality + PSO Cache + Vulkan ES + Texture/Mesh 최적화 + 60fps 매트릭스 + 함정 10대. |
