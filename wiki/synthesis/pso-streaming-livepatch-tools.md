---
type: synthesis
title: "PSO Streaming + Live Patch 무효화 + RenderDoc/PIX 도구 분석"
slug: pso-streaming-livepatch-tools
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/ue-render-shader]]"
  - "[[sources/ue-render-material]]"
  - "[[sources/ue-render-mobile]]"
  - "[[sources/ue-render-vulkan]]"
  - "[[sources/ue-build-skill]]"
entities:
  - "[[entities/UMaterial]]"
  - "[[entities/UTexture]]"
concepts:
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Asset-Lifecycle]]"
status: living
tags: [synthesis, pso, streaming, live-patch, renderdoc, pix]
---

# PSO Streaming + Live Patch 무효화 + RenderDoc/PIX 도구 분석

## 1. Thesis

[[synthesis/pso-precache-platform-matrix]] 의 미해결 3 축 — **(1) Streaming Map 진입 시 PSO 누락 (메인 맵 PSO 만 Precache → Sub-level stall) / (2) Live Patch 후 PSO 무효화 ([[synthesis/runtime-dlc-livepatch-rollout]] 의 자산 swap 결합) / (3) RenderDoc/PIX 의 PSO 통계 분석 — Precached vs JIT 식별)**. 본 synthesis 는 각 축의 표준 패턴 + 도구 사용법 + 측정 절차.

## 2. (1) Streaming Map PSO

LevelStreaming Sub-level 진입 시 새 자산 → 새 PSO 컴파일 필요. 대책:

```cpp
// Sub-level 별 Precache 그룹 정의
// DefaultEngine.ini
[/Script/Engine.RendererSettings]
+PSOPrecacheGroup=(Name="MainMap",        Levels=("/Game/Maps/MainMap"))
+PSOPrecacheGroup=(Name="DungeonLevel1",  Levels=("/Game/Maps/Sub/Dungeon1"))

// 런타임 — Sub-level Load 시점에 명시적 Precache
void AMyGameMode::OnSubLevelLoaded(FName LevelName)
{
    if (LevelName == FName("Dungeon1")) {
        // Sub-level 의 Material × VertexFactory 조합 precache
        UMaterialInterface::PrecachePSOsForLevel(LevelName);
    }
}
```

또는 [[synthesis/cooked-first-frame-stability]] §4 의 GameMode Bundle PreLoad 와 결합 — Sub-level 진입 *전* 에 Bundle 로 묶어 비동기.

## 3. (2) Live Patch PSO 무효화

DLC / Live Patch 자산 swap → 옛 PSO 가 새 Material 안 맞음. Invalidation:

```cpp
// DLC mount + Material 새 버전 도착 후
void AMyGameMode::OnDLCAssetsLoaded()
{
    // 옛 PSO 캐시 무효화
    FShaderPipelineCache::ShutdownPipelineCache();
    FShaderPipelineCache::Initialize(...);

    // 새 자산의 PSO 다시 collect + Precache
    for (UMaterial* Mat : NewDLCMaterials) {
        Mat->PrecachePSOs();
    }
}
```

**함정**: PSO 무효화 중에 다른 draw call → render thread stall. 매치 진행 중 Live Patch 는 Loading Screen 권장.

## 4. (3) RenderDoc / PIX PSO 분석

| 도구 | 플랫폼 | PSO 통계 보는 곳 |
| -- | -- | -- |
| **RenderDoc** | DX12 / Vulkan / OpenGL / Metal (제한) | Capture 후 *Pipeline State* 패널 + *Statistics* — Compile Time / Cache Hit Rate |
| **PIX** | DX12 (Windows) | *PSO Stats* tab — Compile Cache hit/miss 비율 / Compile Time histogram |
| **Xcode GPU Frame Capture** | Metal (iOS/macOS) | *Render Loop* → Pipeline State 비용 표시 |
| **vkconfig + Layer** | Vulkan (Android/Linux) | Validation Layer 의 `VK_LAYER_LUNARG_pipeline_cache_stats` |

**RenderDoc 사용 예** (PSO Precache 검증):

```
1. Game launch + 디버그 빌드 (RenderDoc target inject)
2. F12 (RenderDoc default) — capture 1 frame
3. RenderDoc UI → Pipeline State 패널 → Pipeline 마우스 오버 → "Created at frame N"
4. 만약 "Created at frame 0" 이면 Precached ✓
   "Created at frame 60" 이면 JIT compile → Precache miss
```

