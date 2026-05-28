# 런타임 모듈 계층 맵 (UE 5.7.4)

`Engine/Source/Runtime` 의 189개 모듈을 **의존 계층(아래에서 위로)** 으로 정리한 개요.
각 줄은 "이 계층의 모듈은 그 아래 계층까지의 모듈만 참조한다"는 원칙을 따른다.

```
┌──────────────────────────────────────────────────────────────────┐
│ L7. 게임/시네마틱/AI/UI 게임 레이어                                  │
│   UMG · LevelSequence · MovieSceneTracks · AIModule · NavigationSystem │
│   GameplayTasks · GameplayDebugger · Foliage · Landscape · CinematicCamera │
├──────────────────────────────────────────────────────────────────┤
│ L6. 도메인 런타임 (Engine 의존)                                    │
│   AnimGraphRuntime · ClothingSystemRuntime* · MovieScene · MediaAssets │
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

## 핵심 의존 흐름 (Top 5)

```
Core
 └─ CoreUObject
     └─ Engine ──────┬─> Slate(UI) ──> UMG
                     ├─> Renderer ──> RHI ──> {D3D12RHI, VulkanRHI, OpenGLDrv}
                     ├─> AudioMixer ──> AudioMixerCore
                     ├─> Networking ──> Sockets
                     └─> AIModule ──> NavigationSystem ──> Navmesh
```

## 카테고리별 모듈 요약 (자세한 표는 `catalog/RuntimeIndex.md`)

- **Foundation (≈30)** — 컨테이너/리플렉션/직렬화/태그 등 최저수준
- **Engine/Gameplay (≈18)** — 게임플레이 프레임워크 본체와 부속 시스템
- **Rendering (≈18)** — RHI 추상 + RHI 백엔드 + RDG/Renderer
- **UI/App (≈13)** — Slate/UMG/입력/윈도잉/Web
- **Animation (≈9)** — AnimGraph/Cloth/LiveLink
- **Physics/Geometry (≈9)** — Chaos 통합 + 메시 표현·변환
- **AI (≈5)** — Behavior Tree·EQS·NavMesh·MassEntity
- **Audio (≈19)** — 새 AudioMixer 스택, 분석/디코더/평가
- **Networking (≈14)** — 소켓/온라인/리플레이/스토리지 서버
- **Cinematic (≈12)** — Sequencer/Media/캡처/인코더
- **Platform (8)** — Android/Apple/IOS/Linux/Unix/Windows/Solaris/PlatformThirdPartyHelpers
- **VR/XR (4)** — HMD/AR/EyeTracker/MRMesh
- **VP (3)** — VirtualProduction/Datasmith/NNE
- **DevTools (10)** — Automation/CrashReport/PerfCounters/RewindDebugger
- **Messaging (5)** — MessageBus/RPC/Session
- **Time / VM (3)** — TimeManagement/VectorVM/VerseCompiler
- **Misc (≈9)** — Advertising/Analytics/InstallBundle 등 컨테이너성 모듈

## 컨테이너 폴더 (그룹 모듈)

`.Build.cs` 가 직접 없고, 내부에 다시 모듈을 담는 폴더는 카탈로그에서 "컨테이너"로 표시된다:

```
Apple, IOS, Android, Linux, Unix, Windows, Solaris,           ← 플랫폼
Online, Net, NetworkReplayStreaming, PacketHandlers,          ← 네트워킹
Audio* 일부, Datasmith, Interchange, Experimental,            ← 도메인
Advertising, Analytics, Portal, Toolbox, StudioTelemetry,     ← 통합
PlatformThirdPartyHelpers, NullInstallBundleManager …
```

이런 폴더는 LLM 위키에서는 "이 안에 어떤 서브모듈이 있는지" 만 인덱스하고,
실제 SKILL은 서브모듈 단위로 작성한다.

## 다음 단계

`skills/Core/SKILL.md` 부터 시작하여 Tier 1 → Tier 6 순으로 모듈별 스킬을 채운다.
각 SKILL.md 는 **개요 → 핵심 헤더/클래스 → 자주 쓰는 API → 사용 예제 → 관련 모듈** 의 다섯 섹션으로 구성한다.
