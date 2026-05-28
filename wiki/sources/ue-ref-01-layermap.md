---
type: source
title: "UE refs — 01 LayerMap (L1~L7 의존 계층 hub)"
slug: ue-ref-01-layermap
source_path: raw/ue-wiki-llm/references/01_LayerMap.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
tags: [ue, reference, module, dependency, layer, vault-structure]
---

# UE refs — 01 LayerMap

> Source: [[raw/ue-wiki-llm/references/01_LayerMap.md]] · `Engine/Source/Runtime/` 189 모듈

## 1. Summary

`Engine/Source/Runtime` 의 **189 모듈** 을 **L1~L7 의존 계층** (아래에서 위) 으로 정리한 vault 구조의 권위 hub. 원칙: *이 계층 모듈은 아래 계층까지의 모듈만 참조*. vault 의 모든 sub-skill 이 본 매트릭스의 위치를 따름. 카테고리 매핑 → [[sources/ue-catalog-runtimeindex]].

## 2. L1~L7 의존 계층 🟢

```
┌──────────────────────────────────────────────────────────────────┐
│ L7. 게임/시네마틱/AI/UI 게임 레이어                                  │
│   UMG · LevelSequence · MovieSceneTracks · AIModule · NavigationSystem │
│   GameplayTasks · GameplayDebugger · Foliage · Landscape · CinematicCamera │
├──────────────────────────────────────────────────────────────────┤
│ L6. 도메인 런타임 (Engine 의존)                                    │
│   AnimGraphRuntime · ClothingSystemRuntime · MovieScene · MediaAssets │
│   AudioMixer · NetworkReplayStreaming · LiveLinkAnimationCore · Slate│
│   InteractiveToolsFramework · BlueprintRuntime · PreLoadScreen      │
├──────────────────────────────────────────────────────────────────┤
│ L5. Engine 코어 (CoreUObject + Renderer + Slate 통합)              │
│   Engine · Launch · UnrealGame · UELibrary                         │
├──────────────────────────────────────────────────────────────────┤
│ L4. 렌더링 / UI 인프라                                             │
│   Renderer · RenderCore · SlateCore · SlateRHIRenderer             │
│   D3D12RHI · VulkanRHI · OpenGLDrv · NullDrv · ImageWrapper        │
├──────────────────────────────────────────────────────────────────┤
│ L3. 하드웨어/OS 추상                                               │
│   RHI · RHICore · ApplicationCore · InputCore · Sockets · AudioMixerCore │
│   NetworkFile · PakFile · TraceLog                                 │
├──────────────────────────────────────────────────────────────────┤
│ L2. UObject / 직렬화 / 리플렉션                                    │
│   CoreUObject · Json · JsonUtilities · Cbor · Serialization        │
│   AssetRegistry · GameplayTags · DeveloperSettings                 │
├──────────────────────────────────────────────────────────────────┤
│ L1. 최저수준 기반                                                   │
│   Core · CorePreciseFP · CoreOnline · BuildSettings                │
│   AutoRTFM · TraceLog · MathCore · GeometryCore · ImageCore        │
└──────────────────────────────────────────────────────────────────┘
```

## 3. 핵심 의존 흐름 (Top 5)

```
Core
 └─ CoreUObject
     └─ Engine ──────┬─> Slate (UI) ──> UMG
                     ├─> Renderer ──> RHI ──> {D3D12RHI, VulkanRHI, OpenGLDrv}
                     ├─> AudioMixer ──> AudioMixerCore
                     ├─> Networking ──> Sockets
                     └─> AIModule ──> NavigationSystem ──> Navmesh
```

## 4. 카테고리별 모듈 요약 🟢

| 카테고리 | 모듈 수 | 위치 (L) |
| -- | -- | -- |
| **Foundation** | ≈30 | L1-L2 (컨테이너 / 리플렉션 / 직렬화 / 태그) |
| **Engine / Gameplay** | ≈18 | L5-L7 (게임플레이 프레임워크 본체 + 부속) |
| **Rendering** | ≈18 | L4 (RHI 추상 + 백엔드 + RDG / Renderer) |
| **UI / App** | ≈13 | L3-L7 (Slate / UMG / 입력 / 윈도잉 / Web) |
| **Animation** | ≈9 | L5-L6 (AnimGraph / Cloth / LiveLink) |
| **Physics / Geometry** | ≈9 | L1-L5 (Chaos 통합 + 메시 표현·변환) |
| **AI** | ≈5 | L7 (Behavior Tree · EQS · NavMesh · MassEntity) |
| **Audio** | ≈19 | L3-L6 (AudioMixer 스택 + 분석 / 디코더 / 평가) |
| **Networking** | ≈14 | L3-L6 (소켓 / 온라인 / 리플레이 / 스토리지 서버) |
| **Cinematic** | ≈12 | L6-L7 (Sequencer / Media / 캡처 / 인코더) |
| **Platform** | 8 | L1 (Android / Apple / IOS / Linux / Unix / Windows / Solaris / ThirdParty) |
| **VR / XR** | 4 | L5-L7 (HMD / AR / EyeTracker / MRMesh) |
| **VP** | 3 | L7 (VirtualProduction / Datasmith / NNE) |
| **DevTools** | 10 | L3-L7 (Automation / CrashReport / PerfCounters / RewindDebugger) |
| **Messaging** | 5 | L3-L5 (MessageBus / RPC / Session) |
| **Time / VM** | 3 | L1-L7 (TimeManagement / VectorVM / VerseCompiler) |
| **Misc** | ≈9 | (Advertising / Analytics / InstallBundle 등) |