**PIX 사용 예** (Windows DX12):

```
1. Game launch with PIX (D3D12 debug)
2. Capture
3. Counters → "Pipeline State Object" → Compile Time histogram
4. Histogram 0-1ms bin 이 클수록 Precached ↑
```

## 5. 측정 매트릭스 — Precache 효과 정량화

```cpp
// 디버그 매크로 — 프레임당 새 PSO 컴파일 카운트
#if !UE_BUILD_SHIPPING
static int32 GFrameNewPSOCount = 0;
FAutoConsoleCommand DumpPSO(
    TEXT("MC.DumpPSOStats"), TEXT("Dump PSO compile stats"),
    FConsoleCommandDelegate::CreateLambda([]() {
        UE_LOG(LogMCAsset, Log, TEXT("New PSO this frame: %d"), GFrameNewPSOCount);
        GFrameNewPSOCount = 0;
    }));
#endif
```

또는 5.x 의 `r.PSOPrecaching.Validation=1` — 런타임 PSO 가 Precached 됐는지 검증, JIT 발견 시 Warning.

## 6. 결정 트리

```
PSO 성능 문제 의심?
├── 첫 frame stall (Map 시작 직후) → [[synthesis/pso-precache-platform-matrix]] §2 의 5 백엔드 매트릭스
├── Sub-level 진입 stall → 본 synthesis §2 — Sub-level PSO Group + Bundle 결합
├── Live Patch 후 stall → §3 — Invalidate + 재 Precache + Loading Screen
├── 게임 진행 중 random stall → RenderDoc / PIX 로 PSO compile 시점 캡처 (§4)
└── Mobile 디바이스별 차이 → vkconfig + Pre-Generated Vulkan Pipeline Cache 빌드 ([[synthesis/pso-precache-platform-matrix]] §4 Vulkan)
```

## 7. 함정 / 열린 질문

- [ ] **Cooker 의 *Sub-level Precache* cascade** — Sub-level 의 Material × VertexFactory 조합 자동 collect 안 됨. 명시적 PSOPrecacheGroup 등록 의무
- [ ] **Live Patch *진행 중 draw* 와 동기** — PSO invalidate 도중 다른 thread 에서 draw → 잘못된 PSO 사용. 동기화 (RenderingThread suspend)
- [ ] **RenderDoc 의 *PSO ID* 가 매 capture 마다 다름** — 같은 frame 에서 2회 capture 시 ID 다름. *비교* 보다 *해당 capture 안에서 빈도* 위주 분석
- [ ] **Mobile Vulkan Pipeline Cache 의 *signature 불일치*** — Device A 빌드 cache 를 Device B 에 적용 → Vulkan 거절. Per-device 빌드 ([[synthesis/pso-precache-platform-matrix]] §4)
- [ ] **PIX 의 *Counter overhead*** — PIX counter 자체가 GPU 성능 1-5% 차감. Shipping 빌드 측정 시 PIX counter 끄기
- [ ] **`r.PSOPrecaching.Validation` 의 *false positive*** — 같은 PSO 의 다른 RenderTarget format 변형이 *별개 PSO* 로 잡혀 Validation Warning. Cooker 가 모든 format 조합 collect 검토
- [ ] **VR Foveated Rendering + PSO Streaming** — Foveated 변경 시 PSO 무효 — Sub-level 진입 + Foveated change 동시 발생 시 stall 누적 (열린)
- [ ] **PSO 캐시의 *디스크 위치*** — DX12 = `<Project>/Saved/DX12PSOCache.dxpso` / Vulkan = `<Project>/Saved/VulkanPSOCache.bin` — 옮기기 / CI 캐싱 (열린)

## 8. 관련

### Sources

[[sources/ue-render-shader]] · [[sources/ue-render-material]] · [[sources/ue-render-mobile]] · [[sources/ue-render-vulkan]] · [[sources/ue-build-skill]]

### Entities

[[entities/UMaterial]] · [[entities/UTexture]]

### Concepts

[[concepts/Cooked-vs-Uncooked]] · [[concepts/Asset-Optimization-Policy]] · [[concepts/Asset-Lifecycle]]

### Related synthesis

[[synthesis/pso-precache-platform-matrix]] (5 백엔드 매트릭스 베이스) · [[synthesis/cooked-first-frame-stability]] (Bundle + Match State 결합) · [[synthesis/runtime-dlc-livepatch-rollout]] (Live Patch 자산 swap)
