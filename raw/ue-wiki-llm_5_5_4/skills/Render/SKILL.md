---
name: render
description: UE 5.5.4 Render 카테고리 — RenderCore (RDG / Shader / Material / MaterialExpression / MaterialEditingLibrary 🛠) + Renderer (MeshDrawing / PostProcess / Lumen / Nanite) + RHI (Command List / Resources) + Vulkan/Mobile/VR 플랫폼 분기. 13 sub-skill. FRDGBuilder + FGlobalShader + UMaterialExpression + FMaterialCompiler 548 메소드 (5.5.4) + UMaterialEditingLibrary 56 UFUNCTION (5.5.4) + Substrate 5.x + FSceneViewExtensionBase + FMeshBatch + 5.x Lumen/Nanite + FRHICommandList + OpenXR + Mobile Forward/Deferred. [Render] prefix 호출.
---

# Render — RDG / Shader / Material / SceneViewExtension / MeshDrawing / PostProcess / Lumen+Nanite / RHI

> **위치**:
> - **RenderCore**: `Engine/Source/Runtime/RenderCore/Public/` (99 헤더 — 5.5.4 — RDG / Shader 베이스)
> - **Renderer**: `Engine/Source/Runtime/Renderer/Public/` (44 헤더 — 5.5.4 — MeshDrawing / PostProcess)
> - **RHI**: `Engine/Source/Runtime/RHI/Public/` (55 헤더 — Command List / Resources)
> - **SceneViewExtension**: `Engine/Public/SceneViewExtension.h` (Engine 모듈)
>
> **요지**: UE 5.x 의 **GPU 측 코드 작성** — 게임 스레드 (Components/AssetClasses) 와 분리된 별도 영역. RHI Thread / Render Thread / 멀티 GPU 동기화 + RDG 의 자동 의존성 그래프가 핵심.

---

## 🚨 공통 정책 (자동 적용)

| 정책 | Render 적용 |
|------|------------|
| 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) | RDG Pass 콜백 / Compute Shader Dispatch / RHI Command 첫 줄 `RDG_EVENT_SCOPE` / `SCOPED_DRAW_EVENT` 의무 |
| 🚨 스레드 안전성 | 게임 스레드 (Component) → Render Thread (Proxy 데이터 복사) → RHI Thread (실제 명령 실행) **3축 분리 의무** |
| 🚨 Lifetime | Render Thread 객체 = `BeginInitResource` / `BeginReleaseResource` 페어 의무 |
| 🚨 GPU Skin Cache / Nanite | 5.x — 고정 메시 = Nanite 우선 / 동적 메시 = Skin Cache 활성 |

---

## 1. sub-skill 인덱스 (12 + 메인)

### Tier 1+2 — 핵심 (9)

| sub-skill | 책임 | 핵심 클래스 |
|-----------|------|------------|
| [`RDG`](./references/RDG.md) ⭐⭐ | Render Dependency Graph (5.x 표준) | `FRDGBuilder` / `FRDGTexture` / `FRDGBufferRef` / `FRDGPass` / `FRDGBlackboard` |
| [`Shader`](./references/Shader.md) ⭐ | Global / Material / Compute Shader | `FGlobalShader` / `FMaterialShader` / `FComputeShader` / `IMPLEMENT_GLOBAL_SHADER` / `SHADER_PARAMETER_STRUCT` / `FShaderPermutationDomain` |
| [`Material`](./references/Material.md) | UMaterial 컴파일 / Domain 7종 / ShadingModel 12종 / PSO Precache | `FHLSLMaterialTranslator` / `FMaterialShader` / `MD_*` / `EMaterialQualityLevel` |
| [`MaterialExpression`](./references/MaterialExpression.md) ⭐ | **표현식 깊이** — Custom 노드 작성 + FMaterialCompiler 548 메소드 (5.5.4) + Substrate 5.x | `UMaterialExpression` (Compile/Build) / `FMaterialCompiler` / `UMaterialExpressionCustom` / `MIR::FEmitter` |
| [`MaterialEditingLibrary`](./references/MaterialEditingLibrary.md) 🛠 | **Editor 자동화** (Python/BP) — 56 UFUNCTION (5.5.4) — CRUD / Connection / Compile / MIC | `UMaterialEditingLibrary::CreateMaterialExpression` / `ConnectMaterialProperty` / `ConnectMaterialExpressions` / `RecompileMaterial` / MIC Get/Set |
| [`SceneViewExtension`](./references/SceneViewExtension.md) ⭐ | Post-Process / Custom Pass Hook | `FSceneViewExtensionBase` / 7 hook (PreRenderView / PrePostProcess / etc) |
| [`MeshDrawing`](./references/MeshDrawing.md) | Mesh Pass / Custom Renderer | `FMeshBatch` / `FMeshPassProcessor` / `FStaticMeshSceneProxy` / `PrimitiveSceneInfo` |
| [`PostProcess`](./references/PostProcess.md) | 내장 PostProcess + Custom 등록 | `FPostProcessing` / `AddX_RenderThread` 패턴 |
| [`LumenNanite`](./references/LumenNanite.md) ⭐⭐ | 5.x 신규 기술 | Lumen GI/Reflection + Nanite Virtualized Geometry + GPU Scene |
| [`RHI`](./references/RHI.md) | RHI Command List + Resources | `FRHICommandList` / `FRHIResource` / `FRHITexture` / `FRHIBuffer` / `FRHIThread` |

