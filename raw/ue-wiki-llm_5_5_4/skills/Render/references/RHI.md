---
name: render-rhi
description: RHI (Rendering Hardware Interface) — FRHICommandList + FRHIResource + FRHITexture + FRHIBuffer. RHI Thread + Render Thread 동기화 + Vulkan/D3D12/Metal 추상. RDG 안 RHI 직접 명령 + Custom Resource 작성 표준.
---

# Render/RHI — Command List + Resources + GPU 동기화

> **위치**: `Engine/Source/Runtime/RHI/Public/RHI.h` + `RHICommandList.h` + `RHIResources.h` + `RHIContext.h`
> **요지**: GPU 직접 명령 (Vulkan / D3D12 / Metal 추상). RDG 가 대부분 RHI 호출을 추상화하지만, **Custom Resource / Custom Pass 안 RHI 직접 명령**이 필요한 경우.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 Lifetime | RHI Resource = `BeginInitResource` / `BeginReleaseResource` 페어 의무 |
| 🚨 스레드 | RHI Thread = Render Thread 와도 비동기 — RHI Lambda 안 Render Thread 객체 직접 접근 X |
| 🚨 RDG 우선 | 5.x — RDG 가 자동 처리 가능하면 RDG 사용. RHI 직접 명령 = 최소화 |

---

## 1. 핵심 클래스

| 클래스 | 책임 |
|--------|------|
| `FRHICommandList` | RHI 명령 큐 (Render Thread → RHI Thread) |
| `FRHIResource` | RHI Resource 베이스 (자동 GC) |
| `FRHITexture` | GPU Texture |
| `FRHIBuffer` | GPU Buffer (Vertex / Index / Constant) |
| `FRenderResource` | InitRHI / ReleaseRHI 페어 (CPU 측 wrapper) |
| `FRHIComputeShader` | Compute Shader Resource |

---

## 2. RHI vs RDG vs Render Thread (3단계)

```
[Render Thread]                   [RHI Thread]
ENQUEUE_RENDER_COMMAND
  ↓ (큐잉)
RDG 명령 등록 (FRDGBuilder)
  ↓ Execute()
                                  RHI Lambda 실행 (FRHICommandList)
                                    ↓ 실제 GPU 명령
                                  GPU 실행
```

→ **RDG 가 99% 추상화**. RHI 직접 명령 = Custom Resource / Vulkan 특화 등 드문 경우만.

---

## 3. ENQUEUE_RENDER_COMMAND (게임 → Render)

```cpp
// 게임 스레드 → Render Thread 명령 큐잉
void UMyComponent::DoSomething(float NewValue)
{
    // 게임 스레드 실행
    SomeData = NewValue;

    // Render Thread 큐잉
    ENQUEUE_RENDER_COMMAND(MyCommand)(
        [SceneProxy = SceneProxy, NewValue](FRHICommandList& RHICmdList)
        {
            // Render Thread 실행
            if (SceneProxy)
            {
                SceneProxy->UpdateData_RenderThread(NewValue);
            }
        });
}
```

---

## 4. Custom RHI Resource (FRenderResource 자손)

자주 쓰는 패턴 — Vertex Factory / Index Buffer 등.

### 4.1 정의

```cpp
class FMyVertexBuffer : public FRenderResource
{
public:
    FBufferRHIRef VertexBufferRHI;
    int32 NumVertices = 0;

    // Render Thread 측 초기화
    virtual void InitRHI(FRHICommandListBase& RHICmdList) override
    {
        FRHIResourceCreateInfo CreateInfo(TEXT("MyVertexBuffer"));

        // 5.x — FBufferRHIRef 표준
        FRHIBufferCreateDesc Desc = FRHIBufferCreateDesc::CreateVertex<FVector3f>(
            TEXT("MyVertexBuffer"),
            NumVertices)
            .SetUsage(EBufferUsageFlags::Static | EBufferUsageFlags::ShaderResource);

        VertexBufferRHI = RHICmdList.CreateBuffer(Desc);

        // 데이터 업로드
        void* Data = RHICmdList.LockBuffer(VertexBufferRHI, 0, NumVertices * sizeof(FVector3f), RLM_WriteOnly);
        FMemory::Memcpy(Data, MyVertexData.GetData(), NumVertices * sizeof(FVector3f));
        RHICmdList.UnlockBuffer(VertexBufferRHI);
    }

    virtual void ReleaseRHI() override
    {
        VertexBufferRHI.SafeRelease();
    }
};
```

### 4.2 사용 (의무 라이프사이클)

```cpp
// 생성 + 등록 (Render Thread)
FMyVertexBuffer* Buffer = new FMyVertexBuffer();
Buffer->NumVertices = 100;
BeginInitResource(Buffer);    // ⭐ 자동 InitRHI 호출

// 해제 (Render Thread)
BeginReleaseResource(Buffer);  // ⭐ 자동 ReleaseRHI
delete Buffer;                 // ReleaseFence 후 안전
```

---

## 5. FRHICommandList — RDG Pass 안 직접 명령

