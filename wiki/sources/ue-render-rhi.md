---
type: source
title: "UE Render — RHI sub-skill (Command List + Resources + 동기화)"
slug: ue-render-rhi
source_path: raw/ue-wiki-llm/skills/Render/references/RHI.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-12
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, render, gpu, rhi, command-list, pso]
---

# UE Render — RHI (Rendering Hardware Interface)

> Source: [[raw/ue-wiki-llm/skills/Render/references/RHI.md]] · Parent: [[sources/ue-render-skill]]
> Pair: [[sources/ue-render-vulkan]] (벤더 분기) · [[sources/ue-render-rdg]] (상위 추상)

## §13 Citation Tier

본 카드의 모든 사실 주장은 raw RHI.md 의 §1~12 (FRHICommandList / FRHIResource / FRenderResource / FBufferRHIRef / ENQUEUE_RENDER_COMMAND / FRHIBufferCreateDesc) 에서 직접 확인 — 🟢 VAULT. PSO Precache 연계는 raw RHI.md 직접 언급 없음, [[synthesis/pso-precache-platform-matrix]] 와 [[sources/ue-render-skill]] 의 r.PSOPrecache 정책을 교차 인용 — 🟡 PARTIAL. TransitionResources / IRHICommandContext / FRHICommandListImmediate 세부 API 는 raw RHI.md 에 명시 안 됨, UE 5.7.x 일반 RHI 지식 — 🔴 INFERRED, §6 매트릭스 분리.

## §1 Summary

**RHI = GPU 추상 레이어**. Vulkan / D3D12 / Metal / OpenGL ES 를 하나의 인터페이스로 (`FRHICommandList` + `FRHIResource` + `FRHITexture` + `FRHIBuffer`). 게임 스레드 ↔ Render Thread ↔ RHI Thread **3축 분리** 의 가장 아래 레이어 — 실제 GPU 명령은 RHI Thread 에서 실행. 5.x 에서 **RDG ([[sources/ue-render-rdg]]) 가 99% 추상화** — RHI 직접 명령은 Custom Resource (Vertex Factory / Custom Buffer) 작성, Vulkan/Metal 특화, 또는 Cooked Build PSO 통합 시에만 필요.

## §2 Key claims