### 플랫폼 분기 (3 — 신규 2026-05-08)

| sub-skill | 책임 | 핵심 |
|-----------|------|------|
| [`Vulkan`](./references/Vulkan.md) | RHI 벤더 차이 (D3D12/Vulkan/Metal/OpenGL ES) | Cross-Platform 셰이더 + Validation Layer + Feature Level 분기 |
| [`Mobile`](./references/Mobile.md) | Mobile Forward + Mobile Deferred (5.x) | Mobile Material + PSO Cache + Vulkan ES + 60fps 매트릭스 |
| [`VR`](./references/VR.md) | VR (OpenXR + Quest/Vive/Index/PSVR2) | Stereo Rendering + Foveated + 90/120fps + 멀미 회피 |

---

## 2. 시나리오 결정 트리

```
사용자 작업 → Render 측면?
├── 새 PostProcess Pass 추가 (블러 / 색감 보정)        → SceneViewExtension + RDG
├── Custom Compute Shader (GPU 시뮬)                  → RDG + Shader (Compute)
├── Custom Material Expression (인라인 HLSL 노드)      → MaterialExpression §5 (UMaterialExpressionCustom)
├── Custom Material Expression (C++ 자손 노드) ⭐       → MaterialExpression §3 (Compile + FMaterialCompiler)
├── Substrate 5.x BSDF 작성                            → MaterialExpression §8 (Substrate 통합)
├── Material 자동 생성 / Python 스크립트 🛠            → MaterialEditingLibrary (CreateMaterialExpression + Connect + Recompile)
├── MIC (Material Instance) 일괄 갱신 🛠              → MaterialEditingLibrary §6 (MIC Get/Set)
├── 새 Mesh Renderer (Volumetric / Decal / etc)       → MeshDrawing + Shader
├── GBuffer 접근 (Custom Lighting)                    → SceneViewExtension + Shader
├── Compute → Pixel 의존 그래프                       → RDG (자동 의존성)
├── 5.x Lumen / Nanite 셋업 / 디버그                  → LumenNanite ⭐⭐
├── RHI 직접 명령 (Vulkan 등)                          → RHI
├── 머티리얼 컴파일 (Cooked Build PSO)                 → Material (PSO Precache)
├── 플랫폼별 분기 (DX12/Vulkan/Metal)                  → Vulkan
├── Mobile 60fps 유지 (iOS / Android)                  → Mobile
├── VR 90/120fps (Quest / Index / PSVR2)              → VR ⭐
└── 일반 게임 코드 (UPROPERTY / Spawn / Tick)          → Components / GameFramework (Render X)
```

---

## 3. 라이프사이클 — 3축 스레드 분리

```
[게임 스레드]                  [Render Thread]              [RHI Thread]
ACharacter::Tick()                                          
  ↓ (ActorComponent)                                        
USkeletalMeshComponent::SendRenderDynamicData()             
  ↓ (FRenderCommand 큐)                                     
                              FSkeletalMeshSceneProxy::      
                              GetDynamicMeshElements()        
                                ↓ FMeshBatch 생성             
                              MeshPassProcessor::AddMesh    
                                ↓ FRDGBuilder 등록            
                                                            FRHICommandList::
                                                            DrawIndexedPrimitive
                                                              ↓ GPU
```

**규칙**:
- **게임 스레드**: Component / Actor 객체 접근. UPROPERTY 안전.
- **Render Thread**: Proxy 객체 사용. UObject 직접 접근 X (Race Condition).
- **RHI Thread**: 실제 GPU 명령 실행. Render Thread 와도 비동기.

---

## 4. 페어 매트릭스 (Render ↔ Components ↔ Material)