```cpp
GraphBuilder.AddPass(
    RDG_EVENT_NAME("MyDirectPass"),
    Parameters,
    ERDGPassFlags::Compute,
    [Parameters, Shader](FRDGAsyncTask, FRHIComputeCommandList& RHICmdList)
    {
        // RHI 직접 명령
        SetComputePipelineState(RHICmdList, Shader.GetComputeShader());
        SetShaderParameters(RHICmdList, Shader, Shader.GetComputeShader(), *Parameters);
        RHICmdList.DispatchComputeShader(GroupCount.X, GroupCount.Y, GroupCount.Z);
    }
);
```

---

## 6. FBufferRHIRef vs FBufferRHIRef (5.x 통합)

```cpp
// 5.x — FBufferRHIRef 단일 타입 (Vertex/Index/Structured 등 통합)
FBufferRHIRef VertexBufferRHI;
FBufferRHIRef IndexBufferRHI;
FBufferRHIRef ComputeBufferRHI;

// 생성 (FRHIBufferCreateDesc Builder Pattern)
FRHIBufferCreateDesc Desc = FRHIBufferCreateDesc::CreateVertex<FVector3f>(TEXT("Name"), Count)
    .SetUsage(EBufferUsageFlags::Static | EBufferUsageFlags::ShaderResource | EBufferUsageFlags::UnorderedAccess);

FBufferRHIRef Buffer = RHICmdList.CreateBuffer(Desc);
```

---

## 7. RHI Thread 안전성

```
[Render Thread]                   [RHI Thread]
Lambda 큐잉 ─────────────────→    Lambda 실행
  | 캡처 안 객체                    | 객체 = Render Thread 시점
  | (값 복사 OK)                    | (Render Thread 가 아직도 그 객체 가지고 있음 가정)

규칙:
- 람다 캡처 = 값 복사 또는 TRefCountPtr (RHI Resource)
- Lambda 안 Render Thread 객체 (Proxy 등) = TWeakObjectPtr / 안전 검사 의무
- RHI Resource = TRefCountPtr<FRHIResource> 자동 카운팅
```

---

## 8. RHI Feature Level 검사

```cpp
// FeatureLevel 검사 (Mobile / SM5 / SM6 분기)
if (GMaxRHIFeatureLevel >= ERHIFeatureLevel::SM5)
{
    // PC / Console 표준
}
else if (IsMobilePlatform(GMaxRHIShaderPlatform))
{
    // Mobile 분기
}

// HWRT 검사
if (IsRayTracingEnabled())
{
    // Hardware Ray Tracing 사용 가능
}
```

---

## 9. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | InitRHI / ReleaseRHI 페어 누락 | FRenderResource 자손 + BeginInitResource/BeginReleaseResource |
| 2 | Render Thread 안 RHI Resource 직접 생성 (RHICmdList 없이) | RHICmdList::CreateBuffer 사용 |
| 3 | RHI Lambda 안 Render Thread 객체 직접 접근 | 값 복사 또는 RAII |
| 4 | FBufferRHIRef Lifetime 미관리 (.SafeRelease 누락) | TRefCountPtr 자동 또는 ReleaseRHI 의무 |
| 5 | RDG 우회 + RHI 직접 명령 (5.x) | RDG Pass 안 RHI 명령 권장 |
| 6 | EBufferUsageFlags 잘못 (UAV 누락 등) | Usage Flag 정확 (ShaderResource / UAV / Static) |
| 7 | LockBuffer / UnlockBuffer 페어 누락 | 의무 |
| 8 | 5.x FRHIBufferCreateDesc 미사용 (Legacy) | 5.x = Builder Pattern 표준 |
| 9 | RHI Feature Level 분기 누락 (Mobile crash) | IsMobilePlatform / FeatureLevel 검사 |
| 10 | Multi-GPU (mGPU) 미고려 | MaskedGPU / GPU Index 처리 |

---

## 10. 체크리스트

- [ ] FRenderResource 자손 + InitRHI/ReleaseRHI 페어
- [ ] BeginInitResource / BeginReleaseResource 사용
- [ ] RHI Lambda 안 = 값 복사 또는 TRefCountPtr
- [ ] FBufferRHIRef + FRHIBufferCreateDesc (5.x Builder Pattern)
- [ ] LockBuffer/UnlockBuffer 페어
- [ ] EBufferUsageFlags 정확 (ShaderResource/UAV/Static)
- [ ] FeatureLevel 분기 (SM5/SM6/Mobile)
- [ ] HWRT 검사 (IsRayTracingEnabled)
- [ ] RDG 우선 — RHI 직접 명령 = 최소화

---

## 11. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- [`Render/references/RDG.md`](../RDG/SKILL.md) — RDG 가 대부분 RHI 추상화
- [`Render/references/Shader.md`](../Shader/SKILL.md) — Shader Resource = RHI Resource
- [`Render/references/MeshDrawing.md`](../MeshDrawing/SKILL.md) — Custom Vertex Factory 의 RHI Buffer

## 12. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. FRHICommandList + FRHIResource + FRenderResource + Init/ReleaseRHI 페어 + 5.x FBufferRHIRef + ENQUEUE_RENDER_COMMAND + RHI Thread 안전성 + 함정 10대. |