1. **FRHICommandList** = Render Thread 가 RHI Thread 로 보내는 GPU 명령 큐. `ENQUEUE_RENDER_COMMAND` 가 게임 스레드 → Render Thread 큐잉 매크로, 그 안에서 람다가 `FRHICommandList&` 를 받음 (raw §3).
2. **FRHIResource lifetime** — `FRenderResource` 자손이 `InitRHI(FRHICommandListBase&)` / `ReleaseRHI()` 페어 의무. 등록은 `BeginInitResource(Buffer)` / 해제는 `BeginReleaseResource(Buffer)` — Render Thread 에서 자동 호출, 직접 `new`/`delete` 후 RHI 객체 손대면 race (raw §4).
3. **RHI Thread 분리** — Render Thread 와도 비동기. RHI 람다 캡처 = **값 복사 또는 `TRefCountPtr`** 만. Render Thread 객체 (Proxy 등) 직접 캡처 = `TWeakObjectPtr` + 안전 검사 의무 (raw §7).
4. **FRHIComputeCommandList** = Compute Pass 전용 변종. RDG Pass `ERDGPassFlags::Compute` 람다 시그니처가 `(FRDGAsyncTask, FRHIComputeCommandList& RHICmdList)`. `SetComputePipelineState` + `SetShaderParameters` + `DispatchComputeShader(X,Y,Z)` 가 3종 표준 명령 (raw §5).
5. **FBufferRHIRef 5.x 통합** — Vertex / Index / Structured / Compute 버퍼 모두 단일 `FBufferRHIRef` 타입. 생성은 **Builder Pattern** `FRHIBufferCreateDesc::CreateVertex<T>(Name, Count).SetUsage(EBufferUsageFlags::...)` → `RHICmdList.CreateBuffer(Desc)`. Legacy `FRHIResourceCreateInfo` 단독 호출은 deprecated (raw §6).
6. **EBufferUsageFlags 조합** — `Static` / `Dynamic` (CPU 접근 빈도) × `ShaderResource` (SRV) / `UnorderedAccess` (UAV) / `VertexBuffer` / `IndexBuffer`. UAV 누락이면 Compute Shader 쓰기 불가 → silent fail (raw §9 #6).
7. **LockBuffer / UnlockBuffer 페어** — CPU 측 업로드 시 `RHICmdList.LockBuffer(Buffer, Offset, Size, RLM_WriteOnly)` → `FMemory::Memcpy` → `UnlockBuffer` 의무. Unlock 누락 = GPU 가 영원히 stale data (raw §4.1).
8. **GraphicsPipelineState (PSO)** = Vertex/Pixel Shader + Rasterizer + Blend + DepthStencil 묶음. **5.x PSO Precache 통합** — `r.PSOPrecache=1` 시 RHI 가 Cooked Build cook 단계에서 PSO 직렬화, 런타임 첫 Draw 히칭 100~500ms → 0 ms 회피 ([[synthesis/pso-precache-platform-matrix]] · [[synthesis/cooked-first-frame-stability]]).
9. **RHI Feature Level 분기** — `GMaxRHIFeatureLevel >= ERHIFeatureLevel::SM5` 또는 `IsMobilePlatform(GMaxRHIShaderPlatform)`. HWRT 는 `IsRayTracingEnabled()`. 분기 누락 = Mobile crash (raw §8 + §9 #9).

## §3 함정 (raw §9 10대 중 핵심 5)

| # | 함정 | 정답 |
|---|------|------|
| 1 | `InitRHI` / `ReleaseRHI` 페어 누락 → GPU 메모리 누수 | `FRenderResource` 자손 + `BeginInitResource`/`BeginReleaseResource` |
| 2 | RHI 람다 안 Render Thread Proxy 직접 캡처 | 값 복사 또는 `TRefCountPtr<FRHIResource>` |
| 3 | `FBufferRHIRef` `.SafeRelease()` 누락 | `TRefCountPtr` 자동 또는 `ReleaseRHI` 명시 |
| 4 | Legacy `FRHIResourceCreateInfo` 단독 (5.x deprecated) | `FRHIBufferCreateDesc` Builder Pattern |
| 5 | RDG 우회 + RHI 직접 명령 남발 | RDG Pass 안 RHI 명령 권장, 또는 RDG 로 이주 |

(전체 10대 = raw RHI.md §9)

## §4 코드 예 (3축 캡슐)

```cpp
// 게임 스레드 — UPrimitiveComponent
void UMyComponent::Tick(float DT)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyComponent::Tick);  // 의무
    const float NewValue = ComputeValue();

    // Render Thread 큐잉 — 값 복사
    ENQUEUE_RENDER_COMMAND(UpdateMyData)(
        [SceneProxy = SceneProxy, NewValue](FRHICommandList& RHICmdList)
        {
            // Render Thread 실행 — RHI 명령은 RHICmdList 에 큐잉
            if (SceneProxy) SceneProxy->UpdateData_RenderThread(RHICmdList, NewValue);
        });
}

// Custom RHI Resource (FRenderResource 자손)
class FMyVertexBuffer : public FRenderResource
{
public:
    FBufferRHIRef VertexBufferRHI;
    int32 NumVertices = 0;

    virtual void InitRHI(FRHICommandListBase& RHICmdList) override
    {
        FRHIBufferCreateDesc Desc = FRHIBufferCreateDesc::CreateVertex<FVector3f>(
            TEXT("MyVertexBuffer"), NumVertices)
            .SetUsage(EBufferUsageFlags::Static | EBufferUsageFlags::ShaderResource);

        VertexBufferRHI = RHICmdList.CreateBuffer(Desc);

        void* Data = RHICmdList.LockBuffer(VertexBufferRHI, 0,
            NumVertices * sizeof(FVector3f), RLM_WriteOnly);
        FMemory::Memcpy(Data, MyVertexData.GetData(), NumVertices * sizeof(FVector3f));
        RHICmdList.UnlockBuffer(VertexBufferRHI);
    }
    virtual void ReleaseRHI() override { VertexBufferRHI.SafeRelease(); }
};

// 등록 (Render Thread)
FMyVertexBuffer* Buffer = new FMyVertexBuffer();
Buffer->NumVertices = 100;
BeginInitResource(Buffer);   // InitRHI 자동 호출
// ...
BeginReleaseResource(Buffer);  // ReleaseRHI 자동, ReleaseFence 후 delete 안전
```

## §5 Cross-link

- **상위 추상**: [[sources/ue-render-rdg]] — RDG 가 RHI 99% 추상화. RHI 직접 명령은 RDG Pass 람다 안에서.
- **셰이더 페어**: [[sources/ue-render-shader]] — `FRHIComputeShader` / `SetShaderParameters` 가 RHI 측 셰이더 결합.
- **메시 페어**: [[sources/ue-render-meshdrawing]] — Custom Vertex Factory 의 `FBufferRHIRef` 가 본 카드 §4 패턴.
- **플랫폼 분기**: [[sources/ue-render-vulkan]] — DX12 / Vulkan / Metal / GLES 의 RHI backend 차이 (Render Pass / Pipeline Barrier / Descriptor Set).
- **PSO 통합**: [[synthesis/pso-precache-platform-matrix]] · [[synthesis/pso-streaming-livepatch-tools]] · [[synthesis/cooked-first-frame-stability]] — RHI PSO 가 5.x Precache 의 핵심 자산.
- **횡단 정책**: [[concepts/Profiling-Scope-Rule]] — `ENQUEUE_RENDER_COMMAND` 람다도 `TRACE_CPUPROFILER_EVENT_SCOPE` 첫 줄 의무.

## §6 신뢰도 매트릭스

| 주장 (§2 번호) | Tier | 근거 |
|---|---|---|
| 1 FRHICommandList + ENQUEUE_RENDER_COMMAND | 🟢 | raw §3 직접 |
| 2 FRenderResource Init/ReleaseRHI 페어 | 🟢 | raw §4 직접 |
| 3 RHI Thread 람다 캡처 규칙 | 🟢 | raw §7 직접 |
| 4 FRHIComputeCommandList 3종 명령 | 🟢 | raw §5 직접 |
| 5 FBufferRHIRef 5.x Builder | 🟢 | raw §6 직접 |
| 6 EBufferUsageFlags 조합 | 🟢 | raw §9 #6 직접 |
| 7 LockBuffer/UnlockBuffer 페어 | 🟢 | raw §4.1 + §9 #7 |
| 8 PSO Precache 통합 | 🟡 | raw 직접 X, [[synthesis/pso-precache-platform-matrix]] + [[sources/ue-render-skill]] r.PSOPrecache 교차 |
| 9 Feature Level 분기 | 🟢 | raw §8 직접 |

### vault 미확정 — 🔴 INFERRED (raw RHI.md 에 명시 없음)

- **FRHICommandListImmediate** — 즉시 실행 변종 (RHI Thread 비활성 시 Render Thread 직접 실행). raw 미언급, UE 5.7.x 일반 지식.
- **TransitionResources** — Resource state 전환 명령 (UAV ↔ SRV ↔ RenderTarget). raw §6 에 EBufferUsageFlags 만, transition API 자체는 미언급 — RDG 가 자동 처리하므로 raw 가 생략한 듯.
- **IRHICommandContext** — RHI backend (Vulkan/D3D12/Metal) 가 구현하는 인터페이스. raw 0 hits, 일반 RHI 아키텍처 지식.

→ 이 3 항목은 보너스 발견 후보 (아래 §Boundary).

## §Boundary — 보너스 발견 (POST-RECEIVE 자료)

본 enrich 중 다음 사항을 확인:

1. **raw RHI.md 의 PSO 공백** — raw §1~12 어디에도 `GraphicsPipelineState` / `FRHIGraphicsPipelineStateInitializer` / `PSO Precache` 명시 없음. 그런데 [[sources/ue-render-skill]] 의 "5.x 표준 의무" 4번에 `r.PSOPrecache=1` 가 있고, [[synthesis/pso-precache-platform-matrix]] 가 별도 synthesis 로 존재. **gap**: raw RHI.md 가 PSO 측면을 다루지 않아 enrich 가 §2 claim 8 을 🟡 PARTIAL 로 분리해야 했음. **filing-back 후보**: raw RHI.md §13 (변경 이력 다음) 또는 별도 raw `references/RHI-PSO.md` 작성이 vault 일관성에 기여.

2. **TransitionResources 의 raw 부재** — raw §6 EBufferUsageFlags 만 다루고 transition state machine 은 0 언급. RDG 가 자동화하지만, Custom RHI 직접 명령 시 transition 필수 → raw 가 "RHI 직접 명령 = 최소화" 정책으로 의도적 생략한 것으로 보임. 사용자 확인 후 명시화 가치 있음.

3. **FRHICommandListImmediate** vs `FRHICommandList` 차이 — raw 가 단일 `FRHICommandList&` 만 사용. UE 5.7.x 에서 Immediate 가 별도 변종으로 존재하므로, 본 카드 §6 🔴 섹션에 격리.

4. **페어 일관성** — [[sources/ue-render-vulkan]] 의 "Pipeline Barrier 누락 → race condition" 함정이 본 카드 §3 #2 (RHI 람다 안 Proxy 캡처) 와 동일 패턴. 두 카드가 같은 race 를 다른 레이어에서 다룸 → synthesis 후보 ("RHI race condition 3 레이어: 명령 큐 + Resource lifetime + Pipeline barrier").

5. **PSO Precache cycle** — 본 카드가 cycle #8 인데, [[synthesis/pso-precache-platform-matrix]] · [[synthesis/pso-streaming-livepatch-tools]] · [[synthesis/cooked-first-frame-stability]] 3개 synthesis 가 RHI PSO 를 공통 자산으로 사용. **RHI 카드가 이 3 synthesis 의 가장 lower-level 의존이지만 vault 가 그것을 명시적으로 cross-link 안 했었음** → 본 enrich 가 §5 에서 처음 연결.

사용자 결정 요청:
- [ ] §Boundary #1 (PSO gap) — raw RHI.md 보강 vs 별도 raw 작성?
- [ ] §Boundary #2 (TransitionResources) — raw 명시화 vs 의도적 생략 유지?
- [ ] §Boundary #4 (race synthesis) — 새 synthesis 작성?

## §7 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-10 | 최초 stub (29L) |
| 2026-05-12 | Cycle #8 slim enrich — §1~6 + 9 key claims + §13 tier + Boundary 5종 발견 |