| 작업 | Render 측 | Components 측 (호스트) | Material 측 (자산) |
|------|----------|----------------------|------------------|
| Static Mesh 렌더링 | MeshDrawing (PrimitiveSceneProxy) | Components/MeshComponents (UStaticMeshComponent) | AssetClasses/Material (UMaterial) |
| Skeletal Mesh 렌더링 | MeshDrawing (FSkeletalMeshSceneProxy) | Components/MeshComponents (USkeletalMeshComponent) | AssetClasses/Material |
| Niagara VFX | MeshDrawing (Niagara Renderer) | Plugins/Niagara | AssetClasses/Material |
| Custom PostProcess | SceneViewExtension + RDG + Shader | (없음) | (커스텀 Material 가능) |
| GBuffer Custom Sample | SceneViewExtension | (Material 안 SceneTexture) | (없음) |

---

## 5. 5.x 신규 기능 (위키 강한 영역)

### 5.x Lumen
- 동적 GI / Reflection (Ray Traced + SDF)
- 자세히: [`LumenNanite/SKILL.md`](./LumenNanite/SKILL.md) §1
- 의존: Hardware Ray Tracing (DX12) 또는 SDF Mesh

### 5.x Nanite
- Virtualized Geometry — 수백만 폴리곤 자동 LOD
- 자세히: [`LumenNanite/SKILL.md`](./LumenNanite/SKILL.md) §2
- 호환: Static Mesh / Foliage. Skeletal Mesh = 5.4+ 부분 지원.

### 5.x GPU Scene
- 모든 Primitive = 단일 GPU 데이터 구조
- Multi-View / Instanced Stereo / Mobile 통합

### 5.x Mesh Shaders
- DX12 Mesh Shader Pipeline (GeometryProcessing 후속)

---

## 6. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Render Thread 안 UObject 직접 접근 | Proxy 객체 사용 (FStaticMeshSceneProxy 등) |
| 2 | Render Thread 안 UPROPERTY 멤버 변경 | `ENQUEUE_RENDER_COMMAND` 큐잉 |
| 3 | RHI Resource Lifetime 미관리 | `BeginInitResource` / `BeginReleaseResource` 페어 |
| 4 | RDG 외부 Pass 추가 (Legacy `IPooledRenderTarget`) | RDG Pass 표준 (`AddPass`) |
| 5 | Shader Permutation 누락 | `FShaderPermutationDomain` + `IMPLEMENT_GLOBAL_SHADER` |
| 6 | Cooked Build 안 Custom Shader 못 컴파일 | `ShouldCompilePermutation` + Material 인스턴싱 |
| 7 | PostProcess Custom Pass — 잘못된 hook 시점 | `SceneViewExtension::PrePostProcessPass_RenderThread` 권장 |
| 8 | 5.x Nanite + Custom Vertex Factory 충돌 | Nanite 비활성 또는 Custom Vertex Factory 안 사용 |
| 9 | RDG 의존성 누락 → GPU 데이터 race | `ERDGPassFlags::Compute` 명시 + Resource Read/Write 정확 |
| 10 | Material PSO 캐시 미사용 → 첫 Render 히칭 | 5.x `r.PSOPrecache` 활성 + Material 사용 패턴 등록 |

---

## 7. 체크리스트

- [ ] Render Thread 안 UObject 직접 접근 X
- [ ] FRDGBuilder 사용 — Legacy IPooledRenderTarget X
- [ ] RDG Pass 의존성 명시 (Resource Read/Write)
- [ ] Shader Permutation 정의 + ShouldCompile
- [ ] PostProcess Custom = SceneViewExtension hook
- [ ] 5.x Lumen / Nanite — 호환 검사
- [ ] RHI Resource Lifetime — Init/Release 페어
- [ ] Material PSO Precache 활성 (Cooked Build)
- [ ] 모든 Render 콜백 첫 줄 RDG_EVENT_SCOPE / SCOPED_DRAW_EVENT
- [ ] 🚨 멀티 스레드 안전 (Game ↔ Render ↔ RHI 3축)

---

## 8. 관련 sub-skill / cross-link

- **자산 페어**: [`AssetClasses/references/Material.md`](../AssetClasses/references/Material.md) — UMaterial / MaterialInstance
- **호스트 페어**: [`Components/references/MeshComponents.md`](../Components/references/MeshComponents.md) — Mesh Component (Render 큐잉)
- **VFX**: [`Niagara/SKILL.md`](../Niagara/SKILL.md) — Niagara Renderer (FNiagaraRenderer 자손)
- **Slate Render**: [`SlateCore/references/Drawing.md`](../SlateCore/references/Drawing.md) — Slate FSlateBrush → DrawElement
- **빌드**: [`Build/SKILL.md`](../Build/SKILL.md) — Shader Cooking / PSO Cache

---

## 9. Build.cs 표준 의존성

```csharp
PrivateDependencyModuleNames.AddRange(new[] {
    "Core", "CoreUO