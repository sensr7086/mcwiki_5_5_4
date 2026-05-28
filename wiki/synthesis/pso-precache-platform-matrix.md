---
type: synthesis
title: "PSO Precache 플랫폼 매트릭스 — DX12 / Vulkan / Metal / Mobile / VR 별 Pipeline 캐시 전략"
slug: pso-precache-platform-matrix
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-render-shader]]"
  - "[[sources/ue-render-material]]"
  - "[[sources/ue-render-rhi]]"
  - "[[sources/ue-render-vulkan]]"
  - "[[sources/ue-render-mobile]]"
  - "[[sources/ue-render-vr]]"
  - "[[sources/ue-build-skill]]"
entities:
  - "[[entities/UMaterial]]"
concepts:
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Build-Configurations]]"
status: living
tags: [synthesis, pso, precache, mobile, vr, vulkan, metal]
---

# PSO Precache 플랫폼 매트릭스

## 1. Thesis

PSO (Pipeline State Object) Precache 는 [[synthesis/cooked-first-frame-stability]] §3 의 PSO 사전 컴파일을 *플랫폼별로 다른 백엔드* 에 맞춰 적용하는 시스템. UE 5.x 에서 `r.PSOPrecaching=1` 은 모든 RHI 에서 활성화되지만, **실제 효과 / 측정 / 함정은 백엔드별로 크게 다름**. 5 백엔드 — **DX12 (PC Windows) / Vulkan (PC Linux + Android) / Metal (iOS + macOS) / Mobile Forward (Android Vulkan + iOS Metal subset) / VR (OpenXR Multi-View)**. 각각의 PSO 캐시 위치 / Precache 시점 / 첫 draw stall 비용 / 측정 도구 / 함정 매트릭스.

## 2. 5 백엔드 매트릭스

| 백엔드 | PSO 캐시 위치 | Precache 효과 | 첫 draw stall (없을 시) | 측정 |
| -- | -- | -- | -- | -- |
| **DX12** (Windows PC) | `r.D3D12.PSOCachePath` (.dxpso) | 큼 — 모든 GraphicsPipeline 사전 | 100~500 ms | `stat unit` + `D3D12 Validation Layer` |
| **Vulkan** (Linux/Android) | `VulkanPipelineCache.bin` | 큼 — `VkPipeline` 사전 | 200~1000 ms (모바일 더 큼) | `RenderDoc` + `vkconfig` |
| **Metal** (iOS/macOS) | `MetalPipelineCache.metallib` | 중 — Metal 자체가 lazy 컴파일 빠름 | 50~200 ms | Xcode GPU Frame Capture |
| **Mobile Forward** | Vulkan/Metal 의 subset | 매우 큼 — 모바일 GPU 가 stall 길게 | 500~2000 ms | `stat unit` + 디바이스 `adb` 로그 |
| **VR (OpenXR)** | DX12/Vulkan/Metal 베이스 | 매우 큼 — 90Hz 유지 의무 | 한 번이라도 stall = motion sickness | `XR Performance Toolkit` |

## 3. Project Settings (DefaultEngine.ini)

```ini
[/Script/Engine.RendererSettings]
r.PSOPrecaching=1                                              ; 모든 RHI 활성
r.PSOPrecaching.GlobalShaders=1
r.PSOPrecaching.UseBackgroundThreadForPSOCreation=1            ; worker thread (게임 스레드 안 막음)
r.PSOPrecaching.LogLevel=1                                      ; 디버그 로그
r.PSOPrecaching.Validation=0                                    ; Shipping=0, Dev=1 로 검증

; 플랫폼별 분기 (DefaultEngine.ini 안)
[/Script/Engine.RendererSettings_Mobile]
r.PSOPrecaching=1
r.PSOWarmup.WarmupAmortizationTime=2.0                          ; Match Start 후 2초 동안 분산

[/Script/Engine.RendererSettings_VR]
r.PSOPrecaching=1
r.PSOPrecaching.UseBackgroundThreadForPSOCreation=1            ; VR 은 worker thread 의무
```

## 4. 백엔드별 함정

### DX12 (Windows PC)
- **Pipeline State 변경 시 stall** — 같은 Material 이라도 다른 RenderTarget Format (예: HDR vs SDR) 면 새 PSO. Cooker 가 모든 조합 collect 하지 못 하면 누락
- **Shader Model 변경** — SM5 vs SM6 변경 시 모든 PSO 재컴파일

### Vulkan (Linux/Android)
- **`VkPipelineCache` 가 디바이스 종속** — Adreno vs Mali vs PowerVR 별 다른 .bin. Cooker 가 모든 디바이스 별 빌드 (Android 만 — iOS Metal 은 동일 GPU 가족)
- **`bUseVulkanPSOFileCache`** — 디바이스 첫 부팅 시 PSO 캐시 빌드 — *최초 부팅 30초~ 부팅 시간 폭발*. Pre-Generated cache 를 .pak 안에 포함

### Metal (iOS/macOS)
- **Metal 의 Lazy Pipeline Compile** — 첫 draw 에 컴파일 — 다른 백엔드보다 stall 작지만 *0 은 아님*. Precache 효과 50~200 ms
- **Apple Silicon (M1/M2/M3)** vs Intel Mac vs iOS — 각각 별도 캐시