## 5. 컨테이너 폴더 (그룹 모듈)

`.Build.cs` 없이 내부에 서브모듈 담는 폴더 (카탈로그 = "컨테이너"):

- **플랫폼**: Apple / IOS / Android / Linux / Unix / Windows / Solaris
- **네트워킹**: Online / Net / NetworkReplayStreaming / PacketHandlers
- **도메인**: Audio* 일부 / Datasmith / Interchange / Experimental
- **통합**: Advertising / Analytics / Portal / Toolbox / StudioTelemetry
- **기타**: PlatformThirdPartyHelpers / NullInstallBundleManager

LLM 위키에서는 "이 안에 어떤 서브모듈" 만 인덱스, SKILL 은 서브모듈 단위.

## 6. Vault sub-skill 분포 매트릭스

vault 의 sub-skill 이 위 L1-L7 의 어느 계층을 다루는지:

| Vault 카테고리 | 주 계층 | sub-skill 예시 |
| -- | -- | -- |
| CoreUObject | L2 | UObject / Reflection / GC / Serialization / Network |
| Components | L5 (Engine 자손) | UActorComponent / USceneComponent / 15 자손 |
| GameFramework | L5 | Actor / Pawn / Character / Controller / GameMode |
| AssetClasses | L4-L5 | Mesh / Material / Texture / Animation / Audio |
| Animation | L6 | AnimGraphRuntime + AnimInstance / IK Rig |
| Input | L3-L5 | InputCore (L3) + EnhancedInput (Plugin) |
| Editor 🛠 | (Editor/Developer — 별개) | UnrealEd / PropertyEditor / ToolMenus |
| Slate | L6 | Slate (인하우스 툴 묶음 — 4단 분리 의무) |
| SlateCore | L4 | SWidget / Layout / Drawing / Styling |
| UMG | L7 | UWidget / UUserWidget (Slate 자손) |
| Render | L4 | Renderer / RenderCore / RHI 백엔드 |
| AI | L7 | AIModule / NavigationSystem / Mass |
| Build | (UBT/UAT — 별개) | Build.cs / Target.cs |
| GAS / Niagara / Significance | Plugin | Engine 위 |
| Networking | L3-L6 | Networking / Replication / Iris |
| SpatialPartition (5.x) | L5-L7 | TOctree2 (L1 Math) + WorldPartition (L7) |
| Subsystem | L5 | UEngineSubsystem / UWorldSubsystem 등 |

## 7. 함정 (4대)

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | L4 모듈 (Renderer) 가 L7 모듈 (UMG) 의존 시도 | 의존 역전 — Renderer 는 UMG 모름 |
| 2 | L1 (Core) 에 게임 코드 직접 작성 | L1 = engine 베이스 — 게임 코드 = L7 |
| 3 | Editor 모듈을 L5 (Engine 자손) 처럼 다룸 | Editor/Developer = 별개 — 4단 분리 ([[sources/ue-ref-05-editoronlyindex]]) |
| 4 | 컨테이너 폴더 자체 의존 시도 | 서브모듈 직접 — 컨테이너 = 그룹 |

## 8. Cross-link

- 카탈로그: [[sources/ue-catalog-runtimeindex]] (Runtime 189 모듈 자세히) · [[sources/ue-catalog-editordevindex]] (Editor / Developer)
- 자매 hub: [[sources/ue-ref-03-wikiharness]] (vault 단일 진입점) · [[sources/ue-ref-05-editoronlyindex]] (Editor 4단 분리)
- Manifests: [[sources/ue-readme]] · [[sources/ue-manifest]]
- 카테고리 main 전체: [[sources/ue-coreuobject-skill]] · [[sources/ue-components-skill]] · [[sources/ue-gameframework-skill]] · [[sources/ue-assetclasses-skill]] · [[sources/ue-render-skill]] · [[sources/ue-slate-skill]] · [[sources/ue-slatecore-skill]] · [[sources/ue-umg-skill]] · [[sources/ue-editor-skill]]