### Mobile Forward
- **Forward Renderer 한정** — Deferred 의 GBuffer PSO 는 Mobile Deferred 에서만 (Vulkan with `r.Mobile.SupportDeferred=1`)
- **Tile-based GPU** (Mali/Adreno) — TileSize / RenderPass 변경 시 새 PSO. 모바일 특이

### VR (OpenXR)
- **Multi-View Rendering** — 같은 Material 의 Stereo PSO + Mono PSO 별도. Multi-View 활성 시 Stereo PSO 만 Precache
- **Foveated Rendering 5.x** — Variable Rate Shading 사용 PSO 추가
- **90Hz Frame budget** — 첫 stall 한 번도 허용 안 됨. Background thread compile 의무

## 5. 측정 절차 (각 백엔드)

```cpp
// Cooker 단계 — Precache 대상 collect 검증
// PIE 또는 Editor 빌드 시:
// 콘솔: r.ShaderCompiler.CacheSavePath (대상 path 출력)
// Cooker log: "PrecachePSO: collected N pipelines for AssetXxx"

// 런타임 — 첫 frame stall 측정
// 콘솔: stat startfile / stat stopfile
// Frontend Profiler 로 분석 — D3D12CompilePipelineState / vkCreateGraphicsPipelines 가 stack 에 보이면 누락

// 5.x 신규 — PSO Precache 검증 콘솔
// 콘솔: r.PSOPrecaching.Validation=1
//   → 첫 draw 시 PSO 가 Precache 됐는지 검증, 안 된 PSO 는 Warning 로그
```

## 6. 결정 트리 — 어디까지 Precache 할까

```
[Q1] 빌드 플랫폼?
├── PC Windows (DX12) → Cooker 자동 collect 표준
├── Linux (Vulkan) → 디바이스별 Pre-Generated 캐시 검토
├── Android (Vulkan) → Adreno/Mali/PowerVR 3 디바이스 빌드
├── iOS (Metal) → Apple Silicon + iOS 별도
├── 콘솔 (PS5/Xbox/Switch) → 플랫폼 SDK 표준 (PSO + Shader 캐시 SDK 제공)
└── VR (Quest/PSVR2/PCVR) → 90Hz — 가장 엄격, 모든 PSO Precache + Background thread 의무

[Q2] 게임 규모?
├── 작은 게임 (10~100 Material) → 자동 collect 충분
├── 중간 (~1000 Material) → 카테고리별 Precache (Player / Enemy / Effect / UI)
└── 대형 (~10000 Material) → Material category × Vertex Factory 매트릭스 explicit 수동
```

## 7. 함정 / 열린 질문

- [ ] **Cooker 시간 폭발** — 모든 PSO Precache → cooker 시간 N×M 증가. CI 빌드 시간 30분 → 2시간. Material category 분리 + selective precache
- [ ] **PSO 캐시 저장 위치** — 디바이스 별 캐시 — 디바이스 변경 시 (예: 폰 교체) 재컴파일. Cloud sync 또는 first-launch 패턴
- [ ] **Streaming Map 의 Precache** — 메인 맵 PSO 만 Precache → Streaming Sub-level 진입 시 stall. Sub-level 별 Precache 분리 필요
- [ ] **Live Patch 후 PSO 무효화** — [[synthesis/runtime-dlc-livepatch-rollout]] 의 자산 swap 시 Material 의 PSO 재생성. Patch 적용 후 Precache 재트리거
- [ ] **r.PSOPrecaching.Validation 의 노이즈** — 모든 missing PSO 에 Warning — Editor 에서만 활성 (Shipping 은 0)
- [ ] **Mobile Vulkan 의 Pre-Generated PSO 캐시 갱신** — 디바이스 OS / GPU driver 업데이트 시 캐시 무효. 자동 재생성 로직
- [ ] **VR Foveated Rendering** + PSO Precache — 5.x VRS 의 PSO 가 별도 — Quest 3 / PSVR2 별 검증 (열린)
- [ ] **PIX / RenderDoc 의 PSO 통계** — 캡처 후 *몇 개의 PSO 가 Precached vs JIT* 표시. 디버깅 도구 활용 (열린)

## 8. 관련

### Sources

[[sources/ue-render-shader]] · [[sources/ue-render-material]] · [[sources/ue-render-rhi]] · [[sources/ue-render-vulkan]] · [[sources/ue-render-mobile]] · [[sources/ue-render-vr]] · [[sources/ue-build-skill]]

### Entities

[[entities/UMaterial]]

### Concepts

[[concepts/Cooked-vs-Uncooked]] · [[concepts/Asset-Optimization-Policy]] · [[concepts/Build-Configurations]]

### Related synthesis

[[synthesis/cooked-first-frame-stability]] (PSO 가 5 축 중 하나) · [[synthesis/character-many-npc-5-fold-optimization]] (NPC PSO Precache) · [[synthesis/runtime-dlc-livepatch-rollout]] (DLC 적용 후 PSO 재생성) · [[synthesis/pso-streaming-livepatch-tools]] (Streaming + Live Patch + RenderDoc/PIX 분석)
